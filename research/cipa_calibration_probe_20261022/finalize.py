"""Verify frozen inputs and predecessor preservation; inventory only on request."""
import argparse
import importlib.util
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/cipa_calibration_probe'
CODE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('preserve', CODE / 'preserve.py')
preserve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preserve)

def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2)

def verify():
    result = preserve.verify()
    assert result['passed'] and len(result['checks']) == 6093
    write('FINAL_PREDECESSOR_PRESERVATION.json', result)
    print(json.dumps({'passed': True, 'predecessors': len(result['checks'])}), flush=True)

def inventory():
    checks = []
    for name in ('FREEZE.json', 'FORECAST_SEAL.json'):
        seal = json.loads((OUT / name).read_text())
        for path, expected in seal['files'].items():
            resolved = ROOT / path if name == 'FREEZE.json' else OUT / path
            checks.append({'seal': name, 'path': path, 'passed': preserve.sha(resolved) == expected})
    score = json.loads((OUT / 'SCORE_SEAL.json').read_text())
    checks.append({'path': 'TERMINAL_SCORES.json', 'passed': preserve.sha(OUT / 'TERMINAL_SCORES.json') == score['scores_sha256']})
    checks.append({'path': 'FORECAST_SEAL.json', 'passed': preserve.sha(OUT / 'FORECAST_SEAL.json') == score['forecast_seal_sha256']})
    literature = ROOT / 'log/20261022/frontier_transfer'
    for receipt_path in sorted((literature / 'sources').glob('*.receipt.json')):
        receipt = json.loads(receipt_path.read_text())
        body = receipt_path.with_name(receipt_path.name.replace('.receipt.json', '.body'))
        checks.append({'path': body.relative_to(ROOT).as_posix(), 'passed': receipt['status'] == 200 and body.stat().st_size == receipt['bytes'] and preserve.sha(body) == receipt['sha256']})
    for seal_name, report_key in [('INDEPENDENT_PRIMARY_SEAL.json', 'independent_file'), ('INDEPENDENT_OPPONENT_SEAL.json', 'report'), ('INDEPENDENT_APPLICATION_SEAL.json', 'independent_file')]:
        seal = json.loads((literature / seal_name).read_text())
        checks.append({'path': seal[report_key], 'passed': preserve.sha(ROOT / seal[report_key]) == seal['sha256']})
    for record in json.loads((literature / 'ADDENDUM_2026_SEAL.json').read_text())['files']:
        checks.append({'path': record['path'], 'passed': preserve.sha(ROOT / record['path']) == record['sha256']})
    for record in json.loads((literature / 'PRIMARY_DEBATE_SEAL.json').read_text())['files']:
        checks.append({'path': record['path'], 'passed': preserve.sha(ROOT / record['path']) == record['sha256']})
    independent_audit = json.loads((OUT / 'SCORE_INDEPENDENT_AUDIT.json').read_text())
    checks.append({'path': 'SCORE_INDEPENDENT_AUDIT.json', 'passed': independent_audit['status'] == 'PASS' and independent_audit['actual_head_fits'] == 975})
    assert all(c['passed'] for c in checks)
    write('FINAL_INTEGRITY.json', {'passed': True, 'checks': checks, 'predecessors': 6093,
          'predecessor_preservation_sha256': preserve.sha(OUT / 'FINAL_PREDECESSOR_PRESERVATION.json'),
          'full_goal': 'ACTIVE / NOT_ACHIEVED', 'utc': datetime.now(timezone.utc).isoformat()})
    dirs = [CODE, OUT, ROOT / 'research/frontier_transfer_20261022', ROOT / 'log/20261022/frontier_transfer']
    rows = [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': preserve.sha(p)}
            for folder in dirs for p in sorted(folder.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    write('FINAL_FILE_INVENTORY.json', {'files': rows, 'excludes_itself': True})
    print(json.dumps({'passed': True, 'seal_checks': len(checks), 'phase_files': len(rows)}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['verify', 'inventory'])
    args = parser.parse_args()
    {'verify': verify, 'inventory': inventory}[args.phase]()
