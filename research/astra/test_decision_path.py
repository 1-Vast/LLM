"""Software fixtures only; no biological efficacy claims."""
from dataclasses import replace
from unittest.mock import Mock

import pytest

from agent.memory import CaseStore
from maestro.models import EvidenceAction, FunctionalInterventionProfile
from research.astra.decision_path import Candidate, DecisionPath
from research.astra.interface import ExecutionBinding, ScientificQuery, StateRef, raw_prediction_key


def candidate(name="a", cost=1, prerequisites=()):
    state = StateRef("1" * 64, "2" * 64, "transform1", "unit1", "historical")
    query = ScientificQuery(state, name, "3" * 64, "cells", "pool", "RNA", 24, "continuous")
    binding = ExecutionBinding("4" * 64, "transform1", "5" * 64, 42, "runtime1")
    return Candidate(EvidenceAction(name, "fixture", cost, (), prerequisites=prerequisites), query, binding)


def path(tmp_path, candidates, **kwargs):
    store = CaseStore(tmp_path / "cases.sqlite")
    planner = Mock(return_value=candidates)
    predictor = Mock(return_value={"value": 1})
    selector = Mock(side_effect=lambda eligible, predictions: eligible[:1])
    return DecisionPath(store, planner, selector, predictor, **kwargs)


def test_wait_survives_restart_without_any_reasoning_calls(tmp_path):
    profile = FunctionalInterventionProfile("fixture", context_identifier="cells")
    first = path(tmp_path, (candidate(),))
    assert first.run("case", profile, budget=2).status == "submitted"
    restarted = path(tmp_path, (candidate(),), reviewer=Mock())
    assert restarted.run("case", profile, budget=2).status == "awaiting_result"
    restarted.planner.assert_not_called()
    restarted.predictor.assert_not_called()
    restarted.selector.assert_not_called()
    restarted.reviewer.assert_not_called()


def test_cheap_budget_and_prerequisites_precede_prediction(tmp_path):
    core = path(tmp_path, (candidate("expensive", 4), candidate("missing", 1, ("protein",))))
    result = core.run("case", FunctionalInterventionProfile("fixture", context_identifier="cells"), budget=2)
    assert result.status == "stopped"
    assert result.rejected == {"expensive": "unaffordable", "missing": "missing_prerequisites:protein"}
    core.predictor.assert_not_called()


def test_interpretation_gate_does_not_block_execution(tmp_path):
    c = candidate()
    c = replace(c, action=replace(c.action, interpretation_gate="protein"))
    core = path(tmp_path, (c,))
    assert core.run("case", FunctionalInterventionProfile("fixture", context_identifier="cells"), budget=2).status == "submitted"


def test_single_final_review_after_repair_and_single_submission(tmp_path):
    a, b = candidate(), candidate("b")
    review = Mock()
    repaired = replace(b, binding=replace(b.binding, runtime_version="repaired-runtime"))
    core = path(tmp_path, (a, b), repair=lambda chosen, profile: (repaired,), reviewer=review)
    core.store.record_plan = Mock(wraps=core.store.record_plan)
    result = core.run("case", FunctionalInterventionProfile("fixture", context_identifier="cells"), budget=2,
                      prediction_use="selection")
    assert result.actions == (b.action,)
    assert core.predictor.call_count == 3
    review.assert_called_once_with(result.actions, result.predictions)
    core.store.record_plan.assert_called_once()


def test_raw_cache_reuse_and_content_invalidation(tmp_path):
    c = candidate()
    core = path(tmp_path, (c,))
    profile = FunctionalInterventionProfile("fixture", context_identifier="cells")
    core.run("case1", profile, budget=2)
    core.run("case2", profile, budget=2)
    assert core.predictor.call_count == 1
    changed = replace(c, query=replace(c.query, state=replace(c.query.state, content_sha256="6" * 64)))
    core.planner.return_value = (changed,)
    core.run("case3", profile, budget=2)
    assert core.predictor.call_count == 2


@pytest.mark.parametrize("field,value", [("checkpoint_sha256", "6" * 64),
                                           ("sampling_indices_sha256", "7" * 64),
                                           ("runtime_version", "runtime2")])
def test_execution_identity_changes_cache_key(field, value):
    c = candidate()
    assert raw_prediction_key(c.query, c.binding) != raw_prediction_key(c.query, replace(c.binding, **{field: value}))


def test_prediction_failure_can_leave_legal_evidence_action(tmp_path):
    core = path(tmp_path, (candidate(),))
    core.predictor.side_effect = RuntimeError("checkpoint_unavailable")
    result = core.run("case", FunctionalInterventionProfile("fixture", context_identifier="cells"), budget=2)
    assert result.status == "submitted"
    assert result.predictions["a"] == {"refusal": "checkpoint_unavailable"}
    assert not core._raw_cache
    assert core.selector.call_args.args[1] == {}  # diagnostic predictions do not drive selection


def test_unregistered_selector_and_bundle_over_budget_are_rejected(tmp_path):
    core = path(tmp_path, (candidate(), candidate("b")))
    core.selector.return_value = (candidate("invented"),)
    core.selector.side_effect = None
    with pytest.raises(ValueError, match="unregistered"):
        core.run("case", FunctionalInterventionProfile("fixture"), budget=1)
    core.selector.return_value = core.planner.return_value
    with pytest.raises(ValueError, match="bundle"):
        core.run("case", FunctionalInterventionProfile("fixture"), budget=1)


def test_research_runtime_returns_before_interpreter(tmp_path):
    from tests.fixtures.biological import orchestrator, contract
    from agent.orchestrator import MAESTROOrchestrator
    core = orchestrator(tmp_path)
    core.__class__ = MAESTROOrchestrator
    actions, _, profile = contract()
    core._case_store.open_case("case", budget=5)
    core._case_store.record_plan("case", actions[:1], ready_to_measure=True, context_identifier="fixture_cells")
    core._interpreter.interpret = Mock(side_effect=AssertionError("must not interpret while awaiting"))
    result = core.run("still waiting", available_actions=actions, intervention_profile=profile, case_id="case", budget=5)
    assert result.intent.task_type == "awaiting_result"
    assert result.case.plan_version == 1
    core._interpreter.interpret.assert_not_called()


def test_runtime_reuses_supported_adapter_and_nonwaiting_orchestration(tmp_path):
    from virtual_cell.state_adapter import StateCapabilityAdapter, StateAdapterConfig
    from agent.orchestrator import MAESTROOrchestrator
    from virtual_cell.state_adapter import StateCapabilityAdapter as ProductionAdapter
    from virtual_cell.state_adapter import StateAdapterConfig as ProductionConfig
    from tests.fixtures.biological import orchestrator, contract
    assert StateCapabilityAdapter is ProductionAdapter
    assert StateAdapterConfig is ProductionConfig
    core = orchestrator(tmp_path)
    core.__class__ = MAESTROOrchestrator
    actions, _, profile = contract()
    result = core.run("Constructed software task.", available_actions=actions,
                      intervention_profile=profile, case_id="case", budget=5)
    assert result.case.plan_version == 1


@pytest.mark.parametrize("prediction", [None, {"refusal": "unknown"}, {"valid": False}])
def test_required_model_action_is_blocked_on_refusal(tmp_path, prediction):
    c = candidate()
    c = replace(c, action=replace(c.action, requires_virtual_prediction=True))
    core = path(tmp_path, (c,))
    core.predictor.return_value = prediction
    result = core.run("case", FunctionalInterventionProfile("fixture"), budget=2)
    assert result.status == "stopped"
    assert result.rejected == {"a": "required_prediction_refused"}
    core.selector.assert_not_called()
    assert not core._raw_cache


def test_missing_required_query_and_unregistered_repair_are_rejected(tmp_path):
    c = candidate()
    c = replace(c, action=replace(c.action, requires_virtual_prediction=True), query=None, binding=None)
    core = path(tmp_path, (c,))
    assert core.run("missing", FunctionalInterventionProfile("fixture"), budget=2).rejected == {"a": "required_prediction_missing"}
    core.predictor.assert_not_called()
    core = path(tmp_path, (candidate(),), repair=lambda chosen, profile: (candidate("invented"),))
    with pytest.raises(ValueError, match="unregistered action"):
        core.run("repair", FunctionalInterventionProfile("fixture"), budget=2)
    assert core.store.snapshot("repair").plan_version == 0


@pytest.mark.parametrize("query_changes,action_changes,kind", [
    ({"context": "other"}, {}, "context"),
    ({"endpoint": "other"}, {"readout": "RNA"}, "endpoint"),
    ({"time_hours": 2}, {"time_hours": 24}, "time"),
])
def test_scientific_query_must_match_executable_action(tmp_path, query_changes, action_changes, kind):
    c = candidate()
    c = replace(c, query=replace(c.query, **query_changes), action=replace(c.action, **action_changes))
    core = path(tmp_path, (c,))
    with pytest.raises(ValueError, match=kind):
        core.run("case", FunctionalInterventionProfile("fixture", context_identifier="cells"), budget=2)
    core.predictor.assert_not_called()


def test_authoritative_result_then_restart_recovers_derived_feedback_once(tmp_path):
    """Explicit caller wiring with a constructed observation, never biology.

    A crash between fact import and derived scoring is recovered by replaying
    the same IDs. This does not claim a distributed atomic transaction.
    """
    from agent.memory import MeasurementResult
    from maestro.case_memory import RealMeasurement, ScientificMeasurementStatus
    from research.astra.feedback import FeedbackLink, FeedbackStore

    core = path(tmp_path, (candidate(),))
    profile = FunctionalInterventionProfile("fixture", context_identifier="cells")
    submitted = core.run("case", profile, budget=2)
    identity = FeedbackLink("case", submitted.plan_version, "fixture-plan-1", "a", "fixture-attempt-1", "fixture-prediction-1")
    ledger = FeedbackStore(tmp_path / "cases.sqlite")  # Separate tables, one authoritative CaseStore.
    ledger.register_prediction(identity, {"unresolved": 0.8, "match": 0.2},
                               model_version="fixture-model", state_id="fixture-state", target_id="fixture-readout")
    ledger.register_attempt(identity, execution_source="fixture:execution")
    fact = MeasurementResult("a", "Constructed software observation; no experimental biology.",
                             "fixture:instrument", "cells", None, 1, True,
                             result_id="fixture-result", limitations=("Synthetic test fixture.",))
    assert core.store.import_measurement("case", fact).created
    # Simulate process interruption after the fact transaction, before derived feedback.
    restarted = CaseStore(tmp_path / "cases.sqlite")
    assert not restarted.import_measurement("case", fact).created
    ledger = FeedbackStore(tmp_path / "cases.sqlite")
    measured = RealMeasurement("a", ScientificMeasurementStatus.QUALIFIED, "unresolved", 1, "fixture:instrument")
    scored = ledger.accept_result(identity, fact.result_id, measured, qc_passed=True, detected=True, conditions_matched=True)
    assert scored["score"]["brier"] == pytest.approx(0.08)
    assert not scored["mechanism_discriminating"]
    assert ledger.accept_result(identity, fact.result_id, measured, qc_passed=True, detected=True, conditions_matched=True)["duplicate"]
    assert restarted.snapshot("case").spent == 1
    assert len(ledger.scores("case")) == 1
    # The next choice can explicitly consult this exact case's scores, without fitting weights.
    core = path(tmp_path, (candidate("b"),))
    def next_selection(eligible, predictions):
        assert len(ledger.scores("case")) == 1
        assert not predictions  # Diagnostic mode does not silently steer actions.
        return eligible[:1]
    core.selector = next_selection
    assert core.run("case", profile, budget=2).plan_version == 2


@pytest.mark.parametrize("changes", [
    {"intervention_sha256": "9" * 64}, {"population": "other-population"},
    {"outcome_mode": "attempted_experiment"}, {"time_hours": 1}, {"endpoint": "viability"},
])
def test_repair_cannot_silently_change_registered_science(tmp_path, changes):
    c = candidate()
    changed = replace(c, query=replace(c.query, **changes))
    core = path(tmp_path, (c,), repair=lambda chosen, profile: (changed,))
    with pytest.raises(ValueError, match="scientific contract"):
        core.run("case", FunctionalInterventionProfile("fixture"), budget=2)
    assert core.store.snapshot("case").plan_version == 0
    assert core.predictor.call_count == 1


def test_repaired_state_refreshes_forecast_and_removing_query_clears_it(tmp_path):
    c = candidate()
    changed = replace(c, query=replace(c.query, state=replace(c.query.state, content_sha256="8" * 64)))
    core = path(tmp_path, (c,), repair=lambda chosen, profile: (changed,))
    assert core.run("new-state", FunctionalInterventionProfile("fixture"), budget=2).status == "submitted"
    assert core.predictor.call_count == 2
    core.repair = lambda chosen, profile: (replace(c, query=None, binding=None),)
    assert core.run("no-query", FunctionalInterventionProfile("fixture"), budget=2).predictions == {}


@pytest.mark.parametrize("research_type", [False, True])
def test_typed_prediction_refusal_and_invalid_contract_cannot_enable_action(tmp_path, research_type):
    if research_type:
        from research.astra.interface import StatePrediction
    else:
        from virtual_cell.interface import StatePrediction
    c = candidate()
    c = replace(c, action=replace(c.action, requires_virtual_prediction=True))
    core = path(tmp_path, (c,))
    core.predictor.return_value = StatePrediction(False, None, None, (), abstain_reason="unsupported-context")
    result = core.run("refusal", FunctionalInterventionProfile("fixture"), budget=2)
    assert result.status == "stopped"
    assert result.predictions["a"]["refusal"] == "unsupported-context"
    core.predictor.return_value = StatePrediction(True, {"RNA": 1}, 0.1, ())  # Missing applicability metadata.
    result = core.run("invalid", FunctionalInterventionProfile("fixture"), budget=2)
    assert result.status == "stopped"
    assert result.predictions["a"]["refusal"] == "invalid_prediction_contract"
    assert not core._raw_cache


def test_missing_model_asset_is_explicit_refusal(tmp_path):
    c = candidate()
    c = replace(c, action=replace(c.action, requires_virtual_prediction=True))
    core = path(tmp_path, (c,))
    core.predictor.side_effect = FileNotFoundError("fixture-missing-checkpoint")
    result = core.run("case", FunctionalInterventionProfile("fixture"), budget=2)
    assert result.status == "stopped"
    assert "missing-checkpoint" in result.predictions["a"]["refusal"]
