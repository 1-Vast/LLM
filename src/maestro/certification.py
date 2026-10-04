"""Design-based certificates for claims about candidates an agent has not measured.

File summary
- Path: src/maestro/certification.py
- Purpose: let any planner -- a fixed rule, a model-guided selector or a language model whose
  selection probabilities cannot be written down -- make lawful claims about the untested part
  of its own shortlist. A model ranking alone may never claim an unmeasured outcome; a ranking
  plus a randomised measured audit may make the two claims below.
- Core points:
  - Protocol: fix a shortlist and a score per member from data already measured; measure an
    audit drawn uniformly at random without replacement from the shortlist (`draw_audit`); then
    `certify`. Conditional on everything before the draw, audit and remainder are exchangeable,
    which is the only assumption either certificate needs.
  - Nominations: clipped-score conformal p-values and Benjamini-Hochberg give a subset of the
    remainder with FDR <= alpha (Jin and Candes, JMLR 2023; joint-exchangeability form, Gui,
    Jin, Nair and Ren 2025). The guarantee is marginal: it bounds the expected false-discovery
    proportion, not the error of one list.
  - Yield: an exact hypergeometric lower confidence bound on hits left in the remainder.
  - Refusals are named: AUDIT_TOO_SMALL, NO_CANDIDATE_PASSES (a valid empty selection),
    EMPTY_SHORTLIST, AUDIT_NOT_IN_SHORTLIST.
  - Verified on two real combination screens (research/certified_discovery, O'Neil 2016
    development and NCI-ALMANAC 2017 confirmatory); the research copy is frozen there.
- Interfaces: `draw_audit`, `minimum_audit`, `conformal_pvalues`, `benjamini_hochberg`,
  `yield_lower_bound`, `certify`, `Certificate`, refusal codes.
- Depends on: standard library only.
"""
from __future__ import annotations

import bisect
import math
import random
from dataclasses import dataclass, field
from typing import Hashable, Sequence

AUDIT_TOO_SMALL = "AUDIT_TOO_SMALL"
NO_CANDIDATE_PASSES = "NO_CANDIDATE_PASSES"
EMPTY_SHORTLIST = "EMPTY_SHORTLIST"
AUDIT_NOT_IN_SHORTLIST = "AUDIT_NOT_IN_SHORTLIST"


def draw_audit(shortlist: Sequence[Hashable], size: int, rng: random.Random) -> tuple[list, list]:
    """Uniformly random audit of `size` members and the untested remainder, both in shortlist order."""
    size = max(0, min(int(size), len(shortlist)))
    chosen = set(rng.sample(range(len(shortlist)), size))
    audit = [item for index, item in enumerate(shortlist) if index in chosen]
    remainder = [item for index, item in enumerate(shortlist) if index not in chosen]
    return audit, remainder


def minimum_audit(alpha: float) -> int:
    """Smallest audit for which a conformal p-value can reach alpha (1/(n+1) <= alpha)."""
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0, 1)")
    return int(math.ceil(1.0 / alpha - 1.0 - 1e-12))


def conformal_pvalues(audit_scores: Sequence[float], audit_hits: Sequence[bool],
                      test_scores: Sequence[float]) -> list[float]:
    """p_j = (1 + #{audit non-hits scoring at least t_j}) / (n + 1); higher score = likelier hit.

    Ties count against the candidate, which keeps the p-values valid without randomisation.
    """
    if len(audit_scores) != len(audit_hits):
        raise ValueError("audit scores and labels differ in length")
    nulls = sorted(float(s) for s, hit in zip(audit_scores, audit_hits) if not hit)
    denominator = len(audit_scores) + 1.0
    return [(1.0 + len(nulls) - bisect.bisect_left(nulls, float(t))) / denominator for t in test_scores]


def benjamini_hochberg(p_values: Sequence[float], alpha: float) -> list[bool]:
    """Membership of each hypothesis in the BH(alpha) rejection set."""
    m = len(p_values)
    order = sorted(range(m), key=lambda i: (p_values[i], i))
    cutoff = 0
    for rank, index in enumerate(order, start=1):
        if p_values[index] <= alpha * rank / m:
            cutoff = rank
    selected = [False] * m
    for index in order[:cutoff]:
        selected[index] = True
    return selected


def _log_choose(n: int, r: int) -> float:
    return math.lgamma(n + 1) - math.lgamma(r + 1) - math.lgamma(n - r + 1)


def _upper_tail(observed: int, population: int, successes: int, draws: int) -> float:
    """P(X >= observed) for X ~ Hypergeometric(population, successes, draws)."""
    low = max(observed, draws - (population - successes), 0)
    high = min(draws, successes)
    if low > high:
        return 0.0
    logs = [_log_choose(successes, k) + _log_choose(population - successes, draws - k) - _log_choose(population, draws)
            for k in range(low, high + 1)]
    peak = max(logs)
    return min(1.0, math.exp(peak) * sum(math.exp(value - peak) for value in logs))


def yield_lower_bound(population: int, draws: int, observed: int, delta: float) -> int:
    """1-delta lower confidence bound on hits among the population members NOT drawn."""
    if draws <= 0:
        return 0
    for successes in range(observed, population + 1):
        if _upper_tail(observed, population, successes, draws) > delta:
            return max(successes - observed, 0)
    return max(population - draws, 0)


@dataclass(frozen=True)
class Certificate:
    """What may be claimed about the untested remainder of a shortlist, and on what basis."""

    alpha: float
    delta: float
    shortlist: tuple
    audit: tuple
    audit_hits: tuple
    remainder: tuple
    nominated: tuple
    p_values: tuple
    yield_bound: int
    refusal: str | None = None
    basis: dict = field(default_factory=dict)

    def summary(self) -> dict:
        return {"alpha": self.alpha, "delta": self.delta, "shortlist": len(self.shortlist),
                "audit": len(self.audit), "audit_hits": int(sum(self.audit_hits)),
                "remainder": len(self.remainder), "nominated": len(self.nominated),
                "yield_bound": self.yield_bound, "refusal": self.refusal}


def certify(shortlist: Sequence[Hashable], scores: Sequence[float], audit: Sequence[Hashable],
            audit_hits: Sequence[bool], *, alpha: float, delta: float) -> Certificate:
    """Certify the untested remainder of `shortlist` from a measured uniformly random audit.

    `scores` align with `shortlist` and must have been fixed before any audit label was seen;
    `audit` must come from `draw_audit` (or an equivalent uniform draw) on the same shortlist.
    """
    shortlist, scores = tuple(shortlist), tuple(float(s) for s in scores)
    audit, audit_hits = tuple(audit), tuple(bool(h) for h in audit_hits)
    basis = {"design": "uniform audit without replacement from a fixed shortlist",
             "nominations": "conformal p-values + Benjamini-Hochberg (marginal FDR)",
             "yield": "exact hypergeometric lower bound"}
    if len(scores) != len(shortlist) or len(audit) != len(audit_hits):
        raise ValueError("scores must align with the shortlist and labels with the audit")
    if not shortlist:
        return Certificate(alpha, delta, (), audit, audit_hits, (), (), (), 0, EMPTY_SHORTLIST, basis)
    position = {item: index for index, item in enumerate(shortlist)}
    if len(position) != len(shortlist) or any(item not in position for item in audit) or len(set(audit)) != len(audit):
        return Certificate(alpha, delta, shortlist, audit, audit_hits, (), (), (), 0, AUDIT_NOT_IN_SHORTLIST, basis)
    in_audit = set(audit)
    remainder = tuple(item for item in shortlist if item not in in_audit)
    bound = yield_lower_bound(len(shortlist), len(audit), sum(audit_hits), delta)
    if len(audit) < minimum_audit(alpha):
        return Certificate(alpha, delta, shortlist, audit, audit_hits, remainder, (),
                           tuple(1.0 for _ in remainder), bound, AUDIT_TOO_SMALL, basis)
    p_values = conformal_pvalues([scores[position[item]] for item in audit], audit_hits,
                                 [scores[position[item]] for item in remainder])
    selected = benjamini_hochberg(p_values, alpha)
    nominated = tuple(item for item, keep in zip(remainder, selected) if keep)
    return Certificate(alpha, delta, shortlist, audit, audit_hits, remainder, nominated, tuple(p_values), bound,
                       None if nominated else NO_CANDIDATE_PASSES, basis)
