"""Exact-date access boundary and conflicting-identity tests."""
import io
import json
import sys
import unittest
import zipfile

import auditor_numeric_identity as worker

TEST_OUT = worker.OUT / 'synthetic_tests'


def fixture(path, replacement=None, omit=None, duplicate=None):
    ns = worker.BASE.NS['m']
    cells, safe, days = [], {}, {}
    for row, (day, lineage) in enumerate(((d, l) for d in (2, 3, 5, 7, 10) for l in range(1, 13)), start=2):
        coord = f'E{row}'
        safe.update({f'B{row}': f'Tetracycline {lineage}/Azithromycin/{day}',
                     f'C{row}': f'Tetracycline {lineage}', f'D{row}': 'Azithromycin'})
        days[coord] = day
        cell = f'<c r="{coord}"><v>{day}</v></c>'
        if replacement and replacement[0] == coord:
            cell = replacement[1]
        if coord != omit:
            cells.append(cell)
        if coord == duplicate:
            cells.append(cell)
    # Valid XML with deliberately invalid numerical contents: accidental decoding fails.
    cells.extend(['<c r="F2"><v>FORBIDDEN_F_VALUE</v></c>', '<c r="G2"><f>FORBIDDEN_FORMULA</f><v>FORBIDDEN_G_VALUE</v></c>',
                  '<c r="E62"><v>FORBIDDEN_OUTSIDE_VALUE</v></c>', '<c r="A2"><v>FORBIDDEN_INDEX</v></c>'])
    with zipfile.ZipFile(path, 'x') as z:
        z.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Fig.5a" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{ns}"><sheetData><row>' + ''.join(cells) + '</row></sheetData></worksheet>')
    return safe, days


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TEST_OUT.mkdir(parents=True, exist_ok=False)
        cls.path = TEST_OUT / 'scope.xlsx'
        cls.safe, cls.days = fixture(cls.path)

    def test_only_exact_allowed_numeric_coordinates(self):
        actual = worker.read_days(self.path)
        self.assertEqual(actual, self.days)
        self.assertEqual(set(actual), worker.COORDS)
        self.assertNotIn('FORBIDDEN', json.dumps(actual))

    def test_full_product_and_row_identity(self):
        rows = worker.compare(self.days, self.safe)
        self.assertEqual(len(rows), 60)
        self.assertEqual({(r['lineage'], r['day_from_E']) for r in rows}, worker.EXPECTED)

    def test_numeric_string_day_mismatch_fails(self):
        days = dict(self.days, E2=3)
        with self.assertRaisesRegex(worker.IdentityFailure, 'numeric_day_string_mismatch'):
            worker.compare(days, self.safe)

    def test_string_axis_conflict_fails(self):
        safe = dict(self.safe, C2='Tetracycline 2')
        with self.assertRaisesRegex(worker.IdentityFailure, 'safe_C_D_identity_conflict'):
            worker.compare(self.days, safe)

    def test_duplicate_identity_fails(self):
        safe = dict(self.safe, B3=self.safe['B2'], C3=self.safe['C2'])
        with self.assertRaisesRegex(worker.IdentityFailure, 'duplicate_lineage_day_key'):
            worker.compare(self.days, safe)

    def test_unexpected_lineage_product_fails(self):
        safe = dict(self.safe, B2='Tetracycline 13/Azithromycin/2', C2='Tetracycline 13')
        with self.assertRaisesRegex(worker.IdentityFailure, 'lineage_day_product_mismatch'):
            worker.compare(self.days, safe)

    def test_formula_string_and_noninteger_day_fail(self):
        for label, cell in [('formula', '<c r="E2"><f>2</f><v>2</v></c>'),
                            ('string', '<c r="E2" t="str"><v>2</v></c>'),
                            ('decimal', '<c r="E2"><v>2.5</v></c>')]:
            path = TEST_OUT / f'{label}.xlsx'
            fixture(path, replacement=('E2', cell))
            with self.subTest(kind=label), self.assertRaises(worker.IdentityFailure):
                worker.read_days(path)

    def test_missing_and_duplicate_coordinate_fail(self):
        for label, kwargs in [('missing', {'omit': 'E2'}), ('duplicate', {'duplicate': 'E2'})]:
            path = TEST_OUT / f'{label}.xlsx'
            fixture(path, **kwargs)
            with self.subTest(kind=label), self.assertRaises(worker.IdentityFailure):
                worker.read_days(path)

    def test_input_bytes_unchanged(self):
        before = worker.BASE.sha(self.path)
        worker.read_days(self.path)
        self.assertEqual(worker.BASE.sha(self.path), before)


if __name__ == '__main__':
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    record = {'utc': worker.BASE.utc(), 'runtime': sys.executable, 'tests_run': result.testsRun,
              'successful': result.wasSuccessful(), 'failures': len(result.failures), 'errors': len(result.errors),
              'runner_output': output.getvalue()}
    worker.BASE.write_json(TEST_OUT / 'RESULT.json', record)
    print(json.dumps({k: record[k] for k in ['runtime', 'tests_run', 'successful', 'failures', 'errors']}))
    sys.exit(0 if result.wasSuccessful() else 1)
