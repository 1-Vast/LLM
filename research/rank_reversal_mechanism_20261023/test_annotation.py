"""Poison/isolation and asymmetric-missing-FDR tests on synthetic XLSX only."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('annotation', HERE/'annotate_fdr.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
np = module.np


def fixture(path, out_of_range=False):
    ns = module.NS['m']
    root = ET.Element(f'{{{ns}}}worksheet')
    data = ET.SubElement(root, f'{{{ns}}}sheetData')
    headers = ['target_a_id', 'target_b_id', *module.DEV, 'A549', 'A427']
    rows = [headers, ['a', 'b', *([.01]*5), 'POISON', 'POISON'],
            ['b', 'a', .2, .2, '', .2, .2, 'POISON', 'POISON'],
            ['a', 'c', *([.05]*5), 'POISON', 'POISON']]
    if out_of_range:
        rows[1][2] = 1.01
    for i, values in enumerate(rows, 1):
        row = ET.SubElement(data, f'{{{ns}}}row', r=str(i))
        for col, val in zip('ABCDEFGHI', values):
            cell = ET.SubElement(row, f'{{{ns}}}c', r=f'{col}{i}', t='str')
            ET.SubElement(cell, f'{{{ns}}}v').text = str(val)
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('xl/sharedStrings.xml', f'<sst xmlns="{ns}"/>')
        archive.writestr('xl/worksheets/sheet2.xml', ET.tostring(root))


class AnnotationTests(unittest.TestCase):
    def test_poison_asymmetric_mirrors_and_missingness(self):
        with tempfile.TemporaryDirectory(dir=module.OUT) as folder:
            path = Path(folder)/'synthetic.xlsx'
            fixture(path)
            high, low, missing, meta = module.read_q(path, [('a', 'b'), ('a', 'c')])
            self.assertEqual(high[0, 0], .2)
            self.assertEqual(low[0, 0], .01)
            self.assertTrue(np.isnan(high[0, 2]))
            self.assertTrue(missing[0, 2])
            self.assertEqual(meta['incomplete_cells'], 1)
            self.assertEqual(meta['mirrored_q_disagreement'], 1)
            self.assertEqual(module.counts(np.array([0, 1]), np.array([-1., -1.]), high[:, 0])['supported_negative'], 1)
            self.assertEqual(module.counts(np.array([0, 1]), np.array([-1., -1.]), low[:, 0])['supported_negative'], 2)
            fixture(path, out_of_range=True)
            with self.assertRaises(AssertionError):
                module.read_q(path, [('a', 'b'), ('a', 'c')])

    def test_unsupported_is_not_unknown_and_zero_is_valid(self):
        indices = np.arange(4)
        result = module.counts(indices, np.array([-1., -1., -1., 1.]), np.array([0., .5, np.nan, .01]))
        self.assertEqual(result, {'n': 4, 'supported_negative': 1, 'known_q': 3, 'q_supported': 2, 'unknown': 1})


if __name__ == '__main__':
    unittest.main()
