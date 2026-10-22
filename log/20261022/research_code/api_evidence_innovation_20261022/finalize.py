"""Seal direct-API experiment receipts, independent drafts and chemical audit."""
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
    checks.append({'name': '1186_prior_files_unchanged', 'passed': prior['passed'] and len(prior['checks']) == 1186})
    checks.append({'name': 'prior_inventory_hashes', 'passed': prior['manifest_sha256'] == read('BASELINE_PRESERVATION.json')['manifest_sha256']})
    expected = {
        'mechanism': '219b9ebc8e91bb454296e7835d6474c5df485818334399bb5c9440b43da89cad',
        'skeptic': '5425f81e3ce2305f5a901da957085bd317d674aa9d320db39f50f41ad1b68460',
        'data': '693e769ab26a39b085cc9095c9a95d87388d00deaf0bb6b30176d9e95aa96147'}
    usage = Counter()
    for role, digest in expected.items():
        checks.append({'name': 'sealed_independent:' + role, 'passed': sha(LOG / role / 'INDEPENDENT.md') == digest})
        started, receipt = read(role + '/STARTED.json'), read(role + '/RECEIPT.json')
        checks.append({'name': 'prompt_and_code:' + role, 'passed': started['prompt_sha256'] == sha(LOG / role / 'PROMPT.md')
                       and started['script_sha256'] == sha(ROOT / 'research/api_evidence_innovation_20261022/call_provider.py')})
        checks.append({'name': 'response:' + role, 'passed': receipt['status'] == 'RESPONSE_RETAINED'
                       and receipt['response_sha256'] == sha(LOG / role / 'RESPONSE.md')
                       and not receipt['generated_code_executed']})
        usage.update({key: value for key, value in receipt['usage'].items() if isinstance(value, int)})
    checks.append({'name': 'three_calls_43483_tokens', 'passed': usage['calls'] == 3 and usage['total_tokens'] == 43483})
    for name in ('mechanism/CROSS.md', 'skeptic/CROSS.md', 'data/CROSS_MECHANISM.md',
                 'data/CROSS_SKEPTIC_AND_CHEMISTRY.md', 'data/REPLIES_AND_RECOMMENDATION.md'):
        checks.append({'name': 'actual_cross:' + name, 'passed': (LOG / name).stat().st_size > 1000})
    statuses = Counter()
    for index in range(47):
        name = 'chemical_proxy/request_' + str(index).zfill(2)
        receipt = read(name + '.json')
        statuses[receipt['status']] += 1
        body = LOG / (name + '.body')
        checks.append({'name': 'primary_API:' + str(index), 'passed': sha(body) == receipt['sha256'] and body.stat().st_size == receipt['bytes']})
    checks.append({'name': '47_HTTP_not_48', 'passed': dict(statuses) == {200: 46, 404: 1}})
    audit = read('data/CHEMICAL_PROXY_AUDIT.json')
    checks.append({'name': '748_independent_chemical_checks', 'passed': audit['checks'] == 748 and not audit['failures']
                   and audit['resolved_proxies'] == 45 and audit['parent_scaffold_components'] == 39
                   and not audit['source_material_identity_authenticated']})
    menu = read('data/TGGATES_EIGHT_HOUR_MENU.json')
    checks.append({'name': '8h_menu_freeze', 'passed': menu['frozen_inputs']['protocol_sha256'] == sha(LOG / 'data/TGGATES_EIGHT_HOUR_MENU_PROTOCOL.md')
                   and menu['frozen_inputs']['script_sha256'] == sha(ROOT / 'research/api_evidence_innovation_20261022/data_eight_hour_menu.py')})
    code = ROOT / 'research/api_evidence_innovation_20261022'
    files = sorted(code.glob('*.py'))
    for path in files:
        ast.parse(path.read_text(encoding='utf-8-sig'))
    diff = subprocess.run(['git', 'diff', '--check', '--', str(code.relative_to(ROOT)), str(LOG.relative_to(ROOT)),
                           'research/REPORT.md', 'log/README.md'], cwd=ROOT, capture_output=True, text=True)
    checks.append({'name': 'scoped_diff_check', 'passed': diff.returncode == 0})
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'passed': all(row['passed'] for row in checks),
              'checks': checks, 'prior_files': 1186, 'provider_usage': dict(usage),
              'HTTP_statuses': dict(statuses), 'python_files_parsed': len(files), 'new_biological_fits': 0,
              'future_responses_opened': False, 'diff_stdout': diff.stdout, 'diff_stderr': diff.stderr}
    with (LOG / 'FINAL_INTEGRITY.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    if not result['passed']:
        raise RuntimeError('Final integrity failed')
    paths = sorted(path for folder in (LOG, code) for path in folder.rglob('*') if path.is_file()
                   and path.name != 'FINAL_FILE_INVENTORY.json')
    with (LOG / 'FINAL_FILE_INVENTORY.json').open('x', encoding='utf-8') as stream:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'files': [
            {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)} for path in paths]}, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(checks), 'prior_files': 1186, 'phase_files': len(paths)}))


if __name__ == '__main__':
    main()
