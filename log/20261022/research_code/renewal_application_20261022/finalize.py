"""Seal phase evidence after checking independent audits and old inventories."""
import ast
from collections import Counter
from datetime import datetime, timezone
import json
import subprocess

from preserve import LOG, ROOT, sha, verify


def read(name):
    return json.loads((LOG / name).read_text(encoding='utf-8'))


def main():
    checks = []
    prior = verify()
    checks.append({'name': '1037_prior_files_unchanged', 'passed': prior['passed'] and len(prior['checks']) == 1037})
    baseline = read('BASELINE_PRESERVATION.json')
    checks.append({'name': 'prior_manifest_hashes', 'passed': prior['manifest_sha256'] == baseline['manifest_sha256']})
    independent = {
        'advocate/INDEPENDENT.md': 'b37abe4331edf2bcc4731152eb4d4852ce34eb49ec3bb867d2a394daaec3c53c',
        'skeptic/INDEPENDENT.md': '0e6cf6c994cbc9892d70c3b00f14ccbee77c046109aebc4957faea17cc59b8e9',
        'data/INDEPENDENT.md': '54d54f7199866c186df2a951c6818ed331702fb2774d1565bc12d35962121f96',
        'root_proposal/RESPONSE.md': '27833a0b350fe279b2a6ccb557dec744519365a35d6c26dcbc0fb5d79ffbb2b2',
    }
    for name, expected in independent.items():
        checks.append({'name': 'sealed:' + name, 'passed': sha(LOG / name) == expected})
    for name, expected in read('skeptic/SELECTION_TRANSPORT_FREEZE.json')['files'].items():
        checks.append({'name': 'freeze:' + name, 'passed': sha(ROOT / name) == expected})
    mathematical = read('skeptic/SELECTION_TRANSPORT_RESULT.json')
    checks.append({'name': 'six_constructed_checks', 'passed': len(mathematical['checks']) == 6 and all(mathematical['checks'].values())})
    tests = read('skeptic/SELECTION_TRANSPORT_TESTS.json')
    checks.append({'name': 'three_synthetic_tests', 'passed': tests.get('exit_code') == 0})
    independent_math = read('advocate/COUNTEREXAMPLE_CHECK.json')
    checks.append({'name': '13_independent_founder_checks', 'passed': len(independent_math['checks']) == 13 and all(independent_math['checks'].values())})
    keys = read('data/WATERMELON_KEY_AUDIT.json')
    checks.append({'name': 'independent_support_curves_match', 'passed': keys['raw_token_curve_exact_match'] and keys['single30_curve_exact_match']})
    checks.append({'name': 'missing_keys_explain_guard_failure', 'passed': keys['all_duplicate_excess_exactly_missing_key_excess']
                   and keys['all_sample_cell_keys_duplicate_excess'] == 20616
                   and keys['nonmissing_sample_cell_keys']['duplicate_excess'] == 0
                   and keys['selected_single30_subset']['nonmissing_sample_cell_key_duplicate_excess'] == 0})
    checks.append({'name': 'row_identity_unique', 'passed': keys['all_row_identifiers']['unique'] == 56419
                   and keys['all_row_identifiers']['duplicate_excess'] == 0})
    statuses = Counter()
    for path in sorted((LOG / 'root_sources').glob('*.http.json')):
        receipt = json.loads(path.read_text(encoding='utf-8'))
        body = path.with_name(path.name.replace('.http.json', '.body'))
        statuses[receipt['status']] += 1
        checks.append({'name': 'HTTP_body:' + path.stem, 'passed': body.stat().st_size == receipt['bytes'] and sha(body) == receipt['sha256']})
    checks.append({'name': 'root_18_source_requests', 'passed': dict(statuses) == {200: 16, 500: 2}})
    for folder in ('advocate', 'skeptic', 'data'):
        checks.append({'name': 'actual_cross:' + folder, 'passed': (LOG / folder / 'CROSS.md').stat().st_size > 3000})
    checks.append({'name': 'data_reviewer_integrity', 'passed': read('data/INTEGRITY_AND_INVENTORY.json')['status'] == 'PASS_REVIEWER_SOURCE_AND_RECORD_INTEGRITY'})
    code = ROOT / 'research/renewal_application_20261022'
    files = list(code.glob('*.py'))
    for path in files:
        ast.parse(path.read_text(encoding='utf-8-sig'))
    diff = subprocess.run(['git', 'diff', '--check', '--', str(code.relative_to(ROOT)), str(LOG.relative_to(ROOT)),
                           'research/REPORT.md', 'log/README.md'], cwd=ROOT, capture_output=True, text=True)
    checks.append({'name': 'scoped_diff_check', 'passed': diff.returncode == 0})
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'passed': all(row['passed'] for row in checks),
              'checks': checks, 'prior_files': 1037, 'root_source_HTTP_statuses': dict(statuses),
              'python_files_parsed': len(files), 'new_biological_fits': 0, 'model_performance_not_tested': True,
              'diff_stdout': diff.stdout, 'diff_stderr': diff.stderr}
    with (LOG / 'FINAL_INTEGRITY.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    if not result['passed']:
        raise RuntimeError('Phase integrity failed')
    inventory = sorted(path for directory in (LOG, code) for path in directory.rglob('*') if path.is_file()
                       and path.name != 'FINAL_FILE_INVENTORY.json')
    with (LOG / 'FINAL_FILE_INVENTORY.json').open('x', encoding='utf-8') as stream:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'files': [
            {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)} for path in inventory]}, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(checks), 'prior_files': 1037, 'phase_files': len(inventory)}))


if __name__ == '__main__':
    main()
