"""Conventional comparators (no gates, no program library, no decision-value preposterior):

  gbm_*       nonlinear/contextual interaction model: gradient-boosted regression on pair class, monotherapy features and the
              observed within-campaign class summaries (missing summaries stay NaN), meta-trained on released backgrounds with simulated probe sets;
              acquisition by ensemble variance or UCB (conventional active learning).
  latent_*    latent-factor / functional-fingerprint model (continuous program only) with conventional A-optimal / variance acquisition.
  broadcap    fixed broad-capacity comparator: a mixture of latent ranks 1,2,3,4,6 plus the unexplained component, BALD-like acquisition.
  direct      exploit: measure the highest-prior pairs (end-to-end contract only).
  prior       no probes.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

import iv_core as C
from svc_world import realized_utility

N_ENS = 3
SIM_SIZES = (0, 1, 2, 3, 4, 6)


def features(static, camp_aref, camp_amin, camp_amax, base_z1, probed: list, resid: list, n_cls: int):
    n = static.n
    cls = static.pair_class
    cm = np.full(n_cls, np.nan)
    cnt = np.zeros(n_cls)
    for p, r in zip(probed, resid):
        c = cls[p]
        cm[c] = r if np.isnan(cm[c]) else (cm[c] * cnt[c] + r) / (cnt[c] + 1)
        cnt[c] += 1
    X = np.empty((n, 6 + n_cls))
    X[:, 0] = cls
    X[:, 1] = camp_aref
    X[:, 2] = camp_amin
    X[:, 3] = camp_amax
    X[:, 4] = base_z1
    X[:, 5] = cnt[cls]
    X[:, 6:] = cm[None, :]
    return X


class GBM:
    def __init__(self, models, n_cls):
        self.models, self.n_cls = models, n_cls

    def predict(self, X):
        P = np.stack([m.predict(X) for m in self.models])
        return P.mean(0), P.std(0)


def train_gbm(world, static, M: C.Models, cells, mask, seed: int, max_iter: int = 80):
    """Meta-train on released backgrounds: for each cell simulate probe sets (restricted to the legal probe set) and regress the held-out residual."""
    rng = np.random.default_rng(seed)
    hist = world.history(list(cells))
    n_cls = M.n_cls
    legal = np.nonzero(np.ones(static.n, bool) if mask is None else mask)[0]
    z1 = np.stack([M.prior.z1(hist.Aref[:, k], hist.amin[:, k], hist.amax[:, k]) for k in range(len(cells))], 1)
    rows_X, rows_y, rows_cell = [], [], []
    for k in range(len(cells)):
        for _ in range(3):
            for m in SIM_SIZES:
                pr = list(rng.choice(legal, size=m, replace=False)) if m else []
                resid = [M.E[p, k] for p in pr]
                X = features(static, hist.Aref[:, k], hist.amin[:, k], hist.amax[:, k], z1[:, k], pr, resid, n_cls)
                keep = np.ones(static.n, bool)
                keep[pr] = False
                rows_X.append(X[keep])
                rows_y.append(M.E[keep, k])
                rows_cell.append(np.full(keep.sum(), k))
    X, y, cell_id = np.vstack(rows_X), np.concatenate(rows_y), np.concatenate(rows_cell)
    models = []
    for b in range(N_ENS):
        bag = rng.choice(len(cells), size=len(cells), replace=True)
        w = np.bincount(bag, minlength=len(cells))[cell_id].astype(float)
        m = HistGradientBoostingRegressor(max_iter=max_iter, max_depth=4, learning_rate=0.1, categorical_features=[0], random_state=seed + b)
        m.fit(X, y, sample_weight=w + 1e-6)
        models.append(m)
    return GBM(models, n_cls)


def gbm_campaign(world, static, cell, M, gbm: GBM, policy: str, B: int, contract: str, mask, seed: int):
    camp = world.campaign(cell, B, probe_mask=mask)
    z1 = M.prior.z1(camp.Aref, camp.amin, camp.amax)
    base = camp.Aref + z1
    pool = np.ones(static.n, bool) if mask is None else ~mask
    legal = np.ones(static.n, bool) if mask is None else mask.copy()
    rng = np.random.default_rng(seed)
    probed, resid, recorded, trace = [], [], {}, []
    for _ in range(B):
        X = features(static, camp.Aref, camp.amin, camp.amax, z1, probed, resid, gbm.n_cls)
        mean, sd = gbm.predict(X)
        score = base + mean
        for p, v in recorded.items():
            score[p] = v
        avail = legal.copy()
        avail[probed] = False
        idx = np.nonzero(avail)[0]
        if len(idx) == 0:
            break
        if policy == "gbm_exploit":
            p = int(idx[np.lexsort((idx, -score[idx]))][0])
        elif policy == "gbm_var":
            p = int(idx[np.lexsort((idx, -sd[idx]))][0])
        elif policy == "gbm_ucb":
            p = int(idx[np.lexsort((idx, -(score[idx] + sd[idx])))][0])
        else:
            raise ValueError(policy)
        val = camp.query([p], "probe" if contract != "E" else "act")[p]
        probed.append(p)
        resid.append(val - base[p])
        if pool[p]:
            recorded[p] = val
        trace.append({"probe": p, "policy": policy})
    X = features(static, camp.Aref, camp.amin, camp.amax, z1, probed, resid, gbm.n_cls)
    mean, _ = gbm.predict(X)
    score = np.where(pool, base + mean, -np.inf)
    for p, v in recorded.items():
        score[p] = v
    nom = [int(q) for q in C.top_k(score)]
    return realized_utility(world, camp, nom, pool), camp, nom, trace
