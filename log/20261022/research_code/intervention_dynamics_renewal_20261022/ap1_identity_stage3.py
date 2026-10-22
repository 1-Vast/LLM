"""Final exact root-authorized lineage key pass, reusing tested identity guards."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

import ap1_identity_stage1 as first
import ap1_identity_stage2 as second


def policy():
    cells = {}
    for start, end in [(6, 53), (56, 102)]:
        for row in range(start, end + 1):
            for column, field, kinds in [('D', 'lineageId', second.IDENTITY),
                                         ('F', 'annotationID_string_only', second.STRING),
                                         ('I', 'file_id', second.STRING)]:
                cells[f'{column}{row}'] = {'field': field, 'allowed_types': sorted(kinds)}
    return {'Figure 4e': cells}


def previous_checks():
    checks = []
    for name in ['FREEZE.json', 'STAGE2_FREEZE.json']:
        frozen = json.loads((first.OUT / name).read_text(encoding='utf-8'))
        checks.extend({'path': item['path'], 'unchanged': first.sha(item['path']) == item['sha256']}
                      for item in frozen['files'])
    for name in ['SYNTHETIC_TESTS.json', 'STAGE2_SYNTHETIC_TESTS.json']:
        if not json.loads((first.OUT / name).read_text(encoding='utf-8'))['success']:
            raise ValueError('previous_synthetic_tests_failed')
    if not all(check['unchanged'] for check in checks):
        raise ValueError('previous_frozen_input_changed')
    return checks


def freeze():
    if first.sha(first.RAW) != first.EXPECTED:
        raise ValueError('source_hash_mismatch')
    checks = previous_checks()
    paths = [Path(__file__), Path(first.__file__), Path(second.__file__)]
    paths.extend(first.OUT / name for name in [
        'STAGE3_PROTOCOL.md', 'FREEZE.json', 'STAGE2_FREEZE.json',
        'SYNTHETIC_TESTS.json', 'STAGE2_SYNTHETIC_TESTS.json',
        'STAGE1_STRINGS.json', 'FIELD_ROLES.json', 'REPORT_STAGE1.md',
        'STAGE2_IDENTITIES.json', 'STAGE2_IDENTITY_SUMMARY.json',
        'STAGE2_4E_STRING_TYPE_MATRIX.json', 'STAGE2_FIG3_FULL_TUPLE_POSTCHECK.json'])
    first.write('STAGE3_FREEZE.json', {
        'utc': first.utc(), 'source_sha256': first.EXPECTED,
        'policy_sha256': hashlib.sha256(json.dumps(policy(), sort_keys=True).encode()).hexdigest(),
        'previous_frozen_checks': checks,
        'files': [{'path': str(path), 'sha256': first.sha(path)} for path in paths]})


def pair_summary(result):
    cells = result['sheets']['Figure 4e']['cells']
    sections = {}
    groups = {}
    for label, rows in [('starting_cell', range(6, 54)), ('final_colony', range(56, 103))]:
        by_key = defaultdict(list)
        incomplete = []
        for row in rows:
            lineage, annotation, file_id = (cells[f'{column}{row}'] for column in 'DFI')
            record = {'row': row,
                      'lineageId': {'type': lineage['type'], 'value': lineage.get('value')},
                      'file_id': {'type': file_id['type'], 'value': file_id.get('value')},
                      'annotationID': {'type': annotation['type'], 'value_opened': annotation['value_opened']}}
            if annotation['value_opened']:
                record['annotationID']['string_value'] = annotation['value']
            if not lineage['value_opened'] or not file_id['value_opened']:
                incomplete.append(record)
            else:
                by_key[(file_id['value'], lineage['value'])].append(record)
        groups[label] = by_key
        sections[label] = {
            'rows': len(rows), 'complete_key_rows': sum(len(records) for records in by_key.values()),
            'unique_complete_keys': len(by_key), 'incomplete_key_rows': incomplete,
            'all_key_groups': [{'file_id': key[0], 'lineageId': key[1], 'records': records}
                               for key, records in by_key.items()],
            'duplicate_key_groups': [{'file_id': key[0], 'lineageId': key[1], 'records': records}
                                     for key, records in by_key.items() if len(records) > 1]}
    starts, finals = groups['starting_cell'], groups['final_colony']
    common = starts.keys() & finals.keys()
    pairs, ambiguous = [], []
    for key in sorted(common):
        entry = {'file_id': key[0], 'lineageId': key[1],
                 'starting_rows': [record['row'] for record in starts[key]],
                 'final_rows': [record['row'] for record in finals[key]]}
        (pairs if len(starts[key]) == len(finals[key]) == 1 else ambiguous).append(entry)
    return {
        'comparison': 'exact lexical (file_id,lineageId); original numeric/string types retained in records',
        'sections': sections, 'one_to_one_paired_keys': pairs, 'ambiguous_shared_keys': ambiguous,
        'starting_only_keys': [{'file_id': key[0], 'lineageId': key[1], 'records': starts[key]}
                               for key in sorted(starts.keys() - finals.keys())],
        'final_only_keys': [{'file_id': key[0], 'lineageId': key[1], 'records': finals[key]}
                            for key in sorted(finals.keys() - starts.keys())],
        'one_to_one_pairs_by_file': dict(Counter(pair['file_id'] for pair in pairs)),
        'limits': ['Source-level paired reporter identities do not establish a complete all-attempt/dead/lost tree.',
                   'Unmatched starting identity is not classified as death, loss or censorship.',
                   'No numerical reporter value, drug-B challenge response, selection bound or independent-run/RSI qualification.']}


def run():
    frozen = json.loads((first.OUT / 'STAGE3_FREEZE.json').read_text(encoding='utf-8'))
    if first.sha(first.RAW) != first.EXPECTED or any(first.sha(item['path']) != item['sha256'] for item in frozen['files']):
        raise ValueError('stage3_frozen_input_changed')
    previous_checks()
    first.write('STAGE3_READ_STARTED.json', {'utc': first.utc(), 'source_sha256': first.EXPECTED})
    result = second.read_identity(first.RAW, policy())
    result.update({'utc': first.utc(), 'status': 'FINAL_EXACT_LINEAGE_KEYPASS_COMPLETE',
                   'source_sha256': first.EXPECTED, 'network_requests': 0})
    summary = pair_summary(result)
    checks = [{'path': item['path'], 'unchanged': first.sha(item['path']) == item['sha256']} for item in frozen['files']]
    prior = previous_checks()
    source_hash = first.sha(first.RAW)
    if source_hash != first.EXPECTED or not all(check['unchanged'] for check in checks + prior):
        raise ValueError('frozen_input_changed_after_read')
    first.write('STAGE3_IDENTITIES.json', result)
    first.write('STAGE3_LINEAGE_PAIRING.json', {'utc': first.utc(), 'input_sha256': first.sha(first.OUT / 'STAGE3_IDENTITIES.json'), **summary})
    first.write('STAGE3_FINAL_CHECKS.json', {
        'utc': first.utc(), 'source_sha256': source_hash, 'source_hash_matches': True,
        'frozen_checks': checks, 'previous_frozen_checks': prior, 'all_frozen_unchanged': True,
        'synthetic_guard_reused': 'Stage2 passed tests; no new redundant tests per root authorization',
        'response_value_bodies_opened': False, 'network_requests': 0,
        'approved_positions': len(policy()['Figure 4e']),
        'opened_values': sum(cell['value_opened'] for cell in result['sheets']['Figure 4e']['cells'].values())})
    print(json.dumps({'status': result['status'], 'type_counts': result['sheets']['Figure 4e']['type_counts'],
                      'section_counts': {name: {key: section[key] for key in ['rows', 'complete_key_rows', 'unique_complete_keys']}
                                         for name, section in summary['sections'].items()},
                      'pairs': len(summary['one_to_one_paired_keys']), 'pairs_by_file': summary['one_to_one_pairs_by_file'],
                      'ambiguous': summary['ambiguous_shared_keys'], 'starting_only': summary['starting_only_keys'],
                      'final_only': summary['final_only_keys']}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        {'freeze': freeze, 'run': run}[sys.argv[1]]()
    except Exception as error:
        if not (first.OUT / 'STAGE3_FAILURE.json').exists():
            first.write('STAGE3_FAILURE.json', {'utc': first.utc(), 'status': 'STOP_FINAL_LINEAGE_KEYPASS_FAILURE',
                                               'error_type': type(error).__name__})
        raise
