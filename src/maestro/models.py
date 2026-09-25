"""Frozen records for evidence-bounded mechanism-contrast reasoning.

File summary
- Path: src/maestro/models.py
- Purpose: Typed records that describe evidence and its limits, never a biological truth label.
- Core points:
  - Enums bind every value and scope so a model prediction never becomes a measurement.
  - `EvidenceKind` origin never becomes stronger through downstream analysis.
  - `ContrastCheck.ready_for_mechanism_update` gates any mechanism-level update.
- Interfaces: `MechanismHypothesis`, `FunctionalInterventionProfile`, `EvidenceAction`, `CompositionRule`, `GatedEvidencePlan`, `PremiseRequirement`, `PremiseGrant`, `MechanismContrast`, `ContrastCheck`, `RepairProposal`, `EvidenceObservation`, `MechanismDecision`, enums
- Depends on: (standard library only)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping


class MeasurementStatus(str, Enum):
    """How a value in an intervention profile was obtained."""

    MEASURED = "measured"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


class DevelopmentAction(str, Enum):
    """Condition-specific programme actions, rather than permanent target labels."""

    CONTINUE = "continue"
    REVISE_INTERVENTION = "revise_intervention"
    CHANGE_INTERVENTION_MODE = "change_intervention_mode"
    PRESERVE_MULTI_TARGET_ACTIVITY = "preserve_multi_target_activity"
    REMOVE_MULTI_TARGET_ACTIVITY = "remove_multi_target_activity"
    REVISE_ATTRIBUTION = "revise_attribution"
    DEFER = "defer"
    STOP = "stop"


class EvidenceActionKind(str, Enum):
    """Registered categories of measurements available to a repair step."""

    FUNCTIONAL_MEASUREMENT = "functional_measurement"
    RNA_ABUNDANCE_MEASUREMENT = "rna_abundance_measurement"
    PROTEIN_ABUNDANCE_MEASUREMENT = "protein_abundance_measurement"
    READOUT_MEASUREMENT = "readout_measurement"
    TIME_COURSE = "time_course"
    MODE_MATCHED_COMPARATOR = "mode_matched_comparator"
    ORTHOGONAL_CONTROL = "orthogonal_control"
    EVIDENCE_REVIEW = "evidence_review"


class BiologicalQuantity(str, Enum):
    """What a record actually measures.

    These are distinct quantities, not a single quality ordering. Selectivity
    is comparative across contexts or targets; viability is a distal phenotype
    and is not a better version of occupancy; RNA abundance is not a weaker
    protein measurement. The only relation the code asserts is identity:
    a requirement for one quantity is satisfied only by that quantity.

    A validated bridge model may still inform a scoped inference, but the
    bridge's output is an *estimate* and is marked as one, so it can never
    silently satisfy a requirement for a direct measurement.
    """

    RNA_ABUNDANCE = "rna_abundance"
    PROTEIN_ABUNDANCE = "protein_abundance"
    TARGET_OCCUPANCY = "target_occupancy"
    # A thermal-stability or solubility shift measures that a compound reached a protein
    # and changed its stability in cells. It is an engagement effect size, not a bound
    # fraction, so it is its own quantity: a premise asking for occupancy is not satisfied
    # by it, and neither is a premise asking for proximal pathway activity.
    ENGAGEMENT_SHIFT = "engagement_shift"
    PROXIMAL_ACTIVITY = "proximal_activity"
    VIABILITY = "viability"
    SELECTIVITY = "selectivity"
    UNSPECIFIED = "unspecified"

    def satisfies(self, required: "BiologicalQuantity") -> bool:
        """Whether a record of this quantity answers a requirement for ``required``.

        No automatic substitution in either direction: the relation is identity
        on a named quantity. ``UNSPECIFIED`` never satisfies a named requirement,
        so an untyped legacy record cannot silently pass a typed premise.
        """

        if self is BiologicalQuantity.UNSPECIFIED or required is BiologicalQuantity.UNSPECIFIED:
            return self is required
        return self is required


class NonDiscriminabilityReason(str, Enum):
    """Why a contrast cannot currently support the intended decision."""

    INSUFFICIENT_HYPOTHESES = "insufficient_hypotheses"
    NO_DISCRIMINATING_ACTION = "no_discriminating_action"
    MISSING_FUNCTIONAL_MEASUREMENT = "missing_functional_measurement"
    MISSING_PREREQUISITE = "missing_prerequisite"
    UNMATCHED_INTERVENTION_MODE = "unmatched_intervention_mode"
    MODEL_UNSUPPORTED = "model_unsupported"
    DECISION_NOT_SEPARATED = "decision_not_separated"
    INVALID_ACTION = "invalid_action"
    OUTCOME_MAPPING_UNDECLARED = "outcome_mapping_undeclared"
    OUTCOME_MAPPING_INCOMPLETE = "outcome_mapping_incomplete"
    OUTCOME_NOT_SEPARATED = "outcome_not_separated"
    MODEL_DISCRIMINATION_UNCALIBRATED = "model_discrimination_uncalibrated"


class RepairKind(str, Enum):
    """Constrained edits that can be made to a failed evidence plan."""

    ADD_FUNCTIONAL_MEASUREMENT = "add_functional_measurement"
    ADD_PREREQUISITE_MEASUREMENT = "add_prerequisite_measurement"
    CHANGE_READOUT_OR_TIME = "change_readout_or_time"
    MATCH_INTERVENTION_MODE = "match_intervention_mode"
    REMOVE_MODEL_DEPENDENCE = "remove_model_dependence"
    DEFER = "defer"


class EvidenceScope(str, Enum):
    """The only part of the reasoning state that an observation may constrain."""

    INTERVENTION_IMPLEMENTATION = "intervention_implementation"
    MEASUREMENT_FEASIBILITY = "measurement_feasibility"
    PLAN_LIMITATION = "plan_limitation"
    MECHANISM_CONTRAST = "mechanism_contrast"


class EvidenceKind(str, Enum):
    """Origin of a record; origin never becomes stronger through downstream analysis."""

    REAL_MEASUREMENT = "real_measurement"
    DERIVED_ANALYSIS = "derived_analysis"
    RETRIEVED_SOURCE = "retrieved_source"
    MODEL_PREDICTION = "model_prediction"
    PREDICTION_DERIVED_ANALYSIS = "prediction_derived_analysis"
    LEGACY_UNCLASSIFIED = "legacy_unclassified"


@dataclass(frozen=True)
class MechanismHypothesis:
    """A condition-specific explanation that remains open to refutation.

    ``causal_factor`` is an explicit registration of *which causal factor this
    explanation stands for*.  It exists so that no component has to infer a
    hypothesis's semantics from its ``proposed_action``: a plan label is a
    decision preference, not a claim about what causes the phenotype.
    """

    identifier: str
    description: str
    proposed_action: DevelopmentAction | None = None
    causal_factor: str | None = None


@dataclass(frozen=True)
class FunctionalInterventionProfile:
    """Functional semantics of an intervention, with provenance for every field.

    ``functional_states`` is deliberately a small, task-specific mapping.  A
    single residual-function scalar is not assumed to be valid for every target.
    """

    mode: str
    nominal_dose: float | None = None
    functional_states: Mapping[str, MeasurementStatus] = field(default_factory=dict)
    protein_abundance: MeasurementStatus = MeasurementStatus.UNKNOWN
    activity_spectrum: tuple[str, ...] = ()
    time_hours: float | None = None
    context_identifier: str | None = None
    source_ids: tuple[str, ...] = ()
    measured_fields: Mapping[str, MeasurementStatus] = field(default_factory=dict)

    def measurement_status(self, name: str) -> MeasurementStatus:
        """Return a field's provenance without silently treating estimates as data.

        ``functional:*`` and ``protein_abundance`` keep their dedicated slots
        because the repair rules reason about them by name. Any other
        prerequisite namespace (``abundance:``, ``attribution:``,
        ``pharmacology:`` and so on) is looked up in ``measured_fields``, so a
        case may declare a prerequisite this module does not know about without
        it silently reading as measured. An unlisted field stays UNKNOWN.
        """

        if name == "protein_abundance":
            return self.protein_abundance
        if name.startswith("functional:"):
            return self.functional_states.get(name.removeprefix("functional:"), MeasurementStatus.UNKNOWN)
        if name in self.functional_states:
            return self.functional_states[name]
        return self.measured_fields.get(name, MeasurementStatus.UNKNOWN)

    def is_measured(self, name: str) -> bool:
        """Whether a named field has a measured value; an estimate or an unknown does not."""

        return self.measurement_status(name) == MeasurementStatus.MEASURED

    def unmeasured(self, names: Iterable[str]) -> tuple[str, ...]:
        """The named fields that still lack a measurement, in the order given."""

        return tuple(name for name in names if not self.is_measured(name))

    def has_measured_function(self) -> bool:
        return any(
            status is MeasurementStatus.MEASURED
            for status in self.functional_states.values()
        )


@dataclass(frozen=True)
class EvidenceAction:
    """A registered, executable measurement and its declared interpretation scope.

    ``execution_context`` and ``context_bound`` say where the action runs.
    By default an action is executed in the case's own biological context, and
    a result from anywhere else is refused. An action that deliberately probes
    a *different* context names it in ``execution_context``; an action that
    reviews existing records across contexts sets ``context_bound`` to False
    and is planned without a context. Both keep the context check meaningful
    instead of loosening it: a cross-context review must declare itself as one.

    ``supplies`` names the prerequisite fields this action would make measured
    if it executed and returned a qualified result. It is the declaration that
    makes repair *directed*: a failed check reports which prerequisite is
    missing, and the repair selects the registered capability that supplies
    exactly that field, instead of matching on a fixed action-kind table. The
    declaration is a capability claim by the catalogue author; only a qualified
    real result can make the field measured.

    ``expected_outcomes`` maps a hypothesis identifier to the observable
    outcome this measurement is declared to produce under that hypothesis.
    It is the observation-to-decision specification: two hypotheses whose
    declared outcomes are identical cannot be called distinguishable, and an
    undeclared mapping is an unstated premise, not a validated one (audit F03).
    The declaration remains the case author's claim; only a real result can
    confirm it.

    ``detection_power`` is the declared chance that this measurement returns a
    qualified, interpretable result in this context — a property of the assay
    and the context, not a posterior over hypotheses. It exists because two
    registered assays can answer the same question at different costs while
    differing in whether they answer it at all, and a controller with no
    declared basis for that difference must fall back on price.

    ``interpretation_gate`` names the premise field without which this
    measurement runs, passes its own quality check, and still cannot move a
    mechanism belief. It is declared instead of ``prerequisites`` precisely
    because the two differ: a prerequisite makes the action illegal, a gate
    leaves it legal and makes its result uninterpretable. Only the second is the
    failure this framework is about, and a grammar that cannot say it forces
    every such case to look like a missing prerequisite.
    """

    identifier: str
    description: str
    cost: float
    distinguishes: tuple[str, ...]
    kind: EvidenceActionKind = EvidenceActionKind.READOUT_MEASUREMENT
    prerequisites: tuple[str, ...] = ()
    readout: str | None = None
    time_hours: float | None = None
    expected_conditions: Mapping[str, str] = field(default_factory=dict)
    prediction_readout: str | None = None
    prediction_relevance: float = 0.0
    source_ids: tuple[str, ...] = ()
    requires_virtual_prediction: bool = False
    expected_outcomes: Mapping[str, str] = field(default_factory=dict)
    supplies: tuple[str, ...] = ()
    execution_context: str | None = None
    context_bound: bool = True
    quantity: BiologicalQuantity = BiologicalQuantity.UNSPECIFIED
    quantity_is_estimated: bool = False
    entity: str | None = None
    site: str | None = None
    units: str | None = None
    detection_power: float | None = None
    interpretation_gate: str | None = None

    def __post_init__(self) -> None:
        if self.detection_power is not None and not 0.0 < self.detection_power <= 1.0:
            raise ValueError(
                "detection_power must be in (0, 1]; an assay that cannot return a "
                "qualified result is not a registered measurement."
            )
        if self.interpretation_gate is not None and self.interpretation_gate in self.prerequisites:
            raise ValueError(
                "A field cannot be both a prerequisite and an interpretation gate: the first "
                "makes the action illegal, the second leaves it legal and uninterpretable."
            )

    @property
    def required_premises(self) -> tuple[str, ...]:
        """Every field that must be measured before this action's result can be read.

        A prerequisite makes the action illegal until measured; an interpretation
        gate leaves it legal but uninterpretable. Both are obstacles a registered
        supplier resolves, so checks and supplier chains read them together.
        """

        gate = (self.interpretation_gate,) if self.interpretation_gate is not None else ()
        return tuple(self.prerequisites) + gate

    def satisfies_direct_requirement(self, required: BiologicalQuantity) -> bool:
        """Whether this action can satisfy a requirement for a *measured* quantity.

        A bridge estimate of protein abundance is still an estimate of protein
        abundance: it may scope a downstream inference, and it keeps its
        quantity label, but it does not discharge a requirement for the direct
        measurement. That distinction is what stops an RNA-derived estimate
        from being read as a protein assay.
        """

        return self.quantity.satisfies(required) and not self.quantity_is_estimated


@dataclass(frozen=True)
class CompositionRule:
    """The registered economics under which two actions may become one plan.

    ``shared_control_saving`` is the resource that running two assays on one
    plate saves: a vehicle control, a plate, a handling step. It is a declared
    laboratory quantity, not a tuning knob, and it is reported with every
    instance that depends on it. A rule with a zero saving still composes, and
    the composition then buys nothing — which is the negative control that
    shows the separation comes from shared-control economics rather than from
    composition being named a contribution.
    """

    identifier: str
    shared_control_saving: float
    max_components: int = 2
    note: str = ""

    def composed_cost(self, components: "tuple[EvidenceAction, ...]") -> float:
        """Cost of the composed object, floored at zero and never above the sum.

        The composed object is cheaper than the parts because it shares a
        control, never because a discount was invented for it; a saving that
        would make the object free is refused rather than silently applied.
        """

        total = sum(component.cost for component in components)
        if self.shared_control_saving < 0:
            raise ValueError("A composition rule cannot have a negative shared-control saving.")
        if self.shared_control_saving >= total:
            raise ValueError("A composition rule cannot make a plan cost-free.")
        return total - self.shared_control_saving


@dataclass(frozen=True)
class PlanAuthorization:
    """The declared entitlement a composed plan relies on, with its scope and its expiry.

    ``scope`` is the only layer of the reasoning state the gate's result may
    constrain. A functional premise licenses an intervention-implementation
    update; anything else licenses measurement feasibility. The readout's own
    update to the mechanism contrast is a separate act that needs its own
    qualified result, which is why ``provisional_until`` names one.
    """

    premise: str
    granted_by: str
    scope: EvidenceScope
    provisional_until: str
    note: str = ""


@dataclass(frozen=True)
class GatedEvidencePlan:
    """A contingent evidence plan: measure the gate, continue only if it passes.

    The gate is the action that measures the interpretation premise — the
    functional realization, occupancy or mode-comparability field without which
    the readout cannot move a mechanism belief. The readout is the measurement
    that would separate the contrast *once* that premise is measured.

    The plan is a new registered object rather than a sequence of the two
    components, for one reason that is stated rather than assumed: only a new
    object can carry the shared-control cost, and only a plan with that cost can
    be affordable under a budget that binds before the premise is resolvable.
    Its continuation is contingent, so a passing gate is a precondition of
    buying the readout and a failing gate routes to ``fallback`` instead.
    """

    identifier: str
    gate: EvidenceAction
    readout: EvidenceAction
    rule: CompositionRule
    fallback: DevelopmentAction = DevelopmentAction.REVISE_INTERVENTION
    note: str = ""

    def authorization(self) -> "PlanAuthorization":
        """What entitles this readout to be interpreted, stated rather than implied.

        A composition that merely intersects two field lists is a coincidence
        report: it says the gate happens to supply a name the readout happens to
        need. An authorization says which premise the plan is repairing, at
        which scope the gate's result may grant it, and which observation would
        confirm the grant. The last part is what keeps the authorization
        provisional: no in-loop component can certify that a measurement carries
        the quantity it claims, so the grant stands only until a qualified real
        result either carries the premise or fails to.
        """

        premise = self.readout.interpretation_gate or (
            self.readout.prerequisites[0] if self.readout.prerequisites else ""
        )
        return PlanAuthorization(
            premise=premise,
            granted_by=self.gate.identifier,
            scope=EvidenceScope.INTERVENTION_IMPLEMENTATION
            if premise.startswith("functional:")
            else EvidenceScope.MEASUREMENT_FEASIBILITY,
            provisional_until=(
                f"a qualified real result from '{self.readout.identifier}' that carries "
                f"'{premise}' in its interpretation fields at the gate's own context and time"
            ),
            note=self.note,
        )


    @property
    def components(self) -> tuple[EvidenceAction, ...]:
        return (self.gate, self.readout)

    @property
    def cost(self) -> float:
        """Cost of the plan when the gate passes and the readout is bought."""

        return self.rule.composed_cost(self.components)

    @property
    def gate_cost(self) -> float:
        """Cost of the first stage alone, which is the commitment the agent makes now."""

        return self.gate.cost

    @property
    def worst_case_cost(self) -> float:
        return self.cost

    def supplies(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(self.gate.supplies + self.readout.supplies))

    def outstanding_prerequisites(self) -> tuple[str, ...]:
        """Prerequisites the composed plan does not discharge for itself.

        The readout's prerequisites are the reason the gate exists, so the ones
        the gate supplies are removed. Whatever is left is still required
        before the plan may run, and is reported rather than assumed away.
        """

        discharged = set(self.gate.supplies)
        return tuple(name for name in self.readout.prerequisites if name not in discharged)

    def to_evidence_action(self) -> EvidenceAction:
        """Execution view of the composed plan, for the shared legality rule.

        The declared expected outcomes are the readout's, because the readout is
        what would license a mechanism update; the gate contributes premises,
        not an interpretation of the phenotype.
        """

        return EvidenceAction(
            identifier=self.identifier,
            description=f"Composed plan: {self.gate.identifier} then {self.readout.identifier}",
            cost=self.cost,
            distinguishes=self.readout.distinguishes,
            kind=self.readout.kind,
            prerequisites=self.outstanding_prerequisites(),
            readout=self.readout.readout,
            time_hours=self.readout.time_hours,
            expected_conditions=dict(self.readout.expected_conditions),
            prediction_readout=self.readout.prediction_readout,
            prediction_relevance=self.readout.prediction_relevance,
            source_ids=tuple(dict.fromkeys(self.gate.source_ids + self.readout.source_ids)),
            requires_virtual_prediction=self.readout.requires_virtual_prediction,
            expected_outcomes=dict(self.readout.expected_outcomes),
            supplies=self.supplies(),
            execution_context=self.readout.execution_context,
            context_bound=self.readout.context_bound,
            quantity=self.readout.quantity,
            quantity_is_estimated=self.readout.quantity_is_estimated,
            entity=self.readout.entity,
            site=self.readout.site,
            units=self.readout.units,
            detection_power=self.readout.detection_power,
            # The composed plan carries the gate inside itself, so its execution
            # view is interpretable and declares no external gate.
            interpretation_gate=None,
        )


@dataclass(frozen=True)
class PremiseRequirement:
    """What an interpretation field must be backed by before it counts as met.

    A prerequisite field is a *name*. The name alone carries no biological
    commitment: calling a field ``protein_present`` does not make the record
    that supplies it a protein measurement. This record is the declaration of
    what the name is required to mean, so admission can compare a claim against
    a measurement rather than comparing two strings.

    Each attribute left as ``None`` is simply not required; it is not an
    assertion that the attribute does not matter. ``require_direct_measurement``
    defaults to True because the common failure is a bridge estimate quietly
    standing in for an assay.
    """

    field: str
    quantity: BiologicalQuantity = BiologicalQuantity.UNSPECIFIED
    entity: str | None = None
    site: str | None = None
    units: str | None = None
    context_identifier: str | None = None
    time_hours: float | None = None
    time_tolerance_hours: float | None = None
    require_direct_measurement: bool = True
    note: str = ""

    @property
    def is_typed(self) -> bool:
        """Whether this requirement constrains anything beyond the field name."""

        return (
            self.quantity is not BiologicalQuantity.UNSPECIFIED
            or self.entity is not None
            or self.site is not None
            or self.units is not None
            or self.context_identifier is not None
            or self.time_hours is not None
        )

    def unmet_reasons(self, grant: "PremiseGrant") -> tuple[str, ...]:
        """Why this grant fails to discharge the requirement, named individually."""

        reasons: list[str] = []
        if grant.field != self.field:
            reasons.append(f"field_mismatch:{grant.field}!={self.field}")
        if self.quantity is not BiologicalQuantity.UNSPECIFIED and not grant.quantity.satisfies(self.quantity):
            reasons.append(f"quantity_mismatch:{grant.quantity.value}!={self.quantity.value}")
        if self.require_direct_measurement and grant.is_estimate:
            reasons.append("estimate_offered_for_direct_measurement")
        if self.entity is not None and grant.entity is not None and grant.entity != self.entity:
            reasons.append(f"entity_mismatch:{grant.entity}!={self.entity}")
        if self.entity is not None and grant.entity is None:
            reasons.append("entity_undeclared")
        if self.site is not None and grant.site != self.site:
            reasons.append(f"site_mismatch:{grant.site}!={self.site}")
        if self.units is not None and grant.units is not None and grant.units != self.units:
            reasons.append(f"units_mismatch:{grant.units}!={self.units}")
        # A required qualifier the grant does not carry is unresolved, not
        # satisfied: the record may or may not be in those units, and nothing
        # in it says which.
        if self.units is not None and grant.units is None:
            reasons.append("units_undeclared")
        if (
            self.context_identifier is not None
            and grant.context_identifier is not None
            and grant.context_identifier != self.context_identifier
        ):
            reasons.append(f"context_mismatch:{grant.context_identifier}!={self.context_identifier}")
        if self.context_identifier is not None and grant.context_identifier is None:
            reasons.append("context_undeclared")
        if self.time_hours is not None:
            if grant.time_hours is None:
                reasons.append("time_undeclared")
            elif not isinstance(grant.time_hours, (int, float)) or isinstance(grant.time_hours, bool) or not math.isfinite(grant.time_hours):
                reasons.append("time_nonfinite")
            else:
                tolerance = self.time_tolerance_hours if self.time_tolerance_hours is not None else 0.0
                if not math.isfinite(self.time_hours) or not math.isfinite(tolerance) or tolerance < 0:
                    reasons.append("invalid_required_time_window")
                elif abs(grant.time_hours - self.time_hours) > tolerance + 1e-9:
                    reasons.append(f"time_mismatch:{grant.time_hours}!={self.time_hours}")
        if not grant.quality_passed:
            reasons.append(f"quality_not_passed:{grant.quality}")
        return tuple(reasons)


@dataclass(frozen=True)
class PremiseGrant:
    """What one admitted record actually delivers for one interpretation field.

    The grant is derived from the record and from the action that produced it,
    never from the field's name. ``is_typed`` is False when the producing
    action declared no quantity, which is how a legacy untyped catalogue stays
    usable while remaining visibly untyped.
    """

    field: str
    source_action: str
    quantity: BiologicalQuantity = BiologicalQuantity.UNSPECIFIED
    is_estimate: bool = False
    entity: str | None = None
    site: str | None = None
    units: str | None = None
    context_identifier: str | None = None
    time_hours: float | None = None
    quality: str = "unknown"
    quality_passed: bool = False
    provenance: str = ""

    @property
    def is_typed(self) -> bool:
        return self.quantity is not BiologicalQuantity.UNSPECIFIED


@dataclass(frozen=True)
class MechanismContrast:
    """A pair of explanations tied to a plan and the decision it could change."""

    identifier: str
    hypotheses: tuple[MechanismHypothesis, MechanismHypothesis]
    differing_assumptions: tuple[str, ...]
    plan: EvidenceAction | None
    outcome_categories: tuple[str, ...] = ()
    interpretation_boundaries: tuple[str, ...] = ()
    additional_plans: tuple[EvidenceAction, ...] = ()

    def identifiers(self) -> frozenset[str]:
        return frozenset(hypothesis.identifier for hypothesis in self.hypotheses)

    def actions(self) -> tuple[EvidenceAction, ...]:
        """Return the explicit action bundle without treating an absent plan as executable."""

        return ((self.plan,) if self.plan is not None else ()) + self.additional_plans


@dataclass(frozen=True)
class ContrastCheck:
    """A deterministic audit of whether a plan is ready to constrain a contrast.

    The fields are deliberately separate statuses: ``executable`` and
    ``prerequisites_satisfied`` cover feasibility, ``discriminable`` is only
    syntactic label coverage, and ``outcome_separated`` records whether a
    declared observation-to-decision mapping actually separates the pair
    under the stated assumptions.  Empirical resolution is a different layer
    (``EvidenceState``); no field here claims it.
    """

    executable: bool
    prerequisites_satisfied: bool
    discriminable: bool
    decision_separating: bool
    reasons: tuple[NonDiscriminabilityReason, ...]
    missing_prerequisites: tuple[str, ...] = ()
    outcome_separated: bool = False

    @property
    def ready_for_mechanism_update(self) -> bool:
        """Only a usable, premise-satisfied and outcome-separating plan can update a contrast."""

        return (
            self.executable
            and self.prerequisites_satisfied
            and self.discriminable
            and self.decision_separating
            and self.outcome_separated
            and not self.reasons
        )


@dataclass(frozen=True)
class RepairProposal:
    """An auditable, bounded change to a failed plan, never an invented capability.

    ``promised_fields`` records which prerequisite fields this repair claims the
    replacement action would supply. It is what makes "a repair was adopted"
    separable from "a repair worked": a later qualified real result either makes
    those exact fields measured or it does not, and the ledger scores the
    promise against that observation rather than against a self-assessment.

    ``composed_plan`` is set instead of ``replacement_action`` when the repair is
    a contingent plan rather than a single registered action. The two are
    mutually exclusive by construction: a composition that merely re-listed one
    component would be a substitution wearing a plan's name.
    """

    kind: RepairKind
    replacement_action: EvidenceAction | None
    modified_fields: tuple[str, ...]
    triggered_by: tuple[NonDiscriminabilityReason, ...]
    interpretation_boundary: str
    promised_fields: tuple[str, ...] = ()
    composed_plan: GatedEvidencePlan | None = None

    def __post_init__(self) -> None:
        if self.composed_plan is not None and self.replacement_action is not None:
            raise ValueError(
                "A repair proposal carries either a replacement action or a composed plan, not both."
            )


@dataclass(frozen=True)
class EvidenceObservation:
    """A real observation whose update scope is explicit before it is interpreted."""

    action_identifier: str
    outcome: str
    scope: EvidenceScope
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...] = ()
    evidence_kind: EvidenceKind = EvidenceKind.REAL_MEASUREMENT


class DecisionStatus(str, Enum):
    DECIDED = "decided"
    NEEDS_EVIDENCE = "needs_evidence"
    CONTRADICTED = "contradicted"
    DEFERRED = "deferred"


@dataclass(frozen=True)
class MechanismDecision:
    """An evidence-bounded recommendation, never a biological conclusion."""

    status: DecisionStatus
    selected_action: EvidenceAction | None
    rationale: str
