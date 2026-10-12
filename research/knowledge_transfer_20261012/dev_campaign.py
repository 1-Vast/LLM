"""Development step 5: deterministic campaign arms on the phase-1 tier.

Per fold f: the 1,000-compound reference atlas of ``dev_routes2``; a Pooler fitted on the other
folds' route table; the library is fold f's compounds measured in at least six lines, split by hash
into sub-libraries of about 61 compounds (the planned confirmation size). Budgets are 0.5, 1 and 2
wells per library compound.
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

import campaign as C
import engine
import rkt
from dev_common import CACHE, N_FOLDS, fold_of, load_phase1, phase1_knowledge, vehicle_thresholds
from dev_routes2 import N_REF, h
from pool import SPECIFIC_ROUTES, fit_nested

SUBLIB = 61
BUDGETS = (0.5, 1.0, 2.0)


def fold_pooler(z2, f):
    tr = z2["fold"] != f
    G = z2["G_table"][z2["fold"][tr], z2["line"][tr]].astype(np.float64)
    av = {r: z2[f"av_{r}"][tr] for r in SPECIFIC_ROUTES}
    preds = {r: z2[f"pred_{r}"][tr].astype(np.float64) for r in SPECIFIC_ROUTES}
    gamma = float(np.mean(z2["gammas"][np.arange(N_FOLDS) != f]))
    return fit_nested(z2["F"][tr].astype(np.float64), av, preds, G, z2["truth"][tr].astype(np.float64),
                      z2["active"][tr], z2["fold"][tr], gamma)


def setup(f, data=None):
    """Fold f's reference atlas, maps, generic directions, transfer table, pooler and library."""
    z = load_phase1()
    records, fps, know, vocab, targets = phase1_knowledge()
    Y = z["cp"].astype(np.float32)
    keys = list(z["compound"])
    folds = np.array([fold_of(k) for k in keys])
    thr = vehicle_thresholds(z)
    nlines = np.isfinite(Y[..., 0]).sum(1)
    z2 = data if data is not None else dict(np.load(CACHE / "dev2_routes.npz"))
    pool = sorted(np.flatnonzero((folds != f) & (nlines >= 6)), key=lambda i: h(f"ref{f}:{keys[i]}"))
    ref = np.zeros(len(keys), bool); ref[pool[:N_REF]] = True
    atlas = rkt.build_atlas(Y, ref, fps, know, targets, z["kd"], list(z["kd_gene"]))
    maps = rkt.context_maps(atlas)
    G = engine.generic_direction(atlas, thr)
    gamma = engine.gamma_estimate(atlas, thr, G)
    kappa = C.transfer_specific(atlas, maps, G, thr)
    pooler = fold_pooler(z2, f)
    lib_all = sorted(np.flatnonzero((folds == f) & (nlines >= 6)), key=lambda i: h(f"lib{f}:{keys[i]}"))
    n_sub = max(1, len(lib_all) // SUBLIB)
    raw = np.linalg.norm(np.nan_to_num(Y[ref]), axis=2)
    have = np.isfinite(Y[ref][..., 0])
    ref_rate = ((raw > thr[None]) & have).sum(0) / np.maximum(have.sum(0), 1)
    common = {"lines": [str(x) for x in z["line"]], "genes": [str(x) for x in z["gene_symbol"]], "ref_rate": ref_rate}

    def campaign(s):
        lib = np.array(lib_all[s::n_sub])
        meta = dict(common, names=[records[i].name for i in lib], moa=[sorted(records[i].hub_moa) for i in lib],
                    targets=[sorted(records[i].hub_targets) or sorted(records[i].mapkg)[:6] for i in lib])
        return C.Campaign(f"dev{f}.{s}", atlas, maps, pooler, G, gamma, thr, lib, np.isfinite(Y[lib, :, 0]), kappa), meta

    return campaign, n_sub, gamma


def main(arms=C.DETERMINISTIC_ARMS, folds_run=range(N_FOLDS), max_campaigns=None, out="dev_campaign.json"):
    t0 = time.time()
    z2 = dict(np.load(CACHE / "dev2_routes.npz"))
    rows = []
    for f in folds_run:
        campaign, n_sub, gamma = setup(f, z2)
        print(f"fold {f}: {n_sub} campaigns; gamma {gamma:.3f}; setup {time.time()-t0:.0f}s", flush=True)
        for s in range(n_sub if max_campaigns is None else min(n_sub, max_campaigns)):
            camp, _ = campaign(s)
            for b in BUDGETS:
                W = int(round(b * len(camp.library)))
                for arm in arms:
                    r = C.run_arm(camp, arm, W)
                    r.update({"campaign": camp.cid, "fold": f, "budget": b, "n_lib": len(camp.library), "n_cells": int(camp.grid.sum())})
                    rows.append(r)
            print(f"  campaign {camp.cid} done {time.time()-t0:.0f}s", flush=True)
    (CACHE / out).write_text(json.dumps(rows, indent=0), encoding="utf-8")
    summarise(rows)


def summarise(rows):
    import pandas as pd
    df = pd.DataFrame(rows)
    piv = df.pivot_table(index="arm", columns="budget", values="utility", aggfunc="mean").round(4)
    print(piv.to_string())
    print(df.pivot_table(index="arm", columns="budget", values="usable", aggfunc="mean").round(4).to_string())
    base = df[df.arm == "sparse_hub"].set_index(["campaign", "budget"]).utility
    for arm in df.arm.unique():
        d = df[df.arm == arm].set_index(["campaign", "budget"]).utility - base
        print(arm, {b: (round(float(d.xs(b, level=1).mean()), 4), int((d.xs(b, level=1) > 0).sum()), int((d.xs(b, level=1) < 0).sum())) for b in BUDGETS})


if __name__ == "__main__":
    if "--quick" in sys.argv:
        sys.exit(main(folds_run=[0], max_campaigns=1, out="dev_campaign_quick.json"))
    sys.exit(main())
