"""Bind the scoped research decision; do not rerun scientific experiments."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/operator_renewal'
OUT = LOG / 'root'
CODE = [ROOT / 'research' / name for name in (
    'operator_renewal_20261022', 'frontier_operator_20261022',
    'functional_operator_20261022', 'recursive_operator_20261022')]


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2)


def main():
    spec = importlib.util.spec_from_file_location('previous_preservation',
        ROOT / 'research/cipa_control_information_20261022/preserve.py')
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    preservation = previous.verify()
    for name in ('cipa_control_information', 'contrast_gate_check', 'mse_source_gate',
                 'native_operation/root'):
        manifest = ROOT / f'log/20261022/{name}/FINAL_FILE_INVENTORY.json'
        preservation['manifest_sha256'][manifest.relative_to(ROOT).as_posix()] = sha(manifest)
        for record in load(manifest)['files']:
            path = ROOT / record['path']
            preservation['checks'].append({'path': record['path'], 'passed': path.is_file()
                and path.stat().st_size == record['bytes'] and sha(path) == record['sha256']})
    postfinal = ROOT / 'log/20261022/native_operation/root/POSTFINAL_VERIFICATION.json'
    preservation['checks'].append({'path': postfinal.relative_to(ROOT).as_posix(),
        'passed': sha(postfinal) == load(OUT / 'START.json')['predecessor_postfinal_sha256']})
    assert len(preservation['checks']) == 6705
    preservation.update(passed=all(row['passed'] for row in preservation['checks']),
                        utc=datetime.now(timezone.utc).isoformat())
    assert preservation['passed']

    checks = []

    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        assert condition, name

    def bound(path, expected, label, size=None):
        path = Path(path)
        if not path.is_absolute():
            path = ROOT / path
        if path == ROOT / 'research/REPORT.md':
            path = OUT / 'START_REPORT_SNAPSHOT.md'
        check(label, path.is_file() and sha(path).lower() == expected.lower()
              and (size is None or path.stat().st_size == size))

    def walk(value, seal):
        if isinstance(value, dict):
            if 'path' in value and 'sha256' in value:
                bound(value['path'], value['sha256'],
                      seal.relative_to(LOG).as_posix() + ':' + value['path'], value.get('bytes'))
            for key, child in value.items():
                if ('/' in key or '\\' in key) and isinstance(child, str) and re.fullmatch('[0-9a-fA-F]{64}', child):
                    bound(key, child, seal.relative_to(LOG).as_posix() + ':' + key)
                walk(child, seal)
        elif isinstance(value, list):
            for child in value:
                walk(child, seal)

    seals = sorted(set(LOG.rglob('*SEAL.json')) | set(LOG.rglob('*FREEZE.json'))
                   | set(LOG.rglob('*INVENTORY.json')) | set(LOG.rglob('FINAL_MANIFEST.json')))
    for name in ('frontier/INDEPENDENT_SEAL.json', 'frontier/FINAL_COMPLETE_SEAL.json',
                 'functional/INDEPENDENT_SEAL.json', 'functional/FINAL_REVIEW_SEAL.json',
                 'functional/POSTFINAL_REVIEW_SEAL.json', 'recursive/ORIGINAL_SEAL.json',
                 'recursive/FINAL_MANIFEST.json', 'root/API_FALSIFIER_FREEZE.json',
                 'root/FUNCTIONAL_AUDIT_FREEZE.json'):
        check('mandatory:' + name, LOG / name in seals)
    for seal in seals:
        walk(load(seal), seal)
    for folder in CODE:
        for path in sorted(folder.glob('*.py')):
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
            check('python_parse:' + path.relative_to(ROOT).as_posix(), True)

    api = load(LOG / 'api_constructive/RECEIPT.json')
    check('one_actual_complete_api_call', api['logical_requests'] == 1
          and api['status'] == 'COMPLETE' and api['usage']['total_tokens'] == 3945)
    response = (LOG / 'api_constructive/RESPONSE.md').read_text(encoding='utf-8')
    check('api_returned_text_hash', hashlib.sha256(response.encode()).hexdigest() == api['response_sha256'])
    bound(CODE[0] / 'call_provider.py', api['code_sha256'], 'api_call_code')
    for name, code in [('API_FALSIFIER_RESULT.json', 'check_api_rule.py'),
                       ('FUNCTIONAL_AUDIT_RESULT.json', 'audit_functional.py')]:
        result = load(OUT / name)
        values = result['checks'].values() if isinstance(result['checks'], dict) else [row['passed'] for row in result['checks']]
        check('recorded_checks:' + name, result['all_passed'] and all(values))
        bound(CODE[0] / code, result['code_sha256'], name + ':code')
        bound(OUT / name.replace('_RESULT', '_FREEZE'), result['freeze_sha256'], name + ':freeze')
    functional = load(OUT / 'FUNCTIONAL_AUDIT_RESULT.json')
    check('exact_fixture_sharp_gap', functional['sharp_shared_gauge_pair_gap'] == '10919/143748'
          and functional['dual_slope'] == '-625450/691757'
          and functional['new_biological_scalar_reads'] == functional['fits'] == 0)
    frontier = load(LOG / 'frontier/OPERATION_RESULT.json')
    check('frontier_recorded291', frontier['assertions'] == 291 and len(frontier['tasks']) == 12)
    bound(CODE[1] / 'check_operator.py', frontier['code_sha256'], 'frontier_result_code')
    recursive = load(LOG / 'recursive/CHECK_RESULT.json')
    check('recursive_recorded48identities', recursive['pointwise_candidate_conventional_identities'] == 48)
    bound(CODE[3] / 'trace_credit_check.py', recursive['code_sha256'], 'recursive_result_code')

    for receipt in sorted((LOG / 'frontier').glob('*.receipt.json')):
        record = load(receipt)
        bound(receipt.with_name(receipt.name.removesuffix('.receipt.json') + '.body'),
              record['sha256'], 'frontier_source:' + receipt.stem, record['bytes'])
    for body, receipt in [('paes.html', 'paes_receipt.json'), ('query_rao.xml', 'query_receipt.json')]:
        record = load(LOG / 'recursive' / receipt)
        bound(LOG / 'recursive' / body, record['sha256'], 'recursive_source:' + body, record.get('bytes'))
    for name in ('DECISION.md', 'CONTINUATION.md', 'DEBATE_SYNTHESIS.md', 'SCIENTIFIC_BOUNDARY.md'):
        check('decision_record:' + name, (OUT / name).is_file())

    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    write('DIFF_CHECK.json', {'command': 'git diff --check', 'exit_code': diff.returncode,
                            'stdout': diff.stdout, 'stderr': diff.stderr})
    check('git_diff_check', diff.returncode == 0)
    write('PREDECESSOR_PRESERVATION.json', preservation)
    write('FINAL_INTEGRITY.json', {'passed': True, 'checks': checks,
        'predecessor_entries': len(preservation['checks']),
        'preservation_report_sha256': sha(OUT / 'PREDECESSOR_PRESERVATION.json'),
        'verified_seals_and_manifests': [p.relative_to(LOG).as_posix() for p in seals],
        'new_deepseek_calls': 1, 'reported_deepseek_tokens': 3945,
        'new_predictive_fits': 0, 'biological_assay_scalar_decodes': 0,
        'scientific_experiments_rerun_by_finalizer': 0,
        'scientific_performance_success': False, 'full_goal': 'ACTIVE / NOT_ACHIEVED',
        'utc': datetime.now(timezone.utc).isoformat()})
    files = [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}
             for folder in [LOG] + CODE for p in sorted(folder.rglob('*'))
             if p.is_file() and '__pycache__' not in p.parts]
    write('FINAL_FILE_INVENTORY.json', {'files': files, 'excludes_itself': True})
    print(json.dumps({'passed': True, 'integrity_checks': len(checks),
                      'predecessor_entries': len(preservation['checks']), 'current_files': len(files)}))


if __name__ == '__main__':
    main()
