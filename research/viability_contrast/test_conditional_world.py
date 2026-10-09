"""Synthetic behavioral verification; no pack, held-out data, API or model assets."""
import numpy as np
import pytest

from .conditional_world import ConditionalWorld


def prior():
    basis = np.array([[.7, .1], [.4, -.5], [.8, .6], [-.3, .7], [.2, .4]])
    variance = np.array([.09, .16, .25, .12, .04])
    means = np.array([[.2, .8, .1, .5, .9], [.9, .2, .7, .4, .1],
                      [.5, .4, .3, .2, .6]])
    return basis, variance, means


def joint_condition(basis, variance, means, pos, values):
    """Independent direct conditioning of the full joint Gaussian."""
    cov = basis @ basis.T + np.diag(variance)
    gain = np.linalg.solve(cov[np.ix_(pos, pos)], cov[pos]).T
    posterior_mean = means + (values - means[:, pos]) @ gain.T
    posterior_cov = cov - gain @ cov[pos]
    return posterior_mean, posterior_cov


def test_prior_means_and_scales_are_hypothesis_conditioned():
    basis, variance, means = prior()
    world = ConditionalWorld(basis, variance, means)
    prediction, scale = world.mean_scale()
    np.testing.assert_array_equal(prediction, means)
    np.testing.assert_allclose(scale ** 2, np.broadcast_to(
        variance + np.sum(basis ** 2, axis=1), means.shape))
    assert not np.array_equal(prediction[0], prediction[1])


@pytest.mark.parametrize("positions", [[0], [1, 3], [4, 0, 2], [0, 1, 2, 3, 4]])
def test_posterior_matches_direct_joint_conditioning(positions):
    basis, variance, means = prior()
    values = np.linspace(.25, .85, len(positions))
    expected_mean, expected_cov = joint_condition(basis, variance, means, positions, values)
    world = ConditionalWorld(basis, variance, means)
    world.update(values, np.array(positions))
    prediction, scale = world.mean_scale()
    np.testing.assert_allclose(prediction, expected_mean, atol=1e-12)
    np.testing.assert_allclose(scale ** 2, np.broadcast_to(
        np.diag(expected_cov), means.shape), atol=1e-12)
    assert (scale >= 0).all()


def test_first_reading_does_not_collapse_unmeasured_hypotheses():
    world = ConditionalWorld(*prior())
    world.update(np.array([.6]), np.array([0]))
    means, _ = world.mean_scale()
    assert np.linalg.norm(means[0, 1:] - means[1, 1:]) > .5
    assert means[0, 0] == means[1, 0] == .6


def test_only_supplied_measured_values_affect_prediction():
    response = np.array([.6, .1, .7, .2, .9])
    first = ConditionalWorld(*prior())
    first.update(response[[0, 3]], np.array([0, 3]))
    response[[1, 2, 4]] = [100., -200., 300.]
    second = ConditionalWorld(*prior())
    second.update(response[[0, 3]], np.array([0, 3]))
    for a, b in zip(first.mean_scale(), second.mean_scale()):
        np.testing.assert_array_equal(a, b)


def test_cumulative_update_is_idempotent_and_matches_one_batch():
    staged = ConditionalWorld(*prior())
    staged.update(np.array([.6]), np.array([0]))
    staged.update(np.array([.6, .3]), np.array([0, 3]))
    batch = ConditionalWorld(*prior())
    batch.update(np.array([.6, .3]), np.array([0, 3]))
    staged.update(np.array([.6, .3]), np.array([0, 3]))
    for a, b in zip(staged.mean_scale(), batch.mean_scale()):
        np.testing.assert_array_equal(a, b)


def test_observation_order_and_class_permutation_are_equivariant():
    basis, variance, means = prior()
    world = ConditionalWorld(basis, variance, means)
    world.update(np.array([.6, .3]), np.array([0, 3]))
    perm = [2, 0, 1]
    other = ConditionalWorld(basis, variance, means[perm])
    other.update(np.array([.3, .6]), np.array([3, 0]))
    prediction, scale = world.mean_scale()
    other_prediction, other_scale = other.mean_scale()
    np.testing.assert_allclose(other_prediction, prediction[perm])
    np.testing.assert_allclose(other_scale, scale[perm])


def test_prior_and_outputs_do_not_alias_caller_arrays():
    basis, variance, means = prior()
    world = ConditionalWorld(basis, variance, means)
    expected, _ = world.mean_scale()
    basis[:] = 200.
    variance[:] = 300.
    means[:] = 400.
    world.mean_scale()[0][:] = -100.
    world.mean_scale()[1][:] = -100.
    np.testing.assert_array_equal(world.mean_scale()[0], expected)


@pytest.mark.parametrize("values,positions", [([np.nan], [0]), ([np.inf], [0]),
                          ([.3, .5], [0, 0]), ([.3], [5]), ([.3], [-1]),
                          ([.3], [True]), ([.3], [.0]), ([.3], [0, 1])])
def test_invalid_observations_cannot_change_existing_posterior(values, positions):
    world = ConditionalWorld(*prior())
    world.update(np.array([.6]), np.array([0]))
    before = world.mean_scale()
    with pytest.raises(ValueError):
        world.update(values, positions)
    for a, b in zip(before, world.mean_scale()):
        np.testing.assert_array_equal(a, b)


def test_existing_acquisition_interface_consumes_conditional_predictions():
    from . import run8
    positions = np.linspace(0., 1., 16)
    basis = np.column_stack((positions * .3, (1. - positions) * .2))
    means = np.vstack((.2 + .5 * positions, .8 - .5 * positions))
    world = ConditionalWorld(basis, np.full(16, .04), means)
    pair = ((means[0], np.ones(16) * .2), (means[1], np.ones(16) * .2), (0, 1))
    readings = means[0].copy()
    readings[[2, 11]] = np.nan
    trajectory, measurements, qc = run8.run_episode_v8(
        readings, pair, (.01, .01), "world", [], world)
    assert len(trajectory) == measurements == run8.BUDGET == 16
    assert [purchases for _, purchases in trajectory] == list(range(1, 17))
    assert qc == 2
    assert np.isfinite([score for score, _ in trajectory]).all()
