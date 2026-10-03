"""Verify a multi-round case loop replans only after a qualified result.

File summary
- Path: tests/test_case_control_loop.py
- Purpose: Verify a multi-round case loop replans only after a qualified result.
- Core points:
  - Stops before fabricating any unavailable measurement.
  - Asserts reflection classes and case state transitions under a fixed budget.
- Interfaces: `test_*` functions, `StubClient`
- Depends on: agent.memory, agent.memory, agent.context, agent.knowledge, agent.memory, agent.orchestrator, agent.planner, agent.llm, maestro
"""
from pathlib import Path
import hashlib
import json
import pytest

from maestro.models import BiologicalQuantity

from agent.memory import RunLogger
from agent.memory import CaseState, CaseStore, MeasurementResult
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.llm import VisualInspector
from maestro.models import DevelopmentAction, EvidenceActionKind
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent

from tests.fixtures.stub_client import StubClient  # noqa: E402
def _intent():
    return {
        "task_type": "mechanism_diagnosis",
        "research_question": "Resolve the genetic-pharmacology discrepancy.",
        "target_or_targets": ["TARGET"],
        "interventions": ["compound"],
        "biological_context": "cell-a",
        "phenotype_endpoint": "viability",
        "supplied_evidence": [],
        "constraints": [],
        "missing_information": [],
        "needs_visual_review": False,
    }


def _contrast(action_identifier: str):
    return {
        "identifier": "contrast",
        "hypotheses": [
            {"identifier": "functional-gap", "description": "Insufficient engagement.", "proposed_action": "revise_intervention", "causal_factor": "incomplete_perturbation"},
            {"identifier": "mode-gap", "description": "Interventions are not equivalent.", "proposed_action": "change_intervention_mode", "causal_factor": "mode_non_equivalence"},
        ],
        "differing_assumptions": ["functional implementation"],
        "action_identifier": action_identifier,
        "outcome_categories": ["functional", "mode"],
        "interpretation_boundaries": ["Only real measurements may update this contrast."],
    }


def _controller(tmp_path: Path, responses) -> tuple[MAESTROOrchestrator, MemoryStore, CaseStore]:
    root = tmp_path / "log" / "20260910"
    client = StubClient(responses)
    memory = MemoryStore(root / "memory.sqlite")
    store = CaseStore(root / "cases.sqlite")
    return (
        MAESTROOrchestrator(
            interpreter=TaskInterpreter(client),
            context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
            planner=MechanismContrastPlanner(client),
            visual_inspector=VisualInspector(client, "vision"),
            memory=memory,
            logger=RunLogger(root),
            controller=MAESTROAgent(),
            case_store=store,
        ),
        memory,
        store,
    )


def test_case_loop_replans_only_after_a_qualified_explicit_functional_result(tmp_path: Path):
    controller, memory, store = _controller(
        tmp_path,
        [_intent(), _contrast("mode"), _intent(), _contrast("mode")],
    )
    functional = EvidenceAction(
        "functional", "Measure target activity.", 3.0,
        ("functional-gap", "mode-gap"), kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT,
        quantity=BiologicalQuantity.PROXIMAL_ACTIVITY,
        time_hours=24.0,
        expected_outcomes={"functional-gap": "insufficient_engagement", "mode-gap": "sufficient_engagement"},
    )
    mode = EvidenceAction(
        "mode", "Compare matched intervention modes.", 2.0,
        ("functional-gap", "mode-gap"), prerequisites=("functional:target_activity:sufficient",),
        time_hours=24.0,
        expected_outcomes={"functional-gap": "concordant_mode_response", "mode-gap": "discordant_mode_response"},
    )

    def provider(action, turn):
        del turn
        if action.identifier == "functional":
            return MeasurementResult(
                "functional", "Target activity was sufficient at the planned condition.", "assay-functional",
                "cell-a", 24.0, 3, True,
                interpretation_fields=(
                    "functional:target_activity:sufficient",
                    "phenotype:viability:unaffected",
                ),
                result_id="functional-result",
            )
        return MeasurementResult(
            "mode", "Matched modes produced distinct results.", "assay-mode",
            "cell-a", 24.0, 3, True, result_id="mode-result",
        )

    loop = controller.run_case_loop(
        "Resolve the discrepancy.", available_actions=(functional, mode),
        intervention_profile=FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        result_provider=provider, case_id="loop-case", budget=5.0, max_rounds=3,
    )

    assert [turn.selected_actions[0].identifier for turn in loop.turns] == ["functional", "mode"]
    # A stage decision outranks a resource limit: exhausting the budget is recorded as the
    # deferral it caused, not as evidence, and never as a separate silent stop.
    assert loop.stop_reason == "decision:deferred"
    assert loop.decision is not None
    assert loop.decision.action is DevelopmentAction.DEFER
    assert "no_executable_evidence_path" in loop.decision.unmet_requirements
    assert [reflection.outcome_class for reflection in loop.reflections] == [
        "qualified_result_received", "measurement_without_interpretation_premise",
    ]
    assert store.snapshot("loop-case").state is CaseState.DEFERRED
    memories = memory.search("Post-observation reflection", limit=4)
    assert len(memories) == 2
    assert memories[0].status.value == "derived"


def test_case_loop_stops_without_fabricating_an_unavailable_result(tmp_path: Path):
    controller, _, store = _controller(tmp_path, [_intent(), _contrast("measurement")])
    action = EvidenceAction(
        "measurement", "Measure viability.", 1.0, ("functional-gap", "mode-gap"),
        expected_outcomes={"functional-gap": "viability_restored", "mode-gap": "viability_divergent"},
    )

    loop = controller.run_case_loop(
        "Resolve the discrepancy.", available_actions=(action,),
        intervention_profile=FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        result_provider=lambda action, turn: None,
        case_id="awaiting-case", budget=1.0, max_rounds=3,
    )

    assert len(loop.turns) == 1
    assert loop.reflections == ()
    assert loop.stop_reason == "awaiting_result"
    assert store.snapshot("awaiting-case").state is CaseState.AWAITING_RESULT


def test_result_quality_failure_is_the_primary_stop_reason(tmp_path: Path):
    controller, _, _ = _controller(tmp_path, [_intent(), _contrast("measurement")])
    action = EvidenceAction(
        "measurement", "Review a result.", 1.0, ("functional-gap", "mode-gap"),
        expected_outcomes={"functional-gap": "viability_restored", "mode-gap": "viability_divergent"},
    )

    loop = controller.run_case_loop(
        "Resolve the discrepancy.", available_actions=(action,),
        intervention_profile=FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        result_provider=lambda selected, turn: MeasurementResult(
            selected.identifier, "Unqualified public fit.", "public-record", "cell-a",
            None, None, False, result_id="unqualified-result",
        ),
        case_id="quality-case", budget=1.0, max_rounds=2,
    )

    assert loop.stop_reason == "result_quality_failed"
    assert not loop.evidence_state.mechanism_updates()
    assert loop.reflections[0].outcome_class == "record_quality_failed"


@pytest.mark.parametrize("valid_present", [True, False])
def test_qc_failure_drains_committed_bundle_before_stopping(tmp_path, valid_present):
    controller, _, store = _controller(tmp_path, [_intent(), _contrast("failed")])
    actions = (
        EvidenceAction("failed", "Assay A", 1, ("functional-gap",),
                       expected_outcomes={"functional-gap": "a", "mode-gap": "b"}),
        EvidenceAction("valid", "Assay B", 1, ("mode-gap",),
                       expected_outcomes={"functional-gap": "a", "mode-gap": "b"}),
    )
    calls = []
    def provider(action, turn):
        calls.append((action.identifier, turn.case.plan_version))
        if action.identifier == "valid" and not valid_present:
            return None
        return MeasurementResult(action.identifier, "Instrument result", "instrument:" + action.identifier,
            "cell-a", None, 2, action.identifier == "valid", result_id="r:" + action.identifier,
            plan_version=turn.case.plan_version)

    loop = controller.run_case_loop("task", available_actions=actions,
        intervention_profile=FunctionalInterventionProfile("drug", context_identifier="cell-a"),
        result_provider=provider, case_id="bundle", budget=3, max_rounds=2)
    assert calls == [("failed", 1), ("valid", 1)]
    assert len(loop.turns) == 1
    assert loop.stop_reason == "result_quality_failed"
    assert len(loop.reflections) == (2 if valid_present else 1)
    assert store.snapshot("bundle").spent == (2 if valid_present else 1)
    assert store.snapshot("bundle").state is (CaseState.RESULT_QC_FAILED if valid_present else CaseState.AWAITING_RESULT)
    assert {a["status"] for a in store.action_states("bundle", 1)} == (
        {"qc_failed", "result_recorded"} if valid_present else {"qc_failed", "planned"})
    events = [json.loads(line) for line in controller._logger.events_path.read_text().splitlines()]
    receipts = [event["payload"] for event in events if event["kind"] == "round_result_recorded"]
    assert len(receipts) == (2 if valid_present else 1)
    assert len({receipt["path"] for receipt in receipts}) == len(receipts)
    for receipt in receipts:
        assert hashlib.sha256(Path(receipt["path"]).read_bytes()).hexdigest() == receipt["sha256"]
    review, = [event["payload"] for event in events if event["kind"] == "round_records_reviewed"]
    assert review["rounds"] == 1 and review["rounds_with_a_result"] == 1
