"""Validate a collected single-decision sister-aliquot panel, never infer evidence.

This structural gate supplements independent scientific source review. Times are
timezone-aware actual events. Historical sources with only protocol partial orders
remain reviewable through state_evidence_followup.assess, not invented timestamps.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import math
from pathlib import Path


TABLES = {
    "questions": "question_id,context,parent_id,physical_batch,split,state_sample_id,decision_at,expected_attempt_ids,ledger_evidence,menu_version,budget_CNY,endpoint_id,qc_version,cost_version,refusal_version,protocol_sha256",
    "actions": "question_id,action_id,exact_condition_label,is_control,control_action_id,dose,dose_unit,exposure_hours,source_record_id,source_file_sha256,source_row",
    "attempts": "attempt_id,question_id,action_id,parent_id,aliquot_id,physical_batch,shared_control_group,control_attempt_id,status,reason,randomized_at,randomization_evidence,commanded_at,executed_at,execution_evidence,qc_status,qc_reason,cost_CNY,source_record_id,source_file_sha256,source_row",
    "state_samples": "state_sample_id,question_id,parent_id,aliquot_id,physical_batch,role,collected_at,processed_at,available_at,relation_evidence,qc_status,cost_CNY,waiting_cost_CNY,feature_axis_sha256,source_record_id,source_file,source_file_sha256,source_row",
    "response_samples": "response_sample_id,attempt_id,question_id,parent_id,aliquot_id,physical_batch,role,collected_at,available_at,qc_status,qc_reason,observed_value,endpoint_id,control_response_id,cost_CNY,source_record_id,source_file,source_file_sha256,source_row",
}


def templates(out):
    out.mkdir(parents=True, exist_ok=False)
    for name, header in TABLES.items():
        (out / (name + ".csv")).write_text(header + "\n", encoding="utf-8")


def timestamp(value):
    dt = datetime.fromisoformat(value)
    if dt.utcoffset() is None:
        raise ValueError("timezone required")
    return dt


def finite_nonnegative(value):
    number = float(value)
    return math.isfinite(number) and number >= 0


def validate(tables):
    errors = []

    def require(condition, code):
        if not condition:
            errors.append(code)

    indexed = {}
    for table, key in (("questions", "question_id"), ("attempts", "attempt_id"),
                       ("state_samples", "state_sample_id"), ("response_samples", "response_sample_id")):
        rows = tables[table]
        indexed[table] = {row[key]: row for row in rows}
        require(len(rows) == len(indexed[table]), "duplicate_id:" + table)
    require(bool(tables["questions"]), "empty_panel_not_observations")
    questions, attempts, states, responses = [indexed[k] for k in ("questions", "attempts", "state_samples", "response_samples")]
    actions = {(r["question_id"], r["action_id"]): r for r in tables["actions"]}
    require(len(actions) == len(tables["actions"]), "duplicate_action")
    dependency_splits = {}
    for table in ("state_samples", "attempts", "response_samples", "actions"):
        for row in tables[table]:
            require(row["question_id"] in questions, "orphan_question:" + table)
            require(all(row.get(k) for k in ("source_record_id", "source_file_sha256", "source_row")), "missing_source:" + table)
            if table in ("state_samples", "response_samples"):
                require(row.get("role") == ("baseline_observation" if table == "state_samples" else "response_observation"), "prediction_request_in_observations")
    for qid, q in questions.items():
        try:
            state = states[q["state_sample_id"]]
            require(state["question_id"] == qid, "state_question_join")
            require(state["parent_id"] == q["parent_id"] and state["physical_batch"] == q["physical_batch"], "state_parent_batch_join")
            require(bool(state["relation_evidence"]), "sister_relation_evidence_missing")
            require(state["qc_status"] == "pass", "baseline_QC_not_pass")
            require(timestamp(state["collected_at"]) <= timestamp(state["processed_at"]) <= timestamp(state["available_at"]) < timestamp(q["decision_at"]), "state_not_available_before_decision")
            menu = [r for (question_id, _), r in actions.items() if question_id == qid]
            require(sum(str(r["is_control"]).lower() == "false" for r in menu) >= 2, "fewer_than_two_actions")
            require(any(str(r["is_control"]).lower() == "true" for r in menu), "missing_control_action")
            expected = json.loads(q["expected_attempt_ids"])
            actual = [r for r in attempts.values() if r["question_id"] == qid]
            require(bool(q["ledger_evidence"]) and len(expected) == len(set(expected)) and set(expected) == {r["attempt_id"] for r in actual}, "incomplete_attempt_denominator")
            require({r["action_id"] for r in actual} == {r["action_id"] for r in menu}, "menu_attempt_coverage")
            for row in [q, state, *actual]:
                require(bool(row["parent_id"]) and bool(row["physical_batch"]), "unknown_physical_unit")
                for key in ("parent_id", "physical_batch", "shared_control_group"):
                    if row.get(key):
                        dependency_splits.setdefault((key, row[key]), set()).add(q["split"])
            for attempt in actual:
                require(attempt["parent_id"] == q["parent_id"] and attempt["physical_batch"] == q["physical_batch"], "attempt_parent_batch_join")
                require(attempt["aliquot_id"] != state["aliquot_id"], "destructive_RNA_not_same_aliquot")
                require(attempt["status"] in {"planned", "cancelled", "failed", "commanded", "executed"}, "invalid_attempt_status")
                require(attempt["qc_status"] in {"pass", "fail", "not_run"}, "unknown_attempt_QC")
                if attempt["status"] != "executed":
                    require(bool(attempt["reason"]), "missing_failure_or_nonexecution_reason")
                if attempt["qc_status"] != "pass":
                    require(bool(attempt["qc_reason"]), "missing_QC_reason")
                require(bool(attempt["randomization_evidence"]), "allocation_evidence_missing")
                require(timestamp(q["decision_at"]) <= timestamp(attempt["randomized_at"]), "allocation_before_decision")
                control = attempts[attempt["control_attempt_id"]]
                require(control["question_id"] == qid and control["parent_id"] == attempt["parent_id"] and control["physical_batch"] == attempt["physical_batch"] and control["shared_control_group"] == attempt["shared_control_group"], "unmatched_control")
                require(str(actions[(qid, control["action_id"])]["is_control"]).lower() == "true", "control_is_treatment")
                require(actions[(qid, attempt["action_id"])]["control_action_id"] == control["action_id"], "wrong_declared_control")
                if attempt["status"] == "executed":
                    require(bool(attempt["execution_evidence"]), "command_not_execution")
                    require(timestamp(attempt["randomized_at"]) <= timestamp(attempt["commanded_at"]) <= timestamp(attempt["executed_at"]), "action_time_order")
            for row in [state, *actual]:
                require(finite_nonnegative(row["cost_CNY"]), "invalid_cost")
            require(finite_nonnegative(state["waiting_cost_CNY"]), "unknown_waiting_cost")
        except (KeyError, ValueError, TypeError) as exc:
            errors.append(f"missing_or_invalid_field:{qid}:{exc}")
    for response in responses.values():
        try:
            attempt = attempts[response["attempt_id"]]
            for key in ("question_id", "parent_id", "aliquot_id", "physical_batch"):
                require(response[key] == attempt[key], "response_sample_join")
            require(attempt["status"] == "executed", "response_without_confirmed_execution")
            require(timestamp(attempt["executed_at"]) < timestamp(response["collected_at"]) <= timestamp(response["available_at"]), "response_time_order")
            require(response["qc_status"] in {"pass", "fail"}, "response_QC_unknown")
            require(bool(response["observed_value"]) if response["qc_status"] == "pass" else bool(response["qc_reason"]), "missing_outcome_or_QC_reason")
            if response["qc_status"] == "pass":
                require(math.isfinite(float(response["observed_value"])), "nonfinite_observed_response")
            control_response = responses[response["control_response_id"]]
            require(control_response["attempt_id"] == attempt["control_attempt_id"], "response_control_join")
            require(control_response["endpoint_id"] == response["endpoint_id"], "response_endpoint_mismatch")
            require(finite_nonnegative(response["cost_CNY"]), "invalid_response_cost")
        except (KeyError, ValueError, TypeError) as exc:
            errors.append(f"invalid_response:{exc}")
    require(all(len(splits) == 1 for splits in dependency_splits.values()), "shared_dependency_crosses_split")
    missing = [a["attempt_id"] for a in attempts.values()
               if not any(r["attempt_id"] == a["attempt_id"] and r["qc_status"] == "pass" for r in responses.values())]
    return {"structural_contract_passed": not errors, "errors": sorted(set(errors)),
            "attempts": len(attempts), "missing_valid_response_attempts": missing,
            "scientific_qualification": "requires independent evidence review; structural pass is insufficient",
            "efficacy_ready": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--templates", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.templates:
        templates(args.templates)
    elif args.input and args.output:
        data = {key: list(csv.DictReader((args.input / (key + ".csv")).open(encoding="utf-8-sig", newline=""))) for key in TABLES}
        report = validate(data)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        raise SystemExit(0 if report["structural_contract_passed"] else 2)
    else:
        parser.error("provide --templates or --input and --output")
