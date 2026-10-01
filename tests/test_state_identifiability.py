"""Reject temporal leakage, unsupported sample joins and design-only actions."""
from copy import deepcopy

import pytest

from tools.datasets.state_identifiability import assess_task, response_link_gaps, state_gaps


def qualified_task():
    return {
        "task_id": "contract_only_not_biological_data",
        "predecision_state": {
            "measured_at": "2026-10-01T01:00:00+00:00",
            "available_at": "2026-10-01T02:00:00+00:00",
            "decision_at": "2026-10-01T03:00:00+00:00",
            "action_started_at": "2026-10-01T04:00:00+00:00",
            "role": "predecision_observation", "matching_verified": True,
            "relation": "randomized_sister_aliquots", "sample_id": "parent",
            "response_parent_id": "parent", "source_sha256": "a" * 64,
            "source_path": "contract_fixture_only.csv",
            "source_fields": ["state_available_at", "randomization_parent"],
        },
        "state_blind_control_constructible": True, "same_rules_declared": True,
        "attempt_denominator_verified": True,
        "actions": [{"action": action, "executed": True, "outcome_link_verified": True,
                     "qc_status": "passed", "source_sha256": "b" * 64,
                     "source_path": "contract_fixture_only.csv", "source_fields": ["parent_id", "started_at"],
                     "action_started_at": "2026-10-01T04:00:00+00:00",
                     "response_recorded_at": "2026-10-02T04:00:00+00:00",
                     "outcome_available_at": "2026-10-03T04:00:00+00:00",
                     "response_parent_id": "parent", "sample_relation_verified": True,
                     "endpoint_id": "declared_endpoint"} for action in ("A", "B")],
    }


@pytest.mark.parametrize("field,value", [
    ("available_at", "2026-10-01T05:00:00+00:00"),
    ("measured_at", "2026-10-01T05:00:00+00:00"),
    ("decision_at", "2026-10-01T04:00:00+00:00"),
    ("available_at", "2026-10-01T02:00:00"),
    ("available_at", None),
    ("role", "post_treatment_expression"),
    ("relation", "same_cell_line"),
    ("matching_verified", 1),
    ("source_sha256", "unverified"),
])
def test_temporal_or_matching_gap_blocks_experiment(field, value):
    task = qualified_task()
    task["predecision_state"][field] = value
    result = assess_task(task)
    assert result["classification"] == "replay_only"
    assert not result["state_gain_gate_passed"]


def test_zero_time_or_control_label_does_not_supply_availability():
    assert state_gaps({"time": 0, "control": "DMSO", "sample_id": "line_A"})


def test_missing_actions_give_intervals_only_and_do_not_pass_hard_gate():
    task = qualified_task()
    missing = deepcopy(task["actions"][0])
    missing["action"] = "C"
    missing["executed"] = False
    task["actions"].append(missing)
    result = assess_task(task)
    assert result["classification"] == "utility_interval_only"
    assert not result["state_gain_gate_passed"]


def test_design_menu_is_not_measured_action_coverage():
    task = qualified_task()
    task["actions"][0]["executed"] = None
    assert assess_task(task)["classification"] == "replay_only"


def test_duplicate_receipts_are_not_distinct_comparable_actions():
    task = qualified_task()
    task["actions"][1]["action"] = "A"
    assert not assess_task(task)["state_gain_gate_passed"]


@pytest.mark.parametrize("field,value", [
    ("action_started_at", "2026-10-01T02:00:00+00:00"),
    ("response_recorded_at", "2026-10-01T02:00:00+00:00"),
    ("response_parent_id", "unrelated_parent"),
    ("source_path", None), ("source_fields", []),
    ("endpoint_id", "different_endpoint"),
])
def test_task_signoff_does_not_replace_each_action_raw_proof(field, value):
    task = qualified_task()
    task["actions"][0][field] = value
    assert not assess_task(task)["state_gain_gate_passed"]


def test_qc_failure_can_be_an_observed_attempt_not_an_imputed_success():
    task = qualified_task()
    task["actions"][0]["qc_status"] = "failed"
    assert assess_task(task)["state_gain_gate_passed"]
    task["actions"][0]["qc_status"] = "unknown"
    assert not assess_task(task)["state_gain_gate_passed"]


def test_complete_contract_passes_without_invoking_any_model():
    result = assess_task(qualified_task())
    assert result["classification"] == "comparable"
    assert result["uncertainty"].startswith("not_estimable")


@pytest.mark.parametrize("wells,slots,plates,expected", [
    ("True", "True", "True", []),
    ("False", "False", "False", ["well_source_link_unresolved", "plate_source_link_unresolved"]),
    ("False", "True", "False", ["plate_source_link_unresolved"]),
])
def test_valid_protocol_label_does_not_resolve_source_differences(wells, slots, plates, expected):
    source = {"status": "result_valid", "inst_rows": "2", "cache_expansion_agrees": wells,
              "cache_vs_distinct_slots_agrees": slots, "cache_plate_agrees": plates}
    assert response_link_gaps("l1000_LT", source) == expected
