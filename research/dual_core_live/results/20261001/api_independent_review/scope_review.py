"""Supplementary read-only audit of path parity, uncertainty correction and policy scope."""
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from agent.model_audit import ModelAuditAgent
from research.dual_core_live.support_contract import FORECAST_SUPPORT_CONTRACT, gate_supported_proposal, support_violations


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


checks, findings = 0, []


def check(value, name):
    global checks
    checks += 1
    if not value:
        findings.append(name)


def equal(a, b, name):
    check(np.isclose(a, b, rtol=1e-10, atol=1e-10), name)


def estimate(values):
    means = np.array([np.mean(items) for items in values.values()])
    samples = np.random.default_rng(20261001).choice(means, size=(2000, len(means)), replace=True).mean(axis=1)
    return means.mean(), np.quantile(samples, [.025, .975]).tolist()


original = ROOT / "outputs/dual_core_live_20261001/fixed_benchmark_v1"
recovered = ROOT / "outputs/dual_core_live_20261001/fixed_benchmark_recovered"
frozen = read(original / "predeclared.json")
biology = read(recovered / "biological_rows.json")
summary = read(recovered / "summary.json")
parity = read(recovered / "recovery_parity.json")
check(len(parity) == 15 and len({r["call_id"] for r in parity}) == 15, "cached_parity_population")
for item in parity:
    record = read(original / (item["call_id"] + ".json"))
    check(item["same_card"] and item["same_gate"], "parity_match_flags")
    check(item["original_card_sha256"] == digest(record["card"]), "parity_card_hash")
    check(item["original_proposal_sha256"] == digest(record["proposal"]), "parity_proposal_hash")
    check(item["original_jev_report_sha256"] == digest(record["jev"]), "parity_jev_hash")
    check(item["original_receipt_sha256"] == file_hash(original / (item["call_id"] + ".json")), "parity_receipt_hash")
for task in summary["biology"]:
    baseline = {r["id"]: r for r in biology if r["task"] == task and r["arm"] == "fixed_order"}
    for arm in ("one_step_forecast_optimizer", "deepseek_contract_gated"):
        rows = [r for r in biology if r["task"] == task and r["arm"] == arm]
        saved = summary["biology"][task]["paired_vs_fixed"][arm]
        lower, upper = defaultdict(list), defaultdict(list)
        for r in rows:
            lower[r["independent_unit"]].append(r["utility_lo"] - baseline[r["id"]]["utility_hi"])
            upper[r["independent_unit"]].append(r["utility_hi"] - baseline[r["id"]]["utility_lo"])
        equal(saved["partial_identification_bounds"][0], estimate(lower)[0], "partial_id_lower_equal_unit")
        equal(saved["partial_identification_bounds"][1], estimate(upper)[0], "partial_id_upper_equal_unit")
        for metric, stat in saved["other_paired_metrics"].items():
            groups = defaultdict(list)
            for r in rows:
                groups[r["independent_unit"]].append(r[metric] - baseline[r["id"]][metric])
            mean, interval = estimate(groups)
            equal(mean, stat["mean"], "paired_equal_unit_mean." + metric)
            check(stat["ci"] == interval, "paired_equal_unit_ci." + metric)
        changed = [r for r in rows if [s["action"] for s in r["trace"]["steps"]]
                   != [s["action"] for s in baseline[r["id"]]["trace"]["steps"]]]
        check(saved["action_changed"] == len(changed), "changed_sequences")
        check(saved["action_changed_terminal_same"] == sum(r["final"] == baseline[r["id"]]["final"] for r in changed), "changed_final_string_count")
        check(all(r["utility"] == baseline[r["id"]]["utility"] for r in changed), "changed_actions_no_terminal_utility_gain")
        common = [r for r in rows if r["decided"] and baseline[r["id"]]["decided"]]
        check(saved["matched_common_decided"]["n"] == len(common), "matched_common_decided_population")
        for metric in ("correct", "wrong", "measurements", "days"):
            label = "risk" if metric == "wrong" else metric
            equal(saved["matched_common_decided"]["arm_" + label], np.mean([r[metric] for r in common]), "common_selected." + metric)
            equal(saved["matched_common_decided"]["fixed_" + label], np.mean([baseline[r["id"]][metric] for r in common]), "common_fixed." + metric)
        check(len({r["independent_unit"] for r in rows}) == 6, "six_chemical_units_per_task")

correction = ROOT / "outputs/dual_core_live_20261001/uncertainty_correction"
corrected = read(correction / "corrected_summary.json")
receipt = read(correction / "correction_receipt.json")
check(receipt["input_sha256"] == file_hash(recovered / "summary.json"), "correction_original_hash")
check(receipt["output_sha256"] == file_hash(correction / "corrected_summary.json"), "correction_output_hash")
check(len(receipt["changes"]) == 4, "four_single_unit_intervals_removed")


def compare_tree(a, b, path=""):
    if isinstance(a, dict):
        check(set(a).issubset(b), "correction_preserves_keys:" + path)
        for key, value in a.items():
            if key == "ci" and a.get("units", 2) < 2:
                check(b[key] is None, "single_unit_ci_is_unidentified:" + path)
            else:
                compare_tree(value, b[key], path + "/" + key)
        allowed = {"uncertainty_status", "uncertainty_correction"}
        check(set(b) - set(a) <= allowed, "only_uncertainty_annotations_added:" + path)
    elif isinstance(a, list):
        check(len(a) == len(b), "correction_preserves_list_size:" + path)
        for index, (x, y) in enumerate(zip(a, b)):
            compare_tree(x, y, path + "/" + str(index))
    else:
        check(a == b, "correction_preserves_scalar:" + path)


compare_tree(summary, corrected)

scope_cases = []
with patch("agent.llm.urlopen", side_effect=AssertionError("network_forbidden")), patch("agent.decision_critic.urlopen", side_effect=AssertionError("network_forbidden")):
    auditor = ModelAuditAgent()
    for card in frozen["cards"]:
        card = deepcopy(card)
        affordable = [a["id"] for a in card["actions"] if a["cost"] <= card["remaining_budget"]
                      and a["id"] not in card["attempted_actions"]
                      and set(a.get("prerequisites", [])).issubset(card["qualified_prerequisites"])]
        proposal = {"action": affordable[0] if affordable else "defer", "terminal_authorized": False}
        before = digest({"card": card, "proposal": proposal})
        absent = gate_supported_proposal(card, proposal)
        report = auditor.review(card, proposal)
        explicit = gate_supported_proposal(card, proposal, FORECAST_SUPPORT_CONTRACT)
        check(absent["accepted"] and absent["action"] == proposal["action"], "absence_contract_keeps_no_forecast_policy")
        check(not report.findings, "formal_auditor_not_objective_optimizer")
        if card["family"] == "unsupported_forecast":
            check(explicit["accepted"] is False and explicit["action"] == "defer", "explicit_support_contract_declared_refusal")
        else:
            check(explicit["accepted"] and explicit["action"] == proposal["action"], "supported_policy_not_reranked")
        check(before == digest({"card": card, "proposal": proposal}), "support_and_auditor_do_not_mutate")
        check(set(report.payload()) == {"input_sha256", "proposal_sha256", "findings"}, "findings_no_replacement_or_execution_authority")
        scope_cases.append({"card_id": card["id"], "family": card["family"], "without_contract": absent,
                            "with_explicit_contract": explicit, "formal_audit_findings": len(report.findings)})
    card = deepcopy(frozen["cards"][0])
    supported = [a for a in card["actions"] if a["cost"] <= card["remaining_budget"]][0]
    supported["forecast_available"] = True
    supported["one_step_net_utility"] = .1
    card["actions"].append({"id": "legal_better", "cost": 1, "prerequisites": [], "forecast_available": True, "one_step_net_utility": .9})
    proposal = {"action": supported["id"], "terminal_authorized": False}
    check(gate_supported_proposal(card, proposal, FORECAST_SUPPORT_CONTRACT)["action"] == supported["id"], "helper_does_not_replace_with_optimal_action")
    unauthorized = {"action": supported["id"], "terminal_authorized": True}
    reviewed = auditor.review(card, unauthorized)
    check(any(f.code == "terminal_authority_claim" for f in reviewed.findings), "auditor_reports_authority_defect")
    check("action" not in reviewed.payload() and "repair" not in reviewed.payload(), "auditor_has_no_repair_payload")
    check(gate_supported_proposal(card, unauthorized, FORECAST_SUPPORT_CONTRACT)["action"] == "defer", "caller_contract_deferral_does_not_add_evidence")

result = {"status": "passed" if not findings else "findings", "created_utc": datetime.now(timezone.utc).isoformat(),
          "command": [sys.executable, *sys.argv], "checks": checks, "findings": findings,
          "script_sha256": file_hash(Path(__file__)), "support_helper_sha256": file_hash(ROOT / "research/dual_core_live/support_contract.py"),
          "auditor_sha256": file_hash(ROOT / "src/agent/model_audit.py"), "original_summary_sha256": file_hash(recovered / "summary.json"),
          "corrected_summary_sha256": file_hash(correction / "corrected_summary.json"), "scope_cases": scope_cases,
          "conclusion": "Optional support policy preserves no-forecast legality when absent, refuses only under an explicit forecast-required contract, and supplies no optimum/repaired measurement. Auditor findings remain report-only.",
          "limits": ["Support helper expects a validated registered task card, as declared; it does not replace full schema validation.",
                     "Passing these contract tests does not imply biological superiority or arbitrary model-bug detection."]}
with (OUT / "scope_receipt.json").open("x", encoding="utf-8", newline="\n") as handle:
    json.dump(result, handle, indent=2, allow_nan=False)
    handle.write("\n")
print(json.dumps({"status": result["status"], "checks": checks, "findings": findings}))
