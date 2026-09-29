"""Evaluation planning: consolidated module responsibilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import product
import time
from typing import TYPE_CHECKING, Any, Iterable, Mapping, Sequence
from maestro.models import BiologicalQuantity, PremiseGrant, PremiseRequirement


if TYPE_CHECKING:  # pragma: no cover - typing only, avoids a runtime import cycle
    from .cases import EvidenceMenuItem, PublicCase, RevealedEvidence

_TOLERANCE = 1e-9

# The enumerator's own ceiling. Every consumer that reasons about instance size
# must compare against this one number, so a solver cannot set an escalation
# threshold the enumerator can never reach.
DEFAULT_PLAN_LIMIT = 4096


def effective_fields(observed: Mapping[str, "RevealedEvidence"]) -> frozenset[str]:
    """Interpretation fields that acquired records are admitted to supply.

    A record supplies its declared fields only when it passes the admission
    gates on its own class: schema validity, biological quality, and being a
    real measurement rather than a retrieved or derived record.

    This is the *name-level* gate and it is deliberately not the whole rule. It
    says which fields were claimed by an admissible record; whether the claim
    means what a dependent action needs is decided by :func:`unmet_premises`
    against the case's premise registry.
    """

    return frozenset(
        name
        for record in observed.values()
        if record.admits_biological_fields
        for name in record.interpretation_fields
    )


def granted_premises(
    public: "PublicCase", observed: Mapping[str, "RevealedEvidence"]
) -> Mapping[str, tuple[PremiseGrant, ...]]:
    """What each admitted record actually delivers, per interpretation field.

    The grant's quantity, entity, site and units come from the *action* that
    produced the record, and its context, time and quality come from the record
    itself. Neither comes from the field's name, which is the whole point: a
    field called ``protein_present`` supplied by a viability assay grants
    viability.
    """

    grants: dict[str, list[PremiseGrant]] = {}
    for record in observed.values():
        if not record.admits_biological_fields:
            continue
        item = public.action(record.action_identifier)
        action = item.action if item is not None else None
        for name in record.interpretation_fields:
            grants.setdefault(name, []).append(
                PremiseGrant(
                    field=name,
                    source_action=record.action_identifier,
                    quantity=action.quantity if action is not None else BiologicalQuantity.UNSPECIFIED,
                    is_estimate=bool(action.quantity_is_estimated) if action is not None else False,
                    entity=action.entity if action is not None else None,
                    site=action.site if action is not None else None,
                    units=action.units if action is not None else None,
                    context_identifier=record.context_identifier,
                    time_hours=record.time_hours,
                    quality=record.biological_quality,
                    quality_passed=record.usable_for_mechanism,
                    provenance=record.source_id,
                )
            )
    return {name: tuple(values) for name, values in grants.items()}


def unmet_premises(
    public: "PublicCase",
    action: Any,
    supplied_fields: frozenset[str],
    grants: Mapping[str, tuple[PremiseGrant, ...]] | None = None,
) -> tuple[str, ...]:
    """Prerequisite fields this action still lacks, with the reason for each.

    A field is unmet when no admissible record claims it, or when every record
    that claims it fails the case's declared requirement for that field. A
    field with no declared requirement falls back to name presence, which keeps
    an untyped legacy catalogue working; :attr:`PremiseGrant.is_typed` is how
    such a field is told apart from a checked one.
    """

    registry: Mapping[str, PremiseRequirement] = getattr(public, "premise_registry", {}) or {}
    problems: list[str] = []
    for name in action.prerequisites:
        requirement = registry.get(name)
        if requirement is None or not requirement.is_typed:
            if name not in supplied_fields:
                problems.append(f"{name}:not_supplied")
            continue
        candidates = (grants or {}).get(name, ())
        if not candidates:
            problems.append(f"{name}:not_supplied")
            continue
        failures = [requirement.unmet_reasons(grant) for grant in candidates]
        if all(reasons for reasons in failures):
            # Report the closest near miss rather than every rejection, so the
            # repair step is pointed at one premise it can actually act on.
            closest = min(failures, key=len)
            problems.append(f"{name}:{','.join(closest)}")
    return tuple(problems)


def declared_grants(
    public: "PublicCase", sequence: Sequence[str]
) -> Mapping[str, tuple[PremiseGrant, ...]]:
    """What the *declarations* of a planned sequence would grant, if they held.

    This is the planner's counterpart to :func:`granted_premises`. At planning
    time no record exists, so the quantity, entity, site and units come from
    each action's public declaration and the quality is assumed to pass. That
    optimism is the point: a plan is a bet that the assay will return a
    qualified result.

    What it is *not* optimistic about is meaning. An action that declares it
    measures viability cannot be planned as the supplier of an occupancy
    premise, because no result of that assay would ever discharge it. Rejecting
    that route at planning time is different from assuming the route succeeds.
    """

    grants: dict[str, list[PremiseGrant]] = {}
    for identifier in sequence:
        item = public.action(identifier)
        if item is None:
            continue
        action = item.action
        context = action.execution_context or (public.context_identifier if action.context_bound else None)
        for name in action.supplies:
            grants.setdefault(name, []).append(
                PremiseGrant(
                    field=name,
                    source_action=identifier,
                    quantity=action.quantity,
                    is_estimate=bool(action.quantity_is_estimated),
                    entity=action.entity,
                    site=action.site,
                    units=action.units,
                    context_identifier=context,
                    time_hours=action.time_hours,
                    quality="declared",
                    quality_passed=True,
                    provenance="declaration",
                )
            )
    return {name: tuple(values) for name, values in grants.items()}


@dataclass(frozen=True)
class PlanEnumeration:
    """A plan set together with whether the search that produced it finished."""

    plans: tuple[tuple[str, ...], ...]
    complete: bool
    limit: int
    stopping_reason: str

    def __len__(self) -> int:
        return len(self.plans)

    def __iter__(self):
        return iter(self.plans)


def purchasable_actions(
    public: "PublicCase", queried: Sequence[str], spent: float
) -> tuple["EvidenceMenuItem", ...]:
    """Actions the budget and the registry still allow, premises aside.

    This is the menu a policy is shown. An action whose interpretation premise
    is not yet measured stays on it deliberately: seeing that a capability
    exists but cannot run yet is the signal directed repair acts on. Legality
    is decided separately by :func:`legal_actions`.
    """

    already = set(queried)
    remaining = public.budget - spent
    return tuple(
        item
        for item in public.actions
        if item.available
        and item.action.identifier not in already
        and item.action.cost <= remaining + _TOLERANCE
    )


def legal_actions(
    public: "PublicCase",
    queried: Sequence[str],
    spent: float,
    supplied_fields: frozenset[str],
    *,
    grants: Mapping[str, tuple[PremiseGrant, ...]] | None = None,
    observed: Mapping[str, "RevealedEvidence"] | None = None,
) -> tuple["EvidenceMenuItem", ...]:
    """Return every action that may legally execute right now.

    The four conditions are exactly the ones the replay environment enforces:
    the action is registered as available, it has not already been queried, it
    fits in the remaining budget, and every interpretation prerequisite it
    names is discharged by an admitted record. Execution, scoring and planning
    all call this one function, so they cannot disagree about what could have
    happened.

    The premise check is typed where the case types it. Pass ``observed`` (or
    precomputed ``grants``) to have each prerequisite checked against the
    quantity, entity, site, units, context and time the supplying record
    actually carries. With neither, the check falls back to field-name
    presence, which is the pre-typing behaviour.
    """

    if grants is None and observed is not None:
        grants = granted_premises(public, observed)
    return tuple(
        item
        for item in purchasable_actions(public, queried, spent)
        if not unmet_premises(public, item.action, supplied_fields, grants)
    )


def plan_enumeration(public: "PublicCase", *, limit: int = DEFAULT_PLAN_LIMIT) -> PlanEnumeration:
    """Every purchase sequence the public contract permits, and whether that is all of them.

    This is the planner's view. It uses only declared costs, availability,
    prerequisites and `supplies`: a purchased action is assumed to supply the
    fields it *declares*, because at planning time nobody knows whether the
    record will qualify. That optimism is explicit and is why a selected
    prerequisite assay never guarantees its premise is satisfied.

    The search stops at ``limit``. When it does, ``complete`` is False and the
    caller may not treat the returned set as the whole feasible region: an
    unexplored sequence could be better than anything enumerated. Reporting
    that is the difference between a bounded search and a false certificate.

    The function never reads a hidden outcome, so two worlds with identical
    public contracts produce byte-identical plan sets.
    """

    found: set[tuple[str, ...]] = {()}
    frontier: list[tuple[tuple[str, ...], float, frozenset[str]]] = [((), 0.0, frozenset())]
    truncated = False
    while frontier:
        if len(found) >= limit:
            truncated = True
            break
        sequence, spent, supplied = frontier.pop()
        for item in legal_actions(
            public, sequence, spent, supplied, grants=declared_grants(public, sequence)
        ):
            extended = sequence + (item.action.identifier,)
            if extended in found:
                continue
            found.add(extended)
            frontier.append(
                (extended, spent + item.action.cost, supplied | frozenset(item.action.supplies))
            )
    return PlanEnumeration(
        plans=tuple(sorted(found)),
        complete=not truncated,
        limit=limit,
        stopping_reason="exhausted" if not truncated else "plan_limit_reached",
    )


def enumerate_public_plans(
    public: "PublicCase", *, limit: int = DEFAULT_PLAN_LIMIT
) -> tuple[tuple[str, ...], ...]:
    """The plan set alone, for callers that do not need the completeness flag.

    Prefer :func:`plan_enumeration` anywhere the answer is used to make a
    claim about optimality.
    """

    return plan_enumeration(public, limit=limit).plans


def enumerate_executed_sequences(
    public: "PublicCase",
    outcomes: Mapping[str, "RevealedEvidence"],
    *,
    limit: int = DEFAULT_PLAN_LIMIT,
) -> tuple[tuple[str, ...], ...]:
    """Every purchase sequence that would actually execute in this hidden world.

    Evaluator-only. A declared supplier whose real record fails admission does
    not unlock its dependants here, which is precisely the disagreement between
    a declaration and a measurement that the scorer must respect.
    """

    found: set[tuple[str, ...]] = {()}
    frontier: list[tuple[tuple[str, ...], float]] = [((), 0.0)]
    while frontier and len(found) < limit:
        sequence, spent = frontier.pop()
        observed = {name: outcomes[name] for name in sequence if name in outcomes}
        for item in legal_actions(public, sequence, spent, effective_fields(observed), observed=observed):
            identifier = item.action.identifier
            if identifier not in outcomes:
                # No registered hidden result: the environment would refuse it.
                continue
            extended = sequence + (identifier,)
            if extended in found:
                continue
            found.add(extended)
            frontier.append((extended, spent + item.action.cost))
    return tuple(sorted(found))


def sequence_cost(public: "PublicCase", sequence: Iterable[str]) -> float:
    total = 0.0
    for identifier in sequence:
        item = public.action(identifier)
        if item is not None:
            total += item.action.cost
    return total


def licensing_certificates(
    public: "PublicCase",
    outcomes: Mapping[str, "RevealedEvidence"],
    matches: Any,
    *,
    restricted_to: Iterable[str] | None = None,
) -> tuple[tuple[tuple[str, ...], float], ...]:
    """Legal sequences whose acquired records satisfy ``matches``, with their cost.

    ``matches`` is a predicate over the observed mapping, supplied by the
    scorer. ``restricted_to`` limits the search to actions a policy actually
    acquired, which turns the same enumeration into "the cheapest certificate
    contained in this acquisition".
    """

    allowed = None if restricted_to is None else set(restricted_to)
    certificates: list[tuple[tuple[str, ...], float]] = []
    for sequence in enumerate_executed_sequences(public, outcomes):
        if allowed is not None and not set(sequence).issubset(allowed):
            continue
        observed = {name: outcomes[name] for name in sequence if name in outcomes}
        if matches(observed):
            certificates.append((sequence, sequence_cost(public, sequence)))
    return tuple(sorted(certificates, key=lambda entry: (entry[1], entry[0])))


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
