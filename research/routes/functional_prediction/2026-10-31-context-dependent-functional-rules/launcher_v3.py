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
freeze = json.loads((EP/'numeric_freeze_v3.json').read_text())
for name,value in freeze['files'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == value['sha256'],name
admission = json.loads((EP/'review/execution_admission.json').read_text())
assert admission['scientific_code_execution_admitted'] is True
assert admission['freeze_sha256'] == hashlib.sha256((EP/'numeric_freeze_v3.json').read_bytes()).hexdigest()
environment = dict(os.environ)
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    environment[name] = '4'
# Constrain this launcher and inherited children to four available logical CPUs.
import ctypes
from ctypes import wintypes
kernel = ctypes.WinDLL('kernel32',use_last_error=True)
kernel.GetCurrentProcess.restype = wintypes.HANDLE
kernel.GetProcessAffinityMask.argtypes = [wintypes.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]
kernel.SetProcessAffinityMask.argtypes = [wintypes.HANDLE,ctypes.c_size_t]
handle = kernel.GetCurrentProcess()
available,system = ctypes.c_size_t(),ctypes.c_size_t()
assert kernel.GetProcessAffinityMask(handle,ctypes.byref(available),ctypes.byref(system))
bits = [1<<i for i in range(8*ctypes.sizeof(ctypes.c_size_t)) if available.value & (1<<i)]
chosen = sum(bits[:4])
assert kernel.SetProcessAffinityMask(handle,chosen)
started = time.monotonic()
record = {'created_utc':datetime.now(timezone.utc).isoformat(),'timeout_seconds':1800,'threads_per_pool':4,'logical_cpu_affinity_mask':chosen,'stages':[]}
try:
    for stage in ('fit','score'):
        with (EP/f'{stage}_stdout.txt').open('wb') as stdout,(EP/f'{stage}_stderr.txt').open('wb') as stderr:
            remaining = 1800-(time.monotonic()-started)
            if remaining <= 0:
                raise subprocess.TimeoutExpired(stage,1800)
            process = subprocess.run([sys.executable,'-X','utf8',str(EP/'experiment_v2.py'),stage],cwd=EP.parents[3],
                env=environment,stdout=stdout,stderr=stderr,timeout=remaining)
        record['stages'].append({'stage':stage,'returncode':process.returncode,'elapsed_total':time.monotonic()-started})
        if process.returncode:
            break
except subprocess.TimeoutExpired:
    record['timeout']=True
finally:
    record['elapsed_seconds']=time.monotonic()-started
    receipt.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))
