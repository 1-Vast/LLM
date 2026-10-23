"""Execute once and retain actual console/exit metadata for the pre-frozen pilot."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/feedback_law_discovery'


if __name__ == '__main__':
    freeze = json.loads((OUT/'PILOT_FREEZE.json').read_text(encoding='utf-8'))
    for name, expected in freeze['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
    assert not (OUT/'pilot/INITIATED.json').exists(), 'Inspect existing live/terminal run; never restart automatically'
    started = time.perf_counter()
    utc = datetime.now(timezone.utc).isoformat()
    with (OUT/'pilot/CONSOLE.txt').open('w', encoding='utf-8') as console:
        proc = subprocess.Popen([sys.executable, '-B', str(Path(__file__).with_name('pilot_accounted.py'))],
                                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            console.write(line)
            console.flush()
            print(line, end='', flush=True)
        result = proc.wait()
    receipt = dict(utc=utc, ended_utc=datetime.now(timezone.utc).isoformat(), returncode=result,
                   wall_seconds=time.perf_counter()-started, child_pid=proc.pid,
                   status='COMPLETED' if result == 0 else 'FAILED_RETAINED')
    (OUT/'pilot/RUN_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))
    sys.exit(result)
