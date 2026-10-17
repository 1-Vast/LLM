"""Bridge design: which few wells to measure first in a new context, then what to nominate.

File summary
- Path: src/agent/bridge_design.py
- Purpose: the agent's experimental-design layer on top of the bridged-transfer Virtual Cell
  (`virtual_cell.bridged_transfer.BridgedTransferModel`), for a fixed well budget in one new context.
- Core points:
  - A bridged campaign spends ``k_bridge`` wells first and observes them. It then nominates the
    remaining ``budget - k_bridge`` items from the updated model.
    - Every well counts toward utility.
    - A well on an unmeasured pair is spent and reveals nothing.
    - A bridge costs one extra assay round.
  - Bridge rules:
    - ``random``: hash-ordered random items.
    - ``exploit``: the items with the highest prior expected hits.
    - ``panel``: the population D-optimal panel, the same for every context.
    - ``info``: target-specific D-optimal on the context factors.
    - ``lookahead``: the one-step value of information for the final top-K expected hits, plus the
      bridged item's own hit chance. It is computed in closed form by Gauss-Hermite quadrature,
      with the baseline re-scored at every greedy step (see `_lookahead`).
    - ``lookahead_v1``: the same rule as frozen in the source study, with the prior baseline kept
      after the first pick. It is kept for audit and reproduction only.
  - In ``info``, ``panel`` and ``lookahead``, an item's information is weighted by its
    measurement rate.
  - Verification: the bridge misfit (`BridgedTransferModel.misfit`) is reported, not acted on.
    Covariance-inflation repair and model averaging were tested in the source study and are
    not part of this module (one was harmful, the other neutral).
- Interfaces: `nominate`, `info_gain`, `choose_bridge`, `fixed_panel`, `run_campaign`,
  `Campaign`, `BRIDGE_RULES`.
- Depends on: numpy and `virtual_cell.bridged_transfer`.

Scope of the evidence: 2026-10-17, ``research/context_transfer_20261017``. One-shot Beat AML 2.0
confirmation at 16 wells with a 4-well bridge; the domain is described in
`virtual_cell.bridged_transfer`.
- ``exploit``:
  - +0.073 hits per sample over no bridge [+0.025, +0.127]. This is the confirmed rule.
  - Its four bridge wells are the prior's own top four, so the gain is the value of re-ranking
    the other twelve wells after four readouts.
  - Readouts from another patient instead lose 0.104 hits.
- ``lookahead_v1`` (frozen):
  - −0.035 [−0.070, −0.002] against no bridge and −0.108 [−0.172, −0.051] against exploit.
  - Only 29% of its bridge wells returned a readout (exploit: 88%).
  - On PRISM 19Q4 development it had been the best bridge rule by point estimate.
- ``lookahead`` (corrected), post hoc on exposed data, not confirmatory:
  - The loss above is the baseline defect described in `_lookahead`, not the
    value-of-information design.
  - On Beat AML the corrected rule ties exploit: 0.850 against 0.850 hits, difference 0.000
    [−0.061, +0.064], with 89% of bridge wells measured.
  - On PRISM 19Q4 (32 wells, k 8, rank 40), where q is about 0.975 for every item, the correction
    is neutral against ``lookahead_v1``: +0.025 [−0.016, +0.064] (line holdout) and −0.046
    [−0.104, +0.003] (lineage holdout).
  - Neither version beat exploit there with an interval excluding zero (development lookahead
    − exploit: +0.04 to +0.12 hits per line).
- ``info``, ``panel`` and ``random`` bridges were below no bridge on Beat AML (descriptive).
- Not validated:
  - the corrected ``lookahead`` (no fresh confirmation);
  - other budgets or bridge sizes;
  - prospective plating, where every chosen item can be measured.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from virtual_cell.bridged_transfer import BridgedTransferModel, BridgeState, normal_cdf

BRIDGE_RULES = ("random", "exploit", "panel", "info", "lookahead", "lookahead_v1")
GH_X, GH_W = np.polynomial.hermite_e.hermegauss(12)
GH_W = GH_W / GH_W.sum()
LOOKAHEAD_SHORTLIST = 300


def nominate(score: np.ndarray, k: int, exclude, order: np.ndarray) -> np.ndarray:
    """Top-k items by score (higher is better), excluding ``exclude``; ties by the fixed ``order``."""

    s = np.where(np.isfinite(score), score, -np.inf).astype(float).copy()
    s[np.asarray(exclude, dtype=int)] = -np.inf
    return np.argsort(-(s + order * 1e-12), kind="stable")[:k]


def _shrink(S, v, s2):
    Sv = S @ v
    return S - np.outer(Sv, Sv) / (v @ Sv + s2)


def info_gain(model: BridgedTransferModel, S: np.ndarray, items) -> np.ndarray:
    V = model.V[items]
    return np.einsum("dr,rs,ds->d", V, S, V) / model.s2[items]


def fixed_panel(model: BridgedTransferModel, k: int, order: np.ndarray) -> np.ndarray:
    """Population D-optimal panel of ``k`` items (greedy, rate-weighted)."""

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
    return np.array(picked, dtype=int)


def choose_bridge(rule: str, model: BridgedTransferModel, st: BridgeState, k: int, budget: int,
                  order: np.ndarray, panel=None, rng_order=None) -> np.ndarray:
    if rule not in BRIDGE_RULES:
        raise ValueError(f"unknown bridge rule {rule!r}")
    if k <= 0:
        return np.array([], dtype=int)
    if not 0 < k < budget:
        raise ValueError("k_bridge must be smaller than the budget")
    exclude = list(st.observed)
    if rule == "random":
        if rng_order is None:
            raise ValueError("the random rule needs rng_order")
        return nominate(rng_order, k, exclude, order)
    if rule == "exploit":
        return nominate(model.expected_hit(st), k, exclude, order)
    if rule == "panel":
        panel = fixed_panel(model, k, order) if panel is None else panel
        return np.asarray(panel[:k], dtype=int)
    if rule == "info":
        D = model.V.shape[0]
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
        return np.array(picked, dtype=int)
    return _lookahead(model, st, k, budget, order, rebase=rule == "lookahead")


def _lookahead(model: BridgedTransferModel, st: BridgeState, k: int, budget: int, order: np.ndarray,
               rebase: bool = True) -> np.ndarray:
    """Greedy batch one-step value of information for the final top-K expected hits.

    A bridge item is observed (and informative) with probability q, its measurement rate;
    otherwise its well is spent and it leaves the decision set.

    After the first pick the covariance is shrunk for the items already in the batch while the
    mean is held (a kriging-believer step). With ``rebase=True`` the decision items' hit chances
    and the baseline are re-scored under that shrunk covariance at every step, so a candidate's
    value is its own hit chance plus a non-negative value of information. ``rebase=False`` is the
    ``lookahead_v1`` rule frozen in ``research/context_transfer_20261017``: it keeps the prior hit
    chances as the baseline. The model's own expectation under the shrunk covariance then falls
    below that baseline, so every measured candidate after the first carries a negative bias of
    about the same size. Multiplied by the measurement rate q, the bias favours items that are
    rarely measured. The corrected rule also clips the value of information at zero (it is
    non-negative in theory, so a negative estimate is quadrature noise) and breaks exact ties
    toward the well more likely to return a readout. The two rules can differ at the first pick
    only where the value of information is within that noise of zero.
    """

    K = budget - k
    q = model.measured_rate
    mean, var = model.predict(st)
    t = model.thresholds(st)
    p = q * normal_cdf((t - mean) / np.sqrt(var))
    allowed = np.ones(len(p), bool)
    allowed[list(st.observed)] = False
    p_masked = np.where(allowed, p, -np.inf)
    by_p_all = np.argsort(-(p_masked + order * 1e-12))
    dec = by_p_all[:max(3 * K, 100)]
    by_p = by_p_all[:LOOKAHEAD_SHORTLIST]
    unc = np.where(allowed, info_gain(model, st.S, np.arange(len(p))), -np.inf)
    by_u = np.argsort(-(unc + order * 1e-12))[:LOOKAHEAD_SHORTLIST]
    cand = np.unique(np.concatenate([by_p, by_u]))
    S = st.S.copy()
    picked: list[int] = []
    Vd = model.V[dec]
    for _ in range(k):
        cand = np.array([c for c in cand if c not in picked])
        Vc = model.V[cand]
        cross = Vd @ S @ Vc.T
        var_c = np.einsum("cr,rs,cs->c", Vc, S, Vc) + model.s2[cand]
        var_d = np.einsum("dr,rs,ds->d", Vd, S, Vd) + model.s2[dec]
        kappa = cross / np.sqrt(var_c)[None, :]
        resid_sd = np.sqrt(np.maximum(var_d[:, None] - kappa ** 2, 1e-9))
        in_batch = np.isin(dec, picked)
        p_dec = q[dec] * normal_cdf((t[dec] - mean[dec]) / np.sqrt(var_d)) if rebase else p[dec]
        ranked = np.sort(np.where(in_batch, -np.inf, p_dec))[::-1]
        base = ranked[:K].sum()
        value = np.empty(len(cand))
        for j, c in enumerate(cand):
            z = (t[dec][:, None] - mean[dec][:, None] - kappa[:, j][:, None] * GH_X[None, :]) / resid_sd[:, j][:, None]
            pp = q[dec][:, None] * normal_cdf(z)
            same = dec == c
            pp[same] = -np.inf
            pp[in_batch] = -np.inf
            observed = (-np.sort(-pp, axis=0)[:K].sum(0) * GH_W).sum()
            in_top = same.any() and p_dec[same][0] >= ranked[K - 1]
            unobserved = base - p_dec[same][0] + ranked[K] if in_top else base
            if rebase:
                # the value of information is non-negative in theory; clipping removes quadrature
                # noise, and a tie goes to the well that can return a readout
                gain = max(observed - unobserved, 0.0)
                value[j] = p[c] + (unobserved - base) + q[c] * gain + 1e-9 * q[c]
            else:
                value[j] = p[c] + q[c] * observed + (1 - q[c]) * unobserved - base
        c = int(cand[int(np.argmax(value + order[cand] * 1e-12))])
        picked.append(c)
        S = _shrink(S, model.V[c], model.s2[c])
    return np.array(picked, dtype=int)


@dataclass
class Campaign:
    """One context's campaign: every well, the bridge, the misfit and the assay rounds."""

    wells: np.ndarray
    bridge: np.ndarray
    values: np.ndarray
    misfit: float
    rounds: int
    wasted: int
    prior_source: str


def run_campaign(model: BridgedTransferModel, x, measure: Callable[[np.ndarray], np.ndarray], budget: int,
                 k_bridge: int, rule: str | None, order: np.ndarray, panel=None, rng_order=None) -> Campaign:
    """Run one equal-well campaign in a new context.

    ``measure(items)`` is the assay: it returns one value per item, NaN when the pair was not
    measured. ``rule=None`` (or ``k_bridge=0``) is the no-bridge Virtual Cell campaign: one round,
    all wells nominated from the prior.
    """

    st0 = model.prior(x)
    if rule is None or k_bridge == 0:
        wells = nominate(model.expected_hit(st0), budget, [], order)
        values = np.asarray(measure(wells), dtype=float)
        return Campaign(wells, np.array([], dtype=int), values, float("nan"), 1,
                        int((~np.isfinite(values)).sum()), st0.prior_source)
    bridge = choose_bridge(rule, model, st0, k_bridge, budget, order, panel=panel, rng_order=rng_order)
    yb = np.asarray(measure(bridge), dtype=float)
    st1 = model.posterior(st0, bridge, yb)
    final = nominate(model.expected_hit(st1), budget - k_bridge, bridge, order)
    yf = np.asarray(measure(final), dtype=float)
    values = np.concatenate([yb, yf])
    return Campaign(np.concatenate([bridge, final]), bridge, values, model.misfit(st0, bridge, yb), 2,
                    int((~np.isfinite(values)).sum()), st0.prior_source)
