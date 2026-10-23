"""Append-only access/prediction contracts for the late-state experiment."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone

import numpy
import sklearn

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/ptpc_late_information'
OLD = ROOT / 'log/20261022/ptpc_update_opportunity'
stage = sys.argv[1]
assert stage in ('ACCESS', 'PREDICTION')
target = OUT / (stage + '_FREEZE.json')
assert not target.exists()
original = json.loads((OLD / 'BASELINE_PREDICTION_FREEZE.json').read_text('utf-8'))
for name, expected in original['bindings'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
paths = [OUT / 'PROTOCOL.md', OUT / 'START.md', OUT / 'review/PROTOCOL_CRITIC.md',
         OLD / 'BASELINE_PREDICTION_FREEZE.json', OLD / 'BASELINE_PREPARED.npz',
         OLD / 'BASELINE_PREPARATION.json',
         ROOT / 'log/20261022/generative_repair_renewal/source/archive_followup/S8_IDENTITY_ROWS.json']
paths += sorted(Path(__file__).parent.glob('*.py'))
assert any(p.name == 'prepare_late.py' for p in paths)
if stage == 'PREDICTION':
    access = json.loads((OUT / 'ACCESS_FREEZE.json').read_text('utf-8'))
    for name, expected in access['bindings'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    paths += [OUT / 'ACCESS_FREEZE.json', OUT / 'LATE_PREPARED.npz', OUT / 'PREPARATION.json']
record = {'stage': stage, 'created_utc': datetime.now(timezone.utc).isoformat(),
          'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'python': sys.version, 'platform': platform.platform(), 'numpy': numpy.__version__,
          'sklearn': sklearn.__version__, 'seed': 0,
          'bindings': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
target.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(stage, 'frozen', len(record['bindings']), 'inputs')
