"""Write-once frozen ReferenceWorld follow-up: freeze, probe, then run all four arms."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import gzip
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import numpy as np
import pandas as pd

from research.identifiability_audit.round2 import ROOT, SEED, digest, file_hash, finite_json, paired_ci, read_rows, save

R2 = ROOT / "outputs/identifiability_round2_20260930"
FROZEN = ROOT / "outputs/protocol_v2_1_20260927/e_data1"
DEFAULT_OUT = ROOT / "outputs/dual_core_followup_20261001/anchored_run"
PROTOCOL = Path(__file__).with_name("protocol.json")
ARMS = (("fixed_none", "fixed", None), ("baseline_reference", "baseline", "reference"),
        ("anchored_reference", "anchored", "reference"), ("anchored_permuted", "anchored", "permuted"))
TASKS = (("sciplex3", "B"), ("l1000", "LT"))
DEVIATION_Z, PRICE = 1.645, 0.02


def restore(value):
    if isinstance(value, dict):
        if set(value) == {"nonfinite"}:
            return float(value["nonfinite"])
        return {k: restore(v) for k, v in value.items()}
    if isinstance(value, list):
        return [restore(v) for v in value]
    return value


def freeze(out):
    """Freeze sources and actual replay inputs before either probe or full execution."""
    out.mkdir(parents=True, exist_ok=False)
    inherited = json.loads((R2 / "artifact_ledger.json").read_text(encoding="utf-8"))
    paths = set()
    for field in ("original_and_frozen_inputs", "intervention_inputs", "additional_input_sha256"):
        paths.update(inherited.get(field, {}))
    # All prepared files consumed by existing loaders, including biological-depth metadata.
    for directory in ("outputs/dynamic_world_model_20260926/prepared", "outputs/biological_depth_20260926/prepared",
                      "outputs/sequence_audit_20260926/l1000/prepared"):
        paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT / directory).glob("*") if p.is_file())
    paths.update(p.relative_to(ROOT).as_posix() for p in (FROZEN / "tables").glob("*.jsonl.gz"))
    paths.update(p.relative_to(ROOT).as_posix() for p in (R2 / "interventions").glob("*_freeze.json"))
    paths.update("outputs/identifiability_round2_20260930/" + p for p in
                 ("artifact_ledger.json", "verification.json", "source_discrepancy_detail.csv", "interventions/predeclared.json",
                  "interventions/sciplex3_B_episodes.csv", "interventions/l1000_LT_episodes.csv"))
    sources = set()
    for directory in ("src", "research/protocol_v2", "research/belief_planning", "research/sequence_audit",
                      "research/dynamic_world_model", "research/acquisition_link", "research/identifiability_audit"):
        sources.update(p.relative_to(ROOT).as_posix() for p in (ROOT / directory).rglob("*.py"))
        sources.update(p.relative_to(ROOT).as_posix() for p in (ROOT / directory).glob("*.json"))
    sources.update(p.relative_to(ROOT).as_posix() for p in (Path(__file__), PROTOCOL, ROOT / "tests/test_dual_core_followup.py"))
    # Inherited ledgers may contain descriptions rather than a path: only actual files are inputs.
    absent = sorted(p for p in paths if not (ROOT / p).is_file())
    if absent:
        raise RuntimeError(f"missing_frozen_inputs:{absent}")
    if not json.loads((R2 / "verification.json").read_text())["passed"]:
        raise RuntimeError("inherited_round1_verification_failed")
    record = {"protocol_sha256": file_hash(PROTOCOL), "protocol": json.loads(PROTOCOL.read_text()),
              "input_sha256": {p: file_hash(ROOT / p) for p in sorted(paths)},
              "source_sha256": {p: file_hash(ROOT / p) for p in sorted(sources)},
              "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "command": [sys.executable, *sys.argv],
              "environment": {"interpreter": sys.executable, "python": sys.version, "platform": platform.platform(),
                              "packages": {p: importlib.metadata.version(p) for p in
                                           ("numpy", "pandas", "scipy", "rdkit", "threadpoolctl")}},
              "inherited_ledger_is_not_new_raw_replay": True}
    save(out / "predeclared.json", record)
    print("frozen", digest(record), flush=True)


def verify_freeze(out):
    frozen = json.loads((out / "predeclared.json").read_text())
    for kind in ("input_sha256", "source_sha256"):
        for rel, expected in frozen[kind].items():
            if file_hash(ROOT / rel) != expected:
                raise RuntimeError(f"freeze_changed:{rel}")
    return frozen


class ForecastLog:
    """Global content-addressed banks; episodes keep only compact receipt references."""
    def __init__(self, directory):
        self.query_seen, self.output_seen, self.bundle_seen = set(), set(), set()
        self.files = {name: gzip.open(directory / (name + ".jsonl.gz"), "xt", encoding="utf-8")
                      for name in ("queries", "forecast_outputs", "call_bundles")}

    def write(self, name, value):
        self.files[name].write(json.dumps(finite_json(value), sort_keys=True, allow_nan=False) + "\n")

    def forecast(self, query, content):
        q, o = digest(query), digest(content)
        if o not in self.output_seen:
            self.output_seen.add(o)
            self.write("forecast_outputs", {"output_sha256": o, "content": content})
        if q not in self.query_seen:
            self.query_seen.add(q)
            self.write("queries", {"input_sha256": q, "query": query, "output_sha256": o,
                                   "available": not bool(content["refusal"]), "refusal": content["refusal"]})
        return q, o

    def bundle(self, calls):
        counts = Counter((q, o, channel) for q, o, channel in calls)
        content = [{"input_sha256": q, "output_sha256": o, "channel": channel, "calls": n}
                   for (q, o, channel), n in sorted(counts.items())]
        key = digest(content)
        if key not in self.bundle_seen:
            self.bundle_seen.add(key)
            self.write("call_bundles", {"bundle_sha256": key, "queries": content})
        return {"bundle_sha256": key, "calls": len(calls), "unique_queries": len(counts)}

    def close(self):
        for f in self.files.values():
            f.close()


class LoggedWorld:
    def __init__(self, name, world, keys, task_hash, fold, log):
        self.name, self.world, self.task_hash, self.log = name, world, task_hash, log
        self.cache, self.calls = {}, []
        keys = list(keys)
        order = np.random.default_rng([SEED, fold, 1 if world.ft.classes else 0]).permutation(len(keys))
        if any(i == j for i, j in enumerate(order)):
            order = np.roll(np.arange(len(keys)), 1)
        self.mapping = dict(zip(keys, [keys[i] for i in order]))

    def forecast(self, key, h1, h2, compound, history=(), *, channel="selector"):
        from research.protocol_v2.contracts import C
        key = tuple(key)
        history = tuple((tuple(k), label) for k, label in history)
        query = {"task_input": self.task_hash, "forecast": self.name, "compound": compound,
                 "h1": h1, "h2": h2, "action": C.action_id(key), "history": history}
        q = digest(query)
        if q not in self.cache:
            source = self.mapping[key] if self.name == "permuted" else key
            hist = tuple((self.mapping[k], lab) for k, lab in history) if self.name == "permuted" else history
            fc = replace(self.world.forecast(source, h1, h2, compound, hist), action_identifier=C.action_id(key))
            content = {"branches": [{"hypothesis": b.hypothesis, "probabilities": dict(b.probabilities),
                                     "support": b.support} for b in fc.branches], "refusal": fc.refusal,
                       "version": fc.model_version, "basis": fc.basis, "action": fc.action_identifier}
            q, o = self.log.forecast(query, content)
            self.cache[q] = fc, o
        fc, o = self.cache[q]
        self.calls.append((q, o, channel))
        return fc


def selector(policy, audited):
    from maestro.acquisition import outcome_consequences
    from research.belief_planning import arms as BA, world as W
    from research.belief_planning.planner import plan_measurement, update_belief
    P, C, V = BA.P, BA.C, BA.V

    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        if policy == "fixed":
            return P.fixed(ctx, compound, h1, h2, executed, menu, remaining, setting, state)
        if not ctx.params.get("eliminates"):
            return None, {"reason": "registered_validator_cannot_eliminate", "policy": policy}
        real = tuple((tuple(s["key"]), W.label_of(s["outcome"])) for s in executed)
        by_id = {C.action_id(k): k for k in setting.keys}
        belief = {h1: 0.5, h2: 0.5}
        for i, (key, label) in enumerate(real):
            belief = update_belief(belief, audited.forecast(key, h1, h2, compound, real[:i], channel="belief"), label)
        done = [tuple(s["key"]) for s in executed]

        def legal(hyp):
            keys = done + [by_id[a] for a, _ in hyp]
            if len(keys) >= setting.max_measurements:
                return ()
            left = setting.budget_days - sum(setting.days(k) for k in keys)
            return tuple(P.make_action(k, h1, h2, setting) for k in P.legal_menu(setting, [{"key": k} for k in keys], left))

        if [a.identifier for a in legal(())] != [C.action_id(k) for k in menu]:
            raise AssertionError("planner_runner_menu_mismatch")

        def forecast(action, hyp):
            return audited.forecast(by_id[action.identifier], h1, h2, compound,
                                    real + tuple((by_id[a], label) for a, label in hyp))

        options = {}
        if policy == "anchored":
            fixed_key, _ = P.fixed(ctx, compound, h1, h2, executed, menu, remaining, setting, state)
            options = {"baseline": C.action_id(fixed_key) if fixed_key else None, "deviation_z": DEVIATION_Z}
        before = len(audited.calls)
        plan = plan_measurement((h1, h2), belief, legal, forecast, outcome_consequences(V.registered_rules(h1, h2)),
                                horizon=setting.max_measurements - len(executed), price=PRICE, **options)
        receipt = audited.log.bundle(audited.calls[before:])
        return by_id[plan.chosen] if plan.chosen else None, {"policy": policy, "reason": "belief_" + str(plan.reason),
              "evidence_kind": "model_prediction", "plan": plan.payload(), "forecast_receipt": receipt}
    return arm


def potential_coverage(compound, menu, frozen_row, unresolved):
    """Initial legal menu is a conservative superset of reachable downstream measurements."""
    from research.protocol_v2.contracts import C
    ids = [C.action_id(k) for k in menu]
    missing = [a for a in ids if a not in frozen_row["outcomes"] or
               frozen_row["outcomes"][a].get("lifecycle") not in ("measured_valid", "measured_qc_failed")]
    source = [a for a in ids if (compound, a) in unresolved]
    return {"potential_missing_results": missing, "potential_unresolved_sources": source,
            "point_identified": not (missing or source)}


def bounds(utility, coverage):
    return (float(utility), float(utility)) if coverage["point_identified"] else (-2.0, 1.0)


def observed_identity(record):
    return {"sequence": [s["action"] for s in record["steps"]], "steps":
            [{k: s[k] for k in ("action", "outcome", "qc", "eliminated")} for s in record["steps"]],
            **{k: record[k] for k in ("stop", "final", "measurements", "days")}}


def historic(task):
    cols = ["episode", "forecast", "policy", "steps", "stop", "final", "measurements", "days"]
    result = {}
    for chunk in pd.read_csv(R2 / "interventions" / (task + "_episodes.csv"), usecols=cols, chunksize=2000):
        for row in chunk[((chunk.forecast == "none") & (chunk.policy == "fixed")) |
                         ((chunk.forecast == "reference") & (chunk.policy == "baseline"))].to_dict("records"):
            row["steps"] = json.loads(row["steps"])
            name = "fixed_none" if row["policy"] == "fixed" else "baseline_reference"
            result[row["episode"], name] = observed_identity(row)
    return result


def quality(audited, ctx, compound, h1, h2, truth, menu, trace, frozen_row):
    from research.belief_planning import world as W
    from research.protocol_v2.contracts import C
    if audited is None or not ctx.params.get("eliminates"):
        return {name: None for prefix in ("all", "selected") for name in
                (prefix + "_ce", prefix + "_brier", prefix + "_accuracy")}

    def loss(fc, outcome):
        if fc.refusal or fc.branch_for(truth) is None:
            return None
        probabilities = dict(fc.branch_for(truth).probabilities)
        label = W.label_of(outcome)
        predicted = sorted(probabilities, key=lambda lab: (-probabilities[lab], lab))[0]
        return (-float(np.log(max(probabilities.get(label, 0), 1e-12))),
                sum((probabilities.get(lab, 0) - (lab == label)) ** 2 for lab in W.LABELS), float(predicted == label))

    values = {"all": [], "selected": []}
    for key in menu:
        entry = frozen_row["outcomes"].get(C.action_id(key))
        if entry and entry.get("outcome") in W.OBSERVED:
            item = loss(audited.forecast(key, h1, h2, compound, channel="quality_all"), entry["outcome"])
            if item is not None:
                values["all"].append(item)
    for i, step in enumerate(trace["steps"]):
        history = tuple((tuple(s["key"]), W.label_of(s["outcome"])) for s in trace["steps"][:i])
        item = loss(audited.forecast(step["key"], h1, h2, compound, history, channel="quality_selected"), step["outcome"])
        if item is not None:
            values["selected"].append(item)
    return {prefix + "_" + name: float(np.mean([v[i] for v in sample])) if sample else None
            for prefix, sample in values.items() for i, name in enumerate(("ce", "brier", "accuracy"))}


def run(out, stage):
    from threadpoolctl import threadpool_limits
    from research.protocol_v2 import contracts as K, runner as RN, tasks_v21 as V
    from research.belief_planning import arms as BA, world as W
    frozen = verify_freeze(out)
    if stage == "full" and not json.loads((out / "probe" / "gate.json").read_text())["passed"]:
        raise RuntimeError("probe_gate_failed")
    directory = out / stage
    directory.mkdir(exist_ok=False)
    source = pd.read_csv(R2 / "source_discrepancy_detail.csv")
    bad = source[(source.well_linkage_status == "unresolved_source_linkage") |
                 (source.plate_linkage_status == "unresolved_source_linkage")]
    unresolved = set(zip(bad.compound, bad.action))
    parity, records, checks = [], [], []
    log = ForecastLog(directory)
    episode_file = gzip.open(directory / "episodes.jsonl.gz", "xt", encoding="utf-8")
    try:
        with threadpool_limits(limits=1), patch.object(W.ReferenceWorld, "fit", side_effect=AssertionError("refit_forbidden")) as fit:
            for dataset, tier in TASKS:
                task = dataset + "_" + tier
                folds = json.loads((R2 / "interventions" / (task + "_freeze.json")).read_text())
                old = historic(task)
                for f in folds:
                    fold = f["fold"]
                    count = frozen["protocol"]["probe"].get(task, {}).get(str(fold)) if stage == "probe" else None
                    if stage == "probe" and count is None:
                        continue
                    with patch.object(V.C, "calibrate", return_value=restore(f["validator"])) as calibration:
                        data, ctx, setting, design = V.load(dataset, tier, fold)
                    training = V.training_compounds(ctx, fold)
                    heldout = set(data.compounds.loc[data.compounds.fold == fold, "compound"])
                    view = K.public_view(ctx, heldout, training_compounds=training, design=design)
                    episodes = V.episode_list(ctx, fold)
                    current = {"episodes": [list(e) for e in episodes], "menu": [list(k) for k in setting.keys],
                               "budget_days": setting.budget_days, "max_measurements": setting.max_measurements,
                               "fixed_order": [list(k) for k in setting.fixed_order], "training": list(training),
                               "days": {K.C.action_id(k): setting.days(k) for k in setting.keys},
                               "validator": finite_json(ctx.params),
                               "availability": {c: [list(k) for k in sorted(view.data.availability[c])] for c, *_ in episodes}}
                    failed = [k for k, v in current.items() if digest(v) != digest(f[k])]
                    if failed or K.public_view_problems(view, heldout):
                        raise AssertionError(f"frozen_public_contract_failed:{task}:{fold}:{failed}")
                    fp, pos = BA.fingerprints(view.data.compounds)
                    comp = view.data.compounds.drop_duplicates("compound").set_index("compound")
                    unit_kind = "component" if dataset == "l1000" else "skeleton"
                    world = W.ReferenceWorld(view.ft, view.params, training, fingerprints=fp, positions=pos,
                                             groups=comp[unit_kind].to_dict(), hyperparameters=f["reference_hyperparameters"])
                    task_hash = digest({"frozen_manifest": digest(frozen), "task": task, "fold": f})
                    frozen_rows = {(r["compound"], r["h1"], r["h2"]): r for r in
                                   read_rows(FROZEN / "tables" / f"{task}_{fold}.jsonl.gz")}
                    worlds = {name: LoggedWorld(name, world, setting.keys, task_hash, fold, log) for name in ("reference", "permuted")}
                    checks.append({"task": task, "fold": fold, "frozen_contract": True, "calibration_replaced": calibration.call_count,
                                   "reference_hyperparameters": world.hyperparameters, "training": len(training)})
                    for number, (compound, truth, decoy, h1, h2) in enumerate(episodes[:count] if count else episodes):
                        ep = f"{fold}|{compound}|{h1}|{h2}"
                        frozen_row = frozen_rows[compound, h1, h2]
                        local = RN.local_setting(setting, view.data.availability[compound])
                        initial_menu = BA.P.legal_menu(local, [], local.budget_days)
                        coverage = potential_coverage(compound, initial_menu, frozen_row, unresolved)
                        for arm_name, policy, forecast_name in ARMS:
                            audited = worlds.get(forecast_name)
                            if audited:
                                audited.calls = []
                            decisions = []
                            inner = selector(policy, audited)
                            def arm(*args):
                                start = len(audited.calls) if audited else 0
                                key, note = inner(*args)
                                decisions.append({"chosen": K.C.action_id(key) if key else None, "note": note,
                                                  "forecast_calls": len(audited.calls) - start if audited else 0})
                                return key, note
                            trace = RN.run_episode(arm_name, arm, view, ctx, compound, h1, h2, setting, design_menu=True)
                            if RN.audit_trace(trace, setting):
                                raise AssertionError("registered_trace_rule_failed")
                            score = K.score(trace, truth)
                            row = {"task": task, "episode": ep, "arm": arm_name, "fold": fold, "compound": compound,
                                   "independent_unit": str(frozen_row["unit"]), "chemical_unit_kind": unit_kind,
                                   "h1": h1, "h2": h2, "backend": "ReferenceWorld" if audited else None,
                                   "forecast_control": forecast_name, "backend_version": "belief-planning-1" if audited else None,
                                   "action_menu": [K.C.action_id(k) for k in initial_menu], "coverage": coverage,
                                   "decisions": decisions, "steps": trace["steps"], "offered": trace["offered"],
                                   "stop": trace["stop"], "final": score["final"], "correct": score["correct"], "wrong": score["wrong"],
                                   "undetermined": int(score["final"] == "undetermined"), "deferred": score["deferred"],
                                   "measurements": trace["measurements"], "days": trace["days"], "utility": score["utility"],
                                   "decided": score["decided"], "acted": int(bool(trace["steps"])),
                                   "forecast_entered_selector": any(d["forecast_calls"] for d in decisions),
                                   "forecast_entered_repair": False, "forecast_entered_final_evidence": False,
                                   **quality(audited, ctx, compound, h1, h2, truth, initial_menu, trace, frozen_row)}
                            row["utility_lo"], row["utility_hi"] = bounds(row["utility"], coverage)
                            row["forecast_receipt"] = log.bundle(audited.calls if audited else [])
                            row["forecast_available"] = bool(audited and any(not fc.refusal for fc, _ in audited.cache.values()))
                            row["forecast_refusals"] = sorted({fc.refusal for fc, _ in audited.cache.values() if fc.refusal}) if audited else []
                            if arm_name in ("fixed_none", "baseline_reference"):
                                same = observed_identity(row) == old[ep, arm_name]
                                parity.append({"task": task, "episode": ep, "arm": arm_name, "same": same})
                                if not same:
                                    raise AssertionError(f"observed_parity_failed:{task}:{ep}:{arm_name}")
                            episode_file.write(json.dumps(finite_json(row), allow_nan=False) + "\n")
                            scalar = {k: v for k, v in row.items() if not isinstance(v, (dict, list))}
                            scalar.update(sequence=json.dumps([s["action"] for s in trace["steps"]]),
                                          ranking=json.dumps([sorted(d["note"].get("plan", {}).get("evaluations", {}),
                                              key=lambda a: (-d["note"]["plan"]["evaluations"][a]["utility"], a)) for d in decisions]),
                                          point_identified=coverage["point_identified"],
                                          potential_unresolved_sources=json.dumps(coverage["potential_unresolved_sources"]),
                                          potential_missing_results=json.dumps(coverage["potential_missing_results"]))
                            records.append(scalar)
                        for audited in worlds.values():
                            audited.cache.clear()
                        world._cache.clear()
                        if number % 100 == 0:
                            print(stage, task, fold, number, "episodes completed", flush=True)
                    print(stage, task, fold, "complete", flush=True)
            gate = {"passed": bool(parity) and all(p["same"] for p in parity) and fit.call_count == 0,
                    "parity_checks": len(parity), "reference_fits": fit.call_count, "checks": checks,
                    "episode_arm_paths": len(records), "forecast_queries": len(log.query_seen),
                    "forecast_outputs": len(log.output_seen)}
    finally:
        episode_file.close()
        log.close()
    pd.DataFrame(records).to_csv(directory / "episode_metrics.csv", index=False, mode="x")
    save(directory / "parity.json", parity)
    save(directory / "gate.json", gate)
    if stage == "full":
        analyse(directory)
    save(directory / "run_record.json", {"command": [sys.executable, *sys.argv], "predeclared_sha256": file_hash(out / "predeclared.json"),
         "git_commit": frozen["git_commit"], "environment": frozen["environment"], "gate": gate,
         "outputs_sha256": {p.name: file_hash(p) for p in directory.iterdir() if p.is_file()}})
    print(stage, gate, flush=True)


def analyse(directory):
    frame = pd.read_csv(directory / "episode_metrics.csv")
    summaries, paths = {}, []
    metrics = ("correct", "wrong", "undetermined", "deferred", "measurements", "days", "utility", "utility_lo", "utility_hi",
               "all_ce", "all_brier", "all_accuracy", "selected_ce", "selected_brier", "selected_accuracy", "acted", "decided")
    for task, group in frame.groupby("task"):
        fixed = group[group.arm == "fixed_none"].set_index("episode")
        baseline = group[group.arm == "baseline_reference"].set_index("episode")
        summaries[task] = {"arms": {}, "comparison": {}, "physical_ci": "unavailable: independent plate/batch assignment unverified"}
        for name, arm in group.groupby("arm"):
            summaries[task]["arms"][name] = {m: paired_ci(arm, m) for m in metrics}
            sub = arm.set_index("episode").loc[fixed.index].copy()
            for anchor_name, anchor in (("fixed_none", fixed), ("baseline_reference", baseline)):
                joined = sub.copy()
                joined["sequence_changed"] = (sub.sequence != anchor.sequence).astype(int)
                joined["ranking_changed"] = (sub.ranking != anchor.ranking).astype(int)
                joined["first_changed"] = [int(json.loads(a)[:1] != json.loads(b)[:1]) for a, b in zip(sub.sequence, anchor.sequence)]
                joined["later_changed"] = [int(json.loads(a)[1:] != json.loads(b)[1:]) for a, b in zip(sub.sequence, anchor.sequence)]
                joined["terminal_changed"] = (sub.final != anchor.final).astype(int)
                joined["changed_same_terminal"] = joined.sequence_changed * (1 - joined.terminal_changed)
                for m in ("utility", "correct", "wrong", "deferred", "measurements", "days"):
                    joined["delta_" + m] = sub[m] - anchor[m]
                joined["delta_lo"] = sub.utility_lo - anchor.utility_hi
                joined["delta_hi"] = sub.utility_hi - anchor.utility_lo
                result = {m: paired_ci(joined, m) for m in
                          ("sequence_changed", "ranking_changed", "first_changed", "later_changed", "terminal_changed", "changed_same_terminal",
                           "delta_utility", "delta_correct", "delta_wrong", "delta_deferred", "delta_measurements", "delta_days", "delta_lo", "delta_hi")}
                changed = joined[joined.sequence_changed == 1]
                result["unchanged_terminal_given_changed_action"] = paired_ci(changed, "changed_same_terminal")
                result["matched_coverage"] = {}
                for cover in ("acted", "decided"):
                    common = sub[(sub[cover] == 1) & (anchor[cover] == 1)]
                    result["matched_coverage"][cover] = {"episodes": len(common), "fraction": len(common) / len(sub),
                        "interpretation": "Common observed coverage, descriptive outcome-conditioned comparison, not calibrated selective risk",
                        "candidate": {m: paired_ci(common, m) for m in ("correct", "wrong", "days", "measurements")},
                        "anchor": {m: paired_ci(anchor.loc[common.index], m) for m in ("correct", "wrong", "days", "measurements")}}
                summaries[task]["comparison"][name + "_vs_" + anchor_name] = result
                paths.extend({"task": task, "episode": ep, "arm": name, "anchor": anchor_name,
                              "independent_unit": row.independent_unit, "sequence_changed": row.sequence_changed,
                              "first_changed": row.first_changed, "later_changed": row.later_changed,
                              "terminal_changed": row.terminal_changed, "delta_utility": row.delta_utility,
                              "delta_lo": row.delta_lo, "delta_hi": row.delta_hi,
                              "point_identified": bool(row.point_identified)} for ep, row in joined.iterrows())
        true = group[group.arm == "anchored_reference"].set_index("episode").loc[fixed.index]
        perm = group[group.arm == "anchored_permuted"].set_index("episode").loc[fixed.index]
        contrast = true.copy()
        contrast["action_changed"] = (true.sequence != perm.sequence).astype(int)
        contrast["ranking_changed"] = (true.ranking != perm.ranking).astype(int)
        contrast["delta_utility"] = true.utility - perm.utility
        contrast["delta_lo"] = true.utility_lo - perm.utility_hi
        contrast["delta_hi"] = true.utility_hi - perm.utility_lo
        summaries[task]["true_vs_permuted_anchored"] = {m: paired_ci(contrast, m) for m in
                          ("action_changed", "ranking_changed", "delta_utility", "delta_lo", "delta_hi")}
        summaries[task]["factorial_interaction"] = "not identified: baseline/permuted was not a declared new arm; no full factorial claim"
    pd.DataFrame(paths).to_csv(directory / "path_attribution.csv", index=False, mode="x")
    save(directory / "task_summary.json", summaries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("freeze", "probe", "full"))
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    freeze(args.out) if args.stage == "freeze" else run(args.out, args.stage)


if __name__ == "__main__":
    main()
