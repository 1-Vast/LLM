"""Bind protocol and executable sources before numerical access."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/cdk_middle_feedback'
paths = [OUT / 'NUMERICAL_PROTOCOL.md', *sorted(Path(__file__).parent.glob('*.py'))]
record = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'python': sys.version, 'platform': platform.platform(), 'numpy': numpy.__version__,
          'openpyxl': openpyxl.__version__, 'seed': 'deterministic fits; synthetic tests use 42',
          'bindings': {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
target = OUT / (sys.argv[1] if len(sys.argv) > 1 else 'FREEZE.json')
assert target.parent == OUT and target.suffix == '.json'
assert not target.exists()
target.write_text(json.dumps(record, indent=2), encoding='utf-8')
print('Protocol and code frozen:', len(paths), 'files')
