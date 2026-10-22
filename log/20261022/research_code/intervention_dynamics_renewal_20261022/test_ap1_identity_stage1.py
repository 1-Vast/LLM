"""Synthetic canaries only; never opens the AP1 source workbook."""
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import ap1_identity_stage1 as reader


class StringScopeTests(unittest.TestCase):
    def make_workbook(self, changed=False):
        directory = tempfile.TemporaryDirectory(dir=reader.OUT/'synthetic')
        self.addCleanup(directory.cleanup)
        path = Path(directory.name)/'canary.xlsx'
        hidden = 'CHANGED_PRIVATE_BODY' if changed else 'PRIVATE_RESPONSE_CANARY'
        numeric = '12345679999' if changed else '86753091234'
        error = '#REF!' if changed else '#DIV/0!'
        boolean = '0' if changed else '1'
        cells = [
            '<c r="B3" t="s"><v>0</v></c>',
            '<c r="D4" t="inlineStr"><is><r><t>INLINE_</t></r><r><t>HEADER</t></r></is></c>',
            '<c r="E4" t="str"><v>LITERAL_HEADER</v></c>',
            f'<c r="D5"><v>{numeric}</v></c>',
            f'<c r="E5" t="str"><f>{hidden}_FORMULA</f><v>{hidden}_FORMULA_CACHE</v></c>',
            '<c r="F5" t="s"><f>1+1</f><v>2</v></c>',
            f'<c r="D6" t="e"><v>{error}</v></c>',
            f'<c r="E6" t="b"><v>{boolean}</v></c>',
            '<c r="H3" t="s"><v>0</v></c>',
            '<c r="D8" t="s"><v>1</v></c>',
            f'<c r="D9" t="inlineStr"><is><t>{hidden}_OUTSIDE_INLINE</t></is></c>',
            f'<c r="H9" t="s"><v>{hidden}_INVALID_INDEX</v></c>']
        n = reader.NS['m']
        rel = reader.REL_ID[1:-3]
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('xl/workbook.xml', f'<workbook xmlns="{n}" xmlns:r="{rel}"><sheets><sheet name="Synthetic" r:id="rId1"/></sheets></workbook>')
            archive.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{n}"><dimension ref="B3:G10"/><sheetData><row>{"".join(cells)}</row></sheetData><mergeCells><mergeCell ref="B3:C3"/></mergeCells></worksheet>')
            archive.writestr('xl/sharedStrings.xml', f'<sst xmlns="{n}"><si><r><t>ALLOWED_</t></r><r><t>HEADER</t></r></si><si><t>{hidden}_UNSELECTED_SHARED</t></si><si><t>{hidden}_FORMULA_SHARED_CACHE</t></si></sst>')
        return path

    def read(self, changed=False):
        return reader.read_stage1(self.make_workbook(changed), {'Synthetic': 'B3:G10'})

    def test_scope_anchored_at_used_range(self):
        positions = reader.allowed_positions('B3:G10')
        self.assertEqual(positions['B3'], ['header', 'identity_candidate'])
        self.assertEqual(positions['G7'], ['header'])
        self.assertEqual(positions['C10'], ['identity_candidate'])
        self.assertNotIn('D8', positions)
        self.assertNotIn('H3', positions)
        self.assertNotIn('A3', positions)

    def test_only_selected_string_cells_decoded(self):
        result = self.read()
        strings = result['sheets']['Synthetic']['strings']
        self.assertEqual({item['coordinate']: item['text'] for item in strings},
                         {'B3': 'ALLOWED_HEADER', 'D4': 'INLINE_HEADER', 'E4': 'LITERAL_HEADER'})
        self.assertEqual(result['decoded_shared_string_indices'], [0])
        self.assertEqual(result['decoded_shared_string_count'], 1)

    def test_numeric_formula_error_boolean_and_outside_canaries_absent(self):
        serialized = json.dumps(self.read())
        for text in ['PRIVATE_RESPONSE_CANARY', '86753091234', '12345679999', '#DIV/0!', 'OUTSIDE_INLINE', 'UNSELECTED_SHARED', 'FORMULA_SHARED_CACHE', 'INVALID_INDEX']:
            self.assertNotIn(text, serialized)

    def test_same_shared_index_at_unauthorized_coordinate_not_exported(self):
        result = self.read()['sheets']['Synthetic']
        self.assertNotIn('H3', [item['coordinate'] for item in result['strings']])
        self.assertNotIn('H3', [item['coordinate'] for item in result['authorized_cells']])

    def test_closed_values_do_not_affect_output(self):
        self.assertEqual(self.read(), self.read(changed=True))

    def test_types_merges_and_no_finite_gate(self):
        result = self.read()
        sheet = result['sheets']['Synthetic']
        types = {cell['coordinate']: cell['type'] for cell in sheet['authorized_cells']}
        self.assertEqual([types[c] for c in ['D5', 'E5', 'F5', 'D6', 'E6']], ['n', 'formula', 'formula', 'e', 'b'])
        self.assertEqual(sheet['merge_ranges'], ['B3:C3'])
        self.assertFalse(result['numeric_values_interpreted'])
        self.assertFalse(result['formulas_interpreted'])
        self.assertFalse(result['finite_gate_performed'])

    def test_lazy_shared_rich_text_excludes_phonetics(self):
        xml = f'<sst xmlns="{reader.NS["m"]}"><si><t>UNSELECTED</t></si><si><r><t>AB</t></r><rPh><t>PHONETIC</t></rPh><r><t>CD</t></r></si></sst>'
        self.assertEqual(reader.selected_shared_strings(io.BytesIO(xml.encode()), {1}), {1: 'ABCD'})


if __name__ == '__main__':
    (reader.OUT/'synthetic').mkdir(parents=True, exist_ok=True)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(StringScopeTests))
    reader.write('SYNTHETIC_TESTS.json', {'utc': reader.utc(), 'tests': result.testsRun,
                 'failures': len(result.failures), 'errors': len(result.errors),
                 'success': result.wasSuccessful(), 'source_workbook_opened': False})
    raise SystemExit(0 if result.wasSuccessful() else 1)
