"""Synthetic checks only; never open the biological workbook."""
from pathlib import Path
import tempfile
import unittest
import zipfile

import numpy as np

import rank_pilot as p


class RankPilotTests(unittest.TestCase):
    def test_split_is_disjoint_complete_deterministic(self):
        a, b = p.split_ids()
        self.assertEqual((a, b), p.split_ids())
        self.assertEqual((len(a), len(b), set(a) | set(b), set(a) & set(b)),
                         (10, 10, set(range(1, 21)), set()))

    def test_monotone_transform_invariance(self):
        x = np.array([[1, 2, 2, 8], [9, 3, 5, 7.]])
        np.testing.assert_array_equal(p.ranks(x), p.ranks(np.log2(x)))

    def test_observed_ties_not_hash_broken(self):
        np.testing.assert_allclose(p.ranks([[1, 1, 3, 5]]), [[.25, .25, .625, .875]])

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            p.ranks([[0, np.nan]])

    def test_ridge_constant_target(self):
        np.testing.assert_allclose(p.ridge(np.arange(12).reshape(4, 3), np.full(4, .3), np.ones((2, 3))), [.3, .3])

    def test_test_future_cannot_enter_predict(self):
        a, b = p.split_ids()
        prefix = np.random.default_rng(7).normal(size=(6, 20))
        future = np.random.default_rng(8).normal(size=(6, 20))
        first = p.predict(prefix, future[:, np.array(a)-1], a, b)
        future[:, np.array(b)-1] = 9999
        second = p.predict(prefix, future[:, np.array(a)-1], a, b)
        for method in p.METHODS:
            np.testing.assert_array_equal(first[method], second[method])

    def test_equal_predictions_have_zero_paired_sensitivity(self):
        ids = list(range(1, 11))
        predictions = {m: np.arange(10.) for m in p.METHODS}
        future = np.random.default_rng(9).normal(size=(6, 10))
        boot, deleted = p.sensitivity(predictions, future, ids, draws=12)
        self.assertEqual(len(deleted), 45)
        self.assertTrue(all(v == 0 for array in boot.values() for v in array))
        self.assertTrue(all(v == 0 for d in deleted for v in d['differences'].values()))

    def test_roster_ties_deterministic_unique(self):
        ids = list(range(1, 11))
        selected = p.roster(np.ones(10), ids)
        self.assertEqual(selected, p.roster(np.ones(10), ids))
        self.assertEqual(len(set(selected)), 3)

    def synthetic_workbook(self, kind):
        n = p.source.NS['m']
        rid = p.source.RID[1:-3]
        cells = []
        allow = p.response_allowlist()['Fig4B']
        first = sorted(allow)[0]
        for coordinate in sorted(allow):
            if coordinate == first and kind == 'missing':
                continue
            if coordinate == first and kind == 'formula':
                cells.append(f'<c r="{coordinate}"><f>1+1</f><v>2</v></c>')
            else:
                value = 'NaN' if coordinate == first and kind == 'nonfinite' else '2'
                cells.append(f'<c r="{coordinate}"><v>{value}</v></c>')
        # An out-of-scope invalid value must never be decoded.
        cells.append('<c r="D41"><v>SECRET_NOT_NUMERIC</v></c>')
        temp = tempfile.TemporaryDirectory(dir=p.OUT/'synthetic')
        self.addCleanup(temp.cleanup)
        path = Path(temp.name)/'synthetic.xlsx'
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('xl/workbook.xml', f'<workbook xmlns="{n}" xmlns:r="{rid}"><sheets><sheet name="Fig4B" r:id="rId1"/></sheets></workbook>')
            z.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            z.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{n}"><sheetData>{"".join(cells)}</sheetData></worksheet>')
        return path

    def test_scope_exact240_and_outside_invalid_ignored(self):
        a, b, v = p.read_responses(self.synthetic_workbook('valid'))
        self.assertEqual((a.shape, b.shape, len(v)), ((6, 20), (6, 20), 240))

    def test_missing_cell_stops(self):
        with self.assertRaises(p.identity.Failure):
            p.read_responses(self.synthetic_workbook('missing'))

    def test_formula_stops(self):
        with self.assertRaises(p.identity.Failure):
            p.read_responses(self.synthetic_workbook('formula'))

    def test_nonfinite_cell_stops(self):
        with self.assertRaises(p.identity.Failure):
            p.read_responses(self.synthetic_workbook('nonfinite'))


if __name__ == '__main__':
    (p.OUT/'synthetic').mkdir(parents=True, exist_ok=True)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RankPilotTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    p.source.write_json(p.OUT/'SYNTHETIC_TESTS.json', {'utc': p.source.utc(),
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'success': result.wasSuccessful(), 'source_workbook_opened': False})
    raise SystemExit(0 if result.wasSuccessful() else 1)
