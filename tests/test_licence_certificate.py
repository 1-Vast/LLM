"""The four-gate licence certificate, and the two rates it makes reportable.

File summary
- Path: tests/test_licence_certificate.py
- Purpose: pin the certificate semantics. A qualified result may update the contrast on three
  gates; only a repair that also beats the menu-only bound earns credit; and an update applied
  beyond its licence, or a readout bought without a passing gate, is counted rather than
  argued about.
- Interfaces: pytest test functions
- Depends on: maestro.licence, maestro.models
"""
import pytest

from maestro.licence import (
    GATES,
    GateVerdict,
    audit_licences,
    identifiability,
    incremental_utility,
    input_validity,
    issue_licence,
    outcome_support,
)
from maestro.models import BiologicalQuantity, EvidenceScope, PremiseGrant, PremiseRequirement

OCCUPANCY = BiologicalQuantity.TARGET_OCCUPANCY


def _requirement() -> PremiseRequirement:
    return PremiseRequirement(
        field="functional:target_activity",
        quantity=OCCUPANCY,
        entity="EGFR",
        units="fraction_occupied",
        context_identifier="ACH-000561:TDOTT",
    )


def _grant(**overrides) -> PremiseGrant:
    values = {
        "field": "functional:target_activity",
        "source_action": "matched_target_engagement",
        "quantity": OCCUPANCY,
        "entity": "EGFR",
        "units": "fraction_occupied",
        "context_identifier": "ACH-000561:TDOTT",
        "quality": "qualified",
        "quality_passed": True,
    }
    values.update(overrides)
    return PremiseGrant(**values)


def _certificate(**overrides):
    values = {
        "contrast_identifier": "k",
        "action_identifier": "matched_target_engagement",
        "requirement": _requirement(),
        "grant": _grant(),
        "authorized_fields": ("functional:target_activity",),
        "declared_outcomes": {"h_gap": "insufficient", "h_mode": "sufficient"},
        "hypotheses": ("h_gap", "h_mode"),
        "observed_outcome": "insufficient",
        "planned_context": "ACH-000561:TDOTT",
        "observed_context": "ACH-000561:TDOTT",
        "certified_value": 0.5,
    }
    values.update(overrides)
    return issue_licence(**values)


def test_a_certificate_records_the_four_gates_in_order():
    certificate = _certificate()
    assert tuple(gate.name for gate in certificate.gates) == GATES
    assert certificate.updates_licensed is True
    assert certificate.repair_credited is True
    assert certificate.scope is EvidenceScope.MECHANISM_CONTRAST


def test_an_unregistered_gate_name_is_refused():
    with pytest.raises(ValueError):
        GateVerdict("plausibility", True, "")


def test_a_rna_abundance_grant_cannot_discharge_an_occupancy_premise():
    """The typed admission that already exists decides this gate, rather than a new rule."""

    verdict = input_validity(
        _requirement(),
        _grant(quantity=BiologicalQuantity.RNA_ABUNDANCE),
    )
    assert verdict.passed is False
    certificate = _certificate(grant=_grant(quantity=BiologicalQuantity.RNA_ABUNDANCE))
    assert certificate.updates_licensed is False
    assert certificate.scope is EvidenceScope.MEASUREMENT_FEASIBILITY
    assert certificate.gate("input_validity").detail.startswith("typed admission refused")


def test_an_untyped_premise_passes_by_declaration_and_says_so():
    verdict = input_validity(None, _grant())
    assert verdict.passed is True
    assert "no typed requirement" in verdict.detail


def test_an_undeclared_observed_value_is_not_support():
    assert outcome_support(
        declared_outcomes={"h_gap": "insufficient", "h_mode": "sufficient"},
        hypotheses=("h_gap", "h_mode"),
        observed_outcome="no_call",
    ).passed is False
    assert outcome_support(
        declared_outcomes={"h_gap": "insufficient"},
        hypotheses=("h_gap", "h_mode"),
        observed_outcome="insufficient",
    ).passed is False
    certificate = _certificate(observed_outcome="no_call")
    assert certificate.updates_licensed is False
    assert certificate.scope is EvidenceScope.PLAN_LIMITATION


def test_identifiability_requires_a_context_and_a_matching_window():
    assert identifiability(
        planned_context="c1", observed_context="c1", planned_time_hours=24.0, observed_time_hours=24.0
    ).passed is True
    assert identifiability(planned_context="c1", observed_context="c2").passed is False
    assert identifiability(planned_context=None, observed_context="c1").passed is False
    assert identifiability(
        planned_context="c1",
        observed_context="c1",
        planned_time_hours=24.0,
        observed_time_hours=120.0,
        time_tolerance_hours=6.0,
    ).passed is False


def test_the_utility_gate_needs_a_strict_positive_bound():
    assert incremental_utility(None).passed is False
    assert incremental_utility(0.0).passed is False
    assert incremental_utility(0.5).passed is True


def test_a_qualified_result_may_update_the_contrast_even_when_the_repair_earns_no_credit():
    """The separation the four gates exist to make: evidence authority is not repair credit."""

    certificate = _certificate(certified_value=0.0)
    assert certificate.gate("incremental_utility").passed is False
    assert certificate.updates_licensed is True
    assert certificate.repair_credited is False
    assert certificate.scope is EvidenceScope.MECHANISM_CONTRAST


def test_the_audit_counts_updates_beyond_the_licence_and_readouts_without_a_gate():
    compliant = _certificate(action_identifier="good")
    refused = _certificate(
        action_identifier="bad", grant=_grant(quantity=BiologicalQuantity.RNA_ABUNDANCE)
    )
    audit = audit_licences(
        [compliant, refused],
        applied_updates=(
            ("good", EvidenceScope.MECHANISM_CONTRAST),
            ("bad", EvidenceScope.MECHANISM_CONTRAST),
        ),
        gate_events=(("readout_a", True, True), ("readout_b", False, True), ("readout_c", False, False)),
    )
    assert audit.certificates == 2
    assert audit.updates_licensed == 1
    assert audit.repairs_credited == 1
    assert audit.updates_applied == 2
    assert audit.updates_applied_beyond_the_licence == 1
    assert audit.unlicensed_update_rate == pytest.approx(0.5)
    assert audit.readouts_bought == 2
    assert audit.gate_bypass_rate == pytest.approx(0.5)


def test_a_run_with_no_events_reports_no_rate_rather_than_zero():
    audit = audit_licences([_certificate()])
    assert audit.unlicensed_update_rate is None
    assert audit.gate_bypass_rate is None
