"""Feasibility F12 (exploratory; exposed block-N compounds): choose the registered budget by power.

F9 chose 3 libraries of 325 compounds (31 campaigns with reachable hits) but, at a 10% budget, the
primary contrast on unexpected hits is +7 [+1, +14] at a nominal 95% level, which a family-wise
widening would erase. F12 sweeps the budget fraction and reports each primary contrast at the
nominal level **and** at the family-wise level for a two-contrast family (the level the protocol
will actually use), so the budget is fixed before any sealed outcome is read.

Arms: `maestro` (full agent, stopping on), `agent_novc` (H1 comparator), `vc_only` (H2 comparator).
Cost is reported in screens and rounds so a larger budget is not chosen for free.
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
import maestro_agent as AG  # noqa: E402
import campaign as CA  # noqa: E402
import stats as ST  # noqa: E402
import world as WM  # noqa: E402
from f6_llm_prior import load  # noqa: E402

POOL = 325
N_LIB = 3
FRACS = (0.10, 0.20, 0.30)
BATCH = 5


def main():
    t0 = time.time()
    U = WM.build(include_new=False)
    H = U.hits()
    prior = load("prior", U.brd, U.lineages)
    p2 = np.where(U.has_p2)[0]
    rows = []
    for lib in range(N_LIB):
        rng0 = np.random.default_rng(777 + 31 * lib + POOL)
        pool = np.sort(rng0.choice(p2, size=POOL, replace=False))
        ref = np.setdiff1d(np.arange(len(U.brd)), pool)
        saved = U.sims["vc_cross"]
        U.sims["vc_cross"] = saved.copy()
        U.sims["vc_cross"][:, pool] = np.nan
        for t, T in enumerate(U.lineages):
            if H[pool, t].sum() == 0:
                continue
            kn = set(U.moa[ref][H[ref, t]])
            unexp = H[:, t] & ~np.isin(U.moa, list(kn))
            for frac in FRACS:
                budget = int(round(frac * POOL))
                row = {"lib": lib, "T": T, "frac": frac, "budget": budget,
                       "pool_hits": int(H[pool, t].sum()), "pool_unexpected": int(unexp[pool].sum())}
                for arm, src in (("maestro", None), ("agent_novc", ("klass", "target", "chem", "llm"))):
                    st = CA.State.start(U, t, ref, pool, budget, BATCH)
                    ag = AG.Maestro(U, prior=prior, explore_seats=2, stop=True, sources=src)
                    st, _ = ag.run(st, np.random.default_rng(lib * 100 + t))
                    sel = np.array([c for _, c in st.screened], int)
                    row[f"{arm}|hits"] = int(H[sel, t].sum())
                    row[f"{arm}|unexpected"] = int(unexp[sel].sum())
                    row[f"{arm}|screens"] = len(sel)
                    row[f"{arm}|rounds"] = st.round
                st = CA.State.start(U, t, ref, pool, budget, budget)
                p = WM.Stack(U, WM.VC_SOURCES).fit(ref).score(ref, np.array(st.left))[:, t]
                pick = np.array(st.left)[np.argsort(-p)[:budget]]
                row["vc_only|hits"] = int(H[pick, t].sum())
                row["vc_only|unexpected"] = int(unexp[pick].sum())
                row["vc_only|screens"] = len(pick)
                row["vc_only|rounds"] = 1
                rows.append(row)
            print(lib, T, round(time.time() - t0, 1), flush=True)
        U.sims["vc_cross"] = saved
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "f12_rows.csv", index=False)
    out = {}
    for frac in FRACS:
        sub = df[df.frac == frac]
        g = sub["T"].to_numpy()
        prim = {"H1_vc_unexpected": (sub["maestro|unexpected"] - sub["agent_novc|unexpected"]).to_numpy(float),
                "H2_agent_hits": (sub["maestro|hits"] - sub["vc_only|hits"]).to_numpy(float)}
        fam = ST.family({k: (v, g) for k, v in prim.items()}, alpha=0.05)
        nom = {k: ST.cluster_bootstrap(v, g, alpha=0.05) for k, v in prim.items()}
        out[str(frac)] = {
            "n_campaigns": int(len(sub)), "screens_total": int(sub["maestro|screens"].sum()),
            "rounds_mean": round(float(sub["maestro|rounds"].mean()), 2),
            "totals": {a: {m: int(sub[f"{a}|{m}"].sum()) for m in ("hits", "unexpected")}
                       for a in ("maestro", "agent_novc", "vc_only")},
            "reachable": {"hits": int(sub.pool_hits.sum()), "unexpected": int(sub.pool_unexpected.sum())},
            "nominal95": {k: [round(v["estimate"], 1), round(v["lower"], 1), round(v["upper"], 1)] for k, v in nom.items()},
            "familywise": {k: [round(v["estimate"], 1), round(v["lower"], 1), round(v["upper"], 1), v["verdict"]]
                           for k, v in fam.items()}}
        print(frac, json.dumps(out[str(frac)]["familywise"]), flush=True)
    (HERE / "f12_budget_power.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
