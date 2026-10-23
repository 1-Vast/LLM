"""Verify explicit current seals and preceding phase snapshots, without changes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/update_strategy_renewal'
CODE = ROOT/'research/update_strategy_renewal_20261023'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    target = OUT/'VERIFICATION.json'
    assert not target.exists()
    checks = []
    for seal in sorted(OUT.rglob('*.json')):
        if 'seal' not in seal.name.lower() and seal.name != 'PAIRED_CREDIT_FREEZE.json':
            continue
        body = json.loads(seal.read_text(encoding='utf-8-sig'))
        entries = body.get('files', body.get('artifacts'))
        if seal == OUT/'constructive/CROSS.seal.json':
            entries = [dict(path=str((OUT/'constructive/CROSS.md').relative_to(ROOT)), sha256=body['sha256'])]
        elif isinstance(entries, dict):
            if seal == OUT/'source/CROSS_SEAL.json':
                entries = [dict(path=str((seal.parent/p).relative_to(ROOT)), sha256=h) for p,h in entries.items()]
            else:
                entries = [dict(path=p, sha256=h) for p,h in entries.items()]
        elif entries is None and 'sha256' in body:
            path = body.get('path',body.get('file',body.get('artifact')))
            assert path is not None
            entries = [dict(path=path, sha256=body['sha256'])]
        assert isinstance(entries, list), str(seal)
        for entry in entries:
            path = Path(entry['path'])
            if not path.is_absolute():
                path = ROOT/path
            checks.append(dict(seal=str(seal.relative_to(ROOT)), path=str(path.relative_to(ROOT)),
                               match=digest(path).lower()==entry['sha256'].lower()))
    historical = []
    for phase in ('vuscope_prefix_diagnostic','functional_transition_law'):
        previous = ROOT/f'log/20261023/{phase}/VERIFICATION.json'
        hashes = json.loads(previous.read_text())['files']
        historical.extend(dict(phase=phase,path=name,match=digest(ROOT/name)==expected) for name,expected in hashes.items())
    files = {str(p.relative_to(ROOT)):digest(p) for base in (OUT,CODE) for p in sorted(base.rglob('*'))
             if p.is_file() and p!=target}
    report = dict(utc=datetime.now(timezone.utc).isoformat(), goal='ACTIVE / NOT_ACHIEVED',
                  files=files,seal_checks=checks,preceding_phase_checks=historical,
                  drift=[c for c in checks+historical if not c['match']],
                  scope='Explicit current seals and preceding68/55file snapshots; no global provenance repair, biological measurement or independent-generalization certification')
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(files),seal_checks=len(checks),preceding_files=len(historical),drift=report['drift'])))
    assert not report['drift']
