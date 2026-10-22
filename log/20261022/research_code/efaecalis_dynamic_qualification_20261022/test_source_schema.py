"""Synthetic exposure boundaries; no real source response values."""
import io
import json
import sys
import unittest
import zipfile
from xml.sax.saxutils import escape

import source_schema as worker

TEST_OUT = worker.OUT / 'synthetic_tests_v2'


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TEST_OUT.mkdir(parents=True, exist_ok=False)
        cls.path = TEST_OUT / 'synthetic.xlsx'
        ns = worker.NS['m']
        def inline(coord, text):
            return f'<c r="{coord}" t="inlineStr"><is><t>{escape(text)}</t></is></c>'
        cells = ''.join([inline('A1', 'Ceftriaxone'), inline('B1', 'Day'), inline('C1', 'IC50'),
            inline('A2', 'CRO lineage 4 day2'), inline('B2', '2'), inline('C2', 'Yes'),
            inline('D2', 'No'), inline('E2', 'CS'), inline('F2', 'Validated'),
            inline('G2', '4 µg/ml'), inline('H2', 'IC50=0.7'), inline('I2', 'UnrecognizedCode'),
            '<c r="J2"><v>123456789.987</v></c>', '<c r="K2" t="b"><v>1</v></c>',
            '<c r="L2" t="str"><f>FORBIDDEN_FORMULA</f><v>drug</v></c>',
            '<c r="M2" t="s"><v>0</v></c>',
            '<c r="N2" t="inlineStr"><is><r><t>technical </t></r><r><t>replicate</t></r></is></c>'])
        with zipfile.ZipFile(cls.path, 'x') as z:
            z.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="schema" sheetId="1" r:id="rId1"/></sheets></workbook>')
            z.writestr('xl/_rels/workbook.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            z.writestr('xl/sharedStrings.xml', f'<sst xmlns="{ns}"><si><t>Doxycycline</t></si></sst>')
            z.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{ns}"><dimension ref="A1:N2"/><sheetData><row>{cells}</row></sheetData><mergeCells><mergeCell ref="A3:B3"/></mergeCells></worksheet>')
        cls.before = worker.sha(cls.path)
        cls.result, cls.manifest = worker.project(cls.path)
        cls.sheet = cls.result['sheets'][0]
        cls.cells = {c['coordinate']: c for c in cls.sheet['string_schema_identity_cells']}

    def test_drug_and_identity_names_not_blanket_masked(self):
        for value in ['Ceftriaxone', 'Doxycycline', 'CRO', 'DOX', 'CRO lineage 4 day2', 'V583']:
            self.assertEqual(worker.filter_text(value)['text'], value)

    def test_binary_and_phenotype_outcomes_masked(self):
        for value in ['Yes', 'No', 'true', 'false', 'Validated', 'Monochromatic', 'XR', 'CR', 'CS', 'neutral', 'resistant', 'sensitive', 'High', 'Low', 'Class A']:
            self.assertIn('withheld', worker.filter_text(value))

    def test_numeric_strings_and_doses_masked(self):
        for value in ['2', '<0.1', '1e-4', '24%', '3 ± 2', '4 µg/ml', 'IC50=0.7', '2-fold']:
            self.assertIn('withheld', worker.filter_text(value))

    def test_control_and_metric_headers_pass(self):
        for value in ['no drug', 'no cells', 'ancestor', 'control', 'IC50', 'OD600', 'AUC', 'Day', 'Concentration']:
            self.assertEqual(worker.filter_text(value)['text'], value)

    def test_unknown_strings_explicitly_annotated(self):
        self.assertIn('unclassified_string_design_exposed', worker.filter_text('UnrecognizedCode')['exposure'])

    def test_numeric_boolean_formula_never_exported(self):
        serialized = json.dumps(self.result)
        self.assertNotIn('123456789.987', serialized)
        self.assertNotIn('FORBIDDEN_FORMULA', serialized)
        self.assertNotIn('J2', self.cells)
        self.assertNotIn('K2', self.cells)
        self.assertEqual(self.cells['L2']['withheld'], 'formula_or_cached_result')

    def test_shared_and_rich_inline_strings(self):
        self.assertEqual(self.cells['M2']['text'], 'Doxycycline')
        self.assertEqual(self.cells['N2']['text'], 'technical replicate')

    def test_structure_and_manifest(self):
        self.assertEqual(self.sheet['declared_dimension'], 'A1:N2')
        self.assertEqual(self.sheet['merged_ranges'], ['A3:B3'])
        self.assertEqual(self.sheet['cell_type_counts']['formula_cells'], 1)
        self.assertEqual(len(self.manifest), 4)

    def test_source_unchanged(self):
        self.assertEqual(worker.sha(self.path), self.before)


if __name__ == '__main__':
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    record = {'utc': worker.utc(), 'runtime': sys.executable, 'tests_run': result.testsRun,
        'successful': result.wasSuccessful(), 'failures': len(result.failures), 'errors': len(result.errors),
        'runner_output': output.getvalue()}
    worker.write_json(TEST_OUT / 'RESULT.json', record)
    print(json.dumps({k: record[k] for k in ['runtime', 'tests_run', 'successful', 'failures', 'errors']}))
    sys.exit(0 if result.wasSuccessful() else 1)
