"""Exact diagnostic exposure: L72 all; T72/D72 only on invalid L72 rows."""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'log/20261022/dead_stock_information_gate'
OUT = BASE / 'data_auditor/target_failure_audit'
DATA = ROOT / 'log/20261022/functional_dynamics_gate/root_scout/hct116_dose_response_fresh_object.body'
EXPECTED = '7ec7b019690f09f833a81bd4a98ec47e39df32ac249c767714a7e2d817a39c92'
LIVE, TOTAL, DEAD = 'intersect_live_cells', 'tot_cells', 'intersect_dead_cells'
PROTECTED = [DATA, BASE / 'TARGET_FAILURE_AUDIT_PROTOCOL.md', BASE / 'HCT116_GATE_PROTOCOL.md',
             ROOT / 'research/dead_stock_information_gate_20261022/hct_gate.py',
             BASE / 'hct_gate/PRE_RESPONSE_FREEZE.json', BASE / 'hct_gate/PREFIX_ONLY_KINETIC_CACHE.json',
             BASE / 'RUN.txt', BASE / 'hct_gate/FAILURE.txt']


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)


def parse_observed(raw):
    if raw is None or not raw.strip():
        return {'classification': 'missing_empty', 'raw_literal': raw, 'finite_value': None}
    try:
        value = float(raw)
    except (ValueError, TypeError, OverflowError):
        return {'classification': 'malformed', 'raw_literal': raw, 'finite_value': None}
    if not math.isfinite(value):
        return {'classification': 'nonfinite', 'raw_literal': raw, 'finite_value': None}
    return {'classification': 'negative' if value < 0 else 'valid_nonnegative',
            'raw_literal': raw, 'finite_value': value}


def live_pass(records, target_rows):
    result = {}
    for row_number, row in records:
        if row_number not in target_rows:
            continue
        result[row_number] = {**target_rows[row_number], 'source_row': row_number,
                              'observed_live': parse_observed(row[LIVE])}
    if result.keys() != target_rows.keys():
        raise ValueError('target_rows_not_all_present')
    return result


def relation_pass(records, invalid_live):
    result = {}
    for row_number, row in records:
        if row_number not in invalid_live:
            continue
        total, dead = parse_observed(row[TOTAL]), parse_observed(row[DEAD])
        live = invalid_live[row_number]['observed_live']
        arithmetic = {'finite_operands': all(item['finite_value'] is not None for item in [live, total, dead])}
        if arithmetic['finite_operands']:
            try:
                l, t, d = (Decimal(item['raw_literal'].strip()) for item in [live, total, dead])
            except InvalidOperation:
                raise ValueError('float_decimal_parse_disagreement')
            arithmetic.update({'total_minus_dead': str(t-d), 'total_minus_dead_minus_live': str(t-d-l),
                               'live_plus_dead_equals_total_exact': l+d == t,
                               'dead_exceeds_total': d > t,
                               'total_and_dead_nonnegative': t >= 0 and d >= 0})
        result[row_number] = {'source_row': row_number, 'observed_total': total,
                              'observed_dead': dead, 'arithmetic': arithmetic}
    if result.keys() != invalid_live.keys():
        raise ValueError('invalid_relation_rows_not_all_present')
    return result


def csv_records(path):
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield reader.line_num, row


def identities():
    frozen = json.loads((BASE / 'hct_gate/PRE_RESPONSE_FREEZE.json').read_text(encoding='utf-8'))
    expected_keys = {tuple(key) for key in frozen['keys']}
    frames, origins = {}, {}
    for source_row, row in csv_records(DATA):
        concentration = format(float(row['concentration']), 'g')
        key = (concentration, row['seed'], row['well'])
        elapsed = float(row['Elapsed'])
        if key not in expected_keys or not math.isfinite(elapsed):
            raise ValueError('unexpected_identity')
        identity = (key, elapsed, row['img'])
        if identity in frames:
            raise ValueError('duplicate_identity')
        frames[identity] = {'source_row': source_row, 'key': list(key), 'img': row['img'],
                            'Elapsed_literal': row['Elapsed'], 'Date_Time_literal': row['Date Time']}
        origins[key] = min(origins.get(key, elapsed), elapsed)
    if set(origins) != expected_keys:
        raise ValueError('expected_wells_missing')
    selected, panels = {}, defaultdict(set)
    for (key, elapsed, img), record in frames.items():
        if elapsed - origins[key] == 72:
            selected[record['source_row']] = {**record, 'relative_time': 72,
                                             'origin_Elapsed': origins[key]}
            panels[key].add(img)
    if set(panels) != expected_keys or any(panel != {'1', '2', '3'} for panel in panels.values()):
        raise ValueError('invalid_target_panel')
    return selected


def freeze():
    if sha(DATA) != EXPECTED:
        raise ValueError('source_hash_mismatch')
    tests = OUT / 'SYNTHETIC_TESTS.json'
    if not json.loads(tests.read_text(encoding='utf-8'))['success']:
        raise ValueError('scope_tests_failed')
    files = PROTECTED + [OUT / 'PROTOCOL.md', Path(__file__),
                         Path(__file__).with_name('test_diagnose_targets.py'), tests]
    save('FREEZE.json', {'utc': utc(), 'source_sha256': EXPECTED,
                         'files': [{'path': str(path), 'sha256': sha(path)} for path in files]})


def run():
    freeze_record = json.loads((OUT / 'FREEZE.json').read_text(encoding='utf-8'))
    if any(sha(item['path']) != item['sha256'] for item in freeze_record['files']):
        raise ValueError('frozen_input_changed')
    save('READ_STARTED.json', {'utc': utc(), 'authorized_scope': 'all L72; T72/D72 only individually invalid L72 rows'})
    target_rows = identities()
    live = live_pass(csv_records(DATA), target_rows)
    bad = {row: record for row, record in live.items()
           if record['observed_live']['classification'] != 'valid_nonnegative'}
    relations = relation_pass(csv_records(DATA), bad)
    by_well = defaultdict(list)
    for record in live.values():
        by_well[tuple(record['key'])].append(record)
    affected = []
    for key in sorted({tuple(record['key']) for record in bad.values()}):
        panel = sorted(by_well[key], key=lambda record: record['img'])
        values = [record['observed_live']['finite_value'] for record in panel]
        raw_mean = sum(values)/len(values) if all(value is not None for value in values) else None
        affected.append({'key': list(key), 'complete_live_only_panel': panel,
                         'raw_arithmetic_mean_including_all_images': raw_mean,
                         'registered_nonnegative_image_readout_requirement_passes': False,
                         'mean_finite': raw_mean is not None and math.isfinite(raw_mean),
                         'mean_nonnegative': None if raw_mean is None else raw_mean >= 0})
    combined = [{**record, **relations[row]} for row, record in sorted(bad.items())]
    checks = [{'path': item['path'], 'unchanged': sha(item['path']) == item['sha256']}
              for item in freeze_record['files']]
    if not all(check['unchanged'] for check in checks):
        raise ValueError('frozen_input_changed_after_diagnostic')
    result = {'utc': utc(), 'status': 'TARGET_QUALIFICATION_DIAGNOSTIC_ONLY_NO_RETEST',
              'source_sha256': sha(DATA), 'relative_time': 72, 'target_record_count': len(live),
              'target_well_count': len(by_well),
              'live_classification_counts': dict(Counter(record['observed_live']['classification'] for record in live.values())),
              'invalid_record_count': len(bad), 'affected_well_count': len(affected),
              'invalid_records_exact': combined, 'affected_wells': affected,
              'all_invalid_rows_exact_total_minus_dead_identity': bool(combined) and all(
                  record['arithmetic'].get('live_plus_dead_equals_total_exact', False) for record in combined),
              'exposure_ledger': {
                  'all_72h_live_source_rows': sorted(live),
                  'additional_72h_total_and_dead_source_rows': sorted(bad),
                  'numeric_live_values_opened': len(live), 'numeric_additional_total_values_opened': len(bad),
                  'numeric_additional_dead_values_opened': len(bad),
                  'other_future_response_numeric_reads': 0, 'replicates_numeric_reads': 0,
                  'model_fits': 0, 'filtered_records': 0, 'clipped_values': 0, 'network_requests': 0},
              'frozen_checks': checks, 'all_frozen_unchanged': True,
              'interpretation': 'Invalid observed targets invalidate the registered nonnegative-count transform. This is data qualification failure, not a negative channel-information or biological result. Exact subtraction arithmetic may explain the export value but does not authenticate intended exporter semantics.'}
    save('DIAGNOSTIC.json', result)
    print(json.dumps({key: result[key] for key in ['status', 'target_record_count', 'target_well_count',
                      'live_classification_counts', 'invalid_record_count', 'affected_well_count',
                      'all_invalid_rows_exact_total_minus_dead_identity']}))


if __name__ == '__main__':
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
