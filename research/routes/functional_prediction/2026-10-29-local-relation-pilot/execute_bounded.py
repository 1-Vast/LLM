"""Run each admitted implementation once with sampled CPU/RSS and wall guards."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

import psutil

HERE = Path(__file__).resolve().parent
kind = sys.argv[1]
assert kind in ("primary", "independent")
script = HERE / ("run_primary.py" if kind == "primary" else "run_independent.py")
receipt_path = HERE / f"{kind}_execution.json"
assert not receipt_path.exists(), "Existing execution is not permission to retry"
receipt = {"status": "starting", "script": str(script), "automatic_retry": False,
           "cpu_cap_seconds": 120, "rss_guard_bytes": 1073741824, "wall_cap_seconds": 180,
           "output_cap_bytes": 50000000, "sampled_memory_is_hard_OS_quota": False}
receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
environment = dict(os.environ)
environment.update(OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
start = time.monotonic()
peak_rss, max_cpu, stopped = 0, 0.0, None
with (HERE / f"{kind}_stdout.txt").open("x", encoding="utf-8") as stdout, (HERE / f"{kind}_stderr.txt").open("x", encoding="utf-8") as stderr:
    process = subprocess.Popen([sys.executable, str(script)], cwd=HERE, env=environment, stdout=stdout, stderr=stderr,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    watched = psutil.Process(process.pid)
    while process.poll() is None:
        try:
            peak_rss = max(peak_rss, watched.memory_info().rss)
            timing = watched.cpu_times()
            max_cpu = max(max_cpu, timing.user + timing.system)
        except psutil.NoSuchProcess:
            break
        if peak_rss > 1073741824 or max_cpu > 120 or time.monotonic() - start > 180:
            stopped = "resource_guard"
            process.kill()
            break
        time.sleep(0.02)
    code = process.wait(timeout=10)
output_files = [p for p in HERE.glob(f"{kind}_*") if p.is_file()]
output_bytes = sum(p.stat().st_size for p in output_files)
if output_bytes > 50000000:
    stopped = "output_cap_exceeded"
receipt.update(status="completed" if code == 0 and stopped is None else "failed", pid=process.pid, exit_code=code,
               wall_seconds=time.monotonic() - start, sampled_peak_rss_bytes=peak_rss,
               sampled_max_cpu_seconds=max_cpu, output_bytes=output_bytes, stopped=stopped)
receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False))
sys.exit(0 if receipt["status"] == "completed" else 1)
