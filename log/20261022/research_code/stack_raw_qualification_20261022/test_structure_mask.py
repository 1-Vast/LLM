"""Canaries for outcome-closed structural inspection."""
from io import BytesIO
import unittest

from inspect_structure import NS, structure


class StructureMaskTest(unittest.TestCase):
    def test_value_and_formula_changes_do_not_change_projection(self):
        template = ('<worksheet xmlns="' + NS[1:-1] + '"><dimension ref="A1:C300"/>'
                    '<sheetData><row r="1"><c r="A1" t="s"><v>0</v></c></row>'
                    '<row r="2"><c r="A2"><f>{formula}</f><v>{value}</v></c></row>'
                    '<row r="3"><c r="A3"><v>{future}</v></c></row>'
                    '</sheetData></worksheet>')
        first = structure(BytesIO(template.format(formula='A1+1', value='9', future='19').encode()))
        second = structure(BytesIO(template.format(formula='Z9/2', value='-900', future='secret').encode()))
        self.assertEqual(first, second)
        self.assertNotIn('secret', str(second))

    def test_stops_after_two_rows_and_exposes_no_cached_value(self):
        raw = ('<worksheet xmlns="' + NS[1:-1] + '"><sheetData>'
               '<row r="1"><c r="A1"><v>NO_READ</v></c></row>'
               '<row r="2"><c r="A2" t="s"><v>NO_READ</v></c></row>'
               '<broken-future').encode()
        result = structure(BytesIO(raw))
        self.assertEqual(len(result['first_rows']), 2)
        self.assertNotIn('NO_READ', str(result))


if __name__ == '__main__':
    unittest.main()
