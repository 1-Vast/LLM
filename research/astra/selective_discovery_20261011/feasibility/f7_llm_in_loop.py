"""Feasibility F7 (exploratory; exposed block-N compounds): does the gated LLM prior add inside the loop?

Same pools, budget (10%), batch (6) and seeds (0-2) as F2. Arms:
* ``refit_all_llm``: F2's refit_all plus the LLM prior as a stacked feature (weight learned);
* ``refit_novc_llm``: the agent without the virtual cell (annotation, targets, chemistry, LLM prior);
* ``static_all_llm``: one batch, no feedback.
Compared with F2's refit_all, refit_novc and static_all on identical campaigns.
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

SEEDS = (0, 1, 2)
POOL_SHARE = 0.6
BUDGET_FRAC = 0.10
BATCH = 6
ARMS = {"refit_all_llm": (WM.SOURCES + ("llm",), "refit"), "refit_novc_llm": (("klass", "target", "chem", "llm"), "refit"),
        "static_all_llm": (WM.SOURCES + ("llm",), "static")}


def run(U, H, ref, pool, t, budget, rng, sources, mode, prior):
    known, left, chosen = list(ref), list(pool), []
    st = WM.Stack(U, sources, prior=prior).fit(np.array(known))
    if mode == "static":
        cand = np.array(left)
        p = st.score(np.array(known), cand)[:, t] + 1e-12 * rng.standard_normal(len(cand))
        return list(cand[np.argsort(-p)[:budget]])
    while len(chosen) < budget:
        if chosen:
            st = WM.Stack(U, sources, prior=prior).fit(np.array(known))
        cand = np.array(left)
        p = st.score(np.array(known), cand)[:, t] + 1e-12 * rng.standard_normal(len(cand))
        for c in cand[np.argsort(-p)[: min(BATCH, budget - len(chosen))]]:
            chosen.append(int(c)); left.remove(int(c)); known.append(int(c))
    return chosen


def main():
    t0 = time.time()
    U = WM.build(include_new=False)
    H = U.hits()
    prior = load("prior", U.brd, U.lineages)
    p2 = np.where(U.has_p2)[0]
    rows = []
    for seed in SEEDS:
        rng0 = np.random.default_rng(20261011 + seed)
        pool = np.sort(rng0.choice(p2, size=int(POOL_SHARE * len(p2)), replace=False))
        ref = np.setdiff1d(np.arange(len(U.brd)), pool)
        saved = U.sims["vc_cross"]
        U.sims["vc_cross"] = saved.copy()
        U.sims["vc_cross"][:, pool] = np.nan
        budget = int(round(BUDGET_FRAC * len(pool)))
        coef = WM.Stack(U, WM.SOURCES + ("llm",), prior=prior).fit(ref).model.coef_[0][4 * len(WM.SOURCES): 4 * len(WM.SOURCES) + 2]
        print("seed", seed, "llm coef (logit, missing)", np.round(coef, 3), flush=True)
        for t, T in enumerate(U.lineages):
            if H[pool, t].sum() == 0:
                continue
            row = {"seed": seed, "T": T}
            for arm, (src, mode) in ARMS.items():
                ch = run(U, H, ref, pool, t, budget, np.random.default_rng(seed * 100 + t), src, mode, prior)
                row[arm] = int(H[ch, t].sum())
            rows.append(row)
            print(row, round(time.time() - t0, 1), flush=True)
        U.sims["vc_cross"] = saved
    df = pd.DataFrame(rows).merge(pd.read_csv(HERE / "f2_rows.csv"), on=["seed", "T"])
    df.to_csv(HERE / "f7_rows.csv", index=False)
    tot = {k: int(df[k].sum()) for k in ("pool_hits", "static_all", "static_all_llm", "refit_novc", "refit_novc_llm",
                                         "refit_all", "refit_all_llm", "oracle")}

    def boot(d, B=4000):
        g = df["T"].to_numpy(); u = np.unique(g); r = np.random.default_rng(7)
        est = [sum(d[g == x].sum() for x in r.choice(u, len(u))) for _ in range(B)]
        return [float(d.sum()), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))]
    con = {k: boot((df[a] - df[b]).to_numpy(float)) for k, (a, b) in
           {"llm_in_all": ("refit_all_llm", "refit_all"), "llm_in_novc": ("refit_novc_llm", "refit_novc"),
            "llm_static": ("static_all_llm", "static_all"), "vc_given_llm": ("refit_all_llm", "refit_novc_llm")}.items()}
    out = {"totals": tot, "contrasts": con, "seconds": round(time.time() - t0, 1)}
    print(json.dumps(out, indent=1))
    (HERE / "f7_llm_in_loop.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
