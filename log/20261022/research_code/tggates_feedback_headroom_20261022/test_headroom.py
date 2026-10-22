"""Synthetic checks for target isolation, exposure accounting and the frozen baseline protocol."""
from collections import Counter
from copy import deepcopy
import unittest
from unittest.mock import patch

import numpy as np

import prepare
import run_headroom as run


def sample(exp='e', group='1', individual='1', level='Middle', amount='2'):
    return dict(zip(prepare.IDENTITY_FIELDS, [exp, group, individual, 'synthetic', 'Human',
                     'Female', '24 hr', amount, 'μM', level]))


def compound(label, block=None, role='source', middle=(0.9, 0.8), high=(0.7, 0.6), bits=(1, 5)):
    return {'compound_label': label, 'block_id': block or label, 'role': role,
            'fingerprint_on_bits': list(bits), 'unit': 'μM',
            'doses': {level: {'concentration': amount, 'n': 2,
                              'mean': list(values), 'sd': [0.01, 0.02]}
                      for level, amount, values in [('Low', 1, (1.0, 0.95)),
                          ('Middle', 5, middle), ('High', 25, high)]}}


def ledger():
    return {'pipeline_fits': 0, 'sklearn_fit_calls': 0, 'pipeline_fits_by_family': Counter()}


class GuardedSkippedRow(dict):
    def __getitem__(self, key):
        if key in run.RESPONSE_COLUMNS:
            raise AssertionError('Skipped target response accessed')
        return super().__getitem__(key)


class HeadroomTests(unittest.TestCase):
    def test_split_is_hash_stable_and_24_7_8(self):
        groups = [['label' + str(i)] for i in range(39)]
        first = prepare.block_split(groups)
        self.assertEqual(first, prepare.block_split(list(reversed(groups))))
        self.assertEqual(Counter(row['role'] for row in first),
                         {'source': 24, 'development': 7, 'later': 8})

    def test_later_and_controls_never_access_assay_columns(self):
        permitted = sample()
        later = GuardedSkippedRow(sample(exp='later'))
        control = GuardedSkippedRow(sample(group='control', level='Control', amount='0'))
        observed = dict(permitted, **{'DNA(%)': '90', 'LDH(%)': '80'})
        result = run.project_rows([later, control, observed], {prepare.sample_key(permitted): permitted})
        self.assertEqual(result['invalid'], [])
        self.assertEqual(result['records'][0]['values'], [0.9, 0.8])
        self.assertEqual(result['exposure_counters']['assay_field_accesses'], {'DNA(%)': 1, 'LDH(%)': 1})
        self.assertEqual(result['skipped_response_columns_accessed'], 0)

    def test_partial_invalid_exposure_is_counted_and_retained(self):
        allowed, rows = {}, []
        for number, dna, ldh in [('1', '90', ''), ('2', '91', 'inf'), ('3', 'bad', '80')]:
            identity = sample(individual=number)
            allowed[prepare.sample_key(identity)] = identity
            rows.append(dict(identity, **{'DNA(%)': dna, 'LDH(%)': ldh}))
        result = run.project_rows(rows, allowed)
        self.assertEqual(len(result['invalid']), 3)
        self.assertEqual(result['records'], [])
        counters = result['exposure_counters']
        self.assertEqual(counters['assay_field_accesses'], {'DNA(%)': 3, 'LDH(%)': 2})
        self.assertEqual(counters['numeric_cast_attempts'], {'DNA(%)': 3, 'LDH(%)': 1})
        self.assertEqual(counters['numeric_parse_successes'], {'DNA(%)': 2, 'LDH(%)': 1})
        self.assertEqual(counters['finite_numeric_cast_successes'], {'DNA(%)': 2, 'LDH(%)': 0})
        self.assertEqual(result['numeric_exposure_records'][1]['assays']['DNA(%)']['normalized_value'], 0.91)

    def test_finite_negative_and_above_100_are_not_clipped(self):
        identity = sample()
        result = run.project_rows([dict(identity, **{'DNA(%)': '-5', 'LDH(%)': '120'})],
                                  {prepare.sample_key(identity): identity})
        self.assertEqual(result['records'][0]['values'], [-0.05, 1.2])
        self.assertEqual(len(result['records'][0]['quality_flags']), 2)
        self.assertEqual(result['invalid'], [])

    def test_duplicate_and_absent_selected_keys_abort_projection(self):
        one, two = sample(), sample(individual='2')
        row = dict(one, **{'DNA(%)': '90', 'LDH(%)': '80'})
        result = run.project_rows([row, row], {prepare.sample_key(one): one, prepare.sample_key(two): two})
        self.assertEqual({entry['reason'] for entry in result['invalid']},
                         {'duplicate_selected_key', 'selected_key_absent'})
        self.assertEqual(result['exposure_counters']['assay_field_accesses']['DNA(%)'], 1)

    def test_aggregation_uses_all_manifest_replicates_and_excludes_later(self):
        doses, records = {}, []
        for level, amount in [('Low', '1'), ('Middle', '5'), ('High', '25')]:
            samples = [sample(group=level, individual=str(i), level=level, amount=amount) for i in [1, 2]]
            doses[level] = {'value': amount, 'unit': 'μM', 'samples': samples}
            records += [{'key': list(prepare.sample_key(identity)), 'values': values}
                        for identity, values in zip(samples, [[0.6, 0.8], [1.0, 0.6]])]
        base = {'compound_label': 's', 'block_id': 'b', 'role': 'source', 'fingerprint_on_bits': [1], 'doses': doses}
        later = dict(base, compound_label='later', role='later')
        rows = run.aggregate({'compounds': [base, later]}, {'records': records})
        self.assertEqual(len(rows), 1)
        self.assertTrue(np.allclose(rows[0]['doses']['Middle']['mean'], [0.8, 0.7]))
        self.assertTrue(np.allclose(rows[0]['doses']['Middle']['sd'], np.std([[0.6, 0.8], [1.0, 0.6]], axis=0, ddof=1)))

    def test_feature_construction_does_not_use_high_or_low_outcomes(self):
        rows = [compound('a')]
        changed = deepcopy(rows)
        changed[0]['doses']['High']['mean'] = [1000, -1000]
        changed[0]['doses']['Low']['mean'] = [-999, 999]
        for branch in ['dose_chem', 'full_middle']:
            first = run.feature_arrays(rows, branch, ['μM'])
            second = run.feature_arrays(changed, branch, ['μM'])
            self.assertTrue(all(np.array_equal(a, b) for a, b in zip(first, second)))

    def test_source_cv_holds_entire_block_out_and_counts_29_candidates(self):
        rows = [compound(str(i), block='b' + str(i)) for i in range(24)]
        rows.append(compound('extra', block='b0'))
        calls = []
        def fake_fit(train, test, config, units, counts):
            self.assertFalse({row['block_id'] for row in train} & {row['block_id'] for row in test})
            calls.append(config['family'])
            counts['active_fit'] = {'status': 'STARTED'}
            return np.tile([0.7, 0.6], (len(test), 1))
        with patch.object(run, 'fit_predict', side_effect=fake_fit):
            scores, selected = run.select_source(rows, ['μM'], ledger())
        self.assertEqual(len(scores), 29)
        self.assertEqual(len(calls), 29 * 24)
        self.assertEqual(len(selected), 9)
        self.assertEqual(sum(row['compound_count'] for row in selected['middle_copy']['group_losses']), 25)

    def test_krr_high_regularization_reverts_to_source_mean_not_zero(self):
        train = [compound('a', high=(0.8, 0.7)), compound('b', high=(1.0, 0.9))]
        test = [compound('test', high=(-100, -200))]
        config = {'family': 'krr_full_middle', 'features': 'full_middle', 'alpha': 1e10, 'kernel_scale': 0.5}
        predictions = run.fit_predict(train, test, config, ['μM'], ledger())
        self.assertTrue(np.allclose(predictions, [[0.9, 0.8]], atol=1e-8))

    def test_tanimoto_tie_is_alphabetical_and_ignores_test_target(self):
        train = [compound('z', high=(0.5, 0.4)), compound('a', high=(0.8, 0.7))]
        test = [compound('test', high=(-100, 100))]
        first = run.fit_predict(train, test, {'family': 'tanimoto_residual'}, ['μM'], ledger())
        test[0]['doses']['High']['mean'] = [1000, -1000]
        second = run.fit_predict(train, test, {'family': 'tanimoto_residual'}, ['μM'], ledger())
        self.assertTrue(np.allclose(first, second))
        self.assertTrue(np.allclose(first, [[0.8, 0.7]]))

    def test_bootstrap_resamples_whole_blocks_with_compound_weights(self):
        rows = [compound('a', block='x'), compound('b', block='x'), compound('c', block='y')]
        losses = run.group_losses(rows, np.array([[0.6, 0.5], [0.6, 0.5], [0.6, 0.5]]))
        self.assertEqual([row['compound_count'] for row in losses], [2, 1])
        first = run.bootstrap_groups({'family': losses}, repeats=100)
        self.assertEqual(first, run.bootstrap_groups({'family': losses}, repeats=100))
        self.assertTrue(np.allclose(first['families']['family']['dna_mae_percentile_95'], [0.1, 0.1]))
        self.assertFalse(first['additional_significance_gate'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
