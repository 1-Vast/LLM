"""Mask-only coverage, with exact fixed denominators and no response cache."""
import csv
import json
import math
from collections import Counter

import numpy as np

from prepare import LOG, ROOT, sha, write


MISSING = {'', 'NA', 'NaN', 'nan', 'NAN', 'null', 'NULL'}


def finite_token(token):
    if token in MISSING:
        return False
    return math.isfinite(float(token))


def at_least_four_fifths(count, denominator):
    return 5 * count >= 4 * denominator


def slots_for(manifest):
    contexts = manifest['contexts']
    return [{'replicate': rep, 'row_name': name, 'pool': contexts[name]['pool_ids'][0]}
            for rep in ('X1', 'X2', 'X3') for name in sorted(contexts)
            if (contexts[name]['pool_ids'][0] in manifest['paid_pools']) == (rep == 'X1')]


def summarize(mask, ids, slots, manifest):
    slot_groups = {'paid_' + pool: [i for i, s in enumerate(slots) if s['replicate'] == 'X1' and s['pool'] == pool]
                   for pool in manifest['paid_pools']}
    slot_groups.update({'audit_' + rep: [i for i, s in enumerate(slots) if s['replicate'] == rep]
                        for rep in ('X2', 'X3')})
    counts = {name: mask[:, indices].sum(axis=1) for name, indices in slot_groups.items()}
    qualifies = np.ones(len(ids), dtype=bool)
    for name, indices in slot_groups.items():
        qualifies &= at_least_four_fifths(counts[name], len(indices))
    id_index = {core: i for i, core in enumerate(ids)}
    records = {r['core']: r for r in manifest['records']}
    part_counts, qualified_ids = {}, {}
    for part, part_ids in manifest['retained_ids'].items():
        selected = [core for core in part_ids if qualifies[id_index[core]]]
        qualified_ids[part] = selected
        part_counts[part] = {'original_before_chemical_purge': manifest['original_counts'][part],
                            'fixed_after_purge': len(part_ids), 'qualified': len(selected)}
    plates = manifest['original_plate_assignment']['test']
    qualified_by_plate = Counter(records[core]['compound_plate'] for core in qualified_ids['test'])
    plate_counts = {plate: {'original': sum(records[core]['compound_plate'] == plate for core in manifest['retained_ids']['test']),
                            'qualified': qualified_by_plate[plate]} for plate in plates}
    test_n = len(manifest['retained_ids']['test'])
    gates = {'source_at_least_300': part_counts['source']['qualified'] >= 300,
             'development_at_least_80': part_counts['development']['qualified'] >= 80,
             'test_retention_at_least_70_percent': 10 * part_counts['test']['qualified'] >= 7 * test_n,
             'six_test_plates_each_at_least_10': sum(v['qualified'] >= 10 for v in plate_counts.values()) >= 6,
             'all_seven_test_plates_nonzero': all(v['qualified'] > 0 for v in plate_counts.values())}
    pool_groups = {rep: {pool: [j for j, s in enumerate(slots) if s['replicate'] == rep and s['pool'] == pool]
                        for pool in (manifest['paid_pools'] if rep == 'X1' else manifest['audit_pools'])}
                   for rep in ('X1', 'X2', 'X3')}
    pool_counts = {rep: {pool: mask[:, indices].sum(axis=1) for pool, indices in groups.items()}
                   for rep, groups in pool_groups.items()}
    details = [{'core': core, 'qualified': bool(qualifies[i]),
                'finite_counts': {name: int(values[i]) for name, values in counts.items()},
                'finite_by_pool': {rep: {pool: int(values[i]) for pool, values in groups.items()}
                                   for rep, groups in pool_counts.items()}}
               for i, core in enumerate(ids)]
    per_pool = {}
    for part, part_ids in manifest['retained_ids'].items():
        indices = [id_index[core] for core in part_ids]
        per_pool[part] = {rep: {pool: {'finite': int(mask[np.ix_(indices, [j for j, s in enumerate(slots)
                                               if s['replicate'] == rep and s['pool'] == pool])].sum()),
                                     'nominal': len(indices) * sum(s['replicate'] == rep and s['pool'] == pool for s in slots)}
                                  for pool in (manifest['paid_pools'] if rep == 'X1' else manifest['audit_pools'])}
                         for rep in ('X1', 'X2', 'X3')}
    return {'passed': all(gates.values()), 'gates': gates, 'counts': part_counts,
            'test_minimum_at_70_percent': (7 * test_n + 9) // 10,
            'test_plates': plate_counts, 'qualified_ids': qualified_ids,
            'group_denominators': {name: len(indices) for name, indices in slot_groups.items()},
            'pool_denominators': {rep: {pool: len(indices) for pool, indices in groups.items()}
                                  for rep, groups in pool_groups.items()},
            'details': details, 'per_pool': per_pool,
            'total_finite': int(mask.sum()), 'total_converted_slots': int(mask.size)}


def read_mask(path, manifest):
    ids = sorted(core for values in manifest['retained_ids'].values() for core in values)
    id_index = {core: i for i, core in enumerate(ids)}
    record = {r['core']: r for r in manifest['records']}
    slots = slots_for(manifest)
    mask = np.zeros((len(ids), len(slots)), dtype=bool)
    seen = set()
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream)
        header = next(reader)
        column_index = {name: i for i, name in enumerate(header)}
        assert len(column_index) == len(header)
        addresses = {rep: [(id_index[core], column_index[record[core]['replicate_columns'][rep]]) for core in ids]
                     for rep in ('X1', 'X2', 'X3')}
        slots_by_row = {}
        for index, slot in enumerate(slots):
            slots_by_row.setdefault(slot['row_name'], []).append((index, slot['replicate']))
        for row in reader:
            if row[0] not in slots_by_row:
                continue
            assert row[0] not in seen and len(row) == len(header)
            seen.add(row[0])
            for slot_index, rep in slots_by_row[row[0]]:
                for compound_index, response_column in addresses[rep]:
                    mask[compound_index, slot_index] = finite_token(row[response_column])
    assert seen == set(manifest['contexts'])
    return mask, ids, slots


def main():
    freeze = json.loads((LOG / 'COVERAGE_FREEZE.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT / name) == expected for name, expected in freeze['files'].items())
    manifest = json.loads((LOG / 'MANIFEST_v2.json').read_text(encoding='utf-8'))
    source = ROOT / manifest['source']
    assert sha(source) == manifest['source_sha256']
    mask, ids, slots = read_mask(source, manifest)
    result = summarize(mask, ids, slots, manifest)
    result.update({'status': 'COVERAGE_PASS_ONLY' if result['passed'] else 'STOP_BULK_PROFILE_COVERAGE',
                   'manifest_sha256': sha(LOG / 'MANIFEST_v2.json'), 'source_sha256': sha(source),
                   'response_statistics_computed': False, 'new_fits': 0,
                   'byte_contact': 'CSV rows tokenize all columns; float conversion only fixed retained permitted slots.',
                   'inference': 'Exposed conditional released-catalog feasibility only; no independent N or performance claim.'})
    mask_path = LOG / 'FINITE_MASK.npz'
    with mask_path.open('xb') as stream:
        np.savez_compressed(stream, finite=mask, ids=np.asarray(ids),
                            slots=np.asarray([json.dumps(s, sort_keys=True) for s in slots]))
    result['finite_mask_sha256'] = sha(mask_path)
    write(LOG / 'COVERAGE_RESULT.json', result)
    print(json.dumps({k: result[k] for k in ('status', 'passed', 'gates', 'counts', 'total_converted_slots', 'total_finite')}))


if __name__ == '__main__':
    main()
