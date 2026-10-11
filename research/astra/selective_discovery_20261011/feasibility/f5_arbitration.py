"""Feasibility F5 (exploratory; exposed block-N compounds): per-lineage arbitration among world models.

F2 post hoc: refit_vc beats refit_novc for skin, gastric and uterus, and loses for esophagus and upper
aerodigestive. The pooled stack (refit_all) does not capture this. Picking the better model per
lineage in hindsight would give about 139 against 129 (oracle 158). F4 rejected a panel-composition
explanation, so the arbitration must be learned.

Arms (same pools, budget 10%, batch 6, seeds 0-2 as F2):
* ``refit_all``: F2's pooled stack (baseline);
* ``refit_int``: stack with lineage-specific source-selectivity weights (L2-shrunk);
* ``arb_ref``: for lineage T, model weights w_m proportional to exp(out-of-fold log-likelihood on
  reference compounds with GSE70138 signatures, lineage T), over m in {vc, novc, all}; fixed;
* ``arb_bma``: arb_ref plus each model's prequential log-likelihood on this campaign's screened
  compounds (predictions made before reveal), updated every round.
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
MODELS = {"vc": WM.VC_SOURCES, "novc": ("klass", "target", "chem"), "all": WM.SOURCES}


def ll(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return float(np.sum(np.where(y, np.log(p), np.log(1 - p))))


def run_refit(U, H, ref, pool, t, budget, rng, interact=False):
    known, left, chosen = list(ref), list(pool), []
    while len(chosen) < budget:
        st = WM.Stack(U, WM.SOURCES, interact=interact).fit(np.array(known))
        cand = np.array(left)
        p = st.score(np.array(known), cand)[:, t] + 1e-12 * rng.standard_normal(len(cand))
        for c in cand[np.argsort(-p)[: min(BATCH, budget - len(chosen))]]:
            chosen.append(int(c)); left.remove(int(c)); known.append(int(c))
    return chosen


def run_arb(U, H, ref, pool, t, budget, rng, prior_ll, update):
    known, left, chosen = list(ref), list(pool), []
    camp = {m: 0.0 for m in MODELS}
    trace = []
    while len(chosen) < budget:
        cand = np.array(left)
        ps = {}
        for m, src in MODELS.items():
            st = WM.Stack(U, src).fit(np.array(known))
            ps[m] = st.score(np.array(known), cand)[:, t]
        logw = np.array([prior_ll[m] + (camp[m] if update else 0.0) for m in MODELS])
        w = np.exp(logw - logw.max()); w /= w.sum()
        p = sum(wi * ps[m] for wi, m in zip(w, MODELS)) + 1e-12 * rng.standard_normal(len(cand))
        take = cand[np.argsort(-p)[: min(BATCH, budget - len(chosen))]]
        pos = {c: i for i, c in enumerate(cand)}
        for m in MODELS:   # prequential: this round's pre-reveal predictions for the screened compounds
            camp[m] += ll(np.array([ps[m][pos[c]] for c in take]), H[take, t])
        trace.append(dict(zip(MODELS, np.round(w, 3).tolist())))
        for c in take:
            chosen.append(int(c)); left.remove(int(c)); known.append(int(c))
    return chosen, trace


def main():
    t0 = time.time()
    U = WM.build(include_new=False)
    H = U.hits()
    p2 = np.where(U.has_p2)[0]
    rows, traces = [], {}
    for seed in SEEDS:
        rng0 = np.random.default_rng(20261011 + seed)
        pool = np.sort(rng0.choice(p2, size=int(POOL_SHARE * len(p2)), replace=False))
        ref = np.setdiff1d(np.arange(len(U.brd)), pool)
        saved = U.sims["vc_cross"]
        U.sims["vc_cross"] = saved.copy()
        U.sims["vc_cross"][:, pool] = np.nan
        ref_p2 = np.where(np.isin(ref, p2))[0]                   # positions in ref of P2 reference compounds
        oof = {m: WM.Stack(U, src).oof(ref, ref_p2, seed=seed) for m, src in MODELS.items()}
        budget = int(round(BUDGET_FRAC * len(pool)))
        for t, T in enumerate(U.lineages):
            if H[pool, t].sum() == 0:
                continue
            y_ref = H[ref[ref_p2], t]
            prior_ll = {m: ll(oof[m][:, t], y_ref) for m in MODELS}
            row = {"seed": seed, "T": T, "pool_hits": int(H[pool, t].sum()), "budget": budget,
                   **{f"refLL_{m}": round(v, 2) for m, v in prior_ll.items()}}
            rng = lambda: np.random.default_rng(seed * 100 + t)  # noqa: E731
            row["refit_all"] = int(H[run_refit(U, H, ref, pool, t, budget, rng()), t].sum())
            row["refit_int"] = int(H[run_refit(U, H, ref, pool, t, budget, rng(), interact=True), t].sum())
            ch, _ = run_arb(U, H, ref, pool, t, budget, rng(), prior_ll, update=False)
            row["arb_ref"] = int(H[ch, t].sum())
            ch, tr = run_arb(U, H, ref, pool, t, budget, rng(), prior_ll, update=True)
            row["arb_bma"] = int(H[ch, t].sum())
            traces[f"{seed}:{T}"] = tr
            rows.append(row)
            print(row, round(time.time() - t0, 1), flush=True)
        U.sims["vc_cross"] = saved
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "f5_rows.csv", index=False)
    f2 = pd.read_csv(HERE / "f2_rows.csv")
    df = df.merge(f2[["seed", "T", "refit_vc", "refit_novc", "oracle", "fixed_class"]], on=["seed", "T"])
    tot = {k: int(df[k].sum()) for k in ("pool_hits", "fixed_class", "refit_vc", "refit_novc", "refit_all", "refit_int",
                                         "arb_ref", "arb_bma", "oracle")}
    tot["hindsight_best_of_vc_novc_all"] = int(np.maximum.reduce([df.refit_vc, df.refit_novc, df.refit_all]).sum())

    def boot(d, B=4000):
        g = df["T"].to_numpy(); u = np.unique(g); r = np.random.default_rng(7)
        est = [sum(d[g == x].sum() for x in r.choice(u, len(u))) for _ in range(B)]
        return [float(d.sum()), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))]
    con = {k: boot((df[a] - df[b]).to_numpy(float)) for k, (a, b) in
           {"arb_bma-refit_all": ("arb_bma", "refit_all"), "arb_ref-refit_all": ("arb_ref", "refit_all"),
            "refit_int-refit_all": ("refit_int", "refit_all"), "arb_bma-arb_ref": ("arb_bma", "arb_ref")}.items()}
    out = {"totals": tot, "contrasts": con, "seconds": round(time.time() - t0, 1)}
    print(json.dumps(out, indent=1))
    (HERE / "f5_arbitration.json").write_text(json.dumps({**out, "weight_traces": traces}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
