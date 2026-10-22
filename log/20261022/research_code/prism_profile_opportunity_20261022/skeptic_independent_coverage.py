"""Independent counter-only audit; real response parsing requires a sealed freeze."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/prism_profile_opportunity'
MISSING = {'', 'NA', 'NaN', 'nan', 'NAN', 'null', 'NULL'}


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def finite(token):
    return False if token in MISSING else math.isfinite(float(token))


def coverage_ok(count, nominal):
    return 5 * count >= 4 * nominal


def count_permitted(source, manifest):
    """Count each allowed column/row; never store numeric response values."""
    ids = sorted(core for part in manifest['retained_ids'].values() for core in part)
    if len(ids) != len(set(ids)):
        raise ValueError('Retained parts overlap')
    records = {record['core']: record for record in manifest['records']}
    context_pool = {}
    for name, metadata in manifest['contexts'].items():
        if len(metadata['pool_ids']) != 1:
            raise ValueError('Context has ambiguous pool')
        context_pool[name] = metadata['pool_ids'][0]
    paid = set(manifest['paid_pools'])
    audit = set(manifest['audit_pools'])
    if paid & audit or set(context_pool.values()) != paid | audit:
        raise ValueError('Pool partition mismatch')
    nominal = {pool: sum(value == pool for value in context_pool.values())
               for pool in paid | audit}
    counters = {core: {rep: {pool: 0 for pool in (paid if rep == 'X1' else audit)}
                       for rep in ('X1', 'X2', 'X3')} for core in ids}
    visited, converted = set(), 0
    with source.open(encoding='utf-8-sig', newline='') as stream:
        rows = csv.reader(stream)
        header = next(rows)
        if len(header) != len(set(header)):
            raise ValueError('Duplicate response header')
        positions = {field: index for index, field in enumerate(header)}
        addresses = {core: {rep: positions[records[core]['replicate_columns'][rep]]
                            for rep in ('X1', 'X2', 'X3')} for core in ids}
        for row in rows:
            name = row[0]
            if name not in context_pool:
                continue
            if name in visited or len(row) != len(header):
                raise ValueError('Duplicate context or wrong row width')
            visited.add(name)
            pool = context_pool[name]
            permitted_reps = ('X1',) if pool in paid else ('X2', 'X3')
            for core in ids:
                for rep in permitted_reps:
                    counters[core][rep][pool] += int(finite(row[addresses[core][rep]]))
                    converted += 1
    if visited != set(context_pool):
        raise ValueError('Missing context rows')
    expected_slots = len(ids) * (sum(nominal[p] for p in paid)
                                 + 2 * sum(nominal[p] for p in audit))
    if converted != expected_slots:
        raise ValueError('Permitted conversion count mismatch')
    return counters, nominal, converted


def summarize(counters, nominal, manifest, converted):
    paid, audit = manifest['paid_pools'], manifest['audit_pools']
    audit_n = sum(nominal[pool] for pool in audit)
    details, qualified = {}, {part: [] for part in manifest['retained_ids']}
    for core in sorted(counters):
        counts = {'paid_' + pool: counters[core]['X1'][pool] for pool in paid}
        counts.update({'audit_' + rep: sum(counters[core][rep].values()) for rep in ('X2', 'X3')})
        eligible = (all(coverage_ok(counts['paid_' + pool], nominal[pool]) for pool in paid)
                    and all(coverage_ok(counts['audit_' + rep], audit_n) for rep in ('X2', 'X3')))
        details[core] = {'qualified': eligible, 'finite_counts': counts,
                         'finite_by_pool': counters[core]}
    for part, ids in manifest['retained_ids'].items():
        qualified[part] = sorted(core for core in ids if details[core]['qualified'])
    records = {record['core']: record for record in manifest['records']}
    plates = {plate: {'original': 0, 'qualified': 0}
              for plate in manifest['original_plate_assignment']['test']}
    for core in manifest['retained_ids']['test']:
        counts = plates[records[core]['compound_plate']]
        counts['original'] += 1
        counts['qualified'] += int(details[core]['qualified'])
    part_counts = {part: {'original_before_chemical_purge': manifest['original_counts'][part],
                          'fixed_after_purge': len(manifest['retained_ids'][part]),
                          'qualified': len(ids)} for part, ids in qualified.items()}
    test_n = manifest['original_counts']['test']
    if test_n != len(manifest['retained_ids']['test']):
        raise ValueError('Test candidate denominator changed')
    gates = {'source_at_least_300': len(qualified['source']) >= 300,
             'development_at_least_80': len(qualified['development']) >= 80,
             'test_retention_at_least_70_percent': 10 * len(qualified['test']) >= 7 * test_n,
             'six_test_plates_each_at_least_10': sum(item['qualified'] >= 10 for item in plates.values()) >= 6,
             'all_seven_test_plates_nonzero': len(plates) == 7 and all(item['qualified'] for item in plates.values())}
    passed = all(gates.values())
    return {'status': 'COVERAGE_PASS_ONLY' if passed else 'STOP_BULK_PROFILE_COVERAGE',
            'passed': passed, 'gates': gates, 'counts': part_counts,
            'test_plates': plates, 'qualified_ids': qualified, 'details': details,
            'test_minimum_at_70_percent': (7 * test_n + 9) // 10,
            'group_denominators': {**{'paid_' + pool: nominal[pool] for pool in paid},
                                   'audit_X2': audit_n, 'audit_X3': audit_n},
            'pool_denominators': nominal, 'total_converted_slots': converted,
            'total_finite': sum(sum(sum(pools.values()) for pools in reps.values())
                                for reps in counters.values())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', required=True)
    args = parser.parse_args()
    freeze_path = ROOT / args.freeze
    freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
    required = [Path(__file__).relative_to(ROOT).as_posix(),
                'log/20261022/prism_profile_opportunity/MANIFEST_v2.json']
    if any(name not in freeze['files'] for name in required):
        raise ValueError('Independent code or manifest is not frozen')
    for name, expected in freeze['files'].items():
        if digest(ROOT / name) != expected:
            raise ValueError('Freeze mismatch: ' + name)
    manifest = json.loads((LOG / 'MANIFEST_v2.json').read_text(encoding='utf-8'))
    source = ROOT / manifest['source']
    if digest(source) != manifest['source_sha256']:
        raise ValueError('Source checksum mismatch')
    counters, nominal, converted = count_permitted(source, manifest)
    result = summarize(counters, nominal, manifest, converted)
    result.update({'response_statistics_computed': False, 'new_fits': 0,
                   'source_sha256': digest(source), 'freeze_sha256': digest(freeze_path),
                   'independence_limit': 'Independent implementation after root code review; no root results read before sealing.',
                   'byte_contact': 'CSV tokens all columns; numeric conversion only retained permitted cells; saved counts only.'})
    output = LOG / 'skeptic/INDEPENDENT_COVERAGE_RESULT.json'
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: result[key] for key in ('status', 'gates', 'counts', 'total_converted_slots', 'total_finite')}))


if __name__ == '__main__':
    main()
