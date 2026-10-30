"""T001 fixed constructed check; implements equations without running author code."""
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import psutil
from scipy.integrate import quad_vec, solve_ivp
from scipy.linalg import expm
from scipy.special import expit

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "time_primary_result.json"
if OUTPUT.exists():
    raise SystemExit("Frozen primary output exists; no automatic replay")
started, cpu_started = time.monotonic(), time.process_time()


def generator(t, case):
    k = 0.0 if case == "C0" else 0.3
    rho = expit(k * (t - 12.0))
    bb = np.array([0.95, 0.95 if case == "C1" else 0.98])
    bn = np.array([1.0, 1.0]) if case == "C1" else np.array([1.02, 1.0])
    hb = (2.0 - rho + rho * bb) / 2.0
    hn = (2.0 - rho + rho * bn) / 2.0
    diagonal = np.array([0.03, 0.02]) - np.array([0.01, 0.005]) + np.log(hb)
    nu = np.maximum(np.array([0.003, 0.001]) + np.log(hn), 0.0)
    return np.array([[diagonal[0], nu[0]], [nu[1], diagonal[1]]])


results = {}
for case in ["N1", "C0", "C1"]:
    integral, quadrature_error = quad_vec(lambda t: generator(t, case), 0.0, 24.0,
                                          epsabs=1e-12, epsrel=1e-12)
    plain = expm(integral)
    solution = solve_ivp(lambda t, flat: (flat.reshape(2, 2) @ generator(t, case)).ravel(),
                         (0.0, 24.0), np.eye(2).ravel(), method="DOP853",
                         rtol=1e-11, atol=1e-13)
    if not solution.success:
        raise RuntimeError(solution.message)
    ordered = solution.y[:, -1].reshape(2, 2)
    if not np.isfinite(plain).all() or not np.isfinite(ordered).all():
        raise RuntimeError("Nonfinite propagation")
    plain_total = float(np.array([0.5, 0.5]) @ plain @ np.ones(2))
    ordered_total = float(np.array([0.5, 0.5]) @ ordered @ np.ones(2))
    first, last = generator(0, case), generator(24, case)
    results[case] = {"plain": plain.tolist(), "ordered": ordered.tolist(),
                     "max_entry_difference": float(np.max(np.abs(plain - ordered))),
                     "plain_total": plain_total, "ordered_total": ordered_total,
                     "relative_total_difference": (plain_total - ordered_total) / ordered_total,
                     "commutator_0_24": (first @ last - last @ first).tolist(),
                     "quadrature_error": float(quadrature_error), "ode_nfev": solution.nfev}
    if time.monotonic() - started > 60 or time.process_time() - cpu_started > 60:
        raise RuntimeError("Cooperative resource ceiling reached")

result = {"status": "constructed_mathematical_check_not_biological", "cases": results,
          "protocol_sha256": hashlib.sha256((ROOT / "time_propagation_protocol.md").read_bytes()).hexdigest(),
          "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "source_commit": "19d42e94af20a2be805c78fbb9b104b9a7265d51",
          "cpu_seconds": time.process_time() - cpu_started,
          "wall_seconds": time.monotonic() - started,
          "peak_working_set_bytes": psutil.Process().memory_info().peak_wset,
          "enforcement": "cooperative CPU/wall checks and measured process peak; no OS hard cap",
          "author_code_executed": False, "biological_response_values_accessed": 0}
OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "max_entry_differences":
                  {case: r["max_entry_difference"] for case, r in results.items()},
                  "cpu_seconds": result["cpu_seconds"]}))
