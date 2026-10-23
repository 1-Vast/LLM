"""Freeze source, identity plan, protocol and executable code before label access."""
from datetime import datetime, timezone
import hashlib
import json
from run import ROOT, OUT, SOURCE, identities

assert not (OUT / 'STARTED.json').exists() and not (OUT / 'FREEZE.json').exists()
assert json.loads((OUT / 'PRELABEL_CHECKS.json').read_text())['status'] == 'PASS'
(OUT / 'IDENTITY_PLAN.json').write_text(json.dumps(identities(), indent=2), encoding='utf-8')
paths = [OUT / 'PROTOCOL.md', OUT / 'IDENTITY_PLAN.json', OUT / 'PRELABEL_CHECKS.json', SOURCE]
paths += list((ROOT / 'research/emerald_functional_rule_20261023').glob('*.py'))
record = dict(utc=datetime.now(timezone.utc).isoformat(), biological_values_accessed=False,
    files={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(OUT / 'FREEZE.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(dict(frozen_files=len(paths), utc=record['utc'])))
