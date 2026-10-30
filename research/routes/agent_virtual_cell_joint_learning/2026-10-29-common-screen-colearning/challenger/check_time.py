"""Independent fixed T001.v1 check; never imports or executes author code."""
import time

started_wall = time.perf_counter()
started_cpu = time.process_time()

import ctypes
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.linalg import expm

HERE = Path(__file__).resolve().parent
T = 24.0
THRESHOLD = 1e-7
CASES = {
    "N1": (0.3, (0.95, 0.98), (1.02, 1.0)),
    "C0": (0.0, (0.95, 0.98), (1.02, 1.0)),
    "C1": (0.3, (0.95, 0.95), (1.0, 1.0)),
}


def matrix(t, specification):
    k, b_death, b_birth = specification
    rho = 1.0 / (1.0 + np.exp(k * (12.0 - t)))
    death_effect = np.log((2.0 + rho * (np.array(b_death) - 1.0)) / 2.0)
    birth_effect = np.log((2.0 + rho * (np.array(b_birth) - 1.0)) / 2.0)
    return np.array([
        [0.03 - 0.01 + death_effect[0], max(0.003 + birth_effect[0], 0.0)],
        [max(0.001 + birth_effect[1], 0.0), 0.02 - 0.005 + death_effect[1]],
    ])


def budget_check():
    if time.perf_counter() - started_wall > 60 or time.process_time() - started_cpu > 60:
        raise RuntimeError("Frozen 60-second wall/CPU ceiling exceeded")


def midpoint_product(specification, steps):
    result = np.eye(2)
    dt = T / steps
    for j in range(steps):
        # Earlier time factors multiply on the left for a row population.
        result = result @ expm(dt * matrix((j + 0.5) * dt, specification))
        if j % 256 == 0:
            budget_check()
    if not np.all(np.isfinite(result)):
        raise RuntimeError("Nonfinite ordered product")
    return result


def peak_working_set():
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                "PagefileUsage", "PeakPagefileUsage",
            )
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    read_memory = ctypes.windll.psapi.GetProcessMemoryInfo
    read_memory.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    if not read_memory(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError()
    return counters.PeakWorkingSetSize


report = {
    "protocol": "T001.v1",
    "protocol_sha256": hashlib.sha256((HERE.parent / "time_propagation_protocol.md").read_bytes()).hexdigest(),
    "requested_model": "gpt-6.1-sol", "requested_effort": "high",
    "effective_model": "unknown", "effective_effort": "unknown",
    "method": "Independent chronological midpoint exponential products, 2048/4096; scalar-entry scipy quad for plain integral",
    "root_results_read": False,
    "scope": "Constructed source-family mathematical identity only; no biological data or author code execution",
    "cases": {},
}
for name, specification in CASES.items():
    integral = np.zeros((2, 2))
    errors = np.zeros((2, 2))
    for i in range(2):
        for j in range(2):
            integral[i, j], errors[i, j] = quad(
                lambda t: matrix(t, specification)[i, j], 0.0, T,
                epsabs=1e-12, epsrel=1e-12,
            )
    plain = expm(integral)
    coarse = midpoint_product(specification, 2048)
    ordered = midpoint_product(specification, 4096)
    initial = np.array([0.5, 0.5])
    total_plain = float(np.sum(initial @ plain))
    total_ordered = float(np.sum(initial @ ordered))
    a0, aT = matrix(0.0, specification), matrix(T, specification)
    report["cases"][name] = {
        "integral": integral.tolist(), "quad_error_max": float(errors.max()),
        "M_plain": plain.tolist(), "M_ordered_midpoint_2048": coarse.tolist(),
        "M_ordered": ordered.tolist(),
        "midpoint_2048_4096_max_difference": float(np.max(np.abs(coarse - ordered))),
        "max_entry_difference": float(np.max(np.abs(plain - ordered))),
        "total_plain": total_plain, "total_ordered": total_ordered,
        "relative_total_difference": float((total_plain - total_ordered) / total_ordered),
        "commutator_0_T": (a0 @ aT - aT @ a0).tolist(),
        "commutator_max": float(np.max(np.abs(a0 @ aT - aT @ a0))),
    }
    budget_check()

report["checks"] = {
    "all_finite": all(np.isfinite(c["max_entry_difference"]) for c in report["cases"].values()),
    "midpoint_convergence_below_1e_7": all(c["midpoint_2048_4096_max_difference"] <= THRESHOLD for c in report["cases"].values()),
    "constant_control_below_1e_7": report["cases"]["C0"]["max_entry_difference"] <= THRESHOLD,
    "commuting_control_below_1e_7": report["cases"]["C1"]["max_entry_difference"] <= THRESHOLD,
    "N1_difference_above_1e_7": report["cases"]["N1"]["max_entry_difference"] > THRESHOLD,
}
report["resources"] = {
    "wall_seconds_including_imports": time.perf_counter() - started_wall,
    "cpu_seconds_including_imports": time.process_time() - started_cpu,
    "peak_working_set_bytes": peak_working_set(),
    "ceiling_seconds": 60,
    "enforcement": "Cooperative wall/CPU checks each 256 products and each case; caller timeout=60; memory measured, not hard-capped",
}
report["status"] = "refutes_unrestricted_identity_pending_cross_implementation_comparison" if all(report["checks"].values()) else "failed_or_inconclusive"
(HERE / "time_result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": report["status"], "checks": report["checks"], "resources": report["resources"]}, indent=2))
if not all(report["checks"].values()):
    raise SystemExit(1)
