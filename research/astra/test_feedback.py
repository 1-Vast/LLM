"""Meaningful research feedback regressions; fixtures are synthetic, not biology."""
from dataclasses import replace
import math
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import sys

import pytest

from maestro.case_memory import EpisodeStore, RealMeasurement, ScientificMeasurementStatus as Status
from maestro import case_update as production_update
from research.astra.feedback import FeedbackLink, FeedbackStore, categorical_score
from tests.fixtures.case_memory_integration import _episode


def link(case="case-a", attempt="attempt-1", prediction="prediction-1"):
    return FeedbackLink(case, 1, "plan-1", "a1", attempt, prediction)


def measurement(label="unresolved", status=Status.QUALIFIED):
    return RealMeasurement("a1", status, label, 3, "fixture:instrument-receipt")


def register(store, identity):
    store.register_prediction(identity, {"unresolved": 0.8, "match_h1": 0.2},
                              model_version="fixture-v1", state_id="sha256:fixture-state",
                              target_id="fixture:reading")
    store.register_attempt(identity, execution_source="fixture:execution-receipt")


def test_actual_legacy_bug_and_research_categorical_correction():
    # The original bug remains reproducible against fixed pre-promotion source.
    source = Path(__file__).parent / "results/20261002_round2/legacy_case_update.py.txt"
    loader = SourceFileLoader("maestro._astra_legacy_case_update", str(source))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    legacy = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = legacy
    loader.exec_module(legacy)
    episode = _episode()
    production = EpisodeStore()
    production.append(episode)
    bad = legacy.ingest_result(production, episode, measurement(), qc_passed=True,
                                          detected=True, contrast=("H_on", "H_off"),
                                          forecast_probability=0.8, model_version="fixture")
    assert bad.qualification.value == "reliable_but_inconclusive"
    assert bad.calibration.kind == "reading_probability"
    assert bad.calibration.realised == 0.0  # Reproduces the production semantic bug.
    research = EpisodeStore()
    research.append(episode)
    good = production_update.ingest_result(research, episode, measurement(), qc_passed=True,
                                     detected=True, contrast=("H_on", "H_off"),
                                     forecast_distribution={"unresolved": 0.8, "match_h1": 0.2},
                                     conditions_matched=True, model_version="fixture")
    assert good.qualification.value == "reliable_but_inconclusive"
    assert good.eliminated == ()
    assert good.calibration.realised == 1
    assert good.categorical_scores["brier"] == pytest.approx(0.08)
    assert good.categorical_scores["log_loss"] == pytest.approx(-math.log(0.8))
    assert len(good.episode.calibration_history) == 2
    assert research.get(episode.case_id, 1).digest == episode.digest


def test_legacy_scalar_needs_explicit_predicted_event():
    episode = _episode()
    store = EpisodeStore()
    store.append(episode)
    with pytest.raises(ValueError, match="forecast_label"):
        production_update.ingest_result(store, episode, measurement(), qc_passed=True, detected=True,
                                  contrast=("H_on", "H_off"), forecast_probability=0.8)
    assert store.versions(episode.case_id) == (1,)
    result = production_update.ingest_result(store, episode, measurement(), qc_passed=True, detected=True,
                                       contrast=("H_on", "H_off"), forecast_probability=0.8,
                                       forecast_label="match_h1", conditions_matched=True)
    assert result.calibration.realised == 0
    assert result.calibration.kind == "reading_category:match_h1"


def test_zero_probability_is_infinite_log_loss_not_silently_clipped():
    score = categorical_score({"unresolved": 0.0, "match_h1": 1.0}, "unresolved")
    assert score["brier"] == 2.0
    assert score["log_loss"] is None and score["log_loss_infinite"]


@pytest.mark.parametrize("p", [{}, {"x": 0.7}, {"x": float("nan")},
                               {"x": True}, {"x": 1.2, "y": -0.2}])
def test_invalid_distribution_is_rejected(p):
    with pytest.raises(ValueError):
        categorical_score(p, "x")


def test_restart_pairs_late_result_and_retry_does_not_duplicate_score(tmp_path):
    path = tmp_path / "feedback.sqlite"
    first = FeedbackStore(path)
    identity = link()
    register(first, identity)
    restarted = FeedbackStore(path)
    result = restarted.accept_result(identity, "result-1", measurement(), qc_passed=True, detected=True, conditions_matched=True)
    assert result["score"]["observed_probability"] == 0.8
    assert result["mechanism_discriminating"] is False
    retry = FeedbackStore(path).accept_result(identity, "result-1", measurement(), qc_passed=True, detected=True, conditions_matched=True)
    assert retry["duplicate"]
    assert len(restarted.scores("case-a")) == 1
    assert restarted.get_feedback("result-1")["link"] == result["link"]


def test_same_action_in_other_case_is_not_matched(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite")
    register(store, link())
    with pytest.raises(ValueError, match="exact executed"):
        store.accept_result(link("case-b"), "result-b", measurement(), qc_passed=True, detected=True, conditions_matched=True)
    register(store, link("case-b"))
    store.accept_result(link("case-b"), "result-b", measurement("match_h1"), qc_passed=True, detected=True, conditions_matched=True)
    assert store.scores("case-a") == ()
    assert store.scores("case-b")[0]["score"]["observed_probability"] == 0.2


@pytest.mark.parametrize("changes", [{"case_version": 2}, {"plan_id": "plan-2"},
                                    {"attempt_id": "attempt-2"}, {"prediction_id": "prediction-2"}])
def test_stale_or_different_execution_identity_cannot_score(tmp_path, changes):
    store = FeedbackStore(tmp_path / "feedback.sqlite")
    identity = link()
    register(store, identity)
    with pytest.raises(ValueError, match="exact executed"):
        store.accept_result(replace(identity, **changes), "result", measurement(), qc_passed=True, detected=True, conditions_matched=True)


def test_qc_failure_is_recorded_but_not_a_reading_error_or_mechanism_update(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite")
    register(store, link())
    result = store.accept_result(link(), "result-qc", measurement(status=Status.QC_FAILED),
                                 qc_passed=False, detected=None, conditions_matched=True, eliminated=("H_off",))
    assert result["qualification"] == "unreliable"
    assert result["score"] is None and not result["mechanism_discriminating"]
    assert result["eliminated"] == []


def test_qualified_elimination_is_distinct_from_categorical_accuracy(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite")
    register(store, link())
    result = store.accept_result(link(), "result", measurement("match_h1"),
                                 qc_passed=True, detected=True, conditions_matched=True, eliminated=("H_off",))
    assert result["mechanism_discriminating"]
    assert result["score"]["observed_probability"] == 0.2
    assert result["score"]["brier"] == pytest.approx(1.28)


@pytest.mark.parametrize("changes", [{"conditions_matched": False}, {"measurement": replace(measurement(), independent_units=None)}])
def test_unmatched_or_unverified_units_are_not_scored(tmp_path, changes):
    store = FeedbackStore(tmp_path / "feedback.sqlite")
    register(store, link())
    kwargs = dict(measurement=measurement(), qc_passed=True, detected=True, conditions_matched=True, eliminated=("H_off",))
    kwargs.update(changes)
    result = store.accept_result(link(), "result", **kwargs)
    assert result["score"] is None and not result["mechanism_discriminating"]


def test_conflicting_retries_and_replacement_result_are_rejected(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite")
    register(store, link())
    store.accept_result(link(), "result", measurement(), qc_passed=True, detected=True, conditions_matched=True)
    for result_id, value in [("result", measurement("match_h1")), ("replacement", measurement())]:
        with pytest.raises(ValueError, match="conflicting result"):
            store.accept_result(link(), result_id, value, qc_passed=True, detected=True, conditions_matched=True)
    assert len(store.scores("case-a")) == 1


def test_unexecuted_plan_and_unknown_category_do_not_enter_scores(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite")
    identity = link()
    store.register_prediction(identity, {"unresolved": 1.0}, model_version="v1", state_id="state", target_id="reading")
    with pytest.raises(ValueError, match="executed"):
        store.accept_result(identity, "result", measurement(), qc_passed=True, detected=True, conditions_matched=True)
    store.register_attempt(identity, execution_source="fixture:execution")
    with pytest.raises(ValueError, match="absent"):
        store.accept_result(identity, "result", measurement("unexpected"), qc_passed=True, detected=True, conditions_matched=True)
    assert store.get_feedback("result") is None


def test_conditional_reading_forecast_not_promoted_to_experiment_validity(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite")
    with pytest.raises(ValueError, match="conditional"):
        store.register_prediction(link(), {"unresolved": 1}, model_version="v1", state_id="state",
                                  target_id="reading", outcome_mode="attempted_experiment")


def test_one_execution_cannot_be_rebound_to_new_prediction(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite")
    identity = link()
    register(store, identity)
    replacement = replace(identity, prediction_id="other-prediction")
    store.register_prediction(replacement, {"unresolved": 1}, model_version="v2", state_id="state",
                              target_id="reading")
    with pytest.raises(ValueError, match="already bound"):
        store.register_attempt(replacement, execution_source="fixture:execution")
    store.accept_result(identity, "result", measurement(), qc_passed=True, detected=True, conditions_matched=True)
    assert len(store.scores("case-a")) == 1


def test_unasserted_conditions_are_rejected_without_feedback_side_effects(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite")
    register(store, link())
    with pytest.raises(TypeError, match="conditions_matched"):
        store.accept_result(link(), "missing", measurement(), qc_passed=True, detected=True)
    with pytest.raises(ValueError, match="explicit QC"):
        store.accept_result(link(), "unknown", measurement(), qc_passed=True, detected=True,
                            conditions_matched=None)
    assert store.scores("case-a") == ()
