"""The registered feedback-update repair: leave-one-pool-out diagnosis and analogue-anchored re-propagation.

File summary
- Path: research/feedback_propagation_20261018/repair.py
- Purpose: one small, deterministic feedback-update program for a compound's observed history `(P, y)`.
  It does not touch the base predictor (structure prior, line covariance, endpoint, acquisition rule).
- Failure being repaired: the base update propagates the history through a global Gaussian covariance. Events
  are extremes of a compound-specific selective profile, and the linear conditional mean of the global model
  regresses them to the prior, so for some compounds the propagated profile is no better than the prior
  (observed in development) while the training profiles that agree with the history carry the shape.
- Program (all steps use only the history, the training set and the fitted world):
  1. Diagnose. For every probed pool g in turn (leave-one-pool-out), predict the lines of g from the other pools
     with (a) the base Gaussian update and (b) the analogue-anchored update, and compare the mean squared
     error on g. This is the propagation task itself: values in pools that were not measured.
  2. Repair. If (b) has the smaller total error, propagate with (b): replace the structure prior by the mean
     profile of the K training compounds closest to the history, then apply the Gaussian update to the
     residual. Otherwise keep (a). A history of fewer than `MIN_POOLS` pools cannot be diagnosed and keeps (a).
- Reduces to the base update when the gate is closed or `lam = 0`; with `gate="always"` it is the anchored update
  without diagnosis (the ablation that tells whether the diagnosis adds anything).
- Interfaces: `REGISTERED`, `analog_profile`, `anchored_profile`, `lopo_pool_errors`, `repair_profile`, `score_repair`.
"""
from __future__ import annotations

import warnings

import numpy as np

import rules as R
from bench import call_score

MIN_POOLS = 3
REGISTERED = {"K": 10, "lam": 1.0, "gate": "lopo", "margin": 0.0, "loss": "mse"}


def analog_profile(fold, P, y, K: int) -> np.ndarray:
    """Mean profile of the K training compounds closest to the history on the probed lines (line mean if unmeasured)."""

    w = fold.world
    ref = w.Ytrain[:, P]
    diff = ref - y[None, :]
    both = np.isfinite(diff)
    dist = np.where(both, diff ** 2, 0.0).sum(1) / np.maximum(both.sum(1), 1)
    dist[both.sum(1) < max(1, len(P) // 2)] = np.inf
    nn = np.argsort(dist, kind="stable")[:K]
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        pred = np.nanmean(w.Ytrain[nn], axis=0)
    return np.where(np.isfinite(pred), pred, w.mu)


def anchored_profile(fold, i, P, y, K: int, lam: float) -> np.ndarray:
    """Gaussian update of the residual about a prior that blends the structure prior and the analogue mean."""

    P, y = R._clean(P, y)
    if len(P) == 0:
        return fold.prior[i].copy()
    m = (1.0 - lam) * fold.prior[i] + lam * analog_profile(fold, P, y, K)
    return R.conditional_mean(fold, m, P, y)


def _loss(pred: np.ndarray, obs: np.ndarray, kind: str) -> float:
    if kind == "mse":
        return float(((pred - obs) ** 2).sum())
    if kind == "kill":
        w = 1.0 + 3.0 * (obs <= -1.0)
        return float((w * (pred - obs) ** 2).sum())
    if kind == "spearman":
        if len(obs) < 3 or np.ptp(obs) == 0 or np.ptp(pred) == 0:
            return 0.0
        a = np.argsort(np.argsort(pred)).astype(float)
        b = np.argsort(np.argsort(obs)).astype(float)
        return float(-len(obs) * np.corrcoef(a, b)[0, 1])
    raise ValueError(kind)


def lopo_pool_errors(fold, i, P, y, K: int, lam: float, loss: str = "mse") -> tuple[float, float, int]:
    """Total leave-one-pool-out loss of the base and the anchored update on the held-out pool's lines (lower = better)."""

    P, y = R._clean(P, y)
    pools = fold.pid[P]
    uniq = sorted(set(pools.tolist()))
    e_base = e_anch = 0.0
    n = 0
    for g in uniq:
        out = pools == g
        keep = ~out
        if keep.sum() < 2:
            continue
        Pk, yk = P[keep], y[keep]
        base = R.conditional_mean(fold, fold.prior[i], Pk, yk)
        anch = anchored_profile(fold, i, Pk, yk, K, lam)
        Pg, yg = P[out], y[out]
        e_base += _loss(base[Pg], yg, loss)
        e_anch += _loss(anch[Pg], yg, loss)
        n += int(out.sum())
    return e_base, e_anch, n


def repair_profile(fold, i, P, y, K: int = 10, lam: float = 1.0, gate: str = "lopo", margin: float = 0.0,
                   loss: str = "mse") -> np.ndarray:
    P, y = R._clean(P, y)
    base = R.conditional_mean(fold, fold.prior[i], P, y)
    if gate == "never" or len(P) == 0:
        return base
    if gate == "always":
        return anchored_profile(fold, i, P, y, K, lam)
    if len(set(fold.pid[P].tolist())) < MIN_POOLS:
        return base
    e_base, e_anch, n = lopo_pool_errors(fold, i, P, y, K, lam, loss)
    if n and e_anch < e_base - margin * abs(e_base):
        return anchored_profile(fold, i, P, y, K, lam)
    return base


def score_repair(fold, i, P, y, **params) -> np.ndarray:
    prm = {**REGISTERED, **params}
    return call_score(repair_profile(fold, i, P, y, **prm), fold.G)
