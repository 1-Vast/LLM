"""Synthetic contract checks; no real workbooks or responses are read."""
import unittest
from forecast import predict_fold


class Isolation(unittest.TestCase):
    def test_only_target_prefix_enters_fold(self):
        source = {'AAAA': [10, 9, 8, 7, 6], 'ANAN': [10, 9, 7, 6, 4]}
        target = {'AAAA': [20, 18, 16, -999, 999], 'ANAN': [20, 18, 14, -999, 999]}
        prefix = lambda: {r: values[:3] for r, values in target.items()}
        before = predict_fold(source, prefix())
        target['AAAA'][3:] = [1e9, -1e9]
        target['ANAN'][3:] = [-1e9, 1e9]
        self.assertEqual(before, predict_fold(source, prefix()))
        source['AAAA'][4] = 123
        self.assertNotEqual(before, predict_fold(source, prefix()))

    def test_future_target_values_rejected_by_interface(self):
        full = {'AAAA': [1, 2, 3, 4, 5], 'ANAN': [1, 2, 3, 4, 5]}
        with self.assertRaises(AssertionError):
            predict_fold(full, full)


if __name__ == '__main__':
    unittest.main()
