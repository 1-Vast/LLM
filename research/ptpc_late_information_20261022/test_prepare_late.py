"""Synthetic-only tests: never open any source workbook or prepared array."""
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings

import numpy as np

import prepare_late as preparation


def metadata(sample, pert='p', time='24', background='HCT116'):
    return {'Sample_ID': sample, 'Pert_ID': pert, 'Pert_time_(hrs)': time, 'Cell_line': background}


def xml_rows(rows):
    return BytesIO(('<worksheet xmlns="' + preparation.TAG[1:-1] + '"><sheetData>'
                    '<row r="1"><c r="A1" t="inlineStr"><is><t>Sample_ID</t></is></c>'
                    '<c r="B1"/><c r="C1"/></row>' + ''.join(rows)
                    + '</sheetData></worksheet>').encode())


def row(number, sample, cells):
    return (f'<row r="{number}"><c r="A{number}" t="inlineStr"><is><t>{sample}</t></is></c>'
            + cells + '</row>')


class PreparationBoundaryChecks(unittest.TestCase):
    def test_main_requires_access_freeze_before_source_read(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(preparation, 'OUT', Path(directory)), \
                patch.object(preparation, 'sha256', side_effect=AssertionError('Source hash called prematurely')):
            with self.assertRaises(FileNotFoundError):
                preparation.main()

    def test_nonselected_abundances_are_never_resolved_but_ids_are_checked(self):
        identities = [metadata('selected'), metadata('early', time='6'), metadata('reserve', background='A375')]
        stream = xml_rows([
            row(2, 'selected', '<c r="B2"><v>0</v></c><c r="C2" t="inlineStr"><is><t>NA</t></is></c>'),
            row(3, 'early', '<c r="B3"><f>DO_NOT_RESOLVE</f><v>999</v></c>'),
            row(4, 'reserve', '<c r="B4" t="e"><v>DO_NOT_RESOLVE</v></c>')])
        original_value = preparation.value
        decoded = []

        def guarded_value(cell, shared):
            decoded.append(cell.attrib['r'])
            self.assertNotIn(cell.attrib['r'], ('B3', 'B4'))
            return original_value(cell, shared)

        with patch.object(preparation, 'value', side_effect=guarded_value):
            samples, conditions, counts = preparation.decode_matrix(stream, [], identities, {0}, n_proteins=2)
        np.testing.assert_equal(samples['selected'][0], np.array([0, np.nan]))
        self.assertEqual(conditions['p'], {'selected'})
        self.assertEqual(counts['observed_abundance_cells'], 1)
        self.assertEqual(counts['missing_abundance_cells'], 1)
        self.assertEqual(counts['all_matrix_row_ids_verified'], 3)
        self.assertTrue({'A2', 'A3', 'A4'}.issubset(decoded))

    def test_nonselected_matrix_id_mismatch_rejected(self):
        stream = xml_rows([row(2, 'wrong', '<c r="B2"><f>UNREAD</f></c>')])
        with self.assertRaisesRegex(AssertionError, 'ID mismatch'):
            preparation.decode_matrix(stream, [], [metadata('right', background='A375')], set(), 2)

    def test_sample_identity_spanning_times_rejected_before_values(self):
        identities = [metadata('duplicate'), metadata('duplicate', time='6')]
        with self.assertRaisesRegex(AssertionError, 'spans'):
            preparation.select_rows(identities, [{'pert_id': 'p'}], 1)

    def test_matching_preserves_old_order_not_worksheet_order(self):
        identities = [metadata('a', pert='a'), metadata('b', pert='b'), metadata('reserve', pert='c', background='A375')]
        selected, matched = preparation.select_rows(identities, [{'pert_id': 'b'}, {'pert_id': 'c'}, {'pert_id': 'a'}], 2)
        self.assertEqual(selected, {0, 1})
        np.testing.assert_array_equal(matched, [0, 2])

    def test_selected_negative_and_formula_values_rejected(self):
        for cell in ('<c r="B2"><v>-1</v></c>', '<c r="B2"><f>1</f><v>1</v></c>'):
            with self.subTest(cell=cell), self.assertRaises(AssertionError):
                preparation.decode_matrix(xml_rows([row(2, 'selected', cell)]), [], [metadata('selected')], {0}, 2)

    def test_two_level_medians_preserve_missing_and_do_not_weight_technical_rows(self):
        rows = {'a': [np.array([0., np.nan]), np.array([0., np.nan]), np.array([12., np.nan])],
                'b': [np.array([10., np.nan])]}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', RuntimeWarning)
            result = preparation.aggregate(rows, {'p': {'a', 'b'}}, ['p'])
        self.assertEqual(len(caught), 0)
        np.testing.assert_equal(result, [[5., np.nan]])


if __name__ == '__main__':
    unittest.main()
