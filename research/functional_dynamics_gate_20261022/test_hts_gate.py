"""Meaningful leakage/weight and common-start tests before measured execution."""
import copy
import unittest

import numpy as np

from hts_gate import (drug_split, macro_losses, prefix_features, search_alpha,
                      structure, targets, training_weights, updater)


def fake_rows(drug='drug', rate=.04):
    return [{'drug1': drug, 'cell.line': 'PC9', 'drug1.conc': '1e-6',
             'upid': 'p', 'well': 'A01', 'time': str(t),
             'cell.count': str(2**(3+rate*t)-1)} for t in [0, 4, 8, 20, 24, 28, 32, 60, 80]]


class GateTests(unittest.TestCase):
    def test_future_counts_cannot_change_prefix_or_predictions(self):
        rows = fake_rows()
        a = prefix_features(structure(rows)[0][0])
        changed = copy.deepcopy(rows)
        for r in changed:
            if float(r['time']) > 34:
                r['cell.count'] = 'opaque_future_not_a_number'
        b = prefix_features(structure(changed)[0][0])
        np.testing.assert_array_equal(a['x'], b['x'])
        self.assertEqual(updater(a, .4), updater(b, .4))

    def test_target_access_requires_authorized_drug(self):
        groups, _ = structure(fake_rows())
        with self.assertRaisesRegex(ValueError, 'outside_authorized'):
            targets(groups, ['different'])
        self.assertAlmostEqual(targets(groups, ['drug'])[0], 5.4)

    def test_known_growth_common_start(self):
        f = prefix_features(structure(fake_rows())[0][0])
        self.assertAlmostEqual(f['r0'], .04)
        self.assertAlmostEqual(f['r1'], .04)
        for a in [0, .3, 1]:
            self.assertAlmostEqual(updater(f, a), 5.4)

    def test_identity_split_is_group_stable(self):
        ds = [f'drug{i}' for i in range(14)]
        a = drug_split(ds)
        self.assertEqual(a, drug_split(list(reversed(ds))))
        self.assertEqual([len(a[s]) for s in ['train', 'validation', 'test']], [8, 3, 3])
        self.assertEqual(len(set(sum(a.values(), []))), 14)

    def test_macro_and_fit_weights_do_not_inflate_duplicate_wells(self):
        keys = [('a', 'PC9', '1', 'p', 'A'), ('b', 'PC9', '1', 'p', 'A')]
        pred, y = [0, 0], np.array([1., 3.])
        score = macro_losses(keys, pred, y)['macro_mae']
        extended = keys+[keys[0]]*8
        self.assertEqual(score, macro_losses(extended, [0]*10, np.array([1, 3]+[1]*8))['macro_mae'])
        w = training_weights(extended)
        self.assertAlmostEqual(sum(w[i] for i, k in enumerate(extended) if k[0] == 'a'), w[1])

    def test_alpha_search_uses_same_programs(self):
        f = {'r0': 0., 'r1': 1., 'h': 1., 'anchor': 0.}
        key = [('a', 'PC9', '1', 'p', 'A')]
        a, trials = search_alpha([f], key, np.array([.3]))
        self.assertAlmostEqual(a, .3)
        self.assertEqual(len(trials), 11)
        self.assertAlmostEqual(updater(f, a), .3)

    def test_duplicate_and_invalid_counts_fail(self):
        rows = fake_rows()
        with self.assertRaisesRegex(ValueError, 'duplicate_time'):
            structure(rows+[rows[0]])
        rows[0]['cell.count'] = '-1'
        with self.assertRaisesRegex(ValueError, 'invalid_count'):
            prefix_features(structure(rows)[0][0])


if __name__ == '__main__':
    unittest.main()
