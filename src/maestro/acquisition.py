"""Exact expected-coverage selection when actions declare a chance of returning a result.

File summary
- Path: src/maestro/acquisition.py
- Purpose: choose an evidence bundle by the *probability that it answers* rather than by the
  labels it mentions, using the ``detection_power`` every action may already declare.
- Core points:
  - Plain set cover reads a bundle as covering a hypothesis whenever one selected action claims
    it. An assay that returns an uninterpretable result half the time covers it half the time, so
    the bundle's coverage is ``1 - prod(1 - p_a)`` per hypothesis: a stochastic set-cover
    objective, solved exactly here over the small pools the framework actually has.
  - The objective is expected coverage, not information value and not experimental utility; the
    cost, size and identifier tie-breaks keep the choice auditable and deterministic.
  - An action that declares no ``detection_power`` is treated as certain and *named* in the
    returned assumptions, because assuming a value and hiding the assumption is how a declared
    field stops being a declaration.
  - A pool above the exhaustive cap returns ``too_large`` rather than a heuristic answer, for the
    same reason ``selection.py`` refuses: an exact method that silently becomes approximate is a
    claim the code cannot keep.
- Interfaces: `ExpectedCoveragePlan`, `select_expected_coverage`
- Depends on: maestro.models, maestro.handoff (rejection reasons), maestro.selection (the plan type)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from math import isfinite
from typing import Mapping, Sequence

from .handoff import RejectedCandidate
from .models import EvidenceAction, FunctionalInterventionProfile
from .selection import BudgetedEvidencePlan

MAXIMUM_CANDIDATES = 16
_TOLERANCE = 1e-12


@dataclass(frozen=True)
class ExpectedCoveragePlan:
    """A bundle, the probability it answers each hypothesis, and what it cost."""

    plan: BudgetedEvidencePlan
    coverage_probability: Mapping[str, float] = field(default_factory=dict)
    expected_coverage: float = 0.0
    rejected: tuple[RejectedCandidate, ...] = ()
    assumptions: tuple[str, ...] = ()
    status: str = "optimal"
    reason: str | None = None
    dependence_groups: Mapping[str, str] = field(default_factory=dict)

    def probability_of(self, hypothesis: str) -> float:
        return float(self.coverage_probability.get(hypothesis, 0.0))


def _probability(action: EvidenceAction) -> float:
    return 1.0 if action.detection_power is None else float(action.detection_power)


def _coverage_probabilities(
    selected: Sequence[EvidenceAction], required: frozenset[str], groups: Mapping[str, str]
) -> dict[str, float]:
    probabilities: dict[str, float] = {}
    for hypothesis in required:
        group_power: dict[str, float] = {}
        for action in selected:
            if hypothesis in action.distinguishes:
                group = groups[action.identifier]
                group_power[group] = max(group_power.get(group, 0.0), _probability(action))
        remaining = 1.0
        for power in group_power.values():
            remaining *= 1.0 - power
        probabilities[hypothesis] = 1.0 - remaining
    return probabilities


def _dependence_groups(actions: Sequence[EvidenceAction], sources: Mapping[str, str]) -> dict[str, str]:
    """Freeze connected source clusters over the menu; shared evidence is not a new trial.

    Within a component, max(p) is a conservative union bound under unknown dependence.
    Distinct components still require the explicit conditional-independence assumption.
    Actions without provenance retain the legacy independent-trial assumption.
    """
    components: list[tuple[set[str], set[str]]] = []
    for action in actions:
        refs = {sources.get(ref, ref) for ref in action.source_ids}
        members = {action.identifier}
        merged = [(ids, keys) for ids, keys in components if keys & refs]
        for ids, keys in merged:
            members.update(ids)
            refs.update(keys)
            components.remove((ids, keys))
        components.append((members, refs))
    return {identifier: min(members) for members, _ in components for identifier in members}


def select_expected_coverage(
    required: frozenset[str],
    actions: Sequence[EvidenceAction],
    profile: FunctionalInterventionProfile,
    budget: float,
    *,
    coverage_threshold: float = 0.0,
    weights: Mapping[str, float] | None = None,
    source_groups: Mapping[str, str] | None = None,
) -> ExpectedCoveragePlan:
    """Maximise expected coverage under a budget; ties go to cost, size, then label.

    ``coverage_threshold`` is the probability above which a hypothesis counts as covered in the
    returned sets. The default of zero reproduces set semantics for the covered/uncovered fields
    while the objective still uses the probabilities, so a caller can see the difference between
    "covered in name" and "covered with stated probability".
    """

    if isinstance(budget, bool) or not isfinite(budget) or budget < 0:
        raise ValueError("Budget must be nonnegative.")
    if len({action.identifier for action in actions}) != len(actions):
        raise ValueError("duplicate_action_identifier")
    for action in actions:
        if isinstance(action.cost, bool) or not isinstance(action.cost, (int, float)) or not isfinite(action.cost) or action.cost < 0:
            raise ValueError("invalid_action_cost")
        if action.detection_power is not None and (isinstance(action.detection_power, bool)
                or not isinstance(action.detection_power, (int, float))
                or not isfinite(action.detection_power) or not 0 <= action.detection_power <= 1):
            raise ValueError("invalid_detection_power")
    if source_groups is not None and (any(not isinstance(k, str) or not k.strip()
            or not isinstance(v, str) or not v.strip() for k, v in source_groups.items())
            or {ref for action in actions for ref in action.source_ids} - source_groups.keys()):
        raise ValueError("incomplete_source_groups")
    if not 0.0 <= coverage_threshold <= 1.0:
        raise ValueError("A coverage threshold must lie in [0, 1].")
    weights = dict(weights or {})
    if set(weights) - required or any(
        isinstance(value, bool) or not isfinite(value) or value < 0 for value in weights.values()
    ):
        raise ValueError("Weights must be finite nonnegative values for required hypotheses.")
    if not required:
        return ExpectedCoveragePlan(
            plan=BudgetedEvidencePlan((), frozenset(), frozenset(), 0.0, ()),
            expected_coverage=0.0,
        )

    executable: list[EvidenceAction] = []
    waiting: list[str] = []
    for action in sorted(actions, key=lambda item: item.identifier):
        if action.cost < 0:
            continue
        missing = profile.unmeasured(action.prerequisites)
        if missing:
            waiting.append(f"{action.identifier}: {', '.join(missing)}")
        else:
            executable.append(action)
    assumptions = tuple(
        f"assumed_certain_execution:{action.identifier}"
        for action in executable
        if action.detection_power is None
    )
    groups = _dependence_groups(executable, source_groups or {})
    if len(set(groups.values())) < len(executable):
        assumptions += ("worst_case_dependence_within_source_component",)
    if len(set(groups.values())) > 1:
        assumptions += ("conditional_independence_between_source_components",)
    if len(executable) > 1 and any(not action.source_ids for action in executable):
        assumptions += ("unverified_independence_for_actions_without_source_ids",)
    if len(executable) > MAXIMUM_CANDIDATES:
        rejected = tuple(
            RejectedCandidate(action.identifier, "exact_candidate_limit_exceeded")
            for action in actions
        )
        return ExpectedCoveragePlan(
            plan=BudgetedEvidencePlan(
                (), frozenset(), required, 0.0, tuple(waiting),
                {item.action_identifier: item.reason for item in rejected},
            ),
            assumptions=assumptions,
            status="too_large",
            dependence_groups=groups,
            rejected=rejected,
            reason=(
                f"candidate pool has {len(executable)} executable actions; exact enumeration stops at "
                f"{MAXIMUM_CANDIDATES}"
            ),
        )

    best: tuple[EvidenceAction, ...] = ()
    best_probabilities: dict[str, float] = {hypothesis: 0.0 for hypothesis in required}
    best_expected = 0.0
    best_cost = 0.0
    for size in range(1, len(executable) + 1):
        for candidate in combinations(executable, size):
            cost = sum(action.cost for action in candidate)
            if cost > budget + _TOLERANCE:
                continue
            probabilities = _coverage_probabilities(candidate, required, groups)
            expected = sum(weights.get(name, 1.0) * value for name, value in probabilities.items())
            if _is_better(candidate, expected, cost, best, best_expected, best_cost):
                best, best_probabilities, best_expected, best_cost = (
                    candidate,
                    probabilities,
                    expected,
                    cost,
                )

    covered = frozenset(
        hypothesis
        for hypothesis, probability in best_probabilities.items()
        if probability > coverage_threshold + _TOLERANCE
    )
    rejected = _rejections(actions, best, best_probabilities, budget, profile, groups)
    plan = BudgetedEvidencePlan(
        actions=best,
        covered=covered & required,
        uncovered=required - covered,
        total_cost=best_cost,
        waiting_for_prerequisites=tuple(waiting),
        rejection_reasons={item.action_identifier: item.reason for item in rejected},
    )
    return ExpectedCoveragePlan(
        plan=plan,
        coverage_probability=best_probabilities,
        expected_coverage=best_expected,
        rejected=rejected,
        assumptions=assumptions,
        dependence_groups=groups,
    )


def _is_better(
    candidate: Sequence[EvidenceAction],
    expected: float,
    cost: float,
    best: Sequence[EvidenceAction],
    best_expected: float,
    best_cost: float,
) -> bool:
    if abs(expected - best_expected) > _TOLERANCE:
        return expected > best_expected
    if abs(cost - best_cost) > _TOLERANCE:
        return cost < best_cost
    if len(candidate) != len(best):
        return len(candidate) < len(best)
    return tuple(action.identifier for action in candidate) < tuple(action.identifier for action in best)


def _rejections(
    actions: Sequence[EvidenceAction],
    chosen: Sequence[EvidenceAction],
    probabilities: Mapping[str, float],
    budget: float,
    profile: FunctionalInterventionProfile,
    groups: Mapping[str, str],
) -> tuple[RejectedCandidate, ...]:
    """Name why each unselected action is absent, from what the selection knows."""

    selected = {action.identifier for action in chosen}
    chosen_cost = sum(action.cost for action in chosen)
    rejected: list[RejectedCandidate] = []
    for action in actions:
        if action.identifier in selected:
            continue
        missing = profile.unmeasured(action.prerequisites)
        widened = _coverage_probabilities((*chosen, action), frozenset(probabilities),
                                          {**groups, action.identifier: groups.get(action.identifier, action.identifier)})
        gain = sum(widened.values()) - sum(probabilities.values())
        if missing:
            reason = f"waiting_for_prerequisite:{', '.join(missing)}"
        elif chosen_cost + action.cost > budget + _TOLERANCE:
            reason = "exceeds_budget"
        elif gain <= _TOLERANCE:
            reason = "no_marginal_expected_coverage"
        else:
            reason = "not_selected"
        rejected.append(RejectedCandidate(action.identifier, reason))
    return tuple(rejected)
