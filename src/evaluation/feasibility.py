"""One legality rule shared by execution, scoring, and planning.

File summary
- Path: src/evaluation/feasibility.py
- Purpose: Decide which registered actions may legally execute, and enumerate the resulting legal sequences.
- Core points:
  - `legal_actions` is the single feasibility rule; the replay environment, the scorer and the planner all call it, so no two of them can disagree about what is executable.
  - `enumerate_public_plans` reads only the public contract, so a planner built on it cannot anticipate a hidden outcome.
  - `enumerate_executed_sequences` is evaluator-only: it consumes true outcomes and is never handed to a policy.
- Interfaces: `purchasable_actions`, `legal_actions`, `effective_fields`, `granted_premises`, `declared_grants`, `unmet_premises`, `plan_enumeration`, `enumerate_public_plans`, `enumerate_executed_sequences`, `licensing_certificates`
- Depends on: maestro.models (premise typing); case objects are consumed structurally
"""
from __future__ import annotations

from dataclasses import dataclass
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
