#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M3-P1 formalism/arithmetic only: one-step decision-feedback credit scores.

NO effect run, NO model fit on real/response data, NO method comparison, NO gain claim.
Computes exact one-step DR identities, support/clipping failure diagnostics, score-tilt
updates, allocation second-order terms, planning arithmetic, and baseline equivalence notes.
Writes formalism_M3.json (deterministic) and timing_M3_pilot.json (telemetry only).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "formalism_M3.json")
TIMING = os.path.join(HERE, "timing_M3_pilot.json")
SEED = 20261200
PILOT_REPS = 10
CAPS = {"wall_s": 1800.0, "cpu_s": 7200.0, "memory_gb": 8.0}
TOL = 1e-12


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest().upper()


def write_json(obj, path):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write("\n")


def sanitize(o):
    if isinstance(o, dict):
        return {str(k): sanitize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [sanitize(v) for v in o]
    if isinstance(o, bool):
        return bool(o)
    if isinstance(o, int):
        return int(o)
    if isinstance(o, float):
        if not math.isfinite(o):
            return None
        return float(round(o, 12))
    return o


def sigmoid(x):
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def logit(p):
    p = min(1.0 - 1e-12, max(1e-12, p))
    return math.log(p / (1.0 - p))


# ---------------- categorical known-truth example ----------------
# h in {0,1,2}; a in {0,1,2}; Y in {0,1} with mean mu[h][a]; p(h); behavior b[a|h] known.
P_H = [0.3, 0.4, 0.3]
B = [[0.2, 0.3, 0.5],
     [0.4, 0.4, 0.2],
     [0.25, 0.35, 0.40]]
MU = [[0.20, 0.50, 0.80],
      [0.40, 0.60, 0.30],
      [0.10, 0.70, 0.50]]
PI = {
    "pi_1": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    "pi_2": [[0.2, 0.5, 0.3], [0.5, 0.2, 0.3], [0.3, 0.3, 0.4]],
}
M_TRUE = MU
M_WRONG = [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, 0.5]]


def policy_value(pi, mu):
    return sum(P_H[h] * sum(pi[h][a] * mu[h][a] for a in range(3)) for h in range(3))


def dr_expectation(pi, mu, m, b=B):
    """E_{h~p, a~b, Y~Bernoulli(mu)}[ sum_a' pi m + H(Y - m) ], no clipping."""
    total = 0.0
    for h in range(3):
        for a in range(3):
            if b[h][a] <= 0:
                continue
            H = pi[h][a] / b[h][a]
            total += P_H[h] * b[h][a] * (sum(pi[h][ap] * m[h][ap] for ap in range(3)) + H * (mu[h][a] - m[h][a]))
    return total


def dr_identity():
    rows = {}
    for name, pi in PI.items():
        exact = policy_value(pi, MU)
        true_m = dr_expectation(pi, MU, M_TRUE)
        wrong_m = dr_expectation(pi, MU, M_WRONG)
        rows[name] = {"exact_policy_value": exact,
                      "dr_expected_value_true_m": true_m,
                      "dr_expected_value_wrong_m": wrong_m,
                      "max_abs_gap_true_m": abs(exact - true_m),
                      "max_abs_gap_wrong_m": abs(exact - wrong_m)}
    gaps = [abs(v["exact_policy_value"] - v["dr_expected_value_true_m"]) for v in rows.values()]
    gaps += [abs(v["exact_policy_value"] - v["dr_expected_value_wrong_m"]) for v in rows.values()]
    return {"section": "one_step_DR_identity",
            "assumption": "h known; b(a|h)>0 on pi support; evaluation sample independent of m/pi selection; m arbitrary",
            "rows": rows, "max_abs_gap": max(gaps), "pass": max(gaps) <= TOL,
            "note": "double robustness with known behavior b: E_b[H(Y-m)] + E_pi[m] equals V(pi) exactly; this is standard DR, not a new claim"}


def support_positivity():
    # context 0 action 2 has b=0; a policy placing mass there is not identified.
    pi_unsupported = [[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    h, a = 0, 2
    b_zero = [row[:] for row in B]
    b_zero[h][a] = 0.0
    supported = b_zero[h][a] > 0
    return {"section": "support_positivity",
            "counterexample": {"h": h, "a": a, "b": 0.0, "pi_mass": pi_unsupported[h][a]},
            "supported": supported,
            "identified": bool(supported),
            "classification": "design_invalid: positivity/support if pi uses unsupported action",
            "note": "zero support makes H undefined; no DR correction can identify the policy value; report unidentified, do not impute"}


def clipping_bias():
    # tiny but positive support; cap H at C; show bias of clipped DR vs exact.
    b = [row[:] for row in B]
    b[0][2] = 0.001
    norm = [sum(row) for row in b]
    b = [[v / norm[h] for v in b[h]] for h in range(3)]  # renormalize behavior
    pi = [[1.0 / 3.0] * 3 for _ in range(3)]
    cap = 20.0
    exact = policy_value(pi, MU)
    clipped = 0.0
    raw_weights = []
    clipped_weights = []
    for h in range(3):
        for a in range(3):
            H = pi[h][a] / b[h][a]
            Hc = min(H, cap)
            raw_weights.append(H)
            clipped_weights.append(Hc)
            clipped += P_H[h] * b[h][a] * (
                sum(pi[h][ap] * M_WRONG[h][ap] for ap in range(3)) + Hc * (MU[h][a] - M_WRONG[h][a]))
    return {"section": "weight_clipping_bias",
            "behavior_renormalized": b, "cap": cap,
            "exact_policy_value": exact, "clipped_dr_expected_value": clipped,
            "bias": clipped - exact, "max_raw_weight": max(raw_weights),
            "n_weights_clipped": int(sum(1 for w in raw_weights if w > cap)),
            "detected": bool(abs(clipped - exact) > TOL),
            "note": "predetermined clipping clips weights but changes the estimand; report bias/bound; do not present clipped estimate as exact policy value"}


def score_tilt():
    # binary action, one context: b=[.5,.5], pi=[.8,.2], Y Bernoulli(mu=[.2,.8]), m0=[.5,.5]
    b = [0.5, 0.5]
    pi = [0.8, 0.2]
    H = [pi[a] / b[a] for a in range(2)]
    mu = [0.2, 0.8]
    m0 = [0.5, 0.5]

    def score(eps):
        m_eps = [sigmoid(logit(m0[a]) + eps * H[a]) for a in range(2)]
        return sum(b[a] * H[a] * (mu[a] - m_eps[a]) for a in range(2))

    s0 = score(0.0)
    lo, hi = -20.0, 20.0
    # bisection on sign change
    f_lo, f_hi = score(lo), score(hi)
    root = None
    if f_lo * f_hi <= 0:
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            fm = score(mid)
            if abs(fm) < 1e-14:
                root = mid
                break
            if f_lo * fm <= 0:
                hi = mid
                f_hi = fm
            else:
                lo = mid
                f_lo = fm
        if root is None:
            root = 0.5 * (lo + hi)
    # collinear two-score design: H1=2*H2 -> rank 1, epsilon not unique
    H_coll = [[1.6, 0.4], [0.8, 0.2]]  # rows: two score vectors, proportional
    rank = np_rank(H_coll)
    # finite-sample separation example: all observed Y=0 for an action with positive H; score cannot cross zero finitely
    separation = {"all_Y_zero_positive_H": True,
                  "score_at_minus_inf": 0.0,
                  "score_at_zero": None,
                  "finite_root_guaranteed": False}
    return {"section": "score_tilt_update",
            "setup": {"b": b, "pi": pi, "H": H, "mu": mu, "m0": m0,
                      "m_eps": "logit m_eps = logit m0 + sum_k eps_k H_k"},
            "score_at_eps0": s0, "epsilon_root": root,
            "score_at_root": score(root) if root is not None else None,
            "collinear_scores_rank": rank, "collinear_expected_rank": 1,
            "collinearity_nonunique": bool(rank < 2),
            "finite_sample_separation_risk": separation,
            "note": "root exists in this simple example; with separation/collinearity or H non-identifiability, eps need not be finite/unique; pre-register clipping and non-identification reporting",
            "pass": bool(root is not None and abs(score(root)) <= 1e-10)}


def np_rank(rows):
    # small Gaussian elimination rank
    mat = [[float(x) for x in row] for row in rows]
    n = len(mat)
    m = len(mat[0])
    rank = 0
    for col in range(m):
        pivot = None
        for r in range(rank, n):
            if abs(mat[r][col]) > 1e-12:
                pivot = r
                break
        if pivot is None:
            continue
        mat[rank], mat[pivot] = mat[pivot], mat[rank]
        pv = mat[rank][col]
        mat[rank] = [v / pv for v in mat[rank]]
        for r in range(n):
            if r != rank and abs(mat[r][col]) > 1e-15:
                f = mat[r][col]
                mat[r] = [a - f * b_ for a, b_ in zip(mat[r], mat[rank])]
        rank += 1
    return rank


def allocation_second_order():
    """For frozen m: E[pi^2 (Var + (E-m)^2)/b] is the chi-square contribution to Var of DR score."""
    rows = {}
    for name, pi in PI.items():
        noise = 0.0
        full = 0.0
        for h in range(3):
            for a in range(3):
                var = MU[h][a] * (1.0 - MU[h][a])
                pi2 = pi[h][a] ** 2
                noise += P_H[h] * pi2 * var / B[h][a]
                full += P_H[h] * pi2 * (var + (MU[h][a] - M_WRONG[h][a]) ** 2) / B[h][a]
        rows[name] = {"noise_only_term": noise, "full_second_order_term": full,
                      "bias_squared_contribution": full - noise,
                      "ratio_full_over_noise": (full / noise) if noise > 0 else None}
    # alternative allocation concentrated on larger b for one action; show full term changes
    b_alt = [[0.6, 0.2, 0.2], [0.2, 0.6, 0.2], [0.2, 0.2, 0.6]]
    alt = {}
    for name, pi in PI.items():
        full_alt = 0.0
        for h in range(3):
            for a in range(3):
                var = MU[h][a] * (1.0 - MU[h][a])
                full_alt += P_H[h] * pi[h][a] ** 2 * (var + (MU[h][a] - M_WRONG[h][a]) ** 2) / b_alt[h][a]
        alt[name] = full_alt
    return {"section": "shared_score_allocation_second_order",
            "formula": "sum_a pi_k(a|h)^2 [Var(Y|h,a) + (E[Y|h,a]-m_theta(h,a))^2] / b(a|h)",
            "rows_frozen_m": rows, "alt_allocation_full_term": alt,
            "misspecification_note": "under model misspecification the bias-square term is nonzero and unknown; allocate by noise only is insufficient; use estimate/conservative bound",
            "all_full_ge_noise": bool(all(rows[k]["full_second_order_term"] >= rows[k]["noise_only_term"] for k in rows))}


def planning_arithmetic():
    n_units = 300
    deff = 2.2
    n_eff = n_units / deff
    sd = 0.20
    delta = 0.05
    z = 2.8015852181
    mde = z * sd / math.sqrt(n_eff)
    n_req_ind = math.ceil((z * sd / delta) ** 2)
    n_req_cluster = math.ceil(n_req_ind * deff)
    headroom = {"U_max": 1.0, "U0_B2_example": 0.90, "headroom": 0.10, "delta": delta,
                "headroom_ok": bool(0.10 >= delta),
                "near_ceiling": False,
                "note": "example only; headroom must be checked on independent pre-effect data before any execution"}
    fisher_z = {"delta_0.05": 2 * (z / 0.05) ** 2 + 3,
                "delta_0.10": 2 * (z / 0.10) ** 2 + 3,
                "scope": "Fisher-z comparison planning only; NOT a universal decision-evidence gate and NOT a paired DR sample-size formula"}
    return {"section": "planning_arithmetic",
            "n_units": n_units, "deff": deff, "n_eff": n_eff, "conservative_SD_D": sd,
            "MDE80": mde, "MDE80_le_delta": bool(mde <= delta),
            "n_req_independent": n_req_ind, "n_req_cluster": n_req_cluster,
            "n_req_le_n_units": bool(n_req_cluster <= n_units),
            "headroom_example": headroom,
            "fisher_z_only": fisher_z,
            "cluster_note": "primary analysis must cluster by independent culture/background/task; wells/technical repeats are not independent units"}


def baseline_degeneracy():
    # If pi == b then H=1 and the one-step linear score is just the mean residual (weighted residual).
    pi = B  # same as behavior
    gap = 0.0
    rows = []
    for h in range(3):
        for a in range(3):
            H = pi[h][a] / B[h][a]
            gap = max(gap, abs(H - 1.0))
            rows.append({"h": h, "a": a, "H": H})
    return {"section": "standard_baseline_degeneracy",
            "condition": "pi_k == b => H_k = 1",
            "max_abs_H_minus_1": gap,
            "one_step_linear_score": "sum_{h,a} b(a|h) H(h,a)(Y - phi(h,a)^T theta) becomes an ordinary weighted residual when H=1",
            "implication": "one-step linear version can degenerates to weighted residual regression; preserve equivalent result and withdraw any deep-world-model novelty claim",
            "baselines_required": ["full-history retrain", "importance weighting", "DR/TMLE targeting",
                                   "value-aware model learning", "hierarchical/GP", "BATCHIE adaptation"],
            "same_budget_note": "same features/knowledge/feedback/tuning<=20/compute caps; standard DR/TMLE + allocation equal-budget replication -> withdraw M3 algorithm claim",
            "scope_note": "updating only the functional mean is NOT a cell-dynamics-compatible update; no sequential DR claim without full history/propensity/censoring"}


def failure_and_stage_plan():
    return {
        "section": "three_stage_validation_plan_not_run",
        "stage_1": {
            "name": "one-step synthetic known truth",
            "checks": ["DR/TMLE identity and double robustness", "predetermined weight clipping bias",
                       "zero/near-zero support positivity", "misspecification counterexample",
                       "collinear score / separation non-uniqueness"],
            "outputs": "diagnostics only; no method comparison or gain",
            "status": "not_run"
        },
        "stage_2": {
            "name": "fixed updater compare allocation",
            "arms": ["shared-score allocation", "random allocation", "GP/uncertainty allocation",
                     "decision-AL allocation", "DR+MLE allocation"],
            "condition": "same updater, same feedback budget, same features/knowledge/tuning; compare allocation only",
            "status": "not_run"
        },
        "stage_3": {
            "name": "fixed feedback compare learning; then closed-loop cost",
            "arms": ["candidate one-step score-tilt update", "full-history retrain", "importance weighting",
                     "DR targeting", "TMLE targeting"],
            "endpoint": "independent functional decision utility/regret; delta=.05 normalized; headroom/MDE/cluster checked first; 6,282 Fisher-z only; secondary prediction calibration/DR scores/RNA",
            "status": "not_run"
        },
        "closure": {"require": "closed-loop cost accounting (culture/plate/control/failure/repeats/calibration/compute/tuning)",
                    "status": "not_run"},
        "failure_categories": ["design_invalid: support", "design_invalid: positivity", "design_invalid: propensity",
                               "design_invalid: leakage", "design_invalid: calibration",
                               "design_invalid: compute_budget_exceeded", "unreachable_gate",
                               "precision_insufficient", "no_increment", "inconclusive"],
        "stop_rules": ["standard DR/TMLE + allocation equal-budget replication -> withdraw",
                       "extreme weights/zero support -> unidentified",
                       "evaluation sample reused for policy selection -> leakage",
                       "functional-head calibration only -> not a cell-dynamics claim"],
        "caps": CAPS, "wells": 0, "compute_only": True,
        "real_data": "data_unavailable (C203/C205); no real execution or substitution by synthetic/RNA"
    }


def run_core():
    t0 = time.time()
    dr = dr_identity()
    sup = support_positivity()
    clip = clipping_bias()
    tilt = score_tilt()
    alloc = allocation_second_order()
    plan = planning_arithmetic()
    base = baseline_degeneracy()
    failure = failure_and_stage_plan()
    checks = {
        "dr_identity_pass": bool(dr["pass"]),
        "support_counterexample_detected": bool(not sup["supported"] and not sup["identified"]),
        "clipping_bias_detected": bool(clip["detected"]),
        "score_tilt_root_pass": bool(tilt["pass"]),
        "collinearity_nonunique_detected": bool(tilt["collinearity_nonunique"]),
        "allocation_full_ge_noise": bool(alloc["all_full_ge_noise"]),
        "planning_MDE_le_delta": bool(plan["MDE80_le_delta"]),
        "n_req_le_n_units": bool(plan["n_req_le_n_units"]),
        "baseline_degeneracy_H_equals_1": bool(base["max_abs_H_minus_1"] <= TOL),
    }
    obj = {
        "task": "R204-M3-P1",
        "status": "formalism_only_no_effect",
        "seed": SEED,
        "notation": {
            "h": "known background/history",
            "a": "action", "Y": "independent functional outcome in [0,1]",
            "b": "recorded randomized behavior assignment probability, known",
            "pi_k": "frozen candidate policy",
            "H_k": "pi_k(a|h)/b(a|h)",
            "delta_k": "E[H_k(Y-m_theta)]",
            "policy_value": "E_h sum_a pi_k(a|h) m_theta(h,a) + delta_k",
            "standard": "DR/importance-correction; evaluation sample must be independent of model fit/policy selection; no novelty claim",
        },
        "one_step_DR": dr,
        "support_positivity": sup,
        "clipping_bias": clip,
        "score_tilt_update": tilt,
        "allocation_second_order": alloc,
        "planning_arithmetic": plan,
        "standard_baselines": base,
        "three_stage_plan": failure,
        "checks": checks,
        "all_checks_pass": bool(all(checks.values())),
        "boundaries": ["support research only; not a cell-dynamics-compatible update",
                       "no pharmacology/real decision/transfer/mechanism/novelty claim",
                       "no effect comparison or gain claim",
                       "no code promotion; no old verdict/threshold change",
                       "synthetic compute-only 0 wells; real data currently data_unavailable (C203/C205)"],
    }
    return obj, time.time() - t0


def main():
    obj, elapsed = run_core()
    write_json(sanitize(obj), OUT)
    reps = []
    t0 = time.time()
    for _ in range(PILOT_REPS):
        _, dt = run_core()
        reps.append(dt)
    wall = time.time() - t0
    timing = {
        "task": "R204-M3-P1", "pilot_reps": PILOT_REPS,
        "per_rep_seconds": reps,
        "mean_per_rep_seconds": sum(reps) / len(reps),
        "wall_seconds": wall,
        "caps": CAPS,
        "wells": 0, "compute_only": True,
        "note": "formalism/arithmetic timing only; no effect run; no method comparison",
        "formalism_json_sha256": sha256_file(OUT),
    }
    write_json(sanitize(timing), TIMING)
    print("all_checks_pass", obj["all_checks_pass"], "sha", sha256_file(OUT))
    print("per_rep_mean", timing["mean_per_rep_seconds"], "wall", wall)


if __name__ == "__main__":
    main()
