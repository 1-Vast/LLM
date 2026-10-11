"""Feasibility F10 (exploratory; exposed block-N compounds): is the unexpected-hit endpoint gameable,
and does a two-stream portfolio agent beat the pooled stack?

F3/F8 made unexpected hits the primary endpoint. Two things must be checked before registering it:

1. **Gaming.** A trivial policy that screens only compounds whose annotated class has no known
   selective member, ranked by the virtual cell, maximises the primary endpoint directly. If it also
   keeps total hits, the endpoint is not a discovery measure and must be replaced or paired with a
   non-inferiority requirement on total hits.
2. **Design.** The two cores are good at different things (F8). A pooled stack dilutes both. A
   portfolio agent instead splits each batch between a *confirm* stream (the best overall ranking)
   and an *explore* stream (the best ranking restricted to classes with no known selective member),
   and moves the split by the yield each stream has returned so far.

Arms (pool 60% of the 542 phase-2 compounds, budget 10%, batch 6, 5 seeds; deterministic, no model calls):
* ``pooled``: F2's refit_all (all sources, refit every round);
* ``novel_only_vc``: candidates restricted to novel classes, ranked by the virtual-cell stack;
* ``novel_only_all``: the same restriction, ranked by the full stack;
* ``portfolio_fixed``: half the batch from each stream;
* ``portfolio_adaptive``: the split follows each stream's observed hit yield (Beta(1,1) posterior
  means, allocation proportional, at least one seat per stream while a stream has candidates).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import world as WM  # noqa: E402
from f6_llm_prior import load  # noqa: E402

SEEDS = range(5)
POOL_SHARE = 0.6
BUDGET_FRAC = 0.10
BATCH = 6


def novel_mask(U, known, t, cand):
    """True where the candidate's annotated class has no selective member for T among ``known``."""
    H = U.hits()
    kn = set(U.moa[np.asarray(known)][H[np.asarray(known), t]])
    kn.discard("nan")
    return ~np.isin(U.moa[cand], list(kn))


def rank(U, known, cand, t, sources, prior, rng):
    st = WM.Stack(U, sources, prior=prior).fit(np.array(known))
    return st.score(np.array(known), cand)[:, t] + 1e-12 * rng.standard_normal(len(cand))


def run(U, ref, pool, t, budget, rng, arm, prior):
    known, left, chosen = list(ref), list(pool), []
    yields = {"confirm": [1.0, 1.0], "explore": [1.0, 1.0]}       # Beta(a, b) per stream
    while len(chosen) < budget:
        cand = np.array(left)
        k = min(BATCH, budget - len(chosen))
        nov = novel_mask(U, known, t, cand)
        if arm == "pooled":
            p = rank(U, known, cand, t, WM.SOURCES + ("llm",), prior, rng)
            take = cand[np.argsort(-p)[:k]]
        elif arm in ("novel_only_vc", "novel_only_all"):
            src = WM.VC_SOURCES if arm.endswith("vc") else WM.SOURCES + ("llm",)
            p = rank(U, known, cand, t, src, prior, rng)
            p = np.where(nov, p, -np.inf)                          # non-novel candidates are never bought
            take = cand[np.argsort(-p)[:k]]
            take = take[np.isfinite(p[np.argsort(-p)[:k]])]
            if len(take) == 0:                                     # NO_NOVEL_CANDIDATE: fall back to the full ranking
                take = cand[np.argsort(-rank(U, known, cand, t, WM.SOURCES + ("llm",), prior, rng))[:k]]
        else:
            p_all = rank(U, known, cand, t, WM.SOURCES + ("llm",), prior, rng)
            p_vc = rank(U, known, cand, t, WM.VC_SOURCES, prior, rng)
            if arm == "portfolio_fixed":
                n_exp = k // 2
            else:
                m = {s: yields[s][0] / (yields[s][0] + yields[s][1]) for s in yields}
                n_exp = int(round(k * m["explore"] / max(m["explore"] + m["confirm"], 1e-9)))
                n_exp = min(max(n_exp, 1), k - 1)
            exp_pool = cand[nov]
            n_exp = min(n_exp, len(exp_pool))
            take_e = exp_pool[np.argsort(-p_vc[nov])[:n_exp]] if n_exp else np.array([], int)
            mask = ~np.isin(cand, take_e)
            take_c = cand[mask][np.argsort(-p_all[mask])[: k - len(take_e)]]
            take = np.concatenate([take_e, take_c])
            H = U.hits()
            for s, sel in (("explore", take_e), ("confirm", take_c)):
                h = int(H[sel, t].sum()) if len(sel) else 0
                yields[s][0] += h
                yields[s][1] += len(sel) - h
        for c in take:
            chosen.append(int(c)); left.remove(int(c)); known.append(int(c))
    return chosen


def main():
    t0 = time.time()
    U = WM.build(include_new=False)
    H = U.hits()
    prior = load("prior", U.brd, U.lineages)
    s2, _ = U.selectivity(U.S2)
    rep = np.where(np.isfinite(s2), s2 <= -0.25, False)
    p2 = np.where(U.has_p2)[0]
    arms = ["pooled", "novel_only_vc", "novel_only_all", "portfolio_fixed", "portfolio_adaptive"]
    rows = []
    for seed in SEEDS:
        rng0 = np.random.default_rng(20261011 + seed)
        pool = np.sort(rng0.choice(p2, size=int(POOL_SHARE * len(p2)), replace=False))
        ref = np.setdiff1d(np.arange(len(U.brd)), pool)
        saved = U.sims["vc_cross"]
        U.sims["vc_cross"] = saved.copy()
        U.sims["vc_cross"][:, pool] = np.nan
        budget = int(round(BUDGET_FRAC * len(pool)))
        for t, T in enumerate(U.lineages):
            if H[pool, t].sum() == 0:
                continue
            kn = set(U.moa[ref][H[ref, t]])
            unexp = H[:, t] & ~np.isin(U.moa, list(kn))
            row = {"seed": seed, "T": T, "pool_hits": int(H[pool, t].sum()), "pool_unexpected": int(unexp[pool].sum())}
            for arm in arms:
                ch = np.array(run(U, ref, pool, t, budget, np.random.default_rng(seed * 100 + t), arm, prior), int)
                row[f"{arm}|hits"] = int(H[ch, t].sum())
                row[f"{arm}|unexpected"] = int(unexp[ch].sum())
                row[f"{arm}|replicated"] = int((rep[ch, t] & H[ch, t]).sum())
            rows.append(row)
            print(row, round(time.time() - t0, 1), flush=True)
        U.sims["vc_cross"] = saved
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "f10_rows.csv", index=False)
    g = df["T"].to_numpy()

    def boot(d, B=4000):
        u = np.unique(g); r = np.random.default_rng(7)
        est = [sum(d[g == x].sum() for x in r.choice(u, len(u))) for _ in range(B)]
        return [float(d.sum()), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))]
    out = {"totals": {c: int(df[c].sum()) for c in df.columns if "|" in c or c.startswith("pool")}, "contrasts": {}}
    for m in ("hits", "unexpected", "replicated"):
        for a in arms:
            if a != "pooled":
                out["contrasts"][f"{a}-pooled|{m}"] = boot((df[f"{a}|{m}"] - df[f"pooled|{m}"]).to_numpy(float))
    print(json.dumps(out, indent=1))
    (HERE / "f10_portfolio.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
