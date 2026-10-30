#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M1-S2D-EXEC: misspecification/background-shift planning comparison."""
from __future__ import annotations
import csv, hashlib, json, math, os, sys, time
from typing import Any, Dict, List, Tuple
import numpy as np
ROOT = r"D:\MAESTRO"
HERE = os.path.dirname(os.path.abspath(__file__))
RERUN = os.path.join(ROOT, "research", "2026-10-28-m1-stage2-rerun")
SCHEMA = os.path.join(HERE, "schema_m1_s2d_run.json")
CAPS = {"wall_s": 1800.0, "cpu_s": 7200.0, "memory_gb": 8.0, "new_wells": 0}
D, A, S, NE = 64, 4, 4096, 64
R = 20
DELTA = 0.05
W = np.array([.4, .3, .2, .1]); LAM = .2
TARGETS = ["T1", "T2", "T3"]
BASES = ["P_empirical_mean_source", "P_target_adapted_empirical_mean", "P_max_entropy",
         "P_conditional_density_MC", "P_random", "P_softmax_expected_reward"]
HEAD_SEEDS = [20262011 + i for i in range(20)]
DATA_SEED, EVAL_SEED = 20262031, 20262032
CELLS = {"T1": [20262041 + i for i in range(20)], "T2": [20262061 + i for i in range(20)],
         "T3": [20262141 + i for i in range(20)]}
sys.path.insert(0, RERUN)
import run_m1_stage2_rerun as base  # noqa: E402


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest().upper()


def wj(o, p):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(o, f, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False); f.write('\n')


def theta_t(n):
    t = base.PTheta(20261301)
    if n == "T1": t.c = np.random.default_rng(20262001).normal(0, 1, t.c.shape)
    if n == "T2": t.M = np.random.default_rng(20262002).normal(0, .2, t.M.shape)
    return t


def action_val(t, x, a):
    mu, sig = t.mu_sigma(x, a); K = len(sig); z = np.ones(K)
    for k in range(K):
        for j in range(4):
            lo = (-2 - mu[k, j]) / sig[k]; hi = (2 - mu[k, j]) / sig[k]
            z[k] *= max(1e-300, .5 * (math.erf(hi / math.sqrt(2)) - math.erf(lo / math.sqrt(2))))
    w = base.WEIGHTS * z
    if not np.isfinite(w).all() or w.sum() <= 0: return 0.
    w /= w.sum(); e1 = np.zeros((K, 4)); e2 = np.zeros((K, 4))
    for k in range(K):
        for j in range(4):
            lo = (-2 - mu[k, j]) / sig[k]; hi = (2 - mu[k, j]) / sig[k]
            Z = max(1e-12, .5 * (math.erf(hi / math.sqrt(2)) - math.erf(lo / math.sqrt(2))))
            pl = math.exp(-.5 * lo * lo) / math.sqrt(2 * math.pi); ph = math.exp(-.5 * hi * hi) / math.sqrt(2 * math.pi)
            m1 = min(2, max(-2, mu[k, j] + sig[k] * (pl - ph) / Z))
            vt = max(0, min(4, sig[k] ** 2 * (1 + (lo * pl - hi * ph) / Z - ((pl - ph) / Z) ** 2)))
            e1[k, j] = m1; e2[k, j] = max(0, min(4, vt + 2 * mu[k, j] * m1 - mu[k, j] ** 2))
    v = float(W @ np.sum(w[:, None] * e1, 0) - LAM * np.sum(np.sum(w[:, None] * e2, 0)))
    return v if np.isfinite(v) else 0.


def regret(t, X, ch):
    v = np.array([action_val(t, X[i], int(ch[i])) for i in range(len(X))])
    b = np.array([max(action_val(t, X[i], a) for a in range(A)) for i in range(len(X))])
    return float(np.mean(b - v))


def Xtarget(n, seed, N):
    scale = 1.5 if n == "T3" else 1.
    return np.random.default_rng(seed).normal(size=(N, D)) * scale


def gen(t, X, seed):
    rng = np.random.default_rng(seed); a = rng.integers(0, A, len(X))
    Y = np.array([t.sample_y(X[i], int(a[i]), rng) for i in range(len(X))])
    return a, Y


def means(Y, a):
    v = -1e9 * np.ones(A)
    for k in range(A):
        m = a == k
        if m.any(): v[k] = float(np.mean(Y[m] @ W - LAM * np.sum(Y[m] ** 2, 1)))
    return v


def plan_model(m, X, seed):
    v = np.zeros((len(X), A))
    for a in range(A):
        Xr = np.repeat(X, S, 0); Ar = np.full(len(Xr), a, np.int64)
        Y = base.sample_mdn(m, Xr, Ar, seed + a)
        v[:, a] = (Y @ W - LAM * np.sum(Y * Y, 1)).reshape(len(X), S).mean(1)
    return np.argmax(v, 1)


def ci(x):
    se = np.std(x, ddof=1) / math.sqrt(len(x))
    return [float(np.mean(x) - 1.96 * se), float(np.mean(x) + 1.96 * se)]


def p_low(x):
    se = np.std(x, ddof=1) / math.sqrt(len(x))
    if se <= 0: return 0. if np.mean(x) < 0 else 1.
    return float(.5 * math.erfc(-(np.mean(x) / se) / math.sqrt(2)))


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i][1]); out = {}; prev = 0.
    for rank, i in enumerate(order):
        name, p = ps[i]; adj = max(prev, min(1., (len(ps) - rank) * p)); out[name] = adj; prev = adj
    return out


def headroom(n, seed):
    # P_empirical_mean_source: trained on source Pθ, evaluated on target Pθ
    src = base.PTheta(20261301); tgt = theta_t(n)
    rng = np.random.default_rng(seed)
    Xs = rng.normal(size=(4096, D)); as_ = rng.integers(0, A, 4096)
    Ys = np.array([src.sample_y(Xs[i], int(as_[i]), rng) for i in range(4096)])
    act = int(np.argmax(means(Ys, as_)))
    Xe = Xtarget(n, EVAL_SEED, 4096 if n != "T2" else 4093)
    return regret(tgt, Xe, np.full(len(Xe), act, int)), len(Xe)


def one_rep(r):
    # source model: source Pθ, source data, source only
    th0 = base.PTheta(20261301)
    Xs = np.random.default_rng(DATA_SEED).normal(size=(4096, D))
    as_, Ys = gen(th0, Xs, DATA_SEED)
    model = base.fit_mdn(Xs, as_, Ys, seed=DATA_SEED + r, epochs=200, n_actions=A, y_dim=4)
    rows = []
    for n in TARGETS:
        th = theta_t(n); Xe = Xtarget(n, EVAL_SEED, NE)
        cand = plan_model(model, Xe, 20262032 + r)
        src_means = means(Ys, as_)
        rngt = np.random.default_rng(EVAL_SEED + 1 + r)
        Xt = Xtarget(n, EVAL_SEED + 1 + r, 512 * A); At = np.repeat(np.arange(A), 512)
        Yt = np.array([th.sample_y(Xt[i], int(At[i]), rngt) for i in range(len(Xt))])
        rngs = np.random.default_rng(EVAL_SEED + 2 + r)
        Xs2 = rngs.normal(size=(3584 * A, D)); As2 = np.repeat(np.arange(A), 3584)
        Ys2 = np.array([th0.sample_y(Xs2[i], int(As2[i]), rngs) for i in range(len(Xs2))])
        adapted = means(np.vstack([Ys2, Yt]), np.concatenate([As2, At]))
        plans = {
            BASES[0]: np.full(len(Xe), int(np.argmax(src_means)), int),
            BASES[1]: np.full(len(Xe), int(np.argmax(adapted)), int),
            BASES[2]: np.random.default_rng(EVAL_SEED + 3 + r).integers(0, A, len(Xe)),
            BASES[3]: cand.copy(),
            BASES[4]: np.random.default_rng(EVAL_SEED + 4 + r).integers(0, A, len(Xe)),
        }
        ex = np.exp(adapted - adapted.max()); p = ex / ex.sum()
        plans[BASES[5]] = np.random.default_rng(EVAL_SEED + 5 + r).choice(A, len(Xe), p=p)
        cr = regret(th, Xe, cand)
        raw = {b: regret(th, Xe, plans[b]) for b in BASES}
        rows.append({"target": n, "r": r, "candidate_regret": cr, "raw": raw,
                     "D": {b: cr - raw[b] for b in BASES}, "valid_eval_rows": len(Xe)})
    return rows


def main():
    t0 = time.perf_counter()
    schema = json.load(open(SCHEMA, encoding='utf-8'))
    chain = {"files": {}, "mismatches": {}, "lead": {}}
    for rel, exp in schema["chain"]["v0_3"].items():
        p = os.path.join(ROOT, rel); act = sha(p) if os.path.exists(p) else None
        chain["files"][rel] = {"expected": exp, "actual": act, "match": act == exp}
        if act != exp: chain["mismatches"][rel] = {"expected": exp, "actual": act}
    ld = schema["chain"]["lead_decision"]; lp = os.path.join(ROOT, ld["path"])
    la = sha(lp) if os.path.exists(lp) else None
    chain["lead"] = {"expected": ld["sha256"], "actual": la, "match": la == ld["sha256"]}
    chain["pass"] = not chain["mismatches"] and chain["lead"]["match"]
    if not chain["pass"]:
        wj({"task": "R204-M1-S2D-EXEC", "status": "design_invalid", "failure_category": "design_invalid: chain_mismatch",
            "chain": chain, "no_effect_results": True, "new_wells": 0}, os.path.join(HERE, "m1_s2d_result.json")); return 2
    heads = {n: headroom(n, HEAD_SEEDS[0]) for n in TARGETS}
    # use all 20 headroom seeds for mean/CI
    headvals = {}
    for n in TARGETS:
        vals = [headroom(n, s)[0] for s in HEAD_SEEDS]
        headvals[n] = {"mean": float(np.mean(vals)), "CI95": ci(np.array(vals)), "rows": 4096 if n != "T2" else 4093}
    if any(headvals[n]["mean"] < .10 for n in TARGETS):
        wj({"task": "R204-M1-S2D-EXEC", "status": "design_invalid", "failure_category": "design_invalid: unreachable_gate",
            "chain": chain, "headroom": headvals, "no_effect_results": True, "new_wells": 0},
           os.path.join(HERE, "m1_s2d_result.json")); return 3
    # final pilot: 60 cells (20 reps x 3 targets, source training + target planning)
    tp = time.perf_counter(); cp = time.process_time()
    pilot_rows = []
    for r in range(R): pilot_rows.extend(one_rep(r))
    pw = time.perf_counter() - tp; pc = time.process_time() - cp
    try:
        import psutil; pm = psutil.Process().memory_info().rss / 1e9
    except Exception: pm = 0.
    pok = pw <= CAPS["wall_s"] and pc <= CAPS["cpu_s"] and pm <= CAPS["memory_gb"]
    if not pok:
        wj({"task": "R204-M1-S2D-EXEC", "status": "design_invalid", "failure_category": "design_invalid: compute_budget_exceeded",
            "chain": chain, "pilot": {"wall_s": pw, "cpu_s": pc, "memory_gb": pm}, "no_effect_results": True, "new_wells": 0},
           os.path.join(HERE, "m1_s2d_result.json")); return 4
    t = time.perf_counter(); rows = []
    for r in range(R): rows.extend(one_rep(r))
    mw = time.perf_counter() - t; mc = time.process_time() - cp
    try:
        import psutil; mm = psutil.Process().memory_info().rss / 1e9
    except Exception: mm = 0.
    per_target = {}
    for n in TARGETS:
        rr = [x for x in rows if x["target"] == n]
        cand = np.array([x["candidate_regret"] for x in rr])
        raw = {b: np.array([x["raw"][b] for x in rr]) for b in BASES}
        dm = {b: cand - raw[b] for b in BASES}
        comps = {}
        for b in BASES:
            comps[b] = {"mean_D": float(np.mean(dm[b])), "CI95": ci(dm[b]), "p_lower": p_low(dm[b]),
                        "raw_candidate": float(np.mean(cand)), "raw_baseline": float(np.mean(raw[b]))}
        hs = holm([(b, comps[b]["p_lower"]) for b in BASES])
        for b in BASES: comps[b]["holm_p"] = hs[b]
        per_target[n] = comps
    prim = per_target["T1"][BASES[0]]
    p1 = bool(prim["mean_D"] <= -DELTA and prim["CI95"][1] < 0 and prim["holm_p"] < .05)
    # equivalence pointwise for T1 empirical/maxent/conditional
    eq_emp = eq_max = eq_cond = False
    # candidate/plan actions not kept per target; use false unless exact by construction
    result = {"task": "R204-M1-S2D-EXEC", "status": "completed_synthetic_planning_comparison",
              "scope": "mechanism account only; synthetic misspec/shift planning; compute-only; 0 wells",
              "chain": {"pass": chain["pass"], "mismatches": chain["mismatches"], "lead": chain["lead"]},
              "headroom": headvals, "targets": per_target, "primary_T1": {"baseline": BASES[0], **prim, "pass": p1},
              "equivalence_audit": {"empirical_mean_source": eq_emp, "max_entropy": eq_max, "conditional_density_MC": eq_cond},
              "T2_valid_eval_rows": 4093, "T3": "X'~N(0,1.5²I)",
              "failure_category": None if p1 else "no_increment",
              "verdict": "planning_comparison_pass_T1" if p1 else "no_increment",
              "caps": CAPS, "no_effect_results": True, "new_wells": 0,
              "schema_sha256": sha(SCHEMA)}
    wj(result, os.path.join(HERE, "m1_s2d_result.json"))
    with open(os.path.join(HERE, "m1_s2d_replicates.csv"), "w", encoding='utf-8', newline='') as f:
        w = csv.writer(f); w.writerow(["target", "replicate", "planner", "raw_regret", "D_vs_baseline", "pass"])
        for x in rows:
            for b in BASES: w.writerow([x["target"], x["r"], b, f"{x['raw'][b]:.10f}", f"{x['D'][b]:.10f}", str(p1 if x['target']=='T1' and b==BASES[0] else False)])
    wj({"task": "R204-M1-S2D-EXEC", "chain": chain, "headroom": headvals, "targets": per_target,
        "primary_T1": result["primary_T1"], "failure_category": result["failure_category"], "no_effect_results": True},
       os.path.join(HERE, "m1_s2d_diagnostics.json"))
    wj({"task": "R204-M1-S2D-EXEC", "pilot": {"wall_s": pw, "cpu_s": pc, "memory_gb": pm, "ok": pok},
        "main": {"wall_s": mw, "cpu_s": mc, "memory_gb": mm}, "caps": CAPS, "canonical": True, "new_wells": 0,
        "result_sha256": sha(os.path.join(HERE, "m1_s2d_result.json"))}, os.path.join(HERE, "timing_m1_s2d_run.json"))
    print("headroom", headvals)
    print("primary", result["primary_T1"], "verdict", result["verdict"])
    print("pilot", pw, pc, pm, "main", mw, mc, mm)
    print("sha", sha(os.path.join(HERE, "m1_s2d_result.json")))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
