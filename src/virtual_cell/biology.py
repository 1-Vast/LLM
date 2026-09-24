"""The shared biological vocabulary every backend is described in.

File summary
- Path: src/virtual_cell/biology.py
- Purpose: give MAESTRO one typed description of observables, interventions and
  the causal chain, so backends with different internal representations can be
  compared and composed without being equated.
- Core points:
  - Three different questions are kept apart: is this the same biological
    *quantity*, is this the same *measurement* (assay, observation function,
    measured status, context, time), and may it be admitted as a *direct
    measurement* of something a premise requires.
  - A qualifier that is missing is an unresolved condition with a name, not a
    silent pass: two records that do not say in which context or at what time
    they were taken are not known to be comparable.
  - Composition has three kinds. An identity preserves everything; a
    deterministic conversion executes a registered arithmetic map and invents no
    information; a learned or mechanistic bridge crosses quantities and needs an
    executable mapping plus a validation receipt, and its output is always an
    estimate.
- Interfaces: `Observable`, `MeasurementModel`, `InterventionComponent`,
  `CompositeIntervention`, `ChainSegment`, `ConnectorKind`, `UnitConversion`,
  `UNIT_CONVERSIONS`, `BridgeModel`, `Connector`, `BackendDescription`
- Depends on: maestro.models, virtual_cell.receipts
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import log2
from typing import Callable, Mapping

from maestro.models import BiologicalQuantity, MeasurementStatus, PremiseGrant

from .receipts import ValidationReceipt


class ChainSegment(str, Enum):
    """One link of the chain from what was intended to what was decided.

    A backend almost never spans the whole chain. Recording which segment it
    implements is what stops a transcript predictor from being read as evidence
    about a decision, and what makes a composition auditable rather than
    plausible.
    """

    INTENDED_TO_REALIZED = "intended_intervention_to_realized_perturbation"
    REALIZED_TO_RESPONSE = "realized_perturbation_to_biological_response"
    RESPONSE_TO_OBSERVATION = "biological_response_to_assay_observation"
    OBSERVATION_TO_DECISION = "assay_observation_to_decision"


@dataclass(frozen=True)
class MeasurementModel:
    """How a biological state becomes a number, in PEtab's sense.

    ``observation`` is the observation function that maps state to the reported
    value; ``noise`` is the noise model of that report. Separating them from
    the state is what lets the same underlying quantity be measured by two
    assays with different scales and error structure without either becoming
    the other.
    """

    observation: str
    noise: str
    scale: str = "linear"
    lower_detection_limit: float | None = None
    upper_detection_limit: float | None = None
    aggregation: str | None = None

    def censored(self, value: float) -> bool:
        """Whether a reported value sits at or beyond a detection limit."""

        if self.lower_detection_limit is not None and value <= self.lower_detection_limit:
            return True
        return self.upper_detection_limit is not None and value >= self.upper_detection_limit

    def differs_from(self, other: "MeasurementModel") -> bool:
        return (self.observation, self.noise, self.scale, self.aggregation) != (
            other.observation,
            other.noise,
            other.scale,
            other.aggregation,
        )


@dataclass(frozen=True)
class Observable:
    """A named measurable quantity, fully qualified.

    Total EGFR, EGFR phosphorylated at Y992, an RNA-derived pathway score and
    cell survival all mention the same gene and are four different observables.
    ``context_applicable`` and ``time_applicable`` exist so that an observable
    which genuinely has no time (an untreated baseline profile) can say so,
    instead of leaving ``time_hours`` at ``None`` and being read as unknown.
    """

    name: str
    quantity: BiologicalQuantity
    entity: str
    units: str
    assay: str
    measurement_model: MeasurementModel
    site: str | None = None
    compartment: str | None = None
    context_identifier: str | None = None
    time_hours: float | None = None
    measured: bool = True
    comparator: str | None = None
    context_applicable: bool = True
    time_applicable: bool = True
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.quantity is BiologicalQuantity.SELECTIVITY and self.comparator is None:
            # Selectivity is a comparison, so a selectivity record without a
            # comparator is incomplete rather than merely unlabelled.
            object.__setattr__(self, "limitations", self.limitations + ("selectivity_without_comparator",))

    # -- the three different questions ------------------------------------

    def quantity_mismatches(self, other: "Observable") -> tuple[str, ...]:
        """Disagreements about *what* is measured, ignoring how and where."""

        problems: list[str] = []
        if self.quantity is not other.quantity:
            problems.append("quantity_mismatch")
        if self.entity != other.entity:
            problems.append("entity_mismatch")
        if self.site != other.site:
            problems.append("site_mismatch")
        if self.compartment != other.compartment:
            problems.append("compartment_mismatch")
        if self.quantity is BiologicalQuantity.SELECTIVITY and self.comparator != other.comparator:
            problems.append("comparator_mismatch")
        return tuple(problems)

    def qualifier_mismatches(self, other: "Observable") -> tuple[str, ...]:
        """Disagreements about context, time and measured-versus-estimated status."""

        problems: list[str] = []
        if self.context_applicable != other.context_applicable:
            problems.append("context_applicability_mismatch")
        elif (
            self.context_applicable
            and self.context_identifier is not None
            and other.context_identifier is not None
            and self.context_identifier != other.context_identifier
        ):
            problems.append("context_mismatch")
        if self.time_applicable != other.time_applicable:
            problems.append("time_applicability_mismatch")
        elif (
            self.time_applicable
            and self.time_hours is not None
            and other.time_hours is not None
            and self.time_hours != other.time_hours
        ):
            problems.append("time_mismatch")
        if self.measured != other.measured:
            problems.append("measurement_status_mismatch")
        return tuple(problems)

    def unresolved_conditions(self, other: "Observable") -> tuple[str, ...]:
        """Qualifiers that apply to both but are missing on at least one side."""

        problems: list[str] = []
        if self.context_applicable and other.context_applicable:
            if self.context_identifier is None or other.context_identifier is None:
                problems.append("context_unresolved")
        if self.time_applicable and other.time_applicable:
            if self.time_hours is None or other.time_hours is None:
                problems.append("time_unresolved")
        return tuple(problems)

    def mismatches(self, other: "Observable") -> tuple[str, ...]:
        """Every disagreement between two observables, named individually."""

        problems = [*self.quantity_mismatches(other)]
        if self.units != other.units:
            problems.append("units_mismatch")
        if self.assay != other.assay:
            problems.append("assay_mismatch")
        if self.measurement_model.differs_from(other.measurement_model):
            problems.append("measurement_model_mismatch")
        problems.extend(self.qualifier_mismatches(other))
        return tuple(dict.fromkeys(problems))

    def same_quantity_as(self, other: "Observable") -> bool:
        """Whether both describe the same biological quantity of the same entity."""

        return not self.quantity_mismatches(other)

    def interchangeable_with(self, other: "Observable") -> bool:
        """Whether one record may stand in for the other with nothing left unresolved."""

        return not self.mismatches(other) and not self.unresolved_conditions(other)

    def estimate_gaps(self, requested: "Observable") -> tuple[str, ...]:
        """Why this observable cannot serve as an *estimate* of the requested one.

        Measured-versus-estimated status is deliberately excluded: a backend
        never measures, and refusing it on that ground would make every model
        ineligible for every request.
        """

        gaps = [item for item in self.mismatches(requested) if item != "measurement_status_mismatch"]
        gaps.extend(self.unresolved_conditions(requested))
        return tuple(dict.fromkeys(gaps))

    def grant_for(
        self,
        field: str,
        *,
        source_action: str,
        quality: str = "unknown",
        quality_passed: bool = False,
        provenance: str = "",
    ) -> PremiseGrant:
        """What this observable would deliver for one interpretation field.

        The grant is derived from the observable's own declarations, so premise
        admission compares a measurement against a requirement instead of
        comparing two field names. An unmeasured observable becomes an estimate
        here, which is what stops a predicted or bridged value from discharging
        a requirement for a direct measurement.
        """

        return PremiseGrant(
            field=field,
            source_action=source_action,
            quantity=self.quantity,
            is_estimate=not self.measured,
            entity=self.entity,
            site=self.site,
            units=self.units,
            context_identifier=self.context_identifier,
            time_hours=self.time_hours,
            quality=quality,
            quality_passed=quality_passed,
            provenance=provenance,
        )

    def direct_measurement_gaps(self, required: "Observable") -> tuple[str, ...]:
        """Why this observable cannot be admitted as a direct measurement of ``required``."""

        gaps: list[str] = []
        if not self.measured:
            gaps.append("estimate_offered_for_direct_measurement")
        gaps.extend(item for item in self.mismatches(required) if item != "measurement_status_mismatch")
        gaps.extend(self.unresolved_conditions(required))
        return tuple(dict.fromkeys(gaps))


@dataclass(frozen=True)
class InterventionComponent:
    """One component of an intervention, with its intent kept apart from its effect.

    ``intended_targets`` is what the experimenter meant to hit.
    ``realized_effects`` is what was actually established, each with the status
    of that establishment. A knockout that removes a scaffolding function, an
    inhibitor that leaves a protein present but inactive, and a degrader that
    removes it are three different realisations of "target X is addressed", and
    the framework records which one the evidence supports rather than assuming
    a rule per modality.
    """

    identifier: str
    modality: str
    intended_targets: tuple[str, ...] = ()
    dose: float | None = None
    dose_unit: str | None = None
    schedule: str | None = None
    exposure_hours: float | None = None
    realized_effects: Mapping[str, MeasurementStatus] = field(default_factory=dict)

    def realization_status(self, target: str) -> MeasurementStatus:
        return self.realized_effects.get(target, MeasurementStatus.UNKNOWN)

    @property
    def unverified_targets(self) -> tuple[str, ...]:
        """Intended targets whose functional realisation is not measured."""

        return tuple(
            target
            for target in self.intended_targets
            if self.realization_status(target) is not MeasurementStatus.MEASURED
        )


@dataclass(frozen=True)
class CompositeIntervention:
    """An intervention with one or more components applied to one unit."""

    identifier: str
    components: tuple[InterventionComponent, ...]
    context_identifier: str | None = None

    @property
    def is_combination(self) -> bool:
        return len(self.components) > 1

    @property
    def unverified_targets(self) -> tuple[str, ...]:
        seen: list[str] = []
        for component in self.components:
            for target in component.unverified_targets:
                if target not in seen:
                    seen.append(target)
        return tuple(seen)

    def modalities(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(component.modality for component in self.components))


class ConnectorKind(str, Enum):
    """What a connector claims to do, which decides what it must prove.

    The three are not degrees of the same thing. An identity asserts that two
    descriptions are the same measurement. A deterministic conversion executes
    a known arithmetic map and adds no information. A bridge crosses to a
    different quantity and therefore produces an estimate whose error has to
    have been measured somewhere.
    """

    IDENTITY = "identity"
    DETERMINISTIC_CONVERSION = "deterministic_conversion"
    LEARNED_BRIDGE = "learned_bridge"
    MECHANISTIC_BRIDGE = "mechanistic_bridge"


_BRIDGE_KINDS = frozenset({ConnectorKind.LEARNED_BRIDGE, ConnectorKind.MECHANISTIC_BRIDGE})


@dataclass(frozen=True)
class UnitConversion:
    """A registered, exact arithmetic map between two unit systems of one quantity."""

    identifier: str
    from_units: str
    to_units: str
    forward: Callable[[float], float]
    domain: str = ""

    def apply(self, value: float) -> float:
        return float(self.forward(float(value)))


def _log2_plus_one(value: float) -> float:
    if value < 0:
        raise ValueError("log2(x+1) is undefined for a negative abundance.")
    return log2(value + 1.0)


UNIT_CONVERSIONS: Mapping[tuple[str, str], UnitConversion] = {
    ("TPM", "log2_tpm_plus_1"): UnitConversion(
        "tpm_to_log2_tpm_plus_1", "TPM", "log2_tpm_plus_1", _log2_plus_one, domain="value >= 0"
    ),
    ("log2_tpm_plus_1", "TPM"): UnitConversion(
        "log2_tpm_plus_1_to_tpm", "log2_tpm_plus_1", "TPM", lambda value: 2.0**value - 1.0, domain="value >= 0"
    ),
    ("fraction", "percent"): UnitConversion("fraction_to_percent", "fraction", "percent", lambda value: 100.0 * value),
    ("percent", "fraction"): UnitConversion("percent_to_fraction", "percent", "fraction", lambda value: value / 100.0),
    ("nM", "uM"): UnitConversion("nanomolar_to_micromolar", "nM", "uM", lambda value: value / 1000.0),
    ("uM", "nM"): UnitConversion("micromolar_to_nanomolar", "uM", "nM", lambda value: value * 1000.0),
}


@dataclass(frozen=True)
class BridgeModel:
    """An executable mapping across quantities, identified by its artifact digest."""

    identifier: str
    artifact_sha256: str
    function: Callable[[float], float]
    input_units: str | None = None
    output_units: str | None = None

    def apply(self, value: float) -> float:
        return float(self.function(float(value)))


@dataclass(frozen=True)
class Connector:
    """A declared mapping from one observable to another.

    Composition is where unvalidated bridges get built, so what a connector must
    prove depends on what it claims. A connector that declares no kind is
    treated as an identity claim, which is the pre-typing behaviour: any
    disagreement between its ports is an error.
    """

    identifier: str
    source: Observable
    target: Observable
    segment: ChainSegment
    validation_basis: str | None = None
    independent_units: int | None = None
    limitations: tuple[str, ...] = ()
    kind: ConnectorKind | None = None
    conversion: UnitConversion | None = None
    bridge: BridgeModel | None = None
    validation: ValidationReceipt | None = None

    @property
    def effective_kind(self) -> ConnectorKind:
        return self.kind or ConnectorKind.IDENTITY

    @property
    def output_is_estimate(self) -> bool:
        """A bridge output is an estimate; so is any output declared unmeasured."""

        return self.effective_kind in _BRIDGE_KINDS or not self.target.measured

    def crossed_qualifiers(self) -> tuple[str, ...]:
        """What this connector deliberately crosses, for the audit trail."""

        return self.source.mismatches(self.target)

    def qualification_errors(self) -> tuple[str, ...]:
        problems: list[str] = []
        if self.kind is None:
            problems.extend(self.source.mismatches(self.target))
            problems.extend(self.source.unresolved_conditions(self.target))
            if not self.validation_basis:
                problems.append("no_validation_basis")
            if problems:
                problems.append("connector_kind_undeclared")
            return tuple(dict.fromkeys(problems))

        if self.kind is ConnectorKind.IDENTITY:
            problems.extend(self.source.mismatches(self.target))
            problems.extend(self.source.unresolved_conditions(self.target))
            return tuple(dict.fromkeys(problems))

        if self.kind is ConnectorKind.DETERMINISTIC_CONVERSION:
            problems.extend(self.source.quantity_mismatches(self.target))
            problems.extend(self.source.qualifier_mismatches(self.target))
            problems.extend(self.source.unresolved_conditions(self.target))
            if self.conversion is None:
                problems.append("no_registered_conversion")
            elif (self.conversion.from_units, self.conversion.to_units) != (self.source.units, self.target.units):
                problems.append("conversion_units_mismatch")
            elif UNIT_CONVERSIONS.get((self.conversion.from_units, self.conversion.to_units)) is not self.conversion:
                problems.append("conversion_not_registered")
            return tuple(dict.fromkeys(problems))

        # A bridge crosses quantities by design, so port differences are not
        # errors. What it must have is an executable mapping and a receipt.
        problems.extend(self.source.unresolved_conditions(self.target))
        if self.bridge is None:
            problems.append("no_executable_mapping")
        elif not self.bridge.artifact_sha256:
            problems.append("mapping_artifact_unhashed")
        if self.target.measured:
            problems.append("bridge_output_declared_as_measurement")
        if self.validation is None:
            problems.append("no_validation_receipt")
        else:
            problems.extend(
                self.validation.problems(
                    endpoint=self.target.name,
                    context_identifier=self.target.context_identifier,
                )
            )
            if self.validation.passed is False:
                problems.append("acceptance_not_met")
            if not self.validation.holdout_verified:
                problems.append("holdout_not_verified")
        return tuple(dict.fromkeys(problems))

    @property
    def qualified(self) -> bool:
        return not self.qualification_errors()

    def apply(self, value: float) -> float:
        """Execute the declared mapping, refusing an unqualified connector."""

        errors = self.qualification_errors()
        if errors:
            raise ValueError(f"Connector '{self.identifier}' is not qualified: {', '.join(errors)}")
        if self.effective_kind is ConnectorKind.DETERMINISTIC_CONVERSION and self.conversion is not None:
            return self.conversion.apply(value)
        if self.effective_kind in _BRIDGE_KINDS and self.bridge is not None:
            return self.bridge.apply(value)
        return float(value)


@dataclass(frozen=True)
class BackendDescription:
    """What one backend claims, in the shared vocabulary.

    This is the catalogue entry a router reads. It is a BioSimulators-style
    capability declaration rather than an execution format: the point is that
    eligibility can be decided before the model runs, and that an ineligible
    backend is named as ineligible instead of silently skipped.
    """

    name: str
    model_identifier: str
    model_version: str
    segments: tuple[ChainSegment, ...]
    observables: tuple[Observable, ...]
    supported_modalities: tuple[str, ...]
    supports_combinations: bool = False
    calibration_basis: str | None = None
    validation_domain: str | None = None
    limitations: tuple[str, ...] = ()

    def serves(self, observable: Observable) -> bool:
        return any(not candidate.estimate_gaps(observable) for candidate in self.observables)

    def serves_quantity(self, quantity: BiologicalQuantity) -> bool:
        return any(candidate.quantity is quantity for candidate in self.observables)

    def ineligibility_reasons(
        self,
        *,
        observable: Observable | None = None,
        modality: str | None = None,
        combination: bool = False,
        segment: ChainSegment | None = None,
    ) -> tuple[str, ...]:
        """Why this backend cannot answer the request, named individually."""

        problems: list[str] = []
        if observable is not None and not self.serves(observable):
            if not self.serves_quantity(observable.quantity):
                problems.append("quantity_not_served")
            else:
                gaps = [candidate.estimate_gaps(observable) for candidate in self.observables]
                closest = min(gaps, key=len) if gaps else ()
                hard = [item for item in closest if not item.endswith("_unresolved")]
                problems.append("observable_qualifier_mismatch" if hard else "observable_unresolved_qualifier")
        if modality is not None and self.supported_modalities and modality not in self.supported_modalities:
            problems.append("modality_unsupported")
        if combination and not self.supports_combinations:
            problems.append("combination_unsupported")
        if segment is not None and segment not in self.segments:
            problems.append("segment_not_implemented")
        return tuple(problems)
