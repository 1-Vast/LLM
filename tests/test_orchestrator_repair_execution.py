"""A ruled repair must submit an executable functional measurement.

File summary
- Path: tests/test_orchestrator_repair_execution.py
- Purpose: A ruled repair must submit an executable functional measurement.
- Core points: assertions here are contract tests, not biological results; each test pins one boundary that must not silently move.
- Interfaces: `test_rule_repair_submits_an_executable_functional_measurement()`
- Depends on: agent, maestro
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
from maestro import EvidenceAction, EvidenceActionKind, FunctionalInterventionProfile, MAESTROAgent

from tools.shared.stub_client import StubClient  # noqa: E402
def test_rule_repair_submits_an_executable_functional_measurement(tmp_path: Path):
    client = StubClient(
        [
            {
                "task_type": "mechanism_diagnosis", "research_question": "Resolve discrepancy.",
                "target_or_targets": ["TARGET"], "interventions": ["compound"],
                "biological_context": "cell-a", "phenotype_endpoint": "viability",
                "supplied_evidence": [], "constraints": [], "missing_information": [], "needs_visual_review": False,
            },
            {
                "identifier": "contrast",
                "hypotheses": [
                    {"identifier": "a", "description": "A", "proposed_action": "continue"},
                    {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"},
                ],
                "differing_assumptions": ["functional implementation"], "action_identifier": "mode-comparison",
                "outcome_categories": ["a", "b"], "interpretation_boundaries": ["Functional engagement remains a prerequisite."],
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
    functional = EvidenceAction("functional", "Measure target activity.", 2.0, ("a",), kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT)
    mode = EvidenceAction("mode-comparison", "Compare modes.", 3.0, ("a", "b"), prerequisites=("functional:target_activity",))

    turn = controller.run(
        "Resolve discrepancy.",
        available_actions=(functional, mode),
        intervention_profile=FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
        case_id="repair-case",
        budget=5.0,
    )

    assert tuple(action.identifier for action in turn.selected_actions) == ("functional",)
    assert turn.case is not None and turn.case.state is CaseState.AWAITING_RESULT
