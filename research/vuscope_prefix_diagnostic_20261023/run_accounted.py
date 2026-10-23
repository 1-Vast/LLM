"""Accounting-only wrapper version retaining the previously reviewed wrapper."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
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
    assert not (OUT/'FREEZE.json').exists(), 'Do not overwrite/repeat a frozen run'
    # Explicit final reviewer artifacts; do not infer scientific approval from filenames.
    reviews = [OUT/'critic/FINAL_CODE_REVIEW.md', OUT/'source/FINAL_CODE_BINDING_REVIEW.md']
    seals = [p.with_suffix('.seal.json') for p in reviews]
    for seal in seals:
        body = json.loads(seal.read_text(encoding='utf-8-sig'))
        entries = body.get('files', body.get('artifacts'))
        if isinstance(entries, dict):
            entries = [dict(path=p, sha256=h) for p,h in entries.items()]
        for entry in entries:
            path = Path(entry['path'])
            if not path.is_absolute():
                path = ROOT/path
            assert digest(path).lower() == entry['sha256'].lower(), str(path)
    paths = [OUT/'PROTOCOL.md', OUT/'SCHEDULE.json', OUT/'SCHEMA_METADATA_ONLY.json',
             OUT/'PROTOCOL_METADATA.json', OUT/'PREFIX_EXPOSURE_FAILURE.md',
             OUT/'EXPOSURE_SCOPE_ADDENDUM.md', OUT/'PRE_REVIEW_REPAIRS.md',
             CODE/'pilot.py', CODE/'test_pilot.py', CODE/'run_frozen.py', Path(__file__),
             *reviews, *seals]
    freeze = dict(utc=datetime.now(timezone.utc).isoformat(),
                  files={str(p.relative_to(ROOT)):digest(p) for p in paths},
                  python=sys.version, numpy=numpy.__version__, scipy=scipy.__version__,
                  archive_sha256=digest(ROOT/'log/20261023/functional_transition_law/root_sources/release.zip.body'),
                  environment={'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','MKL_NUM_THREADS':'2'},
                  amendment='Only accounting wrapper adds final reviews/exposure scope; scientific pilot and protocol unchanged')
    (OUT/'FREEZE.json').write_text(json.dumps(freeze, indent=2), encoding='utf-8')
    environment = os.environ.copy()
    environment.update(freeze['environment'])
    started = time.perf_counter()
    with (OUT/'pilot_console.txt').open('w', encoding='utf-8') as console:
        result = subprocess.run([sys.executable,'-B',str(CODE/'pilot.py')], cwd=ROOT,
                                env=environment, stdout=console, stderr=subprocess.STDOUT)
    receipt = dict(utc=datetime.now(timezone.utc).isoformat(), returncode=result.returncode,
                   seconds=time.perf_counter()-started, command=[sys.executable,'-B',str(CODE/'pilot.py')])
    (OUT/'EXECUTION.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))
    raise SystemExit(result.returncode)
