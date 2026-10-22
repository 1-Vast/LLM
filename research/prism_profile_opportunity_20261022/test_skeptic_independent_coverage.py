import csv
from pathlib import Path
import tempfile
import unittest

from skeptic_independent_coverage import count_permitted, coverage_ok, finite


class IndependentCoverageTests(unittest.TestCase):
    def test_nominal_boundaries(self):
        for value, nominal, expected in [(18, 23, False), (19, 23, True),
                                         (19, 25, False), (20, 25, True),
                                         (346, 433, False), (347, 433, True)]:
            self.assertEqual(coverage_ok(value, nominal), expected)

    def test_missing_and_invalid_are_distinct(self):
        for token in ['', 'NA', 'nan', 'NULL', 'inf', '-Infinity']:
            self.assertFalse(finite(token))
        self.assertTrue(finite('-0.25'))
        with self.assertRaises(ValueError):
            finite('UNEXPECTED')

    def test_forbidden_cells_are_not_converted(self):
        manifest = {'retained_ids': {'source': ['keep'], 'development': [], 'test': []},
                    'records': [{'core': core, 'replicate_columns': {rep: core + rep for rep in ('X1', 'X2', 'X3')}}
                                for core in ('keep', 'purged')],
                    'contexts': {'paid': {'pool_ids': ['P1']}, 'audit': {'pool_ids': ['P2']}},
                    'paid_pools': ['P1'], 'audit_pools': ['P2']}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
            source = Path(temporary) / 'synthetic.csv'
            with source.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream)
                writer.writerow(['cell', 'keepX1', 'keepX2', 'keepX3', 'purgedX1', 'purgedX2', 'purgedX3'])
                writer.writerow(['paid', '0.5', 'FORBIDDEN', 'FORBIDDEN', 'FORBIDDEN', 'FORBIDDEN', 'FORBIDDEN'])
                writer.writerow(['audit', 'FORBIDDEN', 'NA', '0.2', 'FORBIDDEN', 'FORBIDDEN', 'FORBIDDEN'])
            counters, nominal, converted = count_permitted(source, manifest)
        self.assertEqual(converted, 3)
        self.assertEqual(nominal, {'P1': 1, 'P2': 1})
        self.assertEqual(counters, {'keep': {'X1': {'P1': 1}, 'X2': {'P2': 0}, 'X3': {'P2': 1}}})


if __name__ == '__main__':
    unittest.main(verbosity=2)
