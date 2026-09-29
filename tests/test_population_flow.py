import numpy as np
import pytest
import torch

from virtual_cell.learned_response import (
    ConditionalPopulationFlow, PopulationPair, fit_population_flow, population_mmd,
)


def test_distribution_metric_detects_equal_mean_different_population():
    bimodal = np.array([[-2.], [-2.], [2.], [2.]])
    collapsed = np.zeros((7, 1))
    assert bimodal.mean() == collapsed.mean()
    assert population_mmd(bimodal, collapsed, 1.) > 0.5
    assert population_mmd(bimodal, bimodal[::-1], 1.) == pytest.approx(0., abs=1e-7)


def test_flow_is_set_equivariant_and_vehicle_exact():
    torch.manual_seed(9)
    model = ConditionalPopulationFlow(3, 2)
    x = np.random.default_rng(4).normal(size=(9, 3)).astype(np.float32)
    c = np.array([1., 0.])
    np.testing.assert_array_equal(model.predict_population(x, c, 0.), x)
    y = model.predict_population(x, c, 1.)
    np.testing.assert_allclose(model.predict_population(x[::-1].copy(), c, 1.), y[::-1], atol=1e-6)
    assert y.shape == x.shape


@pytest.mark.parametrize('control,condition,dose', [
    (np.empty((0, 2)), [1], 1), (np.ones((3, 2)), [np.nan], 1),
    (np.ones((3, 2)), [1], -1), (np.ones((3, 3)), [1], 1),
])
def test_invalid_population_queries_refused(control, condition, dose):
    with pytest.raises(ValueError):
        ConditionalPopulationFlow(2, 1).predict_population(control, condition, dose)


def test_condition_groups_cannot_cross_validation_split():
    x = np.ones((3, 2), dtype=np.float32)
    pair = PopulationPair(x, x + 1, np.ones(1), 1., 'same-chemical')
    with pytest.raises(ValueError, match='split_group_overlap'):
        fit_population_flow([pair], [pair], bandwidth=1., epochs=1)


def test_flow_learns_unpaired_translation_without_collapsing_population():
    # Algorithm check only; these are synthetic cells, not biological evidence.
    torch.set_num_threads(2)
    rng = np.random.default_rng(3)
    x = rng.normal(size=(48, 2)).astype(np.float32)
    v = rng.normal(size=(48, 2)).astype(np.float32)
    train = PopulationPair(x, (x + 0.7)[rng.permutation(48)], np.ones(1), 1., 'train')
    val = PopulationPair(v, (v + 0.7)[::-1].copy(), np.ones(1), 1., 'validation')
    model, history = fit_population_flow([train], [val], bandwidth=1., epochs=100, seed=7)
    prediction = model.predict_population(v, np.ones(1), 1.)
    assert population_mmd(prediction, v + 0.7, 1.) < population_mmd(v, v + 0.7, 1.) * 0.4
    assert prediction.std(axis=0).min() > 0.4
    assert len(history) == 100
