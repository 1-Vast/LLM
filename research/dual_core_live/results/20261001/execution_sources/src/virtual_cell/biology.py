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
- Depends on: maestro.models, virtual_cell.applicability
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field, replace
from enum import Enum
from math import log2
from pathlib import Path
from statistics import fmean, pstdev
from typing import Callable, Iterable, Mapping, Sequence

from maestro.models import BiologicalQuantity, MeasurementStatus, PremiseGrant

from .applicability import ValidationReceipt


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


@dataclass(frozen=True)
class GeneSet:
    """A declared set of genes, identified by what it actually contains.

    ``source`` and ``source_sha256`` record where membership came from, so a
    Reactome-derived set and a hand-frozen panel are distinguishable, and a
    later release cannot change an endpoint without changing its digest.
    """

    identifier: str
    members: tuple[str, ...]
    source: str
    source_sha256: str
    rule: str
    restricted_from: str | None = None

    @property
    def digest(self) -> str:
        """SHA-256 over the identifier and the sorted membership.

        Order is not part of the definition, so two spellings of one set agree;
        a restriction drops members and therefore changes the digest, which is
        what makes a restricted endpoint visibly different from the declared one.
        """

        payload = self.identifier + "\n" + "\n".join(sorted(self.members))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @property
    def size(self) -> int:
        return len(self.members)

    def restricted_to(self, available: Mapping[str, float] | Iterable[str]) -> tuple["GeneSet", tuple[str, ...]]:
        """Return the set restricted to available genes, plus the dropped members."""

        names = set(available)
        present = tuple(member for member in self.members if member in names)
        missing = tuple(member for member in self.members if member not in names)
        return replace(self, members=present, restricted_from=self.digest), missing


def score_gene_set(values: Mapping[str, float], gene_set: GeneSet) -> float:
    """Mean value over the set's members, refusing an undeclared restriction."""

    if not gene_set.members:
        raise ValueError(f"gene set '{gene_set.identifier}' has no members to score")
    missing = [member for member in gene_set.members if member not in values]
    if missing:
        raise ValueError(
            f"gene set '{gene_set.identifier}' has {len(missing)} member(s) absent from the supplied values "
            f"({', '.join(missing[:5])}); call restricted_to() to declare the restriction explicitly"
        )
    return float(fmean(float(values[member]) for member in gene_set.members))


@dataclass(frozen=True)
class BackgroundPool:
    """The declared gene pool a size-matched background is drawn from.

    The pool decides the answer. Drawing from whatever genes happen to be present in
    the supplied values makes a declared set containing undetected members *not*
    size-matched against its own background, and the resulting z is then a function of
    an undeclared sampling choice rather than of the data. So the pool is a first-class
    artefact with its own digest: two runs that disagree must disagree visibly.
    """

    identifier: str
    members: tuple[str, ...]
    source: str
    source_sha256: str
    rule: str

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("A background pool needs an identifier.")
        if not self.members:
            raise ValueError(f"Background pool '{self.identifier}' has no members.")
        if not self.source.strip() or not self.source_sha256.strip():
            raise ValueError(
                f"Background pool '{self.identifier}' must name its source and that source's digest; "
                "an undeclared pool is indistinguishable from the caller's own choice."
            )

    @property
    def digest(self) -> str:
        """SHA-256 over the identifier and the sorted membership, as for a gene set."""

        payload = self.identifier + "\n" + "\n".join(sorted(self.members))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @property
    def size(self) -> int:
        return len(self.members)

    def usable_for(self, values: Mapping[str, float], gene_set: GeneSet) -> tuple[str, ...]:
        """Why this pool cannot supply a background here, named individually."""

        problems: list[str] = []
        available = [member for member in self.members if member in values]
        if len(available) < gene_set.size:
            problems.append(
                f"background_pool_smaller_than_the_gene_set:{len(available)}<{gene_set.size}"
            )
        absent = self.size - len(available)
        if absent:
            problems.append(f"background_members_absent_from_the_values:{absent}_of_{self.size}")
        return tuple(problems)


@dataclass(frozen=True)
class StandardisedScore:
    """A set score beside the background of size-matched random sets."""

    raw: float
    z: float
    background_mean: float
    background_sd: float
    background_draws: int
    gene_set_digest: str
    background_pool_size: int
    background_pool_id: str = ""
    background_pool_digest: str = ""
    background_members_absent_from_the_values: int = 0


def standardised_score(
    values: Mapping[str, float],
    gene_set: GeneSet,
    *,
    draws: int = 1000,
    seed: int = 0,
    background: "BackgroundPool | Sequence[str] | None" = None,
) -> StandardisedScore:
    """Score a set against size-matched random sets drawn from a **declared** pool.

    Standardising against random sets of the same size is what keeps a large set, or a
    set of highly expressed genes, from producing an effect by construction. The pool is
    required, not optional: falling back to the supplied values was a silent sampling
    choice, and a declared set containing undetected members was then compared against a
    background that could not contain them. A caller with no pool is refused by name.
    """

    raw = score_gene_set(values, gene_set)
    if background is None:
        # Fail closed. A guard that passes when nothing is declared is not a guard.
        raise ValueError(
            f"background_pool_not_declared: gene set '{gene_set.identifier}' cannot be "
            "standardised without a declared background pool; pass a BackgroundPool so the "
            "sampling frame is auditable and carries a digest."
        )
    pool_id = ""
    pool_digest = ""
    absent = 0
    if isinstance(background, BackgroundPool):
        problems = background.usable_for(values, gene_set)
        blocking = [item for item in problems if item.startswith("background_pool_smaller")]
        if blocking:
            raise ValueError(
                f"background pool '{background.identifier}' cannot supply size-matched sets: "
                + ", ".join(problems)
            )
        pool_id, pool_digest = background.identifier, background.digest
        absent = background.size - len([item for item in background.members if item in values])
        members: Sequence[str] = [item for item in background.members if item in values]
    else:
        members = background
    pool = sorted(members)
    if len(pool) < gene_set.size:
        raise ValueError(
            f"background pool of {len(pool)} genes cannot supply size-matched sets of {gene_set.size}"
        )
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        chosen = rng.sample(pool, gene_set.size)
        samples.append(fmean(float(values[name]) for name in chosen))
    mean = float(fmean(samples))
    spread = float(pstdev(samples))
    z = 0.0 if spread == 0.0 else (raw - mean) / spread
    return StandardisedScore(
        raw=raw,
        z=float(z),
        background_mean=mean,
        background_sd=spread,
        background_draws=draws,
        gene_set_digest=gene_set.digest,
        background_pool_size=len(pool),
        # The sampling frame travels with the z. Without these three fields a reader
        # cannot tell which declared pool produced the number, and the pool digest is
        # what makes two disagreeing runs visibly disagree.
        background_pool_id=pool_id,
        background_pool_digest=pool_digest,
        background_members_absent_from_the_values=absent,
    )


def load_background_pool(path: Path | str) -> BackgroundPool:
    """Read a digested background-pool artefact, refusing one that does not match itself.

    The artefact is the form a pool travels in between runs: it carries its own digest
    over the sorted membership, so a pool that was edited after declaration is refused
    by name rather than silently re-standardising every endpoint its consumer scores.
    """

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "maestro.background_pool.v1":
        raise ValueError(
            f"background_pool_not_declared: {path} is not a maestro.background_pool.v1 artefact"
        )
    members = payload.get("members")
    if not isinstance(members, list) or not members:
        raise ValueError(f"background pool artefact {path} does not list its members")
    pool = BackgroundPool(
        identifier=str(payload.get("identifier", "")),
        members=tuple(str(member) for member in members),
        source=str(payload.get("source", "")),
        source_sha256=str(payload.get("source_sha256", "")),
        rule=str(payload.get("rule", "")),
    )
    recorded = str(payload.get("digest", ""))
    if recorded != pool.digest:
        raise ValueError(
            f"background pool artefact {path} does not match its recorded digest "
            f"(recorded {recorded}, observed {pool.digest})"
        )
    return pool


def pathway_observable(
    gene_set: GeneSet,
    *,
    context_identifier: str | None,
    time_hours: float | None,
    measured: bool = True,
    units: str = "log1p_normalised_count_shift",
    assay: str = "scrnaseq_pseudobulk",
) -> Observable:
    """Type a gene-set score as what it is: RNA abundance of a declared set."""

    return Observable(
        name=f"pathway_shift:{gene_set.identifier}",
        quantity=BiologicalQuantity.RNA_ABUNDANCE,
        entity=f"gene_set:{gene_set.identifier}",
        units=units,
        assay=assay,
        measurement_model=MeasurementModel(
            observation="mean over member genes of the condition mean minus the vehicle mean",
            noise="normal",
            aggregation="mean over declared gene-set members",
        ),
        context_identifier=context_identifier,
        time_hours=time_hours,
        measured=measured,
        limitations=(
            "transcriptional proxy for pathway activity, not a phosphorylation or enzymatic measurement",
            f"gene_set_digest:{gene_set.digest}",
        ),
    )


@dataclass(frozen=True)
class ExpressivityAudit:
    """Whether an output coordinate space can represent a declared endpoint."""

    gene_set_id: str
    gene_set_digest: str
    total_members: int
    representable: int
    missing_members: tuple[str, ...]
    coordinate_space: str = ""

    @property
    def fraction(self) -> float:
        return 0.0 if self.total_members == 0 else self.representable / self.total_members

    @property
    def verdict(self) -> str:
        if self.total_members and self.representable == self.total_members:
            return "expressible"
        if self.representable == 0:
            return "not_expressible"
        return "partially_expressible"

    @property
    def applicability_reason(self) -> str | None:
        """A named reason a backend cannot serve this endpoint, or None."""

        if self.verdict == "expressible":
            return None
        return f"endpoint_not_representable_in_output_space:{self.gene_set_id}"


def expressivity_audit(
    gene_set: GeneSet, coordinate_names: Iterable[str], *, coordinate_space: str = ""
) -> ExpressivityAudit:
    """Compare a declared endpoint with the coordinates a backend actually emits."""

    names = {name for name in coordinate_names if name}
    representable = [member for member in gene_set.members if member in names]
    missing = tuple(member for member in gene_set.members if member not in names)
    return ExpressivityAudit(
        gene_set_id=gene_set.identifier,
        gene_set_digest=gene_set.digest,
        total_members=gene_set.size,
        representable=len(representable),
        missing_members=missing,
        coordinate_space=coordinate_space,
    )
