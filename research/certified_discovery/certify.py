"""Design-based certification of discoveries nominated after adaptive (black-box) acquisition.

File summary
- Path: research/certified_discovery/certify.py
- Purpose: turn a model's ranking of UNMEASURED candidates into claims with finite-sample error
  control, whatever policy chose the earlier measurements and however miscalibrated the model is.
- Core points:
  - The agent fixes a shortlist S and a score for each member using only data it already has.
    It then measures an audit A drawn uniformly at random without replacement from S, with
    randomness independent of every label in S. Conditional on everything before the draw, the
    audit and the rest of S are exchangeable, which is all the two certificates below need.
    Selection probabilities of the earlier policy (an LLM, a GP, a human) never enter.
  - `conformal_select`: conformal p-values with the clipped score of Jin and Candes (JMLR 2023)
    and Benjamini-Hochberg give a nominated subset of S without A with FDR <= alpha
    (joint-exchangeability form: Gui, Jin, Nair and Ren 2025, Assumption 1).
  - `yield_lower_bound`: an exact hypergeometric lower confidence bound on the number of hits
    still in S without A (finite-population sampling; no model assumption).
  - Every empty result names its reason: AUDIT_TOO_SMALL (no p-value can reach alpha even if
    every audit member were a hit), NO_CANDIDATE_PASSES (a valid, empty selection),
    EMPTY_SHORTLIST.
- Interfaces: `draw_audit`, `conformal_pvalues`, `benjamini_hochberg`, `conformal_select`,
  `yield_lower_bound`, `certify`, `Certificate`.
- Depends on: numpy and the standard library (math.lgamma for the hypergeometric tail).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

AUDIT_TOO_SMALL = "AUDIT_TOO_SMALL"
NO_CANDIDATE_PASSES = "NO_CANDIDATE_PASSES"
EMPTY_SHORTLIST = "EMPTY_SHORTLIST"


def draw_audit(shortlist: np.ndarray, size: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Split a fixed shortlist into a uniformly random audit and the untested remainder."""
    shortlist = np.asarray(shortlist)
    size = int(min(max(size, 0), shortlist.size))
    order = rng.permutation(shortlist.size)
    return shortlist[order[:size]], shortlist[order[size:]]


def minimum_audit(alpha: float) -> int:
    """Smallest audit for which a conformal p-value can reach alpha (1/(n+1) <= alpha)."""
    return int(math.ceil(1.0 / alpha - 1.0 - 1e-12))


def conformal_pvalues(audit_scores, audit_hits, test_scores) -> np.ndarray:
    """p_j = (1 + #{audit nulls scoring at least t_j}) / (n + 1).

    Clipped-score conformal p-values (Jin and Candes 2023, eq. 7) with ties counted against the
    candidate, which keeps them valid without randomisation. Higher score = more likely a hit.
    """
    audit_scores = np.asarray(audit_scores, float)
    audit_hits = np.asarray(audit_hits, bool)
    test_scores = np.asarray(test_scores, float)
    null_scores = np.sort(audit_scores[~audit_hits])
    at_least = null_scores.size - np.searchsorted(null_scores, test_scores, side="left")
    return (1.0 + at_least) / (audit_scores.size + 1.0)


def benjamini_hochberg(p_values: np.ndarray, alpha: float) -> np.ndarray:
    """Boolean mask of the BH(alpha) rejection set."""
    p_values = np.asarray(p_values, float)
    m = p_values.size
    if m == 0:
        return np.zeros(0, bool)
    order = np.argsort(p_values, kind="stable")
    passing = np.flatnonzero(p_values[order] <= alpha * np.arange(1, m + 1) / m)
    mask = np.zeros(m, bool)
    if passing.size:
        mask[order[: passing[-1] + 1]] = True
    return mask


def conformal_select(audit_scores, audit_hits, test_scores, alpha: float) -> tuple[np.ndarray, np.ndarray]:
    p_values = conformal_pvalues(audit_scores, audit_hits, test_scores)
    return benjamini_hochberg(p_values, alpha), p_values


def _log_hypergeom_pmf(k: int, population: int, successes: int, draws: int) -> float:
    def log_choose(n: int, r: int) -> float:
        return math.lgamma(n + 1) - math.lgamma(r + 1) - math.lgamma(n - r + 1)

    return log_choose(successes, k) + log_choose(population - successes, draws - k) - log_choose(population, draws)


def _upper_tail(observed: int, population: int, successes: int, draws: int) -> float:
    """P(X >= observed) for X ~ Hypergeometric(population, successes, draws)."""
    lo = max(observed, draws - (population - successes), 0)
    hi = min(draws, successes)
    if lo > hi:
        return 0.0
    logs = [_log_hypergeom_pmf(k, population, successes, draws) for k in range(lo, hi + 1)]
    peak = max(logs)
    return float(min(1.0, math.exp(peak) * sum(math.exp(v - peak) for v in logs)))


def yield_lower_bound(population: int, draws: int, observed: int, delta: float) -> int:
    """1-delta lower confidence bound on hits among the population members NOT drawn.

    K_L = min{K : P(X >= observed | K) > delta}; the untested remainder holds at least
    K_L - observed hits with probability at least 1 - delta (exact, finite population).
    """
    if draws <= 0:
        return 0
    for successes in range(observed, population + 1):
        if _upper_tail(observed, population, successes, draws) > delta:
            return max(successes - observed, 0)
    return max(population - draws, 0)


@dataclass(frozen=True)
class Certificate:
    """What the agent may claim about the untested part of its shortlist, and why."""

    alpha: float
    delta: float
    shortlist: np.ndarray
    audit: np.ndarray
    audit_hits: np.ndarray
    remainder: np.ndarray
    nominated: np.ndarray
    p_values: np.ndarray
    yield_bound: int
    refusal: str | None = None
    notes: dict = field(default_factory=dict)

    def summary(self) -> dict:
        return {"alpha": self.alpha, "delta": self.delta, "shortlist": int(self.shortlist.size),
                "audit": int(self.audit.size), "audit_hits": int(self.audit_hits.sum()),
                "remainder": int(self.remainder.size), "nominated": int(self.nominated.size),
                "yield_bound": int(self.yield_bound), "refusal": self.refusal}


def certify(shortlist, scores, audit, audit_hits, *, alpha: float, delta: float) -> Certificate:
    """Certify the untested remainder of `shortlist` given a measured random audit.

    `scores` are indexed like `shortlist` and must have been fixed before the audit labels were
    seen. `audit` must be a uniformly random subset of `shortlist` (see `draw_audit`).
    """
    shortlist = np.asarray(shortlist)
    scores = np.asarray(scores, float)
    audit = np.asarray(audit)
    audit_hits = np.asarray(audit_hits, bool)
    if shortlist.size == 0:
        empty = np.zeros(0, shortlist.dtype)
        return Certificate(alpha, delta, shortlist, audit, audit_hits, empty, empty, np.zeros(0), 0, EMPTY_SHORTLIST)
    position = {item: i for i, item in enumerate(shortlist.tolist())}
    if any(item not in position for item in audit.tolist()):
        raise ValueError("audit members must come from the shortlist")
    in_audit = np.zeros(shortlist.size, bool)
    in_audit[[position[item] for item in audit.tolist()]] = True
    remainder = shortlist[~in_audit]
    bound = yield_lower_bound(shortlist.size, audit.size, int(audit_hits.sum()), delta)
    if audit.size < minimum_audit(alpha):
        return Certificate(alpha, delta, shortlist, audit, audit_hits, remainder, remainder[:0],
                           np.ones(remainder.size), bound, AUDIT_TOO_SMALL)
    # Audit scores follow the order of `audit`, the order in which its labels arrive.
    audit_scores = scores[[position[item] for item in audit.tolist()]]
    selected, p_values = conformal_select(audit_scores, audit_hits, scores[~in_audit], alpha)
    nominated = remainder[selected]
    return Certificate(alpha, delta, shortlist, audit, audit_hits, remainder, nominated, p_values, bound,
                       None if nominated.size else NO_CANDIDATE_PASSES)
