"""Bind final reviewed inputs and record one numerical process invocation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/organoid_schedule_forecast'
FILES = [
    'log/20261023/organoid_schedule_forecast/PROTOCOL.md',
    'research/organoid_schedule_forecast_20261023/forecast.py',
    'research/organoid_schedule_forecast_20261023/test_isolation.py',
    'research/organoid_schedule_forecast_20261023/execute_once.py',
    'log/20261023/organoid_schedule_forecast/TEST_RECORD_FINAL.json',
    'log/20261023/organoid_schedule_forecast/critic/FINAL_REVIEW_v2.md',
    'log/20261023/organoid_schedule_forecast/source/FINAL_REVIEW.md',
    'log/20261023/organoid_schedule_qualification/root/zenodo_archive.body',
]


if __name__ == '__main__':
    assert not (OUT / 'FREEZE.json').exists() and not (OUT / 'pilot').exists()
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
    (OUT / 'FREEZE.json').write_text(json.dumps(dict(
        utc=datetime.now(timezone.utc).isoformat(), files=hashes), indent=2), encoding='utf-8')
    result = subprocess.run([sys.executable, '-B', str(ROOT / FILES[1])],
                            cwd=ROOT, capture_output=True, text=True)
    (OUT / 'EXECUTION.json').write_text(json.dumps(dict(
        utc=datetime.now(timezone.utc).isoformat(), returncode=result.returncode,
        stdout=result.stdout, stderr=result.stderr), indent=2), encoding='utf-8')
    print(result.stdout)
    print(result.stderr)
    raise SystemExit(result.returncode)
