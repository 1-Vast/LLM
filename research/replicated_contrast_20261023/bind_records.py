"""Local evidence bindings, not a scientific-validity certification."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/replicated_contrast'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    stage = sys.argv[1]
    assert stage in ['pre', 'post']
    target = OUT / ('EXECUTION_PREFLIGHT.json' if stage == 'pre' else 'VERIFICATION.json')
    assert not target.exists()
    checks = []
    if stage == 'pre':
        for role in ['source', 'constructive', 'critic']:
            assert (OUT / role / 'PREFLIGHT.md').exists()
        assert 'OK' in (OUT / 'TEST_OUTPUT.txt').read_text(encoding='utf-8-sig')
        assert not (OUT / 'NUMERICAL_FREEZE.json').exists()
    else:
        for filename in ['EXECUTION_PREFLIGHT.json', 'NUMERICAL_FREEZE.json']:
            binding = json.loads((OUT / filename).read_text())
            for name, expected in binding['files'].items():
                checks.append(dict(file=name, matches=digest(ROOT / name) == expected))
        prior = ROOT / 'log/20261023/rank_reversal_mechanism/VERIFICATION.json'
        checks.append(dict(file=str(prior.relative_to(ROOT)), matches=prior.exists()))
        assert all(c['matches'] for c in checks)
    files = sorted(p for p in OUT.rglob('*') if p.is_file())
    files += sorted((ROOT / 'research/replicated_contrast_20261023').glob('*.py'))
    record = dict(utc=datetime.now(timezone.utc).isoformat(), stage=stage,
                  files={str(p.relative_to(ROOT)): digest(p) for p in files},
                  checks=checks, failures=sum(not c['matches'] for c in checks),
                  scope='Local file binding only; not scientific validation',
                  goal='ACTIVE / NOT_ACHIEVED')
    target.write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(dict(stage=stage, files=len(files), checks=len(checks), failures=record['failures'])))


if __name__ == '__main__':
    main()
