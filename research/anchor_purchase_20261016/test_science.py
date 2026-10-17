"""Focused scientific contracts, including adversarial unknown/held-out inputs."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location("anchor_diagnostic", Path(__file__).with_name("evaluate.py"))
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_heldout_outcomes_do_not_change_fitted_scores():
    y = np.array([[-2., 1.], [-1., 0.], [99., -99.]])
    similarity = [np.array([[1., .8, .7], [.8, 1., .4], [.7, .4, 1.]])] * 2
    first = study.predict(y, similarity, np.array([0, 1]), np.array([2]))
    y[2] = [-100000, 100000]
    second = study.predict(y, similarity, np.array([0, 1]), np.array([2]))
    for name in study.CANDIDATES:
        np.testing.assert_array_equal(first[name], second[name])


def test_whole_pool_including_control_is_revealed():
    pools = pd.DataFrame({"screen_id": ["S", "S", "S", "T"], "row_name": ["A", "B", "CONTROL", "C"], "pool_id": ["P", "P", "P", "P"]})
    assert study.bundle_members(pools, "S", "A") == ["A", "B", "CONTROL"]
    assert study.bundle_members(pools, "T", "C") == ["C"]


def test_unknown_is_not_inactive_and_cost_is_consumed():
    known, hit = study.terminal(np.array([[-2., np.nan, .2]]), np.array([[-1., -2., -.2]]))
    np.testing.assert_array_equal(known, [[True, False, True]])
    np.testing.assert_array_equal(hit, [[True, False, False]])
    h, u = study.utility(np.array([[0., -3., 1.]]), known, hit, 1)
    assert h[0] == 0 and u[0] == 1
    assert study.BUDGET.require_feasible(3, 0, other_cost=.25) == 3.25
    with pytest.raises(ValueError):
        study.BUDGET.require_feasible(4, 0, other_cost=.25)


def test_offset_cannot_change_rank_and_missing_reference_not_dropped():
    score = np.array([[1., -3., 2.], [0., -2., 1.]])
    np.testing.assert_array_equal(study.ranks(score, 2), study.ranks(score + np.array([[50.], [-99.]]), 2))
    assert study.ranks(np.array([[np.nan, -1., np.nan]]), 3).tolist() == [[1, 0, 2]]


def test_training_prior_never_uses_hidden_query_mean():
    y = np.array([[np.nan, -2.], [np.nan, 0.], [-100., -100.]])
    sim = [np.eye(3), np.eye(3)]
    output = study.predict(y, sim, np.array([0, 1]), np.array([2]))
    np.testing.assert_array_equal(output["line_mean"], [[0., -1.]])


def test_seal_requires_locked_choices_and_protocol():
    import hashlib
    protocol = b"frozen\n"
    choices = b"choices\n"
    seal = study.OutcomeSeal({"protocol": hashlib.sha256(protocol).hexdigest()}, None)
    with pytest.raises(PermissionError):
        seal.release({"protocol": protocol}, choices)
    seal = study.OutcomeSeal({"protocol": hashlib.sha256(protocol).hexdigest()}, hashlib.sha256(choices).hexdigest())
    assert seal.release({"protocol": protocol}, choices)
    with pytest.raises(PermissionError):
        seal.release({"protocol": protocol}, b"altered")
