"""Feasibility F11 (exploratory; exposed block-N compounds): the assembled MAESTRO agent on development
campaigns, including its stopping rule and its refusals.

Arms (same pools, budget 10%, batch 5, 5 seeds):
* ``pooled_nostop``: the pooled stack with feedback, no explore stream, no stopping (the F2/F3 arm,
  at batch 5);
* ``maestro_nostop``: `agent.Maestro` with the explore stream, stopping disabled;
* ``maestro``: the full agent, stopping enabled;
* ``maestro_perm``: the full agent with permuted feedback;
* ``agent_novc``: the same agent without virtual-cell sources (the H1 comparator);
* ``vc_only``: one batch, virtual cell only (the H2 comparator).

Reports hits, unexpected hits, verified hits, screens spent and rounds used, so the stopping rule's
cost saving is visible, plus every refusal code raised.
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import maestro_agent as AG  # noqa: E402
import campaign as CA  # noqa: E402
import stats as ST  # noqa: E402
import world as WM  # noqa: E402
from f6_llm_prior import load  # noqa: E402

SEEDS = range(5)
POOL_SHARE = 0.6
BUDGET_FRAC = 0.10
BATCH = 5


def main():
    t0 = time.time()
    U = WM.build(include_new=False)
    H = U.hits()
    prior = load("prior", U.brd, U.lineages)
    p2 = np.where(U.has_p2)[0]
    rows, refusals = [], Counter()
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
            row = {"seed": seed, "T": T, "pool_hits": int(H[pool, t].sum()), "pool_unexpected": int(unexp[pool].sum()),
                   "budget": budget}
            specs = {
                "pooled_nostop": dict(explore_seats=0, stop=False),
                "maestro_nostop": dict(explore_seats=2, stop=False),
                "maestro": dict(explore_seats=2, stop=True),
                "maestro_perm": dict(explore_seats=2, stop=True, perm=True),
                "agent_novc": dict(explore_seats=2, stop=True, sources=("klass", "target", "chem", "llm")),
            }
            for arm, sp in specs.items():
                st = CA.State.start(U, t, ref, pool, budget, BATCH)
                ag = AG.Maestro(U, prior=prior, explore_seats=sp["explore_seats"], stop=sp["stop"],
                                sources=sp.get("sources"))
                st, info = ag.run(st, np.random.default_rng(seed * 100 + t),
                                  permute_rng=np.random.default_rng(5000 + seed * 100 + t) if sp.get("perm") else None)
                sel = np.array([c for _, c in st.screened], int)
                v = AG.verify(U, st)
                row[f"{arm}|hits"] = int(H[sel, t].sum())
                row[f"{arm}|unexpected"] = int(unexp[sel].sum())
                row[f"{arm}|verified"] = v["verified"]
                row[f"{arm}|screens"] = len(sel)
                row[f"{arm}|rounds"] = st.round
                for r in st.refusals:
                    refusals[f"{arm}:{r['code']}"] += 1
            st = CA.State.start(U, t, ref, pool, budget, budget)
            vcs = WM.Stack(U, WM.VC_SOURCES).fit(ref)
            cand = np.array(st.left)
            p = vcs.score(ref, cand)[:, t]
            pick = cand[np.argsort(-p)[:budget]]
            st.reveal(U, pick)
            row["vc_only|hits"] = int(H[pick, t].sum())
            row["vc_only|unexpected"] = int(unexp[pick].sum())
            row["vc_only|verified"] = AG.verify(U, st)["verified"]
            row["vc_only|screens"] = len(pick)
            row["vc_only|rounds"] = 1
            rows.append(row)
            print({k: v for k, v in row.items() if "|hits" in k or k in ("seed", "T")}, round(time.time() - t0, 1), flush=True)
        U.sims["vc_cross"] = saved
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "f11_rows.csv", index=False)
    arms = ["pooled_nostop", "maestro_nostop", "maestro", "maestro_perm", "agent_novc", "vc_only"]
    totals = {f"{a}|{m}": int(df[f"{a}|{m}"].sum()) for a in arms for m in ("hits", "unexpected", "verified", "screens", "rounds")}
    totals["pool_hits"] = int(df.pool_hits.sum())
    totals["pool_unexpected"] = int(df.pool_unexpected.sum())
    g = df["T"].to_numpy()
    con = {}
    for name, (a, b, m) in {"H1_vc_contribution": ("maestro", "agent_novc", "unexpected"),
                            "H2_agent_contribution": ("maestro", "vc_only", "hits"),
                            "H5_feedback_real_vs_perm": ("maestro", "maestro_perm", "hits"),
                            "explore_stream": ("maestro_nostop", "pooled_nostop", "unexpected"),
                            "explore_stream_hits": ("maestro_nostop", "pooled_nostop", "hits"),
                            "stopping_cost": ("maestro", "maestro_nostop", "screens"),
                            "stopping_hits": ("maestro", "maestro_nostop", "hits")}.items():
        con[name] = ST.cluster_bootstrap((df[f"{a}|{m}"] - df[f"{b}|{m}"]).to_numpy(float), g)
    out = {"totals": totals, "contrasts": {k: [round(v["estimate"], 1), round(v["lower"], 1), round(v["upper"], 1)]
                                            for k, v in con.items()},
           "refusals": dict(refusals), "seconds": round(time.time() - t0, 1)}
    print(json.dumps(out, indent=1))
    (HERE / "f11_agent.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
