import ctypes as C
from ctypes import wintypes as W
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
K=C.WinDLL('kernel32',use_last_error=True)
P=C.WinDLL('psapi',use_last_error=True)
SIZE=C.c_size_t


class BasicLimits(C.Structure):
    _fields_=[('PerProcessUserTimeLimit',C.c_int64),('PerJobUserTimeLimit',C.c_int64),
              ('LimitFlags',W.DWORD),('MinimumWorkingSetSize',SIZE),('MaximumWorkingSetSize',SIZE),
              ('ActiveProcessLimit',W.DWORD),('Affinity',SIZE),('PriorityClass',W.DWORD),('SchedulingClass',W.DWORD)]


class IO(C.Structure):
    _fields_=[(n,C.c_uint64) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount',
                                      'ReadTransferCount','WriteTransferCount','OtherTransferCount')]


class ExtendedLimits(C.Structure):
    _fields_=[('BasicLimitInformation',BasicLimits),('IoInfo',IO),('ProcessMemoryLimit',SIZE),
              ('JobMemoryLimit',SIZE),('PeakProcessMemoryUsed',SIZE),('PeakJobMemoryUsed',SIZE)]


class Memory(C.Structure):
    _fields_=[('cb',W.DWORD),('PageFaultCount',W.DWORD),('PeakWorkingSetSize',SIZE),('WorkingSetSize',SIZE),
              ('QuotaPeakPagedPoolUsage',SIZE),('QuotaPagedPoolUsage',SIZE),
              ('QuotaPeakNonPagedPoolUsage',SIZE),('QuotaNonPagedPoolUsage',SIZE),
              ('PagefileUsage',SIZE),('PeakPagefileUsage',SIZE),('PrivateUsage',SIZE)]


K.CreateJobObjectW.argtypes=[C.c_void_p,W.LPCWSTR]; K.CreateJobObjectW.restype=W.HANDLE
K.SetInformationJobObject.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.DWORD]
K.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE]
K.TerminateJobObject.argtypes=[W.HANDLE,W.UINT]
K.CloseHandle.argtypes=[W.HANDLE]
K.GetProcessTimes.argtypes=[W.HANDLE,C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME)]
P.GetProcessMemoryInfo.argtypes=[W.HANDLE,C.POINTER(Memory),W.DWORD]


def checked(value):
    if not value:
        raise C.WinError(C.get_last_error())
    return value


def times(handle):
    a,b,c,d=W.FILETIME(),W.FILETIME(),W.FILETIME(),W.FILETIME()
    checked(K.GetProcessTimes(handle,C.byref(a),C.byref(b),C.byref(c),C.byref(d)))
    return ((c.dwHighDateTime<<32)+c.dwLowDateTime+(d.dwHighDateTime<<32)+d.dwLowDateTime)/1e7


def memory(handle):
    m=Memory();m.cb=C.sizeof(m)
    checked(P.GetProcessMemoryInfo(handle,C.byref(m),m.cb))
    return m


def main():
    # Exclusive marker prohibits another numerical launch, including accidental retries.
    fd=os.open(HERE/'execution_started.json',os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    with os.fdopen(fd,'w') as f:
        json.dump(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),once=True),f)
    job=checked(K.CreateJobObjectW(None,None))
    limits=ExtendedLimits()
    limits.BasicLimitInformation.PerProcessUserTimeLimit=120*10000000
    limits.BasicLimitInformation.ActiveProcessLimit=1
    limits.BasicLimitInformation.LimitFlags=0x2|0x8|0x100|0x2000
    limits.ProcessMemoryLimit=1073741824
    checked(K.SetInformationJobObject(job,9,C.byref(limits),C.sizeof(limits)))
    start=time.monotonic();start_cpu=time.process_time()
    env=os.environ.copy()
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        env[key]='1'
    process=None
    receipt=dict(hard_job_created=True,job_process_memory_cap=1073741824,
                 job_user_cpu_cap_seconds=120,active_process_limit=1,
                 cpu_monitor_includes_worker_kernel_and_guardian=True,
                 monitor_period_seconds=0.01,output_guard_trigger_bytes=49000000,
                 no_network_calls=True,no_installation=True,run_count=1)
    peak_ws=peak_private=worker_cpu=0
    termination=None
    try:
        with (HERE/'stdout.txt').open('wb') as out,(HERE/'stderr.txt').open('wb') as err:
            process=subprocess.Popen([sys.executable,str(HERE/'compute.py')],cwd=HERE,env=env,
                                     stdout=out,stderr=err,creationflags=0x08000000)
            checked(K.AssignProcessToJobObject(job,W.HANDLE(process._handle)))
            (HERE/'execution_gate').write_text('job assigned before release',encoding='utf-8')
            while True:
                m=memory(W.HANDLE(process._handle))
                peak_ws=max(peak_ws,m.PeakWorkingSetSize)
                peak_private=max(peak_private,m.PeakPagefileUsage,m.PrivateUsage)
                worker_cpu=times(W.HANDLE(process._handle))
                output_size=sum(p.stat().st_size for p in HERE.iterdir() if p.is_file())
                total_cpu=worker_cpu+time.process_time()-start_cpu
                if total_cpu>=120:
                    termination='total_CPU_limit'
                elif output_size>=49000000:
                    termination='output_resource_gate'
                elif m.PrivateUsage>1073741824:
                    termination='RAM_resource_gate'
                elif time.monotonic()-start>180:
                    termination='wall_watchdog'
                if termination:
                    checked(K.TerminateJobObject(job,97))
                    process.wait(timeout=5)
                    break
                if process.poll() is not None:
                    break
                time.sleep(0.01)
        receipt.update(exit_code=process.returncode,termination=termination or 'natural_exit',
                       peak_working_set_bytes=peak_ws,peak_private_commit_bytes=peak_private,
                       worker_cpu_seconds=worker_cpu,guardian_cpu_seconds=time.process_time()-start_cpu,
                       total_cpu_seconds=worker_cpu+time.process_time()-start_cpu,
                       wall_seconds=time.monotonic()-start,
                       pre_receipt_directory_bytes=sum(p.stat().st_size for p in HERE.iterdir() if p.is_file()),
                       completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    except Exception as error:
        receipt.update(guard_error=repr(error))
        if process and process.poll() is None:
            K.TerminateJobObject(job,98)
            process.wait(timeout=5)
    finally:
        K.CloseHandle(job)
        (HERE/'resource_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt))


if __name__=='__main__':
    main()
