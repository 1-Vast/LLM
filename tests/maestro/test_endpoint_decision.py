"""Contracts of the endpoint-aligned follow-up decision (maestro.endpoint_decision)."""
import numpy as np
import pytest

from maestro.endpoint_decision import (ABSTENTION_THRESHOLD_REQUIRED, HIT_PROBABILITY_BELOW_THRESHOLD, SCOPE_NOT_VALIDATED,
                                       VALIDATED_SCOPE, EndpointModel, ScopeRefused, choose, choose_validated,
                                       fit_endpoint_model, pooled_replicate_sd, signed_hits)


def _model(sigma=0.1, tau=0.1, targets=2, features=3, platt=(0.0, 1.0)):
    return EndpointModel(1.0, np.full((targets, features), sigma), np.full((targets, features), tau), platt, 0.5, 2000, 7)


def test_signed_hits_need_threshold_agreement_and_two_replicates():
    reps = np.array([[0.6, 0.7, -0.6, 0.9, 0.6, 0.55],
                     [0.7, -0.1, -0.8, np.nan, 0.5, 0.45]])
    assert signed_hits(reps, 0.5).tolist() == [1, 0, -1, 0, 1, 0]
    # mean exactly at the threshold is not a hit; a single finite replicate is not a hit
    assert signed_hits(np.array([[0.5], [0.5]]), 0.5).tolist() == [0]


def test_pooled_replicate_sd_matches_the_within_cell_variance():
    cells = [np.array([[1.0], [3.0]]), np.array([[0.0], [2.0], [np.nan]])]
    assert np.allclose(pooled_replicate_sd(cells), [np.sqrt((2 + 2) / 2)])
    with pytest.raises(ValueError, match="NO_REPLICATED_CELLS"):
        pooled_replicate_sd([])


def test_a_large_standardised_but_small_raw_forecast_is_not_chosen():
    # Feature 0: raw 0.3 log2 (large in standard units if its reference spread were 0.1).
    # Feature 1: raw 0.9 log2. Only feature 1 can clear the 0.5 threshold.
    model = _model(targets=1, features=2)
    forecast = np.array([[[0.3, 0.9]]])
    P = model.hit_probability(forecast, np.array([[3]]))
    assert P[0, 0, 0] < 0.05 < 0.9 < P[0, 0, 1]
    assert choose(model, forecast, np.array([[3]]))[0].feature == 1


def test_replicate_noise_and_missing_replicates_lower_the_probability():
    forecast = np.array([[[0.8, 0.8, -0.8]]])
    noisy = EndpointModel(1.0, np.full((1, 3), 0.1), np.array([[0.05, 0.6, 0.05]]), (0.0, 1.0), 0.5, 2000, 3)
    P = noisy.hit_probability(forecast, np.array([[3]]))
    assert P[0, 0, 0] > P[0, 0, 1] + 0.3
    assert np.isclose(P[0, 0, 2], P[0, 0, 0])                 # symmetric for a negative forecast
    assert np.allclose(noisy.hit_probability(forecast, np.array([[1]])), 0.0)


def test_choose_per_line_or_per_query_and_abstains_by_name():
    model = _model()
    forecast = np.array([[[0.9, 0.1, 0.0], [0.2, 0.3, 0.6]]])
    lines = choose(model, forecast, np.array([[3, 3]]), abstain_below=0.5)
    assert [(d.target, d.feature, d.sign) for d in lines] == [(0, 0, 1), (1, 2, 1)]
    best = choose(model, forecast, np.array([[3, 3]]), per="query")
    assert len(best) == 1 and (best[0].target, best[0].feature) == (0, 0)
    weak = choose(model, np.array([[[0.45, 0.0, 0.0], [0.0, 0.0, 0.0]]]), np.array([[3, 3]]), abstain_below=0.5)
    assert all(d.refusal == HIT_PROBABILITY_BELOW_THRESHOLD for d in weak)
    with pytest.raises(ValueError, match="per must be"):
        choose(model, forecast, np.array([[3, 3]]), per="compound")


def test_probabilities_are_reproducible_and_batch_invariant_with_fixed_width():
    model = _model()
    rng = np.random.default_rng(0)
    forecast = rng.normal(0, .8, size=(4, 2, 3))
    reps = np.array([[2, 3], [3, 3], [2, 2], [3, 2]])
    a = model.hit_probability(forecast, reps, max_replicates=4)
    b = model.hit_probability(forecast[2:3], reps[2:3], max_replicates=4)
    assert np.array_equal(a, model.hit_probability(forecast, reps, max_replicates=4))
    assert np.array_equal(a[2:3], b)
    with pytest.raises(ValueError, match="AXIS_MISMATCH"):
        model.hit_probability(forecast[:, :1], reps)
    with pytest.raises(ValueError, match="max_replicates"):
        model.hit_probability(forecast, reps, max_replicates=2)


def test_fit_recovers_shrinkage_spread_and_a_finite_recalibration():
    rng = np.random.default_rng(1)
    R, T, F = 60, 2, 5
    forecast = rng.normal(0, 1.0, size=(R, T, F))
    true_mean = 0.8 * forecast + rng.normal(0, 0.3, size=(R, T, F))
    replicates = true_mean[..., None] + rng.normal(0, 0.2, size=(R, T, F, 3))
    truth = replicates.mean(-1)
    hits = np.stack([np.stack([signed_hits(replicates[r, t].T, 0.5) for t in range(T)]) for r in range(R)])
    tau = np.stack([pooled_replicate_sd([replicates[r, t].T for r in range(R)]) for t in range(T)])
    model = fit_endpoint_model(forecast, truth, hits, tau, np.full((R, T), 3), draws=1000, seed=5)
    assert 0.7 < model.shrink < 0.9
    assert np.all((model.sigma > 0.15) & (model.sigma < 0.5))
    assert np.all(np.isfinite(model.platt)) and model.platt[1] > 0
    q = model.calibrated(np.array([0.05, 0.5, 0.95]))
    assert np.all(np.diff(q) > 0) and np.all((q > 0) & (q < 1))
    with pytest.raises(ValueError, match="AXIS_MISMATCH"):
        fit_endpoint_model(forecast, truth[:, :1], hits, tau, np.full((R, T), 3))


def test_a_reported_decision_needs_the_validated_scope_and_an_abstention_rule():
    model = _model()
    forecast, replicates = np.full((1, 2, 3), 0.9), np.full((1, 2), 3)
    ok = choose_validated(model, forecast, replicates, scope=VALIDATED_SCOPE, abstain_below=0.5)
    assert [d.refusal for d in ok] == [d.refusal for d in choose(model, forecast, replicates, abstain_below=0.5)]
    for scope in ("l1000_6h_prism", "", VALIDATED_SCOPE + "_extra"):
        with pytest.raises(ScopeRefused, match=SCOPE_NOT_VALIDATED):
            choose_validated(model, forecast, replicates, scope=scope, abstain_below=0.5)
    for bad in (None, True, 0.0, 1.0, 1.5, "0.5"):
        with pytest.raises(ScopeRefused, match=ABSTENTION_THRESHOLD_REQUIRED):
            choose_validated(model, forecast, replicates, scope=VALIDATED_SCOPE, abstain_below=bad)


def test_the_guarded_entry_point_still_abstains_by_name_below_the_threshold():
    model = _model(platt=(-20.0, 1.0))
    decisions = choose_validated(model, np.full((1, 2, 3), 0.9), np.full((1, 2), 3), scope=VALIDATED_SCOPE, abstain_below=0.5)
    assert decisions and all(d.refusal == HIT_PROBABILITY_BELOW_THRESHOLD for d in decisions)
