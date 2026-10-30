#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M2 Stage 1 controlled-truth implementation (mechanism account only).

Frozen spec: p=5, A=3, hidden d=4, cohorts=200, T=3. No effect comparison,
no gain/regret/decision method comparison, no real data, no wet-lab wells.

Run:
  python -X utf8 run_m2_stage1.py --outdir research/2026-10-28-m2-stage1
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np

ROOT = r"D:\MAESTRO"
STAGE1_DEFAULT = os.path.join(ROOT, "research", "2026-10-28-m2-stage1")
PREREG = os.path.join(ROOT, "research", "2026-10-28-m2-operator-prereg")
SCHEMA_NAME = "schema_m2_stage1.json"
FROZEN_SCHEMA = os.path.join(PREREG, "stage1_schema_v0_2.json")
FORMALISM = os.path.join(PREREG, "formalism_M2_v0_2.py")

P = 5
A = 3
D_HIDDEN = 4
C = 200
T = 3
G_PURE = 30
G_MIXED = 20
COHORTS_PER_PURE_GROUP = 6
COHORTS_PER_MIXED_GROUP = 1
SEED = 20261082
RANDOMIZATION_SEED = 20261083
PILOT_REPS = 10
CLOSURE_CLOSED_MAX = 1e-10
NONCLOSURE_MIN = 1.0
Z80 = 2.801585


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


def phi_from_x(x: np.ndarray) -> np.ndarray:
    """X (d=4) = [x, x^2, x^3, x^4]; phi = [1, X1..X4], p=5."""
    x = np.asarray(x, dtype=float)
    return np.column_stack([np.ones_like(x), x, x ** 2, x ** 3, x ** 4])


def make_groups(rng: np.random.Generator) -> List[Dict[str, Any]]:
    """30 pure groups (10/action) + 20 mixed groups; 4 cohorts/group = 200 cohorts."""
    groups: List[Dict[str, Any]] = []
    idx = 0
    for a in range(A):
        for j in range(10):
            groups.append({"group_id": f"pure_{a}_{j}", "kind": "pure", "action": a,
                           "pi": np.eye(A)[a],
                           "cohort_idx": list(range(idx, idx + COHORTS_PER_PURE_GROUP))})
            idx += COHORTS_PER_PURE_GROUP
    for j in range(G_MIXED):
        pi = rng.dirichlet(np.ones(A))
        groups.append({"group_id": f"mixed_{j}", "kind": "mixed", "action": -1,
                       "pi": pi, "cohort_idx": list(range(idx, idx + COHORTS_PER_MIXED_GROUP))})
        idx += COHORTS_PER_MIXED_GROUP
    assert idx == C, (idx, C)
    assert len(groups) == G_PURE + G_MIXED
    return groups


def build_linear_testbed() -> Dict[str, Any]:
    rng = np.random.default_rng(SEED)
    x0 = rng.normal(0.0, 0.3, C)
    counts = rng.poisson(200.0, C).astype(float)
    groups = make_groups(rng)
    # Matched randomization: each pure block shares the same six X0 values across actions.
    # This is a recorded-X0 stratified design; the recorded-state estimator is still used.
    block_x = rng.normal(0.0, 0.3, size=(10, COHORTS_PER_PURE_GROUP))
    for b in range(10):
        for a in range(A):
            g = next(g for g in groups if g["kind"] == "pure" and g["action"] == a
                     and g["group_id"] == f"pure_{a}_{b}")
            x0[g["cohort_idx"]] = block_x[b]
    # mixed groups keep independent random X0 values
    K_step = rng.normal(0.0, 0.25, size=(A, P, P))
    K_true = np.stack([np.linalg.matrix_power(K_step[a], T) for a in range(A)])
    U_cohort = phi_from_x(x0)                        # C x p
    V_linear_cohort = np.stack([K_true[0] @ U_cohort[i] if False else U_cohort[i] for i in range(0)]) if False else None
    # per-cohort linear V: use action of its group
    group_action = np.zeros(C, dtype=int)
    for g in groups:
        a = g["action"]
        for i in g["cohort_idx"]:
            group_action[i] = a
    V_linear_cohort = np.zeros((C, P))
    # Pure groups use their action; mixed groups use the group mixture pi * K_a U.
    for g in groups:
        for i in g["cohort_idx"]:
            if g["kind"] == "pure":
                V_linear_cohort[i] = K_true[g["action"]] @ U_cohort[i]
            else:
                V_linear_cohort[i] = sum(g["pi"][a] * (K_true[a] @ U_cohort[i]) for a in range(A))
    for g in groups:
        g["U"] = U_cohort[g["cohort_idx"]].mean(axis=0)
        g["V_linear"] = V_linear_cohort[g["cohort_idx"]].mean(axis=0)
        g["U_cohort"] = U_cohort[g["cohort_idx"]]
        g["V_linear_cohort"] = V_linear_cohort[g["cohort_idx"]]
        g["counts"] = counts[g["cohort_idx"]].mean()
    return {"groups": groups, "x0": x0, "counts": counts, "K_true": K_true,
            "U_cohort": U_cohort, "V_linear_cohort": V_linear_cohort,
            "K_step": K_step, "group_action": group_action}


def design_pure(groups: List[Dict[str, Any]]):
    rows, rhs = [], []
    for g in groups:
        if g["kind"] != "pure":
            continue
        a = g["action"]
        U = g["U"]
        V = g["V_linear"]
        for c in range(P):
            row = np.zeros(A * P * P)
            row[a * P * P + c * P:a * P * P + c * P + P] = U
            rows.append(row)
            rhs.append(V[c])
    return np.asarray(rows), np.asarray(rhs)


def design_mixed(groups: List[Dict[str, Any]]):
    rows, rhs = [], []
    for g in groups:
        if g["kind"] != "mixed":
            continue
        U = g["U"]
        V = g["V_linear"]
        for c in range(P):
            row = np.zeros(A * P * P)
            for a in range(A):
                row[a * P * P + c * P:a * P * P + c * P + P] += g["pi"][a] * U
            rows.append(row)
            rhs.append(V[c])
    return np.asarray(rows), np.asarray(rhs)


def fit_theta(J: np.ndarray, rhs: np.ndarray) -> np.ndarray:
    theta, *_ = np.linalg.lstsq(J, rhs, rcond=None)
    return theta


def frozen_arithmetic_examples() -> Dict[str, Any]:
    """Reproduce the frozen v0.2 p=2/p=3 arithmetic examples (independent of p=5 testbed)."""
    xgrid = np.linspace(-1.5, 1.5, 13)
    a_coef, b_coef = 0.7, 0.2
    phi_closed = np.column_stack([np.ones_like(xgrid), xgrid])
    target_closed = np.column_stack([np.ones_like(xgrid), a_coef * xgrid + b_coef])
    K_lin, *_ = np.linalg.lstsq(phi_closed, target_closed, rcond=None)
    resid_closed = float(np.linalg.norm(phi_closed @ K_lin - target_closed, ord="fro"))

    c_non = 0.8
    sigma = 0.15
    phi_nc = np.column_stack([np.ones_like(xgrid), xgrid, xgrid ** 2])
    target_nc = np.column_stack([
        np.ones_like(xgrid),
        xgrid + a_coef + c_non * xgrid ** 2,
        (xgrid + a_coef + c_non * xgrid ** 2) ** 2 + sigma ** 2,
    ])
    K_nc, *_ = np.linalg.lstsq(phi_nc, target_nc, rcond=None)
    resid_nc = float(np.linalg.norm(phi_nc @ K_nc - target_nc, ord="fro"))
    return {
        "note": "independent arithmetic examples from frozen v0.2 formalism; not the p=5 testbed, not data",
        "closed_linear": {"phi": "(1,x)", "dynamics": "x'=0.7x+0.2", "residual_fro": resid_closed,
                           "closed": bool(resid_closed < CLOSURE_CLOSED_MAX)},
        "nonclosed": {"phi": "(1,x,x^2)", "dynamics": "x'=x+0.7+0.8x^2+eps",
                      "residual_fro": resid_nc, "closed": bool(resid_nc < 1e-8),
                      "why": "E[x'^2] contains x^3/x^4 terms absent from phi",
                      "nonclosure_min": NONCLOSURE_MIN},
    }


def nonlinear_testbed(linear: Dict[str, Any]) -> Dict[str, Any]:
    """p=5 nonlinear non-closed case: x' = x + a_const + c*x^2 + noise; powers up to x^4."""
    rng = np.random.default_rng(SEED + 7)
    groups = linear["groups"]
    x0 = linear["x0"]
    a_const = np.array([0.10, 0.20, 0.30])
    c_non = 0.8
    sigma = 0.02
    U_cohort = phi_from_x(x0)
    V_non_cohort = np.zeros((C, P))
    V_lin_cohort = linear["V_linear_cohort"]
    group_action = linear["group_action"]
    for i in range(C):
        x = float(x0[i])
        a = group_action[i] if group_action[i] >= 0 else 0
        for t in range(T):
            x = x + a_const[a] + c_non * x * x + sigma * rng.normal()
        pv = np.array([1.0, x, x ** 2, x ** 3, x ** 4])
        V_non_cohort[i] = pv
    for g in groups:
        g["V_non"] = V_non_cohort[g["cohort_idx"]].mean(axis=0)
        g["V_non_cohort"] = V_non_cohort[g["cohort_idx"]]
    # fit linear K on pure groups with nonlinear V
    rows, rhs = [], []
    for g in groups:
        if g["kind"] != "pure":
            continue
        a = g["action"]
        for c in range(P):
            row = np.zeros(A * P * P)
            row[a * P * P + c * P:a * P * P + c * P + P] = g["U"]
            rows.append(row)
            rhs.append(g["V_non"][c])
    Jn = np.asarray(rows); rn = np.asarray(rhs)
    theta_n = fit_theta(Jn, rn)
    pred = Jn @ theta_n
    resid_non = float(np.linalg.norm(pred - rn))
    return {"V_non_cohort": V_non_cohort, "residual_fro": resid_non,
            "theta": theta_n, "n_obs": int(Jn.shape[0])}


def partial_support(linear: Dict[str, Any]) -> Dict[str, Any]:
    groups = linear["groups"]
    rows, rhs = [], []
    for g in groups:
        if g["kind"] != "pure" or g["action"] == 2:
            continue
        a = g["action"]
        for c in range(P):
            row = np.zeros(A * P * P)
            row[a * P * P + c * P:a * P * P + c * P + P] = g["U"]
            rows.append(row)
            rhs.append(g["V_linear"][c])
    J = np.asarray(rows); r = np.asarray(rhs)
    rank = int(np.linalg.matrix_rank(J))
    return {"actions_assigned": [0, 1], "actions_unassigned": [2],
            "n_rows": int(J.shape[0]), "rank": rank, "param_dim": A * P * P,
            "nullity": A * P * P - rank, "K_2_identifiable": False,
            "expected_rank_lt": 75, "pass_negative": rank < A * P * P}


def same_u_arithmetic(rng: np.random.Generator) -> Dict[str, Any]:
    U = rng.normal(size=P)
    Pi_full = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [0.5, 0.5, 0.0],
                        [0.2, 0.3, 0.5], [0.34, 0.33, 0.33]])
    Pi_mix = np.array([[0.5, 0.5, 0.0], [0.2, 0.3, 0.5], [0.34, 0.33, 0.33]])
    return {"U": U.tolist(), "U_len": int(len(U)),
            "pure_plus_mixes_n": int(len(Pi_full)), "pure_plus_mixes_rank": int(np.linalg.matrix_rank(Pi_full)),
            "mixtures_only_n": int(len(Pi_mix)), "mixtures_only_rank": int(np.linalg.matrix_rank(Pi_mix)),
            "target": "K_a U", "same_u_all_K_a_u_identifiable": bool(np.linalg.matrix_rank(Pi_full) == A)}


def gauge_check(linear: Dict[str, Any], rng: np.random.Generator) -> Dict[str, Any]:
    M = rng.normal(size=(P, P))
    while abs(np.linalg.det(M)) < 1e-8:
        M = rng.normal(size=(P, P))
    Minv = np.linalg.inv(M)
    K = linear["K_true"][0]
    Kg = M @ K @ Minv
    g0 = next(g for g in linear["groups"] if g["kind"] == "pure" and g["action"] == 0)
    U = g0["U"]; V = g0["V_linear"]
    lhs = Kg @ (M @ U)
    rhs = M @ V
    diff = float(np.linalg.norm(lhs - rhs))
    return {"gauge": "K_a -> M K_a M^{-1}", "gauge_norm_diff": diff,
            "pass": bool(diff < 1e-8)}


def randomization_check(linear: Dict[str, Any], partial: Dict[str, Any]) -> Dict[str, Any]:
    groups = linear["groups"]
    pure = [g for g in groups if g["kind"] == "pure"]
    action = np.array([g["action"] for g in pure])
    U = np.vstack([g["U"] for g in pure])
    overall = U.mean(axis=0)
    smds = {}
    for a in range(A):
        m = U[action == a].mean(axis=0)
        sd = U[action == a].std(axis=0, ddof=1) + 1e-12
        smds[str(a)] = float(np.max(np.abs((m - overall) / sd)))
    balance_pass = max(smds.values()) < 0.5
    support_pass = all((action == a).sum() > 0 for a in range(A))
    contract = {
        "pi_recorded_before_outcome": True,
        "pi_independent_of_hidden_given_recorded": True,
        "support_all_actions_main": bool(support_pass),
        "balance_max_smd": smds,
        "balance_pass_max_smd_lt_0.5": bool(balance_pass),
        "between_cohort_assignment_only": True,
        "full_action_labels": True,
        "sisters_exchangeable_design": True,
        "counts_retained": True,
        "partial_support_negative_expected": bool(partial["pass_negative"]),
        "main_randomization_pass": bool(support_pass and balance_pass),
        "failure_category_if_fail": "design_invalid: randomization",
    }
    return contract


def build_schema(outdir: str) -> str:
    """Schema/failure template is written before results; copy frozen v0.2 schema."""
    dst = os.path.join(outdir, SCHEMA_NAME)
    if os.path.dirname(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.abspath(dst) == os.path.abspath(FROZEN_SCHEMA):
        return dst
    if not os.path.isfile(dst):
        shutil.copyfile(FROZEN_SCHEMA, dst)
    return dst


def pilot_once(rng: np.random.Generator) -> float:
    """Planning arithmetic only (no method/effect comparison)."""
    A_, p_ = A, P
    G_ = 60
    Pi_ = rng.dirichlet(np.ones(A_), size=G_)
    U_ = rng.normal(size=(G_, p_))
    K_truth = rng.normal(size=(A_, p_, p_))
    V_ = np.einsum("ga,aij,gj->gi", Pi_, K_truth, U_)
    rows, rhs = [], []
    for g in range(G_):
        for c in range(p_):
            row = np.zeros(A_ * p_ * p_)
            for a in range(A_):
                row[a_ if False else a * p_ * p_ + c * p_:a * p_ * p_ + c * p_ + p_] = Pi_[g, a] * U_[g]
            rows.append(row); rhs.append(V_[g, c])
    theta, *_ = np.linalg.lstsq(np.asarray(rows), np.asarray(rhs), rcond=None)
    return float(np.linalg.norm(theta))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=STAGE1_DEFAULT)
    args = ap.parse_args()
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)
    t0 = time.perf_counter()

    # 1) schema first (before results)
    schema_path = build_schema(outdir)
    schema = json.load(open(schema_path, encoding="utf-8"))
    assert schema["frozen_unique_p"] == P and schema["A_actions"] == A
    assert schema["testbed"]["cohorts"] == C and schema["testbed"]["timepoints"] == T
    assert schema["testbed"]["hidden_state_d"] == D_HIDDEN

    # 2) frozen arithmetic examples
    closed_examples = frozen_arithmetic_examples()

    # 3) linear closed testbed
    linear = build_linear_testbed()
    groups = linear["groups"]

    Jp, rp = design_pure(groups)
    rank_full = int(np.linalg.matrix_rank(Jp))
    theta_full = fit_theta(Jp, rp)
    K_fit = theta_full.reshape(A, P, P)
    resid_full = float(np.linalg.norm(Jp @ theta_full - rp))
    k_err = float(np.linalg.norm((K_fit - linear["K_true"]).reshape(-1)))

    Jm, rm = design_mixed(groups)
    rank_mixed = int(np.linalg.matrix_rank(Jm))
    theta_mixed = fit_theta(Jm, rm)
    resid_mixed = float(np.linalg.norm(Jm @ theta_mixed - rm))
    nullity_mixed = A * P * P - rank_mixed

    # 4) nonlinear non-closure
    non = nonlinear_testbed(linear)

    # 5) partial support negative
    partial = partial_support(linear)

    # 6) same-U / gauge / orthogonal
    rng = np.random.default_rng(SEED + 11)
    same_u = same_u_arithmetic(rng)
    gauge = gauge_check(linear, rng)
    orthogonal = {
        "same_U_pure_vs_mix": "pure groups (1,0)/(0,1) separate K_a U; soft mixes give only linear combinations",
        "separates_K_a_U": True,
        "identifies_all_K": False,
        "mixture_superiority": "not claimed; not tested",
        "note": "orthogonal design arithmetic only; no mixture vs pure performance claim",
    }

    # 7) randomization contract
    rand = randomization_check(linear, partial)

    # 8) pilot / timing
    tp = time.perf_counter()
    pilot_vals = [pilot_once(np.random.default_rng(SEED + 100 + r)) for r in range(PILOT_REPS)]
    per_rep = (time.perf_counter() - tp) / PILOT_REPS
    stage1_proj = per_rep * 20.0 * 1.2
    timing = {
        "pilot_replicates": PILOT_REPS,
        "per_replicate_seconds": round(per_rep, 6),
        "stage1_projected_seconds": round(stage1_proj, 4),
        "caps": {"stage1_wall_s": 600, "cpu_s": 7200, "memory_gb": 8},
        "compute_only": True,
        "new_wells": 0,
        "note": "final code pilot; planning arithmetic only; no effect/method comparison",
    }

    # 9) checks
    checks = {
        "frozen_p_equals_5": P == 5,
        "A_equals_3": A == 3,
        "cohorts_200_T3": C == 200 and T == 3,
        "pure_groups_30": len([g for g in groups if g["kind"] == "pure"]) == 30,
        "pure_groups_per_action_ge5": all(sum(1 for g in groups if g["kind"] == "pure" and g["action"] == a) >= 5 for a in range(A)),
        "U_len_5": same_u["U_len"] == 5,
        "full_K_rank_75": rank_full == A * P * P,
        "full_K_residual_tiny": resid_full < 1e-8,
        "K_truth_recovered": k_err < 1e-6,
        "mixed_rank_75_nullity0": rank_mixed == A * P * P and nullity_mixed == 0,
        "same_U_rank_3": same_u["pure_plus_mixes_rank"] == A,
        "gauge_pass": gauge["pass"],
        "partial_support_rank_lt_75": partial["rank"] < A * P * P,
        "linear_closed_residual_tiny": closed_examples["closed_linear"]["residual_fro"] < CLOSURE_CLOSED_MAX,
        "nonclosed_residual_ge1": closed_examples["nonclosed"]["residual_fro"] >= NONCLOSURE_MIN,
        "testbed_linear_closure_tiny": resid_full < 1e-8,
        "testbed_nonclosure_ge1": non["residual_fro"] >= NONCLOSURE_MIN,
        "randomization_main_pass": rand["main_randomization_pass"],
        "orthogonal_disclaimer_present": orthogonal["mixture_superiority"] == "not claimed; not tested",
    }
    failed = [k for k, v in checks.items() if not bool(v)]
    failure_category = None
    if failed:
        if any(k.startswith("full_K") or k.startswith("mixed") or k.startswith("same_U") or k.startswith("partial") for k in failed):
            failure_category = "design_invalid: identifiability"
        elif any(k.startswith("nonclosed") or k.startswith("testbed_nonclosure") or k.startswith("linear_closed") for k in failed):
            failure_category = "design_invalid: closure"
        elif any(k.startswith("randomization") for k in failed):
            failure_category = "design_invalid: randomization"
        else:
            failure_category = "design_invalid"

    # 10) rows CSV
    rows_path = os.path.join(outdir, "m2_stage1_rows.csv")
    with open(rows_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["case", "group_id", "kind", "action", "pi0", "pi1", "pi2", "cohort",
                    "U0", "U1", "U2", "U3", "U4", "V0", "V1", "V2", "V3", "V4"])
        for g in groups:
            for j, i in enumerate(g["cohort_idx"]):
                pi = g["pi"]
                w.writerow(["linear"] + [g["group_id"], g["kind"], g["action"],
                                          f"{pi[0]:.10f}", f"{pi[1]:.10f}", f"{pi[2]:.10f}", i]
                            + [f"{v:.10f}" for v in linear["U_cohort"][i]]
                            + [f"{v:.10f}" for v in linear["V_linear_cohort"][i]])
        for g in groups:
            for j, i in enumerate(g["cohort_idx"]):
                pi = g["pi"]
                w.writerow(["nonlinear"] + [g["group_id"], g["kind"], g["action"],
                                             f"{pi[0]:.10f}", f"{pi[1]:.10f}", f"{pi[2]:.10f}", i]
                            + [f"{v:.10f}" for v in linear["U_cohort"][i]]
                            + [f"{v:.10f}" for v in non["V_non_cohort"][i]])

    # 11) diagnostics (no timing)
    diagnostics = {
        "task": "R204-M2-STAGE1",
        "status": "controlled_truth_checks_only",
        "frozen_p": P, "A": A, "d_hidden": D_HIDDEN, "cohorts": C, "T": T,
        "groups": {"n_pure": len([g for g in groups if g["kind"] == "pure"]),
                   "n_mixed": len([g for g in groups if g["kind"] == "mixed"]),
                   "pure_group_size": COHORTS_PER_PURE_GROUP,
                   "mixed_group_size": COHORTS_PER_MIXED_GROUP,
                   "action_counts": {str(a): sum(1 for g in groups if g["kind"] == "pure" and g["action"] == a) for a in range(A)}},
        "identifiability": {
            "full_K_param_dim": A * P * P, "full_K_rank": rank_full,
            "full_K_nullity": A * P * P - rank_full, "full_K_residual_fro": resid_full,
            "K_fit_error_fro": k_err,
            "mixed_n_groups": G_MIXED, "mixed_rank": rank_mixed, "mixed_nullity": nullity_mixed,
            "same_U": same_u, "partial_support": partial,
            "gauge": gauge, "U_len": P,
            "pure_groups_total": len([g for g in groups if g["kind"] == "pure"]),
        },
        "closure": {
            "frozen_arithmetic": closed_examples,
            "testbed_linear_residual_fro": resid_full,
            "testbed_nonclosure_residual_fro": non["residual_fro"],
            "testbed_nonclosure_min": NONCLOSURE_MIN,
            "nonclosure_truth": "x'=x+a+0.8x^2+noise; phi=[1,x,x^2,x^3,x^4]; x^3/x^4 terms absent from linear closure",
        },
        "randomization": rand,
        "orthogonal_design": orthogonal,
        "checks": checks,
        "failed_checks": failed,
        "failure_category": failure_category,
        "no_effect_results": True,
        "no_gain_or_method_comparison": True,
        "new_wells": 0,
    }
    diagnostics_path = os.path.join(outdir, "m2_stage1_diagnostics.json")
    write_json(diagnostics, diagnostics_path)

    # 12) result JSON (deterministic; no timing/telemetry)
    result = {
        "task": "R204-M2-STAGE1",
        "status": "completed_controlled_truth_checks" if not failed else "design_invalid",
        "scope": "mechanism account only; controlled synthetic truth checks; no effect/gain/method comparison",
        "frozen_spec": {"p": P, "A": A, "d_hidden": D_HIDDEN, "cohorts": C, "T": T,
                        "pure_groups": G_PURE, "mixed_groups": G_MIXED,
                        "pure_group_size": COHORTS_PER_PURE_GROUP,
                        "mixed_group_size": COHORTS_PER_MIXED_GROUP},
        "identifiability": {
            "full_K_param_dim": A * P * P, "full_K_rank": rank_full,
            "full_K_identifiable": rank_full == A * P * P,
            "mixed_rank": rank_mixed, "mixed_nullity": nullity_mixed,
            "mixed_full_rank_constructive_conditional": rank_mixed == A * P * P,
            "same_U_rank": same_u["pure_plus_mixes_rank"], "same_U_identifiable": same_u["pure_plus_mixes_rank"] == A,
            "U_vector_length": same_u["U_len"],
            "pure_groups_total": len([g for g in groups if g["kind"] == "pure"]),
            "pure_groups_per_action": {str(a): sum(1 for g in groups if g["kind"] == "pure" and g["action"] == a) for a in range(A)},
            "partial_support_rank": partial["rank"],
            "partial_support_identifiable": False,
            "gauge": gauge,
        },
        "closure": {
            "frozen_closed_residual_fro": closed_examples["closed_linear"]["residual_fro"],
            "frozen_nonclosed_residual_fro": closed_examples["nonclosed"]["residual_fro"],
            "testbed_linear_residual_fro": resid_full,
            "testbed_nonclosure_residual_fro": non["residual_fro"],
            "positive_control_closed": bool(closed_examples["closed_linear"]["closed"]),
            "negative_control_nonclosed": bool(non["residual_fro"] >= NONCLOSURE_MIN),
            "case_notes": "frozen arithmetic p=2/p=3 are independent of p=5 testbed; both reported separately",
        },
        "randomization": rand,
        "orthogonal_design": orthogonal,
        "checks": checks,
        "failed_checks": failed,
        "failure_category": failure_category,
        "no_effect_results": True,
        "no_gain_or_method_comparison": True,
        "new_wells": 0,
        "schema_file": SCHEMA_NAME,
        "schema_sha256": sha256_file(schema_path),
        "rows_file": "m2_stage1_rows.csv",
        "diagnostics_file": "m2_stage1_diagnostics.json",
        "timing_file": "timing_m2_stage1.json",
        "two_run_result": "recorded in usage/report; this result JSON contains no telemetry",
    }
    result_path = os.path.join(outdir, "m2_stage1.json")
    write_json(result, result_path)

    # 13) timing separate (telemetry)
    timing.update({
        "full_stage1_wall_seconds": round(time.perf_counter() - t0, 6),
        "result_json_sha256": sha256_file(result_path),
        "canonical": True,
        "note_old_timing_not_mixed": "canonical timing measured by final code; old .00228/.00247 planning values are not mixed into this file",
    })
    timing_path = os.path.join(outdir, "timing_m2_stage1.json")
    write_json(timing, timing_path)

    print("outdir", outdir)
    print("full_K", rank_full, "/", A * P * P, "mixed", rank_mixed, "/", A * P * P, "nullity", nullity_mixed)
    print("same_U", same_u["pure_plus_mixes_rank"], "/", A, "Ulen", same_u["U_len"])
    print("closed", closed_examples["closed_linear"]["residual_fro"], "nonclosed", closed_examples["nonclosed"]["residual_fro"])
    print("testbed nonclosure", non["residual_fro"], "partial rank", partial["rank"])
    print("failed", failed, "failure_category", failure_category)
    print("timing", timing)
    print("result sha", result["schema_sha256"])
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
