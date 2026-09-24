"""Measured proximal function, typed, and the estimate it may not be replaced by.

File summary
- Path: src/maestro/engagement.py
- Purpose: carry one measured in-cell proximal-function record into the framework's premise
  admission, so a mid-chain link is a measurement with a context, a window and a vehicle
  reference rather than a binding estimate from a foreign lysate.
- Core points:
  - A record declares its own consistency: `engaged` must equal the comparison of the
    measured effect against the same-plate vehicle threshold it carries. A record that
    claims engagement its own numbers contradict is refused by name.
  - Proximal function is not occupancy. The grant is typed `PROXIMAL_ACTIVITY`, so a
    requirement for `TARGET_OCCUPANCY` is refused with a quantity mismatch rather than
    satisfied by a neighbouring quantity.
  - `lysate_estimate_grant` exists only to be refused: a competition-binding estimate in a
    foreign lysate is a scoped estimate, and the framework's own rule forbids it from
    discharging an engagement premise in the query context.
- Interfaces: `ProximalFunctionRecord`, `lysate_estimate_grant`, `FOREIGN_LYSATE_REFUSAL`
- Depends on: maestro.models
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import BiologicalQuantity, PremiseGrant

FOREIGN_LYSATE_REFUSAL = "foreign_lysate_estimate_cannot_discharge_an_engagement_premise"


@dataclass(frozen=True)
class ProximalFunctionRecord:
    """One measured proximal-function observation, in one context, at one window."""

    cell_line: str
    readout: str
    entity: str
    site: str | None
    time_hours: float
    effect_log2: float
    vehicle_null_threshold_log2: float
    engaged: bool
    source: str
    source_sha256: str
    units: str = "log2_ratio_to_vehicle"

    def problems(self) -> tuple[str, ...]:
        """Named reasons this record cannot be used as a measured engagement record."""

        issues: list[str] = []
        if not self.cell_line.strip():
            issues.append("context_undeclared")
        if not self.readout.strip() or not self.entity.strip():
            issues.append("readout_undeclared")
        if not self.source.strip() or not self.source_sha256.strip():
            issues.append("source_undeclared")
        if self.time_hours <= 0.0:
            issues.append("time_undeclared")
        expected = self.effect_log2 < self.vehicle_null_threshold_log2
        if self.engaged != expected:
            issues.append(
                "engagement_claim_contradicts_its_own_numbers:"
                f"claimed_{self.engaged}_effect_{self.effect_log2}_threshold_{self.vehicle_null_threshold_log2}"
            )
        return tuple(issues)

    def grant(self, *, field: str = "functional:pathway_activity") -> PremiseGrant:
        """The typed grant this measurement offers, refused if it contradicts itself."""

        issues = self.problems()
        if issues:
            raise ValueError(f"proximal_function_record_not_usable: {', '.join(issues)}")
        return PremiseGrant(
            field=field,
            source_action="measured_proximal_function",
            quantity=BiologicalQuantity.PROXIMAL_ACTIVITY,
            is_estimate=False,
            entity=self.entity,
            site=self.site,
            units=self.units,
            context_identifier=self.cell_line,
            time_hours=self.time_hours,
            quality=(
                "measured_effect_crosses_the_same_plate_vehicle_null"
                if self.engaged
                else "measured_effect_does_not_cross_the_same_plate_vehicle_null"
            ),
            quality_passed=True,
            provenance=f"{self.readout} in {self.cell_line} at {self.time_hours}h from {self.source}",
        )


def lysate_estimate_grant(
    *,
    field: str,
    context_identifier: str | None,
    time_hours: float | None,
    provenance: str = "",
) -> PremiseGrant:
    """An engagement grant backed by a foreign-lysate binding estimate.

    It is returned typed as an estimate so that any direct-measurement requirement refuses
    it by name (`estimate_offered_for_direct_measurement`), and it carries a named reason in
    its quality field so a reader never has to infer why it was not admitted.
    """

    return PremiseGrant(
        field=field,
        source_action="foreign_lysate_competition_binding",
        quantity=BiologicalQuantity.TARGET_OCCUPANCY,
        is_estimate=True,
        entity=None,
        units=None,
        context_identifier=context_identifier,
        time_hours=time_hours,
        quality=FOREIGN_LYSATE_REFUSAL,
        quality_passed=False,
        provenance=provenance or "competition-binding estimate in a foreign lysate",
    )
