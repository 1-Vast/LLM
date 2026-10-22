"""Adversarial identity/value boundaries for the offline followup."""
import io
import json
import sys
import unittest

import auditor_identity_followup as worker
from test_auditor_workbook_identity import synthetic_book

TEST_OUT = worker.OUT / 'synthetic_tests_v2'


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TEST_OUT.mkdir(parents=True, exist_ok=False)
        cls.path = TEST_OUT / 'synthetic.xlsx'
        synthetic_book(cls.path)
        cls.before = worker.base.sha(cls.path)
        cls.all_records = worker.project(cls.path)
        cls.axis_records = worker.project(cls.path, axis_only=True)
        cls.cells = {c['coordinate']: c for c in cls.all_records['sheets'][0]['string_cells']}

    def test_drug_names_and_abbreviations_pass(self):
        for value in ['Tetracycline', 'Azithromycin', 'TET', 'AZI', 'DrugA', 'drug_B']:
            self.assertEqual(worker.filter_string(value), (value, None))

    def test_gene_and_identity_counters_pass(self):
        for value in ['hldE', 'waaF', 'b0012', 'lineage 12', 'day3', 'day 10', 'Passage_7']:
            self.assertEqual(worker.filter_string(value), (value, None))

    def test_general_endpoint_headers_pass(self):
        for value in ['IC90', 'IC 90', 'log2(fold change)', 'OD600', 'IC90_TET', 'DrugA', 'sample_day']:
            self.assertEqual(worker.filter_string(value), (value, None))

    def test_numeric_strings_masked(self):
        for value in ['0.3', '1e-7', '-0.2', '<0.01', '24%', '3 ± 2']:
            self.assertEqual(worker.filter_string(value)[1], 'numeric_string')

    def test_categories_masked(self):
        for value in ['XR', 'CS', 'neutral', 'cross-resistance', 'collateral sensitivity', 'XR_group', 'CS day5', 'synergistic']:
            self.assertEqual(worker.filter_string(value)[1], 'categorical_response_text')

    def test_numeric_measurement_and_dose_masked(self):
        for value in ['IC90=1.25', 'fold change 2.7', 'growth 0.6', '4 µg/ml', '2-fold', 'FC_TET=2.3', '2x']:
            self.assertIsNone(worker.filter_string(value)[0])

    def test_numeric_cell_and_formula_not_emitted(self):
        serialized = json.dumps(self.all_records)
        self.assertNotIn('123456789.4321', serialized)
        self.assertNotIn('SECRET_FORMULA', serialized)
        self.assertNotIn('I2', self.cells)
        self.assertEqual(self.cells['L2']['withheld'], 'formula_or_cached_result')

    def test_axis_scope_and_shared_rich_strings(self):
        axes = {c['coordinate']: c for c in self.axis_records['sheets'][0]['string_cells']}
        self.assertIn('A31', axes)
        self.assertNotIn('B2', axes)
        self.assertEqual(self.cells['M2']['text'], 'Sample ID')
        self.assertEqual(self.cells['N2']['text'], 'Technical replicate')

    def test_source_unchanged(self):
        self.assertEqual(self.before, worker.base.sha(self.path))


if __name__ == '__main__':
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    record = {'utc': worker.base.utc(), 'runtime': sys.executable, 'tests_run': result.testsRun,
              'successful': result.wasSuccessful(), 'failures': len(result.failures), 'errors': len(result.errors),
              'runner_output': output.getvalue()}
    worker.base.write_json(TEST_OUT / 'RESULT.json', record)
    print(json.dumps({k: record[k] for k in ['runtime', 'tests_run', 'successful', 'failures', 'errors']}))
    sys.exit(0 if result.wasSuccessful() else 1)
