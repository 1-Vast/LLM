"""Verify local frozen bytes and explicit seal bindings; never rerun predictors."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261023/rechallenge_forecast'


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

    prior = ROOT / 'log/20261023/rechallenge_task/VERIFICATION_v2.json'
    for name, digest in json.loads(prior.read_text(encoding='utf-8'))['files'].items():
        check('preceding_snapshot', name, digest)
    for seal in sorted(PHASE.rglob('*.json')):
        if 'seal' not in seal.name.lower() and seal.name != 'FREEZE.json':
            continue
        data = json.loads(seal.read_text(encoding='utf-8-sig'))
        files = data.get('files', {})
        if isinstance(files, dict):
            for name, digest in files.items():
                base = ROOT if (ROOT / name).is_file() else seal.parent
                check(str(seal.relative_to(ROOT)), name, digest, base)
        elif isinstance(files, list):
            for item in files:
                check(str(seal.relative_to(ROOT)), item['path'], item['sha256'])
        name = data.get('report') or data.get('artifact') or data.get('path')
        if name and 'sha256' in data:
            base = ROOT if (ROOT / name).is_file() else seal.parent
            check(str(seal.relative_to(ROOT)), name, data['sha256'], base)
        if seal.name == 'FORECAST_SEAL.json':
            check('prediction_before_scoring', seal.parent / 'FORECASTS.json', data['sha256'])
    output = PHASE / 'VERIFICATION.json'
    if output.exists():
        raise FileExistsError('Preserve existing verification; use a separately named correction.')
    paths = sorted(set(PHASE.rglob('*')) | set((ROOT / 'research/rechallenge_forecast_20261023').rglob('*')))
    snapshot = {str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()}
    report = dict(utc=datetime.now(timezone.utc).isoformat(), files=snapshot,
                  checks=checks, failures=sum(not x['matches'] for x in checks),
                  scope='Local byte snapshot and explicit bindings only; no historical provenance repair',
                  goal='ACTIVE / NOT_ACHIEVED')
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(snapshot), checks=len(checks), failures=report['failures'])))
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
