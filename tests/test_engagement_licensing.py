"""Regression tests for the measured proximal-function record and its admissions.

File summary
- Path: tests/test_engagement_licensing.py
- Purpose: pin what a measured mid-chain record may and may not do at the evidence
  boundary: it discharges a proximal-function premise, it never discharges occupancy, and
  a foreign-lysate binding estimate is refused for a direct engagement requirement.
- Core points: assertions here are contract tests, not biological results.
- Interfaces: `test_a_measured_proximal_record_discharges_a_proximal_requirement()`,
  `test_proximal_function_does_not_discharge_an_occupancy_requirement()`,
  `test_a_foreign_lysate_estimate_is_refused_for_a_direct_engagement_premise()`,
  `test_a_record_that_contradicts_its_own_numbers_is_refused()`
- Depends on: maestro.engagement, maestro.models, maestro.licence
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from maestro.engagement import (
    FOREIGN_LYSATE_REFUSAL,
    ProximalFunctionRecord,
    lysate_estimate_grant,
)
from maestro.licence import issue_licence
from maestro.models import BiologicalQuantity, PremiseRequirement


def _record(**overrides) -> ProximalFunctionRecord:
    defaults = dict(
        cell_line="A2058",
        readout="ERK1/2-pT202/Y204",
        entity="MAPK1|MAPK3",
        site="T202|Y204",
        time_hours=9.0,
        effect_log2=-2.025354,
        vehicle_null_threshold_log2=-0.676489,
        engaged=True,
        source="data/external/nyman2020 RFI matrix",
        source_sha256="0" * 64,
    )
    defaults.update(overrides)
    return ProximalFunctionRecord(**defaults)


def test_a_measured_proximal_record_discharges_a_proximal_requirement():
    requirement = PremiseRequirement(
        field="functional:pathway_activity",
        quantity=BiologicalQuantity.PROXIMAL_ACTIVITY,
        entity="MAPK1|MAPK3",
        site="T202|Y204",
        units="log2_ratio_to_vehicle",
        context_identifier="A2058",
        time_hours=9.0,
        require_direct_measurement=True,
    )
    grant = _record().grant()
    assert grant.is_estimate is False
    assert requirement.unmet_reasons(grant) == ()
    certificate = issue_licence(
        contrast_identifier="fixture",
        action_identifier="measured_proximal_function",
        requirement=requirement,
        grant=grant,
        planned_context="A2058",
        observed_context="A2058",
        planned_time_hours=9.0,
        observed_time_hours=9.0,
    )
    assert certificate.gate("input_validity").passed
    assert certificate.updates_licensed


def test_proximal_function_does_not_discharge_an_occupancy_requirement():
    """A neighbouring quantity is not a substitute for the one that was asked for."""

    requirement = PremiseRequirement(
        field="functional:target_occupancy",
        quantity=BiologicalQuantity.TARGET_OCCUPANCY,
        entity="MAPK1|MAPK3",
        context_identifier="A2058",
        time_hours=9.0,
    )
    reasons = requirement.unmet_reasons(_record().grant(field="functional:target_occupancy"))
    assert any(reason.startswith("quantity_mismatch") for reason in reasons)


def test_a_foreign_lysate_estimate_is_refused_for_a_direct_engagement_premise():
    requirement = PremiseRequirement(
        field="functional:target_occupancy",
        quantity=BiologicalQuantity.TARGET_OCCUPANCY,
        entity="MAP2K1",
        context_identifier="A2058",
        time_hours=9.0,
        require_direct_measurement=True,
    )
    estimate = lysate_estimate_grant(
        field="functional:target_occupancy", context_identifier="A2058", time_hours=9.0
    )
    assertion_reasons = requirement.unmet_reasons(estimate)
    assert "estimate_offered_for_direct_measurement" in assertion_reasons
    assert estimate.quality == FOREIGN_LYSATE_REFUSAL
    assert estimate.quality_passed is False


def test_a_record_that_contradicts_its_own_numbers_is_refused():
    broken = _record(engaged=True, effect_log2=-0.1, vehicle_null_threshold_log2=-0.676489)
    issues = broken.problems()
    assert any(issue.startswith("engagement_claim_contradicts_its_own_numbers") for issue in issues)
    with pytest.raises(ValueError, match="proximal_function_record_not_usable"):
        broken.grant()

    consistent_negative = _record(
        engaged=False, effect_log2=-0.908321, vehicle_null_threshold_log2=-1.071825
    )
    assert consistent_negative.problems() == ()
    assert consistent_negative.grant().quality_passed is True
