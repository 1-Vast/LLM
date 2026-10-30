"""Deterministic information-boundary checks, not biological/algorithm efficacy."""
import time

started = time.perf_counter()
cpu_started = time.process_time()

import ctypes
import json
from pathlib import Path

import numpy as np


root = Path(__file__).resolve().parent
mu, f = np.array([0.5, 0.5]), np.array([1.0, 0.0])
A = np.array([[1.0, 0.0], [1.0, 0.0]])
worlds = [np.eye(2), np.array([[0.0, 1.0], [1.0, 0.0]])]
plans, reconstructed, direct, errors = [], [], [], []
for B in worlds:
    np.testing.assert_allclose(mu @ B, mu, atol=1e-12)
    values = np.array([mu @ A @ B @ f, mu @ B @ f])
    plans.append(values.tolist())
    # AB is itself queried: include the direct-program-testing comparator.
    queried_value = float(values[0])
    M_B = np.stack([mu, mu @ A])
    # Only valid here: two states, f=e1, and probabilities sum to one.
    Y_B = np.stack([mu @ B, [queried_value, 1 - queried_value]])
    B_hat = np.linalg.pinv(M_B) @ Y_B
    np.testing.assert_allclose(B_hat, B, atol=1e-12)
    reconstructed.append(int(np.argmax([mu @ A @ B_hat @ f, mu @ B_hat @ f])))
    direct.append(int(np.argmax([queried_value, 0.5])))
    errors.append(float(np.max(np.abs(B_hat - B))))
assert plans == [[1.0, 0.5], [0.0, 0.5]]
assert reconstructed == direct == [0, 1]
q = np.linspace(0, 1, 1001)
regret = np.maximum((1 - q) / 2, q / 2)
assert float(regret.min()) == 0.25
assert np.linalg.matrix_rank(mu[None, :]) == 1
assert np.linalg.matrix_rank(np.stack([mu, mu @ A])) == 2
# Nonnegativity, positive mu, mu@A=e1 force both rows of A to e1.
np.testing.assert_array_equal(mu @ A, f)
P = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
Q = np.array([[0, 0, 1], [1, 0, 0], [0, 0, 1]])
g = np.array([1, 0, 0])
np.testing.assert_array_equal(P @ g, Q @ g)
assert (g @ P @ P @ g, g @ Q @ Q @ g) == (1, 0)
axes = np.array([[1.0, 0.2], [0.55, 0.55]])
mean_value, min_value = axes.mean(axis=1), axes.min(axis=1)
assert (int(mean_value.argmax()), int(min_value.argmax())) == (0, 1)
assert mean_value[1] == min_value[1]  # Measuring B does not distinguish mappings.
assert mean_value[0] != min_value[0]  # Measuring A does in this exact two-model set.
result = {
    "status": "formal_checks_passed_no_algorithm_gain",
    "cohort": {"source_outputs_identical": True, "values_AB_VB": plans,
               "prequery_minimax_expected_simple_regret": float(regret.min()),
               "action_regression_choices": reconstructed, "direct_program_choices": direct,
               "postquery_regret_both_methods": [0.0, 0.0], "B_recovery_max_error": errors,
               "rank_deficiency_does_not_force_nonidentification": True,
               "same_one_step_function_different_two_step_values": [1, 0]},
    "proxy": {"axes_A_B": axes.tolist(), "mean_function": mean_value.tolist(),
              "min_function": min_value.tolist(), "best_drug_mean_min": [0, 1],
              "only_query_A_distinguishes_given_two_mappings": True},
    "biological_efficacy": "not_tested", "algorithm_innovation": "not_established",
    "unqueried_program_transfer": "not_tested", "confidence_interval": "not_applicable_exact_algebra"
}


class ProcessMemory(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
        (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
        "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
        "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]


memory = ProcessMemory()
kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.GetCurrentProcess.restype = ctypes.c_void_p
psapi = ctypes.WinDLL("psapi", use_last_error=True)
psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(ProcessMemory), ctypes.c_ulong]
assert psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(memory), ctypes.sizeof(memory))
timing = {"wall_s": time.perf_counter() - started, "cpu_s": time.process_time() - cpu_started,
          "peak_working_set_bytes": memory.PeakWorkingSetSize, "wall_cap_s": 10,
          "peak_working_set_cap_bytes": 128 * 1024**2}
assert timing["wall_s"] <= 10 and memory.PeakWorkingSetSize <= 128 * 1024**2
(root / "exact_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
(root / "timing_exact.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
print(json.dumps({"status": result["status"], "timing": timing}))
