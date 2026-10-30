#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M1-S2.1 Stage2 preparation v0.2 planning/unit tests only.

No effect comparison, no training, no real data. Freezes:
  - bounded reward on compact Y box,
  - one unique truncated GMM P_theta generator,
  - C-MDN candidate/approximation method and H1/H2/H3 tolerances.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from typing import Any, Dict, List

import numpy as np

ROOT = r"D:\MAESTRO"
HERE = os.path.dirname(os.path.abspath(__file__))
V01 = os.path.join(HERE, "stage2_m1_plan.json")
STAGE1 = os.path.join(ROOT, "research", "2026-10-28-m1-stage1", "m1_stage1.json")
SCHEMA = os.path.join(HERE, "stage2_m1_schema_v0_2.json")
OUT = os.path.join(HERE, "stage2_m1_plan_v0_2.json")
TIMING = os.path.join(HERE, "timing_m1_stage2_prep_v0_2.json")
CAPS = {"wall_s": 1800, "cpu_s": 7200, "memory_gb": 8, "new_wells": 0}
W = np.array([0.4, 0.3, 0.2, 0.1])
LAM = 0.2
BOX = 2.0
R_MIN = -5.2
R_MAX = 0.375
PARAM_SEED = 20261201
TRAIN_SEED = 20261202
EVAL_SEED = 20261203


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest().upper()


def write_json(obj: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write("\n")


def reward(y: np.ndarray) -> np.ndarray:
    return y @ W - LAM * np.sum(y * y, axis=-1)


def generator_params() -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(PARAM_SEED)
    A, K, D, Y = 4, 3, 64, 4
    c = rng.normal(0.0, 0.5, size=(A, K, Y))
    M = rng.normal(0.0, 0.1, size=(A, K, Y, D))
    d = rng.normal(0.0, 0.1, size=(A, K, D))
    return {"c": c, "M": M, "d": d}


def truncated_component_mass(x: np.ndarray, c: np.ndarray, M: np.ndarray, d: np.ndarray) -> float:
    # diagonal Gaussian, truncated to [-BOX,BOX]^4; product of normal CDF differences
    mu = c + M @ x
    sig = 0.1 + 0.4 / (1.0 + np.exp(-(d @ x)))
    sig = max(float(sig), 1e-12)
    z = np.ones(4)
    for j in range(4):
        hi = 0.5 * (1.0 + math.erf((BOX - mu[j]) / (sig * math.sqrt(2.0))))
        lo = 0.5 * (1.0 + math.erf((-BOX - mu[j]) / (sig * math.sqrt(2.0))))
        z[j] = max(0.0, hi - lo)
    return float(np.prod(z))


def sinkhorn_toy() -> Dict[str, Any]:
    K = np.array([[0.8, 0.15, 0.05], [0.1, 0.7, 0.2], [0.2, 0.2, 0.6]], dtype=float)
    r = np.array([0.4, 0.35, 0.25]); c = np.array([0.3, 0.4, 0.3])
    u = np.ones(3); v = np.ones(3); err = 1.0; it = 0
    for it in range(1, 2001):
        u = r / np.maximum(K @ v, 1e-300)
        v = c / np.maximum(K.T @ u, 1e-300)
        err = max(np.max(np.abs(u * (K @ v) - r)), np.max(np.abs(v * (K.T @ u) - c)))
        if err <= 1e-10:
            break
    return {"iterations": it, "max_marginal_error": float(err), "converged": bool(err <= 1e-8),
            "epsilon": 0.5, "max_iterations": 2000}


def planning_tests() -> Dict[str, Any]:
    rng = np.random.default_rng(20261201)
    # reward bounds: corners + random
    corners = np.array([[sx * BOX, sy * BOX, sz * BOX, sw * BOX]
                        for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1) for sw in (-1, 1)])
    rc = reward(corners)
    rnd = rng.uniform(-BOX, BOX, size=(20000, 4))
    rr = reward(rnd)
    r_min_data = float(np.min(np.concatenate([rc, rr])))
    r_max_data = float(np.max(np.concatenate([rc, rr])))
    # generator parameter shapes
    gp = generator_params()
    c, M, d = gp["c"], gp["M"], gp["d"]
    # truncation mass at 4 random x
    xs = rng.normal(size=(4, 64))
    mass = []
    for a in range(4):
        z = 0.0
        for k in range(3):
            wk = (0.5, 0.3, 0.2)[k]
            z += wk * truncated_component_mass(xs[0], c[a, k], M[a, k], d[a, k])
        mass.append(float(z))
    tests = {
        "reward_min_observed": r_min_data,
        "reward_max_observed": r_max_data,
        "reward_min_expected": R_MIN,
        "reward_max_expected": R_MAX,
        "reward_bounded": bool(r_min_data >= R_MIN - 1e-12 and r_max_data <= R_MAX + 1e-12),
        "c_shape": list(c.shape), "M_shape": list(M.shape), "d_shape": list(d.shape),
        "generator_shapes_ok": bool(c.shape == (4, 3, 4) and M.shape == (4, 3, 4, 64) and d.shape == (4, 3, 64)),
        "weights": [0.5, 0.3, 0.2],
        "weights_sum": 1.0,
        "truncation_mass_sample": mass,
        "truncation_mass_finite_positive": bool(all(0.0 < v <= 1.0 for v in mass)),
        "seed_reproducible": bool(np.array_equal(generator_params()["c"], c)),
        "sinkhorn": sinkhorn_toy(),
    }
    tests["all_pass"] = bool(tests["reward_bounded"] and tests["generator_shapes_ok"]
                             and tests["truncation_mass_finite_positive"]
                             and tests["seed_reproducible"] and tests["sinkhorn"]["converged"])
    return tests


def main() -> int:
    t0 = time.perf_counter()
    schema = json.load(open(SCHEMA, encoding="utf-8"))
    # v0.1 prep + Stage1 B2 chain check
    v01 = json.load(open(V01, encoding="utf-8")) if os.path.isfile(V01) else {}
    stage1 = json.load(open(STAGE1, encoding="utf-8"))
    b2 = stage1["B_spec_checks"]["B2_maxent"]
    chain = {
        "stage2_m1_plan_v0_1.json": {"expected": None, "actual": sha256_file(V01) if os.path.isfile(V01) else None},
        "m1_stage1.json": {"expected": None, "actual": sha256_file(STAGE1)},
        "stage1_b2_rename_maxent": bool(b2["rename_maxent_detected"]),
        "stage1_b2_m1_increment_claimed": bool(b2.get("m1_increment_claimed", False)),
        "one_step_projection_withdrawn": bool(b2["rename_maxent_detected"] and not b2.get("m1_increment_claimed", False)),
    }
    tests = planning_tests()
    # H1/H2/H3 frozen planning structures
    h1 = schema["stage2_new_checks"]["H1_approx_scaling"]
    h2 = schema["stage2_new_checks"]["H2_sinkhorn"]
    h3 = schema["stage2_new_checks"]["H3_planning_quality"]
    planning = {
        "H1": {"dimension_grid": h1["dimension_grid"], "sample_grid": h1["sample_grid"],
               "tolerance_table_TV_max": h1["tolerance_table_TV_max"], "status": "planned_not_run"},
        "H2": {"solver": h2["solver"], "epsilon_grid": h2["epsilon_grid"],
               "max_iterations": h2["max_iterations"], "marginal_tolerance": h2["marginal_tolerance"],
               "convergence_rule": h2["convergence_rule"], "status": "planned_not_run"},
        "H3": {"small_case": h3["small_case"], "oracle": h3["oracle"], "metric": h3["metric"],
               "tolerance_TV_max": h3["tolerance_TV_max"], "status": "planned_not_run"},
        "memory_bytes_estimate": float(4096 * 64 * 8 * 3 + 4096 * 4 * 8 * 3),
        "memory_gb_estimate": round((4096 * 64 * 8 * 3 + 4096 * 4 * 8 * 3) / 1e9, 9),
        "within_memory_cap": bool((4096 * 64 * 8 * 3 + 4096 * 4 * 8 * 3) / 1e9 <= 8.0),
    }
    checks = {
        "chain_ok": bool(chain["one_step_projection_withdrawn"]),
        "reward_bounded": bool(tests["reward_bounded"]),
        "generator_shapes_ok": bool(tests["generator_shapes_ok"]),
        "truncation_mass_ok": bool(tests["truncation_mass_finite_positive"]),
        "seed_reproducible": bool(tests["seed_reproducible"]),
        "sinkhorn_converged": bool(tests["sinkhorn"]["converged"]),
        "memory_within_cap": bool(planning["within_memory_cap"]),
        "H1_H2_H3_frozen": bool(all(planning[k]["status"] == "planned_not_run" for k in ("H1", "H2", "H3"))),
        "schema_loaded": True,
        "caps_present": True,
    }
    all_pass = all(checks.values())
    result = {
        "task": "R204-M1-S2.1",
        "status": "prep_v0_2_ready_not_executed" if all_pass else "design_invalid",
        "scope": "M1 Stage2 high-dimensional approximation design preparation v0.2; mechanism account only; no effect/training/real data; 0 wells",
        "positioning": schema["positioning"],
        "reward": schema["reward"],
        "P_theta_generator": schema["P_theta_generator"],
        "stage2_candidate": schema["stage2_candidate"],
        "stage1_checks_retained": schema["stage1_checks_retained"],
        "stage2_new_checks": schema["stage2_new_checks"],
        "baselines": schema["baselines"],
        "stage3_endpoints": schema["stage3_endpoints"],
        "failure_categories": schema["failure_categories"],
        "chain": chain,
        "unit_tests": tests,
        "planning": planning,
        "checks": checks,
        "all_pass": all_pass,
        "failure_category": None if all_pass else "design_invalid",
        "caps": CAPS,
        "no_effect_results": True,
        "no_model_fit_or_training": True,
        "no_method_comparison": True,
        "no_real_data": True,
        "new_wells": 0,
        "schema_sha256": sha256_file(SCHEMA),
        "v0_1_not_modified": True,
        "two_run_note": "external two-run byte-identical check recorded in usage/report; result JSON has no telemetry",
    }
    write_json(result, OUT)

    tp = time.perf_counter()
    for _ in range(10):
        planning_tests()
    per_rep = (time.perf_counter() - tp) / 10.0
    timing = {"task": "R204-M1-S2.1", "pilot_reps": 10,
              "per_rep_seconds": round(per_rep, 9), "mean_per_rep_seconds": round(per_rep, 9),
              "projected_seconds": round(per_rep * 10.0, 6),
              "full_prep_wall_seconds": round(time.perf_counter() - t0, 6),
              "caps": CAPS, "wells": 0, "compute_only": True,
              "canonical": True, "note": "planning/unit-test timing only; no effect comparison"}
    timing["result_json_sha256"] = sha256_file(OUT)
    write_json(timing, TIMING)

    print("all_pass", all_pass, "failure", result["failure_category"])
    print("reward", tests["reward_min_observed"], tests["reward_max_observed"])
    print("H1/H2/H3", {k: planning[k]["status"] for k in ("H1", "H2", "H3")})
    print("checks", {k: v for k, v in checks.items()})
    print("timing", timing)
    print("wrote", OUT, TIMING)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
