"""Verify explicit phase seals and snapshot this phase without editing originals."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'log/20261023/functional_transition_law'
CODE = ROOT / 'research/functional_transition_law_20261023'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    output = EVIDENCE / 'VERIFICATION.json'
    assert not output.exists(), 'Preserve prior verification'
    checks = []
    for seal in sorted(EVIDENCE.rglob('*.json')):
        if 'seal' not in seal.name.lower():
            continue
        body = json.loads(seal.read_text(encoding='utf-8-sig'))
        entries = body.get('files', body.get('artifacts'))
        if entries is None and 'sha256' in body:
            explicit_path = body.get('file', body.get('artifact'))
            if seal == EVIDENCE / 'constructive/CROSS.seal.json':
                explicit_path = 'log/20261023/functional_transition_law/constructive/CROSS.md'
            if explicit_path is not None:
                entries = [dict(path=explicit_path, sha256=body['sha256'])]
        if isinstance(entries, dict):
            entries = [dict(path=p, sha256=h) for p, h in entries.items()]
        assert isinstance(entries, list), f'Unrecognized seal: {seal}'
        for entry in entries:
            path = Path(entry['path'])
            if not path.is_absolute():
                path = ROOT / path
            actual = digest(path)
            checks.append(dict(seal=str(seal.relative_to(ROOT)),
                               path=str(path.relative_to(ROOT)),
                               match=actual.lower() == entry['sha256'].lower()))
    files = {str(p.relative_to(ROOT)): digest(p)
             for base in (EVIDENCE, CODE) for p in sorted(base.rglob('*'))
             if p.is_file() and p != output}
    report = dict(utc=datetime.now(timezone.utc).isoformat(),
                  goal='ACTIVE / NOT_ACHIEVED', files=files,
                  checks=checks, drift=[c for c in checks if not c['match']],
                  scope='Explicit current phase seals only; no repair or certification of historical global provenance')
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(files), checks=len(checks), drift=report['drift'])))
    assert not report['drift']
