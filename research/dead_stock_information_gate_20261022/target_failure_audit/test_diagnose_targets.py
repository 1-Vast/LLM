"""Canaries enforce numeric exposure scope, including affected-well siblings."""
import json
import unittest

import diagnose_targets as audit


class Tracked(str):
    reads = []

    def __new__(cls, text, label):
        item = super().__new__(cls, text)
        item.label = label
        return item

    def __float__(self):
        self.reads.append(self.label)
        if self.label.startswith('closed'):
            raise AssertionError('closed_value_parsed')
        return float(str(self))


class ExposureTests(unittest.TestCase):
    def setUp(self):
        Tracked.reads = []

    def test_only_target_live_and_individually_invalid_extra_fields(self):
        rows = [(2, {audit.LIVE: Tracked('0', 'closed_prefix'), audit.TOTAL: Tracked('x', 'closed_T0'), audit.DEAD: Tracked('x', 'closed_D0')}),
                (3, {audit.LIVE: Tracked('5', 'L72_valid'), audit.TOTAL: Tracked('x', 'closed_T72_valid'), audit.DEAD: Tracked('x', 'closed_D72_valid')}),
                (4, {audit.LIVE: Tracked('-2', 'L72_bad'), audit.TOTAL: Tracked('3', 'T72_bad'), audit.DEAD: Tracked('5', 'D72_bad')}),
                (5, {audit.LIVE: Tracked('0', 'closed_future'), audit.TOTAL: Tracked('x', 'closed_Tfuture'), audit.DEAD: Tracked('x', 'closed_Dfuture')})]
        live = audit.live_pass(rows, {3: {'img': '1'}, 4: {'img': '2'}})
        bad = {row: record for row, record in live.items() if record['observed_live']['classification'] != 'valid_nonnegative'}
        relations = audit.relation_pass(rows, bad)
        self.assertEqual(Tracked.reads, ['L72_valid', 'L72_bad', 'T72_bad', 'D72_bad'])
        self.assertEqual(set(relations), {4})
        self.assertTrue(relations[4]['arithmetic']['live_plus_dead_equals_total_exact'])

    def test_closed_value_perturbation_does_not_change_output(self):
        def run(closed):
            rows = [(2, {audit.LIVE: closed, audit.TOTAL: closed, audit.DEAD: closed}),
                    (3, {audit.LIVE: '5', audit.TOTAL: closed, audit.DEAD: closed})]
            live = audit.live_pass(rows, {3: {'img': '1'}})
            relations = audit.relation_pass(rows, {})
            return live, relations
        self.assertEqual(run('NaN'), run('9999999999'))

    def test_bad_value_classes_do_not_emit_nonfinite_json_numbers(self):
        expected = {'': 'missing_empty', ' ': 'missing_empty', 'NA': 'malformed',
                    'NaN': 'nonfinite', 'Inf': 'nonfinite', '-Inf': 'nonfinite',
                    '1e999': 'nonfinite', '-0.5': 'negative', '0': 'valid_nonnegative'}
        for literal, classification in expected.items():
            result = audit.parse_observed(literal)
            self.assertEqual(result['classification'], classification)
            json.dumps(result, allow_nan=False)

    def test_negative_image_is_invalid_even_if_panel_mean_positive(self):
        rows = [(index, {audit.LIVE: value}) for index, value in enumerate(['20', '-2', '30'], 2)]
        live = audit.live_pass(rows, {index: {'img': str(index-1)} for index in range(2, 5)})
        self.assertGreater(sum(record['observed_live']['finite_value'] for record in live.values())/3, 0)
        self.assertEqual(sum(record['observed_live']['classification'] == 'negative' for record in live.values()), 1)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ExposureTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    audit.save('SYNTHETIC_TESTS.json', {'utc': audit.utc(), 'tests_run': result.testsRun,
                                      'success': result.wasSuccessful(), 'failures': len(result.failures),
                                      'errors': len(result.errors)})
    raise SystemExit(0 if result.wasSuccessful() else 1)
