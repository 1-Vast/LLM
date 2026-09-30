"""Profile-conditioned world for the viability-contrast task (protocol viability-contrast-4).

File summary
- Path: research/viability_contrast/world4.py
- Purpose: the compound-level virtual-cell channel. Given the compound's own purchased
  readings, predict its next reading from profile-similar training compounds (Gaussian
  kernel on mean squared profile distance), blended with the class template by a beta fitted
  on training reading log-likelihood. The world proposes; the fixed validator scores.
- Interfaces / data: `profile_predict`, `fit_beta`, `ProfileWorld.mean_scale`.
- Depends on: research/viability_contrast/{prepare.py, qualify2.py}
"""
from __future__ import annotations

import numpy as np

BETA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)


def _profile_sim(train_auc: np.ndarray, query_vals: np.ndarray, query_pos: np.ndarray) -> np.ndarray:
    """Gaussian-kernel similarity of each training compound to the query profile.

    train_auc: (n_train, n_lines); query_vals/query_pos: purchased readings and their line
    positions. Distance = mean squared difference over jointly finite purchased coordinates.
    """
    t = train_auc[:, query_pos]                       # (n_train, J)
    fin = np.isfinite(t)
    d2 = np.where(fin, (t - query_vals[None, :]) ** 2, 0.0).sum(axis=1)
    cnt = fin.sum(axis=1)
    d = np.where(cnt > 0, d2 / np.maximum(cnt, 1), np.nan)
    scale = np.nanmedian(d)
    if not np.isfinite(scale) or scale <= 0:
        scale = 1.0
    sim = np.where(np.isfinite(d), np.exp(-np.where(np.isfinite(d), d, 0.0) / scale), 0.0)
    return sim


def profile_predict(train_auc: np.ndarray, sim: np.ndarray) -> np.ndarray:
    """Weighted mean AUC per line over training compounds (NaN where no weight)."""
    fin = np.isfinite(train_auc)
    w = sim[:, None] * fin
    den = w.sum(axis=0)
    num = (w * np.where(fin, train_auc, 0.0)).sum(axis=0)
    out = np.full(train_auc.shape[1], np.nan)
    has = den > 0
    out[has] = num[has] / den[has]
    return out


class ProfileWorld:
    """Profile-conditioned predictive for one episode, updated as readings accumulate."""

    def __init__(self, train_auc, beta, base_mean, base_scale):
        # train_auc: (n_train, n_pool); base_mean/base_scale: (n_classes, n_pool)
        self.train_auc = train_auc
        self.beta = beta
        self.base_mean = base_mean
        self.base_scale = base_scale
        self.prof = None

    def update(self, purchased_vals: np.ndarray, purchased_pos: np.ndarray) -> None:
        sim = _profile_sim(self.train_auc, purchased_vals, purchased_pos)
        self.prof = profile_predict(self.train_auc, sim)

    def mean_scale(self):
        if self.prof is None or self.beta == 0.0:
            return self.base_mean, self.base_scale
        has = np.isfinite(self.prof)
        m = np.where(has[None, :], (1 - self.beta) * self.base_mean + self.beta * self.prof[None, :],
                     self.base_mean)
        return m, self.base_scale


def fit_beta(auc, train_by_class, train_pos, units,
             med, scale, valid, med_p, scale_p, pool_arr):
    """Blend weight by training reading log-likelihood.

    For each training compound the profile prediction uses all OTHER training compounds
    (its unit excluded) and every pool line as a coordinate (fitting approximation,
    registered). The own-class predictive blends the class template with the profile
    prediction; the likelihood sums over measured readings.
    """
    base_m = np.where(valid, med, med_p[None, :])
    base_s = np.where(valid, scale, scale_p[None, :])
    results = {}
    profs = np.full((len(train_pos), auc.shape[1]), np.nan)
    for i, p in enumerate(train_pos):
        sim = _profile_sim(auc[train_pos], auc[p, pool_arr], pool_arr)
        # exclude own unit
        same = units[train_pos] == units[p]
        sim = sim.copy()
        sim[same] = 0.0
        profs[i] = profile_predict(auc[train_pos], sim)
    for beta in BETA_GRID:
        ll = 0.0
        for ci, members in enumerate(train_by_class):
            members = np.asarray(members, dtype=int)
            if len(members) == 0:
                continue
            rows = [int(np.where(train_pos == p)[0][0]) for p in members]
            m = base_m[ci]
            s = base_s[ci]
            has = np.isfinite(profs[rows])
            mu = np.where(has, (1 - beta) * m[None, :] + beta * profs[rows], np.broadcast_to(m, (len(rows), len(m))))
            a = auc[np.array(members)]
            z = (a - mu) / s[None, :]
            term = -0.5 * np.minimum(z * z, 900.0) - np.log(s[None, :])
            ll += float(np.nansum(term))
        results[beta] = ll
    return max(results, key=results.get), results
