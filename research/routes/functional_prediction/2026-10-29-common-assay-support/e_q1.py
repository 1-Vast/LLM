"""One frozen synthetic Q1 check, with no biological responses or parameter search."""
import os
import time

WALL, CPU = time.perf_counter(), time.process_time()
for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "1"
import ctypes
import hashlib
import json
import math
from pathlib import Path
import platform
import threading
import warnings
from collections import Counter

import psutil

HERE = Path(__file__).resolve().parent
OUT = HERE / "q1_run"
STOP = threading.Event()
COUNTS = Counter()
LEAVES = []
LOG2 = math.log(2)
JOB = None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                     allow_nan=False) + "\n", encoding="utf-8")


def limits():
    global JOB
    class Basic(ctypes.Structure):
        _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                    ("flags", ctypes.c_uint32), ("min_ws", ctypes.c_size_t),
                    ("max_ws", ctypes.c_size_t), ("active", ctypes.c_uint32),
                    ("affinity", ctypes.c_size_t), ("priority", ctypes.c_uint32),
                    ("scheduling", ctypes.c_uint32)]
    class Extended(ctypes.Structure):
        _fields_ = [("basic", Basic), ("io", ctypes.c_ulonglong * 6),
                    ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                    ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel.CreateJobObjectW.restype = ctypes.c_void_p
    kernel.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    kernel.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    budget = Extended()
    budget.basic.flags, budget.basic.process_time = 0x100 | 0x2, 120 * 10_000_000
    budget.process_memory = 1_073_741_824
    JOB = kernel.CreateJobObjectW(None, None)
    assert JOB and kernel.SetInformationJobObject(JOB, 9, ctypes.byref(budget), ctypes.sizeof(budget))
    assert kernel.AssignProcessToJobObject(JOB, kernel.GetCurrentProcess())
    def monitor():
        process = psutil.Process()
        while not STOP.wait(.02):
            cpu = process.cpu_times()
            size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
            peak = process.memory_info().peak_wset
            if cpu.user + cpu.system > 120 or peak > 1_073_741_824 or size > 50_000_000:
                save("resource_abort.json", {"cpu_seconds": cpu.user + cpu.system,
                     "peak_working_set_bytes": peak, "output_bytes": size})
                os._exit(124)
    threading.Thread(target=monitor, daemon=True).start()


def merged(model):
    groups = {}
    for weight, mu, variance in model:
        groups.setdefault((mu, variance), []).append(weight)
    return [(math.fsum(groups[key]), *key) for key in sorted(groups)]


def logpdf(y, mu, variance):
    COUNTS["gaussian_logdensity_scalar"] += 1
    return -.5 * (math.log(2 * math.pi * variance) + (y - mu)**2 / variance)


def logmass(lo, hi, mu, variance):
    sd = math.sqrt(variance)
    if lo == -math.inf:
        COUNTS["gaussian_logcdf_scalar"] += 1
        return float(log_ndtr((hi - mu) / sd))
    if hi == math.inf:
        COUNTS["gaussian_logsf_scalar"] += 1
        return float(log_ndtr((mu - lo) / sd))
    if (lo + hi) / 2 >= mu:
        COUNTS["gaussian_logsf_scalar"] += 2
        a, b = float(log_ndtr((mu - lo) / sd)), float(log_ndtr((mu - hi) / sd))
    else:
        COUNTS["gaussian_logcdf_scalar"] += 2
        a, b = float(log_ndtr((hi - mu) / sd)), float(log_ndtr((lo - mu) / sd))
    if not b < a:
        raise ArithmeticError("positive interval mass lost in log difference")
    return a + math.log(-math.expm1(b - a))


def mixmass(model, lo, hi):
    value = float(logsumexp([math.log(a) + logmass(lo, hi, m, v) for a, m, v in model]))
    if not math.isfinite(value):
        raise ArithmeticError("nonfinite positive mixture mass")
    return value


def density_range(model, lo, hi):
    lower, upper = [], []
    for a, mu, variance in model:
        lower.append(math.log(a) + (min(logpdf(lo, mu, variance), logpdf(hi, mu, variance))
                     if math.isfinite(lo) and math.isfinite(hi) else -math.inf))
        upper.append(math.log(a) + logpdf(min(max(mu, lo), hi), mu, variance))
    return float(logsumexp(lower)), float(logsumexp(upper))


def leaf(models, lo, hi, label):
    masses = [mixmass(model, lo, hi) for model in models]
    total = float(logsumexp(masses)) - LOG2
    b = math.exp(total)
    logq = [value - LOG2 - total for value in masses]
    q = [math.exp(value) for value in logq]
    if b == 0 or min(q) <= 0:
        raise ArithmeticError("positive bin/posterior underflow")
    ranges = [density_range(model, lo, hi) for model in models]
    logr = [ranges[z][1] - float(logsumexp([ranges[z][1], ranges[1-z][0]])) for z in (0, 1)]
    if any(logq[z] > logr[z] + 1e-12 for z in (0, 1)):
        raise ArithmeticError("posterior exceeds computed upper bound")
    entropy = -math.fsum(q[z] * logq[z] for z in (0, 1))
    d = b * min(entropy, max(logr[z] - logq[z] for z in (0, 1)))
    lower = b * math.fsum(q[z] * (logq[z] + LOG2) for z in (0, 1))
    if d < 0 or not math.isfinite(lower + d):
        raise ArithmeticError("invalid untrimmed bin bound")
    item = {"candidate": label, "lo": str(lo), "hi": str(hi), "L": lower, "d": d,
            "mass": b, "log_model_masses": masses, "logq": logq, "logr": logr}
    LEAVES.append(item)
    return item


def bounds(models, label):
    models = [merged(model) for model in models]
    if models[0] == models[1]:
        return {"L": 0., "U": 0., "width": 0., "guard_hit": True,
                "leaf_count": 0, "computed_leaves": 0, "trace": [], "final_partition": []}
    edges = [-math.inf, -8., 0., 8., math.inf]
    before = len(LEAVES)
    bins = [leaf(models, lo, hi, label) for lo, hi in zip(edges, edges[1:])]
    trace = []
    while True:
        lower = math.fsum(item["L"] for item in bins)
        width = math.fsum(item["d"] for item in bins)
        if lower < -1e-12:
            raise ArithmeticError("negative mutual information")
        trace.append({"leaves": len(bins), "L": lower, "U": lower + width})
        if width <= .02 or len(bins) >= 2048:
            break
        j = max(range(len(bins)), key=lambda i: bins[i]["d"])
        lo, hi = float(bins[j]["lo"]), float(bins[j]["hi"])
        mid = hi - 8 if lo == -math.inf else lo + 8 if hi == math.inf else (lo + hi) / 2
        trace[-1]["split"] = [str(lo), mid, str(hi)]
        bins[j:j+1] = [leaf(models, lo, mid, label), leaf(models, mid, hi, label)]
    return {"L": lower, "U": lower + width, "width": width, "guard_hit": False,
            "leaf_count": len(bins), "computed_leaves": len(LEAVES) - before,
            "trace": trace, "final_partition": bins, "stop": "width" if width <= .02 else "leaf_limit"}


def mi_lb(models):
    all_components = [(a / 2, mu, v) for model in models for a, mu, v in model]
    low = -math.fsum(a * float(logsumexp([math.log(b) + logpdf(mu, nu, v + u)
                        for b, nu, u in all_components])) for a, mu, v in all_components)
    high = math.fsum(.5 * a * (-math.log(a) + .5 * math.log(2 * math.pi * math.e * v))
                      for model in models for a, mu, v in model)
    return low - high


def threshold_bald(models):
    probabilities = [math.exp(mixmass(model, -math.inf, .5)) for model in models]
    def entropy(p):
        return -p * math.log(p) - (1-p) * math.log1p(-p)
    return entropy(math.fsum(probabilities) / 2) - math.fsum(map(entropy, probabilities)) / 2


def reference(models):
    def integrand(y):
        COUNTS["quad_integrand_scalar"] += 1
        lp = [float(logsumexp([math.log(a) + logpdf(y, mu, v) for a, mu, v in model])) for model in models]
        lm = float(logsumexp(lp)) - LOG2
        return math.fsum(.5 * math.exp(value) * (value - lm) for value in lp)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value, error = quad(integrand, -16., 16., epsabs=1e-12, epsrel=1e-12, limit=300)
    tail = math.fsum(.5 * math.exp(mixmass(model, lo, hi))
                    for model in models for lo, hi in [(-math.inf, -16.), (16., math.inf)]) * LOG2
    return {"MI": value, "quad_error_estimate": error, "tail_upper": tail,
            "total_error_estimate": error + tail, "warnings": [str(x.message) for x in caught],
            "usable": not caught and math.isfinite(value + error + tail) and error + tail <= 1e-10}


def timed(function, *args):
    before, cpu = COUNTS.copy(), time.process_time()
    value = function(*args)
    return {"value": value, "cpu_seconds": time.process_time() - cpu,
            "counts": dict(COUNTS - before)}


def main():
    OUT.mkdir(exist_ok=False)
    freeze = json.loads((HERE / "preexecution_q1_freeze.json").read_text(encoding="utf-8"))
    assert all(sha(HERE / name) == digest for name, digest in freeze["files"].items())
    receipt = {"state": "started", "code_sha256": sha(__file__), "protocol_hashes": freeze["files"],
               "one_execution": True, "real_functional_values_read": False}
    save("receipt.json", receipt)
    limits()
    global log_ndtr, logsumexp, quad
    import numpy
    import scipy
    from scipy.special import log_ndtr, logsumexp
    from scipy.integrate import quad
    a = [[(.5, -3., 1.), (.5, 3., 1.)]] * 2
    b = [[(.5, 0., 1.), (.5, 0., 1.)], [(.5, -math.sqrt(3)/2, .25), (.5, math.sqrt(3)/2, .25)]]
    bp = [[(.25, 0., 1.), (.75, 0., 1.)], b[1]]
    inputs = {"A": a, "B": b, "Bprime": bp}
    save("input.json", inputs)
    receipt["input_sha256"] = sha(OUT / "input.json")
    result = {"versions": {"python": platform.python_version(), "numpy": numpy.__version__, "scipy": scipy.__version__},
              "candidates": {}}
    for label, models in inputs.items():
        means = [math.fsum(weight * mu for weight, mu, _ in model) for model in models]
        mean_disagreement = math.fsum((mu - math.fsum(means) / 2)**2 for mu in means) / 2
        result["candidates"][label] = {
            "raw_MI_LB": timed(mi_lb, models), "merged_MI_LB": timed(mi_lb, [merged(m) for m in models]),
            "mean_disagreement": mean_disagreement, "threshold_BALD": timed(threshold_bald, models),
            "reference": timed(reference, models), "Q1": timed(bounds, models, label)}
    ca, cb, cp = (result["candidates"][key] for key in ("A", "B", "Bprime"))
    ba, bb, bprime = (row["Q1"]["value"] for row in (ca, cb, cp))
    refa, refb = (row["reference"]["value"] for row in (ca, cb))
    result["analytic_MI_A_zero"] = merged(a[0]) == merged(a[1])
    h1 = ca["raw_MI_LB"]["value"] > cb["raw_MI_LB"]["value"] and result["analytic_MI_A_zero"] and refb["MI"] > 0
    h2 = all(row["Q1"]["value"]["leaf_count"] <= 2048 and row["Q1"]["value"]["width"] <= .02
             and row["reference"]["value"]["usable"]
             and row["Q1"]["value"]["L"] - 1e-8 <= row["reference"]["value"]["MI"] - row["reference"]["value"]["total_error_estimate"]
             and row["reference"]["value"]["MI"] + row["reference"]["value"]["total_error_estimate"] <= row["Q1"]["value"]["U"] + 1e-8
             for row in (ca, cb)) and bb["L"] > ba["U"] + 1e-8
    h3 = max(abs(bb[key] - bprime[key]) for key in ("L", "U")) <= 1e-10 and abs(cb["raw_MI_LB"]["value"] - cp["raw_MI_LB"]["value"]) > 1e-6
    result["H"] = {"H1": h1, "H2": h2, "H3": h3, "all": h1 and h2 and h3}
    save("results.json", result)
    save("evaluated_leaves.json", LEAVES)
    receipt.update(state="completed", H=result["H"], cpu_seconds=time.process_time() - CPU,
                   wall_seconds=time.perf_counter() - WALL, counts=dict(COUNTS),
                   peak_working_set_bytes=psutil.Process().memory_info().peak_wset,
                   output_bytes_before_final_receipt=sum(p.stat().st_size for p in OUT.iterdir()),
                   resource_guard="Windows process memory/user CPU limits; 20ms total CPU/working-set/output monitor",
                   cpu_limit_seconds=120, memory_limit_bytes=1073741824, output_limit_bytes=50000000)
    save("receipt.json", receipt)
    STOP.set()
    print(json.dumps({"state": receipt["state"], "H": result["H"], "cpu_seconds": receipt["cpu_seconds"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        if OUT.exists():
            save("failure.json", {"state": "numerical_or_execution_failure", "type": type(error).__name__, "message": str(error)})
        raise
