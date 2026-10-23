"""Freeze reviewed inputs, then retain the single diagnostic execution receipt."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/public_recovery_task'
names = [
    'log/20261023/public_recovery_task/NUMERIC_PROTOCOL.md',
    'research/public_recovery_task_20261023/weekly_diagnostic.py',
    'log/20261023/public_recovery_task/root/count_header_source.body',
    'log/20261023/public_recovery_task/critic/CODE_PRE_REVIEW.md',
    'log/20261023/public_recovery_task/critic/CODE_PRE_REVIEW.seal.json',
    'log/20261023/public_recovery_task/source/CROSS.md',
    'log/20261023/public_recovery_task/source/CROSS_RESPONSE_ADDENDUM.md',
    'log/20261023/public_recovery_task/critic/NUMERIC_PRE_REVIEW.md',
]
freeze = OUT / 'NUMERIC_FREEZE.json'
assert not freeze.exists(), 'Preserve existing freeze; do not rerun'
assert not (OUT / 'pilot').exists(), 'Preserve partial outputs; investigate separately'
files = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}
freeze.write_text(json.dumps(dict(files=files, utc=datetime.now(timezone.utc).isoformat()), indent=2), encoding='utf-8')
run = subprocess.run([sys.executable, '-B', str(ROOT / names[1])], cwd=ROOT, capture_output=True, text=True)
(OUT / 'NUMERIC_EXECUTION.json').write_text(json.dumps(dict(
    returncode=run.returncode, stdout=run.stdout, stderr=run.stderr,
    utc=datetime.now(timezone.utc).isoformat(), command=[sys.executable, '-B', names[1]]), indent=2), encoding='utf-8')
print(run.stdout)
print(run.stderr)
sys.exit(run.returncode)
