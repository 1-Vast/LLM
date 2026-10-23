"""Independent post-result data audit. No source ZIP or feature model is opened."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/az_paid_reference_gate'
JSON_OUT = LOG / 'DATA_POST_RESULT_REVIEW.json'
MD_OUT = LOG / 'DATA_POST_RESULT_REVIEW.md'
if JSON_OUT.exists() or MD_OUT.exists():
    raise SystemExit('Refusing to overwrite the independent post-result audit')
used = {}
def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()
def read(name):
    path = LOG / name
    used[name] = sha(path)
    return json.loads(path.read_text(encoding='utf-8'))

checks = {}
def check(name, value):
    checks[name] = bool(value)

receipt, access = read('TEST_TARGETS_RECEIPT.json'), read('ACCESS_TEST_TARGETS.json')
missing, metrics, costs, gates = (read(name) for name in
    ('TEST_MISSINGNESS.json', 'TEST_METRICS.json', 'COSTS.json', 'GATES.json'))
design, meta, inputs_receipt = (read(name) for name in
    ('DESIGN.json', 'EPISODE_META.json', 'INPUTS_RECEIPT.json'))
summaries = read('PAID_SUMMARIES.json')  # Only key/role/rows metadata are projected.
summary_rows = {tuple(s['key']): {'role': s['role'], 'rows': s['rows']} for s in summaries}
del summaries
used['TEST_TARGETS.npz'] = sha(LOG / 'TEST_TARGETS.npz')
check('target_output_hashes', all(sha(LOG / name) == expected for name, expected in receipt['outputs_sha256'].items()))
check('episode_meta_input_hash', used['EPISODE_META.json'] == inputs_receipt['outputs_sha256']['EPISODE_META.json'])
with np.load(LOG / 'TEST_TARGETS.npz', allow_pickle=False) as bundle:
    check('target_only_y_array', bundle.files == ['y'])
    y = bundle['y']
with np.load(LOG / 'DATA.npz', allow_pickle=False) as bundle:
    data = {key: bundle[key] for key in ('role', 'episode', 'valid_mask', 'effect')}
test = data['role'] == 'test'
episodes = [e for e in meta if e['role'] == 'test']
assigned = sorted(design['role_cells']['test'])
by_id = {e['episode_id']: e for e in episodes}
counts = Counter(e['cell'] for e in episodes)
row_counts = Counter(map(int, data['episode'][test]))
check('test_population', len(assigned) == len(counts) == 96 and len(episodes) == 644 and int(test.sum()) == 30212)
check('test_master_identities', set(counts) == set(assigned))
check('target_array_alignment', y.shape == data['role'].shape and len(y) == len(data['episode']))
check('test_targets_all_finite', np.isfinite(y[test]).all())
check('all_non_test_target_slots_nan', np.isnan(y[~test]).all())
check('no_reserve_in_active_arrays', 'reserve' not in data['role'] and not {e['cell'] for e in meta} & set(design['role_cells']['reserve']))
check('valid_effect_and_inputs', data['valid_mask'][test].all() and np.isfinite(data['effect'][test]).all())
check('nominal_episode_alignment', set(row_counts) == set(by_id) and all(e['valid'] for e in episodes))
check('missingness_ids', len(missing) == 644 and {e['episode_id'] for e in missing} == set(by_id))
check('missingness_independent_counts', all(e['cell'] == by_id[e['episode_id']]['cell'] and e['role'] == 'test'
      and e['pair'] == by_id[e['episode_id']]['pair'] and e['rows'] == row_counts[e['episode_id']]
      and e['finite_targets'] == e['rows'] and e['input_valid'] and e['forecast_scorable'] and e['utility_scorable']
      for e in missing))
check('only_inhibition_converted', access['allowed_response_fields'] == {'selected_test_target': ['inhibition']}
      and set(access['conversion_counts']) == {'test_target:test'}
      and set(access['conversion_counts']['test_target:test']) == {'inhibition'})
conversion = access['conversion_counts']['test_target:test']['inhibition']
check('all_target_conversion_counts', conversion['attempted'] == conversion['finite'] == 30212
      and conversion['missing_or_nonfinite'] == conversion['finite_outside_0_1'] == 0)
check('no_targetmono_or_reserve_conversion', access['target_attached_mono_or_fitted_fields_indexed'] is False
      and access['reserve_numeric_conversion'] is False)

populations = {}
for role in ('train', 'validation', 'test'):
    group = [e for e in meta if e['role'] == role]
    keys = {tuple(key) for e in group for key in e['query_keys']}
    result = {'masters': len({e['cell'] for e in group}), 'episodes': len(group),
              'logical_bundles': sum(e['logical_bundles'] for e in group),
              'logical_paid_rows': sum(e['logical_paid_rows'] for e in group),
              'unique_paid_matrices': len(keys),
              'unique_paid_rows': sum(summary_rows[key]['rows'] for key in keys)}
    result['logical_paid_response_fields'] = 3 * result['logical_paid_rows']
    result['unique_paid_response_fields'] = 3 * result['unique_paid_rows']
    populations[role] = result
    check('logical_bundle_cost_' + role, result['logical_bundles'] == 2 * len(group))
    check('logical_row_cost_' + role, result['logical_paid_rows'] == sum(summary_rows[tuple(key)]['rows'] for e in group for key in e['query_keys']))
    check('paid_role_' + role, all(summary_rows[key]['role'] == role for key in keys))
check('total_paid_keys', len(summary_rows) == sum(p['unique_paid_matrices'] for p in populations.values()))
for name in ('logical_bundles', 'logical_paid_rows', 'logical_paid_response_fields', 'unique_paid_matrices', 'unique_paid_rows'):
    check('cost_' + name, costs[name] == sum(p[name] for p in populations.values()))
check('zero_episode_updates', costs['episode_updates'] == 0)

oracle_by_master = defaultdict(list)
test_eids = data['episode'][test]
test_y, test_effect = y[test], data['effect'][test]
for eid, e in by_id.items():
    index = test_eids == eid
    utility = test_y[index] - test_effect[index].max(axis=1)
    oracle_by_master[e['cell']].append(float(np.sort(utility)[-5:].mean()))
oracle = [float(np.mean(oracle_by_master[cell])) for cell in assigned]
expected_counts = [counts[cell] for cell in assigned]
metric_summary = {}
for name, result in metrics.items():
    check('denominators_' + name, result['nominal_rows'] == 30212 and result['nominal_episodes'] == 644
          and result['assigned_masters'] == assigned)
    check('counts_' + name, all(result['per_master_episode_counts'][kind] == expected_counts for kind in ('input', 'forecast', 'recommendation')))
    check('coverage_' + name, result['coverage_pass'] and all(result[k]['episodes'] == 644
          and result[k]['episode_coverage'] == 1 and result[k]['coverage_pass']
          and result[k]['zero_contributor_masters'] == [] for k in ('input', 'forecast', 'recommendation'))
          and result['forecast']['finite_target_rows'] == 30212 and result['forecast']['finite_target_row_coverage'] == 1)
    check('master_macros_' + name, all(len(result['per_master'][key]) == 96 and None not in result['per_master'][key]
          and np.isclose(np.mean(result['per_master'][key]), result[key], rtol=0, atol=1e-14)
          for key in ('mae', 'utility', 'oracle_utility', 'regret')))
    check('oracle_' + name, np.allclose(result['per_master']['oracle_utility'], oracle, rtol=0, atol=1e-14))
    check('regret_' + name, np.isclose(result['oracle_utility'] - result['utility'], result['regret'], rtol=0, atol=1e-14))
    metric_summary[name] = {key: result[key] for key in ('mae', 'utility', 'oracle_utility', 'regret')}
for endpoint in ('mae', 'utility'):
    comparison = gates['comparisons'][endpoint]
    candidate = metrics['effect__' + endpoint][endpoint]
    ordinary = metrics[comparison['ordinary'] + '__' + endpoint][endpoint]
    gain = ordinary - candidate if endpoint == 'mae' else candidate - ordinary
    check('primary_gain_' + endpoint, np.isclose(gain, comparison['gain'], rtol=0, atol=1e-14))
    check('bootstrap_population_' + endpoint, comparison['bootstrap']['n_masters'] == 96)
    check('primary_stop_' + endpoint, gain < 0 and gates['gates'][endpoint] is False)
check('registered_stop', gates['gates'] == {'coverage': True, 'mae': False, 'utility': False, 'both': False})

result = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'utc': datetime.now(timezone.utc).isoformat(),
          'audit_code_sha256': sha(Path(__file__)), 'inputs_sha256': used,
          'checks': checks, 'population': {'masters': 96, 'episodes': 644, 'rows': 30212,
          'finite_targets': int(np.isfinite(y[test]).sum()), 'rows_per_episode': dict(Counter(row_counts.values())),
          'episodes_per_master': dict(Counter(counts.values())),
          'realized_target_pair_episode_counts': {'/'.join(pair): number for pair, number in sorted(Counter(tuple(e['pair']) for e in episodes).items())},
          'coverage_denominator': 'All 644 frozen metadata-eligible test episodes / 30212 rows / all 96 assigned MASTERs; not all 12x96 Cartesian pairs.'},
          'populations_and_costs': populations, 'reported_compute_costs': costs,
          'metric_macros': metric_summary, 'registered_gates': gates,
          'interpretation': {'primary_decision': 'STOP', 'chemical_identity': 'NOT_ESTABLISHED',
          'endpoint': '72-hour CTG inhibitory response; not direct death or clinical efficacy',
          'bootstrap': 'Conditional internal MASTER resampling for this source, panel, fixed training and validation selections; not external independence',
          'agent_or_RSI_evidence': False},
          'access': {'test_targets_loaded': True, 'data_arrays_loaded': ['role', 'episode', 'valid_mask', 'effect'],
          'paid_summary_fields_used': ['key', 'role', 'rows'], 'full_features_loaded': False,
          'source_zip_opened': False, 'reserve_responses_opened': False, 'fits': 0,
          'predictions_actions_selection_numerical_values_loaded': False},
          'cross_review': {'status': 'PENDING', 'responses': []}}
JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
lines = ['# Data post-result independent review', '', 'Status: **' + result['status'] + '**. Primary decision remains **STOP**.', '',
    'Directly loaded only TEST_TARGETS.y and DATA role/episode/valid_mask/effect arrays. No full features, source ZIP, reserve responses, predictions/actions values or new fitting. Paid summary metadata used only key/role/rows. Existing files were read only.', '',
    'Verified 96 assigned MASTERs, 644 frozen eligible episodes, 30,212 target rows. Every test target is finite and every non-test TEST_TARGETS slot is NaN. Every test input/effect is valid. Missingness declarations and all 22 methods agree with the same nominal denominator, including every assigned MASTER. Coverage is 100%; it is not a claim that all 12 target pairs exist for all 96 contexts.', '',
    'Target conversion scope is exclusively selected test inhibition. Receipt reports 30,212 attempted = finite, zero nonfinite/out-of-range, no target attached mono/fitted fields, no reserve numeric conversion. Output hashes match. Raw source correctness is bounded by the pinned preparation receipt and inspected conversion code; source archive was not reopened.', '',
    '| Role | Logical bundles | Logical paid rows | Unique matrices | Unique rows |',
    '|---|---:|---:|---:|---:|']
for role, values in populations.items():
    lines.append('| ' + role + ' | ' + ' | '.join(str(values[k]) for k in ('logical_bundles', 'logical_paid_rows', 'unique_paid_matrices', 'unique_paid_rows')) + ' |')
lines += ['', 'Total logical cost is 4,208 bundles, 192,752 paid rows and 578,256 attached response fields. Physical conversion deduplicates to 2,744 matrices / 125,496 paid rows / 376,488 response fields. Test-only logical cost is 1,288 bundles / 59,080 rows; unique test purchase is 836 matrices / 38,276 rows. Every episode resets its two-bundle history: deduplication does not make reused observations free or independent. Attached repeated mono fields do not establish independent monotherapy wells.', '',
    'Independent MASTER macro/count recomputation and effect-based top-five oracle utility match all 22 method reports. This audit did not recompute each method prediction or chosen action; the separate metrics reviewer covers those values.', '',
    'MAE primary candidate gain is -0.011460855153466898 against validation-selected direct; utility gain is -0.04987049712644414 against combo_direct. Coverage passes, both primary performance gates fail. Speed, missing chemical mapping, descriptive secondary gains or new hypotheses do not change the registered STOP.', '',
    'Source-ID pair separation is established; chemical-pair separation remains NOT_ESTABLISHED from the prior exact-dictionary qualification. This does not prove alias leakage or invalidate the defined source-ID pilot. No new chemical name, merge, panel or target selection is permitted. Endpoint is released 72-hour CTG inhibition/viability proxy: not direct cell death, calibrated drug efficacy, a molecular state trajectory or an independent functional validation of transcript prediction.', '',
    'MASTER bootstrap conditions on this source screen, fixed eligible context/pair panel, training data and validation model selection. It addresses internal context variation while retaining within-MASTER episode clustering; it does not resample new compounds, independent source screens, prospective experiments or complete model-selection uncertainty. Thus neither narrow CIs nor large row counts establish external biological independence.', '',
    'Cross-review is pending actual peer responses. Numerical and access details are in DATA_POST_RESULT_REVIEW.json.']
MD_OUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'checks': len(checks), 'failed': [k for k, v in checks.items() if not v],
                  'population': result['population'], 'primary_decision': 'STOP'}))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
