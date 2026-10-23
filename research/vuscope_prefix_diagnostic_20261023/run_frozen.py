"""Freeze review-bound source files, run once, retain stdout/stderr and exit status."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy
import scipy

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/vuscope_prefix_diagnostic'
CODE = ROOT / 'research/vuscope_prefix_diagnostic_20261023'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    assert not (OUT/'FREEZE.json').exists(), 'Do not rerun or overwrite freeze'
    reviews = [OUT/role/'PRE_EXECUTION_REVIEW.md' for role in ('critic', 'source')]
    assert all(p.exists() for p in reviews), 'Need concrete code/protocol reviews'
    paths = [OUT/'PROTOCOL.md', OUT/'SCHEDULE.json', OUT/'SCHEMA_METADATA_ONLY.json',
             OUT/'PROTOCOL_METADATA.json', OUT/'PREFIX_EXPOSURE_FAILURE.md',
             CODE/'pilot.py', CODE/'test_pilot.py', Path(__file__), *reviews]
    paths += sorted(OUT.glob('*/PRE_EXECUTION_REVIEW*seal.json'))
    assert len(list(OUT.glob('*/PRE_EXECUTION_REVIEW*seal.json'))) == 2
    freeze = dict(utc=datetime.now(timezone.utc).isoformat(),
                  files={str(p.relative_to(ROOT)):digest(p) for p in paths},
                  python=platform.python_version(), numpy=numpy.__version__, scipy=scipy.__version__,
                  archive_sha256=digest(ROOT/'log/20261023/functional_transition_law/root_sources/release.zip.body'),
                  environment={'OMP_NUM_THREADS':'2', 'OPENBLAS_NUM_THREADS':'2', 'MKL_NUM_THREADS':'2'})
    (OUT/'FREEZE.json').write_text(json.dumps(freeze, indent=2), encoding='utf-8')
    environment = os.environ.copy()
    environment.update(freeze['environment'])
    started = time.perf_counter()
    with (OUT/'pilot_console.txt').open('w', encoding='utf-8') as console:
        result = subprocess.run([sys.executable, '-B', str(CODE/'pilot.py')], cwd=ROOT,
                                env=environment, stdout=console, stderr=subprocess.STDOUT)
    receipt = dict(utc=datetime.now(timezone.utc).isoformat(), returncode=result.returncode,
                   seconds=time.perf_counter()-started, command=[sys.executable,'-B',str(CODE/'pilot.py')])
    (OUT/'EXECUTION.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))
    raise SystemExit(result.returncode)
