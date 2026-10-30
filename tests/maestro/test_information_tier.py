"""Contracts of the information-tier boundary (maestro.information_tier)."""
import pytest

from maestro.information_tier import (OUTCOME_PROXIMAL_INPUT, TIER_VIOLATION, UNDECLARED_INPUT, InputDeclaration,
                                      Tier, TierViolation, admit, claimable_tier, cold_start_violations, require)

STRUCTURE = InputDeclaration("morgan_fingerprint", Tier.T0, provenance="chemistry")
CURATED = InputDeclaration("hub_targets", Tier.T0, provenance="curated_hub")
ENGAGEMENT = InputDeclaration("chembl_cell_engagement", Tier.T1, provenance="assay_cell_engagement")
PRIMARY = InputDeclaration("prism_primary_lfc", Tier.T1, provenance="screen")
SECONDARY = InputDeclaration("prism_secondary_auc", Tier.T2, provenance="bought")
GROWTH = InputDeclaration("chembl_growth_inhibition", Tier.T1, outcome_proximal=True)


def test_t1_inputs_cannot_support_a_t0_claim():
    admission = admit([STRUCTURE, CURATED, PRIMARY], Tier.T0)
    assert admission.admitted == ("morgan_fingerprint", "hub_targets")
    assert admission.refused == (("prism_primary_lfc", TIER_VIOLATION),) and not admission.passed
    with pytest.raises(TierViolation, match="prism_primary_lfc:TIER_VIOLATION"):
        require([STRUCTURE, PRIMARY], Tier.T0)
    assert require([STRUCTURE, PRIMARY], Tier.T1).passed
    assert not admit([SECONDARY], Tier.T1).passed and admit([SECONDARY], Tier.T2).passed


def test_outcome_proximal_inputs_are_refused_at_every_tier():
    for tier in Tier:
        assert admit([GROWTH], tier).refused == (("chembl_growth_inhibition", OUTCOME_PROXIMAL_INPUT),)
    with pytest.raises(TierViolation):
        claimable_tier([STRUCTURE, GROWTH])


def test_claimable_tier_is_the_highest_input_tier():
    assert claimable_tier([]) == Tier.T0
    assert claimable_tier([STRUCTURE, CURATED]) == Tier.T0
    assert claimable_tier([STRUCTURE, ENGAGEMENT]) == Tier.T1
    assert claimable_tier([PRIMARY, SECONDARY]) == Tier.T2


def test_registry_refuses_undeclared_or_relabelled_inputs():
    registry = {d.name: d for d in (STRUCTURE, CURATED, PRIMARY)}
    relabelled = InputDeclaration("prism_primary_lfc", Tier.T0)
    unknown = InputDeclaration("vendor_annotations", Tier.T0)
    refused = dict(admit([STRUCTURE, relabelled, unknown], Tier.T0, registry).refused)
    assert refused == {"prism_primary_lfc": UNDECLARED_INPUT, "vendor_annotations": UNDECLARED_INPUT}


def test_cold_start_violations_name_every_source():
    observed = {"prism_primary": {"BRD-K00000001", "BRD-K00000002"}, "lincs_l1000": {"BRD-K00000002"}}
    assert cold_start_violations(["BRD-K00000001", "BRD-K00000002", "BRD-K00000003"], observed) == {
        "BRD-K00000001": ("prism_primary",), "BRD-K00000002": ("lincs_l1000", "prism_primary")}
    with pytest.raises(ValueError):
        InputDeclaration(" ", Tier.T0)
    with pytest.raises(TypeError):
        InputDeclaration("x", 0)
