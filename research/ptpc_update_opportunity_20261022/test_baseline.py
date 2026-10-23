import unittest

import numpy as np

from evaluate_baseline import features, fit_predict, select


class BaselineChecks(unittest.TestCase):
    def setUp(self):
        random = np.random.default_rng(7)
        self.chemical = random.integers(0, 2, (24, 8)).astype(float)
        self.protein = random.normal(size=(24, 6))
        self.protein[:18, 0] = np.nan
        self.labels = np.array([0, 1] * 12)

    def test_target_values_do_not_train_transforms(self):
        changed = self.protein.copy()
        changed[18:, :] = 1e10
        a, _ = features('joint', list(range(18)), list(range(18, 24)), self.chemical, self.protein)
        b, _ = features('joint', list(range(18)), list(range(18, 24)), self.chemical, changed)
        np.testing.assert_array_equal(a, b)
        self.assertTrue(np.isfinite(a).all())

    def test_target_labels_cannot_tune_or_fit(self):
        changed = self.labels.copy()
        changed[18:] = 1 - changed[18:]
        inner = np.array([i % 3 for i in range(24)])
        train, test = list(range(18)), list(range(18, 24))
        a = select('joint', train, inner, self.chemical, self.protein, self.labels)
        b = select('joint', train, inner, self.chemical, self.protein, changed)
        self.assertEqual(a, b)
        np.testing.assert_allclose(fit_predict('joint', a[0], train, test, self.chemical, self.protein, self.labels)[0],
                                   fit_predict('joint', b[0], train, test, self.chemical, self.protein, changed)[0])

    def test_single_class_source_falls_back_without_target_labels(self):
        labels = self.labels.copy()
        labels[:18] = 0
        prediction, notes = fit_predict('joint', 1, list(range(18)), list(range(18, 24)), self.chemical, self.protein, labels)
        np.testing.assert_allclose(prediction, 0)
        self.assertEqual(notes, [])


if __name__ == '__main__':
    unittest.main()
