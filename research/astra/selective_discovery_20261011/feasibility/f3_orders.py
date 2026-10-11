"""Feasibility F3 (exploratory; exposed block-N compounds; deterministic arms only).

F2 showed that at a 10% budget annotation-based rankings reach the oracle in many campaigns. F3
asks where headroom remains, by recording each arm's full selection order (to 10% of the pool) and
reading off:
* hits found at 1, 2, 5 and 10% of the pool;
* *unexpected* hits: hits whose annotated mechanism class has no hit for that lineage among the
  reference compounds (what an annotation lookup cannot anticipate);
* hits that replicate on the independent secondary screen (s_T <= -0.25 there), where measured.

Same split, sources and stacks as F2; five seeds.
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

SEEDS = range(5)
POOL_SHARE = 0.6
MAX_FRAC = 0.10
FRACS = (0.01, 0.02, 0.05, 0.10)
BATCH = 6
SETS = {"vc": WM.VC_SOURCES, "novc": ("klass", "target", "chem"), "all": WM.SOURCES}


def order(U, ref, pool, t, arm, stacks, rng, nmax):
    if arm == "random":
        return list(rng.permutation(pool)[:nmax])
    if arm == "oracle":
        s, m = U.selectivity(U.P[pool])
        h = U.hits()[pool, t]
        return list(pool[np.argsort(np.where(h, -10, 0) + s[:, t])[:nmax]])
    if arm == "fixed_class":
        pr = WM.Stack(U, ("klass",)).source_preds(ref, pool, loo=False)["klass"]
        s = np.where(np.isfinite(pr[0][:, t]), pr[0][:, t], 0.0) + 1e-9 * rng.standard_normal(len(pool))
        return list(pool[np.argsort(s)[:nmax]])
    mode, key = arm.split("_")
    if mode == "static":
        p = stacks[key].score(ref, pool)[:, t] + 1e-12 * rng.standard_normal(len(pool))
        return list(pool[np.argsort(-p)[:nmax]])
    known, left, chosen, model = list(ref), list(pool), [], stacks[key]
    while len(chosen) < nmax:
        if mode == "refit" and chosen:
            model = WM.Stack(U, SETS[key]).fit(np.array(known))
        cand = np.array(left)
        p = model.score(np.array(known), cand)[:, t] + 1e-12 * rng.standard_normal(len(cand))
        for c in cand[np.argsort(-p)[: min(BATCH, nmax - len(chosen))]]:
            chosen.append(int(c)); left.remove(int(c)); known.append(int(c))
    return chosen


def main():
    t0 = time.time()
    U = WM.build(include_new=False)
    H = U.hits()
    s2, m2 = U.selectivity(U.S2)
    rep = np.where(np.isfinite(s2), s2 <= -0.25, np.nan)     # secondary replication where measured
    p2 = np.where(U.has_p2)[0]
    arms = ["random", "fixed_class", "static_vc", "static_novc", "static_all", "featfb_all", "refit_vc", "refit_novc",
            "refit_all", "oracle"]
    rows = []
    for seed in SEEDS:
        rng = np.random.default_rng(20261011 + seed)
        pool = np.sort(rng.choice(p2, size=int(POOL_SHARE * len(p2)), replace=False))
        ref = np.setdiff1d(np.arange(len(U.brd)), pool)
        saved = U.sims["vc_cross"]
        U.sims["vc_cross"] = saved.copy()
        U.sims["vc_cross"][:, pool] = np.nan
        stacks = {k: WM.Stack(U, v).fit(ref) for k, v in SETS.items()}
        nmax = int(round(MAX_FRAC * len(pool)))
        for t, T in enumerate(U.lineages):
            known_hit_classes = set(U.moa[ref][H[ref, t]])
            unexpected = H[:, t] & ~np.isin(U.moa, list(known_hit_classes))
            if H[pool, t].sum() == 0:
                continue
            for arm in arms:
                o = order(U, ref, pool, t, arm, stacks, np.random.default_rng(seed * 100 + t), nmax)
                for f in FRACS:
                    b = int(round(f * len(pool)))
                    sel = np.array(o[:b], int)
                    rows.append({"seed": seed, "T": T, "arm": arm, "frac": f, "budget": b,
                                 "hits": int(H[sel, t].sum()), "unexpected": int(unexpected[sel].sum()),
                                 "replicated": int(np.nansum(rep[sel, t] * H[sel, t])),
                                 "pool_hits": int(H[pool, t].sum()), "pool_unexpected": int(unexpected[pool].sum())})
            print(seed, T, round(time.time() - t0, 1), flush=True)
        U.sims["vc_cross"] = saved
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "f3_rows.csv", index=False)
    summ = df.groupby(["frac", "arm"])[["hits", "unexpected", "replicated"]].sum().unstack(0)
    print(summ.to_string())
    caps = df[df.arm == "oracle"].groupby("frac")[["pool_hits", "pool_unexpected"]].sum()
    print(caps.to_string())
    out = {"sum": {f"{a}|{f}": {k: int(df[(df.arm == a) & (df.frac == f)][k].sum()) for k in ("hits", "unexpected", "replicated")}
                   for a in arms for f in FRACS},
           "pool_hits_per_seedT_sum": int(df[(df.arm == "oracle") & (df.frac == 0.1)].pool_hits.sum()),
           "pool_unexpected_sum": int(df[(df.arm == "oracle") & (df.frac == 0.1)].pool_unexpected.sum()),
           "seconds": round(time.time() - t0, 1)}
    (HERE / "f3_orders.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
