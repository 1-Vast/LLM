"""Bind development protocol and code before the first score-value parse."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261023/interaction_error_diagnostic'
CODE = ROOT/'research/interaction_error_diagnostic_20261023'
target = LOG/'RUN_FREEZE.json'
assert not target.exists()
assert not (LOG/'RESULTS.json').exists()
paths = sorted([*LOG.rglob('*.md'), *LOG.rglob('*SEAL.json'), *CODE.rglob('*.py'), LOG/'TEST_OUTPUT.txt'])
snapshot = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
target.write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(), files=snapshot,
                                 phase='Before biological score-value parsing',
                                 goal='ACTIVE / NOT_ACHIEVED'), indent=2), encoding='utf-8')
print(json.dumps(dict(frozen_files=len(snapshot))))
