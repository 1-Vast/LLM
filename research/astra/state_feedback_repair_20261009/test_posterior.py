"""Closed-form posterior checks and the paid-reveal/full-menu contract."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location("feedback_posterior", Path(__file__).with_name("posterior.py"))
posterior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(posterior)


def test_joint_second_moment_filters_complete_rows_without_centering():
    b = np.array([[1., 2.], [3., 4.], [100., 100.]])
    a = 2*b
    available = np.ones_like(b, bool); available[-1, 1] = False
    covariance, count = posterior.fit_joint(b, a, available)
    errors = np.concatenate([b[:2], a[:2]], axis=1)
    moment = errors.T @ errors / 2
    np.testing.assert_allclose(covariance, .5*moment+.5*np.diag(np.diag(moment))+np.eye(4)*1e-12)
    assert count == 2 and np.linalg.eigvalsh(covariance).min() > 0
    with pytest.raises(ValueError, match="two_complete"):
        posterior.fit_joint(b, a, np.zeros_like(available))


def test_gaussian_condition_matches_closed_form_and_does_not_mutate():
    mean = np.array([1., 2., 3., 4.]); covariance = np.eye(4)*2
    covariance[0, 2] = covariance[2, 0] = .5
    updated, reduced = posterior.condition(mean, covariance, 0, 5.)
    np.testing.assert_allclose(updated, [1.5, 2., 5., 4.])
    np.testing.assert_allclose(reduced, covariance-np.outer(covariance[:, 2], covariance[:, 2])/2)
    np.testing.assert_array_equal(mean, [1., 2., 3., 4.])
    assert covariance[2, 2] == 2


def test_independent_A_does_not_move_B_and_coupled_A_changes_ranking():
    mean = np.r_[np.arange(6.), np.zeros(6)]
    independent = np.eye(12)
    updated, _ = posterior.condition(mean, independent, 0, 100.)
    np.testing.assert_array_equal(updated[:6], mean[:6])
    coupled = posterior.common_joint(np.eye(6), np.ones(6))
    updated, _ = posterior.condition(mean, coupled, 0, 100.)
    assert posterior.top5(updated[:6])[0] == 0


def test_common_joint_matches_original_updates_for_eight_unique_A():
    rng = np.random.default_rng(7); matrix = rng.normal(size=(146, 12))
    covariance = matrix@matrix.T + np.eye(146); noise = np.linspace(.2, 2., 146)
    mean = rng.normal(size=146); offset = rng.normal(size=146); values = rng.normal(size=8)
    joint_mean = np.r_[mean, mean+offset]; joint = posterior.common_joint(covariance, noise)
    for index, value in zip([0, 4, 9, 26, 80, 103, 144, 145], values):
        column = covariance[:, index].copy(); denom = covariance[index, index]+noise[index]
        mean += column/denom*(value-offset[index]-mean[index])
        covariance -= np.outer(column, column)/denom
        joint_mean, joint = posterior.condition(joint_mean, joint, index, value)
        np.testing.assert_allclose(joint_mean[:146], mean, atol=2e-12)
        np.testing.assert_allclose(joint[:146, :146], covariance, atol=2e-12)


@pytest.mark.parametrize("policy", ["kg", "boundary"])
def test_replay_is_deterministic_paid_only_and_retains_all146(policy):
    mean = np.linspace(0., 1., 146); joint = np.eye(292)*.01; events = []
    def buy(index):
        assert 0 <= index < 146
        events.extend([("charge", index), ("release_A", index)])
        return index/146
    first = posterior.replay(mean, np.zeros(146), joint, buy, policy=policy)
    second = posterior.replay(mean, np.zeros(146), joint, lambda index: index/146, policy=policy)
    assert first["selected"] == second["selected"] and first["history"] == second["history"]
    assert len(set(first["purchased_A"])) == 8 and first["cost"] == 13
    assert first["posterior_mean_B"].shape == (146,) and first["posterior_cov_B"].shape == (146, 146)
    assert events == [event for index in first["purchased_A"] for event in [("charge", index), ("release_A", index)]]


def test_zero_covariance_is_finite_and_uses_lowest_index_ties():
    result = posterior.replay(np.zeros(146), np.zeros(146), np.zeros((292, 292)), lambda index: 10.)
    assert result["purchased_A"] == list(range(8)) and result["selected"] == list(range(5))
    assert np.isfinite(result["posterior_mean_B"]).all() and np.isfinite(result["posterior_cov_B"]).all()


def test_supplied_schedule_and_boundary_are_fixed_and_validate_before_purchase():
    mean = np.arange(146.); joint = posterior.common_joint(np.eye(146), np.ones(146))
    result = posterior.replay(mean, np.zeros(146), joint, lambda index: -100., schedule=range(138, 146))
    assert result["purchased_A"] == list(range(138, 146))
    boundary = posterior.replay(mean, np.zeros(146), joint, lambda index: -100., policy="boundary")
    expected = np.lexsort((np.arange(146), abs(mean-140.5)))[:8].tolist()
    assert boundary["purchased_A"] == expected
    with pytest.raises(ValueError, match="eight_unique"):
        posterior.replay(mean, np.zeros(146), joint, lambda index: pytest.fail("bought before validation"), schedule=[0]*8)
