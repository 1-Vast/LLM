"""Synthetic stage2 policy tests; no AP1 workbook access."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import ap1_identity_stage2 as audit


class IdentityScopeTests(unittest.TestCase):
    def fixture(self, changed=False):
        directory = tempfile.TemporaryDirectory(dir=audit.first.OUT/'synthetic')
        self.addCleanup(directory.cleanup)
        path = Path(directory.name)/'identity.xlsx'
        closed = '12345679999' if changed else '86753091234'
        hidden = 'CHANGED_PRIVATE' if changed else 'PRIVATE_RESPONSE_CANARY'
        n, rel = audit.first.NS['m'], audit.first.REL_ID[1:-3]
        cells = [
            '<c r="A1"><v>24</v></c>', f'<c r="B1"><v>{closed}</v></c>',
            '<c r="C1" t="s"><v>0</v></c>',
            f'<c r="D1" t="str"><f>{hidden}</f><v>{hidden}</v></c>',
            '<c r="E1" t="b"><v>1</v></c>', '<c r="F1" t="e"><v>#DIV/0!</v></c>',
            f'<c r="G1"><v>{closed}</v></c>', '<c r="A2" t="s"><v>0</v></c>',
            '<c r="C2" t="s"><v>1</v></c>',
            '<c r="B2" t="inlineStr"><is><t>INLINE_IDENTITY</t></is></c>']
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('xl/workbook.xml', f'<workbook xmlns="{n}" xmlns:r="{rel}"><sheets><sheet name="Synthetic" r:id="rId1"/></sheets></workbook>')
            archive.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{n}"><sheetData><row>{"".join(cells)}</row></sheetData></worksheet>')
            archive.writestr('xl/sharedStrings.xml', f'<sst xmlns="{n}"><si><t>DESIGN_LABEL</t></si><si><t>{hidden}</t></si></sst>')
        allowed = {'Synthetic': {coordinate: {'field': field, 'allowed_types': sorted(types)} for coordinate, field, types in [
            ('A1', 'Time_design_frame', {'n'}), ('B1', 'alignment_string_candidate', audit.STRING),
            ('C1', 'condition', audit.STRING), ('D1', 'Name', audit.IDENTITY),
            ('E1', 'Name', audit.IDENTITY), ('F1', 'Name', audit.IDENTITY), ('B2', 'Id', audit.STRING)]}}
        return audit.read_identity(path, allowed)

    def test_numeric_identity_opens_but_alignment_numeric_and_response_stay_closed(self):
        result = self.fixture()
        cells = result['sheets']['Synthetic']['cells']
        self.assertEqual(cells['A1']['value'], '24')
        self.assertFalse(cells['B1']['value_opened'])
        self.assertNotIn('value', cells['B1'])
        self.assertNotIn('G1', cells)
        self.assertFalse(result['response_fields_opened'])
        self.assertIn('not automatically biological days', result['Time_interpretation'])

    def test_formulas_errors_booleans_shared_and_inline_boundaries(self):
        result = self.fixture()
        cells = result['sheets']['Synthetic']['cells']
        self.assertEqual(cells['C1']['value'], 'DESIGN_LABEL')
        self.assertEqual(cells['B2']['value'], 'INLINE_IDENTITY')
        self.assertEqual(result['decoded_shared_string_indices'], [0])
        self.assertNotIn('A2', cells)
        for coordinate in ['D1', 'E1', 'F1']:
            self.assertFalse(cells[coordinate]['value_opened'])
        serialized = json.dumps(result)
        for canary in ['PRIVATE_RESPONSE_CANARY', '86753091234', '#DIV/0!']:
            self.assertNotIn(canary, serialized)

    def test_closed_value_changes_do_not_affect_output(self):
        self.assertEqual(self.fixture(), self.fixture(changed=True))

    def test_real_policy_excludes_response_columns_and_numeric_misalignment(self):
        scope = audit.policy()
        self.assertNotIn('E4', scope['Figure 2g'])
        self.assertNotIn('O3', scope['Figure 3b'])
        self.assertNotIn('J2', scope['Figure 5b'])
        self.assertNotIn('K6', scope['Figure 4e'])
        self.assertEqual(set(scope['Figure 4e']['F6']['allowed_types']), audit.STRING)
        self.assertEqual(set(scope['Figure 4e']['D56']['allowed_types']), audit.STRING)
        self.assertEqual(scope['Figure 3b']['G3']['allowed_types'], ['n'])
        self.assertNotIn('D59', scope['Figure 4e'])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IdentityScopeTests))
    audit.first.write('STAGE2_SYNTHETIC_TESTS.json', {'utc': audit.first.utc(), 'tests': result.testsRun,
                      'failures': len(result.failures), 'errors': len(result.errors),
                      'success': result.wasSuccessful(), 'source_workbook_opened': False})
    raise SystemExit(0 if result.wasSuccessful() else 1)
