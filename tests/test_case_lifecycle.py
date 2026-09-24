"""Exercise the SQLite-backed case lifecycle across plan and result states.

File summary
- Path: tests/test_case_lifecycle.py
- Purpose: Exercise the SQLite-backed case lifecycle across plan and result states.
- Core points:
  - Checks `CaseStore` plan-versioning, budget, and result idempotency boundaries.
  - A real measurement result must pass condition and replicate checks.
- Interfaces: `test_*` functions, `StubClient`
- Depends on: agent.audit, agent.cases, agent.context, agent.knowledge, agent.memory, agent.orchestrator, agent.planner, agent.vision, maestro
"""
from pathlib import Path
import sqlite3

from agent.audit import RunLogger
from agent.cases import CaseState, CaseStore, MeasurementResult
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.vision import VisualInspector
from maestro import EvidenceAction, EvidenceKind, FunctionalInterventionProfile, MAESTROAgent

from tools.shared.stub_client import StubClient  # noqa: E402
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
    record = evidence.retrieve("planned viability measurement", limit=1)[0]
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
