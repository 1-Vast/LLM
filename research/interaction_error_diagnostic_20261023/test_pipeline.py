"""Synthetic poison/leakage checks, not biological research outcomes."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('diagnostic', HERE/'run.py')
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)
np = diagnostic.np


def fixture(path, mismatch=False):
    ns = diagnostic.NS['m']
    root = ET.Element(f'{{{ns}}}worksheet')
    data = ET.SubElement(root, f'{{{ns}}}sheetData')
    headers = ['target_a_id', 'target_b_id', *diagnostic.DEV, 'A549', 'A427']
    pairs = [('g1', 'g2'), ('g2', 'g1'), ('g1', 'g3'), ('AAVS', 'g1'), ('g1', 'g1')]
    for i, values in enumerate([headers] + [[a, b, *([1.]*5), 'POISON', 'POISON'] for a, b in pairs], 1):
        row = ET.SubElement(data, f'{{{ns}}}row', r=str(i))
        for col, val in zip('ABCDEFGHI', values):
            cell = ET.SubElement(row, f'{{{ns}}}c', r=f'{col}{i}', t='str')
            ET.SubElement(cell, f'{{{ns}}}v').text = str(2. if mismatch and i == 3 and col == 'C' else val)
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('xl/sharedStrings.xml', f'<sst xmlns="{ns}"/>')
        archive.writestr('xl/worksheets/sheet1.xml', ET.tostring(root))


class PipelineTests(unittest.TestCase):
    def test_lung_poison_mirrors_controls(self):
        with tempfile.TemporaryDirectory(dir=diagnostic.OUT) as folder:
            path = Path(folder)/'synthetic.xlsx'
            fixture(path)
            pairs, y, z, meta = diagnostic.load(path, diagnostic.digest(path))
            self.assertEqual(len(pairs), 2)
            self.assertEqual(y.shape, (2, 5))
            self.assertEqual(meta['exclusions'], {'control': 1, 'self': 1})
            self.assertEqual(z.sum(), 4)
            fixture(path, mismatch=True)
            with self.assertRaises(AssertionError):
                diagnostic.load(path, diagnostic.digest(path))

    def test_query_responses_cannot_change_predictions(self):
        rng = np.random.default_rng(10)
        x = rng.normal(size=(50, 4))
        z = np.zeros((50, 10))
        for i in range(50):
            z[i, rng.choice(10, 2, replace=False)] = 1
        y = rng.normal(size=50)
        train, query = np.arange(30), np.arange(30, 50)
        poison = y.copy()
        poison[query] = 1e20
        for configuration in diagnostic.SCORE + diagnostic.IDENTITY:
            with self.subTest(configuration=configuration):
                a = diagnostic.fit_predict(configuration, x, z, y, train, query)
                b = diagnostic.fit_predict(configuration, x, z, poison, train, query)
                np.testing.assert_array_equal(a, b)

    def test_nested_support_fixed_query(self):
        pairs = [(str(i), str(i+1)) for i in range(1200)]
        for salt in (0, 1):
            order = diagnostic.order(pairs, salt)
            self.assertTrue(set(order[:128]) <= set(order[:512]))
            self.assertFalse(set(order[:512]) & set(order[512:]))
            self.assertEqual(len(set(order)), 1200)


if __name__ == '__main__':
    with diagnostic.threadpool_limits(limits=1):
        unittest.main()
