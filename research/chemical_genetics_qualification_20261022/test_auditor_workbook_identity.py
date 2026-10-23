"""Synthetic boundary tests; no paper values are opened by this test runner."""
import io
import json
from pathlib import Path
import sys
import unittest
from xml.sax.saxutils import escape
import zipfile

import auditor_workbook_identity as worker

TEST_OUT = worker.OUT / 'synthetic_tests_v2'


def synthetic_book(path):
    ns = worker.NS['m']
    def string(coord, text):
        return f'<c r="{coord}" t="inlineStr"><is><t>{escape(text)}</t></is></c>'
    cells = [string('A1', 'Drug name'), string('B1', 'Lineage'), string('C1', 'IC90'),
        string('A2', 'Tetracycline'), string('B2', 'lineage 12'), string('C2', '4.2e-5'),
        string('D2', 'XR'), string('E2', 'neutral'), string('F2', 'synergistic'),
        string('G2', '4 µg/ml'), string('H2', 'NA'),
        '<c r="I2" t="n"><v>123456789.4321</v></c>',
        '<c r="J2" t="b"><v>1</v></c>', '<c r="K2" t="e"><v>#N/A</v></c>',
        '<c r="L2" t="str"><f>SECRET_FORMULA</f><v>Lineage</v></c>',
        '<c r="M2" t="s"><v>0</v></c>',
        '<c r="N2" t="inlineStr"><is><r><t>Technical </t></r><r><t>replicate</t></r></is></c>']
    sheet = f'<worksheet xmlns="{ns}"><dimension ref="A1:N31"/><sheetData><row r="1">' + ''.join(cells[:3]) + '</row><row r="2">' + ''.join(cells[3:]) + '</row><row r="30">' + string('A30', 'Day') + '</row><row r="31">' + string('A31', 'DO_NOT_EXPORT_ROW31') + '</row></sheetData><mergeCells><mergeCell ref="A4:B4"/></mergeCells></worksheet>'
    with zipfile.ZipFile(path, 'x') as z:
        z.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Schema" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/sharedStrings.xml', f'<sst xmlns="{ns}"><si><r><t>Sample </t></r><r><t>ID</t></r></si></sst>')
        z.writestr('xl/worksheets/sheet1.xml', sheet)


class ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TEST_OUT.mkdir(parents=True, exist_ok=False)
        cls.path = TEST_OUT / 'synthetic.xlsx'
        synthetic_book(cls.path)
        cls.before = worker.sha(cls.path)
        cls.result = worker.project_workbook(cls.path)
        cls.sheet = cls.result['sheets'][0]
        cls.cells = {x['coordinate']: x for x in cls.sheet['first_30_row_string_labels']}
        cls.serialized = json.dumps(cls.result)

    def test_numeric_strings_are_withheld(self):
        for value in ['2', '-0.4', '1e-6', '25%', '<0.01', '≥ 0.1', '1,200', '3 ± 2']:
            with self.subTest(kind='numeric_string'):
                self.assertEqual(worker.filter_label(value)[1], 'numeric_string')

    def test_numeric_cells_and_formula_never_export(self):
        for sentinel in ['123456789.4321', 'SECRET_FORMULA', 'DO_NOT_EXPORT_ROW31']:
            self.assertNotIn(sentinel, self.serialized)
        self.assertNotIn('I2', self.cells)
        self.assertNotIn('J2', self.cells)
        self.assertNotIn('K2', self.cells)
        self.assertEqual(self.cells['L2']['withheld'], 'formula_or_cached_result')

    def test_response_guards(self):
        for value in ['XR', 'CS', 'neutral', 'phenotype', 'fitness', 'growth', 'IC90', 'AUC', 'cross-resistance', 'collateral sensitivity', 'antagonistic', 'synergistic']:
            with self.subTest(kind='response_text'):
                self.assertEqual(worker.filter_label(value)[1], 'suspected_response_text')

    def test_entities_and_doses_deferred(self):
        self.assertEqual(self.cells['A2']['withheld'], 'unqualified_entity_or_text_deferred')
        self.assertEqual(self.cells['G2']['withheld'], 'dose_or_unit_text_deferred')
        self.assertNotIn('Tetracycline', self.serialized)

    def test_parenthetical_entity_cannot_hide_in_header(self):
        self.assertEqual(worker.filter_label('Drug (Tetracycline)')[1], 'unqualified_entity_or_text_deferred')
        self.assertIsNone(worker.filter_label('Concentration (µg/ml)')[0])

    def test_inline_shared_rich_identity(self):
        self.assertEqual(self.cells['A1']['label'], 'Drug name')
        self.assertEqual(self.cells['B2']['label'], 'lineage 12')
        self.assertEqual(self.cells['M2']['label'], 'Sample ID')
        self.assertEqual(self.cells['N2']['label'], 'Technical replicate')

    def test_row_boundary(self):
        self.assertEqual(self.cells['A30']['label'], 'Day')
        self.assertNotIn('A31', self.cells)

    def test_structure_and_type_counts(self):
        self.assertEqual(self.sheet['declared_dimension'], 'A1:N31')
        self.assertEqual(self.sheet['merged_ranges'], ['A4:B4'])
        self.assertEqual(self.sheet['cell_type_counts'], {'inlineStr': 14, 'n': 1, 'b': 1, 'e': 1, 'str': 1, 'formula_cells': 1, 's': 1})

    def test_source_unchanged(self):
        self.assertEqual(worker.sha(self.path), self.before)
        self.assertEqual(self.result['source_sha256_after'], self.before)


if __name__ == '__main__':
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProjectionTests))
    log = {'utc': worker.utc(), 'runtime': sys.executable, 'tests_run': result.testsRun,
           'successful': result.wasSuccessful(), 'failures': len(result.failures),
           'errors': len(result.errors), 'runner_output': output.getvalue()}
    worker.write_json(TEST_OUT / 'RESULT.json', log)
    print(json.dumps({k: log[k] for k in ['runtime', 'tests_run', 'successful', 'failures', 'errors']}))
    sys.exit(0 if result.wasSuccessful() else 1)
