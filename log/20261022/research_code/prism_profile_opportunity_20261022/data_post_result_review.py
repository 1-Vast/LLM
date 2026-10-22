"""Independent post-result recomputation from saved boolean mask only.

Never opens the raw response matrix; never imports the root converter/scorer.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/prism_profile_opportunity'
OUT = LOG / 'data'
checks = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, condition):
    checks.append({'name': name, 'pass': bool(condition)})
    if not condition:
        raise AssertionError(name)


def load(name):
    return json.loads((LOG / name).read_text(encoding='utf-8'))


freeze = load('COVERAGE_FREEZE.json')
for name, digest in freeze['files'].items():
    check('Frozen file unchanged ' + name, sha(ROOT / name) == digest)
mine = load('data/INDEPENDENT_SPLIT.json')
manifest = load('MANIFEST_v2.json')
result = load('COVERAGE_RESULT.json')
description = load('MASK_DESCRIPTION.json')
execution = load('COVERAGE_EXECUTION_01.json')
check('Original independent calculation sealed', sha(OUT / 'INDEPENDENT_SPLIT.json') == 'aedf9670e8b9e7f9771c9916a6fd7247e17af24107ca23a415f36f7ffc9b44e0')
check('One successful real execution receipt', execution['exit_code'] == 0)
check('Exactly one numbered root execution', len(list(LOG.glob('COVERAGE_EXECUTION_*.json'))) == 1)
check('Result binds frozen manifest', result['manifest_sha256'] == sha(LOG / 'MANIFEST_v2.json'))
check('Same source identity string', result['source_sha256'] == manifest['source_sha256'] == '59fab6f8126cfc57d84a59e11cb67add1c7850da72cc3df6f4f9d6ef0c1808e7')
check('Result binds existing mask bytes', result['finite_mask_sha256'] == sha(LOG / 'FINITE_MASK.npz'))
check('Description binds root result', description['source_result_sha256'] == sha(LOG / 'COVERAGE_RESULT.json'))
with np.load(LOG / 'FINITE_MASK.npz', allow_pickle=False) as artifact:
    check('Only bool and address arrays saved', set(artifact.files) == {'finite', 'ids', 'slots'})
    finite = artifact['finite']
    ids_array = artifact['ids']
    slots_array = artifact['slots']
    check('Only finite mask has numerical/bool dtype', finite.dtype == np.dtype(bool))
    check('ID array is Unicode, not labels', ids_array.dtype.kind == 'U')
    check('Slot array is Unicode, not labels', slots_array.dtype.kind == 'U')
ids = ids_array.tolist()
slots = [json.loads(text) for text in slots_array.tolist()]
mapping = {'source': 'source', 'dev': 'development', 'test': 'test'}
expected_ids = sorted(r['core'] for records in mine['catalog_by_split'].values() for r in records)
check('All1031 independently retained IDs in exact order', ids == expected_ids and len(ids) == len(set(ids)) == 1031)
contexts = manifest['contexts']
expected_slots = [{'replicate': rep, 'row_name': row, 'pool': contexts[row]['pool_ids'][0]}
                  for rep in ('X1', 'X2', 'X3') for row in sorted(contexts)
                  if (contexts[row]['pool_ids'][0] in mine['paid_pool_ids']) == (rep == 'X1')]
check('All914 slots have independent exact addresses', slots == expected_slots and len(slots) == 914)
check('Mask shape1031x914', finite.shape == (len(ids), len(slots)))
check('No duplicate address slots', len({tuple(sorted(s.items())) for s in slots}) == 914)
check('No unpaidX1/paidX2X3 fields', all((s['replicate'] == 'X1') == (s['pool'] in mine['paid_pool_ids']) for s in slots))
groups = {'paid_' + p: [j for j, s in enumerate(slots) if s['replicate'] == 'X1' and s['pool'] == p] for p in mine['paid_pool_ids']}
groups.update({'audit_' + rep: [j for j, s in enumerate(slots) if s['replicate'] == rep] for rep in ('X2', 'X3')})
denominators = {key: len(indices) for key, indices in groups.items()}
check('Exact frozen denominators', denominators == result['group_denominators'] == {'paid_P933': 23, 'paid_P904': 25, 'audit_X2': 433, 'audit_X3': 433})
counts = {key: finite[:, columns].sum(axis=1).astype(int) for key, columns in groups.items()}
passing = np.logical_and.reduce([5 * values >= 4 * denominators[key] for key, values in counts.items()])
id_index = {core: i for i, core in enumerate(ids)}
root_details = {d['core']: d for d in result['details']}
check('All details present exactly once', len(root_details) == len(result['details']) == len(ids) and set(root_details) == set(ids))
pool_groups = {(rep, pool): [j for j, s in enumerate(slots) if s['replicate'] == rep and s['pool'] == pool]
               for rep in ('X1', 'X2', 'X3')
               for pool in (mine['paid_pool_ids'] if rep == 'X1' else mine['unpaid_pool_ids'])}
pool_counts = {key: finite[:, columns].sum(axis=1).astype(int) for key, columns in pool_groups.items()}
for i, core in enumerate(ids):
    check(core + ' qualification agrees', root_details[core]['qualified'] == bool(passing[i]))
    check(core + ' requirement finite counts agree', root_details[core]['finite_counts'] == {k: int(v[i]) for k, v in counts.items()})
    for (rep, pool), values in pool_counts.items():
        check(core + ' ' + rep + '/' + pool + ' finite count', root_details[core]['finite_by_pool'][rep][pool] == int(values[i]))

parts = {}
qualified_ids = {}
cost_by_part = {}
for own, label in mapping.items():
    cores = [r['core'] for r in mine['catalog_by_split'][own]]
    indices = [id_index[c] for c in cores]
    selected = sorted(c for c in cores if passing[id_index[c]])
    qualified_ids[label] = selected
    check(label + ' qualified identities agree', selected == result['qualified_ids'][label])
    original = mine['summary'][own]['raw_tasks']
    check(label + ' counts all denominators agree', result['counts'][label] == {'original_before_chemical_purge': original, 'fixed_after_purge': len(cores), 'qualified': len(selected)})
    passes = {name: sum(5 * int(values[i]) >= 4 * denominators[name] for i in indices) for name, values in counts.items()}
    fractions = {name: sum(int(values[i]) for i in indices) / (len(indices) * denominators[name]) for name, values in counts.items()}
    zero_pool = {rep: sum(any(int(pool_counts[(rep, pool)][i]) == 0 for pool in mine['unpaid_pool_ids']) for i in indices) for rep in ('X2', 'X3')}
    parts[label] = {'original_before_purge': original, 'fixed_after_purge': len(cores), 'qualified': len(selected),
        'qualification_fraction_fixed': len(selected) / len(cores), 'per_requirement_passes': passes,
        'finite_fraction_by_requirement': fractions, 'compounds_with_any_zero_audit_pool': zero_pool}
    check(label + ' description per-requirement passes', passes == description['parts'][label]['per_requirement_passes'])
    check(label + ' description zero-pool counts', zero_pool == description['parts'][label]['compounds_with_any_zero_audit_pool'])
    check(label + ' description fractions', fractions == description['parts'][label]['finite_fraction_by_requirement'])
    for rep in ('X1', 'X2', 'X3'):
        for pool in (mine['paid_pool_ids'] if rep == 'X1' else mine['unpaid_pool_ids']):
            expected = {'finite': sum(int(pool_counts[(rep, pool)][i]) for i in indices), 'nominal': len(indices) * len(pool_groups[(rep, pool)])}
            check(label + ' per-pool aggregate ' + rep + '/' + pool, result['per_pool'][label][rep][pool] == expected)
    cost_by_part[label] = {'all_attempted_compounds': len(cores), 'qualified_only_compounds_not_cost_denominator': len(selected),
        'support_bundle_accesses': 2 * len(cores), 'audit_bundle_accesses': 36 * len(cores),
        'total_bundle_accesses': 38 * len(cores), 'nominal_boolean_slots': 914 * len(cores)}
records = {r['core']: r for r in manifest['records']}
plate_counts = {}
for plate in mine['summary']['test']['plates']:
    original = sum(r['compound_plate'] == plate for r in mine['catalog_by_split']['test'])
    selected = sum(records[c]['compound_plate'] == plate for c in qualified_ids['test'])
    plate_counts[plate] = {'original': original, 'qualified': selected}
check('All seven original test plates exact', plate_counts == result['test_plates'] == description['test_plates'])
test_original = mine['summary']['test']['raw_tasks']
gates = {'source_at_least_300': len(qualified_ids['source']) >= 300,
    'development_at_least_80': len(qualified_ids['development']) >= 80,
    'test_retention_at_least_70_percent': 10 * len(qualified_ids['test']) >= 7 * test_original,
    'six_test_plates_each_at_least_10': sum(v['qualified'] >= 10 for v in plate_counts.values()) >= 6,
    'all_seven_test_plates_nonzero': all(v['qualified'] >= 1 for v in plate_counts.values())}
check('All five independently recomputed gates match', gates == result['gates'])
check('Decisive gate status matches', result['passed'] == all(gates.values()) and result['status'] == ('COVERAGE_PASS_ONLY' if all(gates.values()) else 'STOP_BULK_PROFILE_COVERAGE'))
check('Minimum179 uses original255', result['test_minimum_at_70_percent'] == (7 * test_original + 9) // 10 == 179)
check('All finite and conversion totals', result['total_finite'] == int(finite.sum()) and result['total_converted_slots'] == finite.size == 942334)
check('All attempted cost denominator matches description', description['logical_bundle_accesses_per_execution'] == sum(v['total_bundle_accesses'] for v in cost_by_part.values()) == 39178)
check('All attempted slot denominator matches description', description['numeric_to_bool_conversions_per_execution'] == finite.size)
check('No root response statistics or fits', result['response_statistics_computed'] is False and result['new_fits'] == 0)
report = {'status': 'PASS_INDEPENDENT_BOOL_AUDIT_SUPPORTS_STOP' if not all(gates.values()) else 'PASS_INDEPENDENT_BOOL_AUDIT_COVERAGE_ONLY',
    'utc': datetime.now(timezone.utc).isoformat(), 'checks': len(checks), 'detail': checks,
    'inputs': {str(p.relative_to(ROOT)): sha(p) for p in [LOG / 'COVERAGE_RESULT.json', LOG / 'MASK_DESCRIPTION.json', LOG / 'FINITE_MASK.npz', LOG / 'MANIFEST_v2.json', LOG / 'COVERAGE_FREEZE.json', OUT / 'INDEPENDENT_SPLIT.json']},
    'artifact_schema': {'keys': ['finite', 'ids', 'slots'], 'mask_dtype': str(finite.dtype), 'mask_shape': list(finite.shape), 'ids_dtype': str(ids_array.dtype), 'slots_dtype': str(slots_array.dtype)},
    'parts': parts, 'test_plates': plate_counts, 'gates': gates, 'cost_by_part': cost_by_part,
    'total_finite_slots': int(finite.sum()), 'total_nominal_slots': int(finite.size),
    'raw_response_matrix_reads': 0, 'new_response_numeric_conversions': 0, 'new_GETs': 0, 'model_fits': 0,
    'scope': 'Saved bool-mask/IDs/slots and frozen metadata only; no re-read or caching of real-valued responses.',
    'decision_limit': 'STOP this exact fixed two-pool bulk-panel availability configuration; no model/world/agent/RSI performance tested; no alternate-pool rescue.'}
path = OUT / 'POST_RESULT_VERIFICATION.json'
assert not path.exists()
path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'checks': report['checks'], 'parts': {k: {'qualified': v['qualified'], 'fixed': v['fixed_after_purge'], 'per_requirement_passes': v['per_requirement_passes']} for k, v in parts.items()}, 'gates': gates, 'total_finite': report['total_finite_slots']}))
