"""Meaningful numerical and held-out-label invariance checks."""
import unittest

import numpy as np

from evaluate import GRIDS, losses, predict, select


class ForecastChecks(unittest.TestCase):
    def setUp(self):
        self.data = np.random.default_rng(42).dirichlet(np.ones(4), size=(6, 3))
        self.context = ['a', 'a', 'a', 'b', 'b', 'b']

    def test_probability_and_loss_extremes(self):
        self.assertAlmostEqual(losses(np.array([1., 0]), np.array([0., 1]))['hellinger2'], 1)
        self.assertAlmostEqual(losses(np.array([1., 0]), np.array([0., 1]))['tv'], 1)
        for name, grid in GRIDS.items():
            for parameter in grid:
                p = predict(name, parameter, list(range(5)), 5, self.data, self.context)
                self.assertTrue(np.all(p >= 0))
                self.assertAlmostEqual(p.sum(), 1)

    def test_target_terminal_cannot_change_choice_or_prediction(self):
        other = self.data.copy()
        other[5, 2] = [1, 0, 0, 0]
        train = list(range(5))
        self.assertEqual(select(train, self.data, self.context), select(train, other, self.context))
        for name, grid in GRIDS.items():
            for parameter in grid:
                np.testing.assert_allclose(predict(name, parameter, train, 5, self.data, self.context),
                                           predict(name, parameter, train, 5, other, self.context))

    def test_early_only_cannot_read_middle(self):
        other = self.data.copy()
        other[:, 1] = np.roll(other[:, 1], 1, axis=1)
        for name in ('condition', 'early', 'early_shrink', 'early_kernel', 'early_ridge'):
            for parameter in GRIDS[name]:
                np.testing.assert_allclose(predict(name, parameter, list(range(5)), 5, self.data, self.context),
                                           predict(name, parameter, list(range(5)), 5, other, self.context))


if __name__ == '__main__':
    unittest.main()
