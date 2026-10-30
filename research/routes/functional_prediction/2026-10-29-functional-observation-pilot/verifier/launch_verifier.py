import time
LAUNCH_START = time.perf_counter()
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PYTHON = r'D:\anaconda\envs\maestro\python.exe'
receipt_path = HERE / 'launch_receipt.json'
if (HERE / 'execution_receipt.json').exists():
    raise RuntimeError('Execution receipt exists; replay refused')
with receipt_path.open('x', encoding='utf-8') as handle:
    json.dump(dict(state='STARTED_NO_REPLAY', timeout_seconds=180), handle)
environment = os.environ.copy()
environment.update(OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', OMP_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
receipt = dict(timeout_seconds=180, primary_code_or_results_read=False)
try:
    with (HERE / 'stdout.log').open('x', encoding='utf-8') as stdout, (HERE / 'stderr.log').open('x', encoding='utf-8') as stderr:
        process = subprocess.run([PYTHON, str(HERE / 'verify_mean_gate.py')], cwd=HERE, env=environment,
                                 stdout=stdout, stderr=stderr, timeout=180, check=False)
    receipt.update(state='COMPLETED_NO_REPLAY', returncode=process.returncode)
except subprocess.TimeoutExpired:
    receipt.update(state='TIMEOUT_NO_REPLAY', outcome='INCONCLUSIVE')
except Exception as error:
    receipt.update(state='FAILED_NO_REPLAY', outcome='INCONCLUSIVE', error=repr(error))
finally:
    receipt['outer_wall_seconds_including_setup'] = time.perf_counter() - LAUNCH_START
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
