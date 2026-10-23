"""Bind local phase artifacts; hashes are not scientific validation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/contrast_transport_mechanism'
PRIOR = ROOT / 'log/20261023/replicated_contrast'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(path):
    checks = []
    for name, expected in json.loads(path.read_text())['files'].items():
        checks.append(dict(file=name, matches=sha(ROOT/name) == expected))
    assert all(c['matches'] for c in checks)
    return checks


def main():
    stage = sys.argv[1]
    assert stage in ['freeze', 'verify']
    target = OUT / ('EXECUTION_FREEZE.json' if stage == 'freeze' else 'VERIFICATION.json')
    assert not target.exists()
    checks = verify_manifest(PRIOR / 'VERIFICATION.json')
    if stage == 'freeze':
        for role in ['source', 'critic', 'constructive']:
            assert (OUT/role/'PREFLIGHT.md').exists()
        assert 'OK' in (OUT/'TEST_OUTPUT.txt').read_text(encoding='utf-8-sig')
        assert not (OUT/'PROJECTION_RESULT.json').exists()
    else:
        checks += verify_manifest(OUT/'EXECUTION_FREEZE.json')
    files = sorted(p for p in OUT.rglob('*') if p.is_file())
    files += sorted((ROOT/'research/contrast_transport_mechanism_20261023').rglob('*.py'))
    files += [PRIOR/'CONTRAST_ARRAYS.npz', PRIOR/'SELECTED_PAIR_IDS.json', PRIOR/'CONSTRUCT_IDS.json',
              PRIOR/'VERIFICATION.json']
    record = dict(utc=datetime.now(timezone.utc).isoformat(), stage=stage,
                  files={str(p.relative_to(ROOT)): sha(p) for p in files},
                  checks=checks, failures=sum(not c['matches'] for c in checks),
                  goal='ACTIVE / NOT_ACHIEVED', scope='Local consistency; not scientific validity')
    target.write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(dict(stage=stage, files=len(files), checks=len(checks), failures=record['failures'])))


if __name__ == '__main__':
    main()
