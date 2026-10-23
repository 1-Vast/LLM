"""Synthetic checks; fixtures and test output belong under log/."""
import csv
import unittest

import numpy as np

from run_contrast import COLS, OUT, contrasts, extract


class ContrastTests(unittest.TestCase):
    def fixture(self, bad=None, omit=False):
        directory = OUT / 'synthetic'
        directory.mkdir(exist_ok=True)
        path = directory / 'counts.csv'
        header = ['construct_id', 'target_a_id', 'probe_a_id', 'target_b_id', 'probe_b_id',
                  'plasmid', *COLS, 'A549_T9_1']
        with path.open('w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            for p, size in enumerate([9, 18]):
                for i in range(size - int(omit and p == 0)):
                    values = [3, 7, 15, 31] if p == 0 else [1, 3, 7, 15]
                    if bad is not None and p == i == 0:
                        values[0] = bad
                    writer.writerow([f'{p}_{i}', 'A' if p == 0 else 'C', 'g',
                                     'B' if p == 0 else 'D', 'h', 'POISON', *values, 'POISON'])
        return path

    def test_opaque_fields_and_aggregation(self):
        counts, mapping, ids, means, sizes = extract(self.fixture(), [('A', 'B'), ('C', 'D')])
        np.testing.assert_array_equal(sizes, [9, 18])
        np.testing.assert_allclose(means, [[2, 3, 4, 5], [1, 2, 3, 4]])
        self.assertEqual(counts.shape, (27, 4))
        self.assertEqual(len(ids), 27)
        np.testing.assert_array_equal(np.bincount(mapping), sizes)

    def test_invalid_selected_counts_abort(self):
        for bad in ['', 'NaN', 'inf', '-1', '1.5', 'bad']:
            with self.subTest(bad=bad), self.assertRaises((AssertionError, ValueError)):
                extract(self.fixture(bad=bad), [('A', 'B'), ('C', 'D')])
        with self.assertRaises(AssertionError):
            extract(self.fixture(omit=True), [('A', 'B'), ('C', 'D')])

    def test_log_space_algebra(self):
        means = np.array([[2., 3., 4., 6.], [1., 1., 1., 2.]])
        d, delta = contrasts(means)
        np.testing.assert_allclose(d, [[1, 2, 3, 4]])
        np.testing.assert_allclose(delta, [[-1, -1]])
        np.testing.assert_allclose(contrasts(means + [8, -2, 3, 7])[1], delta)
        baseline = np.array([[5.], [2.]])
        np.testing.assert_allclose(contrasts(means - baseline)[1], delta)
        # +1 means count-depth scaling does NOT preserve log contrasts exactly.
        self.assertNotAlmostEqual(np.log2(2) - np.log2(3), np.log2(3) - np.log2(5))


if __name__ == '__main__':
    unittest.main(verbosity=2)
