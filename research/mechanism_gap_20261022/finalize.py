"""Seal this scoped research decision without rerunning scientific experiments."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/mechanism_gap'
OUT = LOG / 'root'
CODE = [ROOT / 'research' / name for name in (
    'mechanism_gap_20261022', 'mechanism_gap_frontier_20261022',
    'mechanism_gap_functional_20261022', 'mechanism_gap_recursive_20261022',
    'mechanism_gap_review_advocate_20261022', 'mechanism_gap_review_method_20261022',
    'mechanism_gap_review_source_20261022')]


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(name, data):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(data, handle, indent=2)


def main():
    spec = importlib.util.spec_from_file_location('earlier_preservation',
        ROOT / 'research/cipa_control_information_20261022/preserve.py')
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    preservation = previous.verify()
    for name in ('cipa_control_information', 'contrast_gate_check', 'mse_source_gate',
                 'native_operation/root', 'operator_renewal/root'):
        manifest = ROOT / f'log/20261022/{name}/FINAL_FILE_INVENTORY.json'
        preservation['manifest_sha256'][manifest.relative_to(ROOT).as_posix()] = sha(manifest)
        for record in load(manifest)['files']:
            path = ROOT / record['path']
            preservation['checks'].append({'path': record['path'], 'passed': path.is_file()
                and path.stat().st_size == record['bytes'] and sha(path) == record['sha256']})
    post = ROOT / 'log/20261022/native_operation/root/POSTFINAL_VERIFICATION.json'
    expected_post = load(ROOT / 'log/20261022/operator_renewal/root/START.json')['predecessor_postfinal_sha256']
    preservation['checks'].append({'path': post.relative_to(ROOT).as_posix(),
                                   'passed': sha(post) == expected_post})
    assert len(preservation['checks']) == 6853
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
                bound(value['path'], value['sha256'], str(seal.relative_to(LOG)) + ':' + value['path'], value.get('bytes'))
            if 'review_path' in value and 'review_sha256' in value:
                bound(value['review_path'], value['review_sha256'], str(seal.relative_to(LOG)) + ':review')
            for key, child in value.items():
                if ('/' in key or '\\' in key) and isinstance(child, str) and re.fullmatch('[0-9a-fA-F]{64}', child):
                    bound(key, child, str(seal.relative_to(LOG)) + ':' + key)
                walk(child, seal)
        elif isinstance(value, list):
            for child in value:
                walk(child, seal)

    seals = sorted(set(LOG.rglob('*SEAL.json')) | set(LOG.rglob('*FREEZE.json')))
    for name in ('frontier/INDEPENDENT_SEAL.json', 'frontier/POSTCHECK_SEAL.json',
                 'frontier/POSTROLE_API_FINAL_SEAL.json', 'functional/INDEPENDENT_SEAL.json',
                 'recursive/INDEPENDENT_SEAL.json', 'review_advocate/INDEPENDENT_SEAL.json',
                 'review_advocate/DEBATE_SEAL.json', 'review_source/SEAL.json',
                 'review_source/POSTDEBATE_SEAL.json', 'review_method/SEAL.json',
                 'review_method/DEBATE_SEAL.json', 'root/source_completion/STATIC_FREEZE.json'):
        check('required:' + name, LOG / name in seals)
    for seal in seals:
        walk(load(seal), seal)
    advocate = load(LOG / 'review_advocate/DEBATE_SEAL.json')
    bound(LOG / 'review_advocate/INDEPENDENT.md', advocate['independent_sha256'], 'advocate_original_postdebate')
    bound(LOG / 'review_advocate/DEBATE.md', advocate['debate_sha256'], 'advocate_actual_debate')
    check('method_independence_honestly_limited', load(LOG / 'review_method/SEAL.json')['unsolicited_source_message_read_before_seal'])
    for folder in CODE:
        for path in sorted(folder.glob('*.py')):
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
            check('python_parse:' + path.relative_to(ROOT).as_posix(), True)

    frontier = load(LOG / 'frontier/CHECK_RESULT.json')
    check('recorded_frontier_exact_cases', frontier['exact_min_cost_flow_checks'] == 13
          and frontier['exact_common_rate_comparisons'] == 729
          and frontier['stochastic_test'].startswith('NOT_IMPLEMENTED'))
    bound(CODE[1] / 'check_current.py', frontier['code_sha256'], 'frontier_executed_code')
    recursive = load(LOG / 'recursive/RESULT.json')
    check('recorded_recursive_controls_equal', all(value == '0' for method, value in
          recursive['mean_terminal_normalized_squared_errors'].items() if method != 'myopic_diagnostic')
          and recursive['mean_terminal_normalized_squared_errors']['myopic_diagnostic'] == '9/128')
    bound(CODE[3] / 'check_continuation.py', recursive['code_sha256'], 'recursive_executed_code')
    checkpoint = LOG / 'recursive/CHECKPOINT.json'
    # Original writer hashes in-memory LF text; retain its Windows byte representation too.
    content_hash = hashlib.sha256(checkpoint.read_text(encoding='utf-8').encode()).hexdigest()
    check('recursive_returned_checkpoint_text', content_hash == recursive['checkpoint_sha256'])
    checkpoint_receipt = {'returned_text_sha256': content_hash, 'exact_file_sha256': sha(checkpoint),
                          'meaning': 'Original hash is text UTF8 before default Windows newline translation; original file unchanged.'}
    api = load(LOG / 'recursive_context/RECEIPT.json')
    check('one_complete_api_request', api['status'] == 'COMPLETE' and api['logical_requests'] == 1
          and api['usage']['total_tokens'] == 2320)
    bound(LOG / 'recursive_context/RESPONSE.md', api['exact_file_sha256'], 'api_exact_response')
    check('api_returned_content_hash', hashlib.sha256((LOG / 'recursive_context/RESPONSE.md')
          .read_text(encoding='utf-8').encode()).hexdigest() == api['returned_content_sha256'])
    bound(CODE[0] / 'api_context.py', api['code_sha256'], 'api_executed_code')

    source = OUT / 'source_completion'
    direct_rows = []
    for file in ('RECEIPTS.json', 'INDEX_RECEIPTS.json', 'STATIC_RECEIPTS.json'):
        direct_rows.extend(load(source / file))
    for row in direct_rows:
        if 'sha256' in row:
            suffix = '.response' if row in load(source / 'STATIC_RECEIPTS.json') else '.body'
            bound(source / (row['name'] + suffix), row['sha256'], 'root_source:' + row['name'], row['bytes'])
        if 'decoded_sha256' in row:
            path = source / (row['name'] + '.body')
            bound(path, row['decoded_sha256'], 'root_code_source:' + row['name'], row['decoded_bytes'])
            raw = path.read_bytes()
            check('git_blob:' + row['name'], hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw)
                  .hexdigest() == row['git_blob_sha'])
    check('root_seven_success_two_failed_source_requests', sum(row.get('status') == 200 for row in direct_rows) == 7
          and sum('error' in row for row in direct_rows) == 2)
    check('root_successful_source_body_bytes', sum(row.get('bytes', 0) for row in direct_rows) == 582283)
    tree = load(source / 'code_tree.body')
    check('author_tag_tree_complete', tree['truncated'] is False and len(tree['tree']) == 1620
          and tree['sha'] == '188fe2dd39189c453dbedce4ef845e38befd1654')
    for name in ('DECISION.md', 'CONTINUATION.md', 'SOURCE_COMPLETION_DECISION.md',
                 'DEBATE_SYNTHESIS.md', 'OBJECTIVE_STATUS.md'):
        check('root_scientific_record:' + name, (OUT / name).is_file())
    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    write('DIFF_CHECK.json', {'command': 'git diff --check', 'exit_code': diff.returncode,
                            'stdout': diff.stdout, 'stderr': diff.stderr})
    check('git_diff_check', diff.returncode == 0)
    write('PREDECESSOR_PRESERVATION.json', preservation)
    write('FINAL_INTEGRITY.json', {'passed': True, 'checks': checks,
        'predecessor_entries': len(preservation['checks']),
        'preservation_report_sha256': sha(OUT / 'PREDECESSOR_PRESERVATION.json'),
        'verified_seals': [p.relative_to(LOG).as_posix() for p in seals],
        'checkpoint_hash_semantics': checkpoint_receipt,
        'new_deepseek_calls': 1, 'reported_deepseek_tokens': 2320,
        'root_direct_source_requests': len(direct_rows), 'new_predictive_fits': 0,
        'biological_assay_scalar_decodes': 0, 'scientific_experiments_rerun_by_finalizer': 0,
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
