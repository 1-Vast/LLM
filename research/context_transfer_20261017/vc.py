"""Virtual Cell core for context transfer: a low-rank Gaussian response model with a basal prior.

File summary
- Path: research/context_transfer_20261017/vc.py
- Purpose: predict a new context's response to every item, before and after a few measured
  items, with closed-form uncertainty, and turn that into P(registered event) per item.
- Core points:
  - Fitted on source contexts only: y_c = mu + V f_c + e, e_d ~ N(0, s2_d); f_c has a prior from
    a ridge map of basal-expression principal components (leave-one-out residual covariance), or
    the population covariance when a context has no basal profile.
  - Observing items R updates f_c by Bayesian linear regression; predictive mean/variance follow.
  - Event thresholds per item come from source-only residual fits on the generic profile, so
    P(event) targets the same rule the grader applies to the full matrix.
  - This is a response model, not a mechanism or a cell trajectory.
- Interfaces: `ContextModel.fit(Y_s, X_s, ...)`, `.prior(x)`, `.posterior(state, idx, y)`,
  `.predict(state)`, `.event_prob(state)`, `.misfit(state0, idx, y)`.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import ndtr

from common import Z_EVENT, residualise, robust_z


@dataclass
class State:
    m: np.ndarray        # posterior mean of f (r,)
    S: np.ndarray        # posterior covariance of f (r, r)
    observed: np.ndarray  # item indices already measured in this context


class ContextModel:
    def __init__(self, rank: int = 20, n_pcs: int = 30, n_genes: int = 2000, abs_gate=None,
                 min_measured: int = 10, impute_iters: int = 0):
        self.rank, self.n_pcs, self.n_genes = rank, n_pcs, n_genes
        self.abs_gate, self.min_measured = abs_gate, min_measured
        # 0: mean imputation and in-sample noise (version 1). >0: EM-SVD imputation of unmeasured
        # pairs for that many iterations and degrees-of-freedom-corrected noise (version 2).
        self.impute_iters = impute_iters

    # ---------- fitting on source contexts ----------
    def fit(self, Y: np.ndarray, X: np.ndarray):
        Y = np.asarray(Y, dtype=float)
        n, D = Y.shape
        finite = np.isfinite(Y)
        self.n_source = finite.sum(0)
        mu = np.where(self.n_source > 0, np.nanmean(np.where(finite, Y, np.nan), 0), np.nan)
        mu = np.where(np.isfinite(mu), mu, np.nanmean(mu))
        self.mu = mu
        R = np.where(finite, Y - mu, 0.0)
        U, s, Vt = np.linalg.svd(R, full_matrices=False)
        r = min(self.rank, len(s))
        for _ in range(self.impute_iters):
            L = (U[:, :r] * s[:r]) @ Vt[:r]
            U, s, Vt = np.linalg.svd(np.where(finite, Y - mu, L), full_matrices=False)
        self.V = Vt[:r].T * s[:r] / np.sqrt(n)          # D x r loadings, f ~ unit-scale
        F = U[:, :r] * np.sqrt(n)                         # n x r source factors
        resid = np.where(finite, Y - mu - F @ self.V.T, np.nan)
        s2 = np.nanmean(resid ** 2, 0)
        if self.impute_iters:
            n_i = self.n_source.astype(float)
            s2 = s2 * n_i / np.maximum(n_i - r, 1.0)
        floor = np.nanmedian(s2)
        self.s2 = np.where(np.isfinite(s2) & (s2 > 0), np.maximum(s2, 0.05 * floor), floor)
        self.F = F
        self.pop_cov = np.cov(F.T) + 1e-6 * np.eye(r)
        self._fit_prior(F, X)
        self._fit_thresholds(Y)
        self.source_event_rate = self._source_event_rate(Y)
        # a well on an unmeasured pair yields nothing, so scores are expected hits per well
        self.measured_rate = (self.n_source + 0.5) / (n + 1.0)
        return self

    def _fit_prior(self, F, X):
        X = np.asarray(X, dtype=float)
        ok = np.isfinite(X).all(1)
        self.has_prior = ok.sum() >= 20
        if not self.has_prior:
            return
        Xs = X[ok]
        var = Xs.var(0)
        self.genes = np.argsort(-var)[: self.n_genes]
        Z = Xs[:, self.genes]
        self.x_mu, self.x_sd = Z.mean(0), Z.std(0) + 1e-6
        Z = (Z - self.x_mu) / self.x_sd
        _, _, Wt = np.linalg.svd(Z, full_matrices=False)
        self.W = Wt[: self.n_pcs].T
        P = Z @ self.W
        P1 = np.column_stack([np.ones(len(P)), P])
        Fo = F[ok]
        best = None
        for alpha in (1.0, 10.0, 100.0, 1000.0, 10000.0):
            A = P1.T @ P1 + alpha * np.diag([0.0] + [1.0] * P.shape[1])
            B = np.linalg.solve(A, P1.T @ Fo)
            H = np.einsum("ij,jk,ik->i", P1, np.linalg.inv(A), P1)
            loo = (Fo - P1 @ B) / (1 - H)[:, None]
            err = (loo ** 2).mean()
            if best is None or err < best[0]:
                best = (err, alpha, B, loo)
        _, self.alpha, self.B, loo = best
        self.prior_cov = np.cov(loo.T) + 1e-6 * np.eye(F.shape[1])

    def _fit_thresholds(self, Y):
        G = np.nanmedian(Y, axis=1)
        S, coef = residualise(Y.T, G, min_finite=self.min_measured)
        _, med, mad = robust_z(S)
        self.a, self.b = coef[:, 0], coef[:, 1]
        self.med, self.mad = med, mad
        ok = np.isfinite(self.a) & np.isfinite(self.b) & np.isfinite(med)
        self.threshold_ok = ok

    def _source_event_rate(self, Y):
        G = np.nanmedian(Y, axis=1)
        S, _ = residualise(Y.T, G, min_finite=self.min_measured)
        Z, _, _ = robust_z(S)
        with np.errstate(invalid="ignore"):
            ev = Z <= Z_EVENT
            if self.abs_gate is not None:
                ev &= Y.T <= self.abs_gate
        n = np.isfinite(Y.T).sum(1)
        return (ev.sum(1) + 0.1) / (n + 1.0)

    # ---------- a new context ----------
    def prior(self, x) -> State:
        r = self.V.shape[1]
        x = None if x is None else np.asarray(x, dtype=float)
        if self.has_prior and x is not None and np.isfinite(x).all():
            z = (x[self.genes] - self.x_mu) / self.x_sd
            p1 = np.concatenate([[1.0], z @ self.W])
            return State(p1 @ self.B, self.prior_cov.copy(), np.array([], dtype=int))
        return State(np.zeros(r), self.pop_cov.copy(), np.array([], dtype=int))

    def posterior(self, st: State, idx, y) -> State:
        idx = np.asarray(idx, dtype=int)
        y = np.asarray(y, dtype=float)
        keep = np.isfinite(y)
        idx_f, y_f = idx[keep], y[keep]
        observed = np.concatenate([st.observed, idx])
        if len(idx_f) == 0:
            return State(st.m.copy(), st.S.copy(), observed)
        Vr = self.V[idx_f]
        w = 1.0 / self.s2[idx_f]
        P0 = np.linalg.inv(st.S)
        P = P0 + (Vr * w[:, None]).T @ Vr
        S = np.linalg.inv(P)
        m = S @ (P0 @ st.m + (Vr * w[:, None]).T @ (y_f - self.mu[idx_f]))
        return State(m, (S + S.T) / 2, observed)

    def predict(self, st: State):
        mean = self.mu + self.V @ st.m
        var = np.einsum("dr,rs,ds->d", self.V, st.S, self.V) + self.s2
        return mean, var

    def thresholds(self, st: State):
        mean, _ = self.predict(st)
        Gc = np.median(mean)
        t = self.a + self.b * Gc + self.med + Z_EVENT * self.mad
        if self.abs_gate is not None:
            t = np.minimum(t, self.abs_gate)
        return np.where(self.threshold_ok, t, -np.inf)

    def event_prob(self, st: State):
        mean, var = self.predict(st)
        t = self.thresholds(st)
        return ndtr((t - mean) / np.sqrt(var))

    def expected_hit(self, st: State):
        """Expected hits per well: source measurement rate x P(event | measured)."""

        return self.measured_rate * self.event_prob(st)

    def log_density(self, st: State, idx, y) -> float:
        """Mean Gaussian predictive log density of measured items (finite y only)."""

        idx = np.asarray(idx, dtype=int)
        y = np.asarray(y, dtype=float)
        keep = np.isfinite(y)
        mean, var = self.predict(st)
        r = y[keep] - mean[idx[keep]]
        v = var[idx[keep]]
        return float((-0.5 * (np.log(2 * np.pi * v) + r ** 2 / v)).mean())

    def misfit(self, st0: State, idx, y) -> float:
        """Mean squared standardized residual of measured items under the pre-measurement predictive."""

        idx = np.asarray(idx, dtype=int)
        y = np.asarray(y, dtype=float)
        keep = np.isfinite(y)
        if keep.sum() == 0:
            return float("nan")
        mean, var = self.predict(st0)
        return float((((y[keep] - mean[idx[keep]]) ** 2) / var[idx[keep]]).mean())


def select_rank(Y, X, candidates=(5, 10, 20, 40), k_probe: int = 8, abs_gate=None,
                min_measured: int = 10, salt: str = "rank-select", n_inner: int = 3) -> tuple[int, dict]:
    """Choose the rank by inner cross-validation on source contexts only.

    For each candidate rank, fit on the other inner folds; for each inner held-out context, observe
    `k_probe` hash-chosen items and score the predictive log density of its remaining measured
    items. The rank with the highest mean wins (ties to the smaller rank).
    """

    from common import folds, tie_order

    n = Y.shape[0]
    keys = [f"{salt}:{i}" for i in range(n)]
    fid = folds(keys, salt, n_inner)
    scores = {}
    for r in candidates:
        vals = []
        for k in range(n_inner):
            tr, te = np.flatnonzero(fid != k), np.flatnonzero(fid == k)
            m = ContextModel(rank=r, abs_gate=abs_gate, min_measured=min_measured).fit(Y[tr], X[tr])
            for c in te:
                order = tie_order(np.arange(Y.shape[1]).astype(str), f"{salt}:probe:{c}")
                probe = np.argsort(order)[:k_probe]
                x = X[c] if np.isfinite(X[c]).all() else None
                st = m.posterior(m.prior(x), probe, Y[c, probe])
                rest = np.setdiff1d(np.flatnonzero(np.isfinite(Y[c])), probe)
                vals.append(m.log_density(st, rest, Y[c, rest]))
        scores[r] = float(np.mean(vals))
    best = max(candidates, key=lambda r: (round(scores[r], 6), -r))
    return best, scores
