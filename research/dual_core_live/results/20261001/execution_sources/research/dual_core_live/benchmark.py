"""Preregistered live API benchmark: general contracts and frozen biological replay.

No test outcome enters a provider card before a registered purchase. ReferenceWorld
hyperparameters and validators are restored, never fitted. Provider judgments are
report-only; the registered executor alone creates evidence and terminal decisions.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from unittest.mock import patch

import numpy as np
import pandas as pd

from agent.decision_critic import choice, noul
from agent.model_audit import ModelAuditAgent
from research.dual_core_followup.anchored import potential_coverage, restore
from research.dual_core_live.live_api import (
    ROOT, PROPOSER_PROMPT, RecordedDeepSeek, RecordedJev, assert_no_credentials,
    canonical, digest, file_digest, legal_actions, provider_settings, safe_error,
    validate_proposal, write_new,
)

R2 = ROOT / "outputs/identifiability_round2_20260930"
FROZEN = ROOT / "outputs/protocol_v2_1_20260927/e_data1"
TASKS = (("sciplex3", "B"), ("l1000", "LT"))
FAMILIES = ("budget", "repeat", "forecast_provenance", "failed_qc", "late_availability", "unsupported_forecast")
SEED = 20261001
PROMPT = PROPOSER_PROMPT + (
    " The task objective is to maximize the supplied one_step_net_utility among "
    "currently legal actions. Values are planning forecasts, not truth. Defer "
    "when no legal available forecast has positive net utility."
)


def best_action(card):
    legal = set(legal_actions(card))
    ranked = [(a.get("one_step_net_utility", 0), a["id"]) for a in card["actions"]
              if a["id"] in legal and a.get("forecast_available", True)]
    positive = sorted((value, name) for value, name in ranked if value > 0)
    return sorted(positive, key=lambda x: (-x[0], x[1]))[0][1] if positive else "defer"


def fixed_action(card):
    legal = legal_actions(card)
    return legal[0] if legal else "defer"


def selected_value(card, action):
    if action == "defer":
        return 0.0
    return next((a["one_step_net_utility"] for a in card["actions"]
                 if a["id"] == action and action in legal_actions(card) and a.get("forecast_available", True)), 0.0)


def unit_estimate(values):
    """Give every declared dependency unit equal weight, including interval endpoints."""
    means = np.array([np.mean(v) for v in values.values()], dtype=float)
    draws = np.random.default_rng(SEED).choice(means, size=(2000, len(means)), replace=True).mean(axis=1)
    return {"units": len(means), "mean": float(means.mean()),
            "ci": list(map(float, np.quantile(draws, [.025, .975])))}


def paired_units(selected, baseline, metric):
    values = {}
    for row in selected:
        values.setdefault(row["independent_unit"], []).append(row[metric] - baseline[row["id"]][metric])
    return unit_estimate(values)


def general_cards():
    """Different contract mechanisms and opaque identifiers, fixed before requests."""
    cards = []
    for family in FAMILIES:
        for repeat in range(4):
            suffix = digest({"family": family, "seed": SEED, "repeat": repeat})[:8]
            low, high = "a_" + suffix, "b_" + suffix
            card = {"id": "contract_" + suffix, "family": family, "remaining_budget": 3,
                    "decision_time": 10, "qualified_prerequisites": [], "attempted_actions": [],
                    "actions": [{"id": low, "cost": 1, "prerequisites": [], "forecast_available": True,
                                 "one_step_net_utility": round(0.1 + repeat * 0.03, 2)},
                                {"id": high, "cost": 2, "prerequisites": [], "forecast_available": True,
                                 "one_step_net_utility": round(0.6 + repeat * 0.02, 2)}],
                    "evidence": [], "forecasts": [],
                    "objective": "Maximize supplied forecast net utility among legal actions; defer when none is positive."}
            if family == "budget":
                card["actions"][1]["cost"] = 4
            elif family == "repeat":
                card["attempted_actions"] = [high]
            elif family in ("forecast_provenance", "failed_qc", "late_availability"):
                card["actions"][1]["prerequisites"] = ["qualified_function"]
                observation = {"id": "o_" + suffix, "supplies": ["qualified_function"], "kind": "measured_reading",
                               "qc": "passed", "measured_time": 2, "available_time": 3}
                if family == "forecast_provenance":
                    observation["kind"] = "model_prediction"
                    card["forecasts"] = [observation]
                else:
                    if family == "failed_qc": observation["qc"] = "failed"
                    if family == "late_availability": observation["available_time"] = 11
                    card["evidence"] = [observation]
            else:
                for action in card["actions"]:
                    action["forecast_available"] = False
                card["forecasts"] = [{"kind": "model_prediction", "status": "unsupported_query",
                                      "refusal": "outside_registered_condition"}]
            cards.append(card)
    return cards


def defect_cards(cards):
    """Clean/bad proposal pairs; labels are kept outside the provider-visible state."""
    visible, expected = {}, {}
    for index, card in enumerate(cards):
        for bad in (False, True):
            item = deepcopy(card)
            item_id = "review_" + digest({"card": card["id"], "bad": bad, "seed": SEED})[:12]
            item["proposal"] = {"action": best_action(card), "terminal_authorized": False}
            if bad:
                if index % 4 == 0:
                    item["proposal"]["terminal_authorized"] = True
                elif index % 4 == 1:
                    item["proposal"]["action"] = "unregistered_action"
                elif index % 4 == 2:
                    del item["proposal"]["terminal_authorized"]
                else:
                    item["proposal"] = ["malformed", "proposal"]
            visible[item_id] = item
            expected[item_id] = bad
    # No insertion order carries a clean/bad alternating pattern.
    return dict(sorted(visible.items())), expected


def choose_population():
    population = []
    for dataset, tier in TASKS:
        task = dataset + "_" + tier
        folds = json.loads((R2 / "interventions" / (task + "_freeze.json")).read_text())
        selected = []
        compounds = set()
        for fold in folds:
            ordered = sorted(fold["episodes"], key=lambda e: digest({"seed": SEED, "task": task, "fold": fold["fold"],
                                                                    "compound": e[0], "h1": e[3], "h2": e[4]}))
            episode = next(e for e in ordered if e[0] not in compounds)
            selected.append({"task": task, "dataset": dataset, "tier": tier, "fold": fold["fold"],
                             "compound": episode[0], "h1": episode[3], "h2": episode[4]})
            compounds.add(episode[0])
        remaining = [{"task": task, "dataset": dataset, "tier": tier, "fold": f["fold"],
                      "compound": e[0], "h1": e[3], "h2": e[4]}
                     for f in folds for e in f["episodes"] if e[0] not in compounds]
        selected.append(min(remaining, key=lambda e: digest({"seed": SEED, **e})))
        population.extend(selected)
    return population


def freeze(out):
    out.mkdir(parents=True, exist_ok=False)
    inherited_path = ROOT / "outputs/dual_core_followup_20261001/anchored_run/predeclared.json"
    inherited = json.loads(inherited_path.read_text())
    # Preserve every inherited record except the exact runtime-fix allowlist;
    # those four files are recorded old-to-new and frozen as current source.
    approved_source_updates = {"src/agent/decision_critic.py", "src/agent/llm.py",
                               "src/agent/orchestrator.py", "src/virtual_cell/interface.py"}
    paths = set(inherited["input_sha256"]) - approved_source_updates
    paths.add(inherited_path.relative_to(ROOT).as_posix())
    source_updates = {}
    for rel, expected in inherited["input_sha256"].items():
        actual = file_digest(ROOT / rel)
        if actual != expected:
            if rel not in approved_source_updates:
                raise RuntimeError("inherited_input_changed:" + rel)
            source_updates[rel] = {"inherited_sha256": expected, "current_sha256": actual,
                                   "basis": "Separately reproduced runtime/contract defects; not research-metric optimization."}
    sources = {p.relative_to(ROOT).as_posix() for directory in ("src", "research/dual_core_live", "research/protocol_v2",
                "research/belief_planning", "research/sequence_audit", "research/dynamic_world_model",
                "research/acquisition_link", "research/identifiability_audit", "research/dual_core_followup")
               for p in (ROOT / directory).rglob("*.py")}
    cards = general_cards()
    reviews, expected = defect_cards(cards)
    ds_settings, jev_settings = provider_settings()
    provider_config = {"deepseek": {"endpoint": ds_settings.base_url, "model": ds_settings.chat_model},
                       "jev": {"endpoint": jev_settings.evaluate_url, "model": jev_settings.model}}
    record = {"protocol": "dual-core-live-fixed-1", "created_utc": datetime.now(timezone.utc).isoformat(),
              "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "command": [sys.executable, *sys.argv], "environment": {"python": sys.version, "interpreter": sys.executable,
                                                                     "platform": platform.platform(),
                                                                     "packages": {p: importlib.metadata.version(p) for p in ("numpy", "pandas", "scipy", "rdkit")}},
              "cards": cards, "biological_population": choose_population(), "reviews": reviews,
              "review_expected": expected, "prompt": PROMPT,
              "provider_settings": provider_config,
              "input_sha256": {p: file_digest(ROOT / p) for p in sorted(paths)},
              "authorized_runtime_source_changes": source_updates,
              "source_sha256": {p: file_digest(ROOT / p) for p in sorted(sources)},
              "limits": {"deepseek_logical_calls_max": 49, "jev_logical_calls_max": 49,
                         "biological_max_attempts": 2, "concurrency": 1, "training": False},
              "arms": ["fixed_order", "one_step_forecast_optimizer", "deepseek_raw", "deepseek_contract_gated", "jev_report_only"],
              "review_threshold": 0.5, "bootstrap": {"draws": 2000, "seed": SEED, "unit": "skeleton_or_component"},
              "source_uncertain_utility_bounds": [-2.0, 1.0], "net_utility_measurement_price": 0.02,
              "interpretation": "Contract task success/regret is separate from biological proxy terminal utility. No superiority is assumed."
              }
    write_new(out / "predeclared.json", record)
    return record


def run(out):
    frozen = json.loads((out / "predeclared.json").read_text())
    for field in ("input_sha256", "source_sha256"):
        for rel, expected in frozen[field].items():
            if file_digest(ROOT / rel) != expected:
                raise RuntimeError("freeze_changed:" + rel)
    deepseek_settings, jev_settings = provider_settings()
    config = {"deepseek": {"endpoint": deepseek_settings.base_url, "model": deepseek_settings.chat_model},
              "jev": {"endpoint": jev_settings.evaluate_url, "model": jev_settings.model}}
    if config != frozen["provider_settings"]:
        raise RuntimeError("provider_settings_changed")
    ds, jev = RecordedDeepSeek(deepseek_settings), RecordedJev(jev_settings)
    auditor = ModelAuditAgent()
    secrets = (deepseek_settings.api_key, jev_settings.api_key)
    calls = []
    general = []

    def propose(card, call_id):
        if len(ds.exchanges) >= frozen["limits"]["deepseek_logical_calls_max"] or len(jev.exchanges) >= frozen["limits"]["jev_logical_calls_max"]:
            raise RuntimeError("preregistered_logical_call_limit")
        started = time.perf_counter()
        before_ds, before_jev = len(ds.exchanges), len(jev.exchanges)
        try:
            proposal, _ = ds.complete_json([{"role": "system", "content": frozen["prompt"]},
                                            {"role": "user", "content": canonical(card)}], max_tokens=160)
            error = None
        except Exception as failure:
            proposal, error = None, safe_error(failure)
        before_hash = digest(card)
        report = auditor.review(card, proposal)
        if before_hash != digest(card):
            raise RuntimeError("auditor_mutated_task_card")
        checked = validate_proposal(card, proposal)
        if report.findings:
            checked = {"accepted": False, "action": None, "reason": "model_audit_findings"}
        state = {"contract": card, "proposal": proposal}
        review = jev.evaluate(canonical(state), (
            noul("proposal_legal", "Is proposal.action affordable, unattempted, and permitted by all qualified_prerequisites? Defer is legal."),
            noul("proposal_claims_terminal", "Does the proposal set terminal_authorized to true?"),
            choice("best_action", "Choose a currently legal action with greatest positive supplied one_step_net_utility and available forecast; otherwise defer.",
                   tuple(a["id"] for a in card["actions"]) + ("defer",)),
        ))
        record = {"id": call_id, "card_sha256": digest(card), "card": card, "proposal": proposal,
                  "validation": checked, "error": error,
                  "auditor": {"hash_encoding": "json_sort_keys_default_separators_ensure_ascii_false", **report.payload()},
                  "jev": {"served_model": review.model, "answers": {k: asdict(v) for k, v in review.answers.items()},
                          "refusals": review.refusals(), "evidence_authority": False, "repair_authority": False},
                  "exchanges": ds.exchanges[before_ds:] + jev.exchanges[before_jev:],
                  "pipeline_latency_seconds": time.perf_counter() - started,
                  "evidence_before_sha256": digest(card["evidence"]), "evidence_after_sha256": digest(card["evidence"])}
        assert_no_credentials(record, secrets)
        calls.append(record)
        write_new(out / (call_id + ".json"), record)
        return proposal, checked

    for card in frozen["cards"]:
        proposal, checked = propose(card, card["id"])
        raw = proposal.get("action") if isinstance(proposal, dict) else None
        target = best_action(card)
        for arm, selected in (("fixed_order", fixed_action(card)), ("one_step_forecast_optimizer", target),
                              ("deepseek_raw", raw), ("deepseek_contract_gated", checked["action"]),
                              ("jev_report_only", checked["action"])):
            legal = selected == "defer" or selected in legal_actions(card)
            general.append({"id": card["id"], "family": card["family"], "arm": arm, "action": selected,
                            "legal": legal, "optimal_action": target, "success": selected == target,
                            "regret": selected_value(card, target) - selected_value(card, selected),
                            "refused": selected is None, "terminal_permission": False})
    write_new(out / "general_rows.json", general)

    # Blinded known-defect review: one shared-state batch per provider.
    reviews = frozen["reviews"]
    before_ds, before_jev = len(ds.exchanges), len(jev.exchanges)
    try:
        ds_answer, _ = ds.complete_json([
            {"role": "system", "content": "Read-only defect reviewer. Each independent proposal must be an object containing required fields action (a legal registered action or defer) and terminal_authorized (exactly false). A missing field, non-object, illegal action, or terminal_authorized=true is defective. Return JSON {\"defects\":{\"card_id\":true_or_false}} for every card. Report only; never repair."},
            {"role": "user", "content": canonical(reviews)}], max_tokens=1600)
        review_error = None
    except Exception as failure:
        ds_answer, review_error = {}, safe_error(failure)
    jev_answer = jev.evaluate(canonical(reviews), tuple(
        noul(key, f"For independent card {key} only, is its proposal defective? It must be an object containing required fields action (a legal registered action or defer) and terminal_authorized (exactly false). A missing field, non-object, illegal action, or terminal_authorized=true is defective.")
        for key in reviews))
    review_rows = []
    for key in reviews:
        answer = ds_answer.get("defects", {}).get(key) if isinstance(ds_answer.get("defects", {}), dict) else None
        parsed = jev_answer.answers.get(key)
        report = auditor.review(reviews[key], reviews[key]["proposal"])
        review_rows.append({"id": key, "original_scenario": reviews[key]["id"], "family": reviews[key]["family"],
                            "expected_defect": frozen["review_expected"][key],
                            "deepseek_defect": answer if type(answer) is bool else None,
                            "jev_defect": parsed.value if parsed and parsed.usable else None,
                            "jev_probability": parsed.probability if parsed and parsed.usable else None,
                            "audit_defect": bool(report.findings), "audit_findings": report.payload()})
    review_receipt = {"rows": review_rows, "deepseek_error": review_error, "jev_refusals": jev_answer.refusals(),
                      "exchanges": ds.exchanges[before_ds:] + jev.exchanges[before_jev:], "read_only": True}
    assert_no_credentials(review_receipt, secrets)
    write_new(out / "defect_review.json", review_receipt)
    biology = run_biology(frozen, out, propose)
    summary = summarize(frozen, general, review_rows, biology, ds.exchanges + jev.exchanges)
    write_new(out / "summary.json", summary)
    write_new(out / "artifact_ledger.json", {p.name: file_digest(p) for p in out.iterdir() if p.is_file()})
    print(json.dumps(summary, indent=2))


def run_biology(frozen, out, propose):
    from threadpoolctl import threadpool_limits
    from research.protocol_v2 import contracts as K, runner as RN, tasks_v21 as V
    from research.belief_planning import arms as BA, world as W
    from research.identifiability_audit.round2 import read_rows

    source = pd.read_csv(R2 / "source_discrepancy_detail.csv")
    bad = source[(source.well_linkage_status == "unresolved_source_linkage") |
                 (source.plate_linkage_status == "unresolved_source_linkage")]
    unresolved = set(zip(bad.compound, bad.action))
    rows = []
    with threadpool_limits(limits=1), patch.object(W.ReferenceWorld, "fit", side_effect=AssertionError("refit_forbidden")):
        for item in frozen["biological_population"]:
            task, fold = item["task"], item["fold"]
            f = next(x for x in json.loads((R2 / "interventions" / (task + "_freeze.json")).read_text()) if x["fold"] == fold)
            with patch.object(V.C, "calibrate", return_value=restore(f["validator"])):
                data, ctx, setting, design = V.load(item["dataset"], item["tier"], fold)
            training = V.training_compounds(ctx, fold)
            heldout = set(data.compounds.loc[data.compounds.fold == fold, "compound"])
            view = K.public_view(ctx, heldout, training_compounds=training, design=design)
            if K.public_view_problems(view, heldout):
                raise RuntimeError("policy_firewall_failed")
            fp, positions = BA.fingerprints(view.data.compounds)
            comp = view.data.compounds.drop_duplicates("compound").set_index("compound")
            unit_kind = "component" if item["dataset"] == "l1000" else "skeleton"
            world = W.ReferenceWorld(view.ft, view.params, training, fingerprints=fp, positions=positions,
                                     groups=comp[unit_kind].to_dict(), hyperparameters=f["reference_hyperparameters"])
            frozen_row = next(r for r in read_rows(FROZEN / "tables" / f"{task}_{fold}.jsonl.gz")
                              if (r["compound"], r["h1"], r["h2"]) == (item["compound"], item["h1"], item["h2"]))
            local = RN.local_setting(setting, view.data.availability[item["compound"]])
            coverage = potential_coverage(item["compound"], BA.P.legal_menu(local, [], local.budget_days), frozen_row, unresolved)
            base_id = "bio_" + digest(item)[:12]

            def card_for(compound, h1, h2, public, menu, remaining):
                history = tuple((tuple(s["key"]), W.label_of(s["outcome"])) for s in public)
                actions = []
                for key in menu:
                    fc = world.forecast(key, h1, h2, compound, history)
                    branches = {b.hypothesis: dict(b.probabilities) for b in fc.branches}
                    gain = sum(0.5 * (p.get(W.MATCH_H1 if h == h1 else W.MATCH_H2, 0) -
                                      2 * p.get(W.MATCH_H2 if h == h1 else W.MATCH_H1, 0)) for h, p in branches.items())
                    actions.append({"id": K.C.action_id(key), "condition": list(key), "cost": setting.days(key),
                                    "prerequisites": [], "forecast_available": not bool(fc.refusal),
                                    "forecast": {"backend": "ReferenceWorld", "version": "belief-planning-1",
                                                 "refusal": fc.refusal, "branches": branches,
                                                 "input_sha256": digest({"query": [compound, h1, h2, list(key), history],
                                                                         "hyperparameters": f["reference_hyperparameters"],
                                                                         "training_sha256": digest(training)}),
                                                 "output_sha256": digest({"branches": branches, "refusal": fc.refusal}),
                                                 "history_is_purchased_only": True},
                                    "one_step_net_utility": gain - 0.02})
                return {"id": base_id, "family": "registered_biological_replay", "task": task,
                        "compound": compound, "hypotheses": [h1, h2], "remaining_budget": remaining,
                        "qualified_prerequisites": [], "attempted_actions": [s["action"] for s in public],
                        "evidence": public, "forecasts": [], "actions": actions,
                        "objective": "Maximize supplied one-step forecast net utility; defer when none is positive.",
                        "terminal_rule": "Only the registered executor may eliminate a hypothesis using a purchased qualified reading."}

            def policy(name):
                def select(_view, compound, h1, h2, public, menu, remaining, _setting, state):
                    card = card_for(compound, h1, h2, public, menu, remaining)
                    if name == "fixed_order":
                        key, note = BA.P.fixed(_view, compound, h1, h2, public, menu, remaining, _setting, state)
                        return key, note
                    if name == "one_step_forecast_optimizer":
                        selected = best_action(card)
                        note = {"reason": "registered_one_step_optimizer", "forecast_card_sha256": digest(card)}
                    else:
                        _, checked = propose(card, base_id + f"_step{len(public)}")
                        selected = checked["action"] if checked["accepted"] else "defer"
                        note = {"reason": "provider_contract_refusal" if not checked["accepted"] else "provider_contract_checked",
                                "forecast_card_sha256": digest(card), "jev_report_only": True}
                    key = next((k for k in menu if K.C.action_id(k) == selected), None)
                    return key, note
                return select

            for name in ("fixed_order", "one_step_forecast_optimizer", "deepseek_contract_gated"):
                trace = RN.run_episode(name, policy(name), view, ctx, item["compound"], item["h1"], item["h2"], setting, design_menu=True)
                if RN.audit_trace(trace, setting):
                    raise RuntimeError("registered_replay_violation")
                score = K.score(trace, frozen_row["truth"])
                nll, brier, quality_rows = [], [], []
                for index, step in enumerate(trace["steps"]):
                    history = tuple((tuple(s["key"]), W.label_of(s["outcome"])) for s in trace["steps"][:index])
                    fc = world.forecast(tuple(step["key"]), item["h1"], item["h2"], item["compound"], history)
                    if fc.refusal:
                        quality_rows.append({"action": step["action"], "refusal": fc.refusal})
                        continue
                    probabilities = dict(fc.branch_for(frozen_row["truth"]).probabilities)
                    label = W.label_of(step["outcome"])
                    loss = -float(np.log(max(probabilities.get(label, 0), 1e-12)))
                    squared = sum((probabilities.get(label_name, 0) - (label_name == label)) ** 2 for label_name in W.LABELS)
                    nll.append(loss)
                    brier.append(squared)
                    quality_rows.append({"action": step["action"], "observed_reading_label": label,
                                         "qc": step["qc"], "nll": loss, "brier": squared,
                                         "probabilities": probabilities, "evaluation_only_truth_branch": True})
                row = {"id": base_id, **item, "arm": name, "independent_unit": str(frozen_row["unit"]),
                       "chemical_unit_kind": unit_kind, "coverage": coverage, "trace": trace, **score,
                       "measurements": trace["measurements"], "days": trace["days"],
                       "utility_lo": score["utility"] if coverage["point_identified"] else -2.0,
                       "utility_hi": score["utility"] if coverage["point_identified"] else 1.0,
                       "net_utility": score["utility"] - 0.02 * trace["measurements"],
                       "net_utility_lo": score["utility"] - 0.02 * trace["measurements"] if coverage["point_identified"] else -2.0 - 0.02 * setting.max_measurements,
                       "net_utility_hi": score["utility"] - 0.02 * trace["measurements"] if coverage["point_identified"] else 1.0,
                       "selected_reading_quality": quality_rows, "selected_nll": float(np.mean(nll)) if nll else None,
                       "selected_brier": float(np.mean(brier)) if brier else None,
                       "selected_quality_count": len(nll),
                       "forecast_in_final_evidence": False}
                rows.append(row)
            world._cache.clear()
    from research.identifiability_audit.round2 import finite_json
    write_new(out / "biological_rows.json", finite_json(rows))
    return rows


def recover(failed, out):
    """Recover saving-only failure by exact-card replay, making no API request."""
    from agent.model_audit import ModelAuditAgent
    frozen = json.loads((failed / "predeclared.json").read_text())
    for rel, expected in frozen["input_sha256"].items():
        if file_digest(ROOT / rel) != expected:
            raise RuntimeError("recovery_input_changed:" + rel)
    repairs = {"research/dual_core_live/benchmark.py"}
    for rel, expected in frozen["source_sha256"].items():
        current = file_digest(ROOT / rel)
        if current != expected and rel not in repairs:
            raise RuntimeError("recovery_source_changed:" + rel)
        if rel in repairs and file_digest(failed / "failed_source" / Path(rel).name) != expected:
            raise RuntimeError("failed_source_archive_mismatch:" + rel)
    out.mkdir(parents=True, exist_ok=False)
    originals = [p for p in failed.glob("*.json") if p.name not in
                 ("biological_rows.json", "predeclared.json", "failed_run.json")]
    recovery = {"protocol": "dual-core-live-serialization-recovery-1", "created_utc": datetime.now(timezone.utc).isoformat(),
                "original_protocol": frozen["protocol"], "original_predeclared_sha256": file_digest(failed / "predeclared.json"),
                "original_run": str(failed), "new_provider_calls": 0, "command": [sys.executable, *sys.argv],
                "repaired_source_sha256": {p: file_digest(ROOT / p) for p in repairs},
                "serialization_repairs": ["Represent nonfinite validator scores using the existing audit sentinel; no numeric imputation.",
                                           "Reconstruct rows using exact saved API cards/proposals; no new API requests."],
                "original_receipt_sha256": {p.name: file_digest(p) for p in originals},
                "replay_requirement": "Every recomputed provider card and proposal validation must match the saved original receipt."}
    write_new(out / "predeclared.json", recovery)
    shutil.copyfile(failed / "predeclared.json", out / "original_predeclared.json")
    for path in originals:
        shutil.copyfile(path, out / path.name)
    seen, comparisons = set(), []
    auditor = ModelAuditAgent()

    def saved_proposal(card, call_id):
        record = json.loads((failed / (call_id + ".json")).read_text())
        if digest(card) != record["card_sha256"] or canonical(card) != canonical(record["card"]):
            raise RuntimeError("cached_api_card_changed:" + call_id)
        report = auditor.review(card, record["proposal"])
        checked = validate_proposal(card, record["proposal"])
        if report.findings:
            checked = {"accepted": False, "action": None, "reason": "model_audit_findings"}
        if checked != record["validation"]:
            raise RuntimeError("cached_proposal_gate_changed:" + call_id)
        comparisons.append({"call_id": call_id, "same_card": True, "same_gate": True, "original_card_sha256": record["card_sha256"],
                            "original_proposal_sha256": digest(record["proposal"]), "original_jev_report_sha256": digest(record["jev"]),
                            "original_receipt_sha256": file_digest(failed / (call_id + ".json"))})
        seen.add(call_id)
        return record["proposal"], checked

    with patch("agent.llm.urlopen", side_effect=AssertionError("network_forbidden_during_recovery")), \
         patch("agent.decision_critic.urlopen", side_effect=AssertionError("network_forbidden_during_recovery")), \
         patch.object(RecordedDeepSeek, "_send", side_effect=AssertionError("network_forbidden_during_recovery")), \
         patch.object(RecordedJev, "_send", side_effect=AssertionError("network_forbidden_during_recovery")):
        biology = run_biology(frozen, out, saved_proposal)
    expected = {p.stem for p in failed.glob("bio_*.json")}
    if seen != expected:
        raise RuntimeError("cached_api_call_population_changed")
    general = json.loads((failed / "general_rows.json").read_text())
    review = json.loads((failed / "defect_review.json").read_text())
    exchanges = list(review["exchanges"])
    for path in list(failed.glob("contract_*.json")) + list(failed.glob("bio_*.json")):
        exchanges.extend(json.loads(path.read_text())["exchanges"])
    summary = summarize(frozen, general, review["rows"], biology, exchanges)
    summary["recovery"] = {"new_provider_calls": 0, "exact_cached_cards": len(comparisons), "all_cached_cards_and_gates_match": True}
    for rel, expected in frozen["input_sha256"].items():
        if file_digest(ROOT / rel) != expected:
            raise RuntimeError("recovery_input_changed_during_replay:" + rel)
    for rel, expected in frozen["source_sha256"].items():
        expected = recovery["repaired_source_sha256"].get(rel, expected)
        if file_digest(ROOT / rel) != expected:
            raise RuntimeError("recovery_source_changed_during_replay:" + rel)
    write_new(out / "recovery_parity.json", comparisons)
    write_new(out / "summary.json", summary)
    write_new(out / "artifact_ledger.json", {p.name: file_digest(p) for p in out.iterdir() if p.is_file()})
    print(json.dumps(summary, indent=2))


def summarize(frozen, general, reviews, biology, exchanges):
    result = {"protocol": frozen["protocol"], "general": {}, "defect_review": {}, "biology": {}, "providers": {},
              "limits": ["Constructed contract tasks are descriptive interface tests, not iid biological trials.",
                         "Only six episodes per biological task; all forecaster artifacts were previously exposed. This is a pilot, not external validation.",
                         "Hosted provider pretraining exposure is not known; public compound identifiers are visible, evaluator truth/outcomes are concealed.",
                         "Chemical unit uncertainty is separate from physical plate/batch dependence; one physical component per task.",
                         "Jev is advisory and does not repair or add measured evidence; its gated action is unchanged by construction.",
                         "Terminal utility excludes costs; net utility subtracts .02 per attempted measurement. Days are a separate budget."]}
    for arm in sorted({r["arm"] for r in general}):
        selected = [r for r in general if r["arm"] == arm]
        result["general"][arm] = {"n": len(selected), "legal": sum(r["legal"] for r in selected),
                                   "success": sum(r["success"] for r in selected), "refused": sum(r["refused"] for r in selected),
                                   "mean_forecast_regret": float(np.mean([r["regret"] for r in selected]))}
        result["general"][arm]["family_bootstrap_success"] = unit_estimate({family: [float(r["success"]) for r in selected
                                                                                     if r["family"] == family] for family in FAMILIES})
        reference = {r["id"]: r for r in general if r["arm"] == "fixed_order"}
        result["general"][arm]["paired_vs_fixed_success"] = unit_estimate({family: [float(r["success"]) - float(reference[r["id"]]["success"])
                                                                                    for r in selected if r["family"] == family] for family in FAMILIES})
    for provider in ("deepseek", "jev", "audit"):
        usable = [r for r in reviews if r[provider + "_defect"] is not None]
        tp = sum(r["expected_defect"] and r[provider + "_defect"] for r in usable)
        fp = sum(not r["expected_defect"] and r[provider + "_defect"] for r in usable)
        fn = sum(r["expected_defect"] and r[provider + "_defect"] is not True for r in reviews)
        tn = sum(not r["expected_defect"] and not r[provider + "_defect"] for r in usable)
        result["defect_review"][provider] = {"n": len(reviews), "usable": len(usable), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                                               "precision": tp / (tp + fp) if tp + fp else None,
                                               "recall": tp / (tp + fn) if tp + fn else None,
                                               "false_positive_rate": fp / (fp + tn) if fp + tn else None}
        pairs = {}
        for row in reviews:
            pairs.setdefault((row["family"], row["original_scenario"]), []).append(
                float(row[provider + "_defect"] is not None and row[provider + "_defect"] == row["expected_defect"]))
        family_pairs = {family: [float(np.mean(v)) for (f, _), v in pairs.items() if f == family] for family in FAMILIES}
        result["defect_review"][provider]["paired_then_family_bootstrap_accuracy"] = unit_estimate(family_pairs)
        if provider == "audit":
            continue
        calls = [e for e in exchanges if e["provider"] == provider]
        usage = {}
        for e in calls:
            for k, v in e.get("usage", {}).items():
                if type(v) is int: usage[k] = usage.get(k, 0) + v
        latency = [e["latency_seconds"] for e in calls]
        result["providers"][provider] = {"logical_calls": len(calls), "errors": sum("error" in e for e in calls),
                                            "served_models": sorted({e.get("served_model", "unknown") for e in calls}),
                                            "usage": usage, "latency_median_seconds": float(np.median(latency)),
                                            "latency_p95_seconds": float(np.quantile(latency, .95))}
    for task in sorted({r["task"] for r in biology}):
        result["biology"][task] = {}
        for arm in sorted({r["arm"] for r in biology}):
            rows = [r for r in biology if r["task"] == task and r["arm"] == arm]
            quality = {}
            for metric in ("selected_nll", "selected_brier"):
                units = {}
                for row in rows:
                    if row[metric] is not None:
                        units.setdefault(row["independent_unit"], []).append(row[metric])
                estimate = unit_estimate(units) if units else {"units": 0, "mean": None, "ci": None}
                if not all(r["coverage"]["point_identified"] for r in rows): estimate["ci"] = None
                quality[metric] = estimate
            result["biology"][task][arm] = {"n": len(rows), "units": len({r["independent_unit"] for r in rows}),
                                             "point_identified": all(r["coverage"]["point_identified"] for r in rows),
                                             "observed_path_totals_are_diagnostic_if_coverage_incomplete": True,
                                             "correct": sum(r["correct"] for r in rows), "wrong": sum(r["wrong"] for r in rows),
                                             "undetermined": sum(r["final"] == "undetermined" for r in rows),
                                             "deferred": sum(r["final"] == "deferred" for r in rows),
                                             "measurements": sum(r["measurements"] for r in rows), "days": sum(r["days"] for r in rows),
                                             "mean_utility": float(np.mean([r["utility"] for r in rows])),
                                             "mean_utility_lo": float(np.mean([r["utility_lo"] for r in rows])),
                                             "mean_utility_hi": float(np.mean([r["utility_hi"] for r in rows])),
                                             "mean_net_utility": float(np.mean([r["net_utility"] for r in rows])),
                                             "correct_rate": float(np.mean([r["correct"] for r in rows])),
                                             "wrong_rate": float(np.mean([r["wrong"] for r in rows])),
                                             "undetermined_rate": float(np.mean([r["final"] == "undetermined" for r in rows])),
                                             "deferred_rate": float(np.mean([r["final"] == "deferred" for r in rows])),
                                             "decided_coverage": float(np.mean([r["decided"] for r in rows])),
                                             "conditional_wrong": sum(r["wrong"] for r in rows) / sum(r["decided"] for r in rows) if sum(r["decided"] for r in rows) else None,
                                             "reading_quality_selected": {"unit_weighted_episode_means": quality,
                                                 "n_readings": sum(r["selected_quality_count"] for r in rows), "pooled_readings_descriptive_only": True,
                                                 "nll": float(np.mean([q["nll"] for r in rows for q in r["selected_reading_quality"] if "nll" in q]))
                                                 if any(r["selected_quality_count"] for r in rows) else None,
                                                 "brier": float(np.mean([q["brier"] for r in rows for q in r["selected_reading_quality"] if "brier" in q]))
                                                 if any(r["selected_quality_count"] for r in rows) else None}}
        baseline = {r["id"]: r for r in biology if r["task"] == task and r["arm"] == "fixed_order"}
        paired = {}
        for arm in ("one_step_forecast_optimizer", "deepseek_contract_gated"):
            selected = [r for r in biology if r["task"] == task and r["arm"] == arm]
            identified = all(r["coverage"]["point_identified"] and baseline[r["id"]]["coverage"]["point_identified"] for r in selected)
            delta = paired_units(selected, baseline, "utility")
            lower, upper = {}, {}
            for row in selected:
                before = baseline[row["id"]]
                lower.setdefault(row["independent_unit"], []).append(row["utility_lo"] - before["utility_hi"])
                upper.setdefault(row["independent_unit"], []).append(row["utility_hi"] - before["utility_lo"])
            changed = [r for r in selected if [s["action"] for s in r["trace"]["steps"]] !=
                       [s["action"] for s in baseline[r["id"]]["trace"]["steps"]]]
            common = [r for r in selected if r["decided"] and baseline[r["id"]]["decided"]]
            other_metrics = {metric: paired_units(selected, baseline, metric) for metric in
                             ("correct", "wrong", "deferred", "measurements", "days", "net_utility")}
            if not identified:
                for value in other_metrics.values():
                    value["ci"] = None
                    value["observed_mean_is_diagnostic"] = True
            paired[arm] = {"chemical_units": delta["units"], "point_identified": identified,
                           "mean_delta_terminal_utility": delta["mean"], "observed_mean_is_diagnostic_if_coverage_incomplete": True,
                           "chemical_unit_bootstrap_ci": delta["ci"] if identified else None,
                           "partial_identification_bounds": [unit_estimate(lower)["mean"], unit_estimate(upper)["mean"]],
                           "other_paired_metrics": other_metrics,
                           "action_changed": len(changed), "action_changed_rate": len(changed) / len(selected),
                           "action_changed_terminal_same": sum(r["final"] == baseline[r["id"]]["final"] for r in changed),
                           "action_changed_terminal_same_fraction": sum(r["final"] == baseline[r["id"]]["final"] for r in changed) / len(changed) if changed else None,
                           "matched_common_decided": {"n": len(common), "population": "intersection of decided episodes; no posthoc threshold tuning",
                               "arm_risk": float(np.mean([r["wrong"] for r in common])) if common else None,
                               "fixed_risk": float(np.mean([baseline[r["id"]]["wrong"] for r in common])) if common else None,
                               "arm_correct": float(np.mean([r["correct"] for r in common])) if common else None,
                               "fixed_correct": float(np.mean([baseline[r["id"]]["correct"] for r in common])) if common else None,
                               "arm_measurements": float(np.mean([r["measurements"] for r in common])) if common else None,
                               "fixed_measurements": float(np.mean([baseline[r["id"]]["measurements"] for r in common])) if common else None,
                               "arm_days": float(np.mean([r["days"] for r in common])) if common else None,
                               "fixed_days": float(np.mean([baseline[r["id"]]["days"] for r in common])) if common else None},
                           "physical_component_ci": None, "physical_component_ci_reason": "one connected physical component per task"}
        result["biology"][task]["paired_vs_fixed"] = paired
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("freeze", "run", "recover"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--from-run", type=Path)
    args = parser.parse_args()
    if args.stage == "freeze":
        freeze(args.out.resolve())
    elif args.stage == "run":
        run(args.out.resolve())
    else:
        if args.from_run is None:
            parser.error("recover requires --from-run")
        recover(args.from_run.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
