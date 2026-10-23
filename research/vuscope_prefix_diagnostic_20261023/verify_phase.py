"""Verify explicit seals, original phase snapshot and immutable frozen inputs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/vuscope_prefix_diagnostic'
CODE = ROOT/'research/vuscope_prefix_diagnostic_20261023'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pairs(body):
    entries = body.get('files', body.get('artifacts'))
    if isinstance(entries, dict):
        return list(entries.items())
    if isinstance(entries, list):
        return [(e['path'],e['sha256']) for e in entries]
    if 'sha256' in body and ('file' in body or 'artifact' in body or 'path' in body):
        return [(body.get('file', body.get('artifact', body.get('path'))),body['sha256'])]
    raise ValueError('Unrecognized explicit seal schema')


if __name__ == '__main__':
    target = OUT/'VERIFICATION.json'
    assert not target.exists()
    checks = []
    for seal in sorted(OUT.rglob('*.json')):
        if 'seal' not in seal.name.lower() and seal.name != 'FREEZE.json':
            continue
        body = json.loads(seal.read_text(encoding='utf-8-sig'))
        if seal.name == 'PREDICTION_SEAL.json':
            entries = [(str((OUT/'pilot/PREDICTIONS_BEFORE_OUTCOMES.json').relative_to(ROOT)),body['sha256'])]
        else:
            entries = pairs(body)
        for filename, expected in entries:
            path = Path(filename)
            if not path.is_absolute():
                path = ROOT/path
            checks.append(dict(seal=str(seal.relative_to(ROOT)), path=str(path.relative_to(ROOT)),
                               match=digest(path).lower()==expected.lower()))
    previous = ROOT/'log/20261023/functional_transition_law/VERIFICATION.json'
    prior = json.loads(previous.read_text())
    historical = [dict(path=name, match=digest(ROOT/name)==expected) for name,expected in prior['files'].items()]
    snapshot = {str(p.relative_to(ROOT)):digest(p) for base in (OUT,CODE)
                for p in sorted(base.rglob('*')) if p.is_file() and p != target}
    report = dict(utc=datetime.now(timezone.utc).isoformat(), goal='ACTIVE / NOT_ACHIEVED',
                  files=snapshot, seal_checks=checks, preceding_phase_checks=historical,
                  drift=[c for c in checks+historical if not c['match']],
                  scope='Current explicit seals plus preceding55file snapshot; no global historical provenance repair or biological certification')
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(snapshot), seal_checks=len(checks), previous_files=len(historical), drift=report['drift'])))
    assert not report['drift']
