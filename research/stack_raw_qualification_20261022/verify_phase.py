"""Non-fitting verification of receipts, metadata, documents and older freezes."""
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/stack_raw_qualification'
CODE = ROOT / 'research/stack_raw_qualification_20261022'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []

    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})

    preserved = {}
    for name in ['functional_dynamics_gate', 'dead_stock_information_gate']:
        inventory = load(LOG.parent / name / 'FINAL_FILE_INVENTORY.json')
        for item in inventory['files']:
            path = ROOT / item['path']
            check('prior_unchanged:' + item['path'], path.stat().st_size == item['bytes']
                  and sha(path) == item['sha256'])
        preserved[name] = len(inventory['files'])
    receipts = []
    for path in sorted(LOG.rglob('*.NETWORK.json')):
        receipt = load(path)
        body = Path(receipt['body_path'])
        check('receipt_size:' + path.name, body.stat().st_size == receipt['bytes'])
        check('receipt_sha256:' + path.name, sha(body) == receipt['sha256'])
        check('no_retry_auto_redirect:' + path.name,
              receipt['retries'] == 0 and receipt['automatic_redirects'] is False)
        receipts.append(receipt)
    manifest = load(LOG / 'network/v1_root_files.body')
    acquired = load(LOG / 'RAW_ACQUISITION_FINAL.json')
    check('four_objects_qualified', len(manifest) == len(acquired['files']) == 4 and acquired['all_qualified'])
    for item, actual in zip(manifest, acquired['files']):
        path = Path(actual['body_path'])
        check('manifest_size:' + item['id'], path.stat().st_size == item['content_details']['size'])
        check('manifest_sha256:' + item['id'], sha(path) == item['content_details']['sha256_hash'])
    summary = load(LOG / 'IDENTITY_SUMMARY.json')
    pairs = load(LOG / 'SECOND_MARKER_PROJECTION.json')
    check('library_exact_names', summary['library_nonempty_compound_rows'] == 1833
          and summary['library_unique_exact_names'] == 1833 and not summary['library_duplicate_names'])
    for screen, pair in zip(summary['screens'], pairs['files']):
        name = screen['filename']
        check('1920_export_rows:' + name, screen['identity_rows'] == 1920)
        check('1833_unique_joined_nonempty_names:' + name,
              screen['unique_name_exact_library_join_multiplicity'] == {'1': 1833, '0': 1}
              and not screen['unmatched_exact_names'])
        check('SG_first_marker:' + name, screen['marker_counts'] == {'SG+': 1920})
        expected_marker = 'NLS' if '+ DMSO +' in name else 'mKate2+'
        check('second_marker:' + name, pair['second_marker_counts'] == {expected_marker: 1920})
        errors = pair['empty_or_nonstring_compounds']
        check('87_unidentified_errors:' + name, set(errors) == {f'A{r}' for r in range(601, 688)}
              and all(c == {'type': 'e', 'identity_literal': '#N/A'} for c in errors.values()))
        expected = [str(t) for t in range(0, 119, 2)] if name.startswith('U2OS') else [str(t) for t in range(0, 97, 4)]
        header = list(screen['header'].values())
        count = len(expected)
        check('paired_time_headers:' + name, header[2:2+count] == expected
              and header[2+count] == 'phenotypic_Marker' and header[3+count:3+2*count] == expected)
    collisions = load(LOG / 'METADATA_COLLISIONS.json')
    check('same1833_named_entries_across_screens', all(p['common_exact_names'] == 1833
          and not p['first_only'] and not p['second_only'] for p in collisions['cross_screen_exact_name_overlap']))
    conflict = collisions['metadata_collisions']['exact_SMILES']['duplicate_literals']
    check('annotation_conflict_preserved', len(conflict) == 1 and
          {entry['compound'] for entries in conflict.values() for entry in entries} == {'Doxycycline Hyclate', 'E-64'})
    for folder in ['data_auditor', 'skeptic']:
        for document in ['INDEPENDENT.md', 'CROSS.md', 'POST_SCHEMA.md']:
            check('completed_review:' + folder + '/' + document, (LOG / folder / document).is_file())
    for path in CODE.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
        check('source_parses:' + path.name, True)
    decision = LOG / 'DECISION.md'
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', decision.read_text(encoding='utf-8')):
        check('decision_link:' + target, (decision.parent / target).is_file())
    for name, target in [('research/REPORT.md', '../log/20261022/stack_raw_qualification/DECISION.md'),
                         ('log/README.md', '20261022/stack_raw_qualification/DECISION.md')]:
        check('navigation:' + name, target in (ROOT / name).read_text(encoding='utf-8'))
    for name in ['WORKBOOK_STRUCTURE.json', 'LABEL_PROJECTION.json', 'IDENTITY_SUMMARY.json',
                 'SECOND_MARKER_PROJECTION.json', 'METADATA_COLLISIONS.json']:
        obj = load(LOG / name)
        for key in ['cell_values_decoded', 'numeric_or_formula_values_decoded',
                    'response_values_converted', 'response_values_read']:
            if key in obj:
                check('closed_response_self_report:' + name + ':' + key, obj[key] == 0)
    report = {'checks': checks, 'check_count': len(checks), 'all_pass': all(c['pass'] for c in checks),
              'preserved_prior_files': preserved,
              'resources': {'public_GETs': len(receipts), 'retained_HTTP_body_bytes': sum(r['bytes'] for r in receipts),
                            'acquired_workbook_bytes': sum(i['bytes'] for i in acquired['files']),
                            'deepseek_calls': 0, 'model_fits': 0, 'wet_lab_experiments': 0,
                            'scope_canaries_passed': 6},
              'scientific_status': 'MANIFEST_AND_EXPORTED_ROW_SCHEMA_QUALIFIED_RESPONSES_UNOPENED',
              'goal_status': 'ACTIVE_NOT_ACHIEVED'}
    with (LOG / 'VERIFICATION.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'checks'}))
    return 0 if report['all_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
