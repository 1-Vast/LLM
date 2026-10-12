"""Development step 1: out-of-fold route predictions on the phase-1 tier.

For each of five compound folds the remaining compounds are the reference atlas. Each query is a
fold compound measured in line T, scored in two regimes:
* A (``visible``): the compound's own responses in the other lines may be used;
* B (``hidden``): they may not, so only knowledge, chemistry and genetics can transfer.

Writes ``cache/dev_routes.npz`` (per query: route predictions' centred cosines, support features,
truth norms, activity) and prints a summary. Outcome scores here are development evidence only.
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

import rkt
from dev_common import CACHE, N_FOLDS, fold_of, load_phase1, phase1_knowledge, vehicle_thresholds


def main() -> None:
    t0 = time.time()
    z = load_phase1()
    records, fps, know, vocab, targets = phase1_knowledge()
    Y = z["cp"].astype(np.float32)
    KD = z["kd"].astype(np.float32)
    keys = list(z["compound"])
    folds = np.array([fold_of(k) for k in keys])
    thr = vehicle_thresholds(z)
    L = Y.shape[1]
    out = {name: [] for name in ("fold", "comp", "line", "regime", "active", "true_norm")}
    route_cos = {r: [] for r in rkt.ROUTES}
    route_av = {r: [] for r in rkt.ROUTES}
    route_sup = {r: [] for r in rkt.ROUTES}
    preds_store = {r: [] for r in rkt.ROUTES}
    truth_store = []
    for f in range(N_FOLDS):
        ref = folds != f
        atlas = rkt.build_atlas(Y, ref, fps, know, targets, KD, list(z["kd_gene"]))
        maps = rkt.context_maps(atlas)
        print(f"fold {f}: {len(maps)} maps, mean LOO {np.mean([m.loo_cosine for m in maps.values()]):.3f}", flush=True)
        for T in range(L):
            q = np.flatnonzero((folds == f) & np.isfinite(Y[:, T, 0]))
            truth = atlas.Yc[q, T].astype(np.float64)
            for regime, vis in (("A", np.ones((len(q), L), bool)), ("B", np.zeros((len(q), L), bool))):
                routes = rkt.all_routes(atlas, q, T, vis, maps)
                for r, o in routes.items():
                    route_cos[r].append(np.where(o.available, rkt.centred_cosine(o.pred, truth), np.nan))
                    route_av[r].append(o.available)
                    route_sup[r].append(o.support)
                    preds_store[r].append(o.pred.astype(np.float16))
                truth_store.append(truth.astype(np.float16))
                out["fold"].append(np.full(len(q), f)); out["comp"].append(q); out["line"].append(np.full(len(q), T))
                out["regime"].append(np.full(len(q), regime)); out["active"].append(np.linalg.norm(Y[q, T], axis=1) > thr[T])
                out["true_norm"].append(np.linalg.norm(truth, axis=1))
        print(f"  fold {f} done {time.time() - t0:.0f}s", flush=True)
    arrays = {k: np.concatenate(v) for k, v in out.items()}
    for r in rkt.ROUTES:
        arrays[f"cos_{r}"] = np.concatenate(route_cos[r]); arrays[f"av_{r}"] = np.concatenate(route_av[r])
        arrays[f"sup_{r}"] = np.concatenate(route_sup[r]); arrays[f"pred_{r}"] = np.concatenate(preds_store[r])
    arrays["truth"] = np.concatenate(truth_store)
    np.savez_compressed(CACHE / "dev_routes.npz", **arrays)
    # replicate ceiling: two disjoint halves of the same compound x line, centred by the full reference mean
    mu = np.nanmean(Y, axis=0)
    ha, hb = z["cp_half_a"] - mu[None], z["cp_half_b"] - mu[None]
    okr = np.isfinite(ha[..., 0]) & np.isfinite(hb[..., 0])
    act = np.linalg.norm(Y, axis=2) > thr[None]
    ceil_all = rkt.centred_cosine(ha[okr], hb[okr])
    ceil_act = rkt.centred_cosine(ha[okr & act], hb[okr & act])
    summary = {"ceiling_all": [float(np.mean(ceil_all)), int(okr.sum())], "ceiling_active": [float(np.mean(ceil_act)), int((okr & act).sum())]}
    for reg in ("A", "B"):
        m = arrays["regime"] == reg
        for r in rkt.ROUTES:
            av = arrays[f"av_{r}"] & m
            ma = av & arrays["active"]
            summary[f"{reg}:{r}"] = {"available": round(float(av.sum() / m.sum()), 3),
                                     "cos_all": round(float(np.nanmean(arrays[f"cos_{r}"][av])), 4),
                                     "cos_active": round(float(np.nanmean(arrays[f"cos_{r}"][ma])), 4),
                                     "n_active": int(ma.sum())}
    summary["fraction_active"] = float(arrays["active"][arrays["regime"] == "A"].mean())
    summary["seconds"] = round(time.time() - t0, 1)
    print(json.dumps(summary, indent=1))
    (CACHE / "dev_routes_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
