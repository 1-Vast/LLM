"""Exercise the SQLite-backed case lifecycle across plan and result states.

File summary
- Path: tests/test_case_lifecycle.py
- Purpose: Exercise the SQLite-backed case lifecycle across plan and result states.
- Core points:
  - Checks `CaseStore` plan-versioning, budget, and result idempotency boundaries.
  - A real measurement result must pass condition and replicate checks.
- Interfaces: `test_*` functions, `StubClient`
- Depends on: agent.memory, agent.memory, agent.context, agent.knowledge, agent.memory, agent.orchestrator, agent.planner, agent.llm, maestro
"""
from pathlib import Path
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from agent.memory import RunLogger
from agent.memory import CaseState, CaseStore, MeasurementResult
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryScope, MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.llm import VisualInspector
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent
from maestro.models import EvidenceKind

from tests.fixtures.stub_client import StubClient  # noqa: E402


def test_parallel_results_update_budget_and_completion_atomically(tmp_path, monkeypatch):
    from tests.test_restart_contract import setup_case, result
    store = setup_case(tmp_path)
    barrier = Barrier(2)
    unlocked_reads = Barrier(2)
    original = store._case_row

    def read_case(connection, case_id):
        row = original(connection, case_id)
        if not connection.in_transaction:
            # Force the old unlocked readers to see the same stale case. A
            # write transaction must already exist before either first read.
            unlocked_reads.wait(timeout=5)
        return row
    monkeypatch.setattr(store, "_case_row", read_case)

    def submit(name):
        barrier.wait(timeout=5)
        return store.import_measurement("case", result(name))

    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = tuple(pool.map(submit, ("a", "b")))
    monkeypatch.setattr(store, "_case_row", original)
    assert all(receipt.created for receipt in receipts)
    assert len(store.result_identities("case")) == 2
    assert store.snapshot("case").spent == 2
    assert store.snapshot("case").state is CaseState.NEXT_ROUND
    assert not store.pending_actions("case")


def test_parallel_result_retries_are_idempotent(tmp_path):
    from tests.test_restart_contract import setup_case, result
    store = setup_case(tmp_path)
    barrier = Barrier(2)

    def submit(_):
        barrier.wait(timeout=5)
        return store.import_measurement("case", result("a"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = tuple(pool.map(submit, range(2)))
    assert sorted(receipt.created for receipt in receipts) == [False, True]
    assert store.snapshot("case").spent == 1
    assert [row["action_identifier"] for row in store.pending_actions("case")] == ["b"]
def _controller(tmp_path: Path) -> tuple[MAESTROOrchestrator, EvidenceLedger]:
    client = StubClient(
        [
            {
                "task_type": "mechanism_diagnosis",
                "research_question": "Resolve the intervention discrepancy.",
                "target_or_targets": ["TARGET"],
                "interventions": ["compound"],
                "biological_context": "cell-line-a",
                "phenotype_endpoint": "viability",
                "supplied_evidence": [],
                "constraints": [],
                "missing_information": [],
                "needs_visual_review": False,
            },
            {
                "identifier": "contrast-1",
                "hypotheses": [
                    {"identifier": "a", "description": "A", "proposed_action": "continue"},
                    {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"},
                ],
                "differing_assumptions": ["functional state"],
                "action_identifier": "measurement-1",
                "outcome_categories": ["high", "low"],
                "interpretation_boundaries": ["A measurement is not a permanent target verdict."],
            },
        ]
    )
    root = tmp_path / "log" / "20260910"
    memory = MemoryStore(root / "memory.sqlite")
    evidence = EvidenceLedger(root / "evidence.sqlite")
    return (
        MAESTROOrchestrator(
            interpreter=TaskInterpreter(client),
            context_builder=ContextBuilder(evidence, memory),
            planner=MechanismContrastPlanner(client),
            visual_inspector=VisualInspector(client, "vision"),
            memory=memory,
            logger=RunLogger(root),
            controller=MAESTROAgent(),
            case_store=CaseStore(root / "cases.sqlite"),
        ),
        evidence,
    )


def test_case_plan_result_import_is_idempotent_and_preserves_real_measurement_lineage(tmp_path: Path):
    controller, evidence = _controller(tmp_path)
    action = EvidenceAction(
        "measurement-1", "Measure viability.", 5.0, ("a", "b"),
        expected_outcomes={"a": "viability_high", "b": "viability_low"},
    )
    turn = controller.run(
        "Plan a measurement.",
        available_actions=(action,),
        intervention_profile=FunctionalInterventionProfile(mode="inhibition", context_identifier="cell-line-a"),
        case_id="case-1",
        budget=5.0,
    )

    assert turn.case is not None
    assert turn.case.state is CaseState.AWAITING_RESULT
    result = MeasurementResult(
        action_identifier="measurement-1",
        statement="The planned viability measurement was observed.",
        source_id="assay-run-001",
        context_identifier="cell-line-a",
        time_hours=None,
        independent_units=3,
        quality_passed=True,
        conditions={"dose_uM": "1", "exposure_hours": "24"},
        result_id="result-1",
    )
    imported = controller.import_measurement("case-1", result)
    repeated = controller.import_measurement("case-1", result)

    assert imported.created
    assert not repeated.created
    assert imported.snapshot.state is CaseState.NEXT_ROUND
    assert imported.snapshot.remaining_budget == 0.0
    record = evidence.retrieve("planned viability measurement", limit=1, scope=MemoryScope(case_id="case-1"))[0]
    assert record.evidence_kind is EvidenceKind.REAL_MEASUREMENT
    with sqlite3.connect(tmp_path / "log" / "20260910" / "cases.sqlite") as connection:
        conditions_json = connection.execute(
            "SELECT conditions_json FROM results WHERE result_id = 'result-1'"
        ).fetchone()[0]
    assert '"dose_uM": "1"' in conditions_json


def test_case_store_rejects_result_with_wrong_planned_conditions(tmp_path: Path):
    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case("case-2", budget=10.0)
    action = EvidenceAction("action", "Measure.", 2.0, ("a", "b"), time_hours=24.0)
    store.record_plan("case-2", (action,), ready_to_measure=True, context_identifier="cell-a")

    try:
        store.import_measurement(
            "case-2",
            MeasurementResult("action", "Observed.", "run", "cell-b", 24.0, 2, True),
        )
    except ValueError as error:
        assert "context" in str(error)
    else:
        raise AssertionError("Expected mismatched result context to be rejected.")


def test_case_store_defers_an_action_that_exceeds_the_remaining_budget(tmp_path: Path):
    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case("case-3", budget=1.0)
    action = EvidenceAction("action", "Measure.", 2.0, ("a", "b"))

    snapshot = store.record_plan("case-3", (action,), ready_to_measure=True, context_identifier=None)

    assert snapshot.state is CaseState.DEFERRED
    assert snapshot.stop_reason is not None


def test_case_store_waits_for_every_action_in_a_selected_bundle(tmp_path: Path):
    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case("case-4", budget=5.0)
    first = EvidenceAction("first", "First measurement.", 2.0, ("a",))
    second = EvidenceAction("second", "Second measurement.", 3.0, ("b",))
    store.record_plan("case-4", (first, second), ready_to_measure=True, context_identifier="cell-a")

    first_result = store.import_measurement(
        "case-4", MeasurementResult("first", "Observed.", "run-1", "cell-a", None, 2, True)
    )
    second_result = store.import_measurement(
        "case-4", MeasurementResult("second", "Observed.", "run-2", "cell-a", None, 2, True)
    )

    assert first_result.snapshot.state is CaseState.AWAITING_RESULT
    assert first_result.snapshot.spent == 2.0
    assert second_result.snapshot.state is CaseState.NEXT_ROUND
    assert second_result.snapshot.spent == 5.0


def test_case_store_does_not_overwrite_an_unfinished_action_bundle(tmp_path: Path):
    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case("case-5", budget=5.0)
    first = EvidenceAction("first", "First measurement.", 2.0, ("a",))
    replacement = EvidenceAction("replacement", "Replacement measurement.", 2.0, ("b",))
    original = store.record_plan("case-5", (first,), ready_to_measure=True, context_identifier="cell-a")
    resumed = store.record_plan("case-5", (replacement,), ready_to_measure=True, context_identifier="cell-a")

    assert resumed.state is CaseState.AWAITING_RESULT
    assert resumed.plan_version == original.plan_version
    imported = store.import_measurement(
        "case-5", MeasurementResult("first", "Observed.", "run-1", "cell-a", None, 2, True)
    )
    assert imported.snapshot.state is CaseState.NEXT_ROUND


def test_failed_action_keeps_sibling_results_importable_and_charges_both(tmp_path):
    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case("partial", budget=5)
    actions = (EvidenceAction("failed", "A", 2, ("a",)), EvidenceAction("valid", "B", 3, ("b",)))
    store.record_plan("partial", actions, ready_to_measure=True, context_identifier="cell-a")
    failed = MeasurementResult("failed", "QC failed", "run-1", "cell-a", None, None, False, result_id="f")
    first = store.import_measurement("partial", failed)
    assert first.snapshot.state is CaseState.AWAITING_RESULT
    second = store.import_measurement("partial", MeasurementResult(
        "valid", "Observed", "run-2", "cell-a", None, 2, True, result_id="v"))
    assert second.snapshot.state is CaseState.RESULT_QC_FAILED
    assert second.snapshot.spent == 5
    assert not store.import_measurement("partial", failed).created


def test_execution_and_cancellation_are_separate_and_idempotent(tmp_path):
    import pytest
    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case("arms", budget=5)
    actions = (EvidenceAction("run", "A", 2, ("a",)), EvidenceAction("cancel", "B", 3, ("b",)))
    store.record_plan("arms", actions, ready_to_measure=True, context_identifier="cell-a")
    store.start_action("arms", 1, "run", attempt_id="attempt-1", source="operator-receipt")
    assert store.start_action("arms", 1, "run", attempt_id="attempt-1", source="operator-receipt").spent == 0
    with pytest.raises(ValueError, match="unexecuted"):
        store.cancel_unexecuted_action("arms", 1, "run", reason="not used")
    cancelled = store.cancel_unexecuted_action("arms", 1, "cancel", reason="no material")
    assert cancelled.state is CaseState.AWAITING_RESULT and cancelled.spent == 0
    assert store.cancel_unexecuted_action("arms", 1, "cancel", reason="no material") == cancelled
    result = MeasurementResult("run", "QC failed", "run-source", "cell-a", None, None, False,
                               result_id="failed", plan_version=1)
    assert store.import_measurement("arms", result).snapshot.spent == 2
    arms = store.action_states("arms", 1)
    assert {a["status"] for a in arms} == {"qc_failed", "cancelled"}
    assert next(a for a in arms if a["status"] == "qc_failed")["attempt_id"] == "attempt-1"


def test_repeated_action_requires_explicit_plan_attribution(tmp_path):
    import pytest
    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case("repeat", budget=3)
    action = EvidenceAction("a", "A", 1, ("h",))
    store.record_plan("repeat", (action,), ready_to_measure=True, context_identifier=None)
    store.import_measurement("repeat", MeasurementResult("a", "First", "s1", None, None, 1, True, result_id="r1"))
    store.record_plan("repeat", (action,), ready_to_measure=True, context_identifier=None)
    ambiguous = MeasurementResult("a", "Next", "s2", None, None, 1, True, result_id="r2")
    with pytest.raises(ValueError, match="ambiguous_result_plan_version"):
        store.import_measurement("repeat", ambiguous)
    from dataclasses import replace
    assert store.import_measurement("repeat", replace(ambiguous, plan_version=2)).snapshot.spent == 2


def test_prediction_is_not_an_execution_result_or_consumed_budget(tmp_path):
    import pytest
    from maestro.models import EvidenceKind
    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case("forecast", budget=1)
    action = EvidenceAction("a", "A", 1, ("h",))
    store.record_plan("forecast", (action,), ready_to_measure=True, context_identifier=None)
    with pytest.raises(ValueError, match="only_real_measurements"):
        store.import_measurement("forecast", MeasurementResult("a", "Predicted", "model", None, None, 1, True,
            evidence_kind=EvidenceKind.MODEL_PREDICTION, result_id="fake"))
    assert store.snapshot("forecast").state is CaseState.AWAITING_RESULT
    assert store.snapshot("forecast").spent == 0
    assert store.budget_status("forecast")["reserved"] == 1


def test_derived_record_is_accepted_only_for_a_registered_review(tmp_path):
    import pytest
    from maestro.models import EvidenceActionKind, EvidenceKind
    store = CaseStore(tmp_path / "cases.sqlite")
    source = MeasurementResult("a", "Derived published record", "published-source", None, None, None, True,
                               evidence_kind=EvidenceKind.DERIVED_ANALYSIS, result_id="derived")
    for case, kind in (("measurement", EvidenceActionKind.READOUT_MEASUREMENT),
                       ("review", EvidenceActionKind.EVIDENCE_REVIEW)):
        store.open_case(case, budget=1)
        store.record_plan(case, (EvidenceAction("a", "A", 1, ("h",), kind=kind),),
                          ready_to_measure=True, context_identifier=None)
        if case == "measurement":
            with pytest.raises(ValueError, match="requires_registered_evidence_review"):
                store.import_measurement(case, source)
            assert store.snapshot(case).spent == 0
        else:
            assert store.import_measurement(case, source).snapshot.spent == 1
            assert store.action_states(case, 1)[0]["action_kind"] == kind.value
