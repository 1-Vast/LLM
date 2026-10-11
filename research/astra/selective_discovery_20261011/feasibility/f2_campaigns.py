"""Feasibility F2 (exploratory; exposed block-N compounds; deterministic arms only, no model calls).

Mimics the confirmation structure on development data:
* pool = 60% of the 542 block-N compounds with GSE70138 signatures (treated like new compounds:
  their GSE92742 signatures are never used, as query or reference);
* reference = all other block-N compounds (P2 references + GSE92742-only references).

A campaign = (seed, target lineage). Budget = 10% of the pool, batches of 6. Screening reveals the
full PRISM profile. Arms:
* random; fixed_class (annotated class mean from the reference, one batch);
* static_{vc,novc,all}: stacked hit model fit on the reference, one batch;
* featfb_{vc,novc,all}: same weights, but source predictions use reference + screened compounds;
* refit_{vc,novc,all}: weights refit on reference + screened each round;
* oracle.
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
import world as WM  # noqa: E402

SEEDS = (0, 1, 2)
POOL_SHARE = 0.6
BUDGET_FRAC = 0.10
BATCH = 6
SETS = {"vc": WM.VC_SOURCES, "novc": ("klass", "target", "chem"), "all": WM.SOURCES}


def campaign(U, hits, ref, pool, t, arm, stacks, rng):
    budget = int(round(BUDGET_FRAC * len(pool)))
    if arm == "random":
        pick = rng.choice(pool, size=budget, replace=False)
        return int(hits[pick, t].sum()), list(pick)
    if arm == "oracle":
        s, m = U.selectivity(U.P[pool])
        score = np.where(hits[pool, t], -10, 0) + s[:, t]
        pick = pool[np.argsort(score)[:budget]]
        return int(hits[pick, t].sum()), list(pick)
    if arm == "fixed_class":
        st = WM.Stack(U, ("klass",))
        pr = st.source_preds(ref, pool, loo=False)["klass"]
        s = np.where(np.isfinite(pr[0][:, t]), pr[0][:, t], 0.0) + 1e-9 * rng.standard_normal(len(pool))
        pick = pool[np.argsort(s)[:budget]]
        return int(hits[pick, t].sum()), list(pick)
    mode, key = arm.split("_")
    st = stacks[key]
    if mode == "static":
        p = st.score(ref, pool)[:, t] + 1e-12 * rng.standard_normal(len(pool))
        pick = pool[np.argsort(-p)[:budget]]
        return int(hits[pick, t].sum()), list(pick)
    known = list(ref)
    left = list(pool)
    chosen = []
    model = st
    while len(chosen) < budget:
        if mode == "refit" and chosen:
            model = WM.Stack(U, SETS[key]).fit(np.array(known))
        cand = np.array(left)
        p = model.score(np.array(known), cand)[:, t] + 1e-12 * rng.standard_normal(len(cand))
        take = cand[np.argsort(-p)[: min(BATCH, budget - len(chosen))]]
        for c in take:
            chosen.append(int(c))
            left.remove(int(c))
            known.append(int(c))
    return int(hits[chosen, t].sum()), chosen


def main():
    t0 = time.time()
    U = WM.build(include_new=False)
    hits = U.hits()
    print("built", round(time.time() - t0, 1), "hits", int(hits.sum()), flush=True)
    p2 = np.where(U.has_p2)[0]
    rows = []
    arms = ["random", "fixed_class", "static_vc", "static_novc", "static_all", "featfb_vc", "featfb_novc", "featfb_all",
            "refit_vc", "refit_novc", "refit_all", "oracle"]
    for seed in SEEDS:
        rng = np.random.default_rng(20261011 + seed)
        pool = np.sort(rng.choice(p2, size=int(POOL_SHARE * len(p2)), replace=False))
        ref = np.setdiff1d(np.arange(len(U.brd)), pool)
        has_p1_saved = U.has_p1.copy()
        cross_saved = U.sims["vc_cross"]
        U.sims["vc_cross"] = cross_saved.copy()
        U.sims["vc_cross"][:, pool] = np.nan          # pool compounds never serve as GSE92742 references
        stacks = {k: WM.Stack(U, v).fit(ref) for k, v in SETS.items()}
        coef = {k: dict(zip([f"{s}:{f}" for s in v for f in ("s", "m", "miss", "top")],
                            np.round(stacks[k].model.coef_[0][: 4 * len(v)], 3).tolist())) for k, v in SETS.items()}
        print("seed", seed, "stack coef (all)", coef["all"], flush=True)
        for t, T in enumerate(U.lineages):
            npool = int(hits[pool, t].sum())
            row = {"seed": seed, "T": T, "pool_hits": npool, "budget": int(round(BUDGET_FRAC * len(pool)))}
            for arm in arms:
                row[arm], _ = campaign(U, hits, ref, pool, t, arm, stacks, np.random.default_rng(seed * 100 + t))
            rows.append(row)
            print(seed, T, {a: row[a] for a in arms}, round(time.time() - t0, 1), flush=True)
        U.sims["vc_cross"] = cross_saved
        U.has_p1 = has_p1_saved
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "f2_rows.csv", index=False)
    tot = {a: int(df[a].sum()) for a in arms}
    tot["pool_hits"] = int(df.pool_hits.sum())
    tot["capacity"] = int(np.minimum(df.pool_hits, df.budget).sum())
    print(json.dumps(tot, indent=1))

    def boot(d, B=4000):
        g = df["T"].to_numpy()
        u = np.unique(g)
        r = np.random.default_rng(7)
        est = [sum(d[g == x].sum() for x in r.choice(u, len(u))) for _ in range(B)]
        return [float(d.sum()), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))]
    con = {
        "vc_value_static (all-novc)": df.static_all - df.static_novc,
        "vc_value_refit (all-novc)": df.refit_all - df.refit_novc,
        "feedback_all (refit-static)": df.refit_all - df.static_all,
        "feedback_novc (refit-static)": df.refit_novc - df.static_novc,
        "feedback_vc (refit-static)": df.refit_vc - df.static_vc,
        "interaction (fb_all - fb_novc)": (df.refit_all - df.static_all) - (df.refit_novc - df.static_novc),
        "refit_vs_featfb_all": df.refit_all - df.featfb_all,
        "refit_all_vs_fixed_class": df.refit_all - df.fixed_class,
        "refit_all_vs_best_single_core": df.refit_all - np.maximum(df.refit_novc, df.static_vc),
    }
    out = {"totals": tot, "contrasts": {k: boot(v.to_numpy(float)) for k, v in con.items()}, "seconds": round(time.time() - t0, 1)}
    for k, v in out["contrasts"].items():
        print(k, v)
    (HERE / "f2_campaigns.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
