"""Write-once, no-training intervention audit on the registered development replay.

Run with the maestro interpreter: python -m research.identifiability_audit.round2
{verify,run,analyse}. Reference parameters come from the frozen forecast notes.
WorldV2 is unavailable without its fitted transitions; never substitute ReferenceWorld.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
import platform
import re
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/identifiability_round2_20260930"
R1 = ROOT / "outputs/identifiability_audit_20260930"
FROZEN = ROOT / "outputs/protocol_v2_1_20260927/e_data1"
TASKS = (("sciplex3", "B"), ("l1000", "LT"))
SEED = 20260930
# No search: middle, outcome-blind historical upper-risk cap, declared before execution.
CAPS = {"sciplex3": 0.5294, "l1000": 0.2558}
CELLS = (("none", "baseline"), ("reference", "baseline"),
         ("permuted", "baseline"), ("constant", "baseline"),
         ("reference", "fixed"), ("reference", "discrimination"),
         ("reference", "risk_select"), ("none", "fixed"))
NOT_RUN = {
    "world_v2": "No serialized fitted WorldV2/PairModel; historical forecasts cover selected queries only. "
                "WorldV2 initialization or unseen prompt transitions invoke fit_incontext/fit_pair. "
                "No-training instruction forbids refitting. ReferenceWorld is never its substitute.",
    "state_gain": "No measured-at/available-at/decision-at timestamps and sample relation for pre-action state.",
    "case_memory": "Different LINCS2020 population and hypothesis-conditional outcome target.",
    "world_v2_policy_interaction": "The WorldV2 intervention cell is unavailable; no value is imputed.",
}


def finite_json(value):
    """Keep structural validator infinity explicit without emitting invalid JSON numbers."""
    if isinstance(value, dict):
        return {k: finite_json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [finite_json(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": str(value)}
    return value


def digest(value) -> str:
    return hashlib.sha256(json.dumps(finite_json(value), sort_keys=True, separators=(",", ":"),
                                     default=str, allow_nan=False).encode()).hexdigest()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        json.dump(finite_json(value), f, indent=2, default=str, allow_nan=False)


def read_rows(path: Path) -> list:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def tables(task: str) -> list:
    return [r for p in sorted((FROZEN / "tables").glob(task + "_*.jsonl.gz")) for r in read_rows(p)]


def verify(out: Path) -> None:
    """Recheck original hashes, raw-source replay and inherited numerical claims."""
    checks, ledger = [], {}
    def check(name, ok, detail):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
    for rel in ("log/20260930/README.md", "tests/test_identifiability_audit.py"):
        check(rel, (ROOT / rel).is_file(), "Recovered from stash object 11f7e57; see recovery.json")
    check("round1_log", "Round 1" in (ROOT / "log/20260930/README.md").read_text(), "Original record exists")
    for task, expected in (("sciplex3_B", 1296), ("l1000_LT", 2144)):
        old = json.loads((R1 / task / "summary.json").read_text())
        for item in old["inputs"].values():
            if item.get("sha256"):
                p = ROOT / item["path"]
                actual = file_hash(p)
                ledger[item["path"]] = actual
                check(item["path"], actual == item["sha256"], {"old": item["sha256"], "current": actual})
        a = pd.read_csv(R1 / task / "action_source.csv")
        b = pd.read_csv(out / "round1_replay" / task / "action_source.csv")
        check(task + ":action_source", a.equals(b), {"rows": len(b), "expected": expected})
        check(task + ":action_grid", len(b) == expected and not b.duplicated(["compound", "action"]).any(), expected)
    raw = ROOT / "data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad"
    provenance = json.loads(raw.with_suffix(".provenance.json").read_text())
    actual = file_hash(raw)
    ledger[str(raw.relative_to(ROOT))] = actual
    check("raw_sciplex3_hash", actual == provenance["sha256"], {"expected": provenance["sha256"], "actual": actual})
    manifest = json.loads((FROZEN / "manifest.json").read_text())
    for rel, expected in manifest["outputs_sha256"].items():
        actual = file_hash(FROZEN / rel)
        ledger[str((FROZEN / rel).relative_to(ROOT))] = actual
        check("frozen:" + rel, actual == expected, {"expected": expected, "actual": actual})
    old = json.loads((R1 / "unified_score/unified_score.json").read_text())
    new = json.loads((out / "round1_replay/unified_score/unified_score.json").read_text())
    check("unified_numeric_replay", old == new, "Complete JSON equality; cost error remains in historical scorer")
    reasons = pd.read_csv(out / "round1_replay/l1000_LT/unlinked_reasons.csv")
    check("l1000_source_disagreements", len(reasons) == 5 and (reasons.linkage == "unresolved_source_linkage").sum() == 4,
          reasons.to_dict("records"))
    reasons.to_csv(out / "unresolved_sources.csv", index=False, mode="x")
    for path in sorted(R1.rglob("*")):
        if path.is_file():
            ledger[path.relative_to(ROOT).as_posix()] = file_hash(path)
    for path in [FROZEN / "manifest.json", FROZEN / "run_record.json", ROOT / "research/dual_core_v2/protocol.json",
                 ROOT / "outputs/belief_planning_20260927/registered/dev/manifest.json"]:
        ledger[path.relative_to(ROOT).as_posix()] = file_hash(path)
    save(out / "round1_input_hashes.json", ledger)
    save(out / "verification.json", {"passed": all(c["passed"] for c in checks), "checks": checks})
    if not all(c["passed"] for c in checks):
        raise RuntimeError("round1_source_verification_failed: terminal comparison stopped")
    print("Round 1 verified:", len(checks), "checks", flush=True)


def paired_ci(frame: pd.DataFrame, column: str) -> dict:
    values = frame.groupby("independent_unit", sort=True)[column].mean().dropna().to_numpy(float)
    if not len(values):
        return {"mean": None, "ci95": None, "units": 0}
    rng = np.random.default_rng(SEED)
    boot = values[rng.integers(0, len(values), (2000, len(values)))].mean(axis=1)
    return {"mean": float(values.mean()), "ci95": np.quantile(boot, [0.025, 0.975]).tolist(), "units": len(values)}


def corrected_four_arms(task: str, ctxs: dict, out: Path) -> dict:
    """Independent sequence walk; days charged only for actually executed attempts."""
    from research.identifiability_audit import unified_score as U
    from research.protocol_v2 import e_data1 as ED
    from research.protocol_v2.contracts import C
    rows = tables(task)
    s = json.loads((FROZEN / "manifest.json").read_text())["settings"][task]
    days = s["days"]
    seqs = ED.legal_sequences([tuple(k) for k in s["keys"]], days, s["budget_days"], s["max_measurements"])
    choice = ED.fixed_star(rows, seqs)
    records = []
    for row in rows:
        seq = choice[row["fold"]]
        counts = U.template_counts(ctxs[row["fold"]].ft, tuple(seq[0]), (row["h1"], row["h2"]))
        deferred = not all(counts.values())
        for name, picked in (
            ("fixed_must_act", seq), ("fixed_may_abstain", () if deferred else seq),
            ("oracle_must_act", U.oracle_sequence(row, seqs, days, False)),
            ("oracle_may_abstain", U.oracle_sequence(row, seqs, days, True))):
            result = walk_sequence(row, [C.action_id(tuple(k)) for k in picked], days)
            records.append({"arm": name, "fold": row["fold"], "compound": row["compound"],
                            "h1": row["h1"], "h2": row["h2"], "independent_unit": str(row["unit"]), **result})
    frame = pd.DataFrame(records)
    frame.to_csv(out / (task + "_four_arms.csv"), mode="x", index=False)
    return {name: {metric: paired_ci(sub, metric) for metric in
                  ("correct", "wrong", "undetermined", "deferred", "measurements", "days", "utility")}
            for name, sub in frame.groupby("arm")}


def walk_sequence(row: dict, sequence: list, days: dict) -> dict:
    final, spent, n = "deferred", 0.0, 0
    for action in sequence:
        entry = row["outcomes"][action]  # absent outcomes fail closed
        spent += days[action]
        n += 1
        final = "undetermined"
        if entry["lifecycle"] == "measured_valid" and entry["outcome"] in ("eliminate_a", "eliminate_b"):
            removed = row["h1"] if entry["outcome"] == "eliminate_a" else row["h2"]
            final = "wrong" if removed == row["truth"] else "correct"
            break
    return {"final": final, "correct": int(final == "correct"), "wrong": int(final == "wrong"),
            "undetermined": int(final == "undetermined"), "deferred": int(final == "deferred"),
            "measurements": n, "days": spent, "utility": {"correct": 1, "wrong": -2}.get(final, 0)}


class AuditWorld:
    """Same forecast API for every selector; immutable content cached by complete query."""
    def __init__(self, name, world, menu, input_hash, fold):
        self.name, self.world, self.input_hash = name, world, input_hash
        self.cache, self.calls = {}, []
        keys = list(menu)
        rng = np.random.default_rng([SEED, fold, 1 if world.ft.classes else 0])
        order = rng.permutation(len(keys))
        if any(i == j for i, j in enumerate(order)):
            order = np.roll(np.arange(len(keys)), 1)
        self.mapping = dict(zip(keys, [keys[i] for i in order]))

    def forecast(self, key, h1, h2, compound, history=(), *, channel="selector"):
        from maestro.acquisition import OutcomeBranch, OutcomeForecast
        from research.belief_planning import world as W
        from research.protocol_v2.contracts import C
        key, history = tuple(key), tuple((tuple(k), label) for k, label in history)
        query = {"task_input": self.input_hash, "forecast": self.name, "compound": compound,
                 "h1": h1, "h2": h2, "action": C.action_id(key), "history": history}
        input_digest = digest(query)
        if input_digest not in self.cache:
            if self.name == "none":
                fc = OutcomeForecast(C.action_id(key), refusal="forecast_disabled_by_audit", model_version="audit-none")
            elif self.name == "constant":
                fc = OutcomeForecast(C.action_id(key), tuple(OutcomeBranch(h, {label: 0.2 for label in W.LABELS}, 0)
                                                            for h in (h1, h2)), model_version="audit-constant-uniform")
            else:
                source = self.mapping[key] if self.name == "permuted" else key
                hist = tuple((self.mapping[k], label) for k, label in history) if self.name == "permuted" else history
                raw = self.world.forecast(source, h1, h2, compound, hist)
                fc = replace(raw, action_identifier=C.action_id(key))
            content = {"branches": [{"hypothesis": b.hypothesis, "probabilities": dict(b.probabilities),
                                      "support": b.support} for b in fc.branches], "refusal": fc.refusal,
                       "version": fc.model_version, "basis": fc.basis, "action": fc.action_identifier}
            self.cache[input_digest] = fc, content
        fc, content = self.cache[input_digest]
        self.calls.append({**query, "channel": channel, "input_sha256": input_digest,
                           "output_sha256": digest(content), "available": not bool(fc.refusal),
                           "refusal": fc.refusal, "content": content})
        return fc


def selector(policy, audited: AuditWorld, cap):
    from maestro.acquisition import outcome_consequences, select_discriminating_action
    from research.belief_planning import arms as BA, world as W
    from research.belief_planning.planner import plan_measurement, update_belief
    from research.sequence_audit import policies as P
    C, V = BA.C, BA.V
    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        if policy == "fixed":
            return P.fixed(ctx, compound, h1, h2, executed, menu, remaining, setting, state)
        if not ctx.params.get("eliminates"):
            return None, {"reason": "registered_validator_cannot_eliminate", "policy": policy}
        real = tuple((tuple(s["key"]), W.label_of(s["outcome"])) for s in executed)
        by_id = {C.action_id(k): k for k in setting.keys}
        actions = [P.make_action(k, h1, h2, setting) for k in menu]
        rules = outcome_consequences(V.registered_rules(h1, h2))
        if policy == "discrimination":
            forecasts = {a.identifier: audited.forecast(by_id[a.identifier], h1, h2, compound, real) for a in actions}
            plan = select_discriminating_action(frozenset((h1, h2)), actions, BA.E.PROFILE,
                                               min(remaining, setting.step_budget), forecasts, rules)
            chosen = plan.chosen.action_identifier if plan.chosen else None
            return by_id[chosen] if chosen else None, {"policy": policy, "reason": "acquisition_" + plan.status,
                                                       "evidence_kind": "model_prediction"}
        belief = {h1: 0.5, h2: 0.5}
        for i, (key, label) in enumerate(real):
            belief = update_belief(belief, audited.forecast(key, h1, h2, compound, real[:i]), label)
        done = [tuple(s["key"]) for s in executed]
        def legal(hyp):
            keys = done + [by_id[a] for a, _ in hyp]
            if len(keys) >= setting.max_measurements:
                return ()
            left = setting.budget_days - sum(setting.days(k) for k in keys)
            return tuple(P.make_action(k, h1, h2, setting) for k in
                         P.legal_menu(setting, [{"key": k} for k in keys], left))
        def forecast(action, hyp):
            hist = real + tuple((by_id[a], label) for a, label in hyp)
            return audited.forecast(by_id[action.identifier], h1, h2, compound, hist)
        plan = plan_measurement((h1, h2), belief, legal, forecast, rules,
                                horizon=setting.max_measurements - len(executed), price=BA.PRICE,
                                wrong_risk_cap=cap if policy == "risk_select" else None)
        return by_id[plan.chosen] if plan.chosen else None, {
            "policy": policy, "reason": "belief_" + str(plan.reason), "evidence_kind": "model_prediction",
            "p_wrong_upper_plan": plan.value.p_wrong_upper, "wrong_loss_used": plan.wrong_loss_used}
    return arm


def utility_bounds(final: str, unresolved: bool) -> tuple:
    """Conservative outer bounds; uncertainty is never filled by a model."""
    if unresolved:
        return -2.0, 1.0
    value = {"correct": 1.0, "wrong": -2.0, "exhausted": -2.0}.get(final, 0.0)
    return value, value


def run(out: Path, resume: bool = False) -> None:
    from threadpoolctl import threadpool_limits
    from research.protocol_v2 import contracts as K, runner as RN, tasks_v21 as V
    from research.belief_planning import arms as BA, world as W
    if not json.loads((out / "verification.json").read_text())["passed"]:
        raise RuntimeError("round1_source_verification_failed")
    run_dir = out / "interventions"
    run_dir.mkdir(exist_ok=resume)
    inputs = json.loads((out / "round1_input_hashes.json").read_text())
    for path in ROOT.glob("research/**/*.py"):
        inputs[path.relative_to(ROOT).as_posix()] = file_hash(path)
    for path in ROOT.glob("src/**/*.py"):
        inputs[path.relative_to(ROOT).as_posix()] = file_hash(path)
    for path in list((ROOT / "outputs/dynamic_world_model_20260926/prepared").glob("*")) + list(
            (ROOT / "outputs/sequence_audit_20260926/l1000/prepared").glob("*")):
        if path.is_file():
            inputs[path.relative_to(ROOT).as_posix()] = file_hash(path)
    manifest = {"seed": SEED, "cells": CELLS, "risk_caps": CAPS, "not_run": NOT_RUN, "inputs": inputs,
                "command": [sys.executable, *sys.argv], "git_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "environment": {"python": sys.version, "platform": platform.platform(), "interpreter": sys.executable,
                                "packages": {p: importlib.metadata.version(p) for p in
                                             ("numpy", "pandas", "scipy", "h5py", "rdkit", "threadpoolctl")}},
                "exposure": "SciPlex3/L1000 development data, models, caps and outcomes exposed in blocks 2-7 "
                            "since 2026-09-26. Descriptive audit, no untouched-test or superiority claim.",
                "bounds_rule": "U in [-2,+1] on a selected unresolved source condition; shared fixed path exact zero. "
                               "Known QC failures are observed attempts, not imputed biological readings.",
                "visibility": "Structure, hypotheses, training-only tables, frozen calibration, design menu, budgets, "
                              "purchased real readings. No hidden held-out reading, truth, quality or unbought profile. "
                              "Fixed ignores forecasts; other policies share the exact query-to-forecast function.",
                "cost": "Actual attempts charged, QC failures charged; endpoint U=correct-2*wrong excludes cost; "
                        "planner price=0.02 per assay day, reported separately.", "tasks": {}}
    if resume:
        inputs = json.loads((run_dir / "predeclared.json").read_text())["inputs"]
        receipt = "resume_receipt_" + str(len(list(run_dir.glob("resume_receipt*.json"))) + 1) + ".json"
        save(run_dir / receipt, {"command": [sys.executable, *sys.argv],
             "source_sha256": file_hash(Path(__file__)), "cause": "four-arm review passed an extra argument "
             "to existing fixed_star; interventions completed and preserved. Helper corrected; no policy change."})
    else:
        save(run_dir / "predeclared.json", manifest)
    with threadpool_limits(limits=1):
        for dataset, tier in TASKS:
            task = dataset + "_" + tier
            if resume and (run_dir / (task + "_episodes.csv")).is_file():
                anchors = json.loads((run_dir / (task + "_anchors.json")).read_text())
                if not anchors or not all(r["same"] for r in anchors):
                    raise AssertionError("cannot_resume_failed_reference_anchor")
                if not (run_dir / (task + "_four_arm_summary.json")).exists():
                    ctxs = {f: V.load(dataset, tier, f)[1] for f in range(5)}
                    save(run_dir / (task + "_four_arm_summary.json"), corrected_four_arms(task, ctxs, run_dir))
                print(task, "completed intervention preserved", flush=True)
                continue
            records, ctxs, task_freeze, anchors = [], {}, [], []
            forecast_file = gzip.open(run_dir / (task + "_forecasts.jsonl.gz"), "xt", encoding="utf-8")
            source = pd.read_csv(out / "round1_replay" / task / "action_source.csv").set_index(["compound", "action"])
            unresolved = set()
            if dataset == "l1000":
                reasons = pd.read_csv(out / "unresolved_sources.csv")
                unresolved = set(zip(reasons[reasons.linkage == "unresolved_source_linkage"].compound,
                                     reasons[reasons.linkage == "unresolved_source_linkage"].action))
            frozen_by_id = {(r["fold"], r["compound"], r["h1"], r["h2"]): r for r in tables(task)}
            for fold in range(5):
                data, ctx, setting, design = V.load(dataset, tier, fold)
                ctxs[fold] = ctx
                episodes = V.episode_list(ctx, fold)
                heldout = set(data.compounds.loc[data.compounds.fold == fold, "compound"])
                training = V.training_compounds(ctx, fold)
                view = K.public_view(ctx, heldout, training_compounds=training, design=design)
                if K.public_view_problems(view, heldout):
                    raise AssertionError("policy_firewall_failed")
                old = read_rows(FROZEN / "scored" / f"{task}_{fold}.jsonl.gz")
                notes = [s["note"].get("basis", "") for r in old if r["arm"] == "belief" for s in r["steps"]]
                hp = next((dict(zip(("s", "k", "e"), map(float, m.groups()))) for text in notes
                           if (m := re.search(r"\[s=([\d.]+),k=([\d.]+),e=([\d.]+)\]", text))), None)
                if hp is None:
                    if ctx.params.get("eliminates"):
                        raise RuntimeError("missing_frozen_reference_hyperparameters")
                    hp = {"s": 4.0, "k": 0.0, "e": 0.3}  # structural abstention; no policy consults this
                fp, pos = BA.fingerprints(view.data.compounds)
                comp = view.data.compounds.drop_duplicates("compound").set_index("compound")
                unit_col = "component" if dataset == "l1000" else "skeleton"
                groups = comp[unit_col].to_dict()
                world = W.ReferenceWorld(view.ft, view.params, training, fingerprints=fp, positions=pos,
                                         groups=groups, hyperparameters=hp)
                fold_freeze = {"fold": fold, "episodes": [list(e) for e in episodes], "menu": setting.keys,
                               "budget_days": setting.budget_days, "max_measurements": setting.max_measurements,
                               "fixed_order": setting.fixed_order, "days": {K.C.action_id(k): setting.days(k) for k in setting.keys},
                               "qc": "registered executor; failed attempts cost days and change no evidence",
                               "validator": ctx.params, "reference_hyperparameters": hp, "training": training,
                               "endpoint": "MoA proxy, first registered elimination; stop at 2 attempts or budget",
                               "availability": {c: sorted(view.data.availability[c]) for c, *_ in episodes}}
                task_freeze.append(fold_freeze)
                input_hash = digest({"fold": fold_freeze, "input_files": inputs})
                for fname, policy in CELLS:
                    audited = AuditWorld(fname, world, setting.keys, input_hash, fold)
                    inner = selector(policy, audited, CAPS[dataset])
                    for compound, truth, decoy, h1, h2 in episodes:
                        row = frozen_by_id[(fold, compound, h1, h2)]
                        decisions = []
                        def arm(*args):
                            before = len(audited.calls)
                            key, note = inner(*args)
                            decisions.append({"chosen": K.C.action_id(key) if key else None,
                                              "forecast_calls": len(audited.calls) - before, "note": note})
                            return key, note
                        trace = RN.run_episode(fname + "|" + policy, arm, view, ctx, compound, h1, h2, setting,
                                               design_menu=True)
                        if RN.audit_trace(trace, setting):
                            raise AssertionError("illegal_trace")
                        score = K.score(trace, truth)
                        ep = f"{fold}|{compound}|{h1}|{h2}"
                        calls = audited.calls
                        used = any(d["forecast_calls"] for d in decisions)
                        ranking = []
                        nll, brier, snll, sbrier = [], [], [], []
                        for key in setting.keys:
                            fc = audited.forecast(key, h1, h2, compound, channel="probe")
                            probabilities = {b.hypothesis: dict(b.probabilities) for b in fc.branches}
                            if not fc.refusal:
                                val = sum(0.5 * (p.get(W.MATCH_H1 if h == h1 else W.MATCH_H2, 0) -
                                                       2 * p.get(W.MATCH_H2 if h == h1 else W.MATCH_H1, 0))
                                          for h, p in probabilities.items()) - BA.PRICE * setting.days(key)
                                ranking.append((K.C.action_id(key), val))
                                label = W.label_of(row["outcomes"][K.C.action_id(key)]["outcome"])
                                p = probabilities[truth]
                                loss = -float(np.log(max(p.get(label, 0.0), 1e-12)))
                                bs = sum((p.get(l, 0.0) - (l == label)) ** 2 for l in W.LABELS)
                                nll.append(loss); brier.append(bs)
                        for i, step in enumerate(trace["steps"]):
                            hist = tuple((tuple(s["key"]), W.label_of(s["outcome"])) for s in trace["steps"][:i])
                            fc = audited.forecast(step["key"], h1, h2, compound, hist, channel="quality_selected")
                            if not fc.refusal:
                                p = dict(fc.branch_for(truth).probabilities)
                                label = W.label_of(step["outcome"])
                                snll.append(-float(np.log(max(p.get(label, 0), 1e-12))))
                                sbrier.append(sum((p.get(l, 0.0) - (l == label)) ** 2 for l in W.LABELS))
                        sequence = [s["action"] for s in trace["steps"]]
                        rank = [a for a, _ in sorted(ranking, key=lambda x: (-x[1], x[0]))]
                        touched = any((compound, a) in unresolved for a in sequence)
                        low, high = utility_bounds(score["final"], touched)
                        records.append({"task": task, "episode": ep, "fold": fold, "compound": compound,
                                        "independent_unit": str(row["unit"]), "chemical_unit_kind": unit_col,
                                        "h1": h1, "h2": h2, "forecast": fname, "policy": policy,
                                        "backend": "belief_planning.world.ReferenceWorld" if fname in ("reference", "permuted") else fname,
                                        "version": "belief-planning-1" if fname in ("reference", "permuted") else "audit-control",
                                        "action_menu": json.dumps([K.C.action_id(k) for k in setting.keys]),
                                        "coverage": "source_linkage_unresolved" if touched else "registered_attempt_observed",
                                        "sequence": json.dumps(sequence), "first_action": sequence[0] if sequence else "",
                                        "later_actions": json.dumps(sequence[1:]), "ranking": json.dumps(rank),
                                        "forecast_entered_selector": used, "forecast_entered_repair": False,
                                        "forecast_entered_final_evidence": False,
                                        "forecast_input_hashes": json.dumps(sorted({c["input_sha256"] for c in calls})),
                                        "forecast_output_hashes": json.dumps(sorted({c["output_sha256"] for c in calls})),
                                        "forecast_available": any(c["available"] for c in calls),
                                        "forecast_refusals": json.dumps(sorted({c["refusal"] for c in calls if c["refusal"]})),
                                        "steps": json.dumps(trace["steps"], default=str), "decisions": json.dumps(decisions, default=str),
                                        "offered": json.dumps(trace["offered"]), "stop": trace["stop"], "final": score["final"],
                                        "correct": score["correct"], "wrong": score["wrong"],
                                        "undetermined": int(score["final"] == "undetermined"),
                                        "deferred": int(score["final"] == "deferred"),
                                        "measurements": trace["measurements"], "days": trace["days"], "utility": score["utility"],
                                        "utility_lo": low, "utility_hi": high,
                                        "nll_all": float(np.mean(nll)) if nll else np.nan,
                                        "brier_all": float(np.mean(brier)) if brier else np.nan,
                                        "nll_selected": float(np.mean(snll)) if snll else np.nan,
                                        "brier_selected": float(np.mean(sbrier)) if sbrier else np.nan,
                                        "selected_forecast_steps": len(snll)})
                        unique_calls = {}
                        for c in calls:
                            ident = c["channel"], c["input_sha256"]
                            if ident not in unique_calls:
                                unique_calls[ident] = {"task": task, "episode": ep, "policy": policy, **c, "calls": 0}
                            unique_calls[ident]["calls"] += 1
                        for c in unique_calls.values():
                            forecast_file.write(json.dumps(c, default=str, allow_nan=False) + "\n")
                        audited.calls = []
                        audited.cache.clear()
                        world._cache.clear()
                        if fname == "reference" and policy == "baseline":
                            historic = next(r for r in old if r["arm"] == "belief" and r["compound"] == compound
                                            and r["h1"] == h1 and r["h2"] == h2)
                            anchors.append({"episode": ep, "same": sequence == [s["action"] for s in historic["steps"]]})
                    print(task, fold, fname, policy, "done", flush=True)
                world._cache.clear()
            frame = pd.DataFrame(records)
            frame.to_csv(run_dir / (task + "_episodes.csv"), index=False, mode="x")
            forecast_file.close()
            save(run_dir / (task + "_freeze.json"), task_freeze)
            save(run_dir / (task + "_anchors.json"), anchors)
            if not all(r["same"] for r in anchors):
                raise AssertionError("reference_baseline_fails_frozen_anchor")
            save(run_dir / (task + "_four_arm_summary.json"), corrected_four_arms(task, ctxs, run_dir))


def analyse(out: Path) -> None:
    run_dir = out / "interventions"
    summaries = {}
    for dataset, tier in TASKS:
        task = dataset + "_" + tier
        frame = pd.read_csv(run_dir / (task + "_episodes.csv")).fillna({"first_action": ""})
        frozen_folds = json.loads((run_dir / (task + "_freeze.json")).read_text())
        structural = {f["fold"] for f in frozen_folds if not f["validator"].get("eliminates")}
        # No historical reference parameter is observable when the frozen planner never forecasted.
        # Keep the probe receipt, but exclude its structural placeholder from quality claims.
        frame.loc[frame.fold.isin(structural), ["nll_all", "brier_all", "nll_selected", "brier_selected"]] = np.nan
        source = pd.read_csv(out / "round1_replay" / task / "action_source.csv")
        if dataset == "l1000":
            bad = source[~source.cache_plate_agrees]
            unresolved = set(zip(bad.compound, bad.action))
            for i, row in frame.iterrows():
                if any((row.compound, action) in unresolved for action in json.loads(row.sequence)):
                    frame.loc[i, ["utility_lo", "utility_hi", "coverage"]] = [-2.0, 1.0, "source_linkage_unresolved"]
        fixed = frame[(frame.forecast == "reference") & (frame.policy == "fixed")].set_index("episode")
        ref = frame[(frame.forecast == "reference") & (frame.policy == "baseline")].set_index("episode")
        findings, paths = [], []
        for (fname, policy), group in frame.groupby(["forecast", "policy"]):
            sub = group.set_index("episode").loc[fixed.index].copy()
            anchor = ref if policy == "baseline" else fixed
            sub["first_changed"] = (sub.first_action != anchor.first_action).astype(int)
            sub["later_changed"] = (sub.later_actions != anchor.later_actions).astype(int)
            sub["sequence_changed"] = (sub.sequence != anchor.sequence).astype(int)
            sub["terminal_changed"] = (sub.final != anchor.final).astype(int)
            sub["ranking_changed"] = (sub.ranking != anchor.ranking).astype(int)
            sub["action_changed_terminal_same"] = ((sub.sequence != anchor.sequence) & (sub.final == anchor.final)).astype(int)
            sub["delta_correct"] = sub.correct - fixed.correct
            sub["delta_wrong"] = sub.wrong - fixed.wrong
            sub["delta_utility"] = sub.utility - fixed.utility
            sub["delta_lo"] = sub.utility_lo - fixed.utility_hi
            sub["delta_hi"] = sub.utility_hi - fixed.utility_lo
            same_path = sub.sequence == fixed.sequence
            sub.loc[same_path, ["delta_lo", "delta_hi"]] = 0.0
            metrics = ("correct", "wrong", "undetermined", "deferred", "measurements", "days", "utility",
                       "nll_all", "brier_all", "nll_selected", "brier_selected", "first_changed", "later_changed",
                       "sequence_changed", "ranking_changed", "terminal_changed", "action_changed_terminal_same",
                       "delta_correct", "delta_wrong", "delta_utility", "delta_lo", "delta_hi")
            report = {"forecast": fname, "policy": policy, "episodes": len(sub),
                      "metrics": {m: paired_ci(sub, m) for m in metrics},
                      "selected_forecast_calls": int(sub.forecast_entered_selector.sum()),
                      "action_change_reference": "reference|baseline" if policy == "baseline" else "reference|fixed",
                      "outcome_identification": "partial" if (sub.utility_lo != sub.utility_hi).any() else "registered_replay",
                      "action_changed_terminal_same_conditional": float(sub.action_changed_terminal_same.sum() /
                                                                         max(1, sub.sequence_changed.sum()))}
            decided = sub.correct + sub.wrong
            coverage = decided.groupby(sub.independent_unit).mean().mean()
            wrong = sub.wrong.groupby(sub.independent_unit).mean().mean()
            report["decided_coverage"] = float(coverage)
            report["wrong_among_decided"] = float(wrong / coverage) if coverage else None
            acted = sub.measurements > 0
            common = acted & (fixed.measurements > 0)
            report["matched_acted_coverage"] = {"episodes": int(common.sum()),
                "qualification": "Descriptive common acted subset; not randomized or an untouched-test risk guarantee",
                "candidate": {m: paired_ci(sub[common], m) for m in ("correct", "wrong", "days", "measurements")},
                "fixed": {m: paired_ci(fixed[common], m) for m in ("correct", "wrong", "days", "measurements")}}
            joint_decided = (sub.correct + sub.wrong > 0) & (fixed.correct + fixed.wrong > 0)
            report["matched_decided_coverage"] = {"episodes": int(joint_decided.sum()),
                "qualification": "Both policies decided on these same episodes; equal conditional coverage. "
                                 "Outcome-selected descriptive subset, not a pre-action strategy or general risk estimate.",
                "candidate": {m: paired_ci(sub[joint_decided], m) for m in ("correct", "wrong", "days", "measurements")},
                "fixed": {m: paired_ci(fixed[joint_decided], m) for m in ("correct", "wrong", "days", "measurements")}}
            findings.append(report)
            sub["bottleneck"] = np.select(
                [sub.coverage == "source_linkage_unresolved", sub.deferred == 1,
                 sub.policy == "fixed", (sub.sequence_changed == 1) & (sub.terminal_changed == 0),
                 (sub.ranking_changed == 1) & (sub.sequence_changed == 0)],
                ["source_linkage_unresolved", "abstention", "forecast_ignored_negative_control",
                 "menu_or_validator", "forecast_to_selection_insensitive"],
                default="terminal_changed_requires_paired_assessment")
            paths.append(sub.reset_index())
        cells = {(f, p): frame[(frame.forecast == f) & (frame.policy == p)].set_index("episode").loc[fixed.index]
                 for f, p in CELLS}
        interaction = cells[("reference", "baseline")].copy()
        interaction["interaction"] = (cells[("reference", "baseline")].utility - cells[("none", "baseline")].utility -
                                      cells[("reference", "fixed")].utility + cells[("none", "fixed")].utility)
        columns = ["prep_plate_rep1", "prep_plate_rep2"] if dataset == "sciplex3" else ["inst_plate_names"]
        components, plate_count = physical_components(source, columns)
        summaries[task] = {"cells": findings, "reference_presence_x_baseline_vs_fixed": paired_ci(interaction, "interaction"),
                           "structural_validator_folds": sorted(structural),
                           "world_v2_x_policy": {"identified": False, "reason": NOT_RUN["world_v2_policy_interaction"]},
                           "physical_dependence": {"distinct_treatment_plates": plate_count,
                               "components_from_shared_treatment_plates": len(set(components.values())),
                               "ci95": None, "reason": "Shared plate connectivity has insufficient independent clusters; "
                                                        "controls add dependence. Chemical CIs cannot be interpreted as plate CIs."},
                           "ranking_definition": "Unconditioned forecast expected one-step terminal utility minus day price; "
                                                 "probe ranking is separate from policy evaluations and forecast-use calls.",
                           "quality_definition": "Truth-branch attempted-reading NLL and multiclass Brier; QC class included. "
                                                 "All-menu initial predictions and selected-action pre-measurement predictions separated."}
        pd.concat(paths).to_csv(run_dir / (task + "_path_attribution.csv"), mode="x", index=False)
    save(run_dir / "task_summary.json", summaries)
    print("Analysis saved", flush=True)


def physical_components(source: pd.DataFrame, columns: list) -> tuple:
    parents = {c: c for c in source.compound.unique()}
    def find(c):
        while parents[c] != c:
            parents[c] = parents[parents[c]]
            c = parents[c]
        return c
    plates = {}
    for row in source.to_dict("records"):
        for col in columns:
            for plate in str(row[col]).split("|"):
                if plate and plate != "nan":
                    if plate in plates:
                        parents[find(row["compound"])] = find(plates[plate])
                    else:
                        plates[plate] = row["compound"]
    return {c: find(c) for c in parents}, len(plates)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("verify", "run", "analyse"))
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--resume", action="store_true", help="preserve completed task artifacts after a failed review step")
    args = parser.parse_args()
    if args.stage == "run":
        run(args.out, args.resume)
    else:
        {"verify": verify, "analyse": analyse}[args.stage](args.out)


if __name__ == "__main__":
    main()
