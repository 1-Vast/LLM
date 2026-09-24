"""Exposure-matched target engagement derived from measured competition binding.

File summary
- Path: src/maestro/pharmacology.py
- Purpose: state what a measured affinity implies about target engagement at the
  exposure an experiment actually used, and keep that statement inside its
  measured scope.
- Core points:
  - Occupancy is arithmetic on a measured affinity, not an observation of the
    treated cells: the estimate carries the lysate it came from and stays an
    estimate, so it cannot discharge a premise for engagement in the query
    context while it can satisfy a premise written for a scoped estimate.
  - Selectivity is a property of the exposure, not of the compound: the same
    inhibitor can occupy one target at a low dose and several at a high one, and
    the profile reports which targets those are.
  - A missing affinity is reported by name and never imputed; an exposure
    outside the measured dose range is flagged as extrapolation.
- Interfaces: `BindingMeasurement`, `ExposureCondition`, `EngagementEstimate`,
  `EngagementProfile`, `engagement_profile`, `occupancy_from_kd`
- Depends on: maestro.models (the observable vocabulary is imported lazily, so
  this package keeps no module-level dependency on virtual_cell)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Mapping, Sequence

from .models import BiologicalQuantity, PremiseGrant

if TYPE_CHECKING:  # pragma: no cover - typing only
    from virtual_cell.biology import Observable

DEFAULT_LYSATE_CONTEXT = "kinobeads_four_cell_line_lysate_mix"
DEFAULT_ASSAY = "kinobeads_competition_binding"
OCCUPANCY_UNITS = "fraction_of_target_bound"


def occupancy_from_kd(apparent_kd_nM: float, concentration_nM: float) -> float:
    """Fractional occupancy under a one-site relation: C / (C + Kd).

    This is the standard equilibrium expression and nothing more. It assumes a
    single site, free concentration equal to the nominal one, and equilibrium at
    the time of measurement; callers record those assumptions rather than
    correcting for them.
    """

    if apparent_kd_nM <= 0.0:
        raise ValueError("an apparent Kd must be positive")
    if concentration_nM < 0.0:
        raise ValueError("a concentration cannot be negative")
    return float(concentration_nM / (concentration_nM + apparent_kd_nM))


@dataclass(frozen=True)
class BindingMeasurement:
    """One measured compound-target affinity, with the assay it came from."""

    compound: str
    target: str
    apparent_kd_nM: float | None
    assay: str = DEFAULT_ASSAY
    lysate_context: str = DEFAULT_LYSATE_CONTEXT
    confidence: str = ""
    source_id: str = ""
    dose_points_nM: Mapping[float, float] = field(default_factory=dict)

    def occupancy(self, concentration_nM: float) -> float | None:
        """Occupancy at a concentration, or None when the affinity is absent."""

        if self.apparent_kd_nM is None:
            return None
        return occupancy_from_kd(float(self.apparent_kd_nM), float(concentration_nM))

    def within_measured_doses(self, concentration_nM: float) -> bool | None:
        """Whether a concentration lies inside the measured dose range."""

        if not self.dose_points_nM:
            return None
        doses = [float(dose) for dose in self.dose_points_nM]
        return min(doses) <= float(concentration_nM) <= max(doses)

    @property
    def quality_passed(self) -> bool:
        """A high-confidence target classification is the assay's own verdict."""

        return self.confidence.strip().lower().startswith("high")

    def problems(self) -> tuple[str, ...]:
        """Why this record cannot support an occupancy statement, named individually."""

        problems: list[str] = []
        if self.apparent_kd_nM is None:
            problems.append("apparent_kd_missing")
        elif self.apparent_kd_nM <= 0.0:
            problems.append("apparent_kd_not_positive")
        if not self.source_id:
            problems.append("source_unrecorded")
        if not self.confidence:
            problems.append("target_confidence_undeclared")
        return tuple(problems)


@dataclass(frozen=True)
class ExposureCondition:
    """The exposure an experiment actually applied, in its own units."""

    compound: str
    nominal_dose_uM: float
    exposure_hours: float
    context_identifier: str

    @property
    def concentration_nM(self) -> float:
        return float(self.nominal_dose_uM) * 1000.0


@dataclass(frozen=True)
class EngagementEstimate:
    """Occupancy of one target at one exposure, with its measured scope attached."""

    measurement: BindingMeasurement
    condition: ExposureCondition
    occupancy: float
    designated: bool
    extrapolated: bool = False

    @property
    def target(self) -> str:
        return self.measurement.target

    def observable(self) -> "Observable":
        """Type this estimate in the shared observable vocabulary.

        The import is deferred: the observable vocabulary lives in the
        virtual-cell package, and the evidence core keeps no module-level
        dependency on it.
        """

        from virtual_cell.biology import MeasurementModel, Observable

        return Observable(
            name=f"target_occupancy:{self.measurement.compound}:{self.target}",
            quantity=BiologicalQuantity.TARGET_OCCUPANCY,
            entity=self.target,
            units=OCCUPANCY_UNITS,
            assay=self.measurement.assay,
            measurement_model=MeasurementModel(
                observation="C/(C+Kd_app) at the nominal exposure",
                noise="not modelled: a point estimate from a fitted affinity",
            ),
            # The context is the lysate the affinity was measured in, not the
            # cell line the exposure was applied to. Saying so is what keeps the
            # estimate from being read as engagement in the query context.
            context_identifier=self.measurement.lysate_context,
            time_hours=None,
            time_applicable=False,
            measured=False,
            limitations=(
                "affinity measured in a foreign lysate; occupancy in the query context is not measured",
                "nominal medium concentration used as free concentration",
            ),
        )

    def grant(self, field_name: str) -> PremiseGrant:
        """What this estimate delivers for one interpretation field."""

        return PremiseGrant(
            field=field_name,
            source_action=f"{self.measurement.assay}:{self.measurement.source_id or 'unrecorded'}",
            quantity=BiologicalQuantity.TARGET_OCCUPANCY,
            is_estimate=True,
            entity=self.target,
            units=OCCUPANCY_UNITS,
            context_identifier=self.measurement.lysate_context,
            time_hours=None,
            quality=self.measurement.confidence or "unknown",
            quality_passed=self.measurement.quality_passed,
            provenance=self.measurement.source_id,
        )

    def to_record(self) -> dict[str, object]:
        return {
            "compound": self.measurement.compound,
            "target": self.target,
            "designated": self.designated,
            "apparent_kd_nM": self.measurement.apparent_kd_nM,
            "nominal_dose_uM": self.condition.nominal_dose_uM,
            "concentration_nM": self.condition.concentration_nM,
            "occupancy": self.occupancy,
            "confidence": self.measurement.confidence,
            "extrapolated_beyond_measured_doses": self.extrapolated,
            "assay": self.measurement.assay,
            "lysate_context": self.measurement.lysate_context,
            "source_id": self.measurement.source_id,
        }


@dataclass(frozen=True)
class EngagementProfile:
    """Every measured target of one compound at one exposure."""

    condition: ExposureCondition
    estimates: tuple[EngagementEstimate, ...]
    designated_targets: tuple[str, ...]
    threshold: float
    measured_targets: int
    problems: tuple[str, ...]
    limitations: tuple[str, ...]

    def estimate_for(self, target: str) -> EngagementEstimate | None:
        return next((item for item in self.estimates if item.target == target), None)

    @property
    def designated_occupancy(self) -> float | None:
        """Highest occupancy among the designated targets, or None if unmeasured."""

        values = [item.occupancy for item in self.estimates if item.designated]
        return max(values) if values else None

    @property
    def occupied_targets(self) -> tuple[tuple[str, float], ...]:
        occupied = [
            (item.target, item.occupancy) for item in self.estimates if item.occupancy >= self.threshold
        ]
        return tuple(sorted(occupied, key=lambda pair: (-pair[1], pair[0])))

    @property
    def occupied_off_targets(self) -> tuple[tuple[str, float], ...]:
        return tuple(pair for pair in self.occupied_targets if pair[0] not in self.designated_targets)

    @property
    def strongest_off_target(self) -> tuple[str, float] | None:
        return self.occupied_off_targets[0] if self.occupied_off_targets else None

    @property
    def selective(self) -> bool:
        """Designated target occupied and no other measured target with it."""

        designated = self.designated_occupancy
        return designated is not None and designated >= self.threshold and not self.occupied_off_targets

    def to_record(self) -> dict[str, object]:
        return {
            "compound": self.condition.compound,
            "nominal_dose_uM": self.condition.nominal_dose_uM,
            "exposure_hours": self.condition.exposure_hours,
            "query_context": self.condition.context_identifier,
            "designated_targets": list(self.designated_targets),
            "occupancy_threshold": self.threshold,
            "designated_occupancy": self.designated_occupancy,
            "measured_targets": self.measured_targets,
            "occupied_targets": [{"target": name, "occupancy": value} for name, value in self.occupied_targets],
            "strongest_off_target": None
            if self.strongest_off_target is None
            else {"target": self.strongest_off_target[0], "occupancy": self.strongest_off_target[1]},
            "selective_at_this_exposure": self.selective,
            "problems": list(self.problems),
            "estimates": [item.to_record() for item in self.estimates],
        }


def engagement_profile(
    measurements: Sequence[BindingMeasurement],
    condition: ExposureCondition,
    *,
    designated_targets: Sequence[str] = (),
    threshold: float = 0.5,
) -> EngagementProfile:
    """Build the engagement profile of one compound at one exposure."""

    designated = tuple(designated_targets)
    concentration = condition.concentration_nM
    estimates: list[EngagementEstimate] = []
    problems: list[str] = []
    for measurement in measurements:
        occupancy = measurement.occupancy(concentration)
        if occupancy is None:
            if measurement.target in designated:
                problems.append(f"designated_target_affinity_missing:{measurement.target}")
            else:
                problems.append(f"affinity_missing:{measurement.target}")
            continue
        inside = measurement.within_measured_doses(concentration)
        if inside is None:
            problems.append(f"measured_dose_points_unavailable:{measurement.target}")
        elif not inside:
            problems.append(f"occupancy_extrapolated_beyond_measured_doses:{measurement.target}")
        estimates.append(
            EngagementEstimate(
                measurement=measurement,
                condition=condition,
                occupancy=occupancy,
                designated=measurement.target in designated,
                extrapolated=inside is False,
            )
        )
    for target in designated:
        if not any(item.target == target for item in measurements):
            problems.append(f"designated_target_not_measured:{target}")
    return EngagementProfile(
        condition=condition,
        estimates=tuple(estimates),
        designated_targets=designated,
        threshold=float(threshold),
        measured_targets=len(measurements),
        problems=tuple(dict.fromkeys(problems)),
        limitations=(
            "Affinities are competition-binding measurements in a four-cell-line lysate mix, not in the query context.",
            "Occupancy uses the nominal medium concentration as the free concentration; uptake, efflux and protein "
            "binding are unmeasured.",
            "A one-site equilibrium relation is an approximation; the measured dose points are retained for audit.",
            "Binding is not inhibition of function, and neither is evidence that a downstream pathway moved.",
        ),
    )
