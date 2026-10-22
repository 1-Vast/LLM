"""Meaningful boundary and access tests before any real conversion."""
import csv
from pathlib import Path
import tempfile
import unittest

import numpy as np

from coverage import at_least_four_fifths, finite_token, read_mask, slots_for, summarize
from prepare import LOG


def fixture():
    ids = {'source': ['s' + str(i) for i in range(300)],
           'development': ['d' + str(i) for i in range(80)],
           'test': ['t' + str(i) for i in range(210)]}
    contexts = {'c' + str(i): {'pool_ids': ['p' + str(i // 5)]} for i in range(100)}
    records = [{'core': core, 'compound_plate': ('plate' + str(int(core[1:]) // 30) if core.startswith('t') else part)}
               for part, values in ids.items() for core in values]
    manifest = {'contexts': contexts, 'paid_pools': ['p0', 'p1'],
                'audit_pools': ['p' + str(i) for i in range(2, 20)],
                'retained_ids': ids, 'records': records,
                'original_counts': {k: len(v) for k, v in ids.items()},
                'original_plate_assignment': {'test': ['plate' + str(i) for i in range(7)]}}
    all_ids = sorted(core for values in ids.values() for core in values)
    slots = slots_for(manifest)
    return manifest, all_ids, slots, np.ones((len(all_ids), len(slots)), dtype=bool)


class CoverageTests(unittest.TestCase):
    def test_exact_integer_eighty_percent_boundary(self):
        self.assertTrue(at_least_four_fifths(19, 23))
        self.assertFalse(at_least_four_fifths(18, 23))
        self.assertTrue(at_least_four_fifths(347, 433))
        self.assertFalse(at_least_four_fifths(346, 433))

    def test_nonfinite_tokens_and_malformed_abort(self):
        for token in ('NA', '', 'nan', 'inf', '-inf'):
            self.assertFalse(finite_token(token))
        self.assertTrue(finite_token('-1.25'))
        with self.assertRaises(ValueError):
            finite_token('BROKEN_LABEL')

    def test_fully_observed_pass(self):
        manifest, ids, slots, mask = fixture()
        result = summarize(mask, ids, slots, manifest)
        self.assertTrue(result['passed'])
        self.assertEqual(result['counts']['test']['qualified'], 210)

    def test_source_minimum_not_test_only_gate(self):
        manifest, ids, slots, mask = fixture()
        mask[ids.index('s0')] = False
        result = summarize(mask, ids, slots, manifest)
        self.assertFalse(result['gates']['source_at_least_300'])
        self.assertTrue(result['gates']['test_retention_at_least_70_percent'])

    def test_seventy_percent_exact_and_no_repartition(self):
        manifest, ids, slots, mask = fixture()
        # Remove nine per plate: exactly147/210remain and every original plate21.
        for core in manifest['retained_ids']['test']:
            if int(core[1:]) % 30 < 9:
                mask[ids.index(core)] = False
        self.assertTrue(summarize(mask, ids, slots, manifest)['passed'])
        mask[ids.index('t9')] = False
        result = summarize(mask, ids, slots, manifest)
        self.assertFalse(result['gates']['test_retention_at_least_70_percent'])
        self.assertEqual(len(result['test_plates']), 7)

    def test_zero_plate_stops_even_if_six_plates_and_total_pass(self):
        manifest, ids, slots, mask = fixture()
        for i in range(30):
            mask[ids.index('t' + str(i))] = False
        result = summarize(mask, ids, slots, manifest)
        self.assertTrue(result['gates']['six_test_plates_each_at_least_10'])
        self.assertTrue(result['gates']['test_retention_at_least_70_percent'])
        self.assertFalse(result['gates']['all_seven_test_plates_nonzero'])
        self.assertFalse(result['passed'])

    def test_aggregate_panel_allows_zero_pool_but_reports_it(self):
        manifest, ids, slots, mask = fixture()
        for j, slot in enumerate(slots):
            if slot['replicate'] == 'X2' and slot['pool'] == 'p2':
                mask[:, j] = False
        result = summarize(mask, ids, slots, manifest)
        self.assertTrue(result['passed'])
        self.assertEqual(result['details'][0]['finite_by_pool']['X2']['p2'], 0)

    def test_paid_pool_qualification_is_separate(self):
        manifest, ids, slots, mask = fixture()
        index = ids.index('t0')
        selected = [j for j, s in enumerate(slots) if s['replicate'] == 'X1' and s['pool'] == 'p0']
        mask[index, selected[:2]] = False
        result = summarize(mask, ids, slots, manifest)
        self.assertNotIn('t0', result['qualified_ids']['test'])

    def test_converter_never_parses_unpermitted_numeric_fields(self):
        manifest = {'contexts': {'c1': {'pool_ids': ['p1']}, 'c2': {'pool_ids': ['p2']}},
                    'paid_pools': ['p1'], 'audit_pools': ['p2'],
                    'retained_ids': {'source': ['a'], 'development': [], 'test': []},
                    'records': [{'core': 'a', 'replicate_columns': {'X1': 'a1', 'X2': 'a2', 'X3': 'a3'}}]}
        folder = LOG / 'synthetic'
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder) as temp:
            path = Path(temp) / 'allowed.csv'
            with path.open('w', newline='', encoding='utf-8') as stream:
                csv.writer(stream).writerows([['row', 'a1', 'a2', 'a3', 'unused'],
                                             ['c1', '-1', 'NEVER_PARSE', 'NEVER_PARSE', 'NEVER_PARSE'],
                                             ['c2', 'NEVER_PARSE', 'NA', '0.5', 'NEVER_PARSE']])
            mask, ids, slots = read_mask(path, manifest)
            self.assertEqual(ids, ['a'])
            self.assertEqual(mask.tolist(), [[True, False, True]])
            self.assertEqual(len(slots), 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
