"""Confirm replay evaluation never leaks private outcomes to policies.

File summary
- Path: tests/test_evaluation_isolation.py
- Purpose: Confirm replay evaluation never leaks private outcomes to policies.
- Core points:
  - Runs baseline and MAESTRO policies over frozen cases in isolated run trees.
  - Asserts scoring answers stay hidden from the policy-facing replay view.
- Interfaces: `test_*` functions
- Depends on: agent.audit, agent.cases, agent.context, agent.knowledge, agent.memory, agent.orchestrator, agent.planner, evaluation, maestro
"""
from dataclasses import replace
from pathlib import Path

import pytest

from agent.cases import CaseStore, MeasurementResult
from agent.context import ContextBuilder, ContextPacket, TaskIntent, TaskInterpreter
from agent.knowledge import EvidenceLedger, EvidenceStatus
from agent.memory import MemoryStore
from agent.audit import RunLogger
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from evaluation import CaseRepository, EvaluationRunner, ExpertWorkflowPolicy, MAESTROCorePolicy, ReplayEnvironment
from evaluation.baselines import DecisionSubmission
from maestro import DevelopmentAction, EvidenceAction, EvidenceKind, MAESTROAgent, MechanismHypothesis


ROOT = Path(__file__).resolve().parents[1]


def _cases():
    return CaseRepository(ROOT / "data/evaluation/cases/public", ROOT / "data/evaluation/cases/private").load()


def _case(identifier):
    return next(item for item in _cases() if item[0].public.identifier == identifier)


def test_fresh_runs_and_policies_have_separate_state_and_explicit_resume(tmp_path: Path):
    case, outcomes = _case("synthetic-functional-calibration-001")
    first = EvaluationRunner(run_id="run-a", state_root=tmp_path, maximum_steps=1)
    initial = first.run_case(ExpertWorkflowPolicy(), case, outcomes)
    assert initial.selected_actions == ("functional_target_activity",)
    assert initial.spent == 2.0

    resumed = EvaluationRunner(run_id="run-a", state_root=tmp_path).run_case(ExpertWorkflowPolicy(), case, outcomes)
    assert resumed.selected_actions == ("functional_target_activity", "mode_matched_comparator")
    assert resumed.spent == 5.0

    other_policy = EvaluationRunner(run_id="run-a", state_root=tmp_path, maximum_steps=1).run_case(MAESTROCorePolicy(), case, outcomes)
    assert other_policy.selected_actions == ("functional_target_activity",)
    assert (tmp_path / "run-a" / "fixed_expert" / case.public.identifier / "cases.sqlite").is_file()
    assert (tmp_path / "run-a" / "maestro_core" / case.public.identifier / "cases.sqlite").is_file()


class WrongDecisionPolicy:
    name = "wrong_decision"

    def next_action(self, view):
        return next(iter(view.available_actions())).action.identifier if view.available_actions() else None

    def decide(self, view):
        if not view.revealed:
            return None
        return DecisionSubmission(DevelopmentAction.CONTINUE, (view.revealed[0].action_identifier,), "Incorrect conclusion.", (), False, "agent")


def test_decision_mode_scores_a_wrong_policy_without_replacing_its_answer(tmp_path: Path):
    case, outcomes = _case("depmap-prism-snu761-egfr-osimertinib-001")
    result = EvaluationRunner(run_id="wrong", state_root=tmp_path, mode="decision").run_case(WrongDecisionPolicy(), case, outcomes)

    assert result.decision is DevelopmentAction.CONTINUE
    assert result.decision_origin == "agent"
    assert not result.decision_supported
    # The verdict is typed rather than prose: advancing a programme without
    # licensing evidence is a distinct failure mode from deferring or from
    # submitting an unlicensed revision, and section 9.4 counts them apart.
    assert result.verdict == "wrong_advance"
    assert "licensing evidence" in result.scoring_reason


def test_qc_failure_and_insufficient_function_do_not_unlock_mode_mechanism_support(tmp_path: Path):
    case, outcomes = _case("synthetic-functional-calibration-001")
    failed = dict(outcomes)
    failed["mode_matched_comparator"] = replace(failed["mode_matched_comparator"], biological_quality="failed")
    result = EvaluationRunner(run_id="qc", state_root=tmp_path).run_case(MAESTROCorePolicy(), case, failed)
    # The oracle is that a quality-failed comparator cannot license the mode
    # conclusion. Refusing to act is now scored as correct in its own right
    # when nothing else is licensable, so the assertion names the mechanism
    # claim rather than the decision's score.
    assert "change_intervention_mode" not in result.licensed_decisions
    assert "change_intervention_mode" not in result.reachable_decisions
    assert result.decision is DevelopmentAction.DEFER

    insufficient = dict(outcomes)
    insufficient["functional_target_activity"] = replace(
        insufficient["functional_target_activity"],
        outcome="insufficient_engagement",
        interpretation_fields=("functional:target_activity:insufficient",),
    )
    environment = ReplayEnvironment(case, insufficient)
    environment.query("functional_target_activity")
    with pytest.raises(ValueError, match="unmet prerequisites"):
        environment.query("mode_matched_comparator")


def test_case_store_validates_actual_conditions_and_conflicting_result_identifiers(tmp_path: Path):
    store = CaseStore(tmp_path / "cases.sqlite")
    action = EvidenceAction("assay", "Measure.", 1.0, ("a", "b"), time_hours=24.0, expected_conditions={"cell": "right", "drug": "x"})
    store.open_case("case", budget=2.0)
    store.record_plan("case", (action,), ready_to_measure=True, context_identifier="right-context")
    wrong = MeasurementResult("assay", "Observed.", "source", "wrong-context", 999.0, 1, True, conditions={"cell": "wrong", "drug": "x"}, result_id="same")
    with pytest.raises(ValueError, match="context"):
        store.import_measurement("case", wrong)

    valid = MeasurementResult("assay", "Observed.", "source", "right-context", 24.0, 1, True, conditions={"cell": "right", "drug": "x"}, result_id="same")
    store.import_measurement("case", valid)
    changed = MeasurementResult("assay", "Changed.", "source", "right-context", 24.0, 1, True, conditions={"cell": "right", "drug": "x"}, result_id="same")
    with pytest.raises(ValueError, match="different content"):
        store.import_measurement("case", changed)


class PlannerStub:
    def complete_json(self, messages, **kwargs):
        return {
            "identifier": "contrast",
            "hypotheses": [
                {"identifier": "fixed-a", "description": "Changed semantics.", "proposed_action": "continue"},
                {"identifier": "fixed-b", "description": "Fixed B.", "proposed_action": "defer"},
            ],
            "differing_assumptions": [], "action_identifier": "assay", "outcome_categories": [], "interpretation_boundaries": [],
        }, object()


def test_registered_hypothesis_identifier_uses_registered_semantics_not_model_rewording():
    intent = TaskIntent("evidence_review", "Question", (), (), None, None, (), (), (), False)
    packet = ContextPacket(intent, (), (), "public context")
    expected = (
        MechanismHypothesis("fixed-a", "Fixed A.", DevelopmentAction.CONTINUE),
        MechanismHypothesis("fixed-b", "Fixed B.", DevelopmentAction.DEFER),
    )
    proposal = MechanismContrastPlanner(PlannerStub()).propose(
        packet, (EvidenceAction("assay", "Assay", 1.0, ("fixed-a", "fixed-b")),),
        required_hypothesis_identifiers=("fixed-a", "fixed-b"), expected_hypotheses=expected,
    )
    assert proposal.hypotheses[0] == expected[0]
    assert proposal.hypotheses[0].description != "Changed semantics."


def test_retrieved_fitted_record_remains_derived_and_keeps_conditions_for_context(tmp_path: Path):
    memory = MemoryStore(tmp_path / "memory.sqlite")
    ledger = EvidenceLedger(tmp_path / "evidence.sqlite")
    builder = ContextBuilder(ledger, memory)
    result = MeasurementResult(
        "curve", "Fitted curve.", "prism:row", "cell", None, 1, True,
        conditions={"cell": "cell", "drug": "drug"}, metrics={"auc": "0.95"},
        biological_replicates=None, evidence_kind=EvidenceKind.DERIVED_ANALYSIS,
        limitations=("Not a biological replicate.",),
    )
    record = builder.record_result(result)
    assert record.evidence_kind is EvidenceKind.DERIVED_ANALYSIS
    assert "conditions={'cell': 'cell', 'drug': 'drug'}" in record.context
    assert "biological_replicates=None" in record.context


class CapturingReplayClient:
    def __init__(self):
        self.messages = []
        self.responses = [
            {"task_type": "evidence_review", "research_question": "Review registered source evidence.", "target_or_targets": ["EGFR"], "interventions": ["osimertinib"], "biological_context": "ACH-000537:SNU761_LIVER", "phenotype_endpoint": "viability", "supplied_evidence": [], "constraints": [], "missing_information": [], "needs_visual_review": False},
            {"identifier": "registered", "hypotheses": [{"identifier": "screen_curve_available", "description": "The registered PRISM MTS010 osimertinib curve is available for this model and condition.", "proposed_action": "defer"}, {"identifier": "screen_curve_unavailable", "description": "No eligible registered PRISM curve is available, so the retrospective cross-assay evidence cannot be reviewed.", "proposed_action": "stop"}], "differing_assumptions": ["registered record availability"], "action_identifier": "prism_mts010_osimertinib_curve", "outcome_categories": ["available", "unavailable"], "interpretation_boundaries": ["A retrieved curve does not establish target engagement."]},
        ]

    def complete_json(self, messages, **kwargs):
        self.messages.append(messages)
        return self.responses.pop(0), object()


def test_production_planner_context_cannot_read_production_or_other_run_private_evidence(tmp_path: Path):
    case, outcomes = _case("depmap-prism-snu761-egfr-osimertinib-001")
    production = EvidenceLedger(tmp_path / "production" / "evidence.sqlite")
    production.add_evidence("Private AUC 0.951159 must never enter a fresh evaluation.", source="old-run", context="poison", status=EvidenceStatus.RETRIEVED)
    client = CapturingReplayClient()

    def factory(directory: Path):
        memory = MemoryStore(directory / "memory.sqlite")
        return MAESTROOrchestrator(
            interpreter=TaskInterpreter(client),
            context_builder=ContextBuilder(EvidenceLedger(directory / "evidence.sqlite"), memory),
            planner=MechanismContrastPlanner(client),
            visual_inspector=None,
            memory=memory,
            logger=RunLogger(directory),
            controller=MAESTROAgent(),
            case_store=None,
            enable_llm_repair=False,
        )

    from evaluation.baselines import MAESTROOrchestratorPolicy
    result = EvaluationRunner(run_id="isolated", state_root=tmp_path / "runs").run_case(
        MAESTROOrchestratorPolicy(runtime_factory=factory), case, outcomes
    )

    planner_messages = "\n".join(str(messages) for messages in client.messages)
    assert result.query_coverage
    assert "0.951159" not in planner_messages
    assert "critical_actions" not in planner_messages
