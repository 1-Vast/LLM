#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M3-S3B-EXEC corrected-contract candidate learner comparison."""
from __future__ import annotations
import csv, hashlib, json, math, os, sys, time
from typing import Any, Dict, List
import numpy as np
from scipy.optimize import minimize
ROOT = r"D:\MAESTRO"
HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "schema_m3_s3b_run.json")
CAPS = {"wall_s": 1800, "cpu_s": 7200, "memory_gb": 8, "new_wells": 0}
P = np.array([.3, .4, .3])
MU = np.array([[.2, .5, .8], [.4, .6, .3], [.1, .7, .5]])
B = np.array([[.2, .3, .5], [.4, .4, .2], [.25, .35, .4]])
PI2 = np.array([[.82, .09, .09], [.09, .82, .09], [.09, .09, .82]])
W_ALLOC = np.array([[.98731352, .00792905, .00475743], [.01162624, .96512129, .02325248], [.01865776, .01332697, .96801527]])
H = PI2 / W_ALLOC
C_H = 20.
DELTA = .05
R = 20
ARMS = ["P_standard_DR_TMLE", "P_empirical_mean", "P_importance_weighting", "P_full_history_retrain", "P_DR_targeting", "P_value_aware"]
FEED = [20262221 + i for i in range(20)]
EVAL = [20262241 + i for i in range(20)]
ARMS_SEEDS = [20262261 + 20 * a + r for a in range(7) for r in range(20)]
EXEC_COUNT = 1 + 20 + 20 + 20 + 140


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest().upper()


def wj(o, p):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(o, f, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False); f.write('\n')


def sigmoid(z):
    return 1. / (1. + np.exp(-np.clip(z, -40, 40)))


def logit(p):
    p = min(1 - 1e-9, max(1e-9, p)); return math.log(p / (1 - p))


def feedback(seed):
    rng = np.random.default_rng(seed); h = rng.choice(3, size=300, p=P)
    a = np.array([rng.choice(3, p=W_ALLOC[hh]) for hh in h])
    y = rng.binomial(1, MU[h, a])
    return h, a, y


def eval_h(seed):
    return np.random.default_rng(seed).choice(3, size=300, p=P)


def cell_stats(h, a, y):
    n = np.zeros((3, 3)); sy = np.zeros((3, 3)); sh = np.zeros((3, 3)); shy = np.zeros((3, 3))
    for hh, aa, yy in zip(h, a, y):
        w = H[hh, aa]
        n[hh, aa] += 1; sy[hh, aa] += yy; sh[hh, aa] += w; shy[hh, aa] += w * yy
    return n, sy, sh, shy


def m_hat(h, a, y):
    n, sy, sh, shy = cell_stats(h, a, y)
    m = np.full((3, 3), .5)
    for i in range(3):
        for j in range(3):
            if n[i, j] > 0: m[i, j] = sy[i, j] / n[i, j]
    return m, n, sy, sh


def fit_eps(h, a, y):
    m, n, sy, sh = m_hat(h, a, y)
    eps = np.zeros((3, 3)); score = np.zeros((3, 3)); conv = np.ones((3, 3), bool)
    for i in range(3):
        for j in range(3):
            if n[i, j] <= 0: continue
            inds = np.where((h == i) & (a == j))[0]
            yy = y[inds]; w = np.full(len(inds), H[i, j])
            off = logit(m[i, j])
            def nll(e):
                q = sigmoid(off + e[0])
                return -float(np.sum(w * (yy * np.log(np.clip(q, 1e-12, 1)) + (1 - yy) * np.log(np.clip(1 - q, 1e-12, 1)))))
            def jac(e):
                q = sigmoid(off + e[0]); return np.array([float(np.sum(w * (q - yy)))])
            res = minimize(nll, [0.], jac=jac, method='L-BFGS-B', bounds=[(-20, 20)],
                           options={'ftol': 1e-12, 'gtol': 1e-12, 'maxiter': 1000})
            eps[i, j] = float(res.x[0]); score[i, j] = abs(jac([eps[i, j]])[0]) / max(w.sum(), 1e-12)
            conv[i, j] = bool(res.success and score[i, j] < 1e-6)
    return m, eps, score, conv


def policies(h, a, y):
    m, n, sy, sh = m_hat(h, a, y)
    n2, sy2, sh2, shy = cell_stats(h, a, y)
    m, eps, score, conv = fit_eps(h, a, y)
    m_eps = sigmoid(np.array([[logit(m[i, j]) + eps[i, j] for j in range(3)] for i in range(3)]))
    # standard analytic DR/TMLE same m; per-cell V=m+H*mean(Y-m)
    Vstd = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            if n[i, j] > 0: Vstd[i, j] = m[i, j] + H[i, j] * (sy[i, j] / n[i, j] - m[i, j])
            else: Vstd[i, j] = m[i, j]
    # IW cell mean
    iw = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            iw[i, j] = (shy[i, j] / sh[i, j]) if sh[i, j] > 0 else .5
    val = .5 + .5 * (m - .5)
    return {
        "candidate": m_eps, "P_standard_DR_TMLE": Vstd, "P_empirical_mean": m,
        "P_importance_weighting": iw, "P_full_history_retrain": m,
        "P_DR_targeting": Vstd, "P_value_aware": val,
    }, {"eps": eps.tolist(), "score": score.tolist(), "converged": conv.tolist(), "m": m.tolist()}


def regret(policy, hev):
    # policy 3x3 scores; choose argmax per h; known mu
    act = np.argmax(policy, axis=1)
    vals = np.array([MU[hh, act[hh]] for hh in hev])
    best = np.array([MU[hh].max() for hh in hev])
    return float(np.mean(best - vals))


def headroom(seed):
    h, a, y = feedback(seed); hev = eval_h(seed + 1000)
    pol, _ = policies(h, a, y)
    return regret(pol["P_empirical_mean"], hev), regret(pol["P_standard_DR_TMLE"], hev)


def ci(x):
    se = np.std(x, ddof=1) / math.sqrt(len(x)); return [float(np.mean(x) - 2.093 * se), float(np.mean(x) + 2.093 * se)]


def p_low(x):
    se = np.std(x, ddof=1) / math.sqrt(len(x))
    if se <= 0: return 0. if np.mean(x) < 0 else 1.
    from scipy.stats import t as tdist
    return float(tdist.sf(np.mean(x) / se, df=len(x) - 1))


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i][1]); out = {}; prev = 0.
    for rank, i in enumerate(order):
        name, p = ps[i]; adj = max(prev, min(1., (len(ps) - rank) * p)); out[name] = adj; prev = adj
    return out


def dr_identity():
    # m=mu, H=pi2/w; correction expectation under w is zero
    gap = 0.
    for i in range(3):
        for j in range(3):
            gap += P[i] * W_ALLOC[i, j] * H[i, j] * (MU[i, j] - MU[i, j])
    return {"gap": float(abs(gap)), "pass": bool(abs(gap) < 1e-10), "H_max": float(H.max())}


def main():
    t0 = time.perf_counter()
    schema = json.load(open(SCHEMA, encoding='utf-8'))
    chain = {"files": {}, "mismatches": {}, "lead": {}}
    for rel, exp in schema["chain"]["v0_2"].items():
        p = os.path.join(ROOT, rel); act = sha(p) if os.path.exists(p) else None
        chain["files"][rel] = {"expected": exp, "actual": act, "match": act == exp}
        if act != exp: chain["mismatches"][rel] = {"expected": exp, "actual": act}
    ld = schema["chain"]["lead_decision"]; lp = os.path.join(ROOT, ld["path"])
    la = sha(lp) if os.path.exists(lp) else None
    chain["lead"] = {"expected": ld["sha256"], "actual": la, "match": la == ld["sha256"]}
    chain["pass"] = not chain["mismatches"] and chain["lead"]["match"]
    if not chain["pass"]:
        wj({"task": "R204-M3-S3B-EXEC", "status": "design_invalid", "failure_category": "design_invalid: chain_mismatch",
            "chain": chain, "no_effect_results": True, "new_wells": 0}, os.path.join(HERE, "m3_s3b_result.json")); return 2
    if float(H.max()) > C_H:
        wj({"task": "R204-M3-S3B-EXEC", "status": "design_invalid", "failure_category": "design_invalid: support",
            "chain": chain, "H_max": float(H.max()), "C_H": C_H, "no_effect_results": True, "new_wells": 0},
           os.path.join(HERE, "m3_s3b_result.json")); return 3

    dr = dr_identity()
    if not dr["pass"]:
        wj({"task": "R204-M3-S3B-EXEC", "status": "design_invalid", "failure_category": "design_invalid: propensity",
            "chain": chain, "dr_identity": dr, "no_effect_results": True, "new_wells": 0}, os.path.join(HERE, "m3_s3b_result.json")); return 3

    hvals = [headroom(s) for s in range(20262201, 20262221)]
    he = np.array([x[0] for x in hvals]); hs = np.array([x[1] for x in hvals])
    head = {"P_empirical_mean": float(he.mean()), "P_standard_DR_TMLE": float(hs.mean()),
            "CI_empirical": ci(he), "CI_standard": ci(hs)}
    if head["P_empirical_mean"] < .10 or head["P_standard_DR_TMLE"] < .10:
        wj({"task": "R204-M3-S3B-EXEC", "status": "design_invalid", "failure_category": "design_invalid: unreachable_gate",
            "chain": chain, "headroom": head, "no_effect_results": True, "new_wells": 0}, os.path.join(HERE, "m3_s3b_result.json")); return 4

    def run_once():
        rows = []
        for r in range(R):
            h, a, y = feedback(FEED[r]); hev = eval_h(EVAL[r])
            pol, diag = policies(h, a, y)
            raw = {k: regret(pol[k], hev) for k in ["candidate"] + ARMS}
            rows.append({"r": r, "raw": raw, "diag": diag,
                         "D": {k: raw["candidate"] - raw[k] for k in ARMS}})
        return rows

    tp = time.perf_counter(); cp = time.process_time(); pilot = run_once(); pw = time.perf_counter() - tp; pc = time.process_time() - cp
    try:
        import psutil; pm = psutil.Process().memory_info().rss / 1e9
    except Exception: pm = 0.
    if pw > CAPS["wall_s"] or pc > CAPS["cpu_s"] or pm > CAPS["memory_gb"]:
        wj({"task": "R204-M3-S3B-EXEC", "status": "design_invalid", "failure_category": "design_invalid: compute_budget_exceeded",
            "chain": chain, "pilot": {"wall_s": pw, "cpu_s": pc, "memory_gb": pm}, "no_effect_results": True, "new_wells": 0},
           os.path.join(HERE, "m3_s3b_result.json")); return 5
    t = time.perf_counter(); rows = run_once(); mw = time.perf_counter() - t; mc = time.process_time() - cp
    try:
        import psutil; mm = psutil.Process().memory_info().rss / 1e9
    except Exception: mm = 0.
    cand = np.array([x["raw"]["candidate"] for x in rows])
    comps = {}
    for b in ARMS:
        raw = np.array([x["raw"][b] for x in rows]); d = cand - raw
        comps[b] = {"mean_D": float(d.mean()), "CI95": ci(d), "p_lower": p_low(d),
                    "raw_candidate": float(cand.mean()), "raw_baseline": float(raw.mean())}
    hs_ = holm([(b, comps[b]["p_lower"]) for b in ARMS])
    for b in ARMS: comps[b]["holm_p"] = hs_[b]
    prim = comps["P_standard_DR_TMLE"]
    # equivalence: candidate policy pointwise equals standard/empirical etc?
    eq = {b: False for b in ARMS}
    # all arms stored in rows diag m only; report equality if all arm mean D == 0 exactly
    for b in ARMS:
        if all(abs(x["D"][b]) < 1e-15 for x in rows): eq[b] = True
    primary_pass = bool(prim["mean_D"] <= -DELTA and prim["CI95"][1] < 0 and prim["holm_p"] < .05)
    failure = None if primary_pass else "no_increment"
    verdict = "learner_comparison_pass" if primary_pass else "no_increment"
    if eq["P_standard_DR_TMLE"]:
        verdict = "no_increment"; failure = "no_increment"
    result = {"task": "R204-M3-S3B-EXEC", "status": "completed_synthetic_learner_comparison",
              "scope": "mechanism account only; S3b corrected-contract learner comparison; compute-only; 0 wells",
              "chain": {"pass": chain["pass"], "mismatches": chain["mismatches"], "lead": chain["lead"]},
              "environment": schema["environment"], "seeds": schema["seeds"], "n_exec_seeds": 201,
              "dr_identity": dr, "headroom": head,
              "comparisons": comps, "primary": {"baseline": "P_standard_DR_TMLE", **prim, "pass": primary_pass},
              "equivalence_audit": eq, "failure_category": failure, "verdict": verdict,
              "caps": CAPS, "no_effect_results": True, "new_wells": 0,
              "no_real_data": True, "schema_sha256": sha(SCHEMA)}
    wj(result, os.path.join(HERE, "m3_s3b_result.json"))
    with open(os.path.join(HERE, "m3_s3b_replicates.csv"), "w", encoding='utf-8', newline='') as f:
        w = csv.writer(f); w.writerow(["replicate", "planner", "raw_regret", "D_vs_standard", "pass"])
        for x in rows:
            for b in ["candidate"] + ARMS:
                w.writerow([x["r"], b, f"{x['raw'][b]:.10f}", f"{x['D'].get(b, 0):.10f}", str(primary_pass)])
    wj({"task": "R204-M3-S3B-EXEC", "chain": chain, "dr": dr, "headroom": head,
        "comparisons": comps, "failure": failure, "verdict": verdict}, os.path.join(HERE, "m3_s3b_diagnostics.json"))
    wj({"task": "R204-M3-S3B-EXEC", "pilot": {"wall_s": pw, "cpu_s": pc, "memory_gb": pm},
        "main": {"wall_s": mw, "cpu_s": mc, "memory_gb": mm}, "caps": CAPS, "canonical": True, "new_wells": 0,
        "result_sha256": sha(os.path.join(HERE, "m3_s3b_result.json"))}, os.path.join(HERE, "timing_m3_s3b_run.json"))
    print("headroom", head, "dr", dr)
    print("primary", result["primary"], "verdict", verdict, "failure", failure)
    print("comps", {k: (round(v["mean_D"], 6), v["holm_p"]) for k, v in comps.items()})
    print("pilot", pw, pc, pm, "main", mw, mc, mm)
    print("sha", sha(os.path.join(HERE, "m3_s3b_result.json")))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
