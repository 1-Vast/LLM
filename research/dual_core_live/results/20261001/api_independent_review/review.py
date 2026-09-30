"""Independent offline receipt audit; imports no experiment runner or provider client."""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import difflib
import gzip
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ORIGINAL = ROOT / "outputs/dual_core_live_20261001/fixed_benchmark_v1"
RECOVERED = ROOT / "outputs/dual_core_live_20261001/fixed_benchmark_recovered"
SEED = 20261001


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


checks = Counter()
findings = []


def check(condition, name, detail=None):
    checks[name] += 1
    if not condition:
        findings.append({"check": name, "detail": detail})


def near(actual, expected, name, detail=None):
    check(math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10), name,
          detail or {"actual": actual, "expected": expected})


def legal(card):
    return [a["id"] for a in card["actions"] if a["cost"] <= card["remaining_budget"]
            and a["id"] not in card["attempted_actions"]
            and set(a.get("prerequisites", [])).issubset(card["qualified_prerequisites"])]


def best(card):
    choices = [a for a in card["actions"] if a["id"] in legal(card)
               and a.get("forecast_available", True) and a.get("one_step_net_utility", 0) > 0]
    return min(choices, key=lambda a: (-a["one_step_net_utility"], a["id"]))["id"] if choices else "defer"


def gate(card, proposal):
    if not isinstance(proposal, dict):
        return {"accepted": False, "action": None, "reason": "proposal_not_object"}
    selected = proposal.get("action")
    if selected != "defer" and selected not in legal(card):
        return {"accepted": False, "action": None, "reason": "action_not_currently_legal"}
    if proposal.get("terminal_authorized") is not False:
        return {"accepted": False, "action": None, "reason": "proposal_cannot_authorize_terminal"}
    return {"accepted": True, "action": selected, "reason": "contract_checked"}


def bootstrap(groups):
    means = np.array([np.mean(values) for values in groups.values()], dtype=float)
    draws = np.random.default_rng(SEED).choice(means, size=(2000, len(means)), replace=True).mean(axis=1)
    return {"units": len(means), "mean": float(means.mean()),
            "ci": np.quantile(draws, [.025, .975]).tolist()}


def compare_estimate(actual, expected, name):
    check(actual["units"] == expected["units"], name + ".units")
    near(actual["mean"], expected["mean"], name + ".mean")
    for a, b in zip(actual["ci"], expected["ci"]):
        near(a, b, name + ".ci")


def forbidden_keys(value):
    forbidden = {"truth", "expected_defect", "review_expected", "score_a", "score_b",
                 "templates_a", "templates_b", "selected_reading_quality", "evaluation_only_truth_branch"}
    result = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden:
                result.append(key)
            result.extend(forbidden_keys(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(forbidden_keys(child))
    return result


def public_step(step):
    return {key: step[key] for key in ("key", "action", "outcome", "qc", "eliminated", "note")}


frozen = read(ORIGINAL / "predeclared.json")
recovery = read(RECOVERED / "predeclared.json")
summary = read(RECOVERED / "summary.json")
check(len(frozen["input_sha256"]) == 522, "input_population")
check(len(frozen["source_sha256"]) == 134, "source_population")
check(file_hash(ORIGINAL / "predeclared.json") == recovery["original_predeclared_sha256"], "original_prereg_hash")
check(file_hash(RECOVERED / "original_predeclared.json") == file_hash(ORIGINAL / "predeclared.json"), "original_prereg_byte_copy")
input_hashes = {}
for rel, expected in frozen["input_sha256"].items():
    actual = file_hash(ROOT / rel)
    input_hashes[rel] = actual
    check(actual == expected, "input_sha256", rel)
source_hashes = {}
for rel, expected in frozen["source_sha256"].items():
    actual = file_hash(ROOT / rel)
    source_hashes[rel] = actual
    approved = recovery["repaired_source_sha256"].get(rel, expected)
    check(actual == approved, "source_sha256", rel)
check(set(recovery["repaired_source_sha256"]) == {"research/dual_core_live/benchmark.py"}, "serialization_only_source_allowlist")
archived = ORIGINAL / "failed_source/benchmark.py"
check(file_hash(archived) == frozen["source_sha256"]["research/dual_core_live/benchmark.py"], "original_benchmark_archive_hash")
old_text = archived.read_text(encoding="utf-8")
new_text = (ROOT / "research/dual_core_live/benchmark.py").read_text(encoding="utf-8")
old_tree, new_tree = ast.parse(old_text), ast.parse(new_text)
old_functions = {n.name: n for n in old_tree.body if isinstance(n, ast.FunctionDef)}
new_functions = {n.name: n for n in new_tree.body if isinstance(n, ast.FunctionDef)}
changed_functions = [name for name in old_functions if ast.dump(old_functions[name], include_attributes=False)
                     != ast.dump(new_functions[name], include_attributes=False)]
check(set(changed_functions) == {"run_biology", "main"}, "serialization_source_changed_functions", changed_functions)
check(set(new_functions) - set(old_functions) == {"recover"}, "serialization_source_added_functions")
old_biology = ast.get_source_segment(old_text, old_functions["run_biology"])
new_biology = ast.get_source_segment(new_text, new_functions["run_biology"])
normalized = new_biology.replace("    from research.identifiability_audit.round2 import finite_json\n", "").replace(
    'write_new(out / "biological_rows.json", finite_json(rows))', 'write_new(out / "biological_rows.json", rows)')
check(normalized == old_biology, "biological_semantics_unchanged_except_finite_serialization")
print("Hashed 522 inputs and 134 sources; checked archived-source change scope.", flush=True)

copied = {}
for name, expected in recovery["original_receipt_sha256"].items():
    original_hash, recovered_hash = file_hash(ORIGINAL / name), file_hash(RECOVERED / name)
    check(original_hash == expected == recovered_hash, "original_receipt_exact_copy", name)
    copied[name] = recovered_hash
ledger = read(RECOVERED / "artifact_ledger.json")
for name, expected in ledger.items():
    check(file_hash(RECOVERED / name) == expected, "recovered_artifact_ledger", name)
check(recovery["new_provider_calls"] == 0, "recovery_declares_no_calls")

receipts = [read(p) for p in sorted(ORIGINAL.glob("contract_*.json"))]
bio_receipts = {p.stem: read(p) for p in ORIGINAL.glob("bio_*.json")}
review = read(ORIGINAL / "defect_review.json")
check(len(receipts) == 24 and len(bio_receipts) == 15 and len(review["rows"]) == 48, "request_population_counts")
exchanges = review["exchanges"] + [e for r in receipts + list(bio_receipts.values()) for e in r["exchanges"]]
counts = Counter(e["provider"] for e in exchanges)
check(counts == {"deepseek": 40, "jev": 40}, "formal_provider_exchange_count", dict(counts))
for record in receipts + list(bio_receipts.values()):
    card = record["card"]
    check(digest(card) == record["card_sha256"], "card_hash", record["id"])
    check(gate(card, record["proposal"]) == record["validation"], "independent_original_proposal_gate", record["id"])
    check(record["evidence_before_sha256"] == record["evidence_after_sha256"] == digest(card["evidence"]), "unchanged_evidence", record["id"])
    check(record["jev"]["evidence_authority"] is False and record["jev"]["repair_authority"] is False,
          "jev_report_only", record["id"])
    check(not forbidden_keys(card), "card_no_hidden_evaluator_fields", record["id"])
    for e in record["exchanges"]:
        if e["provider"] == "deepseek":
            check(e["request"]["messages"][0]["content"] == frozen["prompt"], "original_prompt_unchanged", record["id"])
            check(json.loads(e["request"]["messages"][1]["content"]) == card, "deepseek_receives_exact_card", record["id"])
            returned = json.loads(e["response"]["choices"][0]["message"]["content"])
            check(returned == record["proposal"], "proposal_matches_provider_output", record["id"])
        else:
            state = json.loads(e["request"]["state"])
            check(state == {"contract": card, "proposal": record["proposal"]}, "jev_receives_exact_public_state", record["id"])
for e in exchanges:
    check(digest(e["request"]) == e["request_sha256"], "request_sha256")
    check(digest(e["response"]) == e["response_sha256"], "response_sha256")
    check(e["served_model"] == e["response"]["model"], "served_model_record")
    check(not forbidden_keys(e["request"]), "request_no_hidden_top_level_fields")
for e in review["exchanges"]:
    visible = json.loads(e["request"]["messages"][1]["content"] if e["provider"] == "deepseek" else e["request"]["state"])
    check(visible == frozen["reviews"] and not forbidden_keys(visible), "review_blinded_visible_cards")
for provider in counts:
    subset = [e for e in exchanges if e["provider"] == provider]
    usage = Counter()
    for e in subset:
        usage.update({k: v for k, v in e["usage"].items() if type(v) is int})
    saved = summary["providers"][provider]
    check(saved["logical_calls"] == len(subset) and saved["usage"] == dict(usage), "provider_calls_usage_recomputed", provider)
    near(saved["latency_median_seconds"], float(np.median([e["latency_seconds"] for e in subset])), "provider_latency_median")
    near(saved["latency_p95_seconds"], float(np.quantile([e["latency_seconds"] for e in subset], .95)), "provider_latency_p95")
    check(saved["errors"] == sum("error" in e for e in subset), "provider_error_count")
smoke = [read(p) for p in (ROOT / "outputs/dual_core_live_20261001/api_smoke").glob("*.json")]
smoke_exchanges = [e for item in smoke if isinstance(item, dict) for e in item.get("exchanges", [])]
smoke_counts = Counter(e["provider"] for e in smoke_exchanges)
check(smoke_counts == {"deepseek": 2, "jev": 2}, "separate_smoke_count", dict(smoke_counts))
print("Checked 80 formal exchanges, 39 action cards, blinded 48-card review and unchanged evidence.", flush=True)

general = read(RECOVERED / "general_rows.json")
general_cards = {card["id"]: card for card in frozen["cards"]}
general_receipts = {r["id"]: r for r in receipts}
check(len(general) == 120, "general_arm_rows")
for row in general:
    card, record = general_cards[row["id"]], general_receipts[row["id"]]
    selected = {"fixed_order": (legal(card) or ["defer"])[0], "one_step_forecast_optimizer": best(card),
                "deepseek_raw": record["proposal"]["action"], "deepseek_contract_gated": record["validation"]["action"],
                "jev_report_only": record["validation"]["action"]}[row["arm"]]
    check(row["action"] == selected and row["success"] == (selected == best(card)), "general_independent_action_success")
    check(row["legal"] == (selected == "defer" or selected in legal(card)), "general_independent_legality")
    def value(action):
        return next((a["one_step_net_utility"] for a in card["actions"] if a["id"] == action
                     and action in legal(card) and a.get("forecast_available", True)), 0)
    near(row["regret"], value(best(card)) - value(selected), "general_independent_regret")
for arm, saved in summary["general"].items():
    rows = [r for r in general if r["arm"] == arm]
    check(saved["n"] == len(rows) and saved["success"] == sum(r["success"] for r in rows)
          and saved["legal"] == sum(r["legal"] for r in rows), "general_summary_counts", arm)
    families = {family: [float(r["success"]) for r in rows if r["family"] == family] for family in frozen["bootstrap"].get("families", sorted({r["family"] for r in rows}))}
    # Preserve preregistered family order, because draw indices make the exact CI order-sensitive.
    ordered = {family: families[family] for family in ("budget", "repeat", "forecast_provenance", "failed_qc", "late_availability", "unsupported_forecast")}
    compare_estimate(saved["family_bootstrap_success"], bootstrap(ordered), "general_family_ci")
for row in review["rows"]:
    visible = frozen["reviews"][row["id"]]
    proposal = visible["proposal"]
    expected = (not isinstance(proposal, dict) or not isinstance(proposal.get("action"), str)
                or proposal.get("terminal_authorized") is not False
                or (proposal.get("action") != "defer" and proposal.get("action") not in legal(visible)))
    check(expected == row["expected_defect"] == frozen["review_expected"][row["id"]], "known_defect_independent_label")
for provider, saved in summary["defect_review"].items():
    tp = fp = fn = tn = 0
    paired = defaultdict(list)
    for row in review["rows"]:
        answer, truth = row[provider + "_defect"], row["expected_defect"]
        tp += bool(truth and answer is True)
        fp += bool(not truth and answer is True)
        fn += bool(truth and answer is not True)
        tn += bool(not truth and answer is False)
        paired[(row["family"], row["original_scenario"])].append(float(answer is not None and answer == truth))
    check((tp, fp, fn, tn) == tuple(saved[k] for k in ("tp", "fp", "fn", "tn")), "defect_confusion_recomputed", provider)
    family_pairs = {f: [float(np.mean(v)) for (family, _), v in paired.items() if family == f]
                    for f in ("budget", "repeat", "forecast_provenance", "failed_qc", "late_availability", "unsupported_forecast")}
    compare_estimate(saved["paired_then_family_bootstrap_accuracy"], bootstrap(family_pairs), "defect_paired_family_ci")

biology = read(RECOVERED / "biological_rows.json")
check(len(biology) == 36 and len({r["id"] for r in biology}) == 12, "biological_population")
check(set(Counter((r["task"], r["arm"]) for r in biology).values()) == {6}, "biological_per_arm_count")
frozen_rows = {}
for task, fold in sorted({(r["task"], r["fold"]) for r in biology}):
    wanted = {(r["compound"], r["h1"], r["h2"]) for r in biology if r["task"] == task and r["fold"] == fold}
    table = ROOT / "outputs/protocol_v2_1_20260927/e_data1/tables" / f"{task}_{fold}.jsonl.gz"
    with gzip.open(table, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            key = row["compound"], row["h1"], row["h2"]
            if key in wanted:
                frozen_rows[task, fold, *key] = row
                wanted.remove(key)
            if not wanted:
                break
    check(not wanted, "frozen_truth_rows_found", {"task": task, "fold": fold, "missing": list(wanted)})
unresolved = set()
with (ROOT / "outputs/identifiability_round2_20260930/source_discrepancy_detail.csv").open(encoding="utf-8", newline="") as handle:
    for r in csv.DictReader(handle):
        if "unresolved_source_linkage" in (r["well_linkage_status"], r["plate_linkage_status"]):
            unresolved.add((r["compound"], r["action"]))
folds = {task: {f["fold"]: f for f in read(ROOT / "outputs/identifiability_round2_20260930/interventions" / f"{task}_freeze.json")}
         for task in {r["task"] for r in biology}}
joins = []
labels = {"eliminate_a": "profile_matches_h2", "eliminate_b": "profile_matches_h1",
          "ambiguous": "profile_unresolved", "undetected": "no_detectable_response", "qc_failed": "quality_failed"}
for row in biology:
    trace = row["trace"]
    original = frozen_rows[row["task"], row["fold"], row["compound"], row["h1"], row["h2"]]
    f = folds[row["task"]][row["fold"]]
    check(row["truth"] == original["truth"] and row["independent_unit"] == str(original["unit"]), "frozen_truth_unit_join")
    check("truth" not in trace and row["forecast_in_final_evidence"] is False, "truth_free_trace")
    check(len(trace["steps"]) == row["measurements"] == trace["measurements"] <= 2, "attempt_budget_count")
    check(trace["days"] == row["days"] <= f["budget_days"], "day_budget")
    remaining = set(trace["remaining"])
    truth = row["truth"]
    other = row["h2"] if truth == row["h1"] else row["h1"]
    final = "deferred" if not trace["steps"] else "correct" if remaining == {truth} else "wrong" if remaining == {other} else "exhausted" if not remaining else "undetermined"
    utility = 1 if final == "correct" else -2 if final in ("wrong", "exhausted") else 0
    check(final == row["final"] and utility == row["utility"], "terminal_score_recomputed")
    near(row["net_utility"], utility - .02 * row["measurements"], "cost_per_attempt")
    initial = trace["offered"][0]
    missing = [a for a in initial if a not in original["outcomes"] or original["outcomes"][a]["lifecycle"] not in ("measured_valid", "measured_qc_failed")]
    bad_source = [a for a in initial if (row["compound"], a) in unresolved]
    check(row["coverage"] == {"potential_missing_results": missing, "potential_unresolved_sources": bad_source,
                               "point_identified": not (missing or bad_source)}, "independent_coverage_recomputed")
    low, high = (utility, utility) if not (missing or bad_source) else (-2, 1)
    check((row["utility_lo"], row["utility_hi"]) == (low, high), "predeclared_utility_bounds")
    for i, step in enumerate(trace["steps"]):
        saved = original["outcomes"][step["action"]]
        check((step["outcome"], step["lifecycle"], step["readout"]) == (saved["outcome"], saved["lifecycle"], saved["readout"]), "purchased_reading_matches_frozen_executor")
        check(step["action"] in trace["offered"][i], "selected_action_in_offered_menu")
        if not step["qc"]:
            check(step["eliminated"] == (trace["steps"][i-1]["eliminated"] if i else []), "failed_qc_no_evidence_update")
    quality = [q for q in row["selected_reading_quality"] if "nll" in q]
    for q in quality:
        p = q["probabilities"]
        near(sum(p.values()), 1, "selected_quality_distribution_sum")
        near(q["nll"], -math.log(max(p.get(q["observed_reading_label"], 0), 1e-12)), "reading_nll_recomputed")
        near(q["brier"], sum((v - (k == q["observed_reading_label"])) ** 2 for k, v in p.items()), "reading_brier_recomputed")
    check(row["selected_quality_count"] == len(quality), "selected_reading_count")
    if quality:
        near(row["selected_nll"], np.mean([q["nll"] for q in quality]), "episode_mean_nll")
        near(row["selected_brier"], np.mean([q["brier"] for q in quality]), "episode_mean_brier")
    if row["arm"] == "deepseek_contract_gated":
        calls = sorted((key, record) for key, record in bio_receipts.items() if key.startswith(row["id"] + "_step"))
        for key, record in calls:
            index = int(key.rsplit("step", 1)[1])
            card = record["card"]
            check(card["evidence"] == [public_step(s) for s in trace["steps"][:index]], "no_unpurchased_readings_in_card", key)
            check(card["attempted_actions"] == [s["action"] for s in trace["steps"][:index]], "card_purchased_action_history", key)
            check([a["id"] for a in card["actions"]] == trace["offered"][index], "card_menu_exact", key)
            near(card["remaining_budget"], f["budget_days"] - sum(s["key"] and next(a["cost"] for a in bio_receipts[row["id"] + "_step0"]["card"]["actions"] if a["id"] == s["action"]) for s in trace["steps"][:index]), "card_budget_exact")
            selected = record["validation"]["action"]
            if index < len(trace["steps"]):
                check(selected == trace["steps"][index]["action"], "api_proposal_trace_join", key)
            else:
                check(selected == "defer", "api_deferral_trace_join", key)
            for action in card["actions"]:
                forecast = action["forecast"]
                history = [[s["key"], labels[s["outcome"]] if s["qc"] else "quality_failed"] for s in trace["steps"][:index]]
                query = {"query": [row["compound"], row["h1"], row["h2"], action["condition"], history],
                         "hyperparameters": f["reference_hyperparameters"], "training_sha256": digest(f["training"])}
                check(digest(query) == forecast["input_sha256"], "forecast_query_input_hash", key)
                check(digest({"branches": forecast["branches"], "refusal": forecast["refusal"]}) == forecast["output_sha256"], "forecast_output_hash", key)
            joins.append({"id": key, "card_hash": record["card_sha256"], "proposal_hash": digest(record["proposal"]),
                          "jev_hash": digest(record["jev"]), "purchased_steps": index})
check(len(joins) == 15, "all_15_cached_cards_joined")
for task in summary["biology"]:
    for arm in ("fixed_order", "one_step_forecast_optimizer", "deepseek_contract_gated"):
        rows = [r for r in biology if r["task"] == task and r["arm"] == arm]
        saved = summary["biology"][task][arm]
        for field in ("correct", "wrong", "measurements", "days"):
            near(saved[field], sum(r[field] for r in rows), "biological_task_totals." + field)
        for field in ("undetermined", "deferred"):
            check(saved[field] == sum(r["final"] == field for r in rows), "biological_task_terminal_totals")
        for metric in ("selected_nll", "selected_brier"):
            groups = defaultdict(list)
            for r in rows:
                if r[metric] is not None:
                    groups[r["independent_unit"]].append(r[metric])
            if groups:
                compare_estimate(saved["reading_quality_selected"]["unit_weighted_episode_means"][metric], bootstrap(groups), "equal_unit_reading_quality")
    fixed = {r["id"]: r for r in biology if r["task"] == task and r["arm"] == "fixed_order"}
    for arm in ("one_step_forecast_optimizer", "deepseek_contract_gated"):
        rows = [r for r in biology if r["task"] == task and r["arm"] == arm]
        saved = summary["biology"][task]["paired_vs_fixed"][arm]
        groups = defaultdict(list)
        for r in rows:
            groups[r["independent_unit"]].append(r["utility"] - fixed[r["id"]]["utility"])
        estimate = bootstrap(groups)
        near(saved["mean_delta_terminal_utility"], estimate["mean"], "chemical_unit_paired_utility")
        check(saved["chemical_unit_bootstrap_ci"] == estimate["ci"], "chemical_unit_paired_ci")
        check(saved["physical_component_ci"] is None, "physical_ci_unidentified")
print("Checked 36 biological scores, all 15 cached path joins, reading losses, bounds and dependency weighting.", flush=True)

receipt = {"status": "passed" if not findings else "findings", "created_utc": datetime.now(timezone.utc).isoformat(),
           "command": [sys.executable, *sys.argv], "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
           "environment": {"python": sys.version, "interpreter": sys.executable, "platform": platform.platform(), "numpy": np.__version__},
           "script_sha256": file_hash(Path(__file__)), "original_prereg_sha256": file_hash(ORIGINAL / "predeclared.json"),
           "recovery_prereg_sha256": file_hash(RECOVERED / "predeclared.json"), "original_benchmark_sha256": file_hash(archived),
           "recovery_benchmark_sha256": file_hash(ROOT / "research/dual_core_live/benchmark.py"),
           "input_sha256": input_hashes, "source_sha256_at_review": source_hashes, "copied_receipt_sha256": copied,
           "recovered_ledger_sha256": file_hash(RECOVERED / "artifact_ledger.json"), "summary_sha256": file_hash(RECOVERED / "summary.json"),
           "check_counts": dict(checks), "checks": sum(checks.values()), "findings": findings,
           "formal_provider_calls": dict(counts), "separate_smoke_calls": dict(smoke_counts), "cached_biological_joins": joins,
           "limitations": ["No network calls were made; logical recorded exchanges cannot prove independent server-side request counts.",
                           "No experiment runner or provider client was imported; numeric scores were independently recomputed from frozen traces.",
                           "Point identification is local to reachable registered menus and existing source audit, not external biological validity.",
                           "All six chemical units per task are previously exposed; one physical component prevents physical-cluster intervals.",
                           "Availability-objective adherence is distinct from formal legality; original unsupported-family failures remain preserved."]}
with (OUT / "receipt.json").open("x", encoding="utf-8", newline="\n") as handle:
    json.dump(receipt, handle, indent=2, ensure_ascii=False, allow_nan=False)
    handle.write("\n")
print(json.dumps({"status": receipt["status"], "checks": receipt["checks"], "findings": findings}, indent=2), flush=True)
