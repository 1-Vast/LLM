"""Synthetic denial and aggregation checks; never opens a published workbook."""
import io
import unittest
import zipfile
from decimal import Decimal

import numpy as np

import gate


def fixture(duplicate=False, value='0.5'):
    buffer = io.BytesIO()
    ns = gate.NS['m']
    strings = ['SampleID', 'drug', 'forbidden', 'source', 'later']
    source = f'<row r="2"><c r="A2" t="s"><v>3</v></c><c r="B2"><v>{value}</v></c><c r="C2"><v>DO_NOT_DECODE</v></c></row>'
    sheet = f'<worksheet xmlns="{ns}"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1" t="s"><v>2</v></c></row>{source}'
    sheet += source if duplicate else '<row r="3"><c r="A3" t="s"><v>4</v></c><c r="B3"><v>DO_NOT_DECODE</v></c></row>'
    sheet += '</sheetData></worksheet>'
    with zipfile.ZipFile(buffer, 'w') as z:
        z.writestr('xl/sharedStrings.xml', f'<sst xmlns="{ns}">' + ''.join(f'<si><t>{s}</t></si>' for s in strings) + '</sst>')
        z.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="raw" r:id="rId1"/><sheet name="scaled" r:id="rId2"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Target="worksheets/sheet2.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml', sheet)
        z.writestr('xl/worksheets/sheet2.xml', 'FORBIDDEN_NON_XML_SCALED_CONTENT')
    buffer.seek(0)
    return buffer


class SourceGateTest(unittest.TestCase):
    def test_only_authorized_rows_fields_and_sheet(self):
        values, accesses, skipped = gate.read_source(fixture(), 'raw', {'source'}, ['drug'])
        self.assertEqual(values, {'source': {'drug': .5}})
        self.assertEqual(len(accesses), 1)
        self.assertEqual(accesses[0]['coordinate'], 'B2')
        self.assertEqual(accesses[0]['numeric_token'], '0.5')
        self.assertEqual(skipped, ['later'])

    def test_missing_and_duplicate_source_fail_closed(self):
        with self.assertRaisesRegex(AssertionError, 'Missing authorized'):
            gate.read_source(fixture(), 'raw', {'absent'}, ['drug'])
        with self.assertRaisesRegex(AssertionError, 'Duplicate authorized'):
            gate.read_source(fixture(True), 'raw', {'source'}, ['drug'])

    def test_authorized_bad_token_retained_as_violation(self):
        values, accesses, _ = gate.read_source(fixture(), 'raw', {'later'}, ['drug'])
        self.assertIsNone(values['later']['drug'])
        self.assertEqual(accesses[0]['status'], 'invalid_numeric_token')

    def test_patient_weighting_and_heldout_selection(self):
        hit = np.array([[0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 0, 1],
                        [1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0]], dtype=bool)
        result = gate.opportunity(hit, ['A', 'A', 'B', 'C'], list('abcdef'))
        self.assertAlmostEqual(result['gap'], 1 / 15)
        self.assertAlmostEqual(result['oracle'], .2)
        self.assertEqual(result['patients'][0]['selected'], list('abcde'))
        self.assertEqual(result['mixed_hit_patients'], 3)
        self.assertEqual(result['leave_one_patient_out_label_aggregations'], 3)

    def test_literal_threshold_not_rounded(self):
        token = '0.1999999999999999999999999999999'
        values, _, _ = gate.read_source(fixture(value=token), 'raw', {'source'}, ['drug'])
        self.assertLess(values['source']['drug'], Decimal('.2'))
        self.assertEqual(str(values['source']['drug']), token)

    def test_exact_tie_at_shortlist_cutoff(self):
        # A and B both have exact mean1/2 across54training patients. Their
        # differently distributed rational rates can break a float mean tie.
        rows, patients = [], []
        for i in range(54):
            count = 6 if i < 42 else 2
            a_hits = 2 if i < 21 else 4 if i < 42 else 1
            for j in range(count):
                rows.append([j < a_hits, j < count // 2, 1, 1, 1, 1, 0])
                patients.append(f'P{i:02d}')
        rows.append([1, 0, 1, 1, 1, 1, 0])
        patients.append('T')
        result = gate.opportunity(np.array(rows, dtype=bool), patients, list('abcdefg'))
        target = next(r for r in result['patients'] if r['patient'] == 'T')
        self.assertEqual(target['selected'], list('cdefa'))
        self.assertEqual(target['gap_exact'], '0')


if __name__ == '__main__':
    print('gate_sha256=' + gate.sha(gate.ROOT / 'research/mse_source_gate_20261022/gate.py'), flush=True)
    print('tests_sha256=' + gate.sha(gate.ROOT / 'research/mse_source_gate_20261022/test_gate.py'), flush=True)
    unittest.main()
