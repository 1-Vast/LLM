"""Synthetic training contracts, not measured biological validation."""
import numpy as np
import pytest
from research.scientific_optimization.response_training import fit_response


def test_small_response_fit_learns_and_restores_selected_epoch():
    rng = np.random.default_rng(11)
    x = rng.normal(size=(80, 3)).astype("float32")
    gate = np.ones(80, dtype="float32")
    y = x[:, :1] * .2
    fit = fit_response(x[:60], gate[:60], y[:60], x[60:], gate[60:], y[60:], seed=11, epochs=45)
    assert np.square(fit.predict(x[60:], gate[60:]) - y[60:]).mean() < np.square(y[60:]).mean()
    assert fit.selected_epoch == min(fit.history, key=lambda h: h["validation_mse"])["epoch"]
    with pytest.raises(ValueError, match="invalid_response_input"):
        fit.predict(np.full((1, 3), np.nan), np.ones(1))


def test_training_refuses_nonfinite_values():
    x = np.ones((5, 3))
    y = np.ones((5, 1))
    with pytest.raises(ValueError, match="invalid_training_data"):
        fit_response(x * np.nan, np.ones(5), y, x, np.ones(5), y, seed=11)
