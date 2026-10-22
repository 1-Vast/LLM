"""Close the completed diagnostic and frontier review without changing evidence."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).resolve().parent
OUT = ROOT / 'log/20261022/cipa_control_information'
FRONTIER = ROOT / 'log/20261022/frontier_mechanism_renewal'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2)


def resolve(name, directory):
    path = Path(name)
    if path.is_absolute():
        return path
    return ROOT / path if (ROOT / path).is_file() else directory / path


def main():
    checks = []

    def check(path, expected, seal):
        checks.append({'seal': seal.name, 'path': path.relative_to(ROOT).as_posix(),
                       'passed': path.is_file() and sha(path) == expected})

    def file_seal(path):
        data = read(path)
        if 'files' in data:
            records = data['files']
            records = records.items() if isinstance(records, dict) else ((r['path'], r['sha256']) for r in records)
        else:
            key = next(k for k in ('path', 'file', 'artifact', 'report', 'independent_file') if k in data)
            records = [(data[key], data['sha256'])]
        for name, expected in records:
            check(resolve(name, path.parent), expected, path)

    for name in ('FREEZE.json', 'FORECAST_SEAL.json', 'INDEPENDENT_DESIGN_SKEPTIC_SEAL.json',
                 'CROSS_REVIEW_SKEPTIC_SEAL.json', 'CROSS_REVIEW_SKEPTIC_FINAL_ADDENDUM_SEAL.json'):
        file_seal(OUT / name)
    forecast = read(OUT / 'FORECAST_SEAL.json')
    check(OUT / 'FREEZE.json', forecast['freeze_sha256'], OUT / 'FORECAST_SEAL.json')
    score = read(OUT / 'SCORE_SEAL.json')
    check(OUT / 'FORECAST_SEAL.json', score['forecast_seal_sha256'], OUT / 'SCORE_SEAL.json')
    check(OUT / 'TERMINAL_SCORES.json', score['scores_sha256'], OUT / 'SCORE_SEAL.json')
    for name in ('INDEPENDENT_INITIAL_SEAL.json', 'ADDENDUM_STRUCTURE_REQUIREMENTS.seal.json',
                 'INDEPENDENT_BIOLOGICAL_SEAL.json', 'CROSS_REPLY_BIOLOGICAL_SEAL.json', 'FRONTIER_EXCHANGE_SEAL.json'):
        file_seal(FRONTIER / name)
    for path in sorted((FRONTIER / 'sources').glob('*.receipt.json')):
        receipt = read(path)
        body = path.with_name(path.name.replace('.receipt.json', '.body'))
        check(body, receipt['sha256'], path)
        checks.append({'path': path.relative_to(ROOT).as_posix(),
                       'passed': receipt['status'] == 200 and body.stat().st_size == receipt['bytes']})
    audit = read(OUT / 'SCORE_INDEPENDENT_AUDIT.json')
    checks.append({'path': 'SCORE_INDEPENDENT_AUDIT.json', 'passed': audit['status'] == 'PASS'
                   and audit['information_gate'] is False and audit['terminal_bundles'] == 959})
    check(CODE / 'audit_results.py', audit['auditor_sha256'], OUT / 'SCORE_INDEPENDENT_AUDIT.json')
    for path in sorted(OUT.glob('*AUDIT*SEAL.json')):
        file_seal(path)
    preservation = read(OUT / 'FINAL_PREDECESSOR_PRESERVATION.json')
    checks.append({'path': 'FINAL_PREDECESSOR_PRESERVATION.json',
                   'passed': preservation['passed'] and len(preservation['checks']) == 6195})
    assert all(row['passed'] for row in checks), [row for row in checks if not row['passed']]
    write('FINAL_INTEGRITY.json', {'passed': True, 'checks': checks,
          'predecessor_entries': 6195, 'predecessor_report_sha256': sha(OUT / 'FINAL_PREDECESSOR_PRESERVATION.json'),
          'full_goal': 'ACTIVE / NOT_ACHIEVED', 'utc': datetime.now(timezone.utc).isoformat()})
    folders = [CODE, OUT, ROOT / 'research/frontier_mechanism_renewal_20261022', FRONTIER]
    records = [{'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)}
               for folder in folders for path in sorted(folder.rglob('*'))
               if path.is_file() and '__pycache__' not in path.parts]
    write('FINAL_FILE_INVENTORY.json', {'files': records, 'excludes_itself': True})
    print(json.dumps({'passed': True, 'seal_checks': len(checks), 'phase_files': len(records), 'predecessors': 6195}))


if __name__ == '__main__':
    main()
