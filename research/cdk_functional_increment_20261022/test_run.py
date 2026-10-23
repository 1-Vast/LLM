"""Checks for label exclusion and legal prefix dependence, without S4 access."""
import unittest
import json
import numpy as np
from run import evaluate, grams, predict, rank_targets


class ProtocolTests(unittest.TestCase):
    def test_source_only_ranks_and_pair_exclusion(self):
        rng = np.random.default_rng(71)
        x = rng.normal(size=(8, 4))
        gram = x @ x.T
        y = np.arange(8, dtype=float)
        groups = ['a'] * 4 + ['b'] * 4
        first = predict(gram, y, groups, list(range(6)), [6, 7], 1)[0]
        y[6:] = [-1000, 1000]
        second = predict(gram, y, groups, list(range(6)), [6, 7], 1)[0]
        np.testing.assert_array_equal(first, second)
        np.testing.assert_allclose(rank_targets(np.array([5, 1, 5, 9])), [.5, .125, .5, .875])

    def test_end_invariance(self):
        rng = np.random.default_rng(72)
        data = rng.dirichlet(np.ones(7), size=(8, 3))
        before = grams(data)
        data[:, 2] = np.nan
        after = grams(data)
        for key in before:
            np.testing.assert_array_equal(before[key], after[key])

    def test_no_signal_ties(self):
        predictions, baseline, fallback = predict(np.ones((6, 6)), np.arange(6.),
                                                  ['a'] * 6, [0, 1, 2, 3], [4, 5], 1)
        np.testing.assert_allclose(predictions, baseline)
        self.assertAlmostEqual(predictions[0], predictions[1])
        self.assertFalse(any(fallback))

    def test_constant_source_targets_and_json(self):
        rng = np.random.default_rng(73)
        x = rng.normal(size=(6, 4))
        predictions = predict(x @ x.T, np.ones(6), ['a'] * 3 + ['b'] * 3,
                              [0, 1, 3, 4], [2, 5], 1)[0]
        np.testing.assert_allclose(predictions, [.5, .5])
        tasks = [['d', 'a', i] for i in range(3)] + [['d', 'b', i] for i in range(3)]
        values = np.array([[1, np.nan], [2, 1], [3, 2], [1, 3], [2, 4], [3, 5.]])
        payload = evaluate(values, tasks, {'early': x @ x.T})
        json.dumps(payload)
        self.assertEqual(payload['palbociclib']['summary']['1']['early']['pairs'], 6)

    def test_separate_condition_monotone_transform_invariance(self):
        rng = np.random.default_rng(74)
        x = rng.normal(size=(8, 4))
        y = np.array([1., 2, 3, 4, 5, 6, 7, 8])
        groups = ['a'] * 4 + ['b'] * 4
        before = predict(x @ x.T, y, groups, [0, 1, 2, 4, 5, 6], [3, 7], 1)[0]
        y[:4] = np.exp(y[:4]) + 1000
        y[4:] = y[4:] ** 3 / 1000
        after = predict(x @ x.T, y, groups, [0, 1, 2, 4, 5, 6], [3, 7], 1)[0]
        np.testing.assert_array_equal(before, after)


if __name__ == '__main__':
    unittest.main()
