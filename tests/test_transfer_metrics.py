"""Contracts of the block Q transfer metrics: specific cosine, AURC, clustered tests and map utility."""
import numpy as np
import pytest

from tools.evaluation.transfer_metrics import (aurc, aurc_difference, centred_cosine, map_utility,
                                               paired_cluster_test, specific_cosine)


def test_specific_cosine_gives_no_credit_for_the_generic_direction():
    rng = np.random.default_rng(0)
    g = np.zeros(20); g[0] = 1.0
    truth = rng.normal(size=(50, 20)) + 3 * g
    generic_only = np.repeat(g[None], 50, 0)
    assert centred_cosine(generic_only, truth).mean() > 0.5
    assert np.allclose(specific_cosine(generic_only, truth, np.repeat(g[None], 50, 0)), 0.0)
    assert np.allclose(specific_cosine(truth, truth, np.repeat(g[None], 50, 0)), 1.0)


def test_zero_prediction_scores_zero():
    assert centred_cosine(np.zeros((3, 4)), np.ones((3, 4))).tolist() == [0.0, 0.0, 0.0]


def test_aurc_rewards_confidence_that_ranks_errors():
    loss = np.array([0.0, 0.1, 0.9, 1.0])
    assert aurc(-loss, loss) < aurc(loss, loss)
    assert aurc(np.zeros(4), loss) == pytest.approx(aurc(np.zeros(4), loss))
    with pytest.raises(ValueError):
        aurc(np.array([]), np.array([]))


def test_paired_cluster_test_uses_cluster_means():
    clusters = np.repeat(np.arange(30), 5)
    a = np.ones(150) * 0.6
    b = np.ones(150) * 0.5
    out = paired_cluster_test(a, b, clusters, draws=2000)
    assert out["n_clusters"] == 30 and out["favour"] == 30
    assert out["estimate"] == pytest.approx(0.1)
    assert out["p_greater"] < 0.001
    null = paired_cluster_test(b, b, clusters, draws=2000)
    assert null["p_two_sided"] == pytest.approx(1.0)


def test_aurc_difference_is_positive_when_a_ranks_better():
    rng = np.random.default_rng(1)
    loss = rng.random(200)
    clusters = np.arange(200) // 4
    out = aurc_difference(-loss, rng.random(200), loss, clusters, resamples=200)
    assert out["estimate"] > 0 and out["p_le_zero"] < 0.05


def test_map_utility_counts_only_active_cells():
    truth = np.zeros((2, 2, 3)); truth[0, 0] = [1, 0, 0]; truth[1, 1] = [0, 1, 0]
    active = np.array([[True, False], [False, True]])
    fills = np.zeros((2, 2, 3)); fills[1, 1] = [0, 1, 0]
    profiled = np.array([[True, False], [False, False]])
    out = map_utility(profiled, fills, truth, active)
    assert out["utility"] == pytest.approx(1.0) and out["n_active"] == 2 and out["wells"] == 1
    none = map_utility(profiled, fills, truth, np.zeros((2, 2), bool))
    assert none["refusal"] == "NO_ACTIVE_CELLS"
