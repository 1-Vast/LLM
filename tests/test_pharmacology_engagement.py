"""Regression tests for exposure-matched target engagement from competition binding.

File summary
- Path: tests/test_pharmacology_engagement.py
- Purpose: pin what a measured affinity may and may not license when it is used to
  describe engagement at the exposure an experiment actually used.
- Core points:
  - Occupancy is arithmetic on a measured affinity, not an assertion about a cell:
    the estimate carries the lysate it was measured in and stays an estimate.
  - A foreign-context estimate never discharges a premise that requires measured
    engagement in the query context; the reasons are named individually.
  - A missing affinity is missing: it is reported, never imputed.
  - Polypharmacology is a property of the exposure, not of the compound label.
- Interfaces: pytest test functions
- Depends on: maestro.pharmacology, maestro.models
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from maestro.models import BiologicalQuantity, PremiseRequirement
from maestro.pharmacology import (
    BindingMeasurement,
    ExposureCondition,
    engagement_profile,
    occupancy_from_kd,
)


# Values are the locally recorded Klaeger 2017 apparent Kd for gefitinib, which
# is the worked example in the pre-registration. They are fixture inputs here,
# not a biological claim of this test.
GEFITINIB = (
    BindingMeasurement("Gefitinib", "EGFR", 413.3, confidence="High confidence", source_id="klaeger2017"),
    BindingMeasurement("Gefitinib", "RIPK2", 903.5, confidence="High confidence", source_id="klaeger2017"),
    BindingMeasurement("Gefitinib", "GAK", 950.8, confidence="High confidence", source_id="klaeger2017"),
    BindingMeasurement("Gefitinib", "MET", 4371.6, confidence="High confidence", source_id="klaeger2017"),
    BindingMeasurement("Gefitinib", "ACAD10", 33794.9, confidence="Low confidence", source_id="klaeger2017"),
)


def _condition(dose_uM: float) -> ExposureCondition:
    return ExposureCondition(
        compound="Gefitinib",
        nominal_dose_uM=dose_uM,
        exposure_hours=24.0,
        context_identifier="NCI-H596",
    )


def test_occupancy_is_the_langmuir_relation_on_a_measured_affinity():
    assert occupancy_from_kd(100.0, 100.0) == pytest.approx(0.5)
    assert occupancy_from_kd(100.0, 0.0) == pytest.approx(0.0)
    assert occupancy_from_kd(100.0, 900.0) == pytest.approx(0.9)
    assert occupancy_from_kd(1.0, 1000.0) > occupancy_from_kd(1000.0, 1000.0)


def test_a_missing_affinity_is_reported_and_never_imputed():
    unmeasured = BindingMeasurement("Gefitinib", "ERBB2", None, source_id="klaeger2017")
    assert unmeasured.occupancy(5000.0) is None
    assert "apparent_kd_missing" in unmeasured.problems()
    profile = engagement_profile([unmeasured], _condition(5.0), designated_targets=("ERBB2",))
    assert profile.designated_occupancy is None
    assert "designated_target_affinity_missing:ERBB2" in profile.problems


def test_the_same_compound_is_selective_at_one_exposure_and_not_at_another():
    low = engagement_profile(GEFITINIB, _condition(0.05), designated_targets=("EGFR",))
    high = engagement_profile(GEFITINIB, _condition(5.0), designated_targets=("EGFR",))

    assert low.designated_occupancy == pytest.approx(0.108, abs=0.01)
    assert low.occupied_targets == ()
    assert high.designated_occupancy == pytest.approx(0.924, abs=0.01)
    assert {target for target, _ in high.occupied_targets} == {"EGFR", "RIPK2", "GAK", "MET"}
    assert not high.selective
    assert high.strongest_off_target[0] in {"RIPK2", "GAK"}


def test_engagement_from_a_foreign_lysate_does_not_discharge_an_in_context_premise():
    """The estimate is usable and scoped; it is not a measurement in this cell line."""

    profile = engagement_profile(GEFITINIB, _condition(5.0), designated_targets=("EGFR",))
    estimate = profile.estimate_for("EGFR")
    assert estimate is not None

    observable = estimate.observable()
    assert observable.quantity is BiologicalQuantity.TARGET_OCCUPANCY
    assert observable.measured is False
    assert observable.context_identifier != "NCI-H596"

    requirement = PremiseRequirement(
        field="target_engagement_confirmed",
        quantity=BiologicalQuantity.TARGET_OCCUPANCY,
        entity="EGFR",
        context_identifier="NCI-H596",
    )
    reasons = requirement.unmet_reasons(estimate.grant("target_engagement_confirmed"))
    assert "estimate_offered_for_direct_measurement" in reasons
    assert any(reason.startswith("context_mismatch") for reason in reasons)


def test_the_same_estimate_does_discharge_a_premise_that_asks_for_a_scoped_estimate():
    """A requirement written for what this evidence is must still be satisfiable."""

    profile = engagement_profile(GEFITINIB, _condition(5.0), designated_targets=("EGFR",))
    estimate = profile.estimate_for("EGFR")
    requirement = PremiseRequirement(
        field="engagement_estimated_in_lysate",
        quantity=BiologicalQuantity.TARGET_OCCUPANCY,
        entity="EGFR",
        require_direct_measurement=False,
    )
    assert requirement.unmet_reasons(estimate.grant("engagement_estimated_in_lysate")) == ()


def test_an_exposure_outside_the_measured_dose_range_is_flagged():
    measurement = BindingMeasurement(
        "Gefitinib",
        "EGFR",
        413.3,
        confidence="High confidence",
        dose_points_nM={3.0: 1.0, 30.0: 0.96, 300.0: 0.80, 3000.0: 0.40},
        source_id="klaeger2017",
    )
    inside = engagement_profile([measurement], _condition(0.5), designated_targets=("EGFR",))
    outside = engagement_profile([measurement], _condition(50.0), designated_targets=("EGFR",))
    assert "occupancy_extrapolated_beyond_measured_doses:EGFR" not in inside.problems
    assert "occupancy_extrapolated_beyond_measured_doses:EGFR" in outside.problems


def test_the_profile_reports_its_own_assumptions():
    profile = engagement_profile(GEFITINIB, _condition(5.0), designated_targets=("EGFR",))
    text = " ".join(profile.limitations).lower()
    assert "lysate" in text
    assert "nominal" in text or "free intracellular" in text
    assert profile.measured_targets == 5
