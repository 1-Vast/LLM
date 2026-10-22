from io import BytesIO
import unittest

from inspect_identities import project
from inspect_structure import NS


class IdentityMaskTest(unittest.TestCase):
    def test_closed_numeric_string_formula_responses_are_invariant(self):
        sheet = ('<worksheet xmlns="' + NS[1:-1] + '"><sheetData><row r="1">'
                 '<c r="A1" t="s"><v>0</v></c><c r="C1"><v>0</v></c></row>'
                 '<row r="2"><c r="A2" t="s"><v>1</v></c>'
                 '<c r="B2" t="s"><v>2</v></c><c r="C2"><v>{closed}</v></c>'
                 '<c r="D2" t="s"><v>3</v></c><c r="E2"><f>{closed}</f>'
                 '<v>{closed}</v></c></row></sheetData></worksheet>')
        strings = ('<sst xmlns="' + NS[1:-1] + '"><si><t>Compound</t></si>'
                   '<si><t>Drug</t></si><si><t>SG+</t></si><si><t>{closed}</t></si></sst>')
        def run(value):
            return project(BytesIO(sheet.format(closed=value).encode()),
                           BytesIO(strings.format(closed=value).encode()))
        self.assertEqual(run('999'), run('UNOPENED'))
        self.assertNotIn('UNOPENED', str(run('UNOPENED')))
        self.assertEqual(set(run('999')), {'A1', 'C1', 'A2', 'B2'})


if __name__ == '__main__':
    unittest.main()
