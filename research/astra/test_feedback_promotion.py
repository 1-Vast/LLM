"""Promotion contracts: categorical semantics and opt-in CaseStore projections."""
from dataclasses import replace
import math
import sqlite3

import pytest

from agent.memory import CaseStore, MeasurementResult
from maestro.case_memory import EpisodeStore, RealMeasurement, ScientificMeasurementStatus as Status
from maestro.case_update import ingest_result, score_reading_distribution
from maestro.models import EvidenceAction, EvidenceKind
from tests.fixtures.case_memory_integration import _episode


def episode_store():
    store = EpisodeStore()
    episode = _episode()
    store.append(episode)
    return store, episode


def ingest(store, episode, *, label="unresolved", status=Status.QUALIFIED,
           qc=True, conditions=True, eliminated=(), units=3):
    return ingest_result(store, episode, RealMeasurement("a1", status, label, units, "fixture:measurement"),
                         qc_passed=qc, detected=True, conditions_matched=conditions,
                         contrast=("H_on", "H_off"), eliminated=eliminated,
                         forecast_distribution={"unresolved": 0.8, "match_h1": 0.2}, model_version="fixture-v1")


def test_unresolved_reading_scores_correctly_without_mechanism_elimination():
    store, episode = episode_store()
    result = ingest(store, episode)
    assert result.qualification.value == "reliable_but_inconclusive"
    assert result.eliminated == ()
    assert result.calibration.kind == "reading_category:unresolved"
    assert result.calibration.realised == 1
    assert result.categorical_scores["brier"] == pytest.approx(0.08)
    assert result.categorical_scores["log_loss"] == pytest.approx(-math.log(0.8))
    assert len(result.episode.calibration_history) == 2


def test_discriminating_reading_can_still_be_poorly_predicted():
    store, episode = episode_store()
    result = ingest(store, episode, label="match_h1", eliminated=("H_off",))
    assert result.qualification.value == "qualified"
    assert result.categorical_scores["brier"] == pytest.approx(1.28)
    assert result.categorical_scores["observed_probability"] == 0.2


@pytest.mark.parametrize("changes", [{"qc": False}, {"conditions": False}, {"conditions": None},
                                    {"units": None}, {"status": Status.QC_FAILED},
                                    {"status": Status.PLANNED_MISSING}])
def test_unqualified_readout_is_not_a_categorical_prediction_error(changes):
    store, episode = episode_store()
    result = ingest(store, episode, **changes)
    assert result.calibration is None and result.categorical_scores is None
    assert result.episode.calibration_history == ()


def test_ambiguous_scalar_rejected_before_episode_update():
    store, episode = episode_store()
    with pytest.raises(ValueError, match="forecast_label"):
        ingest_result(store, episode, RealMeasurement("a1", Status.QUALIFIED, "unresolved", 3, "fixture"),
                      qc_passed=True, detected=True, contrast=("H_on", "H_off"), forecast_probability=0.8)
    assert store.versions(episode.case_id) == (1,)


def test_explicit_condition_mismatch_cannot_eliminate_mechanism():
    store, episode = episode_store()
    with pytest.raises(ValueError, match="cannot eliminate"):
        ingest(store, episode, label="match_h1", conditions=False, eliminated=("H_off",))
    assert store.versions(episode.case_id) == (1,)


@pytest.mark.parametrize("distribution", [{"x": 0.8}, {"x": float("nan")}, {"x": True},
                                         {"x": 1.1, "y": -0.1}])
def test_malformed_probabilities_are_rejected(distribution):
    with pytest.raises(ValueError):
        score_reading_distribution(distribution, "x")


def test_declared_zero_probability_retains_infinite_loss():
    scores = score_reading_distribution({"x": 0, "y": 1}, "x")
    assert scores["log_loss"] is None and scores["log_loss_infinite"]
    assert scores["brier"] == 2


def planned_store(tmp_path, case="case-a"):
    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case(case, budget=10)
    action = EvidenceAction("a1", "fixture assay", 1.0, ("H_on", "H_off"), time_hours=24)
    snapshot = store.record_plan(case, (action,), ready_to_measure=True, context_identifier="fixture-context")
    return store, snapshot.plan_version


def measured(result_id="result-1"):
    return MeasurementResult("a1", "fixture unresolved", "fixture:instrument", "fixture-context", 24, 3, True,
                             metrics={"reading": "unresolved"}, result_id=result_id)


def record_forecast(store, version, case="case-a", request="request-1"):
    return store.record_prediction(case, version, "a1", request,
                                   {"model_version": "fixture-v1", "target": "reading",
                                    "probabilities": {"unresolved": 0.8, "match_h1": 0.2}},
                                   attempt_id=None)


def test_case_store_restart_idempotence_and_budget_authority(tmp_path):
    store, version = planned_store(tmp_path)
    assert record_forecast(store, version)
    assert not record_forecast(store, version)
    imported = store.import_measurement("case-a", measured())
    restarted = CaseStore(store.path)
    prediction = restarted.prediction_for_result("case-a", imported.result_id)
    assert prediction["request_id"] == "request-1" and prediction["attempt_id"] is None
    scores = score_reading_distribution(prediction["payload"]["probabilities"], "unresolved")
    assert restarted.record_prediction_score("case-a", imported.result_id, "request-1", scores, conditions_matched=True)
    assert not restarted.record_prediction_score("case-a", imported.result_id, "request-1", scores, conditions_matched=True)
    assert not restarted.import_measurement("case-a", measured()).created
    assert restarted.snapshot("case-a").spent == 1.0
    assert len(CaseStore(store.path).prediction_scores("case-a")) == 1


def test_same_action_in_new_plan_does_not_rebind_old_result(tmp_path):
    store, version = planned_store(tmp_path)
    record_forecast(store, version)
    store.import_measurement("case-a", measured())
    action = EvidenceAction("a1", "repeat", 1.0, ("H_on", "H_off"), time_hours=24)
    second = store.record_plan("case-a", (action,), ready_to_measure=True, context_identifier="fixture-context")
    record_forecast(store, second.plan_version, request="request-2")
    assert store.prediction_for_result("case-a", "result-1")["request_id"] == "request-1"
    with pytest.raises(ValueError, match="exact accepted"):
        store.record_prediction_score("case-a", "result-1", "request-2", {"brier": 0.08}, conditions_matched=True)


def test_case_and_request_isolation(tmp_path):
    store, version = planned_store(tmp_path)
    record_forecast(store, version)
    store.import_measurement("case-a", measured())
    assert store.prediction_for_result("case-b", "result-1") is None
    with pytest.raises(ValueError, match="exact accepted"):
        store.record_prediction_score("case-b", "result-1", "request-1", {"brier": 0.08}, conditions_matched=True)
    assert store.prediction_scores("case-b") == ()


def test_forecast_immutable_and_cannot_be_added_after_observation(tmp_path):
    store, version = planned_store(tmp_path)
    record_forecast(store, version)
    with pytest.raises(ValueError, match="immutable"):
        record_forecast(store, version, request="new")
    store.import_measurement("case-a", measured())
    other, version_b = planned_store(tmp_path, "case-b")
    other.import_measurement("case-b", measured("result-b"))
    with pytest.raises(ValueError, match="before the result"):
        record_forecast(other, version_b, "case-b")


@pytest.mark.parametrize("result_changes", [{"quality_passed": False}, {"independent_units": None},
                                          {"evidence_kind": EvidenceKind.MODEL_PREDICTION}])
def test_accepted_but_unqualified_result_cannot_create_derived_score(tmp_path, result_changes):
    store, version = planned_store(tmp_path)
    record_forecast(store, version)
    store.import_measurement("case-a", replace(measured(), **result_changes))
    with pytest.raises(ValueError, match="qualified real"):
        store.record_prediction_score("case-a", "result-1", "request-1", {"brier": 0.08}, conditions_matched=True)
    assert store.prediction_scores("case-a") == ()


def test_score_conditions_must_be_explicit_and_conflicts_rejected(tmp_path):
    store, version = planned_store(tmp_path)
    record_forecast(store, version)
    store.import_measurement("case-a", measured())
    with pytest.raises(TypeError, match="conditions_matched"):
        store.record_prediction_score("case-a", "result-1", "request-1", {"brier": 0.08})
    for unknown in (None, False, 1):
        with pytest.raises(ValueError, match="Explicit matched"):
            store.record_prediction_score("case-a", "result-1", "request-1", {"brier": 0.08}, conditions_matched=unknown)
    store.record_prediction_score("case-a", "result-1", "request-1", {"brier": 0.08}, conditions_matched=True)
    with pytest.raises(ValueError, match="immutable"):
        store.record_prediction_score("case-a", "result-1", "request-1", {"brier": 1.0}, conditions_matched=True)


def test_existing_database_additive_tables_preserve_case_state(tmp_path):
    store, version = planned_store(tmp_path)
    before = store.snapshot("case-a")
    with sqlite3.connect(store.path) as db:
        db.execute("DROP TABLE prediction_scores")
        db.execute("DROP TABLE prediction_records")
    reopened = CaseStore(store.path)
    assert reopened.snapshot("case-a") == before
    assert record_forecast(reopened, version)
