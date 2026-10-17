"""Research-agent core for context transfer: which few items to measure first, and when to repair.

File summary
- Path: research/context_transfer_20261017/agent.py
- Purpose: the bridge-selection rules and the verification/repair step that sit on top of the
  Virtual Cell (vc.ContextModel) in a new context with a fixed well budget.
- Core points:
  - Every rule spends `k_bridge` wells first, observes them, and then nominates the remaining
    `budget - k_bridge` items from the updated model. All measured wells count toward utility.
  - Scores are expected hits per well (source measurement rate x P(event)); information gains
    are weighted by the same rate, because a well on an unmeasured pair reveals nothing.
  - Rules: random, exploit (highest prior expected hit), fixed panel (population D-optimal, the same
    for every target in a fold), information (target-specific D-optimal on the context factors),
    and decision lookahead (one-step value of information for the final top-K decision, plus the
    bridged item's own hit chance), computed in closed form with Gauss-Hermite quadrature.
  - Verification: the bridge misfit (mean squared standardized residual under the prior). Repair:
    when misfit exceeds a frozen threshold, the prior covariance is inflated by the misfit before
    the update, so the bridge data dominate (an empirical-Bayes scale correction).
  - Alternative repair (development): Bayesian model averaging of the transferred prior and the
    population prior, weighted by the marginal likelihood of the bridge readouts.
- Interfaces: `choose_bridge(rule, model, state, k, budget, ...)`, `nominate(p, k, exclude, order)`,
  `repaired_prior(model, state, idx, y, threshold)`, `bma_expected_hit(model, states, idx, y)`.
"""
from __future__ import annotations

import numpy as np
from scipy.special import ndtr

from vc import State

GH_X, GH_W = np.polynomial.hermite_e.hermegauss(12)
GH_W = GH_W / GH_W.sum()


def nominate(score: np.ndarray, k: int, exclude, order: np.ndarray) -> np.ndarray:
    """Top-k items by score (higher better), excluding `exclude`; ties by the fixed `order`."""

    s = np.where(np.isfinite(score), score, -np.inf).astype(float).copy()
    s[np.asarray(exclude, dtype=int)] = -np.inf
    key = s + order * 1e-12
    return np.argsort(-key, kind="stable")[:k]


def _shrink(S, v, s2):
    Sv = S @ v
    return S - np.outer(Sv, Sv) / (v @ Sv + s2)


def info_gain(model, S, items):
    V = model.V[items]
    return np.einsum("dr,rs,ds->d", V, S, V) / model.s2[items]


def choose_bridge(rule: str, model, st: State, k: int, budget: int, order: np.ndarray,
                  panel=None, rng_order=None) -> np.ndarray:
    D = model.V.shape[0]
    exclude = list(st.observed)
    if k <= 0:
        return np.array([], dtype=int)
    if rule == "random":
        return nominate(rng_order, k, exclude, order)
    if rule == "exploit":
        return nominate(model.expected_hit(st), k, exclude, order)
    if rule == "panel":
        return np.asarray(panel[:k], dtype=int)
    if rule == "info":
        S = st.S.copy()
        picked = []
        allowed = np.ones(D, bool)
        allowed[exclude] = False
        for _ in range(k):
            g = info_gain(model, S, np.arange(D)) * model.measured_rate
            g[~allowed] = -np.inf
            j = int(np.argmax(g + order * 1e-12))
            picked.append(j)
            allowed[j] = False
            S = _shrink(S, model.V[j], model.s2[j])
        return np.array(picked)
    if rule == "lookahead":
        return _lookahead(model, st, k, budget, order)
    raise ValueError(rule)


def _lookahead(model, st: State, k: int, budget: int, order: np.ndarray) -> np.ndarray:
    """Greedy batch one-step value of information for the final top-K expected hits.

    Expected hits per well are q * P(event), with q the source measurement rate; a bridge item is
    observed (and informative) with probability q, otherwise it is a spent, empty well.
    """

    K = budget - k
    q = model.measured_rate
    mean, var = model.predict(st)
    t = model.thresholds(st)
    p = q * ndtr((t - mean) / np.sqrt(var))
    allowed = np.ones(len(p), bool)
    allowed[list(st.observed)] = False
    p_masked = np.where(allowed, p, -np.inf)
    n_dec = max(3 * K, 100)
    dec = np.argsort(-(p_masked + order * 1e-12))[:n_dec]
    by_p = np.argsort(-(p_masked + order * 1e-12))[:300]
    unc = info_gain(model, st.S, np.arange(len(p)))
    unc = np.where(allowed, unc, -np.inf)
    by_u = np.argsort(-(unc + order * 1e-12))[:300]
    cand = np.unique(np.concatenate([by_p, by_u]))
    S = st.S.copy()
    picked: list[int] = []
    Vd = model.V[dec]
    for _ in range(k):
        cand = np.array([c for c in cand if c not in picked])
        Vc = model.V[cand]
        cross = Vd @ S @ Vc.T                                    # dec x cand
        var_c = np.einsum("cr,rs,cs->c", Vc, S, Vc) + model.s2[cand]
        var_d = np.einsum("dr,rs,ds->d", Vd, S, Vd) + model.s2[dec]
        kappa = cross / np.sqrt(var_c)[None, :]                   # dec x cand
        resid_sd = np.sqrt(np.maximum(var_d[:, None] - kappa ** 2, 1e-9))
        # the final top-K excludes every item already in the bridge batch
        p_dec = np.where(np.isin(dec, picked), -np.inf, p[dec])
        ranked = np.sort(p_dec)[::-1]
        base = ranked[:K].sum()
        value = np.empty(len(cand))
        for j, c in enumerate(cand):
            # p'(xi) for every decision item, xi at Gauss-Hermite nodes
            z = (t[dec][:, None] - mean[dec][:, None] - kappa[:, j][:, None] * GH_X[None, :]) / resid_sd[:, j][:, None]
            pp = q[dec][:, None] * ndtr(z)
            same = dec == c
            pp[same] = -np.inf
            pp[np.isin(dec, picked)] = -np.inf
            top = -np.sort(-pp, axis=0)[:K]
            observed = (top.sum(0) * GH_W).sum()
            # unmeasured with probability 1 - q_c: the well is spent and c leaves the decision set
            in_top = same.any() and p[c] >= ranked[K - 1]
            unobserved = base - p[c] + ranked[K] if in_top else base
            value[j] = p[c] + q[c] * observed + (1 - q[c]) * unobserved - base
        j = int(np.argmax(value + order[cand] * 1e-12))
        c = int(cand[j])
        picked.append(c)
        S = _shrink(S, model.V[c], model.s2[c])
    return np.array(picked)


def fixed_panel(model, k: int, order: np.ndarray) -> np.ndarray:
    S = model.pop_cov.copy()
    D = model.V.shape[0]
    allowed = np.ones(D, bool)
    picked = []
    for _ in range(k):
        g = info_gain(model, S, np.arange(D)) * model.measured_rate
        g[~allowed] = -np.inf
        j = int(np.argmax(g + order * 1e-12))
        picked.append(j)
        allowed[j] = False
        S = _shrink(S, model.V[j], model.s2[j])
    return np.array(picked)


def repaired_prior(model, st0: State, idx, y, threshold: float):
    """Verification and repair: inflate the prior covariance when the bridge misfit is large."""

    mis = model.misfit(st0, idx, y)
    if np.isfinite(mis) and mis > threshold:
        return State(st0.m.copy(), st0.S * mis, st0.observed.copy()), mis, True
    return st0, mis, False


def bma_expected_hit(model, states, idx, y):
    """Verification by Bayesian model averaging over candidate priors for the context factors.

    Each prior (e.g. the basal-expression transfer and the population prior) is updated on the
    bridge readouts; its weight is the marginal likelihood of those readouts under that prior,
    with equal prior odds. Returns (expected hits per well, weights). With no finite readout the
    first prior keeps all the weight.
    """

    idx = np.asarray(idx, dtype=int)
    y = np.asarray(y, dtype=float)
    keep = np.isfinite(y)
    logml, hits = [], []
    for st in states:
        post = model.posterior(st, idx, y)
        hits.append(model.expected_hit(post))
        if keep.sum() == 0:
            logml.append(0.0)
            continue
        Vb = model.V[idx[keep]]
        C = Vb @ st.S @ Vb.T + np.diag(model.s2[idx[keep]])
        r = y[keep] - model.mu[idx[keep]] - Vb @ st.m
        sign, logdet = np.linalg.slogdet(C)
        logml.append(float(-0.5 * (logdet + r @ np.linalg.solve(C, r))))
    if keep.sum() == 0:
        w = np.zeros(len(states))
        w[0] = 1.0
    else:
        a = np.array(logml)
        w = np.exp(a - a.max())
        w /= w.sum()
    return sum(wi * hi for wi, hi in zip(w, hits)), w

