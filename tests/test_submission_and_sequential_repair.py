"""Terminal submission contract and sequential repair.

File summary
- Path: tests/test_submission_and_sequential_repair.py
- Purpose: Terminal submission contract and sequential repair.
- Core points: assertions here are contract tests, not biological results; each test pins one boundary that must not silently move.
- Interfaces: `test_terminal_submission_reports_structured_contract_failures()`, `test_terminal_submission_uses_one_format_only_retry()`, `test_llm_repair_can_adopt_an_executable_functional_measurement_without_unlocking_mechanism()`
- Depends on: agent, evaluation, maestro
"""
from pathlib import Path

from agent.audit import RunLogger
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.vision import VisualInspector
from evaluation.baselines import LLMActionPolicy, _parse_submission
from evaluation.cases import ReplayEnvironment
from maestro import EvidenceAction, EvidenceActionKind, FunctionalInterventionProfile, MAESTROAgent

from tools.shared.stub_client import StubClient  # noqa: E402
def _synthetic_view():
    from evaluation import CaseRepository

    root = Path(__file__).resolve().parents[1]
    case, outcomes = next(
        item for item in CaseRepository(
            root / "data/evaluation/cases/public", root / "data/evaluation/cases/private"
        ).load() if item[0].public.identifier == "synthetic-functional-calibration-001"
    )
    environment = ReplayEnvironment(case, outcomes)
    environment.query("functional_target_activity")
    return environment.view()


def test_terminal_submission_reports_structured_contract_failures():
    view = _synthetic_view()

    submission = _parse_submission(
        {
            "decision": "not-a-development-action",
            "evidence_ids": ["private-action"],
            "rationale": 7,
            "limitations": "not-a-list",
            "needs_more_evidence": "false",
        },
        view,
    )

    # Readiness is now carried by `decision_ready`; a malformed legacy flag is
    # reported against the field that actually governs the contract, and a
    # submission that is not ready must name the premise it is waiting for.
    assert submission.validation_errors == (
        "invalid_decision", "unrevealed_evidence_id", "invalid_rationale",
        "invalid_limitations", "invalid_decision_ready",
        "deferred_without_naming_a_missing_premise",
    )
    assert submission.submitted_payload == {
        "decision": "not-a-development-action", "evidence_ids": ["private-action"],
        "rationale": 7, "limitations": "not-a-list", "needs_more_evidence": "false",
        "decision_ready": None, "required_missing_premises": None,
    }


def test_a_supported_decision_stands_while_the_menu_is_still_open():
    """A nonempty menu is a fact about the menu, not a defect in the decision."""

    view = _synthetic_view()
    assert view.available_actions(), "this fixture must still have purchasable actions"

    submission = _parse_submission(
        {
            "decision": "revise_intervention",
            "evidence_ids": ["functional_target_activity"],
            "rationale": "The revealed functional result is the cited basis.",
            "limitations": ["Further evidence remains purchasable and was not acquired."],
            "decision_ready": True,
        },
        view,
    )

    assert submission.validation_errors == ()
    assert submission.decision_ready
    assert submission.additional_evidence_available


def test_a_policy_that_is_not_ready_must_name_the_missing_premise():
    view = _synthetic_view()

    unnamed = _parse_submission(
        {
            "decision": None,
            "evidence_ids": [],
            "rationale": "Not enough to conclude.",
            "limitations": [],
            "decision_ready": False,
        },
        view,
    )
    assert "deferred_without_naming_a_missing_premise" in unnamed.validation_errors

    named = _parse_submission(
        {
            "decision": None,
            "evidence_ids": [],
            "rationale": "Not enough to conclude.",
            "limitations": [],
            "decision_ready": False,
            "required_missing_premises": ["functional:target_activity"],
        },
        view,
    )
    assert named.validation_errors == ()
    assert named.required_missing_premises == ("functional:target_activity",)


def test_a_decision_cannot_be_submitted_while_declaring_it_is_not_ready():
    view = _synthetic_view()

    submission = _parse_submission(
        {
            "decision": "revise_intervention",
            "evidence_ids": ["functional_target_activity"],
            "rationale": "Contradictory submission.",
            "limitations": [],
            "decision_ready": False,
            "required_missing_premises": ["functional:target_activity"],
        },
        view,
    )
    assert "decision_submitted_while_not_ready" in submission.validation_errors


def test_terminal_submission_uses_one_format_only_retry():
    view = _synthetic_view()
    client = StubClient([
        {"decision": "invalid", "evidence_ids": [], "rationale": "", "limitations": [], "needs_more_evidence": False},
        {
            "decision": "revise_intervention", "evidence_ids": ["functional_target_activity"],
            "rationale": "The revealed functional result is the cited basis.", "limitations": [],
            "needs_more_evidence": False,
        },
    ])

    submission = LLMActionPolicy(client).decide(view)

    assert submission is not None and not submission.validation_errors
    assert submission.format_attempts == 2
    assert client.responses == []


def test_llm_repair_can_adopt_an_executable_functional_measurement_without_unlocking_mechanism(tmp_path: Path):
    task = {
        "task_type": "mechanism_diagnosis", "research_question": "Resolve discrepancy.",
        "target_or_targets": ["TARGET"], "interventions": ["compound"],
        "biological_context": "cell-a", "phenotype_endpoint": "viability",
        "supplied_evidence": [], "constraints": [], "missing_information": [], "needs_visual_review": False,
    }
    plan = {
        "identifier": "contrast", "hypotheses": [
            {"identifier": "a", "description": "A", "proposed_action": "continue"},
            {"identifier": "b", "description": "B", "proposed_action": "revise_intervention"},
        ],
        "differing_assumptions": ["functional implementation"], "action_identifier": "mode",
        "outcome_categories": ["a", "b"], "interpretation_boundaries": ["Real results remain required."],
    }
    repair = {
        "action_identifier": "functional", "modified_fields": ["plan.action_identifier"],
        "rationale": "Measure the missing functional premise first.",
        "remaining_limitations": ["A functional measurement does not establish mode equivalence."],
    }
    root = tmp_path / "log" / "20260910"
    client = StubClient([task, plan, repair])
    memory = MemoryStore(root / "memory.sqlite")
    controller = MAESTROOrchestrator(
        interpreter=TaskInterpreter(client),
        context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client),
        visual_inspector=VisualInspector(client, "vision"), memory=memory,
        logger=RunLogger(root), controller=MAESTROAgent(), enable_llm_repair=True,
    )
    functional = EvidenceAction(
        "functional", "Measure target activity.", 1.0, ("a",),
        kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT,
    )
    mode = EvidenceAction("mode", "Compare modes.", 1.0, ("a", "b"), prerequisites=("functional:target_activity:sufficient",))

    turn = controller.run(
        "Resolve discrepancy.", available_actions=(functional, mode),
        intervention_profile=FunctionalInterventionProfile(mode="drug", context_identifier="cell-a"),
    )

    assert turn.llm_repair is not None and turn.llm_repair.action_identifier == "functional"
    assert tuple(action.identifier for action in turn.selected_actions) == ("functional",)
    assert turn.check is not None and not turn.check.ready_for_mechanism_update
