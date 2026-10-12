"""Block Q engine: route tables, certificates and predictions for any atlas (development or confirmation).

The atlas stacks reference compounds (``ref`` True) and query/library compounds (``ref`` False).
Library responses are present in ``Yc`` but routes read a library compound's own lines only through
an explicit visibility mask, and analogue routes read references only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import rkt
from pool import SPECIFIC_ROUTES, perp

SUPPORT_DIM = {"context": 3, "pheno": 5, "chem": 5, "know": 5, "genetic": 4}


def generic_direction(atlas: rkt.Atlas, thr: np.ndarray) -> np.ndarray:
    """Per line: unit mean centred response of active references (vehicle-quantile activity)."""
    L, p = atlas.Yc.shape[1], atlas.Yc.shape[2]
    G = np.zeros((L, p))
    for T in range(L):
        rows = atlas.ref & np.isfinite(atlas.Yc[:, T, 0])
        raw_norm = np.linalg.norm(atlas.Yc[rows, T] + atlas.mu[T], axis=1)
        a = raw_norm > thr[T]
        if a.sum() >= 5:
            G[T] = atlas.Yc[rows, T][a].mean(0)
    return rkt.unit_rows(G)


def gamma_estimate(atlas: rkt.Atlas, thr: np.ndarray, G: np.ndarray) -> float:
    """Mean cosine of active reference responses with their line's generic direction."""
    vals = []
    for T in range(atlas.Yc.shape[1]):
        rows = atlas.ref & np.isfinite(atlas.Yc[:, T, 0])
        Yr = atlas.Yc[rows, T].astype(np.float64)
        a = np.linalg.norm(Yr + atlas.mu[T], axis=1) > thr[T]
        if a.sum() >= 5:
            # leave-one-out generic direction so a reference does not score against itself
            s = Yr[a].sum(0)
            loo = rkt.unit_rows(s[None] - Yr[a])
            vals.append(rkt.centred_cosine(loo, Yr[a]))
    return float(np.mean(np.concatenate(vals)))


def own_activity(atlas: rkt.Atlas, q: np.ndarray, T: int, visible: np.ndarray, thr: np.ndarray) -> np.ndarray:
    """Activity of each query compound in its visible other lines: count active, max and mean norm ratio."""
    L = atlas.Yc.shape[1]
    out = np.zeros((len(q), 3))
    raw = atlas.Yc[q] + atlas.mu[None]
    norms = np.linalg.norm(np.nan_to_num(raw), axis=2) / thr[None]
    have = np.isfinite(atlas.Yc[q, :, 0]) & visible
    have[:, T] = False
    for i in range(len(q)):
        v = norms[i, have[i]]
        if len(v):
            out[i] = [(v > 1).sum(), v.max(), v.mean()]
    return out


def features(routes: dict, oa: np.ndarray) -> np.ndarray:
    cols = []
    for r in SPECIFIC_ROUTES:
        o = routes[r]
        cols.append(o.available.astype(float)[:, None])
        cols.append(np.where(o.available[:, None], o.support, 0.0))
    cols.append(oa)
    return np.concatenate(cols, 1)


@dataclass
class QueryBlock:
    q: np.ndarray
    T: int
    routes: dict
    F: np.ndarray


def slice_route(o: rkt.RouteOutput, rows: np.ndarray) -> rkt.RouteOutput:
    return rkt.RouteOutput(o.pred[rows], o.available[rows], o.support[rows], o.support_names)


def query_block(atlas, q, T, visible, maps, thr, cache: dict | None = None, static: dict | None = None) -> QueryBlock:
    """Routes and features for queries ``q`` in line ``T``; knowledge routes are cached per (T, q).

    ``static`` optionally supplies the visibility-independent chem/know routes already computed for ``q``.
    """
    routes = {"context": rkt.route_context(atlas, q, T, visible, maps),
              "pheno": rkt.route_pheno(atlas, q, T, visible)}
    key = (T, q.tobytes())
    if static is not None:
        routes.update(static)
    elif cache is not None and key in cache:
        routes.update(cache[key])
    else:
        static = {"chem": rkt.route_chem(atlas, q, T), "know": rkt.route_know(atlas, q, T)}
        if cache is not None:
            cache[key] = static
        routes.update(static)
    oa = own_activity(atlas, q, T, visible, thr)
    return QueryBlock(q, T, routes, features(routes, oa))


def predict_block(block: QueryBlock, pooler, G: np.ndarray, gamma: float):
    """Certificate and unit centred prediction (generic + certified specific direction)."""
    preds = {r: block.routes[r].pred for r in SPECIFIC_ROUTES}
    av = {r: block.routes[r].available for r in SPECIFIC_ROUTES}
    Gq = np.repeat(G[block.T][None], len(block.q), 0)
    s, cert = pooler.certify(preds, Gq, block.F, av)
    rho = np.where(cert.refusal == "", cert.rho, 0.0)
    direction = rkt.unit_rows(gamma * Gq + (rho * np.sqrt(max(1 - gamma * gamma, 0)))[:, None] * s)
    expected_cos = np.sqrt(gamma ** 2 + rho ** 2 * (1 - gamma ** 2))
    return direction, s, cert, expected_cos
