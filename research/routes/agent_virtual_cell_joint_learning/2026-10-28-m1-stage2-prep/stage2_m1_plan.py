#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M1-STAGE2-PREP planning arithmetic / skeleton unit tests only.

No effect comparison, no model fit, no training, no real data.
Prepares the Stage2 high-dimensional approximation design with:
  - chain verification (M1 v0.2 + Stage1),
  - Stage1 B2 equivalence acknowledgement (one-step projection withdrawn),
  - structural unit tests (shape/finite/support/seed/Sinkhorn),
  - budget/approximation planning arithmetic,
  - pilot timing (planning only).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from typing import Any, Dict, List

import numpy as np

ROOT = r"D:\MAESTRO"
PREREG = os.path.join(ROOT, "research", "2026-10-28-m1-executable-gen-prereg")
STAGE1 = os.path.join(ROOT, "research", "2026-10-28-m1-stage1")
HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "stage2_m1_schema.json")
OUT = os.path.join(HERE, "stage2_m1_plan.json")
TIMING = os.path.join(HERE, "timing_m1_stage2_prep.json")
CAPS = {"wall_s": 1800, "cpu_s": 7200, "memory_gb": 8, "new_wells": 0}
TRAIN_N = 4096
EVAL_N = 2048
D_X = 64
A_N = 4
Y_N = 4


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


def softmax(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    m = float(np.max(z))
    e = np.exp(z - m)
    return e / e.sum()


def sinkhorn_toy() -> Dict[str, Any]:
    K = np.array([[0.8, 0.15, 0.05], [0.1, 0.7, 0.2], [0.2, 0.2, 0.6]], dtype=float)
    r = np.array([0.4, 0.35, 0.25])
    c = np.array([0.3, 0.4, 0.3])
    u = np.ones(3); v = np.ones(3)
    err = 1.0
    it = 0
    for it in range(1, 2001):
        u = r / np.maximum(K @ v, 1e-300)
        v = c / np.maximum(K.T @ u, 1e-300)
        err = max(np.max(np.abs(u * (K @ v) - r)), np.max(np.abs(v * (K.T @ u) - c)))
        if err <= 1e-10:
            break
    return {"iterations": it, "max_marginal_error": float(err),
            "converged": bool(err <= 1e-8), "finite": bool(np.all(np.isfinite(u)) and np.all(np.isfinite(v)))}


def structural_unit_tests() -> Dict[str, Any]:
    rng = np.random.default_rng(20261201)
    X = rng.normal(size=(32, D_X))
    A = rng.integers(0, A_N, size=32)
    Y = rng.normal(size=(32, Y_N))
    full_actions = sorted(set(A.tolist()))
    constrained_actions = [a for a in full_actions if a in (0, 1)]
    seed1 = np.random.default_rng(20261201).normal(size=(4, 4))
    seed2 = np.random.default_rng(20261201).normal(size=(4, 4))
    sink = sinkhorn_toy()
    tests = {
        "shape_X": {"shape": list(X.shape), "pass": X.shape == (32, D_X)},
        "shape_A": {"shape": list(A.shape), "pass": A.shape == (32,)},
        "shape_Y": {"shape": list(Y.shape), "pass": Y.shape == (32, Y_N)},
        "finite": {"pass": bool(np.all(np.isfinite(X)) and np.all(np.isfinite(Y)))},
        "support_full": {"actions": full_actions, "pass": bool(len(full_actions) == A_N)},
        "support_constrained": {"actions": constrained_actions,
                                "pass": bool(constrained_actions == [0, 1])},
        "seed_reproducible": {"pass": bool(np.array_equal(seed1, seed2)),
                              "seed": 20261201},
        "sinkhorn": sink,
    }
    tests["all_pass"] = all(bool(v.get("pass", v.get("converged", False))) for v in tests.values()
                             if isinstance(v, dict) and "pass" in v) and sink["converged"]
    return tests


def planning() -> Dict[str, Any]:
    dimension_grid = [8, 16, 32, 64]
    sample_grid = [512, 1024, 2048, 4096]
    memory_bytes_est = float(TRAIN_N * D_X * 8 * 3 + TRAIN_N * Y_N * 8 * 3)
    return {
        "dimension_grid": dimension_grid,
        "sample_grid": sample_grid,
        "train_N": TRAIN_N,
        "eval_N": EVAL_N,
        "A": A_N,
        "Y_dim": Y_N,
        "memory_bytes_estimate": memory_bytes_est,
        "memory_gb_estimate": round(memory_bytes_est / 1e9, 9),
        "within_memory_cap": bool(memory_bytes_est / 1e9 <= CAPS["memory_gb"]),
        "approx_error_plan": "evaluate approximation error vs dimension/sample on known synthetic truth; report only, no effect/gain",
        "sinkhorn_plan": "marginal error <=1e-8; finite iterations; else design_invalid: projection",
        "planning_quality_plan": "compare planning quality to exact small-case oracle; no effect claim",
        "status": "planned_not_run",
    }


def main() -> int:
    t0 = time.perf_counter()
    schema = json.load(open(SCHEMA, encoding="utf-8"))
    chain = {}
    for name, expected in schema["frozen_chain"].items():
        if name.startswith("m1_stage1") or name.startswith("report_m1"):
            path = os.path.join(STAGE1, name)
        else:
            path = os.path.join(PREREG, name)
        actual = sha256_file(path) if os.path.isfile(path) else None
        chain[name] = {"expected": expected, "actual": actual, "match": actual == expected}
    chain_ok = all(v["match"] for v in chain.values())
    if not chain_ok:
        result = {"task": "R204-M1-STAGE2-PREP", "status": "design_invalid",
                  "failure_category": "design_invalid: chain_mismatch", "chain": chain,
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, OUT)
        print("CHAIN MISMATCH", chain)
        return 2

    stage1 = json.load(open(os.path.join(STAGE1, "m1_stage1.json"), encoding="utf-8"))
    b2 = stage1["B_spec_checks"]["B2_maxent"]
    b2_equiv = bool(b2["rename_maxent_detected"])
    one_step_withdrawn = bool(b2_equiv and not b2.get("m1_increment_claimed", False))
    if not one_step_withdrawn:
        result = {"task": "R204-M1-STAGE2-PREP", "status": "design_invalid",
                  "failure_category": "design_invalid: rename_maxent", "chain": chain,
                  "stage1_b2": b2, "no_effect_results": True, "new_wells": 0}
        write_json(result, OUT)
        print("STAGE1 B2 NOT AS EXPECTED", b2)
        return 2

    tests = structural_unit_tests()
    plan = planning()
    baseline_spec = schema["baselines"]
    checks = {
        "chain_ok": chain_ok,
        "stage1_b2_withdrawn": one_step_withdrawn,
        "unit_shapes": bool(tests["shape_X"]["pass"] and tests["shape_A"]["pass"] and tests["shape_Y"]["pass"]),
        "unit_finite": bool(tests["finite"]["pass"]),
        "unit_support": bool(tests["support_full"]["pass"] and tests["support_constrained"]["pass"]),
        "unit_seed_reproducible": bool(tests["seed_reproducible"]["pass"]),
        "unit_sinkhorn_converged": bool(tests["sinkhorn"]["converged"]),
        "memory_within_cap": bool(plan["within_memory_cap"]),
        "caps_present": True,
    }
    all_pass = all(checks.values())
    result = {
        "task": "R204-M1-STAGE2-PREP",
        "status": "prep_ready_not_executed" if all_pass else "design_invalid",
        "scope": "M1 Stage2 high-dimensional approximation design preparation only; no effect/training/real data; mechanism account; 0 wells",
        "positioning": schema["positioning"],
        "chain": chain,
        "chain_ok": chain_ok,
        "stage1_b2": {"rename_maxent_detected": b2_equiv,
                       "one_step_projection_withdrawn": one_step_withdrawn,
                       "stage1_b2_equivalence": b2},
        "high_dim_settings": schema["high_dim_settings"],
        "stage1_checks_retained": schema["stage1_checks_retained"],
        "stage2_new_checks": schema["stage2_new_checks"],
        "baseline_spec": baseline_spec,
        "stage3_endpoints": schema["stage3_endpoints"],
        "failure_categories": schema["failure_categories"],
        "unit_tests": tests,
        "planning": plan,
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
        "two_run_note": "external two-run byte-identical check recorded in usage/report; result JSON has no telemetry",
    }
    write_json(result, OUT)

    tp = time.perf_counter()
    for _ in range(10):
        structural_unit_tests()
    per_rep = (time.perf_counter() - tp) / 10.0
    timing = {"task": "R204-M1-STAGE2-PREP", "pilot_reps": 10,
              "per_rep_seconds": round(per_rep, 9), "mean_per_rep_seconds": round(per_rep, 9),
              "projected_seconds": round(per_rep * 10.0, 6),
              "full_stage2_prep_wall_seconds": round(time.perf_counter() - t0, 6),
              "caps": CAPS, "wells": 0, "compute_only": True,
              "canonical": True, "note": "planning/unit-test timing only; no effect comparison"}
    timing["result_json_sha256"] = sha256_file(OUT)
    write_json(timing, TIMING)

    print("chain_ok", chain_ok, "b2_withdrawn", one_step_withdrawn)
    print("unit_tests", {k: v for k, v in checks.items()})
    print("all_pass", all_pass, "failure", result["failure_category"])
    print("timing", timing)
    print("wrote", OUT, TIMING)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
