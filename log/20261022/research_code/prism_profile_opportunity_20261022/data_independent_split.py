"""Independent metadata-only split, pool-payload and coverage-denominator audit.

Does not import root experiment code or open any response matrix. Numerical
availability gates remain unexecuted until a separate protocol authorizes them.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/prism_profile_opportunity/data'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT / 'log/20261022/update_value_qualification/data/FIELD_CONTRACT.json'
EXPECTED_SOURCE = 'ff6d9d5417349c7553f597a42128c7350e146b4e99245fc6376218514967fe1b'
SEED = 'prism-profile-20261022-v1'
source_bytes = SOURCE.read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == EXPECTED_SOURCE
source = json.loads(source_bytes)
catalog = source['catalog']
assert len(catalog) == 1274
assert len({r['core'] for r in catalog}) == 1274
assert all(r['parent_resolution'] == 'RESOLVED' and len(r['nonisomeric_largest_fragment']) == len(r['murcko_scaffolds']) == 1 for r in catalog)


def hashed(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def keys(rows):
    return {('parent', r['nonisomeric_largest_fragment'][0]) for r in rows} | {
        ('scaffold', r['murcko_scaffolds'][0]) for r in rows}


def reasons(row, reference):
    result = []
    if ('parent', row['nonisomeric_largest_fragment'][0]) in reference:
        result.append('SAME_NONISOMERIC_PARENT')
    if ('scaffold', row['murcko_scaffolds'][0]) in reference:
        result.append('SAME_EXACT_MURCKO_INCLUDING_EMPTY')
    return result


plates = sorted({r['compound_plate'] for r in catalog}, key=lambda plate: (hashed(SEED + '|' + plate), plate))
assert len(plates) == len({hashed(SEED + '|' + plate) for plate in plates}) == 35
split_plates = {'test': plates[:7], 'dev': plates[7:14], 'source': plates[14:]}
raw = {label: sorted([r for r in catalog if r['compound_plate'] in selected], key=lambda r: r['core']) for label, selected in split_plates.items()}
test_keys = keys(raw['test'])
raw_dev_test_keys = keys(raw['dev'] + raw['test'])
kept = {'test': raw['test'],
        'dev': [r for r in raw['dev'] if not reasons(r, test_keys)],
        'source': [r for r in raw['source'] if not reasons(r, raw_dev_test_keys)]}
excluded = {'test': [],
    'dev': [{'core': r['core'], 'plate': r['compound_plate'], 'reason': reasons(r, test_keys)} for r in raw['dev'] if reasons(r, test_keys)],
    'source': [{'core': r['core'], 'plate': r['compound_plate'], 'reason': reasons(r, raw_dev_test_keys)} for r in raw['source'] if reasons(r, raw_dev_test_keys)]}
pairwise = {}
for a, b in [('source', 'dev'), ('source', 'test'), ('dev', 'test')]:
    overlaps = keys(kept[a]) & keys(kept[b])
    pairwise[a + '__' + b] = {'shared_parent_keys': sorted(v for k, v in overlaps if k == 'parent'),
                             'shared_scaffold_keys': sorted(v for k, v in overlaps if k == 'scaffold')}
    assert not overlaps
assert sum(map(len, raw.values())) == 1274
assert all(len(kept[k]) + len(excluded[k]) == len(raw[k]) for k in raw)
assert set(r['core'] for r in kept['source']).isdisjoint(r['core'] for r in raw['dev'] + raw['test'])

pool_rows = {pool: sorted(rows) for pool, rows in source['pool_rows'].items()}
pool_order = sorted(pool_rows, key=lambda pool: (hashed(SEED + '|pool|' + pool), pool))
paid = pool_order[:2]
unpaid = pool_order[2:]
assert len(paid) == 2 and len(unpaid) == 18
assert len({row for rows in pool_rows.values() for row in rows}) == sum(map(len, pool_rows.values())) == 481
paid_rows = sorted(row for p in paid for row in pool_rows[p])
unpaid_rows = sorted(row for p in unpaid for row in pool_rows[p])
assert set(paid_rows).isdisjoint(unpaid_rows)
assert len(paid_rows) + len(unpaid_rows) == 481

pool_catalog = [{'pool_id': p, 'rank': i + 1, 'sha256': hashed(SEED + '|pool|' + p),
                 'role': 'PAID_X1_SUPPORT' if p in paid else 'UNPAID_X2_X3_AUDIT',
                 'nominal_eligible_rows': len(pool_rows[p]), 'row_names': pool_rows[p],
                 'finite_threshold_if_each_pool_80_percent': math.ceil(0.8 * len(pool_rows[p]))}
                for i, p in enumerate(pool_order)]
cost = {'per_task': {
    'paid_support_pool_bundles_X1': 2,
    'paid_support_nominal_fields_X1': len(paid_rows),
    'audit_A_pool_bundles_X2': 18, 'audit_A_nominal_fields_X2': len(unpaid_rows),
    'audit_B_pool_bundles_X3': 18, 'audit_B_nominal_fields_X3': len(unpaid_rows),
    'planned_used_pool_bundles_total': 38,
    'planned_used_nominal_fields_total': len(paid_rows) + 2 * len(unpaid_rows),
    'full_profile_column_pool_bundles': 20, 'full_profile_column_nominal_fields': 481,
    'all_three_full_columns_pool_bundles': 60, 'all_three_full_columns_nominal_fields': 1443},
    'limits': 'Catalog slots/bundle counts only. Whole-profile column is twenty pool bundles; physical controls, stock, all attempts, monetary cost and independently purchasable preprocessed pools are not authenticated.'}
split_summary = {}
for label in ('source', 'dev', 'test'):
    counts = Counter(r['compound_plate'] for r in kept[label])
    split_summary[label] = {'plates': split_plates[label], 'raw_tasks': len(raw[label]), 'kept_tasks': len(kept[label]),
        'purged_tasks': len(excluded[label]), 'kept_by_plate': {p: counts[p] for p in split_plates[label]},
        'kept_empty_scaffold': sum(r['murcko_scaffolds'][0] == '' for r in kept[label]),
        'nominal_cost_all_kept_tasks': {key: value * len(kept[label]) for key, value in cost['per_task'].items()}}
result = {'status': 'METADATA_ONLY_INDEPENDENT_AUDIT_NOT_RESPONSE_QUALIFICATION',
    'utc': datetime.now(timezone.utc).isoformat(), 'seed': SEED,
    'input': {'path': str(SOURCE.relative_to(ROOT)), 'sha256': EXPECTED_SOURCE},
    'root_experiment_code_imported': False, 'response_matrix_opened': False, 'response_values_converted': 0,
    'external_GETs': 0, 'model_fits': 0,
    'ordering_rule': "SHA256 UTF-8(seed+'|'+plate), ascending hex; first7 test/next7 dev/remaining21 source",
    'pool_ordering_rule': "SHA256 UTF-8(seed+'|pool|'+pool), ascending hex; first2 paid",
    'plate_order': [{'rank': i + 1, 'plate': p, 'sha256': hashed(SEED + '|' + p)} for i, p in enumerate(plates)],
    'purge_rules': {'test': 'Retain all raw test tasks',
        'dev': 'Purge any exact nonisomeric-parent OR exact Murcko (including empty) match to raw test',
        'source': 'Purge any exact nonisomeric-parent OR exact Murcko (including empty) match to ORIGINAL raw dev OR raw test, even if dev was later purged'},
    'summary': split_summary, 'pairwise_key_overlap_after_purge': pairwise, 'excluded': excluded,
    'catalog_by_split': {label: rows for label, rows in kept.items()},
    'paid_pool_ids': paid, 'unpaid_pool_ids': unpaid, 'pool_catalog': pool_catalog,
    'paid_row_names': paid_rows, 'unpaid_row_names': unpaid_rows, 'cost': cost,
    'coverage_gates_unexecuted': {
        'paid_each_pool_X1_minimum_finite': {p: math.ceil(0.8 * len(pool_rows[p])) for p in paid},
        'unpaid_X2_each_80_percent_possible_aggregate_threshold': math.ceil(0.8 * len(unpaid_rows)),
        'unpaid_X3_each_80_percent_possible_aggregate_threshold': math.ceil(0.8 * len(unpaid_rows)),
        'unpaid_each_pool_thresholds_if_protocol_chooses_stricter_interpretation': {p: math.ceil(0.8 * len(pool_rows[p])) for p in unpaid},
        'audit_aggregate_versus_each_pool_rule': 'PENDING formal protocol; do not choose based on response values',
        'test_tasks_70_percent_original_test_minimum': math.ceil(0.7 * len(raw['test'])),
        'minimum_test_plates_with_at_least10_qualified_tasks': 6,
        'original_test_plates': len(split_plates['test']),
        'source_dev_training_size_minima': 'PENDING formal protocol',
        'actual_finite_coverage_and_retention': 'UNREAD / NOT_EXECUTED'},
    'interpretation': ['Exact parent/scaffold separation is verified; this is not proof of independent chemistry/plates/assays.',
        'Task axis is later compound profile. Same fixed pool/cell panel; unpaid pools do not establish new-cell-context transfer.',
        'Shared treatment-level ComBat/control processing creates transductive support/audit dependencies.',
        'Historically exposed same release; locked replay remains development, not fresh biological confirmation.']}
out = OUT / 'INDEPENDENT_SPLIT.json'
assert not out.exists(), 'Do not overwrite independent first metadata result'
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'split': split_summary, 'paid_pools': paid, 'paid_rows': len(paid_rows), 'audit_rows': len(unpaid_rows),
    'test_retention_min': result['coverage_gates_unexecuted']['test_tasks_70_percent_original_test_minimum'],
    'cost_per_task': cost['per_task']}))
