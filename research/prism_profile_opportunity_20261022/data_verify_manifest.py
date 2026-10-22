"""Compare root metadata manifest with independently sealed split; no root imports/response reads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

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


independent_path = OUT / 'INDEPENDENT_SPLIT.json'
check('Independent metadata result immutable', sha(independent_path) == 'aedf9670e8b9e7f9771c9916a6fd7247e17af24107ca23a415f36f7ffc9b44e0')
check('Independent first draft immutable', sha(OUT / 'INDEPENDENT.md') == '301a3a20ba7497f045f4c6c0fb51fb82e3dc5867503e792a6027ca5c25c6031f')
mine = json.loads(independent_path.read_text(encoding='utf-8'))
manifest_path = LOG / 'MANIFEST_v2.json'
theirs = json.loads(manifest_path.read_text(encoding='utf-8'))
first = json.loads((LOG / 'MANIFEST.json').read_text(encoding='utf-8'))
archived = json.loads((ROOT / mine['input']['path']).read_text(encoding='utf-8'))
check('Manifest seed exactly matches', theirs['seed'] == mine['seed'])
check('Same source hash', theirs['source_sha256'] == archived['source_sha256'])
check('Same481 context metadata', theirs['contexts'] == archived['eligible_contexts'])
check('All1274 resolved/header-complete records identical', sorted(theirs['records'], key=lambda r: r['core']) == sorted(archived['catalog'], key=lambda r: r['core']))
check('No duplicate root record core IDs', len({r['core'] for r in theirs['records']}) == len(theirs['records']))
check('Exact paid pools/order', theirs['paid_pools'] == mine['paid_pool_ids'])
check('Exact unpaid pool membership', set(theirs['audit_pools']) == set(mine['unpaid_pool_ids']))
check('No paid/audit pool overlap', set(theirs['paid_pools']).isdisjoint(theirs['audit_pools']))
mapping = {'source': 'source', 'dev': 'development', 'test': 'test'}
for label, other_label in mapping.items():
    expected_ids = sorted(r['core'] for r in mine['catalog_by_split'][label])
    check('Exact plate assignment ' + label, theirs['original_plate_assignment'][other_label] == mine['summary'][label]['plates'])
    check('Original denominator ' + label, theirs['original_counts'][other_label] == mine['summary'][label]['raw_tasks'])
    check('Retained count ' + label, theirs['retained_counts'][other_label] == len(expected_ids))
    check('Exact retained compound identities ' + label, theirs['retained_ids'][other_label] == expected_ids)
    check('Exact purged identities ' + label, theirs['purged_ids'][other_label] == sorted(r['core'] for r in mine['excluded'][label]))
for name in ('original_plate_assignment', 'paid_pools', 'audit_pools', 'contexts', 'records', 'retained_ids', 'purged_ids', 'original_counts', 'retained_counts'):
    check('v1/v2 design unchanged ' + name, first[name] == theirs[name])
check('v2 requires all7 nonzero', theirs['coverage_rule']['all_seven_test_plates_must_have_a_qualified_compound'] is True)
check('Original6of7 threshold retained', theirs['coverage_rule']['test_plates_with_at_least_10_qualified_compounds'] == 6)
check('Source/dev minima', theirs['source_minimum_qualified'] == 300 and theirs['development_minimum_qualified'] == 80)
check('Paid pool threshold80%', theirs['coverage_rule']['each_paid_pool_X1_finite_fraction_at_least'] == 0.8)
check('Audit panel threshold80%', theirs['coverage_rule']['each_unpaid_panel_X2_X3_finite_fraction_at_least'] == 0.8)
check('Test original retention70%', theirs['coverage_rule']['test_compound_retention_fraction_at_least'] == 0.7)
check('Prior metadata binding', theirs['metadata_sha256'] == sha(ROOT / 'log/20261022/update_value_qualification/data/PRISM_METADATA_QUALIFICATION.json'))
check('Prior geometry binding', theirs['geometry_sha256'] == sha(ROOT / 'log/20261022/update_value_qualification/data/MANIFEST_GEOMETRY.json'))
retained_ids = [r for ids in theirs['retained_ids'].values() for r in ids]
check('Retained IDs partition1031', len(retained_ids) == len(set(retained_ids)) == sum(v['kept_tasks'] for v in mine['summary'].values()))
slots = [(rep, name, info['pool_ids'][0]) for rep in ('X1', 'X2', 'X3')
         for name, info in sorted(theirs['contexts'].items())
         if (info['pool_ids'][0] in theirs['paid_pools']) == (rep == 'X1')]
check('Exactly914 allowed per-task slots', len(slots) == mine['cost']['per_task']['planned_used_nominal_fields_total'] == 914)
check('No duplicate allowed slots', len(set(slots)) == len(slots))
check('48 paidX1 addresses', sum(rep == 'X1' for rep, _, _ in slots) == len(mine['paid_row_names']) == 48)
for rep in ('X2', 'X3'):
    check(rep + '433 unpaid addresses', sum(r == rep for r, _, _ in slots) == len(mine['unpaid_row_names']) == 433)
check('No unpaidX1 or paidX2/X3 allowed', all((rep == 'X1') == (pool in theirs['paid_pools']) for rep, _, pool in slots))
check('Whole profile remains20pool bundles', mine['cost']['per_task']['full_profile_column_pool_bundles'] == 20)
protocol = LOG / 'PROTOCOL.md'
code_paths = [ROOT / 'research/prism_profile_opportunity_20261022' / name for name in ('prepare.py', 'coverage.py')]
result = {'status': 'METADATA_MANIFEST_MATCH', 'checks': len(checks), 'detail': checks,
    'utc': datetime.now(timezone.utc).isoformat(),
    'bindings': {str(p.relative_to(ROOT)): sha(p) for p in [independent_path, OUT / 'INDEPENDENT.md', LOG / 'MANIFEST.json', manifest_path, protocol] + code_paths},
    'permitted_conversion_slots': len(retained_ids) * len(slots),
    'permitted_conversion_units': len(retained_ids) * mine['cost']['per_task']['planned_used_pool_bundles_total'],
    'response_values_or_masks_read': False, 'root_code_imported': False,
    'qualification_result': 'NOT_RECOMPUTED; this verifies metadata/addresses only',
    'clarifications': ['Original independent JSON unpaid80% ambiguity resolved before numerics as per-replicate aggregate433, not per-pool.',
        'v2 all7 nonzero gate is a pre-numerical review amendment; design identities unchanged.',
        'Per-compound/pool coverage should be descriptive detail, not a new acceptance threshold.',
        'Future model input must not silently consume unpaid X2/X3 finite masks as extra target feedback.']}
path = OUT / 'MANIFEST_COMPARISON.json'
assert not path.exists()
path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: result[k] for k in ('status', 'checks', 'permitted_conversion_slots', 'permitted_conversion_units')}))
