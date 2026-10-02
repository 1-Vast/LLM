"""Shared synthetic orchestration fixtures; no biological observations."""
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.llm import VisualInspector
from agent.memory import CaseStore, MemoryStore, RunLogger
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from maestro import EvidenceAction
from tests.fixtures.stub_client import StubClient


TASK = {
    "task_type": "mechanism_diagnosis", "research_question": "Resolve discrepancy.",
    "target_or_targets": ["TARGET"], "interventions": ["compound"],
    "biological_context": "cell-a", "phenotype_endpoint": "viability",
    "supplied_evidence": [], "constraints": [], "missing_information": [], "needs_visual_review": False,
}


def _plan(action):
    return {
        "identifier": "contrast", "hypotheses": [
            {"identifier": "a", "description": "A", "proposed_action": "continue"},
            {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"},
        ],
        "differing_assumptions": ["implementation"], "action_identifier": action,
        "outcome_categories": ["a", "b"], "interpretation_boundaries": ["A real result remains necessary."],
    }


def _controller(root, responses, *, case_store=True):
    client = StubClient(responses)
    memory = MemoryStore(root / "memory.sqlite")
    return MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client), visual_inspector=VisualInspector(client, "unused"),
        memory=memory, logger=RunLogger(root),
        case_store=CaseStore(root / "cases.sqlite") if case_store else None,
    )


def _action(identifier="assay"):
    return EvidenceAction(identifier, "Assay", 1.0, ("a", "b"), expected_outcomes={"a": "a", "b": "b"})
