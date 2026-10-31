"""One admitted comparison matrix under one hard wall-clock budget."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

EP = Path(__file__).resolve().parent
receipt = EP/'launch_receipt.json'
assert not receipt.exists(), 'No automatic rerun'
freeze = json.loads((EP/'numeric_freeze_v1.json').read_text())
for name,value in freeze['files'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == value['sha256'],name
admission = json.loads((EP/'review/execution_admission.json').read_text())
assert admission['scientific_code_execution_admitted'] is True
assert admission['freeze_sha256'] == hashlib.sha256((EP/'numeric_freeze_v1.json').read_bytes()).hexdigest()
environment = dict(os.environ)
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    environment[name] = '4'
started = time.monotonic()
record = {'created_utc':datetime.now(timezone.utc).isoformat(),'timeout_seconds':1800,'threads':4,'stages':[]}
try:
    for stage in ('fit','score'):
        with (EP/f'{stage}_stdout.txt').open('wb') as stdout,(EP/f'{stage}_stderr.txt').open('wb') as stderr:
            process = subprocess.run([sys.executable,'-X','utf8',str(EP/'experiment.py'),stage],cwd=EP.parents[3],
                env=environment,stdout=stdout,stderr=stderr,timeout=max(1,1800-(time.monotonic()-started)))
        record['stages'].append({'stage':stage,'returncode':process.returncode,'elapsed_total':time.monotonic()-started})
        if process.returncode:
            break
except subprocess.TimeoutExpired:
    record['timeout']=True
finally:
    record['elapsed_seconds']=time.monotonic()-started
    receipt.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))
