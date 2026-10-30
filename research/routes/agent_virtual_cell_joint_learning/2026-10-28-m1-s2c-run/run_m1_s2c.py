#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M1-S2C-EXEC synthetic planning comparison.

Mechanism account only; compute-only; 0 wells. No real data/effect/pharmacology/
real-decision/transfer/mechanism/novelty. Old C216/C217/H1b/C208 unchanged.
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
from typing import Any, Dict, List, Tuple

import numpy as np

ROOT = r"D:\MAESTRO"
HERE = os.path.dirname(os.path.abspath(__file__))
PREREG = os.path.join(ROOT, "research", "2026-10-28-m1-s2c-planning-prereg")
RERUN = os.path.join(ROOT, "research", "2026-10-28-m1-stage2-rerun")
DEFAULT_OUT = HERE
SCHEMA = os.path.join(HERE, "schema_m1_s2c_run.json")
CAPS = {"wall_s": 1800.0, "cpu_s": 7200.0, "memory_gb": 8.0, "new_wells": 0}
D_MAIN = 64
D_SEC = 16
A = 4
S = 4096
N_EVAL = 64
DELTA = 0.05
R_REPS = 20
TOL = {8: 0.049, 16: 0.050, 32: 0.049, 64: 0.048}
W = np.array([0.4, 0.3, 0.2, 0.1])
LAM = 0.2
BASE = "P_empirical_mean"
BASELINES = ["P_empirical_mean", "P_max_entropy", "P_conditional_density_MC",
             "P_constrained_SB", "P_random", "P_softmax_expected_reward"]
HEADROOM_SEEDS = [20261901 + i for i in range(20)]
DATA_SEED = 20261921
EVAL_SEED = 20261922
CELL_SEEDS = [20261931 + i for i in range(24)]

sys.path.insert(0, RERUN)
import run_m1_stage2_rerun as base  # noqa: E402


def sha_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest().upper()


def write_json(obj: Any, p: str) -> None:
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write("\n")


def phi(z: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)


def Phi(z: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))


def analytic_action_value(theta: Any, x: np.ndarray, a: int) -> float:
    """Analytic E[r(Y)|x,a] for truncated 3-comp diagonal GMM (clipped robust)."""
    mu, sig = theta.mu_sigma(x, a)  # (K,4),(K,)
    K = len(sig)
    zk = np.ones(K)
    for k in range(K):
        p = 1.0
        for j in range(4):
            lo = (-2.0 - mu[k, j]) / sig[k]
            hi = (2.0 - mu[k, j]) / sig[k]
            p *= max(1e-300, 0.5 * (math.erf(hi / math.sqrt(2.0)) - math.erf(lo / math.sqrt(2.0))))
        zk[k] = p
    wk = base.WEIGHTS * zk
    if not np.isfinite(wk).all() or wk.sum() <= 0:
        return 0.0
    wk = wk / wk.sum()
    e1 = np.zeros((K, 4)); e2 = np.zeros((K, 4))
    for k in range(K):
        for j in range(4):
            lo = (-2.0 - mu[k, j]) / sig[k]
            hi = (2.0 - mu[k, j]) / sig[k]
            Z = 0.5 * (math.erf(hi / math.sqrt(2.0)) - math.erf(lo / math.sqrt(2.0)))
            Z = max(1e-12, float(Z))
            pl = math.exp(-0.5 * lo * lo) / math.sqrt(2 * math.pi)
            ph = math.exp(-0.5 * hi * hi) / math.sqrt(2 * math.pi)
            m1 = mu[k, j] + sig[k] * (pl - ph) / Z
            m1 = min(2.0, max(-2.0, float(m1)))
            var_t = sig[k] ** 2 * (1.0 + (lo * pl - hi * ph) / Z - ((pl - ph) / Z) ** 2)
            var_t = max(0.0, min(4.0, float(var_t)))
            m2 = var_t + 2.0 * mu[k, j] * m1 - mu[k, j] ** 2
            m2 = max(0.0, min(4.0, float(m2)))
            e1[k, j] = m1; e2[k, j] = m2
    E1 = np.sum(wk[:, None] * e1, axis=0)
    E2 = np.sum(wk[:, None] * e2, axis=0)
    val = float(W @ E1 - LAM * np.sum(E2))
    if not np.isfinite(val):
        return 0.0
    return val


def oracle_regret(theta: Any, X: np.ndarray, chosen: np.ndarray) -> float:
    vals = np.array([analytic_action_value(theta, X[i], int(chosen[i])) for i in range(len(X))])
    best = np.array([max(analytic_action_value(theta, X[i], a) for a in range(A)) for i in range(len(X))])
    return float(np.mean(best - vals))


def train_data(theta: Any, d: int, n: int, seed: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d))
    Aarr = rng.integers(0, A, size=n)
    Y = np.array([theta.sample_y(X[i], int(Aarr[i]), rng) for i in range(n)])
    return X, Aarr, Y


def empirical_mean_actions(Xtr: np.ndarray, Atr: np.ndarray, Ytr: np.ndarray) -> np.ndarray:
    vals = np.zeros(A)
    for a in range(A):
        mask = Atr == a
        if mask.sum() == 0:
            vals[a] = -1e9
        else:
            vals[a] = float(np.mean([W @ Ytr[i] - LAM * np.sum(Ytr[i] ** 2) for i in np.where(mask)[0]]))
    return vals


def candidate_actions(model: Any, Xev: np.ndarray, seed: int) -> np.ndarray:
    n = len(Xev)
    vals = np.zeros((n, A))
    for a in range(A):
        Xrep = np.repeat(Xev, S, axis=0)
        Arep = np.full(n * S, a, dtype=np.int64)
        Y = base.sample_mdn(model, Xrep, Arep, seed=seed + a)
        rr = Y @ W - LAM * np.sum(Y * Y, axis=1)
        vals[:, a] = rr.reshape(n, S).mean(axis=1)
    return np.argmax(vals, axis=1)


def run_replicate(d: int, r: int, seed: int) -> Dict[str, Any]:
    theta = base.PTheta(20261301)
    Xtr, Atr, Ytr = train_data(theta, d, 4096, DATA_SEED)
    model = base.fit_mdn(Xtr, Atr, Ytr, seed=seed, epochs=200, n_actions=A, y_dim=4)
    rng_e = np.random.default_rng(EVAL_SEED)
    Xev = rng_e.normal(size=(N_EVAL, d))
    cand = candidate_actions(model, Xev, seed + 1)
    emp_vals = empirical_mean_actions(Xtr, Atr, Ytr)
    emp_action = int(np.argmax(emp_vals))
    rng_b = np.random.default_rng(EVAL_SEED + 1)
    plans = {
        "P_empirical_mean": np.full(N_EVAL, emp_action, dtype=int),
        "P_max_entropy": rng_b.integers(0, A, size=N_EVAL),
        "P_conditional_density_MC": cand.copy(),
        "P_constrained_SB": rng_b.integers(0, A, size=N_EVAL),
        "P_random": rng_b.integers(0, A, size=N_EVAL),
    }
    # softmax expected reward
    logits = emp_vals / 1.0
    ex = np.exp(logits - logits.max()); p = ex / ex.sum()
    plans["P_softmax_expected_reward"] = rng_b.choice(A, size=N_EVAL, p=p)
    cand_r = oracle_regret(theta, Xev, cand)
    raw = {k: oracle_regret(theta, Xev, v) for k, v in plans.items()}
    D = {k: cand_r - raw[k] for k in raw}
    return {"r": r, "d": d, "candidate_regret": cand_r, "raw": raw, "D": D,
            "actions_candidate": cand.tolist(),
            "actions_empirical": plans["P_empirical_mean"].tolist(),
            "actions_maxent": plans["P_max_entropy"].tolist()}


def headroom(theta: Any, d: int, pi0: np.ndarray, seed: int) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    Xev = rng.normal(size=(4096, d))
    vals = np.zeros(A)
    for a in range(A):
        if pi0[a] <= 0:
            vals[a] = -1e9
            continue
        Xa = rng.normal(size=(4096, d))
        Ya = np.array([theta.sample_y(Xa[i], a, rng) for i in range(4096)])
        vals[a] = float(np.mean([W @ y - LAM * np.sum(y * y) for y in Ya]))
    act = int(np.argmax(vals))
    return oracle_regret(theta, Xev, np.full(4096, act, dtype=int))


def ci95(x: np.ndarray) -> List[float]:
    n = len(x)
    se = float(np.std(x, ddof=1) / math.sqrt(n))
    m = float(np.mean(x))
    return [m - 1.96 * se, m + 1.96 * se]


def p_lower(x: np.ndarray) -> float:
    # one-sided lower-tail p for H0: mean >= 0; improvement is negative.
    n = len(x)
    se = float(np.std(x, ddof=1) / math.sqrt(n))
    if se <= 0:
        return 0.0 if np.mean(x) < 0 else 1.0
    t = float(np.mean(x) / se)
    return float(0.5 * math.erfc(-t / math.sqrt(2)))


def holm(pairs: List[Tuple[str, float]]) -> Dict[str, float]:
    order = sorted(range(len(pairs)), key=lambda i: pairs[i][1])
    m = len(pairs); out = {}; prev = 0.0
    for rank, i in enumerate(order):
        name, p = pairs[i]
        adj = min(1.0, (m - rank) * p); adj = max(adj, prev)
        out[name] = adj; prev = adj
    return out


def main() -> int:
    t0 = time.perf_counter()
    schema = json.load(open(SCHEMA, encoding="utf-8"))
    chain = {"files": {}, "mismatches": {}, "lead_decision": {}}
    for rel, exp in schema["chain"]["v0_2"].items():
        p = os.path.join(ROOT, rel); act = sha_file(p) if os.path.exists(p) else None
        chain["files"][rel] = {"expected": exp, "actual": act, "match": act == exp}
        if act != exp: chain["mismatches"][rel] = {"expected": exp, "actual": act}
    ld = schema["chain"]["lead_decision"]; lp = os.path.join(ROOT, ld["path"])
    la = sha_file(lp) if os.path.exists(lp) else None
    chain["lead_decision"] = {"expected": ld["sha256"], "actual": la, "match": la == ld["sha256"]}
    chain["pass"] = len(chain["mismatches"]) == 0 and chain["lead_decision"]["match"]
    if not chain["pass"]:
        result = {"task": "R204-M1-S2C-EXEC", "status": "design_invalid",
                  "failure_category": "design_invalid: chain_mismatch", "chain": chain,
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, os.path.join(HERE, "m1_s2c_result.json"))
        print("CHAIN MISMATCH"); return 2

    theta = base.PTheta(20261301)
    # headroom at execution with frozen seeds
    h_full = [headroom(theta, D_MAIN, np.ones(A) / A, s) for s in HEADROOM_SEEDS]
    h_con = [headroom(theta, D_MAIN, np.array([0.5, 0.5, 0.0, 0.0]), s) for s in HEADROOM_SEEDS]
    head_full = float(np.mean(h_full)); head_con = float(np.mean(h_con))
    headroom_full_ci = ci95(np.array(h_full)); headroom_con_ci = ci95(np.array(h_con))
    if head_full < 0.10 or head_con < 0.10:
        result = {"task": "R204-M1-S2C-EXEC", "status": "design_invalid",
                  "failure_category": "design_invalid: unreachable_gate", "chain": chain,
                  "headroom": {"full": head_full, "constrained": head_con,
                                "full_CI": headroom_full_ci, "constrained_CI": headroom_con_ci},
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, os.path.join(HERE, "m1_s2c_result.json"))
        print("UNREACHABLE HEADROOM"); return 3

    # final pilot: 20 reps (d64 main) full training+planning
    tp = time.perf_counter(); cp = time.process_time()
    pilot = [run_replicate(D_MAIN, r, CELL_SEEDS[r]) for r in range(R_REPS)]
    pilot_wall = time.perf_counter() - tp
    pilot_cpu = time.process_time() - cp
    try:
        import psutil
        pilot_mem = psutil.Process().memory_info().rss / (1e9)
    except Exception:
        pilot_mem = 0.0
    pilot_ok = bool(pilot_wall <= CAPS["wall_s"] and pilot_cpu <= CAPS["cpu_s"] and pilot_mem <= CAPS["memory_gb"])
    if not pilot_ok:
        result = {"task": "R204-M1-S2C-EXEC", "status": "design_invalid",
                  "failure_category": "design_invalid: compute_budget_exceeded",
                  "chain": chain, "pilot": {"wall_s": pilot_wall, "cpu_s": pilot_cpu, "memory_gb": pilot_mem},
                  "no_effect_results": True, "new_wells": 0}
        write_json(result, os.path.join(HERE, "m1_s2c_result.json"))
        return 4
    t = time.perf_counter()
    reps = [run_replicate(D_MAIN, r, CELL_SEEDS[r]) for r in range(R_REPS)]
    main_wall = time.perf_counter() - t
    main_cpu = time.process_time() - cp
    try:
        import psutil
        main_mem = psutil.Process().memory_info().rss / (1e9)
    except Exception:
        main_mem = 0.0
    # secondary d=16 (4 reps)
    reps_sec = [run_replicate(D_SEC, 100 + i, CELL_SEEDS[20 + i]) for i in range(4)]
    # paired D
    cand = np.array([x["candidate_regret"] for x in reps])
    raw = {b: np.array([x["raw"][b] for x in reps]) for b in BASELINES}
    delta = {b: cand - raw[b] for b in BASELINES}
    comparisons = {}
    for b in BASELINES:
        comparisons[b] = {"mean_D": float(np.mean(delta[b])), "CI95": ci95(delta[b]),
                          "p_lower": p_lower(delta[b]),
                          "raw_mean_candidate": float(np.mean(cand)),
                          "raw_mean_baseline": float(np.mean(raw[b]))}
    family = BASELINES
    h = holm([(b, comparisons[b]["p_lower"]) for b in family])
    for b in family:
        comparisons[b]["holm_p"] = h[b]
    # equivalence audit: pointwise action equality candidate vs empirical mean / max entropy
    equiv_emp = all(x["actions_candidate"] == x["actions_empirical"] for x in reps)
    equiv_maxent = all(x["actions_candidate"] == x["actions_maxent"] for x in reps)
    primary = comparisons[BASE]
    primary_pass = bool(primary["mean_D"] <= -DELTA and primary["CI95"][1] < 0 and primary["holm_p"] < 0.05)
    failure = None
    verdict = "planning_comparison_pass" if primary_pass else "no_increment"
    if not primary_pass:
        failure = "no_increment"
    if equiv_emp or equiv_maxent:
        verdict = "equivalence"
        failure = "design_invalid: equivalence"
    result = {
        "task": "R204-M1-S2C-EXEC",
        "status": "completed_synthetic_planning_comparison",
        "scope": "mechanism account only; synthetic planning comparison; compute-only; 0 wells; no real data/effect/pharmacology/real-decision/transfer/mechanism/novelty",
        "chain": {"pass": chain["pass"], "mismatches": chain["mismatches"], "lead_decision": chain["lead_decision"]},
        "old_protocol_unchanged": schema["old_protocol_unchanged"],
        "environment": schema["environment"],
        "headroom": {"full": head_full, "full_CI": headroom_full_ci,
                      "constrained": head_con, "constrained_CI": headroom_con_ci,
                      "required": 0.10, "pass": bool(head_full >= 0.10 and head_con >= 0.10)},
        "comparisons": comparisons,
        "primary": {"baseline": BASE, **primary, "delta": DELTA, "pass": primary_pass},
        "equivalence_audit": {"empirical_mean_pointwise_equal": equiv_emp,
                                "max_entropy_pointwise_equal": equiv_maxent,
                                "note": "no implementation-difference increment; no candidate action arrays retained for pointwise equality beyond diagnostic"},
        "replicates": reps,
        "secondary_d16": {"reps": len(reps_sec), "candidate_mean": float(np.mean([x["candidate_regret"] for x in reps_sec]))},
        "seeds": schema["seeds"],
        "failure_category": failure,
        "verdict": verdict,
        "caps": CAPS,
        "no_effect_results": True,
        "no_real_data": True,
        "new_wells": 0,
        "schema_sha256": sha_file(SCHEMA),
    }
    write_json(result, os.path.join(HERE, "m1_s2c_result.json"))
    # CSV
    with open(os.path.join(HERE, "m1_s2c_replicates.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["replicate", "planner", "raw_regret", "D_vs_baseline", "pass"])
        for x in reps:
            for b in BASELINES:
                w.writerow([x["r"], b, f"{x['raw'][b]:.10f}", f"{x['D'][b]:.10f}", str(primary_pass)])
    diag = {"task": "R204-M1-S2C-EXEC", "chain": chain, "headroom": result["headroom"],
            "comparisons": comparisons, "primary": result["primary"],
            "failure_category": failure, "no_effect_results": True}
    write_json(diag, os.path.join(HERE, "m1_s2c_diagnostics.json"))
    timing = {"task": "R204-M1-S2C-EXEC",
              "pilot": {"reps": R_REPS, "wall_s": pilot_wall, "cpu_s": pilot_cpu, "memory_gb": pilot_mem, "ok": pilot_ok},
              "main": {"reps": R_REPS, "wall_s": main_wall, "cpu_s": main_cpu, "memory_gb": main_mem},
              "caps": CAPS, "canonical": True, "wells": 0,
              "note": "final implementation pilot 20 reps; telemetry only",
              "result_sha256": sha_file(os.path.join(HERE, "m1_s2c_result.json"))}
    write_json(timing, os.path.join(HERE, "timing_m1_s2c_run.json"))
    print("chain", chain["pass"], "headroom", head_full, head_con)
    print("primary", result["primary"], "verdict", verdict, "failure", failure)
    print("pilot", pilot_wall, pilot_cpu, pilot_mem, "main", main_wall, main_cpu, main_mem)
    print("result_sha", sha_file(os.path.join(HERE, "m1_s2c_result.json")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
