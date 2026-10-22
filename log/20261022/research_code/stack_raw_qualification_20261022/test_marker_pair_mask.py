from io import BytesIO
import unittest

from inspect_marker_pair import project_pair
from inspect_structure import NS


class MarkerPairMaskTest(unittest.TestCase):
    def test_closed_both_channel_values_and_side_table_do_not_change_projection(self):
        sheet = ('<worksheet xmlns="' + NS[1:-1] + '"><row r="2">'
                 '<c r="A2"><v>0</v></c><c r="AB2" t="s"><v>0</v></c>'
                 '<c r="C2"><v>{hidden}</v></c><c r="AC2"><v>{hidden}</v></c>'
                 '<c r="BD2" t="s"><v>1</v></c></row></worksheet>')
        strings = ('<sst xmlns="' + NS[1:-1] + '"><si><t>mKate2+</t></si>'
                   '<si><t>{hidden}</t></si></sst>')
        def run(value):
            return project_pair(BytesIO(sheet.format(hidden=value).encode()),
                                BytesIO(strings.format(hidden=value).encode()), 'AB')
        self.assertEqual(run('980'), run('UNKNOWN'))
        self.assertEqual(run('980')['A2']['identity_literal'], '0')
        self.assertNotIn('UNKNOWN', str(run('UNKNOWN')))


if __name__ == '__main__':
    unittest.main()
