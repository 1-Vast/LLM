"""Learned in-context completion world for the viability-contrast task (protocol viability-contrast-5).

File summary
- Path: research/viability_contrast/world5.py
- Purpose: the learned compound-level virtual-cell channel, replacing world4's kNN kernel.
  A rank-r SVD basis of the training compounds' median-centred AUC matrix (median-imputed,
  a registered basis-fit approximation) defines a linear-Gaussian latent model; a held-out
  compound's purchased readings identify its latent coefficients by an exact Gaussian
  posterior, giving a predictive mean AND variance at every unpurchased line. The
  per-hypothesis predictive precision-blends the class template with this completion, so
  the blend weight adapts per line and per step (world4's fixed beta is the constant-
  variance special case). Also carries the phase-G5 genetic channel: per-class OLS of AUC
  on the line's CRISPR dependency on the class's primary target gene, kept only when it
  improves training log-likelihood.
- Interfaces / data: `fit_basis`, `select_rank`, `LearnedWorld` (update / mean_scale /
  reveal_genetic), `fit_genetic`.
- Depends on: research/viability_contrast/{prepare.py, qualify2.py}
"""
from __future__ import annotations

import numpy as np

RANK_GRID = (4, 8, 16)
K_FIT = 4
MIN_VAR = 0.05 ** 2


def fit_basis(A: np.ndarray, rank: int):
    """Rank-r linear-Gaussian basis of a (n_train, n_pool) AUC matrix with NaNs.

    Returns (center, V, tau2): per-line median centre; basis V (n_pool, r) scaled so the
    training coefficients have about unit variance (calibrated N(0, I) latent prior);
    per-line residual variance floored at MIN_VAR.
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
    p_mean = center + V @ w
    p_var = tau2 + np.einsum("pr,rr,pr->p", V, sig, V)
    return p_mean, np.maximum(p_var, MIN_VAR)


def select_rank(auc, train_by_class, train_pos, base_m, base_s, pool_arr, key, units):
    """Rank by simulated-episode log-likelihood on training compounds.

    For each training compound, K_FIT deterministic lines (SHA256-ordered among its
    measured pool lines) are treated as purchased; the own-class precision-blended
    predictive is scored by Gaussian log-likelihood on the compound's remaining measured
    pool lines. The basis is fitted once per candidate rank on all training compounds
    (basis-leakage approximation, registered in protocol5.json).
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
                bv = bs ** 2
                prec = 1.0 / bv[rest] + 1.0 / pv[rest]
                mu = (bm[rest] / bv[rest] + pm[rest] / pv[rest]) / prec
                var = 1.0 / prec
                z = (row[rest] - mu) / np.sqrt(var)
                ll += float(np.sum(-0.5 * np.minimum(z * z, 900.0) - 0.5 * np.log(var)))
        results[rank] = ll
    return max(results, key=results.get), results


class LearnedWorld:
    """Learned-completion predictive for one episode, updated as readings accumulate."""

    def __init__(self, center, V, tau2, base_mean, base_scale):
        # base_mean/base_scale: (n_classes, n_pool) validator-side templates
        self.center, self.V, self.tau2 = center, V, tau2
        self.base_mean, self.base_scale = base_mean, base_scale
        self.p_mean = None
        self.p_var = None
        self.gen_mean = np.full_like(base_mean, np.nan)   # (n_classes, n_pool)
        self.gen_var = np.full_like(base_mean, np.nan)

    def update(self, purchased_vals: np.ndarray, purchased_pos: np.ndarray) -> None:
        if len(purchased_pos) == 0:
            return
        w, sig = _posterior(self.center, self.V, self.tau2, purchased_vals, purchased_pos)
        self.p_mean, self.p_var = _predictive(self.center, self.V, self.tau2, w, sig)

    def reveal_genetic(self, ci: int, j: int, mean: float, var: float) -> None:
        self.gen_mean[ci, j] = mean
        self.gen_var[ci, j] = max(var, MIN_VAR)

    def mean_scale(self):
        """Precision blend of the class term (genetic where revealed, else template)
        with the profile completion."""
        bm = np.where(np.isfinite(self.gen_mean), self.gen_mean, self.base_mean)
        bv = np.where(np.isfinite(self.gen_var), self.gen_var, self.base_scale ** 2)
        if self.p_mean is None:
            return bm, np.sqrt(bv)
        pv = self.p_var[None, :]
        prec = 1.0 / bv + 1.0 / pv
        m = (bm / bv + self.p_mean[None, :] / pv) / prec
        s = np.sqrt(1.0 / prec)
        return m, s


def fit_genetic(auc, dep, pool_pos, members, gene_idx):
    """Per-class OLS of AUC on the line's dependency on the class gene.

    auc: full matrix; dep: (n_crispr_lines, n_genes); pool_pos: pool positions of the
    crispr lines; members: training compound positions of the class; gene_idx: column of
    the class gene in dep. Returns (alpha, beta, sigma2, delta_ll, n_pairs) or None.
    delta_ll is the training log-likelihood gain over the class template predictive on
    the same pairs (keep-if-it-helps discipline, protocol5.json phase G5).
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
