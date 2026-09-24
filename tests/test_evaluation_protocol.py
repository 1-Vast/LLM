"""Evaluation protocol: laboratory cost, named refusals, the hidden partition, and the score table.

File summary
- Path: tests/test_evaluation_protocol.py
- Purpose: pin the evaluation-infrastructure contracts of the governing report's sections 26,
  29, 36, 37 and 55: cost in wells and turnaround days, refusals with codes, a result partition
  no policy can reach, a per-step trace of passed-over candidates, and a six-row score table.
- Core points: assertions here are contract tests, not biological results; each test pins one
  boundary that must not silently move.
- Interfaces: `test_*` functions only
- Depends on: evaluation
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from evaluation import (
    CaseRepository,
    CostBasis,
    CostingProfile,
    EvaluationRunner,
    ExpertWorkflowPolicy,
    LabCost,
    MAESTROCorePolicy,
    ReplayEnvironment,
    RevealRefusal,
    SharedControl,
    build_score_table,
    exit_verdict,
    load_costing_profile,
)
from evaluation import cli
from evaluation.lab_cost import sequence_lab_cost
from evaluation.prediction_controls import is_identity, shuffled_assignment, with_prediction_values
from evaluation.score_table import SECTION_37_ROWS, cluster_bootstrap_interval, row_metrics, wilson_interval

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data" / "evaluation" / "cases"
PUBLIC = CASES / "public"
PRIVATE = CASES / "private"
COSTING_PUBLIC = ROOT / "data" / "evaluation" / "costing" / "contract_and_boundary_cases.json"
COSTING_REAL = ROOT / "data" / "evaluation" / "costing" / "real_record_retrieval.json"
SYNTHETIC = "synthetic-functional-calibration-001"
BOUNDARY = "depmap-prism-snu761-egfr-osimertinib-001"


def _contract_cases(*, costing: bool = True):
    profile = load_costing_profile(COSTING_PUBLIC) if costing else None
    return {case.public.identifier: (case, outcomes) for case, outcomes in CaseRepository(PUBLIC, PRIVATE, costing=profile).load()}


def _synthetic_package(tmp_path: Path, *, public_edit=None, private_edit=None) -> tuple[Path, Path]:
    public_dir, private_dir = tmp_path / "public", tmp_path / "private"
    public_dir.mkdir()
    private_dir.mkdir()
    public = json.loads((PUBLIC / "synthetic_functional_calibration.json").read_text(encoding="utf-8"))
    private = json.loads((PRIVATE / f"{SYNTHETIC}.results.json").read_text(encoding="utf-8"))
    if public_edit is not None:
        public_edit(public)
    if private_edit is not None:
        private_edit(private)
    (public_dir / "synthetic_functional_calibration.json").write_text(json.dumps(public), encoding="utf-8")
    (private_dir / f"{SYNTHETIC}.results.json").write_text(json.dumps(private), encoding="utf-8")
    return public_dir, private_dir


def _final_test(identifier: str, *, confirms=(), contradicts=(), quality: str = "passed") -> dict:
    return {
        "identifier": identifier,
        "statement": "Synthetic held-back result used only to test a terminal decision.",
        "source_id": "synthetic:functional-calibration-001:final-test",
        "outcome": "held_back_outcome",
        "confirms": list(confirms),
        "contradicts": list(contradicts),
        "record_validated": True,
        "biological_quality": quality,
        "evidence_kind": "real_measurement",
    }


def test_a_retrieval_consumes_nothing_and_a_measurement_consumes_wells():
    with pytest.raises(ValueError, match="lab_cost_retrieval_consumes_resources"):
        LabCost(CostBasis.RECORD_RETRIEVAL, wells=6, turnaround_days=0.0)
    with pytest.raises(ValueError, match="lab_cost_measurement_without_wells"):
        LabCost(CostBasis.NEW_MEASUREMENT, wells=0, turnaround_days=2.0)
    assert LabCost(CostBasis.RECORD_RETRIEVAL, wells=0, turnaround_days=0.0).price_key() == ("record_retrieval", 0, 0.0, None)


def test_a_shared_control_is_charged_once_per_sequence():
    prices = {
        "a": LabCost(CostBasis.NEW_MEASUREMENT, 24, 3.0, shared_control="vehicle"),
        "b": LabCost(CostBasis.NEW_MEASUREMENT, 48, 7.0, shared_control="vehicle"),
        "c": LabCost(CostBasis.RECORD_RETRIEVAL, 0, 0.0),
    }
    controls = {"vehicle": SharedControl("vehicle", wells=6)}
    both = sequence_lab_cost(prices, controls, ["a", "b", "c"])
    assert both.declared and both.wells == 24 + 48 + 6 and both.control_wells == 6
    assert both.turnaround_days == 10.0 and both.shared_controls_charged == ("vehicle",)
    assert (both.new_measurements, both.record_retrievals) == (2, 1)
    assert sequence_lab_cost(prices, controls, ["a"]).wells == 30
    nothing = sequence_lab_cost(prices, controls, [])
    assert nothing.declared and nothing.wells == 0


def test_an_unpriced_action_is_refused_by_name_and_never_priced_at_zero():
    partial = sequence_lab_cost({"a": LabCost(CostBasis.NEW_MEASUREMENT, 24, 3.0), "x": None}, {}, ["a", "x"])
    assert not partial.declared and partial.wells is None and partial.turnaround_days is None
    assert partial.refusal == "lab_cost_undeclared:x" and partial.assay_wells == 24


def test_the_contract_case_is_priced_in_wells_and_days_beside_its_abstract_cost():
    priced = _contract_cases()
    report = EvaluationRunner().evaluate(MAESTROCorePolicy(), tuple(priced.values()))
    result = next(item for item in report.results if item.case_id == SYNTHETIC)
    assert result.selected_actions == ("functional_target_activity", "mode_matched_comparator")
    assert result.spent == 5.0
    assert (result.wells_spent, result.turnaround_days_spent, result.new_measurements) == (72, 10.0, 2)
    assert result.lab_cost_refusal is None

    unpriced = _contract_cases(costing=False)
    bare = EvaluationRunner().evaluate(MAESTROCorePolicy(), tuple(unpriced.values()))
    result = next(item for item in bare.results if item.case_id == SYNTHETIC)
    assert result.wells_spent is None
    assert result.lab_cost_refusal == "lab_cost_undeclared:functional_target_activity,mode_matched_comparator"


def test_every_executable_action_in_the_real_packages_is_a_retrieval_that_uses_no_wells():
    profile = load_costing_profile(COSTING_REAL)
    for package in ("real", "real_v2", "real_v3"):
        loaded = CaseRepository(CASES / package / "public", CASES / package / "private", costing=profile).load()
        for case, _ in loaded:
            for item in case.public.actions:
                assert item.lab_cost is not None, (package, case.public.identifier, item.action.identifier)
                expected = CostBasis.RECORD_RETRIEVAL if item.available else CostBasis.NEW_MEASUREMENT
                assert item.lab_cost.basis is expected
    report = EvaluationRunner(mode="decision").evaluate(ExpertWorkflowPolicy(), loaded)
    assert report.lab_cost["cases_refused"] == 0 and report.lab_cost["wells_over_priced_cases"] == 0
    assert report.lab_cost["new_measurements"] == 0 and report.lab_cost["record_retrievals"] > 0


def test_an_overlay_that_contradicts_a_declared_price_is_refused(tmp_path: Path):
    def inline_price(public):
        public["actions"][0]["lab_cost"] = {"basis": "new_measurement", "wells": 12, "turnaround_days": 3}

    public_dir, private_dir = _synthetic_package(tmp_path, public_edit=inline_price)
    profile = CostingProfile(
        "conflicting", "test", actions={"functional_target_activity": LabCost(CostBasis.NEW_MEASUREMENT, 24, 3.0)}
    )
    with pytest.raises(ValueError, match="costing_conflict"):
        CaseRepository(public_dir, private_dir, costing=profile).load()
    agreeing = CostingProfile(
        "agreeing", "test", actions={"functional_target_activity": LabCost(CostBasis.NEW_MEASUREMENT, 12, 3.0)}
    )
    (case, _), = CaseRepository(public_dir, private_dir, costing=agreeing).load()
    assert case.public.action("functional_target_activity").lab_cost.wells == 12


def test_an_overlay_entry_that_prices_no_action_is_refused():
    profile = CostingProfile("misspelt", "test", actions={"functional_target_activty": LabCost(CostBasis.NEW_MEASUREMENT, 24, 3.0)})
    with pytest.raises(ValueError, match="costing_entry_matches_no_action:functional_target_activty"):
        CaseRepository(PUBLIC, PRIVATE, costing=profile).load()


def test_every_refused_query_carries_a_machine_readable_code():
    cases = _contract_cases(costing=False)
    case, outcomes = cases[SYNTHETIC]
    environment = ReplayEnvironment(case, outcomes)
    codes = []
    for identifier in ("not_registered_anywhere", "mode_matched_comparator"):
        with pytest.raises(RevealRefusal) as refused:
            environment.query(identifier)
        codes.append(refused.value.code)
    assert codes == ["action_not_in_menu", "unmet_prerequisites"]
    environment.query("functional_target_activity")
    with pytest.raises(RevealRefusal) as repeated:
        environment.query("functional_target_activity")
    assert repeated.value.code == "action_already_revealed"
    with pytest.raises(RevealRefusal) as unaffordable:
        environment.query("broad_transcriptome")
    assert unaffordable.value.code == "exceeds_remaining_budget"
    boundary, boundary_outcomes = cases[BOUNDARY]
    with pytest.raises(ValueError, match="unavailable in this case package") as unavailable:
        ReplayEnvironment(boundary, boundary_outcomes).query("matched_target_engagement")
    assert unavailable.value.code == "action_unavailable_in_package"


def test_a_final_test_record_can_never_be_reached_by_a_policy(tmp_path: Path):
    held = _final_test("independent_compound_same_target", confirms=["change_intervention_mode"])
    public_dir, private_dir = _synthetic_package(tmp_path, private_edit=lambda private: private.update(final_test=[held]))
    (case, outcomes), = CaseRepository(public_dir, private_dir).load()
    assert [record.identifier for record in case.scoring.final_test] == ["independent_compound_same_target"]
    assert "independent_compound_same_target" not in outcomes
    environment = ReplayEnvironment(case, outcomes)
    with pytest.raises(RevealRefusal) as refused:
        environment.query("independent_compound_same_target")
    assert refused.value.code == "action_not_in_menu"
    assert "independent_compound_same_target" not in json.dumps(environment.view().public_contract())


@pytest.mark.parametrize(
    "record, message",
    [
        (_final_test("broad_transcriptome", confirms=["stop"]), "final_test_record_shadows_public_action"),
        (_final_test("held_back", confirms=[]), "final_test_record_bears_on_no_decision"),
        (_final_test("held_back", confirms=["stop"], contradicts=["stop"]), "final_test_record_confirms_and_contradicts"),
    ],
)
def test_a_final_test_record_a_policy_could_reach_or_that_tests_nothing_is_refused(tmp_path: Path, record, message):
    public_dir, private_dir = _synthetic_package(tmp_path, private_edit=lambda private: private.update(final_test=[record]))
    with pytest.raises(ValueError, match=message):
        CaseRepository(public_dir, private_dir).load()


@pytest.mark.parametrize(
    "record, expected",
    [
        (_final_test("held_back", confirms=["change_intervention_mode"]), "consistent"),
        (_final_test("held_back", contradicts=["change_intervention_mode"]), "contradicted"),
        (_final_test("held_back", confirms=["change_intervention_mode"], quality="failed"), "inadmissible"),
        (_final_test("held_back", confirms=["stop"]), "untested"),
    ],
)
def test_the_final_test_verdict_sits_beside_the_licensing_verdict_and_never_changes_it(tmp_path: Path, record, expected):
    public_dir, private_dir = _synthetic_package(tmp_path, private_edit=lambda private: private.update(final_test=[record]))
    report = EvaluationRunner().evaluate(MAESTROCorePolicy(), CaseRepository(public_dir, private_dir).load())
    result = report.results[0]
    assert result.final_test_verdict == expected
    assert result.verdict == "correct" and result.decision_supported
    assert report.final_test_verdicts == {expected: 1}


def test_the_trace_names_every_candidate_the_policy_passed_over():
    cases = _contract_cases(costing=False)
    report = EvaluationRunner().evaluate(MAESTROCorePolicy(), (cases[SYNTHETIC],))
    first, second = report.results[0].trace
    assert first.candidates == ("functional_target_activity", "broad_transcriptome")
    assert (first.chosen, first.rejected, first.outcome) == ("functional_target_activity", ("broad_transcriptome",), "acquired")
    assert second.candidates == ("mode_matched_comparator",) and second.rejected == () and second.outcome == "acquired"


def test_the_shuffle_moves_every_available_value_and_nothing_else():
    loaded = CaseRepository(CASES / "real_v3" / "public", CASES / "real_v3" / "private").load()
    for case, outcomes in loaded:
        assignment = shuffled_assignment(case.public)
        available = {item.action.identifier: item.prediction_value for item in case.public.actions if item.available}
        assert set(assignment) == set(available)
        assert sorted(assignment.values()) == sorted(available.values())
        assert all(assignment[name] != value for name, value in available.items())
        assert not is_identity(case.public)
        view = ReplayEnvironment(case, outcomes).view()
        moved = with_prediction_values(view, assignment)
        assert [item.action.identifier for item in moved.available_actions()] == [
            item.action.identifier for item in view.available_actions()
        ]
    first = loaded[0][0].public
    assert shuffled_assignment(first) == shuffled_assignment(first)


def test_the_score_table_keeps_all_six_rows_and_names_what_did_not_run():
    cases = tuple(_contract_cases().values())
    runner = EvaluationRunner(mode="decision")
    reports = [asdict(runner.evaluate(policy, cases)) for policy in (ExpertWorkflowPolicy(), MAESTROCorePolicy())]
    table = build_score_table(reports)
    assert [row["row"] for row in table["rows"]] == [key for key, _ in SECTION_37_ROWS]
    statuses = {row["row"]: row["status"] for row in table["rows"]}
    assert [key for key, status in statuses.items() if status == "run"] == ["fixed_expert_rule_flow", "full_system"]
    assert all(row["reason"] for row in table["rows"] if row["status"] == "not_run")
    assert table["conclusion"]["all_rows_run"] is False
    assert table["conclusion"]["evidence_for_core_claim"] is False
    complete = build_score_table(
        reports, row_arms={key: "maestro_core" for key, _ in SECTION_37_ROWS}, blind_adjudication=False
    )
    assert complete["conclusion"]["all_rows_run"] is True
    assert complete["conclusion"]["evidence_for_core_claim"] is False


def test_the_intervals_are_the_standard_ones_and_deterministic():
    low, high = wilson_interval(0, 10)
    assert low == 0.0 and abs(high - 0.277533) < 1e-6
    assert wilson_interval(3, 0) is None
    clusters = {"g1": (1, 3), "g2": (0, 2), "g3": (2, 2)}
    interval = cluster_bootstrap_interval(clusters)
    assert interval == cluster_bootstrap_interval(clusters)
    assert 0.0 <= interval[0] <= 3 / 7 <= interval[1] <= 1.0
    assert cluster_bootstrap_interval({"only": (1, 4)}) is None


def test_executed_strong_controls_populate_their_primary_rows():
    arms = {"simple_model_plus_voi": "simple_model_voi",
            "same_llm_explicit_hypotheses": "explicit_hypotheses_llm",
            "full_system_shuffled_predictions": "maestro_core_shuffled_predictions"}
    table = build_score_table([{"policy": arm, "results": []} for arm in arms.values()])
    rows = {row["row"]: row for row in table["rows"]}
    assert all(rows[row]["status"] == "run" and rows[row]["arm"] == arm for row, arm in arms.items())
    assert not table["supplementary_rows"]
    assert table["conclusion"]["evidence_for_core_claim"] is False


def test_appropriate_deferral_counts_only_cases_where_nothing_else_was_reachable():
    report = {
        "policy": "p",
        "results": [
            {"case_id": "a", "verdict": "correct", "decision": "defer", "reachable_decisions": ["defer"], "spent": 0.0},
            {"case_id": "b", "verdict": "over_deferral", "decision": "defer", "reachable_decisions": ["continue", "defer"], "spent": 1.0},
            {"case_id": "c", "verdict": "correct", "decision": "continue", "reachable_decisions": ["continue"], "spent": 1.0, "wells_spent": 0, "turnaround_days_spent": 0.0},
        ],
    }
    row = row_metrics(report, {})
    assert row["appropriate_deferral"] == {"eligible": 1, "deferred_correctly": 1, "rate": 1.0}
    assert row["over_deferral"]["count"] == 1 and row["wrong_action"]["count"] == 0
    assert row["cost_to_evidence_standard"]["cases"] == 1 and row["cost_to_evidence_standard"]["wells"] == 0


def _panel_report(policy: str, verdicts: list[str]) -> dict:
    return {
        "policy": policy,
        "results": [{"case_id": f"c{index}", "verdict": verdict, "selected_actions": []} for index, verdict in enumerate(verdicts)],
    }


def test_the_exit_conditions_are_applied_in_their_written_order():
    idle = exit_verdict(
        input_name="declared value",
        informed=_panel_report("informed", ["correct", "over_deferral"]),
        removed=_panel_report("removed", ["correct", "over_deferral"]),
        shuffled=_panel_report("shuffled", ["over_deferral", "over_deferral"]),
    )
    assert idle["consequence"] == "remove_from_loop"
    assert [item["status"] for item in idle["conditions"]] == ["triggered", "not_assessable", "not_assessable", "not_assessable"]
    useful = exit_verdict(
        input_name="declared value",
        informed=_panel_report("informed", ["correct", "correct"]),
        removed=_panel_report("removed", ["correct", "over_deferral"]),
        shuffled=_panel_report("shuffled", ["over_deferral", "over_deferral"]),
        declaration_reader=_panel_report("reader", ["correct", "correct"]),
    )
    assert [item["status"] for item in useful["conditions"]] == ["not_triggered", "not_assessable", "triggered", "not_assessable"]
    assert useful["consequence"] == "record_as_external_information_gain"


def test_the_cli_records_the_preregistration_and_writes_the_score_table(tmp_path: Path, monkeypatch):
    preregistration = tmp_path / "PREREGISTRATION.md"
    preregistration.write_text("MAESTRO test pre-registration.\n", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "maestro-evaluate",
            "--public-cases", str(PUBLIC),
            "--private-results", str(PRIVATE),
            "--workspace", str(ROOT),
            "--output", str(tmp_path / "out"),
            "--state-root", str(tmp_path / "state"),
            "--mode", "decision",
            "--policy", "protocol",
            "--costing", str(COSTING_PUBLIC),
            "--preregistration", str(preregistration),
            "--score-table",
            "--run-id", "protocol-test",
        ],
    )
    assert cli.main() == 0
    run = tmp_path / "out" / "runs" / "protocol-test"
    payload = json.loads((run / "evaluation_protocol_decision.json").read_text(encoding="utf-8"))
    assert payload["preregistration"]["sha256"] == hashlib.sha256(preregistration.read_bytes()).hexdigest()
    assert payload["preregistration"]["unchanged_during_run"] is True
    assert payload["costing"]["identifier"] == "contract-and-boundary-cases-v1"
    assert {report["policy"] for report in payload["reports"]} == {
        "fixed_expert",
        "prediction_value_heuristic",
        "prediction_value_shuffled",
        "prediction_value_removed",
        "maestro_core",
        "repair_disabled",
        "random_legal_edit",
        "outcome_aware_selection",
    }
    assert not (tmp_path / "out" / "runs" / "protocol-test" / "maestro_core").exists()
    table = json.loads((run / "score_table_protocol_decision.json").read_text(encoding="utf-8"))
    assert len(table["rows"]) == 6
    assert table["exit_verdict"]["input"] == "declared prediction_value"
    assert table["provenance"]["costing_sha256"] == payload["costing"]["sha256"]
