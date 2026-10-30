"""Contracts of the strict information-tier gate (maestro.tier_gate)."""
import pytest

from maestro.information_tier import InputDeclaration, Tier, TierViolation
from maestro.tier_gate import (COLD_START_UNCHECKED, COLD_START_VIOLATION, PROVENANCE_MISSING, PROVENANCE_UNVERIFIED,
                               REGISTRY_REQUIRED, strict_admit, strict_require)
from tests.fixtures.strict_evidence import Lab

STRUCTURE = InputDeclaration("structure", Tier.T0, provenance="s_structure")
SCREEN = InputDeclaration("primary_screen", Tier.T1, provenance="s_screen")
MISDECLARED = InputDeclaration("primary_screen", Tier.T0, provenance="s_screen")      # a T1 input declared T0


def lab(tmp_path):
    lab = Lab(tmp_path)
    lab.source("s_structure", "smiles")
    lab.source("s_screen", "viability")
    return lab


def reasons(admission):
    return dict(admission.refused)


def test_a_call_without_a_registry_is_refused_by_name(tmp_path):
    assert reasons(strict_admit([STRUCTURE], Tier.T1, None)) == {"structure": REGISTRY_REQUIRED}
    assert reasons(strict_admit([STRUCTURE], Tier.T1, {})) == {"structure": REGISTRY_REQUIRED}
    assert reasons(strict_admit([], Tier.T1, None)) == {"*": REGISTRY_REQUIRED}


def test_inputs_must_match_the_registry_and_the_claimed_tier(tmp_path):
    registry = {"structure": STRUCTURE, "primary_screen": SCREEN}
    assert strict_admit([STRUCTURE, SCREEN], Tier.T1, registry).passed
    assert reasons(strict_admit([SCREEN], Tier.T0, registry, compounds=["c"], observations={})) == {"primary_screen": "TIER_VIOLATION"}
    assert reasons(strict_admit([MISDECLARED], Tier.T1, registry)) == {"primary_screen": "UNDECLARED_INPUT"}


def test_a_misdeclared_screen_cannot_pass_a_cold_start_claim_because_the_data_are_checked(tmp_path):
    registry = {"primary_screen": MISDECLARED}
    admission = strict_admit([MISDECLARED], Tier.T0, registry, compounds=["c1", "c2"], observations={"primary_screen": {"c2"}})
    assert reasons(admission) == {"c2": f"{COLD_START_VIOLATION}:primary_screen"}
    clean = strict_admit([STRUCTURE], Tier.T0, {"structure": STRUCTURE}, compounds=["c1"], observations={"primary_screen": {"c9"}})
    assert clean.passed


def test_a_cold_start_claim_without_the_compounds_and_observations_is_not_admitted(tmp_path):
    assert reasons(strict_admit([STRUCTURE], Tier.T0, {"structure": STRUCTURE})) == {"*": COLD_START_UNCHECKED}
    assert strict_admit([STRUCTURE], Tier.T1, {"structure": STRUCTURE}).passed


def test_provenance_must_be_named_and_the_bytes_must_still_match(tmp_path):
    l = lab(tmp_path)
    bare = InputDeclaration("structure", Tier.T0)
    assert reasons(strict_admit([bare], Tier.T1, {"structure": bare})) == {"structure": PROVENANCE_MISSING}
    registry = {"structure": STRUCTURE}
    assert strict_admit([STRUCTURE], Tier.T1, registry, ledger=l.ledger).passed
    (l.root / "s_structure.csv").write_bytes(b"altered")
    assert reasons(strict_admit([STRUCTURE], Tier.T1, registry, ledger=l.ledger)) == {"structure": f"{PROVENANCE_UNVERIFIED}:SOURCE_DIGEST_MISMATCH"}
    ghost = InputDeclaration("ghost", Tier.T0, provenance="never_registered")
    assert reasons(strict_admit([ghost], Tier.T1, {"ghost": ghost}, ledger=l.ledger)) == {"ghost": f"{PROVENANCE_UNVERIFIED}:SOURCE_UNREGISTERED"}


def test_require_raises_the_historical_violation_type(tmp_path):
    with pytest.raises(TierViolation):
        strict_require([STRUCTURE], Tier.T1, None)
