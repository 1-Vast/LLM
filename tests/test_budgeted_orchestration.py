"""Validate budgeted orchestration, planning, and case-loop behaviour.

File summary
- Path: tests/test_budgeted_orchestration.py
- Purpose: Validate budgeted orchestration, planning, and case-loop behaviour.
- Core points:
  - Exercises `MAESTROOrchestrator.run` and `run_case_loop` with stubbed LLM clients.
  - Confirms budget, prerequisite, and mechanism-contrast scoping hold end to end.
- Interfaces: `test_*` functions, `StubClient`
- Depends on: agent.audit, agent.cases, agent.context, agent.knowledge, agent.memory, agent.orchestrator, agent.planner, agent.vision, maestro
"""
from pathlib import Path

from agent.audit import RunLogger
from agent.cases import CaseState, CaseStore
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.vision import VisualInspector
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent

from tools.shared.stub_client import StubClient  # noqa: E402
def test_orchestrator_adopts_a_budget_feasible_action_bundle(tmp_path: Path):
    client = StubClient(
        [
            {
                "task_type": "mechanism_diagnosis",
                "research_question": "Resolve a discrepancy.",
                "target_or_targets": ["TARGET"],
                "interventions": ["compound"],
                "biological_context": "cell line",
                "phenotype_endpoint": "viability",
                "supplied_evidence": [],
                "constraints": [],
                "missing_information": [],
                "needs_visual_review": False,
            },
            {
                "identifier": "contrast",
                "hypotheses": [
                    {"identifier": "a", "description": "A", "proposed_action": "continue"},
                    {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"},
                ],
                "differing_assumptions": ["implementation"],
                "action_identifier": "expensive",
                "outcome_categories": ["a", "b"],
                "interpretation_boundaries": ["A real result remains necessary."],
            },
        ]
    )
    root = tmp_path / "log" / "20260910"
    memory = MemoryStore(root / "memory.sqlite")
    controller = MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision"),
        memory=memory,
        logger=RunLogger(root),
        controller=MAESTROAgent(),
        case_store=CaseStore(root / "cases.sqlite"),
    )
    actions = (
        EvidenceAction(
            "a", "Resolve a.", 2.0, ("a",),
            expected_outcomes={"a": "outcome_a", "b": "outcome_b"},
        ),
        EvidenceAction(
            "b", "Resolve b.", 3.0, ("b",),
            expected_outcomes={"a": "outcome_a", "b": "outcome_b"},
        ),
        EvidenceAction("expensive", "Resolve both.", 6.0, ("a", "b"), expected_outcomes={"a": "outcome_a", "b": "outcome_b"}),
    )

    turn = controller.run(
        "Resolve this discrepancy.",
        available_actions=actions,
        intervention_profile=FunctionalInterventionProfile(mode="inhibition"),
        case_id="bundle-case",
        budget=5.0,
    )

    assert tuple(action.identifier for action in turn.selected_actions) == ("a", "b")
    assert turn.check is not None and turn.check.ready_for_mechanism_update
    assert turn.case is not None and turn.case.state is CaseState.AWAITING_RESULT
