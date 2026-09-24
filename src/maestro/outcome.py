"""Executable outcome-interpretation rules (rho) and bounded, set-based evidence updates.

File summary
- Path: src/maestro/outcome.py
- Purpose: Apply registered `rho` rules to a real result under explicit conditions and scope.
- Core points:
  - `rho` names which real result may constrain which mechanism variable and when.
  - Only a real measurement can constrain a mechanism contrast.
  - A result shrinks the compatible set; it never produces a probability nobody measured.
  - Failed results are retained with a narrower scope, not discarded.
- Interfaces: `InterpretationTable`, `interpret`, `OutcomeRule`, `OutcomeInterpretation`, `EvidenceState`, `default_rules_for`, `OutcomeClass`
- Depends on: maestro.models
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Protocol, Sequence

from .models import (
    BiologicalQuantity,
    EvidenceAction,
    EvidenceActionKind,
    EvidenceKind,
    EvidenceScope,
    FunctionalInterventionProfile,
    MechanismContrast,
    MechanismHypothesis,
    PremiseGrant,
    PremiseRequirement,
)


class OutcomeClass(str, Enum):
    """The pre-declared result categories of section 5.1, including the failures."""

    PREDICTED = "predicted"
    AMBIGUOUS = "ambiguous"
    OUT_OF_PREDICTION = "out_of_prediction"
    QUALITY_FAILED = "quality_failed"
    CONDITION_UNMATCHED = "condition_unmatched"
    NON_MEASUREMENT = "non_measurement"


class ObservationRecord(Protocol):
    """The fields MAESTRO needs from a real result; ``MeasurementResult`` satisfies it."""

    action_identifier: str
    quality_passed: bool
    interpretation_fields: tuple[str, ...]
    context_identifier: str | None
    time_hours: float | None
    conditions: Mapping[str, str]
    evidence_kind: EvidenceKind
    independent_units: int | None
    result_id: str | None
    source_id: str


@dataclass(frozen=True)
class MeasuredPremise:
    """One admitted assay field with its own biological coordinates and lineage.

    Several modalities may inform a rule, but a grant never changes quantity
    merely because it becomes the parent of a mechanism-level interpretation.
    """

    grant: PremiseGrant
    result_id: str
    independent_units: int | None
    scope: EvidenceScope
    conditions: Mapping[str, str] = field(default_factory=dict)
    source_cluster: str | None = None


@dataclass(frozen=True)
class OutcomeRule:
    """One registered row of ``rho``.

    ``matched_fields`` must all appear in the result's declared interpretation
    fields; ``eliminates`` names the hypotheses this result is allowed to remove
    from the compatible set.  ``scope`` records which layer the result may
    update, so an implementation-level result cannot silently be promoted into a
    mechanism-level verdict.
    """

    identifier: str
    outcome_label: str
    matched_fields: frozenset[str] = frozenset()
    forbidden_fields: frozenset[str] = frozenset()
    required_prefixes: frozenset[str] = frozenset()
    eliminates: frozenset[str] = frozenset()
    scope: EvidenceScope = EvidenceScope.MECHANISM_CONTRAST
    action_identifier: str | None = None
    required_conditions: frozenset[str] = frozenset()
    requires_time_match: bool = False
    boundary: str = ""
    allowed_action_kinds: frozenset[EvidenceActionKind] = frozenset()
    field_requirements: tuple[PremiseRequirement, ...] = ()
    evidence_requirements: tuple[PremiseRequirement, ...] = ()
    matched_condition_keys: tuple[str, ...] = ()
    minimum_independent_units: int = 1
    metric_bounds: Mapping[str, tuple[float | None, float | None]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.minimum_independent_units, bool) or not isinstance(self.minimum_independent_units, int) or self.minimum_independent_units < 1:
            raise ValueError("minimum_independent_units must be a positive integer.")
        for name, bounds in self.metric_bounds.items():
            if not name or len(bounds) != 2 or all(value is None for value in bounds):
                raise ValueError("A metric bound requires a name and at least one finite limit.")
            low, high = bounds
            if any(value is not None and not _finite_number(value) for value in bounds):
                raise ValueError("Metric limits must be finite numbers, not booleans.")
            if low is not None and high is not None and low > high:
                raise ValueError("Metric lower bound cannot exceed its upper bound.")
        for requirement in self.field_requirements:
            if requirement.field not in self.matched_fields and not any(
                requirement.field.startswith(prefix) for prefix in self.required_prefixes
            ):
                raise ValueError("A typed field requirement must name a field used by its rule.")

    def matches(self, observation: ObservationRecord) -> bool:
        fields = frozenset(observation.interpretation_fields)
        if self.action_identifier is not None and observation.action_identifier != self.action_identifier:
            return False
        if not self.matched_fields.issubset(fields):
            return False
        return not (self.forbidden_fields & fields)


@dataclass(frozen=True)
class OutcomeInterpretation:
    """What one real result is allowed to do, decided before it is used."""

    outcome_class: OutcomeClass
    scope: EvidenceScope
    rule_identifier: str | None
    outcome_label: str
    eliminates: frozenset[str]
    conditions_matched: bool
    unmatched_conditions: tuple[str, ...]
    rationale: str
    boundary: str
    authorized_fields: tuple[str, ...] = ()
    refused_fields: tuple[str, ...] = ()
    supporting_result_ids: tuple[str, ...] = ()
    supporting_fields: tuple[str, ...] = ()

    @property
    def can_update_mechanism(self) -> bool:
        return (
            self.scope is EvidenceScope.MECHANISM_CONTRAST
            and self.outcome_class is OutcomeClass.PREDICTED
        )


SCOPE_RANK: Mapping[EvidenceScope, int] = {
    EvidenceScope.PLAN_LIMITATION: 0,
    EvidenceScope.MEASUREMENT_FEASIBILITY: 1,
    EvidenceScope.INTERVENTION_IMPLEMENTATION: 2,
    EvidenceScope.MECHANISM_CONTRAST: 3,
}


def scope_rank(scope: EvidenceScope) -> int:
    """Order the update layers so a weaker scope never licenses a stronger claim."""

    return SCOPE_RANK[scope]


@dataclass(frozen=True)
class ValidatedEvidenceUpdate:
    """The single admission verdict for one observation.

    It separates the questions that used to collapse into ``quality_passed``:
    whether the record is readable at all, whether its declared quality check
    passed, whether its measurement conditions match the plan, whether it is
    statistically usable, and which layer each declared field may update.  Every
    consumer reads this object, so a model prediction or a condition-unmatched
    record cannot acquire a licence by being relabelled.
    """

    result_id: str
    action_identifier: str
    interpretation: OutcomeInterpretation
    readable: bool
    qc_passed: bool
    conditions_matched: bool
    statistically_usable: bool
    admitted_fields: tuple[str, ...]
    scope: EvidenceScope
    measured_premises: tuple[MeasuredPremise, ...] = ()

    @property
    def admissible(self) -> bool:
        return bool(self.admitted_fields)

    def admits(self, field: str, *, required_scope: EvidenceScope) -> bool:
        """Whether this observation may satisfy ``field`` at the required layer."""

        return field in self.admitted_fields and scope_rank(self.scope) >= scope_rank(required_scope)


def admit_evidence(
    interpretation: OutcomeInterpretation,
    observation: ObservationRecord,
    *,
    independent_units: int | None = None,
    action: EvidenceAction | None = None,
    source_cluster: str | None = None,
) -> ValidatedEvidenceUpdate:
    """Decide once, centrally, what an observation is allowed to update.

    A field is admitted only when the record is a real measurement whose quality
    check passed, whose conditions matched, and whose rule fired.  Everything
    else stays readable and is recorded with a narrower scope.  An unknown
    independent-unit count (``None``) is reported as not statistically usable
    rather than being silently replaced by a default.
    """

    qc_passed = observation.quality_passed is True
    conditions_matched = bool(interpretation.conditions_matched)
    is_measurement = observation.evidence_kind is EvidenceKind.REAL_MEASUREMENT
    units = observation.independent_units if independent_units is None else independent_units
    usable = qc_passed and _valid_units(units)
    admitted = (
        tuple(name for name in interpretation.authorized_fields if name in observation.interpretation_fields)
        if (
            qc_passed
            and conditions_matched
            and is_measurement
            and interpretation.outcome_class is OutcomeClass.PREDICTED
            and (action is None or action.identifier == observation.action_identifier)
        )
        else ()
    )
    premises = tuple(
        MeasuredPremise(
            grant=_grant_for(action, observation, name),
            result_id=observation.result_id or observation.action_identifier,
            independent_units=units,
            scope=interpretation.scope,
            conditions=dict(observation.conditions),
            source_cluster=source_cluster,
        )
        for name in admitted
        if action is not None
    )
    return ValidatedEvidenceUpdate(
        result_id=observation.result_id or observation.action_identifier,
        action_identifier=observation.action_identifier,
        interpretation=interpretation,
        readable=True,
        qc_passed=qc_passed,
        conditions_matched=conditions_matched,
        statistically_usable=usable,
        admitted_fields=admitted,
        scope=interpretation.scope if admitted else EvidenceScope.PLAN_LIMITATION,
        measured_premises=premises,
    )


@dataclass(frozen=True)
class UpdateRecord:
    """An append-only note describing what an observation was allowed to change."""

    result_id: str
    action_identifier: str
    outcome_class: OutcomeClass
    scope: EvidenceScope
    eliminated: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class EvidenceState:
    """The set of hypotheses still compatible with the evidence, plus why.

    This is deliberately a *set*, not a posterior.  Section 5.5 accepts reviewed
    set or interval updates for the first version because a precise posterior
    would require distributions nobody measured.
    """

    candidates: frozenset[str]
    eliminated: frozenset[str] = frozenset()
    updates: tuple[UpdateRecord, ...] = ()
    independent_source_clusters: frozenset[str] = frozenset()

    @classmethod
    def open(cls, hypotheses: Sequence[MechanismHypothesis]) -> "EvidenceState":
        return cls(candidates=frozenset(hypothesis.identifier for hypothesis in hypotheses))

    def apply(
        self,
        interpretation: OutcomeInterpretation,
        observation: ObservationRecord,
        *,
        source_cluster: str | None = None,
    ) -> "EvidenceState":
        """Record every observation, but only let a qualified one remove a hypothesis."""

        eliminated_now = (
            frozenset(interpretation.eliminates) & self.candidates
            if interpretation.can_update_mechanism
            else frozenset()
        )
        clusters = self.independent_source_clusters
        if source_cluster:
            clusters = clusters | {source_cluster}
        note = (
            interpretation.rationale
            if eliminated_now
            else f"Retained without a mechanism update: {interpretation.boundary}"
        )
        record = UpdateRecord(
            result_id=observation.result_id or observation.action_identifier,
            action_identifier=observation.action_identifier,
            outcome_class=interpretation.outcome_class,
            scope=interpretation.scope,
            eliminated=tuple(sorted(eliminated_now)),
            note=note,
        )
        return EvidenceState(
            candidates=self.candidates - eliminated_now,
            eliminated=self.eliminated | eliminated_now,
            updates=self.updates + (record,),
            independent_source_clusters=clusters,
        )

    @property
    def resolved(self) -> bool:
        return len(self.candidates) == 1

    @property
    def exhausted(self) -> bool:
        """No registered explanation is compatible; the explanation set is insufficient."""

        return not self.candidates

    @property
    def still_ambiguous(self) -> bool:
        return len(self.candidates) > 1

    def mechanism_updates(self) -> tuple[UpdateRecord, ...]:
        return tuple(item for item in self.updates if item.scope is EvidenceScope.MECHANISM_CONTRAST)


class InterpretationTable:
    """Apply registered ``rho`` rules to a real result under explicit conditions."""

    def __init__(
        self,
        rules: Sequence[OutcomeRule] = (),
        *,
        time_tolerance_hours: float = 1.0,
        require_context_match: bool = True,
    ):
        if not _finite_number(time_tolerance_hours) or time_tolerance_hours < 0:
            raise ValueError("time_tolerance_hours must be finite and nonnegative.")
        self._rules = tuple(rules)
        self._time_tolerance = time_tolerance_hours
        self._require_context_match = require_context_match

    @property
    def rules(self) -> tuple[OutcomeRule, ...]:
        return self._rules

    def interpret(
        self,
        observation: ObservationRecord,
        contrast: MechanismContrast,
        profile: FunctionalInterventionProfile,
        plan: EvidenceAction | None = None,
        *,
        prior_evidence: Sequence[MeasuredPremise] = (),
    ) -> OutcomeInterpretation:
        """Classify a result without promoting it beyond what its conditions support."""

        if observation.quality_passed is not True:
            return OutcomeInterpretation(
                outcome_class=OutcomeClass.QUALITY_FAILED,
                scope=EvidenceScope.MEASUREMENT_FEASIBILITY,
                rule_identifier=None,
                outcome_label="quality_failed",
                eliminates=frozenset(),
                conditions_matched=False,
                unmatched_conditions=("quality_passed",),
                rationale="The record failed its declared quality check.",
                boundary="A failed measurement updates detection feasibility only; it is retained without constraining the mechanism.",
            )
        if observation.evidence_kind is not EvidenceKind.REAL_MEASUREMENT:
            return OutcomeInterpretation(
                outcome_class=OutcomeClass.NON_MEASUREMENT,
                scope=EvidenceScope.PLAN_LIMITATION,
                rule_identifier=None,
                outcome_label="non_measurement_record",
                eliminates=frozenset(),
                conditions_matched=False,
                unmatched_conditions=(f"evidence_kind={observation.evidence_kind.value}",),
                rationale="Only a real measurement can constrain a mechanism contrast.",
                boundary="A derived or predicted record keeps its declared limitations and cannot update the contrast.",
            )

        rule = self._matching_rule(observation)
        if rule is None:
            fields = tuple(observation.interpretation_fields)
            unresolved = bool(fields)
            return OutcomeInterpretation(
                outcome_class=OutcomeClass.OUT_OF_PREDICTION if unresolved else OutcomeClass.AMBIGUOUS,
                scope=EvidenceScope.PLAN_LIMITATION,
                rule_identifier=None,
                outcome_label="unregistered_outcome",
                eliminates=frozenset(),
                conditions_matched=True,
                unmatched_conditions=(),
                rationale=(
                    "A qualified result does not match any registered outcome category."
                    if unresolved
                    else "The result declares no interpretation field, so it cannot be tied to a mechanism variable."
                ),
                boundary=(
                    "Unregistered qualified results require revising the explanation set; they are not forced into an existing hypothesis."
                    if unresolved
                    else "An uninterpreted result is kept as evidence but cannot remove an explanation."
                ),
            )

        plan = plan or next(
            (item for item in contrast.actions() if item.identifier == observation.action_identifier), None
        )
        authorized = tuple(dict.fromkeys(
            name for name in observation.interpretation_fields
            if name in rule.matched_fields or any(name.startswith(prefix) for prefix in rule.required_prefixes)
        ))
        unmatched = list(self._unmatched_conditions(observation, profile, plan, rule))
        if plan is None or plan.identifier != observation.action_identifier:
            unmatched.append("action:unregistered_or_mismatched")
        else:
            if rule.allowed_action_kinds and plan.kind not in rule.allowed_action_kinds:
                unmatched.append(f"action_kind:{plan.kind.value}")
            if plan.supplies:
                unmatched.extend(f"field_not_supplied:{name}" for name in authorized if name not in plan.supplies)
            for requirement in rule.field_requirements:
                grant = _grant_for(plan, observation, requirement.field)
                unmatched.extend(
                    f"field:{requirement.field}:{reason}" for reason in requirement.unmet_reasons(grant)
                )
            if plan.quantity_is_estimated:
                unmatched.append("estimate_offered_for_direct_measurement")
        if rule.scope is EvidenceScope.MECHANISM_CONTRAST and not _valid_units(
            observation.independent_units, minimum=rule.minimum_independent_units
        ):
            unmatched.append("independent_units:insufficient_or_unknown")
        for name, (low, high) in rule.metric_bounds.items():
            raw = getattr(observation, "metrics", {}).get(name)
            try:
                value = float(raw) if not isinstance(raw, bool) else float("nan")
            except (TypeError, ValueError, OverflowError):
                value = float("nan")
            if not math.isfinite(value):
                unmatched.append(f"metric:{name}:missing_or_nonfinite")
            elif (low is not None and value < low) or (high is not None and value > high):
                unmatched.append(f"metric:{name}:outside_registered_bounds")
        supporting, premise_problems = self._supporting_evidence(observation, rule, prior_evidence)
        unmatched.extend(premise_problems)
        if unmatched:
            return OutcomeInterpretation(
                outcome_class=OutcomeClass.CONDITION_UNMATCHED,
                scope=EvidenceScope.PLAN_LIMITATION,
                rule_identifier=rule.identifier,
                outcome_label=rule.outcome_label,
                eliminates=frozenset(),
                conditions_matched=False,
                unmatched_conditions=tuple(dict.fromkeys(unmatched)),
                rationale="The rule matched but its measurement or biological evidence conditions are not satisfied.",
                boundary=rule.boundary
                or "An unmatched condition limits the result to a plan-level limitation; the mechanism contrast is unchanged.",
                refused_fields=tuple(observation.interpretation_fields),
            )

        return OutcomeInterpretation(
            outcome_class=OutcomeClass.PREDICTED,
            scope=rule.scope,
            rule_identifier=rule.identifier,
            outcome_label=rule.outcome_label,
            eliminates=frozenset(rule.eliminates),
            conditions_matched=True,
            unmatched_conditions=(),
            rationale=f"Rule '{rule.identifier}' ({rule.outcome_label}) is satisfied.",
            boundary=rule.boundary
            or "The result constrains only the hypotheses named by the matched rule.",
            authorized_fields=authorized,
            refused_fields=tuple(name for name in observation.interpretation_fields if name not in authorized),
            supporting_result_ids=tuple(dict.fromkeys(item.result_id for item in supporting)),
            supporting_fields=tuple(dict.fromkeys(item.grant.field for item in supporting)),
        )

    def _supporting_evidence(
        self,
        observation: ObservationRecord,
        rule: OutcomeRule,
        evidence: Sequence[MeasuredPremise],
    ) -> tuple[tuple[MeasuredPremise, ...], tuple[str, ...]]:
        """Match each required earlier assay on its own coordinates, without imputation.

        Unless the reviewed requirement explicitly declares a different time,
        measurements must occupy the same time window. Cross-assay exposure,
        sample or intervention identity is checked on the keys the rule declares.
        """

        selected: list[MeasuredPremise] = []
        problems: list[str] = []
        for requirement in rule.evidence_requirements:
            candidates = [item for item in evidence if item.grant.field == requirement.field]
            valid: list[MeasuredPremise] = []
            failures: list[tuple[str, ...]] = []
            for item in candidates:
                reasons = list(requirement.unmet_reasons(item.grant))
                if scope_rank(item.scope) < scope_rank(EvidenceScope.INTERVENTION_IMPLEMENTATION):
                    reasons.append("scope:measurement_not_admitted")
                if not _valid_units(item.independent_units, minimum=rule.minimum_independent_units):
                    reasons.append("independent_units:insufficient_or_unknown")
                if not item.result_id or not item.grant.provenance:
                    reasons.append("lineage:undeclared")
                if item.result_id == observation.result_id:
                    reasons.append("earlier_measurement_required")
                if not observation.context_identifier or item.grant.context_identifier != observation.context_identifier:
                    reasons.append("context:unmatched")
                if requirement.time_hours is None:
                    expected, observed = observation.time_hours, item.grant.time_hours
                    if not _finite_number(expected) or not _finite_number(observed):
                        reasons.append("time:unspecified")
                    elif abs(expected - observed) > self._time_tolerance:
                        reasons.append("time:unmatched")
                for key in rule.matched_condition_keys:
                    if key not in observation.conditions or key not in item.conditions:
                        reasons.append(f"condition:{key}:undeclared")
                    elif item.conditions[key] != observation.conditions[key]:
                        reasons.append(f"condition:{key}:unmatched")
                failures.append(tuple(reasons))
                if not reasons:
                    valid.append(item)
            if valid:
                selected.append(valid[-1])
            else:
                detail = ",".join(min(failures, key=len)) if failures else "not_measured"
                problems.append(f"evidence:{requirement.field}:{detail}")
        return tuple(selected), tuple(problems)

    def _matching_rule(self, observation: ObservationRecord) -> OutcomeRule | None:
        for rule in self._rules:
            if rule.matches(observation):
                return rule
        return None

    def _unmatched_conditions(
        self,
        observation: ObservationRecord,
        profile: FunctionalInterventionProfile,
        plan: EvidenceAction | None,
        rule: OutcomeRule,
    ) -> tuple[str, ...]:
        unmatched: list[str] = []
        expected_context = (
            plan.execution_context or (profile.context_identifier if plan.context_bound else None)
            if plan is not None else profile.context_identifier
        )
        if self._require_context_match and expected_context:
            if expected_context != observation.context_identifier:
                unmatched.append(f"context:{expected_context}!={observation.context_identifier}")
        if plan is not None:
            for key, expected in plan.expected_conditions.items():
                if observation.conditions.get(key) != expected:
                    unmatched.append(f"condition:{key}:unmatched")
        for key in sorted(rule.required_conditions):
            if key not in observation.conditions:
                unmatched.append(f"condition:{key}")
        fields = tuple(observation.interpretation_fields)
        for prefix in sorted(rule.required_prefixes):
            if not any(field.startswith(prefix) for field in fields):
                unmatched.append(f"field_prefix:{prefix}")
        if rule.requires_time_match:
            expected = plan.time_hours if plan is not None else None
            observed = observation.time_hours
            if not _finite_number(expected) or not _finite_number(observed):
                unmatched.append("time:unspecified")
            elif abs(expected - observed) > self._time_tolerance:
                unmatched.append(f"time:{observed}!={expected}")
        return tuple(unmatched)


def _finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _valid_units(value: object, *, minimum: int = 1) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _grant_for(action: EvidenceAction | None, observation: ObservationRecord, name: str) -> PremiseGrant:
    """The producing assay, not a free-text field, defines the biological quantity."""

    return PremiseGrant(
        field=name,
        source_action=observation.action_identifier,
        quantity=action.quantity if action is not None else BiologicalQuantity.UNSPECIFIED,
        is_estimate=action.quantity_is_estimated if action is not None else False,
        entity=action.entity if action is not None else None,
        site=action.site if action is not None else None,
        units=action.units if action is not None else None,
        context_identifier=observation.context_identifier,
        time_hours=observation.time_hours,
        quality="passed" if observation.quality_passed else "failed",
        quality_passed=observation.quality_passed and observation.evidence_kind is EvidenceKind.REAL_MEASUREMENT,
        provenance=observation.source_id,
    )


INCOMPLETE_PERTURBATION_FACTOR = "incomplete_perturbation"
"""The causal factor a case must register explicitly before it can be removed."""

PHENOTYPE_FIELD_PREFIX = "phenotype:"
MODE_COMPARATOR_FIELD = "mode:matched_comparator:measured"
MODE_DIFFERENCE_FIELD = "mode:matched_comparator:discordant"
REALISATION_FIELD = "functional:target_activity:insufficient"
SUFFICIENT_FUNCTION_FIELD = "functional:target_activity:sufficient"


def default_rules_for(contrast: MechanismContrast) -> tuple[OutcomeRule, ...]:
    """A conservative starting ``rho`` for a two-hypothesis contrast.

    The factor that explains a discordant phenotype by incomplete intervention
    realisation is **not** inferred from ``proposed_action``: a case has to
    register it with ``MechanismHypothesis.causal_factor``.  When nothing is
    registered, the sufficient-function rules remove nothing and the pair stays
    open, because retiring an explanation needs a declared causal factor rather
    than a plan label.

    A sufficient-function measurement can unlock a dependent assay, but cannot
    retire a mechanism on its own. The default comparison needs a separately
    admitted proximal measurement plus a discordant, measured viability
    comparator in the same context/time window. The two assays keep separate
    quantities, scopes and source identifiers. Callers must register reviewed
    dose/sample/intervention matching, thresholds and cross-time support before
    drawing biological conclusions.
    """

    eliminates = frozenset(
        hypothesis.identifier
        for hypothesis in contrast.hypotheses
        if hypothesis.causal_factor == INCOMPLETE_PERTURBATION_FACTOR
    )
    return (
        OutcomeRule(
            identifier="functional_insufficient",
            outcome_label="functional_perturbation_insufficient",
            matched_fields=frozenset({REALISATION_FIELD}),
            eliminates=frozenset(),
            scope=EvidenceScope.INTERVENTION_IMPLEMENTATION,
            allowed_action_kinds=frozenset({EvidenceActionKind.FUNCTIONAL_MEASUREMENT}),
            field_requirements=(PremiseRequirement(REALISATION_FIELD, BiologicalQuantity.PROXIMAL_ACTIVITY),),
            boundary=(
                "An insufficient-perturbation result constrains intervention implementation; "
                "it does not refute the competing explanation or the target mechanism."
            ),
        ),
        OutcomeRule(
            identifier="functional_sufficient_mode_matched",
            outcome_label="functional_perturbation_sufficient_with_matched_mode",
            matched_fields=frozenset({MODE_COMPARATOR_FIELD, MODE_DIFFERENCE_FIELD, "phenotype:viability:unaffected"}),
            forbidden_fields=frozenset({REALISATION_FIELD}),
            eliminates=eliminates,
            scope=EvidenceScope.MECHANISM_CONTRAST,
            requires_time_match=True,
            allowed_action_kinds=frozenset({EvidenceActionKind.MODE_MATCHED_COMPARATOR}),
            field_requirements=(PremiseRequirement(MODE_COMPARATOR_FIELD, BiologicalQuantity.VIABILITY),),
            evidence_requirements=(PremiseRequirement(SUFFICIENT_FUNCTION_FIELD, BiologicalQuantity.PROXIMAL_ACTIVITY),),
            boundary=(
                "Retiring the realisation explanation requires a separately admitted proximal-function "
                "measurement and a discordant mode-matched viability comparator, not merely a label "
                "saying a comparison was measured. The default bridge is same-context/same-time only; "
                "dose, intervention and sample identity must be declared by reviewed case-specific rules."
            ),
        ),
        OutcomeRule(
            identifier="functional_sufficient_without_mode_match",
            outcome_label="functional_perturbation_sufficient",
            matched_fields=frozenset({SUFFICIENT_FUNCTION_FIELD}),
            forbidden_fields=frozenset({REALISATION_FIELD, MODE_COMPARATOR_FIELD}),
            eliminates=frozenset(),
            scope=EvidenceScope.INTERVENTION_IMPLEMENTATION,
            requires_time_match=True,
            allowed_action_kinds=frozenset({EvidenceActionKind.FUNCTIONAL_MEASUREMENT}),
            field_requirements=(PremiseRequirement(SUFFICIENT_FUNCTION_FIELD, BiologicalQuantity.PROXIMAL_ACTIVITY),),
            boundary=(
                "The measured proximal-function field may unlock a dependent assay without an "
                "invented phenotype. It does not retire a mechanism, establish a mode difference, "
                "or license a mode-change decision on its own."
            ),
        ),
        OutcomeRule(
            identifier="condition_mismatch",
            outcome_label="condition_match_unsatisfied",
            matched_fields=frozenset({"mechanism:condition_matched:unsatisfied"}),
            eliminates=frozenset(),
            scope=EvidenceScope.PLAN_LIMITATION,
            boundary="A declared condition mismatch blocks mechanism attribution; it is not evidence for any explanation.",
        ),
    )
