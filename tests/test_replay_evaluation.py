"""Replay evaluation: isolation, modes, submission and scoring.

File summary
- Path: tests/test_replay_evaluation.py
- Purpose: Replay evaluation: isolation, modes, submission and scoring.
- Core points: assertions here are contract tests, not biological results; each test pins one boundary that must not silently move.
- Interfaces: `test_public_replay_view_has_no_hidden_result_before_query()`, `test_shared_replay_reports_cost_evidence_and_supported_decision()`, `test_production_orchestrator_replay_receives_results_only_after_query()`
- Depends on: agent, evaluation, maestro
"""
from pathlib import Path

from evaluation import (
    CaseRepository,
    EvaluationRunner,
    ExpertWorkflowPolicy,
    MAESTROCorePolicy,
    MAESTROOrchestratorPolicy,
    PredictionValuePolicy,
    ReplayEnvironment,
)
from maestro import DevelopmentAction
from agent.audit import RunLogger
from agent.cases import CaseStore
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.vision import VisualInspector
from maestro import MAESTROAgent

from tools.shared.stub_client import StubClient  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


def _case_data():
    return CaseRepository(
        ROOT / "data" / "evaluation" / "cases" / "public",
        ROOT / "data" / "evaluation" / "cases" / "private",
    ).load()


def _synthetic_case():
    return next(item for item in _case_data() if item[0].public.identifier == "synthetic-functional-calibration-001")


def test_public_replay_view_has_no_hidden_result_before_query():
    case, outcomes = _synthetic_case()
    environment = ReplayEnvironment(case, outcomes)
    view = environment.view()

    assert not view.revealed
    assert not hasattr(view.case, "results")
    assert not hasattr(view.case, "scoring")
    assert all("sufficient_engagement" not in item.statement for item in view.case.initial_evidence)

    revealed = environment.query("functional_target_activity")

    assert revealed.outcome == "sufficient_engagement"
    assert environment.spent == 2.0


def test_shared_replay_reports_cost_evidence_and_supported_decision():
    cases = _case_data()
    runner = EvaluationRunner()

    expert = runner.evaluate(ExpertWorkflowPolicy(), cases)
    maestro = runner.evaluate(MAESTROCorePolicy(), cases)
    prediction = runner.evaluate(PredictionValuePolicy(), cases)

    expert_result = next(item for item in expert.results if item.case_id == "synthetic-functional-calibration-001")
    maestro_result = next(item for item in maestro.results if item.case_id == "synthetic-functional-calibration-001")
    prediction_result = next(item for item in prediction.results if item.case_id == "synthetic-functional-calibration-001")
    assert expert_result.decision is DevelopmentAction.CHANGE_INTERVENTION_MODE
    assert expert_result.decision_supported
    assert not expert_result.autonomous_decision_supported
    assert maestro_result.selected_actions == (
        "functional_target_activity",
        "mode_matched_comparator",
    )
    assert maestro_result.decision_supported
    assert maestro_result.spent == 5.0
    assert not prediction_result.decision_supported
    assert prediction_result.spent == 4.0
def test_production_orchestrator_replay_receives_results_only_after_query(tmp_path: Path):
    task = {
        "task_type": "mechanism_diagnosis", "research_question": "Resolve discrepancy.",
        "target_or_targets": ["TARGET"], "interventions": ["compound"],
        "biological_context": "synthetic-cell-context", "phenotype_endpoint": "viability",
        "supplied_evidence": [], "constraints": [], "missing_information": [], "needs_visual_review": False,
    }
    plan = {
        "identifier": "contrast",
        "hypotheses": [
            {"identifier": "functional_gap", "description": "The drug condition did not sufficiently alter target function.", "proposed_action": "revise_intervention"},
            {"identifier": "mode_mismatch", "description": "The genetic and pharmacological perturbations are not functionally equivalent.", "proposed_action": "change_intervention_mode"},
        ],
        "differing_assumptions": ["functional calibration"], "action_identifier": "mode_matched_comparator",
        "outcome_categories": ["a", "b"], "interpretation_boundaries": ["Real results remain required."],
    }
    client = StubClient([task, plan, task, plan])
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

    report = EvaluationRunner().evaluate(
        MAESTROOrchestratorPolicy(controller), (_synthetic_case(),)
    )

    result = report.results[0]
    assert result.selected_actions == ("functional_target_activity", "mode_matched_comparator")
    assert result.decision is DevelopmentAction.CHANGE_INTERVENTION_MODE
    assert result.decision_supported
