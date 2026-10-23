"""Check the preceding snapshot, new HTTP bodies, and sealed review artifacts."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261023/organoid_schedule_qualification'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []

    def check(label, name, expected, base=ROOT):
        path = Path(name)
        if not path.is_absolute():
            path = base / path
        actual = sha(path) if path.is_file() else None
        checks.append(dict(binding=label, path=str(path), expected=expected,
                           actual=actual, matches=actual == expected.lower()))

    prior = ROOT / 'log/20261023/rechallenge_forecast/VERIFICATION.json'
    for name, digest in json.loads(prior.read_text(encoding='utf-8'))['files'].items():
        check('preceding_snapshot', name, digest)
    for record in sorted(PHASE.rglob('*.json')):
        if not record.name.endswith('.receipt.json') and 'seal' not in record.name.lower():
            continue
        data = json.loads(record.read_text(encoding='utf-8-sig'))
        if record.name.endswith('.receipt.json') and 'sha256' in data:
            check('HTTP_body', str(record).replace('.receipt.json', '.body'), data['sha256'])
        if 'seal' not in record.name.lower():
            continue
        files = data.get('files', {})
        if isinstance(files, dict):
            for name, digest in files.items():
                check(record.name, name, digest, ROOT if (ROOT / name).is_file() else record.parent)
        elif isinstance(files, list):
            for item in files:
                check(record.name, item['path'], item['sha256'])
        name = data.get('report') or data.get('artifact') or data.get('path')
        if name and 'sha256' in data:
            check(record.name, name, data['sha256'], ROOT if (ROOT / name).is_file() else record.parent)
        for name, digest in data.get('inputs', {}).items():
            check(record.name + ':input', name, digest)
    paths = sorted(set(PHASE.rglob('*')) | set((ROOT / 'research/organoid_schedule_qualification_20261023').rglob('*')))
    snapshot = {str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()}
    report = dict(utc=datetime.now(timezone.utc).isoformat(), files=snapshot,
                  checks=checks, failures=sum(not x['matches'] for x in checks),
                  scope='Local bytes, HTTP receipts and explicit seals; not biological independence or global provenance',
                  goal='ACTIVE / NOT_ACHIEVED')
    target = PHASE / 'VERIFICATION.json'
    assert not target.exists()
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(snapshot), checks=len(checks), failures=report['failures'])))
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
