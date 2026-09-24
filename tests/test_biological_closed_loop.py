"""Adversarial and positive production-path checks for biological evidence closure.

File summary
- Path: tests/test_biological_closed_loop.py
- Purpose: Verify that each biological link has its own assay, conditions and measured lineage.
- Core points: all values below are constructed fixtures; passing them is not biological validation.
- Interfaces: test_* functions
- Depends on: maestro.outcome, agent.orchestrator, tools.shared.biological_fixture
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from agent.orchestrator import MAESTROOrchestrator
from maestro import (
    DecisionStatus, DevelopmentAction, EvidenceKind, EvidenceScope, EvidenceState,
    FunctionalInterventionProfile, InterpretationTable, MeasurementStatus, MechanismContrast,
    MechanismHypothesis, MODE_COMPARATOR_FIELD, MODE_DIFFERENCE_FIELD, OutcomeClass, OutcomeRule,
    SUFFICIENT_FUNCTION_FIELD, admit_evidence,
)
from maestro.models import BiologicalQuantity, PremiseRequirement
from maestro.reliability import PredictionReliabilityLedger
from maestro.repair import RepairLedger, RepairRecord
from maestro.models import RepairKind
from virtual_cell import Interval, IntervalKind, StatePrediction
from tools.shared.biological_fixture import contract, results, run_chain, ENGAGEMENT, CONDITIONS


def _contrast(actions):
    return MechanismContrast(
        "typed-chain", (MechanismHypothesis("incomplete", "Incomplete", DevelopmentAction.REVISE_INTERVENTION),
                        MechanismHypothesis("mode", "Mode", DevelopmentAction.CHANGE_INTERVENTION_MODE)),
        ("realization",), actions[-1],
    )


def _admit_sequence(actions=None, supplied=None):
    original, table, profile = contract()
    actions = actions or original
    supplied = supplied or results()
    contrast = _contrast(actions)
    history, admissions = [], []
    for action in actions:
        observation = supplied[action.identifier]
        interpretation = table.interpret(observation, contrast, profile, action, prior_evidence=history)
        admission = admit_evidence(interpretation, observation, action=action)
        history.extend(admission.measured_premises)
        admissions.append(admission)
    return admissions


def test_three_real_assay_records_close_only_at_the_final_link(tmp_path):
    agent, loop = run_chain(tmp_path)
    assert [a.identifier for turn in loop.turns for a in turn.selected_actions] == ["engagement", "function", "comparator"]
    assert loop.decision.status is DecisionStatus.DECIDED
    assert loop.decision.action is DevelopmentAction.CHANGE_INTERVENTION_MODE
    assert loop.evidence_state.candidates == frozenset({"mode"})
    assert {p.grant.quantity for p in loop.measured_premises} == {
        BiologicalQuantity.TARGET_OCCUPANCY, BiologicalQuantity.PROXIMAL_ACTIVITY, BiologicalQuantity.VIABILITY,
    }
    assert len({p.result_id for p in loop.measured_premises}) == 3
    assert len(loop.evidence_state.mechanism_updates()) == 1
    assert agent._case_store.snapshot("constructed_chain").spent == 3.0


def test_separate_links_retain_their_quantity_scope_and_parent_result_ids():
    engagement, function, comparator = _admit_sequence()
    assert engagement.scope is EvidenceScope.INTERVENTION_IMPLEMENTATION
    assert function.scope is EvidenceScope.INTERVENTION_IMPLEMENTATION
    assert comparator.scope is EvidenceScope.MECHANISM_CONTRAST
    assert set(comparator.interpretation.supporting_result_ids) == {
        "fixture_result_engagement", "fixture_result_function",
    }
    assert SUFFICIENT_FUNCTION_FIELD not in comparator.admitted_fields
    assert function.measured_premises[0].grant.quantity is BiologicalQuantity.PROXIMAL_ACTIVITY


@pytest.mark.parametrize("missing", ["engagement", "function", "comparator"])
def test_missing_link_stops_without_fabricating_a_measurement(tmp_path, missing):
    _, loop = run_chain(tmp_path, transform=lambda supplied: {key: value for key, value in supplied.items() if key != missing})
    assert loop.stop_reason == "awaiting_result"
    assert loop.decision is None or loop.decision.status is not DecisionStatus.DECIDED
    assert not loop.evidence_state.mechanism_updates()


@pytest.mark.parametrize("changes,reason", [
    ({"quantity": BiologicalQuantity.RNA_ABUNDANCE}, "quantity_mismatch"),
    ({"quantity": BiologicalQuantity.PROTEIN_ABUNDANCE}, "quantity_mismatch"),
    ({"quantity": BiologicalQuantity.ENGAGEMENT_SHIFT}, "quantity_mismatch"),
    ({"quantity_is_estimated": True}, "estimate_offered"),
    ({"entity": "OTHER_TARGET"}, "entity_mismatch"),
    ({"units": "unregistered_units"}, "units_mismatch"),
])
def test_wrong_biological_quantity_or_identity_cannot_unlock_the_chain(changes, reason):
    actions, _, _ = contract()
    changed = (replace(actions[0], **changes),) + actions[1:]
    first, middle, last = _admit_sequence(actions=changed)
    assert not first.admissible
    assert any(reason in issue for issue in first.interpretation.unmatched_conditions)
    assert not middle.admissible and not last.admissible


@pytest.mark.parametrize("changes,reason", [
    ({"context_identifier": "other_cells"}, "context"),
    ({"time_hours": 2.5}, "time"),
    ({"time_hours": float("nan")}, "time"),
    ({"independent_units": None}, "independent_units"),
    ({"independent_units": True}, "independent_units"),
    ({"quality_passed": False}, "quality"),
    ({"evidence_kind": EvidenceKind.MODEL_PREDICTION}, "non_measurement"),
])
def test_invalid_parent_record_never_supports_a_mechanism(changes, reason):
    supplied = results()
    supplied["engagement"] = replace(supplied["engagement"], **changes)
    _, middle, last = _admit_sequence(supplied=supplied)
    assert not middle.admissible and not last.admissible


@pytest.mark.parametrize("metric", ["0.1", "nan", "inf", "not_numeric", True, None])
def test_declared_engagement_is_rejected_when_its_numbers_do_not_support_it(metric):
    supplied = results()
    supplied["engagement"] = replace(supplied["engagement"], metrics={"occupancy": metric})
    first, _, last = _admit_sequence(supplied=supplied)
    assert not first.admissible and not last.admissible
    assert any("metric:occupancy" in issue for issue in first.interpretation.unmatched_conditions)


def test_correctly_typed_links_from_different_exposure_do_not_form_a_chain():
    actions, table, profile = contract()
    supplied = results()
    first = table.interpret(supplied["engagement"], _contrast(actions), profile, actions[0])
    history = admit_evidence(first, supplied["engagement"], action=actions[0]).measured_premises
    altered = replace(history[0], conditions={**CONDITIONS, "exposure": "different"})
    result = table.interpret(supplied["function"], _contrast(actions), profile, actions[1], prior_evidence=(altered,))
    assert not result.can_update_mechanism
    assert result.outcome_class is OutcomeClass.CONDITION_UNMATCHED
    assert any("exposure:unmatched" in issue for issue in result.unmatched_conditions)


def test_fields_outside_the_registered_rule_are_not_admitted_or_promoted():
    actions, table, profile = contract()
    supplied = results()["engagement"]
    spoofed = replace(supplied, interpretation_fields=supplied.interpretation_fields + (MODE_COMPARATOR_FIELD, "protein_abundance"))
    interpretation = table.interpret(spoofed, _contrast(actions), profile, actions[0])
    admission = admit_evidence(interpretation, spoofed, action=actions[0])
    assert admission.admitted_fields == (ENGAGEMENT,)
    assert set(interpretation.refused_fields) == {MODE_COMPARATOR_FIELD, "protein_abundance"}
    updated = MAESTROOrchestrator._profile_after_result(profile, spoofed, admission)
    assert updated.measurement_status(ENGAGEMENT) is MeasurementStatus.MEASURED
    assert updated.protein_abundance is MeasurementStatus.UNKNOWN
    assert updated.measurement_status(MODE_COMPARATOR_FIELD) is MeasurementStatus.UNKNOWN
    assert supplied.source_id in updated.source_ids


def test_protein_assay_updates_the_protein_slot_not_a_functional_alias():
    actions, _, profile = contract()
    action = replace(actions[0], supplies=("protein_abundance",), quantity=BiologicalQuantity.PROTEIN_ABUNDANCE)
    observed = replace(results()["engagement"], interpretation_fields=("protein_abundance",))
    table = InterpretationTable((OutcomeRule(
        "protein", "present", frozenset({"protein_abundance"}),
        scope=EvidenceScope.INTERVENTION_IMPLEMENTATION,
        field_requirements=(PremiseRequirement("protein_abundance", BiologicalQuantity.PROTEIN_ABUNDANCE),),
    ),))
    admission = admit_evidence(table.interpret(observed, _contrast(actions), profile, action), observed, action=action)
    updated = MAESTROOrchestrator._profile_after_result(profile, observed, admission)
    assert updated.protein_abundance is MeasurementStatus.MEASURED
    assert not updated.has_measured_function()


def test_surviving_hypotheses_are_not_reset_on_an_unchanged_next_round():
    actions, _, _ = contract()
    state = EvidenceState(frozenset({"mode"}), eliminated=frozenset({"incomplete"}))
    controller = object.__new__(MAESTROOrchestrator)
    assert controller._state_for_round("case", state, _contrast(actions)) is state


class Logger:
    def event(self, *args, **kwargs):
        pass


def _scoring_fixture():
    action = replace(contract()[0][0], prediction_readout="response")
    prediction = StatePrediction(
        True, {"response": 0.0}, None, (), request_id="q", model_version="fixture_model",
        intervals={"response": Interval(-0.1, 0.1, kind=IntervalKind.CALIBRATED,
                                        level=0.9, basis="synthetic test declaration")},
    )
    turn = SimpleNamespace(action_predictions={action.identifier: prediction}, prediction=prediction,
                           session_id="test", intent=SimpleNamespace(biological_context="fixture_cells"))
    observed = replace(results()[action.identifier], metrics={"response": "1.0"})
    controller = object.__new__(MAESTROOrchestrator)
    controller._logger = Logger()
    controller._reliability = PredictionReliabilityLedger()
    return controller, turn, action, observed


@pytest.mark.parametrize("change", [
    {"evidence_kind": EvidenceKind.MODEL_PREDICTION}, {"quality_passed": False},
    {"action_identifier": "other_action"}, {"context_identifier": "other_cells"},
    {"time_hours": 9.0}, {"independent_units": None}, {"metrics": {"response": "nan"}},
    {"conditions": {}}, {"metrics": {"response": True}},
])
def test_invalid_prediction_pairs_do_not_enter_calibration(change):
    controller, turn, action, observed = _scoring_fixture()
    controller._score_prediction(turn, action, replace(observed, **change))
    assert not controller._reliability.records


def test_missing_action_prediction_does_not_borrow_the_primary_prediction():
    controller, turn, action, observed = _scoring_fixture()
    turn.action_predictions = {"different_action": turn.prediction}
    controller._score_prediction(turn, action, observed)
    assert not controller._reliability.records


def test_duplicate_real_experiment_cannot_create_three_calibration_misses():
    controller, turn, action, observed = _scoring_fixture()
    for index in range(3):
        turn.action_predictions[action.identifier] = replace(turn.prediction, request_id=f"request_{index}")
        controller._score_prediction(turn, action, replace(observed, result_id=f"result_{index}"))
    assert len(controller._reliability.records) == 1
    assert not controller._reliability.is_revoked("fixture_model", "response", "fixture_cells")


def test_real_unexpected_result_still_scores_a_prediction_without_a_mechanism_rule():
    controller, turn, action, observed = _scoring_fixture()
    controller._score_prediction(turn, action, replace(observed, interpretation_fields=("unexpected",)))
    assert len(controller._reliability.records) == 1
    assert controller._reliability.records[0].interval_hit is False


@pytest.mark.parametrize("minimum", [1, 2, 4])
def test_declared_minimum_replication_is_required_on_all_chain_links(minimum):
    actions, table, profile = contract()
    supplied = results()
    history = []
    contrast = _contrast(actions)
    for action in actions[:2]:
        observation = replace(supplied[action.identifier], independent_units=minimum)
        interpreted = table.interpret(observation, contrast, profile, action, prior_evidence=history)
        history.extend(admit_evidence(interpreted, observation, action=action).measured_premises)
    final = table.interpret(supplied["comparator"], contrast, profile, actions[-1], prior_evidence=history)
    assert final.can_update_mechanism is (minimum >= 3)


def test_a_repair_is_verified_from_its_own_result_not_next_round_plan(tmp_path):
    agent, loop = run_chain(tmp_path)
    rows = [row for row in loop.repair_trajectory if row["gap_resolved"] is True]
    assert rows and all(row["result_id"] and row["adopted"] for row in rows)
    for row in rows:
        assert row["result_id"] == "fixture_result_" + row["action_identifier"]


def test_unobserved_repair_remains_unscored(tmp_path):
    _, loop = run_chain(tmp_path, transform=lambda supplied: {})
    assert loop.stop_reason == "awaiting_result"
    assert all(row["gap_resolved"] is None for row in loop.repair_trajectory)


def test_changed_hypothesis_description_cannot_resurrect_a_refuted_candidate(tmp_path):
    from tools.shared.biological_fixture import PLAN, orchestrator
    actions, table, profile = contract()
    first_rule = replace(table.rules[0], scope=EvidenceScope.MECHANISM_CONTRAST,
                         eliminates=frozenset({"incomplete"}))
    table = InterpretationTable((first_rule,) + table.rules[1:])
    changed = {**PLAN, "hypotheses": [{**item, "description": item["description"] + " Updated."} for item in PLAN["hypotheses"]]}
    agent = orchestrator(tmp_path, table=table, plans=[PLAN, changed])
    supplied = results()
    calls = []
    def provider(action, turn):
        calls.append(action.identifier)
        return supplied[action.identifier]
    loop = agent.run_case_loop("Check definitions", available_actions=actions, intervention_profile=profile,
        result_provider=provider, case_id="definitions", budget=5.0, max_rounds=2)
    assert loop.stop_reason == "hypothesis_definition_changed"
    assert loop.evidence_state.candidates == frozenset({"mode"})
    assert loop.evidence_state.eliminated == frozenset({"incomplete"})
    assert len(loop.evidence_state.updates) == 1
    assert calls == ["engagement"]
    assert loop.decision.status is DecisionStatus.DEFERRED


def test_a_repair_cannot_borrow_the_old_actions_calibrated_prediction():
    from maestro import MAESTROAgent, EvidenceAction
    from maestro.models import NonDiscriminabilityReason
    from maestro.repair import RepairController
    _, turn, _, _ = _scoring_fixture()
    old = EvidenceAction("old", "Old readout", 2.0, ("incomplete", "mode"),
        prediction_readout="response", expected_outcomes={"incomplete": "same", "mode": "same"})
    new = replace(old, identifier="new", requires_virtual_prediction=True,
        expected_outcomes={"incomplete": "one", "mode": "two"})
    contrast = replace(_contrast((old,)), plan=old)
    profile = FunctionalInterventionProfile(mode="drug")
    agent = MAESTROAgent()
    check = agent.check_contrast(contrast, profile, turn.prediction)
    outcome = RepairController(agent, max_attempts=1).run(
        contrast, check, (old, new), profile, turn.prediction,
        action_predictions={"old": turn.prediction},
    )
    assert not outcome.check.ready_for_mechanism_update
    assert NonDiscriminabilityReason.MODEL_UNSUPPORTED in outcome.check.reasons


@pytest.mark.parametrize("change", ["context", "time", "request_id", "model_version"])
def test_prediction_request_coordinates_must_match_the_calibration_pair(change):
    from virtual_cell import PredictionRequest, Intervention, SystemContext
    controller, turn, action, observed = _scoring_fixture()
    request = PredictionRequest(
        request_id="q", case_id="case", contrast_id="contrast", plan_version=1,
        intervention=Intervention("fixture_compound", "drug", ("TARGET",), time_hours=1.0),
        context=SystemContext("fixture_cells", "test cells"), readouts=("response",), model_version="fixture_model",
    )
    if change == "context":
        request = replace(request, context=SystemContext("different_cells", "foreign"))
    elif change == "time":
        request = replace(request, intervention=replace(request.intervention, time_hours=48.0))
    else:
        request = replace(request, **{change: "different"})
    turn.action_prediction_requests = {action.identifier: request}
    controller._score_prediction(turn, action, observed)
    assert not controller._reliability.records


def test_repair_resolution_targets_the_adopted_record_not_a_later_cycle_record():
    ledger = RepairLedger()
    adopted = ledger.register(RepairRecord(
        attempt=1, fingerprint="same", kind=RepairKind.ADD_PREREQUISITE_MEASUREMENT,
        action_identifier="gate", triggered_by=(), modified_fields=(), expected_gain="test",
        adopted=True, resolved_reasons=(), remaining_reasons=(), promised_fields=("gate",),
    ))
    later = ledger.register(replace(adopted, attempt=3, adopted=False, stop_reason="repair_cycle_detected"))
    ledger.resolve_fingerprint("same", True, result_id="real_result", target=adopted)
    assert ledger.records[0].gap_resolved is True and ledger.records[0].result_id == "real_result"
    assert ledger.records[1] is later and later.gap_resolved is None
