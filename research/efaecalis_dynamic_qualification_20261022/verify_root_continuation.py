"""Final record/integrity checks; no new outcome analysis or source decoding."""
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261022/efaecalis_dynamic_qualification'
PILOT = OUT/'rank_pilot'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    checks = {}
    frozen = load(PILOT/'FREEZE.json')
    for item in frozen['files']:
        checks['frozen:'+item['path']] = hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() == item['sha256']
    result = load(PILOT/'RESULT.json')
    post = load(PILOT/'POSTRUN_VERIFICATION.json')
    tests = load(PILOT/'SYNTHETIC_TESTS.json')
    checks['twelve_synthetic_checks_pass'] = tests['tests'] == 12 and tests['success'] and not tests['source_workbook_opened']
    checks['twenty_two_independent_checks_pass'] = len(post['checks']) == 22 and all(post['checks'].values())
    checks['stop_retained'] = result['status'] == 'STOP_THIS_SOURCE_CONFIGURATION_FOR_FRAMEWORK_EXPANSION'
    checks['all_framework_claims_unproven'] = all(result['claims'][k] == 'NOT_TESTED' for k in ['world_model', 'agent', 'inheritance', 'RSI'])
    checks['no_pilot_API_or_HTTP'] = result['http_requests'] == result['execution_resources']['API_calls'] == 0
    for name in ['DECISION.md', 'rank_pilot/REPORT.md']:
        path = OUT/name
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if not re.match(r'[a-z]+://', target):
                checks['link:'+name+':'+target] = (path.parent/target).resolve().is_file()
    for name in ['rank_pilot.py', 'test_rank_pilot.py', 'verify_rank_pilot_postrun.py', Path(__file__).name]:
        ast.parse(Path(__file__).with_name(name).read_text(encoding='utf-8'))
        checks['parse:'+name] = True
    receipt = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'check_count': len(checks),
               'checks': checks, 'scope': 'record integrity only; no biological or framework success',
               'source_decoding': False, 'http_requests': 0}
    with (OUT/'ROOT_FINAL_VERIFICATION.json').open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'status': receipt['status'], 'checks': len(checks)}))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
