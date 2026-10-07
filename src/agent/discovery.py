"""Certified discovery loop: the agent buys batches, learns in context, and claims only what it may.

File summary
- Path: src/agent/discovery.py
- Purpose: run one budgeted discovery campaign in one context (e.g. a newly screened cell line)
  with a world model and any planner, and return typed claims whose basis is explicit.
- Core points:
  - The agent never sees a label it did not buy: `measure(indices)` is the only route to an
    outcome (a laboratory, or a replay of a measured screen).
  - Rounds 1..R-1 buy the planner's batch; a planner may be a world-model ranking or any black
    box with `choose` (an LLM, a human). The last round, by default, buys a uniformly random
    audit from the top kappa x batch of the world model's ranking, fixed before the draw, and
    certifies the untested remainder (`maestro.certification`).
  - Claims: MEASURED_HIT (a bought label above threshold), CERTIFIED_NOMINATION (FDR <= alpha,
    marginal), YIELD_BOUND (exact 1-delta lower bound on hits left in the shortlist) and
    REFUSAL with the certificate's code. A predicted label is never reported as a hit.
  - Laboratory cost (experiments, rounds) is reported by the caller's units; provider spend of
    an LLM planner is the planner's own ledger, never mixed in.
- Interfaces: `DiscoverySpec`, `WorldModelPlanner`, `Claim`, `DiscoveryReport`, `run_discovery`.
- Depends on: numpy, `maestro.certification`, `virtual_cell.combination_world`.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Protocol

import numpy as np

from maestro import certification
from virtual_cell.combination_world import CombinationWorld

MEASURED_HIT = "MEASURED_HIT"
CERTIFIED_NOMINATION = "CERTIFIED_NOMINATION"
YIELD_BOUND = "YIELD_BOUND"
REFUSAL = "REFUSAL"


@dataclass(frozen=True)
class DiscoverySpec:
    budget_fraction: float = 0.10
    rounds: int = 4
    kappa: int = 2
    alpha: float = 0.2
    delta: float = 0.1
    terminal: str = "certify"        # "certify" (registered design) or "exploit"

    def __post_init__(self) -> None:
        if self.terminal not in ("certify", "exploit"):
            raise ValueError("terminal must be 'certify' or 'exploit'")
        if type(self.rounds) is not int or type(self.kappa) is not int:
            raise ValueError("rounds and kappa must be integers")
        for name in ("budget_fraction", "alpha", "delta"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{name} must be finite and numeric")
        if not 0 < self.alpha < 1 or not 0 < self.delta < 1:
            raise ValueError("alpha and delta must lie in (0, 1)")
        if self.rounds < 2 or not 0 < self.budget_fraction <= 1 or self.kappa < 1:
            raise ValueError("need at least two rounds, a budget fraction in (0, 1] and kappa >= 1")


class Planner(Protocol):
    name: str

    def scores(self, measured: np.ndarray, values: np.ndarray) -> np.ndarray: ...


class WorldModelPlanner:
    """Buy the candidates the world model gives the highest probability of being a hit."""

    name = "world_model"

    def __init__(self, world: CombinationWorld):
        self.world = world

    def scores(self, measured: np.ndarray, values: np.ndarray) -> np.ndarray:
        mean, var = self.world.posterior(measured, values)
        return self.world.p_hit(mean, var)


@dataclass(frozen=True)
class Claim:
    kind: str
    candidate: int | None
    value: float | None
    basis: str


@dataclass
class DiscoveryReport:
    purchases: list[list[int]]
    labels: dict[int, float]
    claims: list[Claim]
    certificate: certification.Certificate | None
    budget: int
    planner: str
    notes: dict = field(default_factory=dict)

    @property
    def measured_hits(self) -> int:
        return sum(claim.kind == MEASURED_HIT for claim in self.claims)


def _top(scores: np.ndarray, available: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    scores = np.asarray(scores)
    if scores.shape != available.shape or scores.dtype.kind not in "iuf" or not np.isfinite(scores).all():
        raise ValueError("planner scores must be one finite numeric value per candidate")
    candidates = np.flatnonzero(available)
    order = np.lexsort((-rng.random(candidates.size), scores[candidates]))[::-1]
    return candidates[order[:k]]


def run_discovery(world: CombinationWorld, measure: Callable[[np.ndarray], np.ndarray], spec: DiscoverySpec,
                  *, planner=None, seed: int = 0) -> DiscoveryReport:
    """One campaign over the world's target-line candidates (indices 0..n-1)."""
    planner = planner or WorldModelPlanner(world)
    ranker = WorldModelPlanner(world)
    n = world.rows.size
    budget = int(math.ceil(spec.budget_fraction * n))
    batch = int(math.ceil(budget / spec.rounds))
    rng = np.random.default_rng(seed)
    measured = np.zeros(n, bool)
    labels: dict[int, float] = {}
    purchases: list[list[int]] = []

    def buy(indices: np.ndarray, limit: int) -> None:
        # Validate identities before conversion or calling a potentially paid measurement.
        indices = np.asarray(indices, dtype=object)
        if indices.ndim != 1 or any(isinstance(i, (bool, np.bool_)) or not isinstance(i, (int, np.integer))
                                    for i in indices):
            raise ValueError("planner indices must be a one-dimensional sequence of integers")
        if any(i < 0 or i >= n for i in indices):
            raise ValueError("planner candidate index out of range")
        if indices.size > min(limit, budget - measured.sum()):
            raise ValueError("planner purchase exceeds the round quota or remaining budget")
        indices = indices.astype(int)
        if indices.size == 0:
            return
        if measured[indices].any() or len(set(indices.tolist())) != indices.size:
            raise ValueError("a planner may not buy a candidate twice")
        values = np.asarray(measure(indices))
        if values.shape != indices.shape:
            raise ValueError("measure() must return one label per purchased candidate")
        if values.dtype.kind not in "iuf" or not np.isfinite(values).all():
            raise ValueError("measure() must return finite numeric labels")
        values = values.astype(float)
        measured[indices] = True
        labels.update(zip(indices.tolist(), values.tolist()))
        purchases.append(indices.tolist())

    def history() -> tuple[np.ndarray, np.ndarray]:
        idx = np.array(sorted(labels), int)
        return idx, np.array([labels[i] for i in idx.tolist()], float)

    choose = getattr(planner, "choose", None)
    for _ in range(spec.rounds - 1):
        k = int(min(batch, budget - measured.sum()))
        idx, vals = history()
        buy(choose(~measured, idx, vals, k) if choose else _top(planner.scores(idx, vals), ~measured, k, rng), k)
    last = int(budget - measured.sum())
    idx, vals = history()
    certificate = None
    if spec.terminal == "exploit":
        buy(choose(~measured, idx, vals, last) if choose else _top(planner.scores(idx, vals), ~measured, last, rng), last)
    else:
        scores = ranker.scores(idx, vals)                 # fixed before any audit label is seen
        shortlist = _top(scores, ~measured, spec.kappa * last, rng).tolist()
        audit, _ = certification.draw_audit(shortlist, last, random.Random(seed))
        buy(np.array(audit, int), last)
        certificate = certification.certify(
            shortlist, [scores[i] for i in shortlist], audit,
            [labels[i] > world.screen.threshold for i in audit], alpha=spec.alpha, delta=spec.delta)
    claims = [Claim(MEASURED_HIT, i, v, "measured label above threshold")
              for i, v in sorted(labels.items()) if v > world.screen.threshold]
    if certificate is not None:
        claims += [Claim(CERTIFIED_NOMINATION, int(i), None,
                         f"conformal selection, FDR <= {spec.alpha} (marginal), random audit of {len(certificate.audit)}")
                   for i in certificate.nominated]
        claims.append(Claim(YIELD_BOUND, None, float(certificate.yield_bound),
                            f">= this many hits remain among {len(certificate.remainder)} untested shortlisted, "
                            f"probability >= {1 - spec.delta}"))
        if certificate.refusal:
            claims.append(Claim(REFUSAL, None, None, certificate.refusal))
    return DiscoveryReport(purchases, labels, claims, certificate, budget, getattr(planner, "name", "planner"),
                           {"batch": batch, "rounds": spec.rounds, "terminal": spec.terminal})
