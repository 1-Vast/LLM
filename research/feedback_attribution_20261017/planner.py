"""Development reference planner: is an intermediate experiment worth running, and how large?

File summary
- Path: research/feedback_attribution_20261017/planner.py
- Purpose: a small joint-Monte-Carlo reference for the two-stage design value, written to be
  checked before it is optimised. It keeps the promoted low-rank model and its posterior update and
  uses one terminal score for the prior, the fantasies and the real posterior.
- The objective, for evidence D, total budget W and a first-round set B of size k:
  - Q(B) = E[U(B) | D] + E_{O_B | D}[ max_{|S| <= W-k, S outside B} E[U(S) | D, O_B] ] - C_extra(B);
  - against the best one-shot set of W items: Delta(B) = Q(B) - Q(none) = EVSI(B) - OC(B) - C_extra(B).
    - EVSI(B) = E_O[max_S E[U(S) | D, O]] - max_S E[U(S) | D], with S of size W-k outside B;
    - OC(B) = max_{|S|=W} E[U(S) | D] - E[U(B) | D] - max_{|S|=W-k, outside B} E[U(S) | D], the
      expected hits given up by spending k queries on B;
    - C_extra(B) = ``round_cost`` if k > 0, in hits per context (a declared value, not a price).
  - U is additive expected hits, so the inner max is the top W-k of the posterior scores.
- Fantasies: each draw samples the context's factors, all readouts of B and, independently, whether
  each readout returns (probability ``q``). The posterior uses only returned readouts, so a draw
  with nothing returned leaves the state, and every later score, unchanged.
- Candidates: for each k in ``k_options`` the first round is the top k by the current score
  (exploit-first). k = 0 (no intermediate experiment) is always compared. Common random numbers
  are shared across k.
- This is a reference implementation of the decision value under the model. It does not show that
  the model is right; its terms are only as good as the scorer's probabilities.
- Interfaces: `design_values`, `choose_design`, `DesignValue`.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import common  # noqa: F401
from agent.bridge_design import nominate
from virtual_cell.bridged_transfer import BridgedTransferModel, BridgeState


@dataclass
class DesignValue:
    k: int
    bridge: np.ndarray
    direct: float
    opportunity_cost: float
    evsi: float
    evsi_se: float
    round_cost: float
    delta: float
    returned_share: float


def _top_sum(score: np.ndarray, n: int, exclude) -> float:
    if n <= 0:
        return 0.0
    s = np.asarray(score, float).copy()
    s[np.asarray(exclude, dtype=int)] = -np.inf
    s = np.sort(s[np.isfinite(s)])[::-1][:n]
    return float(s.sum())


def design_values(model: BridgedTransferModel, prob, st0: BridgeState, q: np.ndarray, budget: int,
                  k_options, order: np.ndarray, draws: int, rng: np.random.Generator,
                  round_cost: float = 0.0, menu=None) -> list[DesignValue]:
    """Value terms of every candidate first-round size, k = 0 included.

    ``prob(state)`` is the event probability per item (the terminal score is ``q * prob``);
    ``menu`` (optional boolean mask) restricts every choice to feasible items.
    """

    q = np.asarray(q, float)
    D = len(q)
    banned = np.array(list(st0.observed) + ([] if menu is None else np.flatnonzero(~menu).tolist()), dtype=int)

    def score(st):
        return q * prob(st)

    p0 = score(st0)
    one_shot = _top_sum(p0, budget, banned)
    out = [DesignValue(0, np.array([], int), one_shot, 0.0, 0.0, 0.0, 0.0, 0.0, float("nan"))]
    r = len(st0.m)
    Lc = np.linalg.cholesky(st0.S + 1e-12 * np.eye(r))
    f = st0.m + rng.standard_normal((draws, r)) @ Lc.T
    noise = rng.standard_normal((draws, D))
    ret = rng.random((draws, D))
    s0 = np.where(np.isin(np.arange(D), banned), -np.inf, p0)
    for k in k_options:
        if k <= 0 or k >= budget:
            continue
        B = nominate(s0, k, banned, order)
        B = B[np.isfinite(s0[B])]
        if len(B) < k:
            continue
        direct = float(p0[B].sum())
        rest0 = _top_sum(p0, budget - k, np.concatenate([banned, B]))
        oc = one_shot - direct - rest0
        vals = np.empty(draws)
        returned = 0
        for i in range(draws):
            y = model.mu[B] + model.V[B] @ f[i] + noise[i, B] * np.sqrt(model.s2[B])
            back = ret[i, B] < q[B]
            returned += int(back.sum())
            y = np.where(back, y, np.nan)
            st1 = model.posterior(st0, B, y)
            vals[i] = _top_sum(score(st1), budget - k, np.concatenate([banned, B])) - rest0
        evsi = float(vals.mean())
        se = float(vals.std(ddof=1) / np.sqrt(draws)) if draws > 1 else float("inf")
        out.append(DesignValue(int(k), B, direct, float(oc), evsi, se, float(round_cost),
                               float(evsi - oc - round_cost), returned / (draws * k)))
    return out


def choose_design(values: list[DesignValue]) -> DesignValue:
    """The largest Delta; k = 0 unless some k > 0 has Delta > 0. Ties go to the smaller k."""

    best = values[0]
    for v in values[1:]:
        if v.delta > best.delta + 1e-12:
            best = v
    return best
