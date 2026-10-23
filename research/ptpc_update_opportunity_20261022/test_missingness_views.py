"""Train-only preprocessing and heldout-label invariance in QC-added views."""
import unittest

import numpy as np

from evaluate_baseline import features, fit_predict


class AddedViewChecks(unittest.TestCase):
    def test_reserved_rows_cannot_change_source_transforms_or_fit(self):
        generator = np.random.default_rng(11)
        chemical = generator.integers(0, 2, (20, 7)).astype(float)
        protein = generator.normal(size=(20, 5))
        protein[::3, 1] = np.nan
        labels = np.array([0, 1] * 10)
        train, test = list(range(14)), list(range(14, 20))
        changed = protein.copy()
        changed[test] = np.nan
        y_changed = labels.copy()
        y_changed[test] = 1 - y_changed[test]
        for name in ('chemistry_raw', 'missingness', 'protein_masked', 'joint_masked'):
            original_source, _ = features(name, train, test, chemical, protein)
            changed_source, _ = features(name, train, test, chemical, changed)
            np.testing.assert_array_equal(original_source, changed_source)
            a = fit_predict(name, 1, train, test, chemical, protein, labels)[0]
            b = fit_predict(name, 1, train, test, chemical, protein, y_changed)[0]
            np.testing.assert_allclose(a, b)
            self.assertTrue(np.all((a >= 0) & (a <= 1)))


if __name__ == '__main__':
    unittest.main()
