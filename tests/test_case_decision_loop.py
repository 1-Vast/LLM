"""End-to-end case loop: interpretation, set update, and a bounded development decision.

File summary
- Path: tests/test_case_decision_loop.py
- Purpose: Drive a multi-round case loop and check set-based updates and the decision layer.
- Core points:
  - Exercises `run_case_loop` with stubbed clients and asserts evidence-state transitions.
  - A qualified, condition-matched result, not budget exhaustion, licenses a decision.
- Interfaces: `test_*` functions
- Depends on: agent.audit, agent.cases, agent.context, agent.knowledge, agent.memory, agent.orchestrator, agent.planner, agent.vision, maestro
"""
from pathlib import Path

from maestro.models import BiologicalQuantity

from agent.audit import RunLogger
from agent.cases import CaseState, CaseStore, MeasurementResult
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.vision import VisualInspector
from maestro import (
    MODE_COMPARATOR_FIELD,
    MODE_DIFFERENCE_FIELD,
    SUFFICIENT_FUNCTION_FIELD,
    DecisionStatus,
    DevelopmentAction,
    EvidenceAction,
    EvidenceActionKind,
    EvidenceKind,
    EvidenceScope,
    FunctionalInterventionProfile,
    MAESTROAgent,
    RepairKind,
)

from tools.shared.stub_client import StubClient  # noqa: E402

TASK = {
    "task_type": "mechanism_diagnosis",
    "research_question": "Resolve the genetic-pharmacological discrepancy.",
    "target_or_targets": ["TARGET"],
    "interventions": ["compound"],
    "biological_context": "cell-a",
    "phenotype_endpoint": "viability",
    "supplied_evidence": [],
    "constraints": [],
    "missing_information": [],
    "needs_visual_review": False,
}

PLAN = {
    "identifier": "contrast",
    "hypotheses": [
        {
            "identifier": "incomplete_perturbation",
            "description": "A",
            "proposed_action": "revise_intervention",
            "causal_factor": "incomplete_perturbation",
        },
        {
            "identifier": "mode_non_equivalence",
            "description": "B",
            "proposed_action": "change_intervention_mode",
            "causal_factor": "mode_non_equivalence",
        },
    ],
    "differing_assumptions": ["functional implementation"],
    "action_identifier": "comparator",
    "outcome_categories": ["sufficient", "insufficient"],
    "interpretation_boundaries": ["Functional engagement remains a prerequisite."],
}


def _mode_evidence() -> tuple[str, ...]:
    """Function, phenotype, and a matched-mode comparison: what a mode change rests on."""

    return ("phenotype:viability:unaffected", MODE_COMPARATOR_FIELD, MODE_DIFFERENCE_FIELD)
def _actions() -> tuple[EvidenceAction, ...]:
    return (
        EvidenceAction(
            "functional",
            "Measure proximal target activity.",
            2.0,
            ("incomplete_perturbation",),
            kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT,
            quantity=BiologicalQuantity.PROXIMAL_ACTIVITY,
            supplies=(SUFFICIENT_FUNCTION_FIELD, "functional:target_activity:insufficient"),
            time_hours=24.0,
        ),
        EvidenceAction(
            "comparator",
            "Compare degradation with inhibition.",
            3.0,
            ("incomplete_perturbation", "mode_non_equivalence"),
            kind=EvidenceActionKind.MODE_MATCHED_COMPARATOR,
            quantity=BiologicalQuantity.VIABILITY,
            supplies=_mode_evidence(),
            prerequisites=("functional:target_activity:sufficient",),
            time_hours=24.0,
            expected_outcomes={
                "incomplete_perturbation": "concordant_mode_response",
                "mode_non_equivalence": "discordant_mode_response",
            },
        ),
    )


def _profile() -> FunctionalInterventionProfile:
    return FunctionalInterventionProfile(mode="drug", context_identifier="cell-a")


def _orchestrator(tmp_path: Path, responses) -> MAESTROOrchestrator:
    root = tmp_path / "log" / "20260911"
    memory = MemoryStore(root / "memory.sqlite")
    client = StubClient(responses)
    return MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision"),
        memory=memory,
        logger=RunLogger(root),
        controller=MAESTROAgent(),
        case_store=CaseStore(root / "cases.sqlite"),
    )


def _result(identifier: str, fields: tuple[str, ...], **overrides) -> MeasurementResult:
    payload = {
        "action_identifier": identifier,
        "statement": "Measured.",
        "source_id": "source-a",
        "context_identifier": "cell-a",
        "time_hours": 24.0,
        "independent_units": 3,
        "quality_passed": True,
        "interpretation_fields": fields,
        "result_id": f"result-{identifier}",
    }
    payload.update(overrides)
    return MeasurementResult(**payload)


def test_insufficient_perturbation_licenses_an_implementation_repair(tmp_path: Path):
    controller = _orchestrator(tmp_path, [TASK, PLAN, TASK, PLAN])
    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        result_provider=lambda action, turn: (
            _result("functional", ("functional:target_activity:insufficient",))
            if action.identifier == "functional"
            else None
        ),
        case_id="case-repair",
        budget=5.0,
        max_rounds=2,
    )
    assert loop.decision is not None
    assert loop.decision.status is DecisionStatus.DECIDED
    assert loop.decision.action is DevelopmentAction.REVISE_INTERVENTION
    assert loop.evidence_state is not None and loop.evidence_state.still_ambiguous
    assert loop.repair_trajectory
    assert loop.repair_trajectory[0]["kind"] == RepairKind.ADD_FUNCTIONAL_MEASUREMENT.value
    assert loop.repair_trajectory[0]["adopted"] is True


def test_sufficient_function_alone_does_not_change_the_intervention_mode(tmp_path: Path):
    """A sufficient-function result proposes a mode comparison; it does not decide one."""

    controller = _orchestrator(tmp_path, [TASK, PLAN])
    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        result_provider=lambda action, turn: (
            _result("functional", (SUFFICIENT_FUNCTION_FIELD,))
            if action.identifier == "functional"
            else None
        ),
        case_id="case-sufficient-only",
        budget=5.0,
        max_rounds=1,
    )
    assert loop.decision is not None
    assert loop.decision.status is not DecisionStatus.DECIDED
    assert loop.evidence_state is not None
    assert loop.evidence_state.still_ambiguous
    assert loop.evidence_state.mechanism_updates() == ()


def test_functional_assay_cannot_spoof_a_matched_comparator(tmp_path: Path):
    controller = _orchestrator(tmp_path, [TASK, PLAN])
    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        result_provider=lambda action, turn: (
            _result("functional", _mode_evidence())
            if action.identifier == "functional"
            else None
        ),
        case_id="case-resolved",
        budget=5.0,
        max_rounds=1,
    )
    assert loop.decision is not None
    assert loop.decision.status is not DecisionStatus.DECIDED
    assert loop.evidence_state is not None and loop.evidence_state.still_ambiguous
    assert not loop.evidence_state.mechanism_updates()
    assert not loop.measured_premises


def test_failed_measurement_is_kept_but_does_not_update_the_mechanism(tmp_path: Path):
    controller = _orchestrator(tmp_path, [TASK, PLAN])
    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        result_provider=lambda action, turn: (
            _result(
                "functional",
                ("functional:target_activity:sufficient",),
                quality_passed=False,
                limitations=("signal below detection",),
            )
            if action.identifier == "functional"
            else None
        ),
        case_id="case-quality",
        budget=5.0,
        max_rounds=1,
    )
    assert loop.evidence_state is not None
    assert loop.evidence_state.still_ambiguous
    assert loop.evidence_state.mechanism_updates() == ()
    assert loop.decision is not None
    assert loop.decision.status is not DecisionStatus.DECIDED
    assert loop.stop_reason == "result_quality_failed"


def test_two_rounds_record_whether_a_repair_gap_was_actually_closed(tmp_path: Path):
    controller = _orchestrator(tmp_path, [TASK, PLAN, TASK, PLAN])
    results = {
        "functional": _result(
            "functional", (SUFFICIENT_FUNCTION_FIELD, "phenotype:viability:unaffected")
        ),
        "comparator": _result("comparator", _mode_evidence()),
    }
    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        result_provider=lambda action, turn: results.get(action.identifier),
        case_id="case-two-rounds",
        budget=10.0,
        max_rounds=2,
    )
    assert tuple(action.identifier for turn in loop.turns for action in turn.selected_actions) == (
        "functional",
        "comparator",
    )
    resolved = [row for row in loop.repair_trajectory if row["gap_resolved"] is True]
    assert resolved, "An adopted repair must be scored against its own qualified observation."
    assert resolved[0]["result_id"] == "result-functional"
    assert loop.decision is not None
    assert loop.decision.status is DecisionStatus.DECIDED
    assert loop.decision.action is DevelopmentAction.CHANGE_INTERVENTION_MODE
    assert loop.evidence_state.candidates == frozenset({"mode_non_equivalence"})
    assert controller._case_store.snapshot("case-two-rounds").state is CaseState.COMPLETED


def test_prediction_derived_results_never_become_mechanism_updates(tmp_path: Path):
    controller = _orchestrator(tmp_path, [TASK, PLAN])
    loop = controller.run_case_loop(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        result_provider=lambda action, turn: (
            _result(
                "functional",
                ("functional:target_activity:sufficient",),
                evidence_kind=EvidenceKind.MODEL_PREDICTION,
            )
            if action.identifier == "functional"
            else None
        ),
        case_id="case-prediction",
        budget=5.0,
        max_rounds=1,
    )
    assert loop.evidence_state is not None
    assert loop.evidence_state.still_ambiguous
    assert all(
        update.scope is not EvidenceScope.MECHANISM_CONTRAST
        for update in loop.evidence_state.updates
    )


def test_repair_records_are_exposed_on_a_single_turn(tmp_path: Path):
    controller = _orchestrator(tmp_path, [TASK, PLAN])
    turn = controller.run(
        "Resolve the discrepancy.",
        available_actions=_actions(),
        intervention_profile=_profile(),
        case_id="case-single",
        budget=5.0,
    )
    assert turn.repair is not None
    assert turn.repair.kind is RepairKind.ADD_FUNCTIONAL_MEASUREMENT
    assert turn.repair_records
    assert turn.repair_stop_reason in {
        "no_progress",
        "repair_cycle_detected",
        "max_attempts_reached",
        "ready",
        "no_registered_repair",
    }
    assert turn.selected_actions == (_actions()[0],)
