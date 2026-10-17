"""Bridged context transfer: a low-rank Bayesian response model that a few measured wells can verify.

File summary
- Path: src/virtual_cell/bridged_transfer.py
- Purpose: predict, for a new biological context (a cell line or a primary patient sample), the
  chance that each item of a screening library is a selective hit. Predictions are available
  before any well and after a few measured "bridge" wells. Closed-form uncertainty lets an agent
  decide which wells to measure first.
- Model: fitted on source contexts only.
  - Response: ``y_c = mu + V f_c + e``, with ``e_d ~ N(0, s2_d)`` and rank r.
  - Fit: unmeasured source pairs are imputed by EM-SVD at rank r (``impute_iters`` rounds). Each
    item's noise is its residual variance on measured pairs, corrected by ``n_i / (n_i - r)``.
  - Prior on ``f_c``: a ridge map from basal-expression principal components, with alpha by
    leave-one-out and the leave-one-out residual covariance. A context without a basal profile
    gets the population covariance, and its state says so (``prior_source``).
  - Measuring items updates ``f_c`` by Bayesian linear regression.
  - Event thresholds per item come from source-only residual fits on the generic context profile,
    so ``event_prob`` targets the same rule as `selective_events`.
  - ``expected_hit`` is per well: the item's source measurement rate times P(event). A well on an
    unmeasured pair yields nothing.
- Endpoint (`selective_events`):
  - G is the context's median over items, and each item's residual on [1, G] is robust-z scored
    across contexts.
  - An event is z <= -3, plus an optional absolute gate.
  - Items measured in fewer than ``min_measured`` contexts have no events.
- Refusals:
  - ``TOO_FEW_SOURCE_CONTEXTS``: fewer source contexts than the rank needs.
  - ``ITEM_AXIS_MISMATCH``: features or outcomes do not match the fitted axes.
- This is a response model, not a mechanism, a trajectory or measured evidence.
- Interfaces: `selective_events`, `residualise`, `robust_z`, `BridgeState`,
  `BridgedTransferModel` (`fit`, `prior`, `posterior`, `predict`, `thresholds`, `event_prob`,
  `expected_hit`, `misfit`, `source_events`, `source_event_rate`), `normal_cdf`.
- Depends on: numpy. If scipy is installed, `normal_cdf` uses its ``ndtr``, as the source study
  did. Otherwise a numpy approximation is used (relative error below 1.2e-7), which can break exact
  near-ties differently.

Scope of the evidence: 2026-10-17, ``research/context_transfer_20261017``, frozen
2026-10-17T04:43:08Z and run once on Beat AML 2.0 (`VALIDATED_SCOPE`).
- Confirmation domain:
  - 520 primary AML samples with RNA-seq, from 479 patients, x 166 single-agent inhibitors;
  - probit-fit AUC from the release's paper-inclusion set, with about 62% of sample-inhibitor pairs
    measured;
  - `selective_events` with no absolute gate and at least 100 measured samples per inhibitor,
    giving 2.1 events per sample;
  - 16 wells per sample, five patient-disjoint folds, and the rank chosen per fold by inner
    decisions (40, 10, 20, 20, 20).
- Supported:
  - The prior beat nearest-context transfer (event rate of the 10 nearest source samples by basal
    expression): +0.075 hits per sample [+0.014, +0.137], Holm p 0.017.
  - Updated by four exploit-first bridge wells, it beat the prior alone by +0.073 [+0.025, +0.127].
- Not shown:
  - The prior alone did not beat the context-free item prior (the item's source event rate):
    -0.008 [-0.063, +0.050]. Its edge over nearest-context transfer is largely that baseline's
    weakness (nearest-context minus item: -0.083).
  - The basal profile matters against a wrong one (shuffled-context control: +0.081), but on this
    endpoint not against none.
- Development only: on PRISM 19Q4 (exposed), the prior beat the item prior by +0.68 hits at 32
  wells (line holdout) and +0.35 (lineage holdout).
- Not validated:
  - other assays, endpoints, well budgets or measurement-availability structures;
  - prospective plating.
  This is a response model, not a mechanism.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

VALIDATED_SCOPE = "beataml2_primary_aml_inhibitor_auc_selective_events_16_wells_patient_disjoint"
Z_EVENT = -3.0
TOO_FEW_SOURCE_CONTEXTS = "TOO_FEW_SOURCE_CONTEXTS"
ITEM_AXIS_MISMATCH = "ITEM_AXIS_MISMATCH"
RIDGE_ALPHAS = (1.0, 10.0, 100.0, 1000.0, 10000.0)


class TransferRefused(ValueError):
    """A named refusal; ``code`` is one of the module's refusal constants."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


try:  # exact parity with the source study when scipy is present
    from scipy.special import ndtr as _ndtr
except ImportError:  # pragma: no cover - exercised by the numpy fallback test
    _ndtr = None


def _erfc(x: np.ndarray) -> np.ndarray:
    """Complementary error function (Chebyshev fit; fractional error below 1.2e-7)."""

    z = np.abs(x)
    t = 1.0 / (1.0 + 0.5 * z)
    poly = (-z * z - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 + t * (
        -0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (
            -0.82215223 + t * 0.17087277)))))))))
    r = t * np.exp(poly)
    return np.where(x >= 0, r, 2.0 - r)


def normal_cdf(x, exact: bool | None = None) -> np.ndarray:
    """Standard normal CDF; ``exact=False`` forces the numpy approximation."""

    x = np.asarray(x, dtype=float)
    if _ndtr is not None and exact is not False:
        return _ndtr(x)
    return 0.5 * _erfc(-x / np.sqrt(2.0))


def residualise(M: np.ndarray, G: np.ndarray, min_finite: int = 10):
    """Per item row: remove the least-squares intercept and slope on G over finite entries.

    Returns the residual matrix (NaN where M is NaN) and the (intercept, slope) per row.
    """

    out = np.full(M.shape, np.nan)
    coef = np.full((M.shape[0], 2), np.nan)
    for i, y in enumerate(M):
        f = np.isfinite(y) & np.isfinite(G)
        if f.sum() < min_finite:
            continue
        A = np.column_stack([np.ones(f.sum()), G[f]])
        beta, *_ = np.linalg.lstsq(A, y[f], rcond=None)
        coef[i] = beta
        out[i, f] = y[f] - A @ beta
    return out, coef


def robust_z(S: np.ndarray):
    """Per row robust z; also returns the row median and scaled MAD."""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN rows of unfitted items
        med = np.nanmedian(S, axis=1, keepdims=True)
        mad = np.nanmedian(np.abs(S - med), axis=1, keepdims=True) * 1.4826
    mad = np.maximum(mad, 1e-6)
    return (S - med) / mad, med[:, 0], mad[:, 0]


def selective_events(Y: np.ndarray, abs_gate: float | None, min_measured: int):
    """The selective-hit endpoint on a context x item matrix Y (lower = stronger effect).

    Returns (events, G). Unmeasured pairs are never events.
    """

    Y = np.asarray(Y, dtype=float)
    G = np.nanmedian(Y, axis=1)
    S, _ = residualise(Y.T, G)
    Z, _, _ = robust_z(S)
    measured = np.isfinite(Y.T).sum(1) >= min_measured
    with np.errstate(invalid="ignore"):
        ev = (Z <= Z_EVENT) & measured[:, None]
        if abs_gate is not None:
            ev &= Y.T <= abs_gate
    return ev.T & np.isfinite(Y), G


@dataclass
class BridgeState:
    """Belief about one context's factors: mean, covariance, items already measured."""

    m: np.ndarray
    S: np.ndarray
    observed: np.ndarray
    prior_source: str = "basal"


class BridgedTransferModel:
    """Low-rank Gaussian response model with a basal-expression prior; see the module docstring."""

    def __init__(self, rank: int = 20, n_pcs: int = 30, n_genes: int = 2000, abs_gate: float | None = None,
                 min_measured: int = 10, impute_iters: int = 15):
        if rank < 1:
            raise ValueError("rank must be positive")
        self.rank, self.n_pcs, self.n_genes = rank, n_pcs, n_genes
        self.abs_gate, self.min_measured = abs_gate, min_measured
        self.impute_iters = impute_iters

    # ---------- fitting on source contexts ----------
    def fit(self, Y: np.ndarray, X: np.ndarray) -> "BridgedTransferModel":
        Y = np.asarray(Y, dtype=float)
        X = np.asarray(X, dtype=float)
        n, D = Y.shape
        if X.shape[0] != n:
            raise TransferRefused(ITEM_AXIS_MISMATCH, f"{X.shape[0]} feature rows for {n} contexts")
        if n <= self.rank:
            raise TransferRefused(TOO_FEW_SOURCE_CONTEXTS, f"{n} source contexts for rank {self.rank}")
        finite = np.isfinite(Y)
        self.n_source = finite.sum(0)
        with np.errstate(invalid="ignore"):
            col = np.where(finite, Y, 0.0).sum(0) / np.maximum(self.n_source, 1)
        mu = np.where(self.n_source > 0, col, np.nan)
        mu = np.where(np.isfinite(mu), mu, np.nanmean(mu))
        self.mu = mu
        R = np.where(finite, Y - mu, 0.0)
        U, s, Vt = np.linalg.svd(R, full_matrices=False)
        r = min(self.rank, len(s))
        for _ in range(self.impute_iters):
            L = (U[:, :r] * s[:r]) @ Vt[:r]
            U, s, Vt = np.linalg.svd(np.where(finite, Y - mu, L), full_matrices=False)
        self.V = Vt[:r].T * s[:r] / np.sqrt(n)
        F = U[:, :r] * np.sqrt(n)
        resid = np.where(finite, Y - mu - F @ self.V.T, 0.0)
        s2 = np.where(self.n_source > 0, (resid ** 2).sum(0) / np.maximum(self.n_source, 1), np.nan)
        if self.impute_iters:
            n_i = self.n_source.astype(float)
            s2 = s2 * n_i / np.maximum(n_i - r, 1.0)
        floor = np.nanmedian(s2)
        self.s2 = np.where(np.isfinite(s2) & (s2 > 0), np.maximum(s2, 0.05 * floor), floor)
        self.F = F
        self.pop_cov = np.cov(F.T) + 1e-6 * np.eye(r)
        self._fit_prior(F, X)
        self._fit_thresholds(Y)
        self._source_Y = Y
        self.source_event_rate = self._event_rate(Y)
        self.measured_rate = (self.n_source + 0.5) / (n + 1.0)
        return self

    def _fit_prior(self, F, X):
        ok = np.isfinite(X).all(1)
        self.has_prior = ok.sum() >= 20
        if not self.has_prior:
            return
        Xs = X[ok]
        self.genes = np.argsort(-Xs.var(0))[: self.n_genes]
        Z = Xs[:, self.genes]
        self.x_mu, self.x_sd = Z.mean(0), Z.std(0) + 1e-6
        Z = (Z - self.x_mu) / self.x_sd
        _, _, Wt = np.linalg.svd(Z, full_matrices=False)
        self.W = Wt[: self.n_pcs].T
        P = Z @ self.W
        P1 = np.column_stack([np.ones(len(P)), P])
        Fo = F[ok]
        best = None
        for alpha in RIDGE_ALPHAS:
            A = P1.T @ P1 + alpha * np.diag([0.0] + [1.0] * P.shape[1])
            B = np.linalg.solve(A, P1.T @ Fo)
            H = np.einsum("ij,jk,ik->i", P1, np.linalg.inv(A), P1)
            loo = (Fo - P1 @ B) / (1 - H)[:, None]
            err = (loo ** 2).mean()
            if best is None or err < best[0]:
                best = (err, alpha, B, loo)
        _, self.alpha, self.B, loo = best
        self.prior_cov = np.cov(loo.T) + 1e-6 * np.eye(F.shape[1])

    def _residual_z(self, Y):
        G = np.nanmedian(Y, axis=1)
        S, coef = residualise(Y.T, G, min_finite=self.min_measured)
        Z, med, mad = robust_z(S)
        return Z, coef, med, mad

    def _fit_thresholds(self, Y):
        _, coef, med, mad = self._residual_z(Y)
        self.a, self.b = coef[:, 0], coef[:, 1]
        self.med, self.mad = med, mad
        self.threshold_ok = np.isfinite(self.a) & np.isfinite(self.b) & np.isfinite(med)

    def _events(self, Y):
        Z = self._residual_z(Y)[0]
        with np.errstate(invalid="ignore"):
            ev = Z <= Z_EVENT
            if self.abs_gate is not None:
                ev &= Y.T <= self.abs_gate
        return ev

    def _event_rate(self, Y):
        n = np.isfinite(Y.T).sum(1)
        return (self._events(Y).sum(1) + 0.1) / (n + 1.0)

    def source_events(self) -> np.ndarray:
        """Source-only events (context x item), as used by neighbour-based comparators."""

        return self._events(self._source_Y).T

    # ---------- a new context ----------
    def prior(self, x=None) -> BridgeState:
        r = self.V.shape[1]
        x = None if x is None else np.asarray(x, dtype=float)
        if self.has_prior and x is not None and np.isfinite(x).all():
            if x.shape[0] <= int(self.genes.max()):
                raise TransferRefused(ITEM_AXIS_MISMATCH, f"basal profile has {x.shape[0]} features")
            z = (x[self.genes] - self.x_mu) / self.x_sd
            p1 = np.concatenate([[1.0], z @ self.W])
            return BridgeState(p1 @ self.B, self.prior_cov.copy(), np.array([], dtype=int), "basal")
        return BridgeState(np.zeros(r), self.pop_cov.copy(), np.array([], dtype=int), "population")

    def posterior(self, st: BridgeState, idx, y) -> BridgeState:
        idx = np.asarray(idx, dtype=int)
        y = np.asarray(y, dtype=float)
        keep = np.isfinite(y)
        idx_f, y_f = idx[keep], y[keep]
        observed = np.concatenate([st.observed, idx])
        if len(idx_f) == 0:
            return BridgeState(st.m.copy(), st.S.copy(), observed, st.prior_source)
        Vr = self.V[idx_f]
        w = 1.0 / self.s2[idx_f]
        P0 = np.linalg.inv(st.S)
        S = np.linalg.inv(P0 + (Vr * w[:, None]).T @ Vr)
        m = S @ (P0 @ st.m + (Vr * w[:, None]).T @ (y_f - self.mu[idx_f]))
        return BridgeState(m, (S + S.T) / 2, observed, st.prior_source)

    def predict(self, st: BridgeState):
        mean = self.mu + self.V @ st.m
        var = np.einsum("dr,rs,ds->d", self.V, st.S, self.V) + self.s2
        return mean, var

    def thresholds(self, st: BridgeState) -> np.ndarray:
        mean, _ = self.predict(st)
        t = self.a + self.b * np.median(mean) + self.med + Z_EVENT * self.mad
        if self.abs_gate is not None:
            t = np.minimum(t, self.abs_gate)
        return np.where(self.threshold_ok, t, -np.inf)

    def event_prob(self, st: BridgeState) -> np.ndarray:
        mean, var = self.predict(st)
        return normal_cdf((self.thresholds(st) - mean) / np.sqrt(var))

    def expected_hit(self, st: BridgeState) -> np.ndarray:
        """Expected hits per well: source measurement rate x P(event | measured)."""

        return self.measured_rate * self.event_prob(st)

    def misfit(self, st0: BridgeState, idx, y) -> float:
        """Mean squared standardised residual of measured items under the pre-measurement predictive.

        About 1 when the transferred prior is right; NaN when no measured value is finite.
        """

        idx = np.asarray(idx, dtype=int)
        y = np.asarray(y, dtype=float)
        keep = np.isfinite(y)
        if keep.sum() == 0:
            return float("nan")
        mean, var = self.predict(st0)
        return float((((y[keep] - mean[idx[keep]]) ** 2) / var[idx[keep]]).mean())
