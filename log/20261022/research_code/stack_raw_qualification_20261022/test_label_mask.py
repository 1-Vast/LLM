from io import BytesIO
import unittest

from inspect_labels import selected_strings
from inspect_structure import NS


class LabelMaskTest(unittest.TestCase):
    def test_closed_values_strings_and_formulas_do_not_affect_output(self):
        sheet = ('<worksheet xmlns="' + NS[1:-1] + '"><sheetData><row r="1">'
                 '<c r="A1" t="s"><v>0</v></c><c r="B1"><v>{closed}</v></c>'
                 '<c r="C1"><f>{formula}</f><v>{closed}</v></c>'
                 '</row></sheetData></worksheet>')
        strings = ('<sst xmlns="' + NS[1:-1] + '"><si><t>Time</t></si>'
                   '<si><t>{closed}</t></si></sst>')
        def run(value):
            return selected_strings(BytesIO(sheet.format(closed=value, formula=value).encode()),
                                    BytesIO(strings.format(closed=value).encode()), {'A1', 'B1', 'C1'})
        self.assertEqual(run('990'), run('SECRET'))
        self.assertEqual(run('990')['A1'], {'label_or_identity_text': 'Time'})
        self.assertNotIn('990', str(run('990')))

    def test_selected_numeric_string_is_blocked(self):
        sheet = ('<worksheet xmlns="' + NS[1:-1] + '"><c r="A1" t="s"><v>0</v></c></worksheet>')
        strings = '<sst xmlns="' + NS[1:-1] + '"><si><t>-1.25e2</t></si></sst>'
        result = selected_strings(BytesIO(sheet.encode()), BytesIO(strings.encode()), {'A1'})
        self.assertEqual(result, {'A1': {'blocked_numeric_string': True}})


if __name__ == '__main__':
    unittest.main()
