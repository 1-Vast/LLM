"""Verify recorded bindings and preserve predecessors; do not rerun experiments."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/next_mechanism'
OUT = LOG / 'root'
CODE = [ROOT / 'research' / name for name in (
    'next_mechanism_20261022', 'next_mechanism_frontier_20261022',
    'next_mechanism_recursive_20261022', 'next_mechanism_source_20261022')]


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
                 'native_operation/root', 'operator_renewal/root', 'mechanism_gap/root'):
        manifest = ROOT / f'log/20261022/{name}/FINAL_FILE_INVENTORY.json'
        preservation['manifest_sha256'][manifest.relative_to(ROOT).as_posix()] = sha(manifest)
        for record in load(manifest)['files']:
            path = ROOT / record['path']
            preservation['checks'].append({'path': record['path'], 'passed': path.is_file()
                and path.stat().st_size == record['bytes'] and sha(path) == record['sha256']})
    post = ROOT / 'log/20261022/native_operation/root/POSTFINAL_VERIFICATION.json'
    expected = load(ROOT / 'log/20261022/operator_renewal/root/START.json')['predecessor_postfinal_sha256']
    preservation['checks'].append({'path': post.relative_to(ROOT).as_posix(), 'passed': sha(post) == expected})
    assert len(preservation['checks']) == 7005
    preservation.update(passed=all(r['passed'] for r in preservation['checks']),
                        utc=datetime.now(timezone.utc).isoformat())
    if not preservation['passed']:
        failed = [row for row in preservation['checks'] if not row['passed']]
        write('FINALIZATION_PRESERVATION_FAILURE.json', {'failed': failed,
              'utc': preservation['utc'], 'scientific_experiments_rerun': 0})
        print(json.dumps({'preservation_failed': failed}), flush=True)
    assert preservation['passed']
    checks = []

    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        assert condition, name

    def bound(path, expected, label, size=None):
        check(label, path.is_file() and sha(path).lower() == expected.lower()
              and (size is None or path.stat().st_size == size))

    def walk(value, seal):
        if isinstance(value, dict):
            entry = value.get('path', value.get('file'))
            if isinstance(entry, str) and 'sha256' in value:
                path = Path(entry)
                if not path.is_absolute():
                    path = ROOT / path if path.parts[0] in ('research', 'log') else seal.parent / path
                bound(path, value['sha256'], str(seal.relative_to(LOG)) + ':' + entry, value.get('bytes'))
            for child in value.values():
                walk(child, seal)
        elif isinstance(value, list):
            for child in value:
                walk(child, seal)

    seals = sorted(set(LOG.rglob('*SEAL.json')) | set(LOG.rglob('*SEAL*.json')))
    for seal in seals:
        walk(load(seal), seal)
    for role in ('frontier', 'recursive', 'source'):
        check('independent:' + role, (LOG / role / 'INDEPENDENT_SEAL.json').is_file())
        check('actual_crossreview:' + role, (LOG / role / 'CROSS_REVIEW.md').is_file())
    for name in ('frontier/POSTSEAL_REVIEW.json', 'frontier/DEBATE_COMPLETION.json'):
        walk(load(LOG / name), LOG / name)
    recursive_cross = load(LOG / 'recursive/CROSS_REVIEW_SEAL.json')
    bound(LOG / 'recursive/CROSS_REVIEW.md', recursive_cross['cross_review_sha256'], 'recursive_cross_exact',
          recursive_cross['cross_review_bytes'])
    cdk_cross = load(LOG / 'recursive/cdk_mechanism/CROSS_SEAL.json')
    bound(LOG / 'recursive/cdk_mechanism/CROSS_REVIEW.md', cdk_cross['cross_sha256'],
          'recursive_cdk_actual_cross', cdk_cross['cross_bytes'])
    for folder in CODE:
        for path in folder.rglob('*.py'):
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
            check('python_parse:' + path.relative_to(ROOT).as_posix(), True)
    frontier = load(LOG / 'frontier/RESULT.json')
    check('recorded_frontier_falsifier', frontier['all_pass'] and frontier['check_count'] == 27
          and frontier['plans']['A']['parameter_mse'] == '1'
          and frontier['plans']['B']['parameter_mse'] == '625/49')
    bound(CODE[1] / 'check_segment_coverage.py', frontier['code_sha256'], 'executed_frontier_code')
    bound(LOG / 'frontier/MINIMAL_FALSIFICATION_PROTOCOL.md', frontier['protocol_sha256'], 'frontier_frozen_protocol')
    recursive = load(LOG / 'recursive/FALSIFIER_RESULT.json')
    check('recorded_edit_ordering_falsifier', [r['order_difference'] for r in recursive['later']] == ['1', '-1']
          and recursive['arithmetic_costs']['source_edit_evaluations'] == 32
          and recursive['arithmetic_costs']['later_edit_evaluations'] == 8)
    bound(CODE[2] / 'check_edit_algebra.py', recursive['code_sha256'], 'executed_recursive_code')
    identity = load(LOG / 'source/STANDARD_IDENTITY.json')
    check('recorded_sequence_matches', len(identity['checks']) == 2
          and all(r['length'] == 100 and r['matches_reverse_complement'] for r in identity['checks']))
    bound(LOG / 'source/nature_supp_tables.body', identity['table_sha256'], 'standard_primary_table')
    bound(ROOT / 'log/20261022/mechanism_gap/root/source_completion/pretreatment_code.body',
          identity['code_sha256'], 'standard_primary_static_code')
    literature = OUT / 'literature'
    rows = []
    for name in ('RECEIPTS.json', 'SELECTED_RECEIPTS.json', 'WOUND_INDEX_RECEIPTS.json',
                 'CDK_RECEIPTS.json'):
        rows.extend(load(literature / name))
    for name, prefix in (('PROFET_ALTERNATIVE_RECEIPT.json', 'profet_bioc'),
                         ('CDK_ALTERNATIVE_RECEIPT.json', 'cdk_epmc')):
        row = load(literature / name)
        rows.append(dict(row, name=prefix))
    for row in rows:
        if 'sha256' in row:
            path = literature / (row['name'] + '.body')
            if not path.exists():
                path = literature / (row['name'] + '.xml')
            bound(path, row['sha256'], 'root_primary:' + row['name'], row['bytes'])
    check('root_request_ledger', len(rows) == 11 and sum('sha256' in r for r in rows) == 9
          and sum(r.get('bytes', 0) for r in rows) == 3913072)
    wound = load(literature / 'wound_tree.body')
    check('new_density_source_tree', wound['truncated'] is False and len(wound['tree']) == 7839)
    for name in ('DECISION.md', 'CONTINUATION.md', 'OBJECTIVE_STATUS.md', 'SOURCE_UPDATE.md', 'DEBATE_SYNTHESIS.md'):
        check('required_root_record:' + name, (OUT / name).is_file())
    for name in ('frontier/cdk_critic/INDEPENDENT.md', 'recursive/cdk_mechanism/INDEPENDENT.md',
                 'recursive/cdk_mechanism/OBSERVATION_LAW_RESPONSE.md', 'source/cdk_review/ADDENDUM.md',
                 'source/cdk_review/S4_ADDENDUM.md', 'source/cdk_review/S4_SEAL.json',
                 'recursive/cdk_mechanism/CROSS_REVIEW.md', 'frontier/cdk_critic/SOURCE_CROSS.md'):
        check('new_cdk_record:' + name, (LOG / name).is_file())
    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    write('DIFF_CHECK.json', {'command': 'git diff --check', 'exit_code': diff.returncode,
                            'stdout': diff.stdout, 'stderr': diff.stderr})
    check('git_diff_check', diff.returncode == 0)
    write('PREDECESSOR_PRESERVATION.json', preservation)
    write('FINAL_INTEGRITY.json', {'passed': True, 'checks': checks,
        'predecessor_entries': len(preservation['checks']), 'verified_seals': [p.relative_to(LOG).as_posix() for p in seals],
        'root_direct_http_requests': 11, 'root_successful_primary_body_bytes': 3913072,
        'new_direct_deepseek_calls': 0, 'native_usage_and_money': 'NOT_EXPOSED_BY_COLLABORATION_INTERFACE',
        'new_biological_predictor_fits': 0, 'new_biological_outcome_scalar_decodes': 0,
        'scientific_experiments_rerun_by_finalizer': 0, 'scientific_performance_success': False,
        'full_goal': 'ACTIVE / NOT_ACHIEVED', 'utc': datetime.now(timezone.utc).isoformat()})
    files = [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}
             for folder in [LOG] + CODE for p in sorted(folder.rglob('*'))
             if p.is_file() and '__pycache__' not in p.parts]
    write('FINAL_FILE_INVENTORY.json', {'files': files, 'excludes_itself': True})
    print(json.dumps({'passed': True, 'checks': len(checks), 'predecessor_entries': 7005, 'current_files': len(files)}))


if __name__ == '__main__':
    main()
