"""Development scorer: one fixed event, uncertainty in overall sensitivity, one terminal score.

File summary
- Path: research/feedback_attribution_20261017/coherent.py
- Purpose: a coherent alternative to `BridgedTransferModel.event_prob` for planning and selection.
  It is development code: nothing here is validated, and the promoted module is unchanged.
- The defect it addresses:
  - `BridgedTransferModel.thresholds` puts the predicted median response, ``median(mean)``, into
    the event threshold ``t_d = a_d + b_d * median(mean) + med_d - 3 * MAD_d`` and then scores
    ``Phi((t_d - mean_d) / sd(Y_d))``. The threshold moves with the prediction, but its
    uncertainty is ignored: the variance used is Var(Y_d), not Var(Y_d - b_d * G).
  - The score is therefore not a probability of one fixed event. Its expectation over
    future observations differs from its current value (`martingale_gap`), so planning can score
    terminal outcomes with a different event from the one used after a real readout.
- The coherent score:
  - Event H_d = {Y_d - a_d - b_d * G <= c_d}, with a_d, b_d, c_d = med_d - 3 * MAD_d fixed from
    source contexts (the same source-only fits the promoted model already makes).
  - Overall sensitivity G (the context's median response) is modelled on the factors:
    G = g0 + g'f + eta, with eta ~ N(0, s_eta^2), fitted by least squares of source G on the
    source factor scores.
  - Then Y_d - a_d - b_d * G is Gaussian with mean mu_d - a_d - b_d * g0 + (V_d - b_d * g)'m and
    variance (V_d - b_d * g)'S(V_d - b_d * g) + s2_d + b_d^2 * s_eta^2. This is the brief's
    Var(Y_d) + b_d^2 Var(G) - 2 b_d Cov(Y_d, G) under the low-rank model, with e_d and eta treated
    as independent (each item is about 1/100 of the median).
  - Because the event is fixed and the update is the same Gaussian posterior, the prior score
    equals the expected posterior score exactly (`martingale_gap` is zero up to Monte Carlo error).
  - ``q`` (any availability weight) multiplies the probability; it is supplied by the caller, so
    archive coverage and assay success are kept apart from the biological event.
- Also here:
  - `global_posterior`: the update restricted to overall sensitivity (attribution group E); only
    the scalar s = g'(f - m) is learned from the readouts.
  - `mc_event_prob`: a joint Monte Carlo reference for the exact endpoint (G = median over the
    items that are measured), used to check the linear-G approximation.
  - `derange`: a within-context permutation of returned readouts (attribution group F).
- Interfaces: `CoherentScorer`, `global_posterior`, `mc_event_prob`, `martingale_gap`, `derange`.
"""
from __future__ import annotations

import numpy as np

import common  # noqa: F401  (puts src on sys.path)
from virtual_cell.bridged_transfer import Z_EVENT, BridgedTransferModel, BridgeState, normal_cdf


class CoherentScorer:
    """Fixed-event, linear-G Gaussian event probability for a fitted `BridgedTransferModel`."""

    def __init__(self, model: BridgedTransferModel, Y_source: np.ndarray):
        Y_source = np.asarray(Y_source, dtype=float)
        G = np.nanmedian(Y_source, axis=1)
        F = model.F
        A = np.column_stack([np.ones(len(F)), F])
        ok = np.isfinite(G)
        beta, *_ = np.linalg.lstsq(A[ok], G[ok], rcond=None)
        resid = G[ok] - A[ok] @ beta
        self.g0, self.g = float(beta[0]), beta[1:]
        self.s_eta2 = float(resid @ resid / max(ok.sum() - A.shape[1], 1))
        self.model = model
        b = np.where(model.threshold_ok, model.b, 0.0)
        a = np.where(model.threshold_ok, model.a, 0.0)
        self.c = np.where(model.threshold_ok, model.med + Z_EVENT * model.mad, -np.inf)
        self.L = model.V - b[:, None] * self.g[None, :]
        self.offset = model.mu - a - b * self.g0
        self.noise = model.s2 + b ** 2 * self.s_eta2
        self.ok = model.threshold_ok

    def residual(self, st: BridgeState):
        mean = self.offset + self.L @ st.m
        var = np.einsum("dr,rs,ds->d", self.L, st.S, self.L) + self.noise
        return mean, var

    def event_prob(self, st: BridgeState) -> np.ndarray:
        mean, var = self.residual(st)
        p = normal_cdf((self.c - mean) / np.sqrt(var))
        return np.where(self.ok, p, 0.0)

    def predicted_G(self, st: BridgeState) -> tuple[float, float]:
        return float(self.g0 + self.g @ st.m), float(self.g @ st.S @ self.g + self.s_eta2)


def global_posterior(model: BridgedTransferModel, g: np.ndarray, st: BridgeState, idx, y) -> BridgeState:
    """Bayesian update of the factors through overall sensitivity only.

    s = g'(f - m) has prior N(0, g'Sg). The readouts are modelled with the rest of f (w, independent
    of s) integrated out under the prior, so they inform s alone. Missing readouts are skipped; with
    none returned the state is unchanged.
    """

    idx = np.asarray(idx, dtype=int)
    y = np.asarray(y, dtype=float)
    keep = np.isfinite(y)
    observed = np.concatenate([st.observed, idx])
    if keep.sum() == 0:
        return BridgeState(st.m.copy(), st.S.copy(), observed, st.prior_source)
    idx, y = idx[keep], y[keep]
    Sg = st.S @ g
    sig2 = float(g @ Sg)
    u = Sg / sig2
    Cw = st.S - np.outer(Sg, Sg) / sig2
    Vb = model.V[idx]
    a = Vb @ u
    R = Vb @ Cw @ Vb.T + np.diag(model.s2[idx])
    resid = y - model.mu[idx] - Vb @ st.m
    Ri_a = np.linalg.solve(R, a)
    prec = 1.0 / sig2 + a @ Ri_a
    s_var = 1.0 / prec
    s_mean = s_var * (Ri_a @ resid)
    S = Cw + np.outer(u, u) * s_var
    return BridgeState(st.m + u * s_mean, (S + S.T) / 2, observed, st.prior_source)


def mc_event_prob(model: BridgedTransferModel, st: BridgeState, draws: int, rng: np.random.Generator,
                  measured_rate=None) -> np.ndarray:
    """Joint Monte Carlo P(event) for the exact endpoint: G is the median over measured items.

    Which items are measured is drawn per draw with probability ``measured_rate`` (default: the
    model's source coverage), so G is the median the endpoint would actually compute.
    """

    q = model.measured_rate if measured_rate is None else np.asarray(measured_rate, float)
    r = len(st.m)
    Lc = np.linalg.cholesky(st.S + 1e-12 * np.eye(r))
    f = st.m + rng.standard_normal((draws, r)) @ Lc.T
    Y = model.mu + f @ model.V.T + rng.standard_normal((draws, len(model.mu))) * np.sqrt(model.s2)
    seen = rng.random(Y.shape) < q
    G = np.nanmedian(np.where(seen, Y, np.nan), axis=1)
    R = Y - model.a - model.b * G[:, None]
    c = model.med + Z_EVENT * model.mad
    with np.errstate(invalid="ignore"):
        ev = (R <= c) & model.threshold_ok
    return ev.mean(0)


def martingale_gap(model: BridgedTransferModel, score, st: BridgeState, idx, draws: int,
                   rng: np.random.Generator) -> np.ndarray:
    """E over prior-predictive readouts of score(posterior) minus score(prior), per item.

    ``score(state)`` returns a probability per item. For a fixed event and an exact update the gap
    is zero; readouts are drawn jointly from the model, all returned.
    """

    idx = np.asarray(idx, dtype=int)
    r = len(st.m)
    Lc = np.linalg.cholesky(st.S + 1e-12 * np.eye(r))
    p0 = score(st)
    acc = np.zeros_like(p0)
    for _ in range(draws):
        f = st.m + Lc @ rng.standard_normal(r)
        y = model.mu[idx] + model.V[idx] @ f + rng.standard_normal(len(idx)) * np.sqrt(model.s2[idx])
        acc += score(model.posterior(st, idx, y))
    return acc / draws - p0


def derange(y: np.ndarray, key_order: np.ndarray) -> np.ndarray:
    """Cyclically shift the returned (finite) readouts among their own positions.

    The positions keep their missingness, the number of returned readouts and the multiset of
    values; each returned value moves to a different item when at least two are returned.
    ``key_order`` fixes the cycle (a hashed order per item).
    """

    y = np.asarray(y, dtype=float).copy()
    pos = np.flatnonzero(np.isfinite(y))
    if len(pos) < 2:
        return y
    pos = pos[np.argsort(key_order[pos], kind="stable")]
    y[pos] = y[np.roll(pos, 1)]
    return y
