"""Corrected learned-completion world for the viability-contrast task (protocol viability-contrast-5b).

File summary
- Path: research/viability_contrast/world5b.py
- Purpose: the v5 learned compound-level virtual-cell channel with the registered
  corrections of protocol5b.json. C1: the predictive variance uses the full quadratic
  form V sig V^T (world5 used only the diagonal of sig). C2: three fusion rules between
  the class template and the completion - 'precision' (v5 heuristic, retained for
  comparability), 'holdout' (convex blend with a training-selected scalar weight and a
  working variance), 'off' (template only). Rank and blend weight are both selected by
  the simulated-episode training log-likelihood machinery, with the basis-leakage
  approximation registered in protocol5.
- Interfaces / data: `fit_basis`, `select_rank`, `select_weight`, `LearnedWorld`
  (update / mean_scale / reveal_genetic), `fit_genetic` (unchanged from world5).
- Depends on: research/viability_contrast/{prepare.py, qualify2.py}
"""
from __future__ import annotations

import numpy as np

RANK_GRID = (4, 8, 16)
W_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
K_FIT = 4
MIN_VAR = 0.05 ** 2


def fit_basis(A: np.ndarray, rank: int):
    """Rank-r linear-Gaussian basis of a (n_train, n_pool) AUC matrix with NaNs.

    Identical to world5.fit_basis: per-line median centre; basis V scaled so the
    training coefficients have about unit variance; per-line residual variance floored.
    """
    n = A.shape[0]
    center = np.nanmedian(A, axis=0)
    center = np.where(np.isfinite(center), center, 0.0)
    Y = np.where(np.isfinite(A), A - center[None, :], 0.0)
    U, S, Vt = np.linalg.svd(Y, full_matrices=False)
    r = min(rank, len(S))
    V = Vt[:r].T * (S[:r] / np.sqrt(max(n, 1)))[None, :]
    recon = (U[:, :r] * S[:r][None, :]) @ Vt[:r]
    resid = np.where(np.isfinite(A), (A - center[None, :]) - recon, np.nan)
    tau2 = np.nanmean(resid ** 2, axis=0)
    tau2 = np.where(np.isfinite(tau2), tau2, np.nanvar(A, axis=0))
    tau2 = np.maximum(np.where(np.isfinite(tau2), tau2, 1.0), MIN_VAR)
    return center, V, tau2


def _posterior(center, V, tau2, vals, pos):
    """Exact Gaussian posterior over latent coefficients from purchased readings."""
    y = (vals - center[pos]) / tau2[pos]
    Vj = V[pos]
    W = Vj / tau2[pos][:, None]
    prec = Vj.T @ W + np.eye(V.shape[1])
    sig = np.linalg.inv(prec)
    w = sig @ (Vj.T @ y)
    return w, sig


def _predictive(center, V, tau2, w, sig):
    """C1 correction: full quadratic form V sig V^T (world5 read only diag(sig))."""
    p_mean = center + V @ w
    p_var = tau2 + np.einsum("pi,ij,pj->p", V, sig, V)
    return p_mean, np.maximum(p_var, MIN_VAR)


def blend(bm, bv, pm, pv, mode, w):
    """Fuse template (bm, bv) with completion (pm, pv) under the registered rules."""
    if mode == "off":
        return bm, bv
    if mode == "holdout":
        return w * pm + (1.0 - w) * bm, w * w * pv + (1.0 - w) ** 2 * bv
    # 'precision': the v5 uncalibrated heuristic (protocol5b C2)
    prec = 1.0 / bv + 1.0 / pv
    return (bm / bv + pm / pv) / prec, 1.0 / prec


def select_rank(auc, train_by_class, train_pos, base_m, base_s, pool_arr, key, units,
                blend_source="precision"):
    """Rank by simulated-episode log-likelihood on training compounds.

    The basis is fitted once per candidate rank on all training compounds. The blend
    used for scoring is the precision rule (as in v5) unless blend_source says
    otherwise; the corrected predictive variance (C1) applies in all cases, so the
    selected rank may differ from v5's.
    """
    import hashlib

    results = {}
    for rank in RANK_GRID:
        center, V, tau2 = fit_basis(auc[train_pos][:, pool_arr], rank)
        ll = 0.0
        for ci, members in enumerate(train_by_class):
            members = np.asarray(members, dtype=int)
            if len(members) == 0:
                continue
            for p in members:
                row = auc[p, pool_arr]
                fin = np.where(np.isfinite(row))[0]
                if len(fin) <= K_FIT:
                    continue
                order = sorted(fin, key=lambda j: hashlib.sha256(
                    f"{key}|rank|{units[p]}|{j}".encode()).hexdigest())
                pos = np.array(order[:K_FIT])
                w, sig = _posterior(center, V, tau2, row[pos], pos)
                pm, pv = _predictive(center, V, tau2, w, sig)
                rest = np.setdiff1d(fin, pos)
                bm, bs = base_m[ci], base_s[ci]
                mu, var = blend(bm[rest], bs[rest] ** 2, pm[rest], pv[rest],
                                blend_source, 0.5)
                z = (row[rest] - mu) / np.sqrt(var)
                ll += float(np.sum(-0.5 * np.minimum(z * z, 900.0) - 0.5 * np.log(var)))
        results[rank] = ll
    return max(results, key=results.get), results


def select_weight(auc, train_by_class, base_m, base_s, pool_arr, key, units,
                  center, V, tau2):
    """Holdout-blend weight by simulated-episode log-likelihood (protocol5b C2).

    One scalar w in W_GRID per fold, selected on training compounds only with the basis
    fixed at the fold's selected rank. w = 0 is the template-only option, so the
    selection can retire the completion channel on its own.
    """
    import hashlib

    results = {}
    for w_sel in W_GRID:
        ll = 0.0
        for ci, members in enumerate(train_by_class):
            members = np.asarray(members, dtype=int)
            if len(members) == 0:
                continue
            for p in members:
                row = auc[p, pool_arr]
                fin = np.where(np.isfinite(row))[0]
                if len(fin) <= K_FIT:
                    continue
                order = sorted(fin, key=lambda j: hashlib.sha256(
                    f"{key}|weight|{units[p]}|{j}".encode()).hexdigest())
                pos = np.array(order[:K_FIT])
                w, sig = _posterior(center, V, tau2, row[pos], pos)
                pm, pv = _predictive(center, V, tau2, w, sig)
                rest = np.setdiff1d(fin, pos)
                bm, bs = base_m[ci], base_s[ci]
                mu, var = blend(bm[rest], bs[rest] ** 2, pm[rest], pv[rest],
                                "holdout", w_sel)
                z = (row[rest] - mu) / np.sqrt(var)
                ll += float(np.sum(-0.5 * np.minimum(z * z, 900.0) - 0.5 * np.log(var)))
        results[w_sel] = ll
    return max(results, key=results.get), results


class LearnedWorld:
    """Learned-completion predictive for one episode, updated as readings accumulate."""

    def __init__(self, center, V, tau2, base_mean, base_scale, blend_mode="precision",
                 blend_w=0.5):
        # base_mean/base_scale: (n_classes, n_pool) validator-side templates
        self.center, self.V, self.tau2 = center, V, tau2
        self.base_mean, self.base_scale = base_mean, base_scale
        self.blend_mode = blend_mode
        self.blend_w = float(blend_w)
        self.p_mean = None
        self.p_var = None
        self.gen_mean = np.full_like(base_mean, np.nan)   # (n_classes, n_pool)
        self.gen_var = np.full_like(base_mean, np.nan)

    def update(self, purchased_vals: np.ndarray, purchased_pos: np.ndarray) -> None:
        if self.blend_mode == "off" or len(purchased_pos) == 0:
            return
        w, sig = _posterior(self.center, self.V, self.tau2, purchased_vals, purchased_pos)
        self.p_mean, self.p_var = _predictive(self.center, self.V, self.tau2, w, sig)

    def reveal_genetic(self, ci: int, j: int, mean: float, var: float) -> None:
        self.gen_mean[ci, j] = mean
        self.gen_var[ci, j] = max(var, MIN_VAR)

    def mean_scale(self):
        """Blended predictive over classes: template (genetic where revealed) fused
        with the completion under the world's registered fusion rule."""
        bm = np.where(np.isfinite(self.gen_mean), self.gen_mean, self.base_mean)
        bv = np.where(np.isfinite(self.gen_var), self.gen_var, self.base_scale ** 2)
        if self.p_mean is None:
            return bm, np.sqrt(bv)
        pv = self.p_var[None, :]
        pm = self.p_mean[None, :]
        m, v = blend(bm, bv, pm, pv, self.blend_mode, self.blend_w)
        return m, np.sqrt(np.maximum(v, MIN_VAR))


def fit_genetic(auc, dep, pool_pos, members, gene_idx):
    """Per-class OLS of AUC on the line's dependency on the class gene.

    Unchanged from world5.fit_genetic (frozen); the known baseline flaw of the frozen
    fit is documented in README section 3.6 and re-analysed post hoc there. The gated
    tier that consumes this fit is itself gated on a realistic arm qualifying.
    """
    rows, ds, ys = [], [], []
    for p in members:
        a = auc[p, pool_pos]
        fin = np.isfinite(a) & np.isfinite(dep[:, gene_idx])
        if fin.sum() < 5:
            continue
        rows.append(p)
        ds.append(dep[fin, gene_idx])
        ys.append(a[fin])
    if not rows:
        return None
    d = np.concatenate(ds)
    y = np.concatenate(ys)
    X = np.column_stack([np.ones_like(d), d])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    fit = X @ coef
    sigma2 = max(float(np.mean((y - fit) ** 2)), MIN_VAR)
    ll_gen = float(np.sum(-0.5 * (y - fit) ** 2 / sigma2 - 0.5 * np.log(sigma2)))
    m = np.median(y)
    s2 = max(float(np.median(np.abs(y - m)) * 1.4826) ** 2, MIN_VAR)
    ll_tpl = float(np.sum(-0.5 * (y - m) ** 2 / s2 - 0.5 * np.log(s2)))
    return float(coef[0]), float(coef[1]), sigma2, ll_gen - ll_tpl, int(len(y))
