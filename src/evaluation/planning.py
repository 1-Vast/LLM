"""Constrained evidence-plan selection over the public contract.

File summary
- Path: src/evaluation/planning.py
- Purpose: Choose a feasible evidence bundle under explicit experimental constraints, using public information only.
- Core points:
  - This is the *evidence-selection* problem. Choosing interventions and scheduling assays are separate problems and are not modelled here.
  - The instantiated instances are tiny (at most four listed actions and ten legal prefixes per case), so exhaustive enumeration is exact and no external solver is introduced; `scalability_profile` records the size at which that stops being true.
  - Scenario branching uses declared outcome classes, never a hidden result, so the planner is non-anticipative by construction.
- Interfaces: `PlanConstraints`, `PlanSolution`, `solve_exact`, `scalability_profile`, `decision_ambiguity`, `hypothesis_compatibility`, `CompatibilityStatus`, `CompatibilityVerdict`
- Depends on: evaluation.feasibility
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from itertools import product
from typing import TYPE_CHECKING, Mapping, Sequence

from .feasibility import DEFAULT_PLAN_LIMIT, plan_enumeration, sequence_cost

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .cases import PublicCase

# Enumeration is exact below this many candidate plans. Above it the instance
# has outgrown the method and a CP-SAT or MILP formulation is warranted; the
# profile reports that rather than silently returning a heuristic answer.
#
# This must not exceed the enumerator's own ceiling. A threshold the enumerator
# can never reach is unreachable code that also makes the "too large" branch a
# promise the solver cannot keep: the search would truncate first and still
# claim to have finished.
EXACT_ENUMERATION_LIMIT = DEFAULT_PLAN_LIMIT


@dataclass(frozen=True)
class PlanConstraints:
    """Resource and compatibility limits a selected bundle must respect.

    Every field is an explicit experimental quantity rather than an abstract
    penalty. Shared controls are charged once as a setup, not once per assay
    that uses them, which is how a plate is actually costed.
    """

    budget: float
    wells_available: int | None = None
    batch_capacity: int | None = None
    wells_per_action: Mapping[str, int] = field(default_factory=dict)
    required_replicates: Mapping[str, int] = field(default_factory=dict)
    shared_control_wells: Mapping[str, int] = field(default_factory=dict)
    control_required_by: Mapping[str, str] = field(default_factory=dict)
    incompatible_pairs: tuple[tuple[str, str], ...] = ()
    unavailable: frozenset[str] = frozenset()

    def wells_used(self, sequence: Sequence[str]) -> int:
        selected = set(sequence)
        total = sum(
            self.wells_per_action.get(name, 0) * max(1, self.required_replicates.get(name, 1))
            for name in selected
        )
        controls = {self.control_required_by[name] for name in selected if name in self.control_required_by}
        total += sum(self.shared_control_wells.get(name, 0) for name in controls)
        return total

    def violations(self, public: "PublicCase", sequence: Sequence[str]) -> tuple[str, ...]:
        """Every constraint this bundle breaks, named rather than summed away."""

        selected = set(sequence)
        problems: list[str] = []
        if sequence_cost(public, sequence) > self.budget + 1e-9:
            problems.append("budget")
        if self.batch_capacity is not None and len(selected) > self.batch_capacity:
            problems.append("batch_capacity")
        if self.wells_available is not None and self.wells_used(sequence) > self.wells_available:
            problems.append("wells")
        for first, second in self.incompatible_pairs:
            if first in selected and second in selected:
                problems.append(f"incompatible:{first}+{second}")
        for name in sorted(selected & set(self.unavailable)):
            problems.append(f"unavailable:{name}")
        return tuple(problems)


@dataclass(frozen=True)
class PlanSolution:
    """A selected bundle with the solver status it is entitled to claim."""

    sequence: tuple[str, ...]
    objective: float
    status: str
    bound: float
    gap: float
    evaluated: int
    feasible_count: int
    runtime_seconds: float
    scenarios: int
    rejected: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = ()
    search_complete: bool = True
    stopping_reason: str = "exhausted"

    @property
    def proven_optimal(self) -> bool:
        """Optimality is claimed only when the search actually finished.

        A truncated enumeration has an objective for the part it saw and no
        knowledge of the part it did not, so it has an incumbent, not an
        optimum.
        """

        return self.status == "OPTIMAL" and self.search_complete


def declared_scenarios(public: "PublicCase", sequence: Sequence[str]) -> tuple[Mapping[str, str], ...]:
    """Every combination of declared outcome classes the selected actions could return.

    These are the case author's public declarations. They are not probabilities
    and are not the hidden result: an action with no declared mapping
    contributes a single ``unknown`` branch, which is what an undeclared
    observation actually is.
    """

    axes: list[tuple[tuple[str, str], ...]] = []
    for name in sequence:
        item = public.action(name)
        declared = sorted(set(item.action.expected_outcomes.values())) if item is not None else []
        if not declared:
            declared = ["unknown"]
        axes.append(tuple((name, value) for value in declared))
    if not axes:
        return ({},)
    return tuple(dict(combination) for combination in product(*axes))


class CompatibilityStatus(str, Enum):
    """What an observation set has actually established about the hypotheses.

    ``DECIDED`` and ``CONTRADICTORY`` are different outcomes and must not be
    conflated: one hypothesis surviving is a resolved contrast, none surviving
    means the declarations and the observations cannot both be right. The
    second is a reason to investigate the model or the assay, never a success.
    """

    AMBIGUOUS = "ambiguous"
    DECIDED = "decided"
    CONTRADICTORY = "contradictory"
    UNUSABLE_MEASUREMENT = "unusable_measurement"


@dataclass(frozen=True)
class CompatibilityVerdict:
    """Which hypotheses survive an observation set, and what broke if none do."""

    status: CompatibilityStatus
    surviving: tuple[str, ...]
    conflicting_actions: tuple[str, ...] = ()
    unusable_actions: tuple[str, ...] = ()
    undeclared_actions: tuple[str, ...] = ()

    @property
    def decided(self) -> bool:
        """True only for a genuine resolution, never for a contradiction."""

        return self.status is CompatibilityStatus.DECIDED

    @property
    def residual(self) -> int:
        """The planner's objective term.

        A contradiction is charged the full hypothesis count rather than zero,
        because a plan that produces one has resolved nothing and has bought
        an investigation. Scoring it as the best possible outcome is exactly
        the error that let conflicting evidence disappear.
        """

        if self.status is CompatibilityStatus.CONTRADICTORY:
            return max(1, len(self.conflicting_actions) + 1)
        return len(self.surviving)


def hypothesis_compatibility(
    public: "PublicCase", observed: Mapping[str, str]
) -> CompatibilityVerdict:
    """Evaluate every declared observation against every hypothesis, jointly.

    The previous rule stopped filtering once a single hypothesis remained, so a
    later observation that ruled out that last hypothesis was silently ignored.
    Here each hypothesis is tested against the *whole* observation set, so a
    conflict is still visible after the set has narrowed.

    An observation whose value is not among the action's declared outcomes is
    an unusable measurement, not a refutation: the declaration says nothing
    about that value, so it cannot eliminate anything.
    """

    hypotheses = tuple(item["identifier"] for item in public.hypotheses)
    unusable: list[str] = []
    undeclared: list[str] = []
    usable: dict[str, tuple[Mapping[str, str], str]] = {}

    for name, value in observed.items():
        item = public.action(name)
        if item is None or not item.action.expected_outcomes:
            undeclared.append(name)
            continue
        declared = item.action.expected_outcomes
        if not set(hypotheses).issubset(set(declared)):
            undeclared.append(name)
            continue
        if value not in set(declared.values()):
            unusable.append(name)
            continue
        usable[name] = (declared, value)

    surviving = tuple(
        name
        for name in hypotheses
        if all(declared[name] == value for declared, value in usable.values())
    )

    if unusable and not usable:
        # Every observation in hand is unusable. Nothing was eliminated, but
        # calling that "ambiguous" would hide that the acquisitions failed
        # rather than that none were made.
        return CompatibilityVerdict(
            status=CompatibilityStatus.UNUSABLE_MEASUREMENT,
            surviving=surviving,
            unusable_actions=tuple(sorted(unusable)),
            undeclared_actions=tuple(sorted(undeclared)),
        )

    if surviving:
        status = (
            CompatibilityStatus.DECIDED if len(surviving) == 1 else CompatibilityStatus.AMBIGUOUS
        )
        return CompatibilityVerdict(
            status=status,
            surviving=surviving,
            unusable_actions=tuple(sorted(unusable)),
            undeclared_actions=tuple(sorted(undeclared)),
        )

    # No hypothesis explains everything. Name the observations that have to be
    # dropped before one would, so the repair step has somewhere to start.
    conflicting: set[str] = set()
    for hypothesis in hypotheses:
        disagreeing = [
            name for name, (declared, value) in usable.items() if declared[hypothesis] != value
        ]
        if disagreeing:
            conflicting.update(disagreeing)
    return CompatibilityVerdict(
        status=CompatibilityStatus.CONTRADICTORY,
        surviving=(),
        conflicting_actions=tuple(sorted(conflicting)),
        unusable_actions=tuple(sorted(unusable)),
        undeclared_actions=tuple(sorted(undeclared)),
    )


def decision_ambiguity(public: "PublicCase", observed: Mapping[str, str]) -> int:
    """Residual ambiguity for the planner's objective.

    Kept as the scalar the optimiser minimises. It now routes through
    :func:`hypothesis_compatibility`, so a contradiction is charged rather than
    rewarded; callers that need to know *why* a plan scored as it did should
    ask for the verdict instead of this number.
    """

    return hypothesis_compatibility(public, observed).residual


def solve_exact(
    public: "PublicCase",
    constraints: PlanConstraints,
    *,
    cost_weight: float = 0.25,
    robust: bool = True,
) -> PlanSolution:
    """Select the bundle minimising worst-case residual ambiguity plus weighted cost.

    The objective is deliberately not an invented expected value of information:
    with no credible outcome distribution, the planner reports the worst case
    over the declared scenario set. ``robust=False`` averages over scenarios
    instead, which is only defensible when the declarations are equiprobable by
    construction; it is offered so the sensitivity of a claim to that choice can
    be measured rather than assumed.

    ``OPTIMAL`` with a zero gap is returned only when the enumeration actually
    finished; a truncated search returns ``FEASIBLE_INCOMPLETE`` with an
    infinite gap, because the region it never reached could hold a better plan.
    Even a proven optimum is optimality of this declared finite model, not a
    statement about biology.
    """

    started = time.perf_counter()
    enumeration = plan_enumeration(public, limit=EXACT_ENUMERATION_LIMIT)
    plans = enumeration.plans

    best: tuple[float, tuple[str, ...]] | None = None
    rejected: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    feasible = 0
    scenario_total = 0
    for sequence in plans:
        problems = constraints.violations(public, sequence)
        if problems:
            rejected.append((sequence, problems))
            continue
        feasible += 1
        scenarios = declared_scenarios(public, sequence)
        scenario_total += len(scenarios)
        residuals = [decision_ambiguity(public, scenario) for scenario in scenarios]
        residual = max(residuals) if robust else sum(residuals) / len(residuals)
        value = residual + cost_weight * sequence_cost(public, sequence)
        if best is None or value < best[0] - 1e-12 or (abs(value - best[0]) <= 1e-12 and sequence < best[1]):
            best = (value, sequence)

    runtime = time.perf_counter() - started
    if best is None:
        # With a complete search this is a proof of infeasibility. With a
        # truncated one it only means nothing feasible was reached before the
        # cap, which is a different statement and is reported as one.
        status = "INFEASIBLE" if enumeration.complete else "NO_FEASIBLE_PLAN_FOUND_INCOMPLETE"
        return PlanSolution(
            sequence=(), objective=float("inf"), status=status, bound=float("-inf"),
            gap=float("inf"), evaluated=len(plans), feasible_count=0, runtime_seconds=runtime,
            scenarios=scenario_total, rejected=tuple(rejected),
            search_complete=enumeration.complete, stopping_reason=enumeration.stopping_reason,
        )
    if not enumeration.complete:
        # An incumbent from a partial search. The only valid lower bound is the
        # trivial one, so the gap is infinite: the unexplored region could
        # contain anything.
        return PlanSolution(
            sequence=best[1], objective=best[0], status="FEASIBLE_INCOMPLETE",
            bound=float("-inf"), gap=float("inf"), evaluated=len(plans),
            feasible_count=feasible, runtime_seconds=runtime, scenarios=scenario_total,
            rejected=tuple(rejected), search_complete=False,
            stopping_reason=enumeration.stopping_reason,
        )
    return PlanSolution(
        sequence=best[1], objective=best[0], status="OPTIMAL", bound=best[0], gap=0.0,
        evaluated=len(plans), feasible_count=feasible, runtime_seconds=runtime,
        scenarios=scenario_total, rejected=tuple(rejected), search_complete=True,
        stopping_reason=enumeration.stopping_reason,
    )


def scalability_profile(public: "PublicCase", constraints: PlanConstraints) -> Mapping[str, object]:
    """Report the instance size and whether exhaustive enumeration still applies."""

    enumeration = plan_enumeration(public, limit=EXACT_ENUMERATION_LIMIT)
    plans = enumeration.plans
    solution = solve_exact(public, constraints)
    return {
        "menu_size": len(public.actions),
        "available_actions": sum(1 for item in public.actions if item.available),
        "legal_plans_including_empty": len(plans),
        "enumeration_complete": enumeration.complete,
        "enumeration_stopping_reason": enumeration.stopping_reason,
        "declared_scenarios_evaluated": solution.scenarios,
        "exact_enumeration_applies": enumeration.complete,
        "solver_backend": "exhaustive_enumeration",
        "solver_status": solution.status,
        "runtime_seconds": round(solution.runtime_seconds, 6),
        "escalation_threshold_plans": EXACT_ENUMERATION_LIMIT,
        "escalation_note": (
            "A CP-SAT or MILP formulation is warranted only above the threshold, or when "
            "scheduling and shared-control structure no longer fit this selection model."
        ),
    }
