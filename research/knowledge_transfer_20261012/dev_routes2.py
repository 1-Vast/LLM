"""Development step 3: route table under confirmation-like conditions (phase-1 tier).

Per fold, the reference atlas is 1,000 compounds drawn (by hash) from the other folds among those
measured in at least six lines, mirroring the 979-compound phase-2 reference tier. Queries are the
fold's compounds, in three visibility regimes:
* A: all other measured lines visible; A1: exactly one (chosen by hash); B: none.
Writes ``cache/dev2_routes.npz`` with route predictions, support, features and truth.
"""
from __future__ import annotations

import hashlib
import json
import time

import numpy as np

import engine
import rkt
from dev_common import CACHE, N_FOLDS, fold_of, load_phase1, phase1_knowledge, vehicle_thresholds

N_REF = 1000


def h(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)


def main():
    t0 = time.time()
    z = load_phase1()
    records, fps, know, vocab, targets = phase1_knowledge()
    Y = z["cp"].astype(np.float32)
    keys = list(z["compound"])
    folds = np.array([fold_of(k) for k in keys])
    thr = vehicle_thresholds(z)
    L = Y.shape[1]
    nlines = np.isfinite(Y[..., 0]).sum(1)
    cols = {k: [] for k in ("fold", "comp", "line", "regime", "active", "F", "truth")}
    G_table = np.zeros((N_FOLDS, L, Y.shape[2]), np.float32); gammas = np.zeros(N_FOLDS)
    for r in rkt.ROUTES[:4]:
        for k in ("pred", "av"):
            cols[f"{k}_{r}"] = []
    for f in range(N_FOLDS):
        pool = [i for i in np.flatnonzero((folds != f) & (nlines >= 6))]
        pool.sort(key=lambda i: h(f"ref{f}:{keys[i]}"))
        ref = np.zeros(len(keys), bool); ref[pool[:N_REF]] = True
        atlas = rkt.build_atlas(Y, ref, fps, know, targets, z["kd"], list(z["kd_gene"]))
        maps = rkt.context_maps(atlas)
        G = engine.generic_direction(atlas, thr)
        gamma = engine.gamma_estimate(atlas, thr, G)
        G_table[f] = G; gammas[f] = gamma
        print(f"fold {f}: maps {len(maps)} meanLOO {np.mean([m.loo_cosine for m in maps.values()]):.3f} gamma {gamma:.3f}", flush=True)
        cache: dict = {}
        for T in range(L):
            q = np.flatnonzero((folds == f) & np.isfinite(Y[:, T, 0]))
            truth = atlas.Yc[q, T].astype(np.float64)
            measured = np.isfinite(Y[q, :, 0])
            one = np.zeros((len(q), L), bool)
            for i, c in enumerate(q):
                others = [s for s in range(L) if s != T and measured[i, s]]
                if others:
                    one[i, others[h(f"vis:{keys[c]}:{T}") % len(others)]] = True
            for regime, vis in (("A", np.ones((len(q), L), bool)), ("A1", one), ("B", np.zeros((len(q), L), bool))):
                blk = engine.query_block(atlas, q, T, vis, maps, thr, cache)
                for r in rkt.ROUTES[:4]:
                    cols[f"pred_{r}"].append(blk.routes[r].pred.astype(np.float16))
                    cols[f"av_{r}"].append(blk.routes[r].available)
                cols["F"].append(blk.F.astype(np.float32))
                cols["truth"].append(truth.astype(np.float16))
                cols["fold"].append(np.full(len(q), f)); cols["comp"].append(q); cols["line"].append(np.full(len(q), T))
                cols["regime"].append(np.full(len(q), regime)); cols["active"].append(np.linalg.norm(Y[q, T], axis=1) > thr[T])
        print(f"  fold {f} done {time.time() - t0:.0f}s", flush=True)
    arrays = {k: np.concatenate(v) for k, v in cols.items()}
    np.savez_compressed(CACHE / "dev2_routes.npz", G_table=G_table, gammas=gammas, **arrays)
    print(json.dumps({"n": int(len(arrays["comp"])), "seconds": round(time.time() - t0, 1)}))


if __name__ == "__main__":
    main()
