"""Behavior tests for reference-only gain fitting and matched fallback."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location("state_readout_study", Path(__file__).with_name("run.py"))
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def fixture():
    rng = np.random.default_rng(7)
    state = rng.normal(size=(8, 6))
    measured = np.arange(6)[None] + .8 * state
    return dict(train_A=measured.copy(), train_B=measured,
        availability_A=np.ones((8, 6), bool), availability_B=np.ones((8, 6), bool),
        precision_B=np.ones((8, 6)), state_B=state,
        state_available_B=np.ones((8, 6), bool),
        state_B_permuted=state[:, ::-1].copy(), state_available_B_permuted=np.ones((8, 6), bool))


def test_calibration_recovers_known_response_gain():
    arrays = fixture()
    gains = study.fit(arrays, list(range(8)), np.arange(6), "global_gain", 0.)
    np.testing.assert_allclose(gains, .8, atol=1e-12)
    chosen, _ = study.choose(arrays, list(range(8)), np.arange(6), "global_gain")
    assert chosen == 0.


def test_outerheld_outcomes_cannot_change_model_or_choice():
    arrays = fixture()
    train = list(range(1, 8))
    groups = np.array([0, 0, 1, 1, 2, 2])
    original = study.choose(arrays, train, groups, "drug_gain")
    poisoned = {k: value.copy() for k, value in arrays.items()}
    for key in ("train_A", "train_B", "precision_B"):
        poisoned[key][0] = 1e6
    assert study.choose(poisoned, train, groups, "drug_gain") == original
    np.testing.assert_array_equal(study.fit(arrays, train, groups, "drug_gain", 10),
                                  study.fit(poisoned, train, groups, "drug_gain", 10))


def test_drugshared_gain_and_disabled_exact_fallback():
    arrays = fixture()
    groups = np.array([0, 0, 1, 1, 2, 2])
    gains = study.fit(arrays, list(range(8)), groups, "drug_gain", 10)
    for i in (0, 2, 4):
        assert gains[i] == gains[i + 1]
    np.testing.assert_array_equal(study.fit(arrays, list(range(8)), groups, "drug_gain", None), np.full(6, .5))


def test_reference_calculation_ignores_excluded_values_and_missing_state():
    arrays = fixture()
    arrays["train_B"][0] = np.nan
    arrays["state_B"][0] = np.nan
    mean, deviation, _, valid = study.references(arrays, list(range(1, 8)), 0)
    assert np.isfinite(mean).all()
    arrays["state_available_B"][0, 2] = False
    mean, deviation, _, valid = study.references(arrays, list(range(1, 8)), 0)
    assert deviation[2] == 0 and not valid[2]


def test_no_candidate_support_fails_explicitly():
    arrays = fixture()
    arrays["availability_B"][:, 1] = False
    with pytest.raises(ValueError, match="missing_reference_support"):
        study.references(arrays, list(range(1, 8)), 0)
