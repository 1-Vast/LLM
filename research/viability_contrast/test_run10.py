"""Repair contract checks, synthetic inputs only."""
from types import SimpleNamespace

import numpy as np

from . import run9, run10
from .conditional_world import ConditionalWorld


def sample(score):
    return {"trajectory": [(score, 1)], "truth_sign": 1, "qc_prefix": [0]}


def test_fixed_sequence_stops_after_first_failure(monkeypatch):
    calls = []
    def bound(w, n, delta):
        calls.append(delta)
        return [.01, .2, .01][len(calls) - 1]
    monkeypatch.setattr(run9, "upper", bound)
    selected, table = run10.fixed_sequence([sample(100.)] * 200, [64., 4., .5], "conditional")
    assert selected == 64.
    assert len(table) == len(calls) == 2
    assert calls == [run9.DELTA / run10.SEQUENCES] * 2


def test_conditional_empty_decisions_never_certify():
    selected, table = run10.fixed_sequence([sample(.1)] * 200, [64., .5], "conditional")
    assert selected is None and len(table) == 1
    assert table[0]["ucb"] == 1.


def test_exact_sequence_capacity_improves_without_grid_penalty():
    assert run9.upper(0, 98, run9.DELTA / run10.SEQUENCES) > .05
    assert run9.upper(0, 99, run9.DELTA / run10.SEQUENCES) <= .05
    selected, _ = run10.fixed_sequence([sample(100.)] * 100, [4., .5], "conditional")
    assert selected == .5


def test_train_order_deterministic_full_family():
    training = [sample(10.)] * 80 + [sample(-1.)] * 20
    for endpoint in ("marginal", "conditional"):
        order = run10.threshold_order(training, endpoint)
        assert order == run10.threshold_order(training, endpoint)
        assert len(set(order)) == len(run9.GRID)
        assert set(order) == set(run9.GRID)


def test_residual_fitting_excludes_nontraining_outcomes():
    rng = np.random.default_rng(4)
    auc = rng.normal(size=(12, 20))
    labels = np.arange(12) % 2
    fw = SimpleNamespace(base_m=np.zeros((2, 20)))
    train = np.arange(8)
    original = run10.residual_prior(fw, auc, train, labels, np.arange(20))
    auc[8:] = 1e10
    poisoned = run10.residual_prior(fw, auc, train, labels, np.arange(20))
    for a, b in zip(original, poisoned):
        np.testing.assert_array_equal(a, b)


def test_covariance_uses_class_residuals_not_class_location():
    rng = np.random.default_rng(7)
    auc = rng.normal(size=(16, 20))
    labels = np.arange(16) % 2
    train, pool = np.arange(16), np.arange(20)
    base = np.zeros((2, 20))
    basis, noise, mean = run10.residual_prior(SimpleNamespace(base_m=base), auc, train, labels, pool)
    shifts = np.array([2., -3.])[:, None] * np.ones((2, 20))
    shifted_basis, shifted_noise, shifted_mean = run10.residual_prior(
        SimpleNamespace(base_m=shifts), auc + shifts[labels], train, labels, pool)
    np.testing.assert_allclose(basis @ basis.T, shifted_basis @ shifted_basis.T, atol=1e-12)
    np.testing.assert_allclose(noise, shifted_noise, atol=1e-12)
    np.testing.assert_allclose(mean + shifts, shifted_mean, atol=1e-12)


def test_purchase_receipt_prefix_and_no_future_reading():
    n = 24
    basis = np.column_stack((np.linspace(0., .3, n), np.linspace(.2, 0., n)))
    means = np.vstack((np.linspace(.2, .7, n), np.linspace(.8, .3, n)))
    pair = ((means[0], np.full(n, .2)), (means[1], np.full(n, .2)), (0, 1))
    response = means[0].copy()
    response[3] = np.nan
    def replay(values):
        return run10.episode(values, pair, (.01, .01), "conditional", [],
                            ConditionalWorld(basis, np.full(n, .04), means), list(range(n)))
    result = replay(response)
    assert len(set(result["purchase_positions"])) == len(result["trajectory"]) == 16
    assert result["purchase_lines"] == result["purchase_positions"]
    poisoned = response.copy()
    unbought = np.setdiff1d(np.arange(n), result["purchase_positions"])
    poisoned[unbought] = 1e6
    assert replay(poisoned) == result
    assert result["qc_prefix"] == np.cumsum([v is None for v in result["purchase_values"]]).tolist()


def test_missing_purchase_charged_exactly_once():
    n = 20
    pair = ((np.full(n, .2), np.full(n, .2)), (np.full(n, .8), np.full(n, .2)), (0, 1))
    values = np.full(n, .3)
    values[[1, 4]] = np.nan
    result = run10.episode(values, pair, (.01, .01), "fixed", list(range(n)), None, list(range(n)))
    assert result["qc_prefix"][-1] == 2
    assert len(result["purchase_positions"]) == 16
    assert result["purchase_values"][1] is None
