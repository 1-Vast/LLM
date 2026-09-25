"""Auditable budgeted selection of a small evidence-action set under a declared cost cap.

File summary
- Path: src/maestro/selection.py
- Purpose: Choose a minimal-cost set cover over executable actions within a fixed budget.
- Core points:
  - Exhaustive small-set cover; unmet prerequisites stay explicit rather than hidden.
  - Order of comparison: coverage, then cost, then set size, then declared prediction priority.
    A prediction can only break a tie between otherwise equivalent plans; it can never buy an
    extra action or a more expensive plan.
  - `select` raises on a negative budget or a candidate pool above the 16-action cap.
- Interfaces: `BudgetedEvidencePlan`, `BudgetedEvidenceSelector`, `select`
- Depends on: maestro.models
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Mapping, Sequence

from .models import EvidenceAction, FunctionalInterventionProfile


@dataclass(frozen=True)
class BudgetedEvidencePlan:
    """Current executable actions only; unmet prerequisites remain explicit."""

    actions: tuple[EvidenceAction, ...]
    covered: frozenset[str]
    uncovered: frozenset[str]
    total_cost: float
    waiting_for_prerequisites: tuple[str, ...]
    rejection_reasons: Mapping[str, str] = field(default_factory=dict)


class BudgetedEvidenceSelector:
    """Choose an exact small-set cover without claiming global research utility."""

    def __init__(self, *, maximum_candidates: int = 16):
        self._maximum_candidates = maximum_candidates

    def select(
        self,
        required: frozenset[str],
        actions: Sequence[EvidenceAction],
        profile: FunctionalInterventionProfile,
        budget: float,
        *,
        weights: Mapping[str, float] | None = None,
        action_priorities: Mapping[str, float] | None = None,
    ) -> BudgetedEvidencePlan:
        if budget < 0:
            raise ValueError("Budget must be nonnegative.")
        if not required:
            return BudgetedEvidencePlan((), frozenset(), frozenset(), 0.0, ())
        executable, waiting = self._partition(actions, profile)
        if len(executable) > self._maximum_candidates:
            raise ValueError(
                f"Candidate pool has {len(executable)} actions; maximum is {self._maximum_candidates}."
            )
        weighted = weights or {}
        priorities = action_priorities or {}
        best: tuple[EvidenceAction, ...] = ()
        best_covered: frozenset[str] = frozenset()
        best_cost = 0.0
        for size in range(1, len(executable) + 1):
            for candidate in combinations(executable, size):
                cost = sum(action.cost for action in candidate)
                if cost > budget:
                    continue
                covered = frozenset().union(*(set(action.distinguishes) for action in candidate)) & required
                if self._is_better(candidate, covered, cost, best, best_covered, best_cost, weighted, priorities):
                    best, best_covered, best_cost = candidate, covered, cost
        return BudgetedEvidencePlan(
            actions=best,
            covered=best_covered,
            uncovered=required - best_covered,
            total_cost=best_cost,
            waiting_for_prerequisites=waiting,
        )

    @staticmethod
    def _partition(
        actions: Sequence[EvidenceAction], profile: FunctionalInterventionProfile
    ) -> tuple[tuple[EvidenceAction, ...], tuple[str, ...]]:
        executable: list[EvidenceAction] = []
        waiting: list[str] = []
        for action in actions:
            if action.cost < 0:
                continue
            missing = profile.unmeasured(action.prerequisites)
            if missing:
                waiting.append(f"{action.identifier}: {', '.join(missing)}")
            else:
                executable.append(action)
        return tuple(executable), tuple(waiting)

    @staticmethod
    def _is_better(
        candidate: tuple[EvidenceAction, ...],
        covered: frozenset[str],
        cost: float,
        best: tuple[EvidenceAction, ...],
        best_covered: frozenset[str],
        best_cost: float,
        weights: Mapping[str, float],
        action_priorities: Mapping[str, float],
    ) -> bool:
        score = sum(weights.get(identifier, 1.0) for identifier in covered)
        best_score = sum(weights.get(identifier, 1.0) for identifier in best_covered)
        if score != best_score:
            return score > best_score
        if cost != best_cost:
            return cost < best_cost
        # A bigger set is never preferred at equal coverage and equal cost: extra
        # arms buy redundancy, not information, and must not be rewarded.
        if len(candidate) != len(best):
            return len(candidate) < len(best)
        priority = sum(action_priorities.get(action.identifier, 0.0) for action in candidate)
        best_priority = sum(action_priorities.get(action.identifier, 0.0) for action in best)
        if priority != best_priority:
            return priority > best_priority
        return tuple(action.identifier for action in candidate) < tuple(action.identifier for action in best)
