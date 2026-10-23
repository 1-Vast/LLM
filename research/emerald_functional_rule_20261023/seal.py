"""Bind final artifacts and verify prelabel and prior-phase byte seals."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/emerald_functional_rule'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

checks = {}
for name in ['log/20261023/dose_update_qualification/VERIFICATION.json',
             'log/20261023/emerald_functional_rule/FREEZE.json']:
    prior = json.loads((ROOT/name).read_text())['files']
    drift = [p for p, h in prior.items() if digest(ROOT/p) != h]
    checks[name] = dict(files=len(prior), drift=drift)
    assert not drift
assert json.loads((OUT / 'RESULT_AUDIT.json').read_text())['status'] == 'PASS'
paths = [p for directory in [OUT, ROOT / 'research/emerald_functional_rule_20261023']
         for p in directory.rglob('*') if p.is_file() and p.name != 'VERIFICATION.json']
record = dict(utc=datetime.now(timezone.utc).isoformat(), checks=checks,
    goal='ACTIVE / NOT_ACHIEVED', phase='PROGRESS / STOP_FIXED_SINGLE_PLUS_ONE_ANCHOR',
    files={p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)})
target = OUT / 'VERIFICATION.json'
target.write_text(json.dumps(record, indent=2), encoding='utf-8')
assert all(digest(ROOT/p) == h for p, h in record['files'].items())
print(json.dumps(dict(files=len(paths), drift=0, prior_checks=checks)))
