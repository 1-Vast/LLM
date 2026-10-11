"""Feasibility F9 (power rehearsal at the planned confirmation geometry; exposed compounds only).

The confirmation tier holds 975 new compounds. The plan is L disjoint libraries, one campaign per
(library, lineage), budget 10% of the library, batch 5, with lineage-cluster bootstrap over the 14
lineages. F9 rehearses that geometry on development compounds (pool sampled from the 542 with
GSE70138 signatures, reference = the other block-N compounds) for pool sizes 195 (L=5) and 325
(L=3), and reports the primary contrasts so the registered geometry is chosen before any sealed
outcome is read.

Arms rehearsed are the deterministic ones only (no model calls): MAESTRO-like (all sources, refit),
AGENT-noVC (klass/target/chem, refit), VC-only (static), FIXED (class mean).
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

GEOM = {195: 5, 325: 3}
BUDGET_FRAC = 0.10
BATCH = 5
ARMS = {"maestro": (WM.SOURCES + ("llm",), "refit"), "agent_novc": (("klass", "target", "chem", "llm"), "refit"),
        "vc_only": (WM.VC_SOURCES, "static"), "fixed": (("klass",), "static")}


def run(U, ref, pool, t, budget, rng, sources, mode, prior):
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
    s2, _ = U.selectivity(U.S2)
    rep = np.where(np.isfinite(s2), s2 <= -0.25, False)
    p2 = np.where(U.has_p2)[0]
    rows = []
    for size, L in GEOM.items():
        for lib in range(L):
            rng0 = np.random.default_rng(777 + 31 * lib + size)
            pool = np.sort(rng0.choice(p2, size=size, replace=False))
            ref = np.setdiff1d(np.arange(len(U.brd)), pool)
            saved = U.sims["vc_cross"]
            U.sims["vc_cross"] = saved.copy()
            U.sims["vc_cross"][:, pool] = np.nan
            budget = int(round(BUDGET_FRAC * size))
            for t, T in enumerate(U.lineages):
                if H[pool, t].sum() == 0:
                    continue
                kn = set(U.moa[ref][H[ref, t]])
                unexp = H[:, t] & ~np.isin(U.moa, list(kn))
                row = {"size": size, "lib": lib, "T": T, "budget": budget, "pool_hits": int(H[pool, t].sum()),
                       "pool_unexpected": int(unexp[pool].sum())}
                for arm, (src, mode) in ARMS.items():
                    ch = np.array(run(U, ref, pool, t, budget, np.random.default_rng(lib * 100 + t), src, mode, prior), int)
                    row[f"{arm}|hits"] = int(H[ch, t].sum())
                    row[f"{arm}|unexpected"] = int(unexp[ch].sum())
                    row[f"{arm}|replicated"] = int((rep[ch, t] & H[ch, t]).sum())
                rows.append(row)
            U.sims["vc_cross"] = saved
            print(size, lib, round(time.time() - t0, 1), flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "f9_rows.csv", index=False)

    def boot(d, g, B=4000):
        u = np.unique(g); r = np.random.default_rng(7)
        est = [sum(d[g == x].sum() for x in r.choice(u, len(u))) for _ in range(B)]
        return [float(d.sum()), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))]
    out = {}
    for size in GEOM:
        sub = df[df["size"] == size]
        g = sub["T"].to_numpy()
        out[str(size)] = {"n_campaigns": int(len(sub)), "pool_hits": int(sub.pool_hits.sum()),
                          "pool_unexpected": int(sub.pool_unexpected.sum()),
                          "totals": {c: int(sub[c].sum()) for c in sub.columns if "|" in c}}
        for m in ("hits", "unexpected", "replicated"):
            for name, (a, b) in {"vc_contribution": ("maestro", "agent_novc"), "agent_contribution": ("maestro", "vc_only"),
                                 "vs_fixed": ("maestro", "fixed")}.items():
                out[str(size)][f"{name}|{m}"] = boot((sub[f"{a}|{m}"] - sub[f"{b}|{m}"]).to_numpy(float), g)
    print(json.dumps(out, indent=1))
    (HERE / "f9_power.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
