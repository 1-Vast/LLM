import unittest

import numpy as np
from sklearn.svm import SVC

from evaluate_late import normalized_block, kernels, fit_score, blocks, panel_features


class FeatureTests(unittest.TestCase):
    def test_late_value_and_mask_information_are_separated(self):
        rng = np.random.default_rng(92)
        arrays = {'chemistry': rng.integers(2, size=(8, 5)),
                  'early': rng.normal(size=(8, 4)), 'late': rng.normal(size=(8, 4))}
        arrays['late'][0, 0] = np.nan
        train, test = np.arange(6), np.arange(6, 8)
        original = blocks(train, test, arrays)
        changed = {k: v.copy() for k, v in arrays.items()}
        changed['late'][6, 1] += 100
        values = blocks(train, test, changed)
        for panel in ('C', 'Craw', 'E', 'M'):
            for a, b in zip(panel_features(original, panel), panel_features(values, panel)):
                np.testing.assert_array_equal(a, b)
        self.assertFalse(np.array_equal(panel_features(original, 'V')[1], panel_features(values, 'V')[1]))
        changed['late'][6, 1] = np.nan
        missing = blocks(train, test, changed)
        for panel in ('C', 'Craw', 'E'):
            for a, b in zip(panel_features(original, panel), panel_features(missing, panel)):
                np.testing.assert_array_equal(a, b)
        self.assertFalse(np.array_equal(panel_features(original, 'M')[1], panel_features(missing, 'M')[1]))

    def test_target_cannot_change_source_transform(self):
        a = np.array([[1., np.nan, 2.], [3., np.nan, 4.], [5., np.nan, np.nan]])
        first, _ = normalized_block(a, np.array([[1., 999., 2.]]), 'protein')
        second, _ = normalized_block(a, np.array([[1e9, -999., np.nan]]), 'protein')
        np.testing.assert_array_equal(first, second)
        self.assertEqual(first.shape[1], 2)
        self.assertAlmostEqual(np.mean(np.sum(first * first, axis=1)), 1.)

    def test_constant_and_missing_blocks_do_not_invent_signal(self):
        a, b = normalized_block(np.ones((3, 2)), np.full((2, 2), 5.), 'mask')
        np.testing.assert_array_equal(a, np.zeros((3, 2)))
        np.testing.assert_array_equal(b, np.zeros((2, 2)))
        a, b = normalized_block(np.full((3, 2), np.nan), np.ones((2, 2)), 'protein')
        self.assertTrue(np.isfinite(a).all() and np.isfinite(b).all())

    def test_cached_kernel_matches_standard_rbf_svc(self):
        rng = np.random.default_rng(76)
        a, b = rng.normal(size=(24, 7)), rng.normal(size=(5, 7))
        y = np.arange(24) % 2
        expected = SVC(C=.1, gamma='scale', class_weight='balanced').fit(a, y).decision_function(b)
        actual, notes, mode = fit_score('rbf', .1, a, b, y, kernels(a, b))
        np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=1e-12)
        self.assertEqual(notes, [])
        self.assertEqual(mode, 'classifier')


if __name__ == '__main__':
    unittest.main()
