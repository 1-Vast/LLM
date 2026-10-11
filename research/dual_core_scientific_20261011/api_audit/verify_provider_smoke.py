"""Read-only artifact audit: no provider call or model response is generated."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
sys.path.insert(0, str(WORKSPACE / "src"))
from agent.llm import MAESTROSettings
from maestro.acquisition import OutcomeBranch, OutcomeForecast, outcome_consequences
from maestro.decision_value_policy import (
    FrozenDecisionValuePolicy, decision_hypotheses_binding, decision_interpretation_binding,
)
from maestro.models import (
    BiologicalQuantity, DevelopmentAction, EvidenceAction, EvidenceActionKind, EvidenceKind, EvidenceScope,
    FunctionalInterventionProfile, MechanismHypothesis,
)
from maestro.outcome import OutcomeRule


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    definitions = [("initial_live_historical", "LATEST.json", False, False, 3, 0),
                   ("hypothesis_bound_replay_historical", "LATEST_REPLAY.json", True, False, 0, 3),
                   ("hypothesis_bound_live_historical", "LATEST_FINAL.json", True, False, 1, 0),
                   ("final_interpretation_bound_replay", "LATEST_INTERPRETATION_REPLAY.json", True, True, 0, 3)]
    errors = []
    authenticated_calls = []
    runs = []
    for label, pointer, hypotheses_bound, interpretation_bound, expected_calls, expected_replays in definitions:
        results_path = HERE / read_json(HERE / pointer)["results"]
        result = read_json(results_path)
        directory = results_path.parent
        protocol = read_json(directory / "PROTOCOL.json")
        if digest(directory / "PROTOCOL.json") != result["protocol_sha256"]:
            errors.append(label + ": protocol hash mismatch")
        if result["actual_http_requests"] != expected_calls or result.get("offline_provider_response_replays", 0) != expected_replays:
            errors.append(label + ": call/replay accounting mismatch")
        if not result["all_scenarios_pass"]:
            errors.append(label + ": recorded scenario failure")
        bound_hypotheses = tuple(MechanismHypothesis(
            item["identifier"], item["description"], DevelopmentAction(item["proposed_action"]), item["causal_factor"])
            for item in protocol["hypothesis_definitions"])
        expected_binding = decision_hypotheses_binding(bound_hypotheses)
        if hypotheses_bound and protocol.get("hypotheses_sha256") != expected_binding:
            errors.append(label + ": protocol hypothesis binding mismatch")
        rules = ()
        settings = {}
        expected_interpretation = None
        if interpretation_bound:
            settings = protocol["interpretation_settings"]
            if settings != {"time_tolerance_hours": 1.0, "require_context_match": True}:
                errors.append(label + ": interpretation settings differ from the frozen audit specification")
            normalized_rules = []
            set_fields = {"matched_fields", "forbidden_fields", "required_prefixes", "eliminates", "required_conditions"}
            for item in protocol["interpretation_rules"]:
                item = dict(item)
                for field in set_fields:
                    item[field] = frozenset(item[field])
                item["scope"] = EvidenceScope(item["scope"])
                item["allowed_action_kinds"] = frozenset(EvidenceActionKind(x) for x in item["allowed_action_kinds"])
                normalized_rules.append(OutcomeRule(**item))
            rules = tuple(normalized_rules)
            expected_interpretation = decision_interpretation_binding(rules, **settings)
            if protocol.get("interpretation_sha256") != expected_interpretation:
                errors.append(label + ": protocol interpretation binding mismatch")
        for scenario in result["scenarios"]:
            case = directory / scenario["scenario"]
            receipt_path = case / "evaluation_receipt.json"
            receipt = read_json(receipt_path)
            if digest(receipt_path) != scenario["receipt_sha256"]:
                errors.append(label + ": receipt hash mismatch")
            if hypotheses_bound and receipt.get("hypotheses_sha256") != expected_binding:
                errors.append(label + ": receipt hypothesis binding mismatch")
            if interpretation_bound and receipt.get("interpretation_sha256") != expected_interpretation:
                errors.append(label + ": receipt interpretation binding mismatch")
            if scenario["case_before"]["spent"] != scenario["case_after"]["spent"] or scenario["case_after"]["spent"] != 0:
                errors.append(label + ": measurement spend changed")
            if scenario["raw_planner_proposal"]["action_identifier"] != "flat":
                errors.append(label + ": actual proposal differs from declared engineering preference")
            selection = scenario["selection_gates"][-1]
            gate = scenario["execution_gates"][-1]
            expected_action = ["useful"] if scenario["scenario"] == "informative_overrides_flat" else []
            if scenario["selected_action_ids"] != expected_action or gate["submitted_action_ids"] != expected_action:
                errors.append(label + ": selected/submitted action mismatch")
            if expected_action and abs(selection["evaluations"]["useful"]["net_value"] - 0.86) > 1e-12:
                errors.append(label + ": synthetic terminal-loss arithmetic mismatch")
            if scenario["scenario"] == "all_flat_refuses" and selection["evaluations"]["flat"]["reason"] != "non_positive_net_value":
                errors.append(label + ": all-flat refusal missing")
            if scenario["scenario"] == "external_shift_refuses":
                if "outcome_distribution_shifted" not in selection["evaluations"]["flat"]["reason"] or scenario["forecaster_calls"] != 0:
                    errors.append(label + ": external shift did not prevent forecast work")
            if interpretation_bound:
                if selection.get("interpretation_sha256") != expected_interpretation:
                    errors.append(label + ": selection log lacks the final interpretation binding")
                source = read_json(case / "synthetic_source.json")
                profile = FunctionalInterventionProfile(**source["profile"])
                actions = []
                for item in source["actions"]:
                    item = dict(item)
                    item["kind"] = EvidenceActionKind(item["kind"])
                    item["quantity"] = BiologicalQuantity(item["quantity"])
                    for field in ("distinguishes", "prerequisites", "source_ids", "supplies"):
                        item[field] = tuple(item[field])
                    actions.append(EvidenceAction(**item))
                forecasts = {}
                for identifier, item in read_json(case / "synthetic_forecasts.json").items():
                    item = dict(item)
                    item["branches"] = tuple(OutcomeBranch(**x) for x in item["branches"])
                    item["evidence_kind"] = EvidenceKind(item["evidence_kind"])
                    forecasts[identifier] = OutcomeForecast(**item)
                policy = FrozenDecisionValuePolicy.from_receipt(receipt_path, scenario["receipt_sha256"])
                recomputed = policy.select(frozenset({"a", "b"}), tuple(actions), profile, 10.0, forecasts,
                                           outcome_consequences(rules), endpoint="viability", hypotheses=bound_hypotheses,
                                           interpretation_rules=rules, **settings)
                chosen = [recomputed.chosen.action_identifier] if recomputed.chosen else []
                if chosen != expected_action:
                    errors.append(label + ": current bound policy arithmetic did not reproduce the recorded choice")
            with sqlite3.connect((case / "cases.sqlite").resolve().as_uri() + "?mode=ro", uri=True) as connection:
                measured_count = connection.execute("SELECT COUNT(*) FROM results").fetchone()[0]
                spent = connection.execute("SELECT spent FROM cases").fetchone()[0]
            if measured_count != 0 or spent != 0:
                errors.append(label + ": persisted measurement fact or spend exists")
            if not all(scenario["checks"].values()):
                errors.append(label + ": a recorded invariant is false")
        for call in result["provider_calls"]:
            if call["status"] == "offline_replay_of_actual_provider_response":
                for path_key, sha_key in [("source_request_path", "source_request_sha256"), ("source_response_path", "source_response_sha256")]:
                    if digest(HERE / call[path_key]) != call[sha_key]:
                        errors.append(label + ": replay source hash mismatch")
                if call["new_http_requests"] != 0 or not call["replay_context_matches_source"]:
                    errors.append(label + ": unqualified offline replay")
                continue
            for path_key, sha_key in [("request_path", "request_sha256"), ("response_path", "response_sha256")]:
                if digest(HERE / call[path_key]) != call[sha_key]:
                    errors.append(label + ": live provider artifact hash mismatch")
            request = read_json(HERE / call["request_path"])
            response = read_json(HERE / call["response_path"])
            if set(request) - {"model", "messages", "temperature", "max_tokens", "response_format", "thinking"}:
                errors.append(label + ": unexpected provider payload field")
            if request["max_tokens"] > 1600 or call["timeout_seconds"] > 60 or call["transport_attempt_limit"] != 1:
                errors.append(label + ": API bound violated")
            if response["usage"] != call["usage"] or call["authorization_header_persisted"]:
                errors.append(label + ": provider usage or header audit mismatch")
            authenticated_calls.append(call)
        runs.append({"label": label, "results": str(results_path.relative_to(HERE)), "results_sha256": digest(results_path),
                     "actual_http_requests": expected_calls, "offline_response_replays": expected_replays,
                     "scenarios_passed": len(result["scenarios"]), "hypothesis_semantics_bound": hypotheses_bound,
                     "interpretation_semantics_bound": interpretation_bound,
                     "current_schema": interpretation_bound})
    # Never print or persist the credential, including on a failed scan.
    secret = MAESTROSettings.from_workspace(WORKSPACE, require_provider=False).api_key
    for path in (HERE / "runs").rglob("*"):
        if path.is_file() and secret and secret.encode("utf-8") in path.read_bytes():
            errors.append("Credential bytes detected in an artifact; contents are not displayed.")
    usage = {field: sum(x["usage"].get(field, 0) for x in authenticated_calls)
             for field in ("prompt_tokens", "completion_tokens", "total_tokens")}
    if len(authenticated_calls) != 4 or usage != {"prompt_tokens": 3238, "completion_tokens": 1658, "total_tokens": 4896}:
        errors.append("Total API usage arithmetic mismatch")
    report = {"audit_passed": not errors, "errors": errors, "scope": "Synthetic engineering API compatibility and authority audit only.",
              "runs": runs, "total_actual_http_requests": len(authenticated_calls),
              "total_offline_response_replays": sum(x["offline_response_replays"] for x in runs),
              "total_provider_reported_usage": usage, "real_measurement_results": 0,
              "measurement_budget_spend": 0, "monetary_api_cost": None,
              "biological_effect_or_llm_incremental_value_established": False, "credential_scan_passed": not any("Credential" in e for e in errors)}
    (HERE / "AUDIT_SUMMARY.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["audit_passed"] else 1)
