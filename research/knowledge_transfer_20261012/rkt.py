"""Routed knowledge transfer (RKT): research implementation of block Q's virtual-cell core.

A query is (compound d, line T). Each route turns one kind of transferable evidence into a centred
prediction of d's landmark response in T, and reports the support it had:

* R0 ``systematic``: the reference mean response in T (centred prediction 0).
* R1 ``context``: d measured in other lines s, mapped s -> T by ridge maps fitted on reference
  compounds measured in both lines (cross-system perturbation data, PRESAGE's strongest source).
* R2 ``pheno``: reference compounds whose responses in the other lines resemble d's (needs d
  measured somewhere; the block-N transfer, now predicting the transcriptional response in T).
* R2 ``chem``: structural analogues (Morgan Tanimoto) measured in T.
* R2 ``know``: knowledge analogues (shared targets, MAP-KG edges, mechanism) measured in T.
* R3 ``genetic``: signed knockdown consensus signatures of d's targets in T (knowledge of what the
  compound acts on, routed through measured genetic perturbation in the same cell line).

Centring: every response is centred by the reference mean of its line (``mu``), and knockdowns by
the knockdown mean of their line, so routes are scored on perturbation-specific signal only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ROUTES = ("context", "pheno", "chem", "know", "genetic")


def unit_rows(X: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(X, axis=-1, keepdims=True)
    return np.where(n > 0, X / np.maximum(n, 1e-12), 0.0)


def centred_cosine(pred: np.ndarray, true: np.ndarray) -> np.ndarray:
    """Row-wise cosine of centred vectors; 0 where the prediction is the systematic mean."""
    num = (pred * true).sum(-1)
    den = np.linalg.norm(pred, axis=-1) * np.linalg.norm(true, axis=-1)
    return np.where(den > 1e-9, num / np.maximum(den, 1e-12), 0.0)


@dataclass
class RidgeMap:
    B: np.ndarray            # p x p map on centred responses
    lam: float
    loo_cosine: float        # mean leave-one-out centred cosine on the fitting compounds
    n: int


def fit_ridge_map(X: np.ndarray, Z: np.ndarray, lams=(1e1, 1e2, 1e3, 1e4, 1e5)) -> RidgeMap:
    """Multi-output ridge Z ~ X B with lambda by leave-one-out mean centred cosine."""
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    UtZ = U.T @ Z
    best = None
    for lam in lams:
        d = S ** 2 / (S ** 2 + lam)
        H_diag = (U ** 2 * d).sum(1)
        Zhat = U @ (d[:, None] * UtZ)
        resid = (Z - Zhat) / np.maximum(1 - H_diag, 1e-6)[:, None]
        loo = Z - resid
        score = float(np.mean(centred_cosine(loo, Z)))
        if best is None or score > best[1]:
            best = (lam, score)
    lam, score = best
    B = Vt.T @ ((S / (S ** 2 + lam))[:, None] * UtZ)
    return RidgeMap(B=B.astype(np.float32), lam=lam, loo_cosine=score, n=len(X))


@dataclass
class Atlas:
    """Centred responses of reference compounds, with the knowledge needed by the routes."""
    Yc: np.ndarray           # n_comp x n_line x p, centred by the reference line means, NaN if missing
    mu: np.ndarray           # n_line x p reference means
    ref: np.ndarray          # boolean n_comp: may serve as a reference
    fps: np.ndarray          # n_comp x bits Morgan fingerprints
    know: np.ndarray         # n_comp x vocab boolean knowledge tokens (targets, MAP-KG edges, mechanism)
    targets: list            # per compound: dict symbol -> sign
    KDc: np.ndarray          # n_gene x n_line x p, centred by the knockdown line means, NaN if missing
    kd_index: dict           # symbol -> row in KDc


def build_atlas(Y: np.ndarray, ref: np.ndarray, fps, know, targets, KD, kd_genes) -> Atlas:
    mu = np.nanmean(np.where(ref[:, None, None], Y, np.nan), axis=0)
    Yc = Y - mu[None]
    kd_mu = np.nanmean(KD, axis=0)
    return Atlas(Yc=Yc.astype(np.float32), mu=mu.astype(np.float32), ref=ref, fps=fps, know=know,
                 targets=targets, KDc=(KD - kd_mu[None]).astype(np.float32),
                 kd_index={g: i for i, g in enumerate(kd_genes)})


def context_maps(atlas: Atlas, min_shared: int = 50) -> dict:
    """Ridge maps for every ordered line pair, fitted on references measured in both lines."""
    have = np.isfinite(atlas.Yc[..., 0]) & atlas.ref[:, None]
    L = atlas.Yc.shape[1]
    maps = {}
    for s in range(L):
        for t in range(L):
            if s == t:
                continue
            rows = have[:, s] & have[:, t]
            if rows.sum() < min_shared:
                continue
            maps[(s, t)] = fit_ridge_map(atlas.Yc[rows, s].astype(np.float64), atlas.Yc[rows, t].astype(np.float64))
    return maps


@dataclass
class RouteOutput:
    pred: np.ndarray          # n_query x p centred prediction (0 where unavailable)
    available: np.ndarray     # n_query boolean
    support: np.ndarray       # n_query x k support features (route-specific)
    support_names: tuple


def route_context(atlas: Atlas, q: np.ndarray, T: int, visible: np.ndarray, maps: dict) -> RouteOutput:
    """``visible``: n_query x n_line boolean, which of the query's own line profiles may be used."""
    n, p = len(q), atlas.Yc.shape[2]
    num = np.zeros((n, p)); wsum = np.zeros(n); nsrc = np.zeros(n); best = np.zeros(n)
    for s in range(atlas.Yc.shape[1]):
        if s == T or (s, T) not in maps:
            continue
        m = maps[(s, T)]
        ok = visible[:, s] & np.isfinite(atlas.Yc[q, s, 0])
        if not ok.any():
            continue
        pred = atlas.Yc[q[ok], s].astype(np.float64) @ m.B
        w = max(m.loo_cosine, 0.0) ** 2
        num[ok] += w * unit_rows(pred) * np.linalg.norm(pred, axis=1, keepdims=True)
        wsum[ok] += w
        nsrc[ok] += 1
        best[ok] = np.maximum(best[ok], m.loo_cosine)
    avail = wsum > 0
    pred = np.where(avail[:, None], num / np.maximum(wsum, 1e-12)[:, None], 0.0)
    src_norm = np.where(avail, np.linalg.norm(pred, axis=1), 0.0)
    return RouteOutput(pred, avail, np.stack([nsrc, best, src_norm], 1), ("n_sources", "best_map_loo", "pred_norm"))


def _knn(sim: np.ndarray, Yref: np.ndarray, k: int, gamma: float, floor: float):
    """Similarity-weighted mean of the k most similar references (sim: n_query x n_ref, NaN=unusable)."""
    s = np.where(np.isfinite(sim) & (sim > floor), sim, -np.inf)
    kk = min(k, s.shape[1])
    idx = np.argpartition(-s, kk - 1, axis=1)[:, :kk]
    top = np.take_along_axis(s, idx, 1)
    order = np.argsort(-top, axis=1)
    idx = np.take_along_axis(idx, order, 1); top = np.take_along_axis(top, order, 1)
    ok = np.isfinite(top)
    w = np.where(ok, np.clip(top, 0, None) ** gamma, 0.0)
    pred = np.einsum("qk,qkp->qp", w, Yref[idx]) / np.maximum(w.sum(1, keepdims=True), 1e-12)
    avail = ok.any(1)
    pred[~avail] = 0.0
    top1 = np.where(ok[:, 0], top[:, 0], 0.0)
    meank = np.where(ok, top, 0.0).sum(1) / np.maximum(ok.sum(1), 1)
    nn = ok.sum(1)
    # dispersion: 1 - mean pairwise agreement of the neighbours with their weighted mean
    agree = np.einsum("qkp,qp->qk", unit_rows(Yref[idx]), unit_rows(pred))
    disp = np.where(ok, agree, 0.0).sum(1) / np.maximum(nn, 1)
    return pred, avail, np.stack([top1, meank, nn, disp, np.linalg.norm(pred, axis=1)], 1), idx


def ref_rows(atlas: Atlas, T: int) -> np.ndarray:
    return np.flatnonzero(atlas.ref & np.isfinite(atlas.Yc[:, T, 0]))


def route_chem(atlas, q, T, *, k=10, gamma=2.0, floor=0.3):
    R = ref_rows(atlas, T)
    a = atlas.fps[q].astype(np.float32); b = atlas.fps[R].astype(np.float32)
    inter = a @ b.T
    union = a.sum(1)[:, None] + b.sum(1)[None] - inter
    sim = np.where(union > 0, inter / np.maximum(union, 1e-9), np.nan)
    sim[np.equal.outer(q, R)] = np.nan
    pred, avail, sup, _ = _knn(sim, atlas.Yc[R, T], k, gamma, floor)
    return RouteOutput(pred, avail, sup, ("top_sim", "mean_k_sim", "n_nn", "nn_agreement", "pred_norm"))


def route_know(atlas, q, T, *, k=10, gamma=1.0, floor=0.0):
    R = ref_rows(atlas, T)
    a = atlas.know[q].astype(np.float32); b = atlas.know[R].astype(np.float32)
    inter = a @ b.T
    union = a.sum(1)[:, None] + b.sum(1)[None] - inter
    sim = np.where(union > 0, inter / np.maximum(union, 1e-9), np.nan)
    sim[np.equal.outer(q, R)] = np.nan
    pred, avail, sup, _ = _knn(sim, atlas.Yc[R, T], k, gamma, floor)
    return RouteOutput(pred, avail, sup, ("top_sim", "mean_k_sim", "n_nn", "nn_agreement", "pred_norm"))


def route_pheno(atlas, q, T, visible, *, k=10, gamma=2.0, floor=0.0):
    R = ref_rows(atlas, T)
    L = atlas.Yc.shape[1]
    acc = np.zeros((len(q), len(R))); cnt = np.zeros((len(q), len(R)))
    for s in range(L):
        if s == T:
            continue
        qa = visible[:, s] & np.isfinite(atlas.Yc[q, s, 0])
        rb = np.isfinite(atlas.Yc[R, s, 0])
        if not qa.any() or not rb.any():
            continue
        Qs = unit_rows(np.nan_to_num(atlas.Yc[q, s]).astype(np.float32))
        Rs = unit_rows(np.nan_to_num(atlas.Yc[R, s]).astype(np.float32))
        c = Qs @ Rs.T
        m = qa[:, None] & rb[None]
        acc += np.where(m, c, 0.0); cnt += m
    sim = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
    sim[np.equal.outer(q, R)] = np.nan
    pred, avail, sup, _ = _knn(sim, atlas.Yc[R, T], k, gamma, floor)
    return RouteOutput(pred, avail, sup, ("top_sim", "mean_k_sim", "n_nn", "nn_agreement", "pred_norm"))


def route_genetic(atlas, q, T):
    p = atlas.Yc.shape[2]
    pred = np.zeros((len(q), p)); n_t = np.zeros(len(q)); n_all = np.zeros(len(q)); coh = np.zeros(len(q))
    for i, d in enumerate(q):
        tg = atlas.targets[d]
        n_all[i] = len(tg)
        vecs = []
        for g, sign in tg.items():
            j = atlas.kd_index.get(g)
            if j is None or not np.isfinite(atlas.KDc[j, T, 0]):
                continue
            vecs.append(sign * atlas.KDc[j, T])
        if vecs:
            V = np.stack(vecs)
            pred[i] = V.mean(0)
            n_t[i] = len(vecs)
            if len(vecs) > 1:
                U = unit_rows(V)
                g = U @ U.T
                coh[i] = (g.sum() - len(vecs)) / (len(vecs) * (len(vecs) - 1))
            else:
                coh[i] = 1.0
    avail = n_t > 0
    return RouteOutput(pred, avail, np.stack([n_t, n_all, coh, np.linalg.norm(pred, axis=1)], 1),
                       ("n_kd_targets", "n_targets", "kd_coherence", "pred_norm"))


def all_routes(atlas, q, T, visible, maps, params=None) -> dict:
    params = params or {}
    return {
        "context": route_context(atlas, q, T, visible, maps),
        "pheno": route_pheno(atlas, q, T, visible, **params.get("pheno", {})),
        "chem": route_chem(atlas, q, T, **params.get("chem", {})),
        "know": route_know(atlas, q, T, **params.get("know", {})),
        "genetic": route_genetic(atlas, q, T),
    }
