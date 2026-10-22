"""Synthetic exact-coordinate identity/design tests without response decoding."""
from copy import deepcopy
import io
import json
import sys
import unittest
import zipfile

import numeric_identity as worker

TEST_OUT = worker.OUT / 'synthetic_tests'


def synthetic_values():
    labels, values = {}, {'Fig1B': {}, 'Fig4B': {}}
    row = 3
    for drug in ['CIP', 'DAP', 'DOX', 'CRO', 'LZD']:
        for day in [2, 4, 6, 8]:
            for lineage in range(1, 5):
                labels[row] = f'{drug} {lineage}'
                values['Fig1B'][f'B{row}'] = str(day)
                row += 1
    for col, _ in worker.PANELS:
        for row in range(9, 29):
            values['Fig4B'][f'{col}{row}'] = str(row - 8)
    for c, value in zip(range(3, 9), ['0', '0.05', '0.1', '0.2', '0.4', '0.8']):
        values['Fig4B'][f'{worker.column(c)}4'] = value
    for c in range(4, 24):
        values['Fig4B'][f'{worker.column(c)}34'] = str(c - 3)
    for row in range(35, 49):
        values['Fig4B'][f'C{row}'] = str(row - 34)
    for c in range(4, 19):
        values['Fig4B'][f'{worker.column(c)}31'] = str(c - 4)
    return labels, values


def workbook(path, values, override=None, omit=None, duplicate=None):
    ns = worker.source.NS['m']
    with zipfile.ZipFile(path, 'x') as z:
        sheets, rels = [], []
        for index, (name, coordinates) in enumerate(values.items(), start=1):
            sheets.append(f'<sheet name="{name}" sheetId="{index}" r:id="rId{index}"/>')
            rels.append(f'<Relationship Id="rId{index}" Target="worksheets/sheet{index}.xml"/>')
            cells = []
            for coord, value in coordinates.items():
                if (name, coord) == omit:
                    continue
                cell = f'<c r="{coord}"><v>{value}</v></c>'
                if override and (name, coord) == override[:2]:
                    cell = override[2]
                cells.append(cell)
                if (name, coord) == duplicate:
                    cells.append(cell)
            cells.append('<c r="ZZ999"><v>FORBIDDEN_RESPONSE_NOT_A_NUMBER</v></c>')
            z.writestr(f'xl/worksheets/sheet{index}.xml', f'<worksheet xmlns="{ns}"><sheetData><row>' + ''.join(cells) + '</row></sheetData></worksheet>')
        z.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + ''.join(sheets) + '</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + ''.join(rels) + '</Relationships>')


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TEST_OUT.mkdir(parents=True, exist_ok=False)
        cls.labels, cls.values = synthetic_values()
        cls.allow = {s: set(v) for s, v in cls.values.items()}
        cls.path = TEST_OUT / 'scope.xlsx'
        workbook(cls.path, cls.values)

    def test_only_allowed_cells_decoded(self):
        actual = worker.read_allowed(self.path, self.allow)
        self.assertEqual(actual, self.values)
        self.assertNotIn('FORBIDDEN', json.dumps(actual))

    def test_products_and_persistent_ids(self):
        result = worker.analyze(self.values, self.labels)
        self.assertTrue(result['main_clone_identity']['complete_5drug_4lineage_4day'])
        self.assertTrue(result['CRO_population_DOX_challenge']['all_panels_same_twenty_ID_set'])
        self.assertEqual(result['CRO_population_DOX_challenge']['embedded_numeric_day_labels'], list(range(1, 15)))

    def test_formula_and_typedstring_excluded(self):
        for label, xml in [('formula', '<c r="B3"><f>2</f><v>2</v></c>'), ('string', '<c r="B3" t="str"><v>2</v></c>')]:
            path = TEST_OUT / f'{label}.xlsx'
            workbook(path, self.values, override=('Fig1B', 'B3', xml))
            with self.subTest(kind=label), self.assertRaises(worker.Failure):
                worker.read_allowed(path, self.allow)

    def test_missing_and_duplicate_fail(self):
        for label, kwargs in [('missing', {'omit': ('Fig1B', 'B3')}), ('duplicate', {'duplicate': ('Fig1B', 'B3')})]:
            path = TEST_OUT / f'{label}.xlsx'
            workbook(path, self.values, **kwargs)
            with self.subTest(kind=label), self.assertRaises(worker.Failure):
                worker.read_allowed(path, self.allow)

    def test_nonfinite_and_noninteger_fail(self):
        path = TEST_OUT / 'nonfinite.xlsx'
        workbook(path, self.values, override=('Fig1B', 'B3', '<c r="B3"><v>Infinity</v></c>'))
        with self.assertRaises(worker.Failure):
            worker.read_allowed(path, self.allow)
        with self.assertRaises(worker.Failure):
            worker.integer('2.5')

    def test_duplicate_main_identity_fails(self):
        labels = dict(self.labels)
        labels[4] = labels[3]
        with self.assertRaises(worker.Failure):
            worker.analyze(self.values, labels)

    def test_panel_duplicate_and_changed_set_detected(self):
        values = deepcopy(self.values)
        values['Fig4B']['J10'] = values['Fig4B']['J9']
        with self.assertRaises(worker.Failure):
            worker.analyze(values, self.labels)
        values = deepcopy(self.values)
        values['Fig4B']['J9'] = '21'
        self.assertFalse(worker.analyze(values, self.labels)['CRO_population_DOX_challenge']['all_panels_same_twenty_ID_set'])

    def test_negative_dose_fails(self):
        values = deepcopy(self.values)
        values['Fig4B']['C4'] = '-0.1'
        with self.assertRaises(worker.Failure):
            worker.analyze(values, self.labels)

    def test_source_unchanged(self):
        before = worker.source.sha(self.path)
        worker.read_allowed(self.path, self.allow)
        self.assertEqual(worker.source.sha(self.path), before)


if __name__ == '__main__':
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    record = {'utc': worker.source.utc(), 'runtime': sys.executable, 'tests_run': result.testsRun,
        'successful': result.wasSuccessful(), 'failures': len(result.failures), 'errors': len(result.errors), 'runner_output': output.getvalue()}
    worker.source.write_json(TEST_OUT / 'RESULT.json', record)
    print(json.dumps({k: record[k] for k in ['runtime', 'tests_run', 'successful', 'failures', 'errors']}))
    sys.exit(0 if result.wasSuccessful() else 1)
