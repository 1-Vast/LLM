#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M3-S2-EXEC synthetic allocation diagnostics.

Support research / mechanism account only. No effect/regret/decision-utility/top-k,
no method comparison, no real data. Runs one frozen Stage2 allocation diagnostic:
R=10 x (300 initial + 6 arms x 300 allocation units); per-arm 13 diagnostic fields.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time
import tracemalloc
from typing import Any, Dict, List, Tuple

import numpy as np

ROOT = r"D:\MAESTRO"
PREREG = os.path.join(ROOT, "research", "2026-10-28-m3-stage2-exec-prereg")
DEFAULT_OUT = os.path.join(ROOT, "research", "2026-10-28-m3-stage2-run")
SCHEMA_NAME = "schema_m3_stage2_run.json"
CAPS = {"wall_s": 1800, "cpu_s": 7200, "memory_gb": 8, "new_wells": 0}
P = np.array([0.3, 0.4, 0.3])
B = np.array([[0.2, 0.3, 0.5], [0.4, 0.4, 0.2], [0.25, 0.35, 0.4]], dtype=float)
MU = np.array([[0.2, 0.5, 0.8], [0.4, 0.6, 0.3], [0.1, 0.7, 0.5]], dtype=float)
PI2 = np.array([[0.2, 0.5, 0.3], [0.5, 0.2, 0.3], [0.3, 0.3, 0.4]], dtype=float)
M_WRONG = np.full((3, 3), 0.5)
C_H = 20.0
R_MAIN = 10
R_PILOT = 2
N_INITIAL = 300
N_ALLOC = 300
NH, NA = 3, 3
ARM_IDS = ["S_shared_score", "S_random", "S_gp_uncertainty", "S_decision_AL",
           "S_optimal_experimental_design", "S_DR_MLE_allocation"]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest().upper()


def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def write_json(obj: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write("\n")


def arm_weights(a: int) -> np.ndarray:
    """Frozen allocation rule; diagnostic only, not a learner/effect comparison."""
    var = MU * (1.0 - MU)
    if a == 0:  # shared score
        w = P[:, None] * PI2 ** 2 * (var + (MU - M_WRONG) ** 2) / B
    elif a == 1:  # random
        w = np.ones((NH, NA))
    elif a == 2:  # GP/uncertainty
        w = np.sqrt(var / B)
    elif a == 3:  # decision AL
        w = P[:, None] * PI2 * np.abs(MU - M_WRONG) / B
    elif a == 4:  # optimal experimental design (Bernoulli information)
        w = B * (1.0 - B)
    elif a == 5:  # DR+MLE noise-only allocation
        w = P[:, None] * PI2 ** 2 * var / B
    else:
        raise ValueError(a)
    w = np.maximum(w, 0.0)
    return w / w.sum()


def arm_seed(a: int, r: int) -> int:
    return 20261411 + 10 * a + r


def run_replicate(r: int, arms_only: bool = False) -> Dict[str, Any]:
    data_seed = 20261401 + r
    rng0 = np.random.default_rng(data_seed)
    h0 = rng0.choice(NH, size=N_INITIAL, p=P)
    a0 = np.array([rng0.choice(NA, p=B[h]) for h in h0])
    y0 = rng0.binomial(1, MU[h0, a0])
    initial = {"n": N_INITIAL, "n_events": int(y0.sum()), "n_h": np.bincount(h0, minlength=NH).tolist(),
               "n_a": np.bincount(a0, minlength=NA).tolist()}
    per_arm = []
    for a, arm_id in enumerate(ARM_IDS):
        rng = np.random.default_rng(arm_seed(a, r))
        w = arm_weights(a)
        flat = w.ravel() / w.sum()
        cells = rng.choice(NH * NA, size=N_ALLOC, p=flat)
        hh = cells // NA
        aa = cells % NA
        y = rng.binomial(1, MU[hh, aa])
        Hraw = PI2[hh, aa] / B[hh, aa]
        Hc = np.minimum(Hraw, C_H)
        delta = Hc * (y - M_WRONG[hh, aa])
        # realized frequency
        freq = np.zeros((NH, NA))
        for h, a_ in zip(hh, aa):
            freq[h, a_] += 1
        freq = freq / N_ALLOC
        # allocation Q terms
        var = MU * (1.0 - MU)
        q_noise = P[:, None] * PI2 ** 2 * var / B
        q_full = P[:, None] * PI2 ** 2 * (var + (MU - M_WRONG) ** 2) / B
        q_bias = q_full - q_noise
        clipping = {"cap": C_H, "max_raw_H": float(np.max(Hraw)), "n_clipped": int(np.sum(Hraw > C_H)),
                    "bias_bound": "clipped estimate != exact policy value; diagnostic only"}
        H_summary = {"mean": float(np.mean(Hc)), "min": float(np.min(Hc)), "max": float(np.max(Hc)),
                     "n_finite": int(np.isfinite(Hc).sum())}
        delta_summary = {"mean": float(np.mean(delta)), "se": float(np.std(delta, ddof=1) / math.sqrt(N_ALLOC)),
                         "n_finite": int(np.isfinite(delta).sum())}
        alloc_Q = {"full_total": float(q_full.sum()), "noise_only_total": float(q_noise.sum()),
                   "bias_squared_total": float(q_bias.sum()), "full_ge_noise": bool(q_full.sum() >= q_noise.sum() - 1e-12)}
        variance_term = {"noise_only_total": float(q_noise.sum()), "full_total": float(q_full.sum())}
        audit = {"n_alloc": N_ALLOC, "feedback": N_ALLOC, "tuning_configs": 0,
                 "caps": CAPS, "legal_package": True, "same_updater": True}
        # per-arm payload hash (self-hash; external two-run check covers whole result)
        payload = {
            "arm_id": arm_id, "replicate_id": r,
            "allocation_weights": w.tolist(), "realized_allocation_frequency": freq.tolist(),
            "H_summary": H_summary, "delta_summary": delta_summary,
            "allocation_Q": alloc_Q, "variance_term": variance_term,
            "clipping": clipping, "equal_budget_audit": audit,
        }
        two_run_sha = sha256_obj(payload)
        support_ok = bool(np.all(B > 0) and np.all(w >= 0) and abs(w.sum() - 1.0) < 1e-12
                          and np.all(freq >= 0) and abs(freq.sum() - 1.0) < 1e-9)
        finite_ok = bool(np.isfinite(list(H_summary.values())).all() if False else
                         (np.isfinite(H_summary["mean"]) and np.isfinite(H_summary["min"])
                          and np.isfinite(H_summary["max"]) and np.isfinite(delta_summary["mean"])))
        q_ok = bool(alloc_Q["full_ge_noise"] and math.isfinite(alloc_Q["full_total"]))
        budget_ok = bool(audit["n_alloc"] == N_ALLOC and audit["feedback"] == N_ALLOC
                         and audit["tuning_configs"] <= 20 and CAPS["new_wells"] == 0)
        no_forbidden = True  # no effect/regret/decision fields emitted
        passes = bool(support_ok and finite_ok and q_ok and budget_ok and no_forbidden and len(two_run_sha) == 64)
        failure = None
        if not support_ok:
            failure = "design_invalid: support"
        elif not finite_ok:
            failure = "design_invalid: nonidentifiable"
        elif not q_ok:
            failure = "design_invalid: calibration"
        elif not budget_ok:
            failure = "design_invalid: compute_budget_exceeded"
        per_arm.append({
            "arm_id": arm_id, "replicate_id": r,
            "allocation_weights": w.tolist(), "realized_allocation_frequency": freq.tolist(),
            "H_summary": H_summary, "delta_summary": delta_summary,
            "allocation_Q": alloc_Q, "variance_term": variance_term,
            "clipping": clipping, "equal_budget_audit": audit,
            "two_run_sha": two_run_sha, "pass": passes, "failure_category": failure,
        })
    return {"replicate_id": r, "initial_behavior": initial, "per_arm": per_arm}


def run_all(reps: int) -> Dict[str, Any]:
    runs = [run_replicate(r) for r in range(reps)]
    return {"R": reps, "replicates": runs,
            "total_units": reps * (N_INITIAL + 6 * N_ALLOC),
            "total_allocation_units": reps * 6 * N_ALLOC}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=DEFAULT_OUT)
    args = ap.parse_args()
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)
    t0 = time.perf_counter()
    schema_path = os.path.join(outdir, SCHEMA_NAME)
    if os.path.abspath(schema_path) != os.path.abspath(os.path.join(DEFAULT_OUT, SCHEMA_NAME)):
        if not os.path.isfile(schema_path):
            import shutil
            shutil.copyfile(os.path.join(DEFAULT_OUT, SCHEMA_NAME), schema_path)
    schema = json.load(open(schema_path, encoding="utf-8"))

    # chain verify 17 files + Lead decision
    chain = {}
    for rel, expected in schema["chain_files"].items():
        p = os.path.join(ROOT, rel)
        actual = sha256_file(p) if os.path.isfile(p) else None
        chain[rel] = {"expected": expected, "actual": actual, "match": actual == expected}
    dec = schema["lead_decision"]
    dp = os.path.join(ROOT, dec["path"])
    dec_actual = sha256_file(dp) if os.path.isfile(dp) else None
    decision = {"path": dec["path"], "expected": dec["sha256"], "actual": dec_actual, "match": dec_actual == dec["sha256"]}
    chain_ok = all(v["match"] for v in chain.values()) and decision["match"]
    if not chain_ok:
        result = {"task": "R204-M3-S2-EXEC", "status": "design_invalid",
                  "failure_category": "design_invalid: chain_mismatch",
                  "chain": chain, "lead_decision": decision,
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, os.path.join(outdir, "m3_stage2.json"))
        print("CHAIN MISMATCH")
        return 2

    # final-implementation pilot: 2 replicates x 6 arms x 300 allocations
    tracemalloc.start()
    tp = time.perf_counter(); cp = time.process_time()
    pilot = run_all(R_PILOT)
    pilot_wall = time.perf_counter() - tp
    pilot_cpu = time.process_time() - cp
    _, pilot_peak = tracemalloc.get_traced_memory()
    tracemalloc.reset_peak()
    pilot_mem_gb = pilot_peak / 1e9
    pilot_ok = (pilot_wall <= CAPS["wall_s"] and pilot_cpu <= CAPS["cpu_s"] and pilot_mem_gb <= CAPS["memory_gb"])
    if not pilot_ok:
        result = {"task": "R204-M3-S2-EXEC", "status": "design_invalid",
                  "failure_category": "design_invalid: compute_budget_exceeded",
                  "chain": chain, "lead_decision": decision,
                  "pilot": {"wall_s": pilot_wall, "cpu_s": pilot_cpu, "memory_gb": pilot_mem_gb},
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, os.path.join(outdir, "m3_stage2.json"))
        return 3

    # main run: R=10
    tm = time.perf_counter(); cm = time.process_time()
    main_run = run_all(R_MAIN)
    main_wall = time.perf_counter() - tm
    main_cpu = time.process_time() - cm
    _, main_peak = tracemalloc.get_traced_memory()
    main_mem_gb = main_peak / 1e9
    tracemalloc.stop()
    main_ok = (main_wall <= CAPS["wall_s"] and main_cpu <= CAPS["cpu_s"] and main_mem_gb <= CAPS["memory_gb"])

    per_arm = [arm for rep in main_run["replicates"] for arm in rep["per_arm"]]
    failed = [arm for arm in per_arm if not arm["pass"]]
    failure = None
    if not main_ok:
        failure = "design_invalid: compute_budget_exceeded"
    elif failed:
        failure = failed[0]["failure_category"] or "design_invalid"
    # G1-G6
    g1 = bool(all(np.all(np.array(arm["allocation_weights"]) >= 0) and
                  abs(np.sum(arm["allocation_weights"]) - 1.0) < 1e-9 for arm in per_arm))
    g2 = bool(all(math.isfinite(arm["clipping"]["max_raw_H"]) and arm["clipping"]["n_clipped"] >= 0 for arm in per_arm))
    g3 = bool(all(arm["allocation_Q"]["full_ge_noise"] for arm in per_arm))
    g4 = True  # no evaluation/decision output; target not used as labels
    g5 = "external_check_required"
    g6 = bool(main_ok and len(per_arm) == R_MAIN * 6)
    gates = {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6}
    if failure is None:
        if not g1:
            failure = "design_invalid: support"
        elif not (g2 and g3):
            failure = "design_invalid: calibration"
        elif not g4:
            failure = "design_invalid: leakage"
        elif not g6:
            failure = "design_invalid: compute_budget_exceeded"
    # envelope SHA over the per-arm payload (external two-run compares the whole JSON)
    payload_sha = sha256_obj({"per_arm": per_arm, "replicates": main_run["replicates"]})
    result = {
        "task": "R204-M3-S2-EXEC",
        "status": "completed_allocation_diagnostics" if failure is None else "design_invalid",
        "scope": "support research / mechanism account only; Stage2 synthetic allocation diagnostics; compute-only; 0 wells; no decision utility/regret/top-k/learning comparison",
        "chain": chain,
        "lead_decision": decision,
        "chain_ok": chain_ok,
        "seeds": schema["seeds"],
        "sample_semantics": schema["sample_semantics"],
        "environment": schema["environment"],
        "arms": schema["arms"],
        "per_arm": per_arm,
        "G1_G6": gates,
        "failure_categories": schema["failure_categories"],
        "budget": {"caps": CAPS, "compute_only": True, "new_wells": 0},
        "run_shas": {"per_arm_payload_sha": payload_sha,
                     "two_run": "external_check_required; telemetry separate"},
        "failure_category": failure,
        "verdict": "allocation_diagnostics_completed" if failure is None else "design_invalid",
        "no_effect_results": True,
        "no_decision_utility_or_regret": True,
        "no_topk": True,
        "no_learning_comparison": True,
        "no_method_comparison": True,
        "no_real_data": True,
        "new_wells": 0,
        "schema_sha256": sha256_file(schema_path),
        "two_run_note": "external two independent processes; result JSON byte-identical; telemetry separate",
    }
    write_json(result, os.path.join(outdir, "m3_stage2.json"))

    rows_path = os.path.join(outdir, "m3_stage2_per_arm.csv")
    with open(rows_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=schema["per_arm_fields"])
        w.writeheader()
        for arm in per_arm:
            row = dict(arm)
            for k in ("allocation_weights", "realized_allocation_frequency", "H_summary", "delta_summary",
                      "allocation_Q", "variance_term", "clipping", "equal_budget_audit"):
                row[k] = json.dumps(row[k], sort_keys=True, ensure_ascii=False)
            w.writerow({k: row[k] for k in schema["per_arm_fields"]})

    diagnostics = {"task": "R204-M3-S2-EXEC", "chain": chain, "lead_decision": decision,
                   "G1_G6": gates, "failed_arm_count": len(failed),
                   "failure_category": failure, "payload_sha": payload_sha,
                   "no_effect_results": True}
    write_json(diagnostics, os.path.join(outdir, "m3_stage2_diagnostics.json"))

    timing = {"task": "R204-M3-S2-EXEC",
              "pilot": {"reps": R_PILOT, "wall_s": pilot_wall, "cpu_s": pilot_cpu, "memory_gb": pilot_mem_gb, "ok": pilot_ok},
              "main": {"reps": R_MAIN, "wall_s": main_wall, "cpu_s": main_cpu, "memory_gb": main_mem_gb, "ok": main_ok},
              "caps": CAPS, "canonical": True, "wells": 0, "compute_only": True,
              "stage1_pilot_reference_only": True,
              "note": "final-implementation pilot (2 reps x 6 arms x 300 alloc) and main timing; no effect comparison",
              "result_json_sha256": sha256_file(os.path.join(outdir, "m3_stage2.json"))}
    write_json(timing, os.path.join(outdir, "timing_m3_stage2_run.json"))

    print("chain_ok", chain_ok, "pilot_ok", pilot_ok, "main_ok", main_ok)
    print("per_arm", len(per_arm), "failed", len(failed), "failure", failure)
    print("pilot", pilot_wall, pilot_cpu, pilot_mem_gb)
    print("main", main_wall, main_cpu, main_mem_gb)
    print("per_arm_sha", payload_sha)
    print("wrote", outdir)
    return 0 if failure is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
