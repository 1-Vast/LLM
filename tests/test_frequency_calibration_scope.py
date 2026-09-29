"""Scientific invariants for the single-step, development-scoped frequency estimator."""
from dataclasses import replace

import pytest

from maestro.adaptive_retrieval import FeatureArm
from maestro.hypothesis_forecast import dirichlet_forecast, fit_frequency_calibration
from maestro.hypothesis_forecast import CaseMemoryOutcomeForecaster
from tests.fixtures.case_memory_forecasting import _actions, _contrast, _episode, _state, _store


CONTEXT = ("l1000", "signature", "A549", "lab-a", "24", "10000")


def _rows(context=CONTEXT):
    return [
        {"unit": "cal-a", "counts": {"yes": 8., "no": 2.}, "effective_support": 10.,
         "outcome": "yes", "context": context},
        {"unit": "cal-a", "counts": {"yes": 8., "no": 2.}, "effective_support": 10.,
         "outcome": "no", "context": context},
        {"unit": "cal-b", "counts": {"yes": 8., "no": 2.}, "effective_support": 10.,
         "outcome": "yes", "context": context},
    ]


def _fit(rows=None, **kwargs):
    args = dict(training_units=("train-a", "train-b"), source_snapshot="training-snapshot",
                outcome_mode="valid_readout", feature_arm="scalar")
    args.update(kwargs)
    return fit_frequency_calibration(_rows() if rows is None else rows, **args)


def test_weight_rescaling_cannot_change_forecast_or_posterior_concentration():
    counts = {"yes": 1.2, "no": .3, "unresolved": 0., "absent": .1}
    original = dirichlet_forecast(counts, effective_support=7.4)
    scaled = dirichlet_forecast({k: v * 100 for k, v in counts.items()}, effective_support=7.4)
    assert original[0] == pytest.approx(scaled[0])
    assert original[1] == scaled[1]


def test_increasing_support_recovers_empirical_frequencies_without_fixed_temperature():
    frequencies = {"yes": .9, "no": .1, "unresolved": 0., "absent": 0.}
    small, _ = dirichlet_forecast(frequencies, effective_support=10)
    large, _ = dirichlet_forecast(frequencies, effective_support=1e12)
    assert large == pytest.approx(frequencies, abs=1e-11)
    assert abs(large["yes"] - .9) < abs(small["yes"] - .9)


def test_equal_weights_exactly_reproduce_jeffreys_frequency_baseline():
    counts = {"yes": 7, "no": 2, "unresolved": 1, "absent": 0}
    probabilities, concentration = dirichlet_forecast(counts, effective_support=10)
    assert concentration == 12
    assert probabilities == pytest.approx({k: (v + .5) / 12 for k, v in counts.items()})


def test_calibration_refuses_training_unit_overlap():
    with pytest.raises(ValueError, match="calibration_training_overlap"):
        _fit(training_units=("train-a", "cal-a"))


def test_equal_unit_fit_is_invariant_to_repeating_all_rows_of_one_unit():
    rows = _rows()
    repeated = rows + [dict(r) for r in rows if r["unit"] == "cal-a"] * 8
    fit, duplicate_fit = _fit(rows), _fit(repeated)
    assert fit.pseudocount == pytest.approx(duplicate_fit.pseudocount, rel=1e-6)
    assert fit.calibration_units == duplicate_fit.calibration_units == ("cal-a", "cal-b")


@pytest.mark.parametrize("index,value", [
    (0, "scRNA"), (1, "viability"), (2, "MCF7"), (3, "lab-b"), (4, "48"), (5, "5000"),
])
def test_fitted_profile_refuses_every_changed_context_dimension(index, value):
    fit = _fit()
    changed = list(CONTEXT)
    changed[index] = value
    assert fit.refusal(CONTEXT, "valid_readout", "scalar", 2, "training-snapshot") is None
    assert fit.refusal(tuple(changed), "valid_readout", "scalar", 2,
                       "training-snapshot") == "outside_calibration_context"


@pytest.mark.parametrize("mode,arm,count", [
    ("attempted_experiment", "scalar", 2),
    ("valid_readout", "combined", 2),
    ("valid_readout", "scalar", 4),
])
def test_profile_refuses_changed_estimand(mode, arm, count):
    assert _fit().refusal(CONTEXT, mode, arm, count,
                          "training-snapshot") == "calibration_estimand_mismatch"


def test_profile_refuses_changed_source_snapshot_or_estimator_version():
    fit = _fit()
    assert fit.refusal(CONTEXT, "valid_readout", "scalar", 2,
                       "new-snapshot") == "calibration_source_mismatch"
    assert replace(fit, model_version="other-estimator").refusal(
        CONTEXT, "valid_readout", "scalar", 2, "training-snapshot") == "calibration_source_mismatch"


def _production_fit():
    store = _store([_episode(f"source-{i}", +1) for i in range(6)])
    action, state = _actions()[0], _state(+1)
    context = CaseMemoryOutcomeForecaster.calibration_context(action, state)
    rows = [{**row, "counts": {**row["counts"], "unresolved": 0., "absent": 0.}}
            for row in _rows(context)]
    fit = _fit(rows, training_units=tuple(ep.case_id for ep in store.latest()),
               source_snapshot=store.snapshot_digest())
    return store, action, state, fit


def test_development_fit_does_not_claim_external_calibration(monkeypatch):
    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "1")
    store, action, state, fit = _production_fit()
    forecaster = CaseMemoryOutcomeForecaster(store, feature_arm=FeatureArm.SCALAR, calibration=fit)
    receipt = forecaster.forecast_detailed(_contrast(), action, None, state)
    assert receipt["applicable"]
    assert receipt["calibration_status"] == "uncalibrated"
    assert receipt["calibration_fit"] == "development_only"
    assert receipt["regularisation"]["fitted"]
    assert all("qc_failed" not in branch["probabilities"] for branch in receipt["branches"])


@pytest.mark.parametrize("change,reason", [
    ("context", "outside_calibration_context"),
    ("estimand", "calibration_estimand_mismatch"),
    ("snapshot", "calibration_source_mismatch"),
])
def test_forecaster_enforces_profile_scope_before_emitting_probabilities(monkeypatch, change, reason):
    monkeypatch.setenv("MAESTRO_CASE_MEMORY_ENABLED", "1")
    store, action, state, fit = _production_fit()
    if change == "context":
        state = replace(state, laboratory="unseen-lab")
    elif change == "estimand":
        state = replace(state, outcome_mode="attempted_experiment")
    else:
        fit = replace(fit, source_snapshot="stale-snapshot")
    forecaster = CaseMemoryOutcomeForecaster(store, feature_arm=FeatureArm.SCALAR, calibration=fit)
    forecast = forecaster.forecast(_contrast(), (action,), None, state)[action.identifier]
    assert forecast.refusal == reason
    assert not forecast.branches
