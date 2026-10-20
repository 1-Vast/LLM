"""Analytical / synthetic fixtures: they establish IMPLEMENTATION correctness only (branching, exits, identity, KG consistency); they are no evidence of effectiveness.

Aliased fixture world: 30 pairs. Regimes 1,2 share marker pair 0 (+0.35); regimes 3,4 share marker pair 1 (+0.35). Regime r also lifts its own effect pairs
EFF[r] (+0.4). The library knows all four regimes exactly. Noise-free reads make every branch decision exact and hand-checkable.
"""
from __future__ import annotations

import numpy as np

import pi_model as M
import pi_plan as PL

P = 30
EFF = {1: [2, 3, 4, 5, 6, 7], 2: [8, 9, 10, 11, 12, 13], 3: [14, 15, 16, 17, 18, 19], 4: [20, 21, 22, 23, 24, 25]}
MARK = {1: 0, 2: 0, 3: 1, 4: 1}


def profile(r):
    v = np.zeros(P)
    if r:
        v[MARK[r]] = 0.35
        v[EFF[r]] = 0.4
    return v


def fixture_lib():
    L = np.vstack([profile(r) for r in range(5)])
    return M.Lib(L, [4, 4, 4, 4, 4], 0.0013)


def base_a():
    return np.linspace(0.35, 0.45, P)


def camp_for(regime, a=None, noise=0.0, seed=0):
    a = base_a() if a is None else a
    z = np.random.default_rng(seed).standard_normal(P) * noise
    T = a + profile(regime) + z
    return M.Camp(a, T.copy(), T=T)


def branching_plan(lib):
    a = base_a()
    return PL.Plan(0, [0.17], [1, EFF[1][0]], 4, a, np.full(P, 0.05), lib.fingerprint(), bin_mass=[0.5, 0.5])


def kg_vs_monte_carlo(n=200000, seed=0):
    """One-step KG by Gauss-Hermite versus a direct Monte-Carlo estimate from the same generative mixture (consistency of outcome model and update)."""
    lib = fixture_lib()
    a = base_a()
    obs = {}
    w = M.posterior(lib, obs)
    cand = np.array([0, 1, 2, 8, 14])
    kg, cur = M.kg1_all(lib, a, obs, w, cand, G=5)
    rng = np.random.default_rng(seed)
    mc = []
    for p in cand:
        c = rng.choice(lib.C, size=n, p=w)
        r = lib.Lfull[c, p] + lib.sd[c] * rng.standard_normal(n)
        vals = np.empty(n)
        # group by unique rounding is unnecessary: evaluate shortlist value per draw, vectorised over a subsample
        sub = slice(0, 4000)
        v = []
        for ri in r[sub]:
            o = {int(p): float(ri)}
            ww = M.posterior(lib, o)
            v.append(M._topk_mean(M.scores(lib, a, o, ww)))
        mc.append((float(np.mean(v)) - cur, float(np.std(v) / np.sqrt(len(v)))))
    return kg, mc


def run_branching():
    lib = fixture_lib()
    pl = branching_plan(lib)
    out = {}
    for regime in (1, 3):
        row = M.run_campaign(lib, camp_for(regime), 4, pl, arm="plan")
        out[regime] = row
    return lib, pl, out


def run_unknown_exit():
    lib = fixture_lib()
    pl = branching_plan(lib)
    a = base_a()
    T = a.copy()
    T[0] += 0.18                                   # marker pair elevated: first branch fires
    T[26] += 0.9                                    # ... but a pair outside every profile is hugely elevated, so no regime explains the background
    T[1] += 0.9
    camp = M.Camp(a, T.copy(), T=T)
    return M.run_campaign(lib, camp, 4, pl, arm="plan"), lib


def run_stop_branch():
    lib = fixture_lib()
    a = base_a()
    pl = PL.Plan(0, [0.17], [-1, -1], 4, a, np.full(P, 0.05), lib.fingerprint())
    camp = camp_for(3)
    row = M.run_campaign(lib, camp, 4, pl, arm="plan")
    ref = M.run_campaign(lib, camp_for(3), 4, M.Kg1(), arm="kg1")
    return row, ref


def run_inapplicable():
    lib = fixture_lib()
    pl = branching_plan(lib)
    pl2 = PL.Plan(pl.p1, pl.edges, pl.second, 4, pl.aref_mu, pl.aref_sd, "0" * 64)       # validated under another library
    row = M.run_campaign(lib, camp_for(1), 4, pl2, arm="plan")
    ref = M.run_campaign(lib, camp_for(1), 4, M.Kg1(), arm="kg1")
    a = base_a().copy()
    a[5] += 1.0                                                                         # public reference far outside the training range
    row2 = M.run_campaign(lib, camp_for(1, a=a), 4, pl, arm="plan")
    return row, ref, row2
