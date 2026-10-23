"""Verify this phase's fixed inputs and prior local snapshot; never rerun forecasts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/public_recovery_task'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    checks = []
    def check(path, expected):
        checks.append(dict(path=str(path), matches=digest(path).lower() == expected.lower()))

    prior = read(ROOT / 'log/20261023/regrowth_data_qualification/VERIFICATION.json')
    for name, expected in prior['files'].items():
        check(ROOT / name, expected)
    for name, expected in read(OUT / 'NUMERIC_FREEZE.json')['files'].items():
        check(ROOT / name, expected)
    check(OUT / 'pilot/PREFIX_FORECASTS.json', read(OUT / 'pilot/PREDICTION_SEAL.json')['sha256'])
    # Verify every explicit artifact/path binding in phase seals. Extra metadata
    # such as chronology or independence assertions is not proved by hashes.
    for path in sorted(OUT.rglob('*.json')):
        if 'seal' not in path.name.lower():
            continue
        seal = read(path)
        if 'artifact' in seal and 'sha256' in seal:
            check(ROOT / seal['artifact'], seal['sha256'])
        if isinstance(seal.get('files'), list):
            for entry in seal['files']:
                if isinstance(entry, dict) and 'path' in entry and 'sha256' in entry:
                    check(ROOT / entry['path'], entry['sha256'])
        elif isinstance(seal.get('files'), dict):
            for name, expected in seal['files'].items():
                candidate = ROOT / name
                if not candidate.exists():
                    candidate = path.parent / name
                check(candidate, expected)
    snapshots = {}
    for directory in (OUT, ROOT / 'research/public_recovery_task_20261023'):
        for path in sorted(directory.rglob('*')):
            if path.is_file() and path.name != 'VERIFICATION.json':
                snapshots[str(path.relative_to(ROOT))] = digest(path)
    result = dict(utc=datetime.now(timezone.utc).isoformat(), files=snapshots,
                  checks=checks, preceding_files=len(prior['files']),
                  failures=sum(not x['matches'] for x in checks),
                  scope='Local snapshot and explicit hash bindings only; not biological truth or global provenance')
    destination = OUT / 'VERIFICATION.json'
    assert not destination.exists(), 'Preserve original verification'
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(snapshots), checks=len(checks), preceding_files=len(prior['files']), failures=result['failures'])))
    assert result['failures'] == 0
