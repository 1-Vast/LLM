"""Identifiability map: which mechanism pairs can one observation separate, and when (H5).

For classes with reference drugs, the predicted cross-rejection R_pred[a, b, o] is the probability
that a drug of class a, observed at option o alone, rejects hypothesis b at alpha. It is simulated
from reference data only: potency lambda ~ N(1, tau^2) clipped at 0, prototype of a at o, and a
residual vector resampled from reference residuals at o; b's p-value uses the single-option
calibration of b's bucket.

The realised cross-rejection R_real[a, b, o] is the fraction of query drugs of class a with option
o whose single-option p-value for b is <= alpha.

Outputs: agreement between predicted and realised rates across cells, the predicted
non-identifiable pairs (max over the menu of both directions below a floor) and how often they were
separated in reality, and the time split (6 h vs 24 h) of the best option per pair.
"""
from __future__ import annotations

import numpy as np

import falsify as F


def predicted_cross_rejection(fz: F.Falsifier, classes: np.ndarray, n_sim: int = 64, seed: int = 0,
                              lam_pool: np.ndarray | None = None) -> np.ndarray:
    """R_pred (A, A, n_opt) for hypothesis indices ``classes`` (which are also the reference set of
    relative scores), using the falsifier's own calibration and p-value rule. Potencies are resampled
    from ``lam_pool`` (fitted on reference drugs) when given, else drawn from the prior N(1, tau^2)."""
    rng = np.random.default_rng(seed)
    P = fz.P[classes]  # (A, n_opt, K)
    A_, n_opt, K = P.shape
    out = np.full((A_, A_, n_opt), np.nan)
    for o in range(n_opt):
        pool = fz.resid_pool[o]
        v = fz.noise.var[o]
        mu = P[:, o]  # (A, K)
        okc = ~np.isnan(mu[:, 0])
        mu0 = np.nan_to_num(mu)
        if lam_pool is not None and len(lam_pool):
            lam = rng.choice(lam_pool, size=(A_, n_sim), replace=True)
        else:
            lam = np.clip(rng.normal(1.0, np.sqrt(fz.noise.tau2), size=(A_, n_sim)), 0, None)
        e = pool[rng.integers(0, len(pool), size=(A_, n_sim))]  # (A, n_sim, K)
        Zs = (lam[..., None] * mu0[:, None, :] + e).reshape(-1, K)  # (A * n_sim, K)
        Q = np.sum(Zs * Zs / v, axis=1)
        b = (Zs / v) @ mu0.T
        Am = np.sum(mu0 * mu0 / v, axis=1)
        nll, _ = F.score_from_stats(Q[:, None], b, Am[None], fz.noise.tau2, 1)
        s = fz._scores(nll, ~okc)
        p = fz.cal.pvalues(s, Q, fz.buckets[classes], (o,), classes)  # (A * n_sim, A)
        out[:, :, o] = (p <= fz.alpha).reshape(A_, n_sim, A_).mean(axis=1)
        out[~okc, :, o] = np.nan
        out[:, ~okc, o] = np.nan
    return out


def realised_cross_rejection(fz: F.Falsifier, Z: np.ndarray, labels: np.ndarray, queries: np.ndarray,
                             classes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """R_real (A, A, n_opt) and counts (A, n_opt) from query drugs' single-option p-values."""
    names = fz.names[classes]
    pos = {n: i for i, n in enumerate(names)}
    A_, n_opt = len(classes), Z.shape[1]
    hits = np.zeros((A_, A_, n_opt))
    cnt = np.zeros((A_, n_opt))
    for qi in queries:
        a = pos.get(labels[qi])
        if a is None:
            continue
        for o in range(n_opt):
            if np.isnan(Z[qi, o, 0]):
                continue
            p = fz.pvalues(Z[qi], [o], classes)
            hits[a, :, o] += p <= fz.alpha
            cnt[a, o] += 1
    with np.errstate(invalid="ignore", divide="ignore"):
        real = hits / cnt[:, None, :]
    return real, cnt
