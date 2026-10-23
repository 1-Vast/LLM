import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone

import numpy
import rdkit
import sklearn

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/ptpc_update_opportunity'
paths = [OUT / 'DEVELOPMENT_BASELINE_PROTOCOL.md', OUT / 'source/LABEL_GATE_SEAL.json',
         OUT / 'source/HCT116_CONDITION_GROUPS.json',
         ROOT / 'log/20261022/generative_repair_renewal/source/archive_followup/S8_IDENTITY_ROWS.json']
paths += [Path(__file__).parent / n for n in ('prepare_baseline.py', 'evaluate_baseline.py', 'test_baseline.py', 'freeze_baseline.py')]
if (OUT / 'BASELINE_PREPARED.npz').exists():
    paths += [OUT / 'BASELINE_PREPARED.npz', OUT / 'BASELINE_PREPARATION.json']
record = {'created_utc': datetime.now(timezone.utc).isoformat(),
          'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'python': sys.version, 'platform': platform.platform(), 'numpy': numpy.__version__,
          'sklearn': sklearn.__version__, 'rdkit': rdkit.__version__, 'seed': 0,
          'bindings': {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
target = OUT / (sys.argv[1] if len(sys.argv) > 1 else 'BASELINE_FREEZE.json')
assert target.parent == OUT and target.suffix == '.json'
assert not target.exists()
target.write_text(json.dumps(record, indent=2), encoding='utf-8')
print('Baseline protocol/code/input binding:', len(paths))
