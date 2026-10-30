"""Launch the single primary process with its frozen 180-second outer timeout."""
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
record_path = root / "primary_outer_execution.json"
if record_path.exists() or (root / "execution_receipt.json").exists():
    raise SystemExit("A primary execution record exists; no automatic replay")
record = {"state": "launching", "timeout_seconds": 180,
          "command": [sys.executable, str(root / "run_mean_gate.py")]}
record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
start = time.monotonic()
try:
    run = subprocess.run(record["command"], cwd=root, capture_output=True,
                         text=True, timeout=180)
    record.update(state="exited", returncode=run.returncode,
                  outer_wall_seconds=time.monotonic() - start)
    (root / "primary_stdout.txt").write_text(run.stdout, encoding="utf-8")
    (root / "primary_stderr.txt").write_text(run.stderr, encoding="utf-8")
    print(run.stdout)
    if run.returncode:
        print(run.stderr, file=sys.stderr)
except subprocess.TimeoutExpired:
    record.update(state="terminated_at_outer_timeout",
                  outer_wall_seconds=time.monotonic() - start)
finally:
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
