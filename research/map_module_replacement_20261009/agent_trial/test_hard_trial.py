"""Meaningful authorization and leakage counterexamples for hidden-source trial."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import pytest

spec = spec_from_file_location("hard_source_trial", Path(__file__).with_name("hard_trial.py"))
hard = module_from_spec(spec)
spec.loader.exec_module(hard)


def sample():
    case = {"cid": "1", "smiles": "CC", "requested_gene": "DRD2", "requested_mode": "agonist"}
    prior = [{"cid": "1", "smiles": "CC", "gene_symbols": ["DRD2"], "parsed_mode": "agonist"}]
    card = {"id": "mechanism:2", "kind": "mechanism", "molecule_chembl_id": "CHEMBL1", "target": {"gene_symbols": ["DRD2", "DRD3"], "type": "PROTEIN FAMILY"}, "action_type": "ANTAGONIST", "direct_interaction": 1, "assay": {"assay_type": None, "confidence_score": None}}
    identity = {"tool_id": "exact_identity", "payload": {"molecule_status": "exact", "exact_molecule_ids": ["CHEMBL1"]}}
    mechanism = {"tool_id": "mechanism", "payload": {"cards": [card]}}
    return case, prior, identity, mechanism


def test_hidden_identity_does_not_authorize_real_mechanism_card():
    case, prior, identity, mechanism = sample()
    result = hard.supported_package(case, prior, [mechanism])
    assert result["molecule_status"] == "unverified"
    assert not result["qualified_card_ids"] and not result["source_conflict_detected"]


def test_source_conflict_preserves_family_scope_without_biological_claim():
    case, prior, identity, mechanism = sample()
    result = hard.supported_package(case, prior, [identity, mechanism])
    assert result["qualified_card_ids"] == ["mechanism:2"]
    assert result["reported_modes"] == ["ANTAGONIST"]
    assert result["target_scope"] == "family_membership"
    assert result["source_conflict_detected"] and not result["requested_mode_supported"]
    assert not result["case_measurement_supported"] and not result["independent_biological_confirmation"]


def test_other_drug_prior_cannot_create_conflict():
    case, prior, identity, mechanism = sample()
    prior[0]["smiles"] = "CCC"
    assert not hard.supported_package(case, prior, [identity, mechanism])["source_conflict_detected"]


def test_other_molecule_source_card_cannot_bind_to_an_exact_identity():
    case, prior, identity, mechanism = sample()
    mechanism["payload"]["cards"][0]["molecule_chembl_id"] = "CHEMBL2"
    result = hard.supported_package(case, prior, [identity, mechanism])
    assert not result["qualified_card_ids"] and not result["source_conflict_detected"]


def test_target_or_reference_metadata_cannot_establish_interaction():
    case, prior, identity, mechanism = sample()
    for tool in ("target", "reference"):
        result = hard.supported_package(case, prior, [identity, {"tool_id": tool, "payload": {"target": mechanism["payload"]["cards"][0]["target"]}}])
        assert not result["qualified_card_ids"] and not result["direct_interaction_assertion"]


def test_deterministic_choice_never_reads_hidden_source_answer():
    case, prior, identity, mechanism = sample()
    assert hard.choose_deterministic(case, []) == "exact_identity"
    assert hard.choose_deterministic(case, [identity]) == "mechanism"
    case["requested_mode"] = "bind"
    assert hard.choose_deterministic(case, [identity]) == "assay"
    identity["payload"]["molecule_status"] = "blocked"
    assert hard.choose_deterministic(case, [identity]) is None


def test_initial_menu_cannot_disclose_acquired_identity_mode_or_target():
    assert len(hard.TOOLS) == 5
    menu = " ".join(hard.TOOLS.values())
    for outcome in ("CHEMBL715", "DRD2", "ANTAGONIST", "case_08"):
        assert outcome not in menu


def test_reservation_precedes_source_access_and_third_purchase_is_blocked(monkeypatch):
    events, reads = [], []

    def inspect(tool, source, seed):
        assert events[-1]["event"] == "reserved"
        assert events[-1]["tool_id"] == tool
        reads.append(tool)
        return {"output_sha256": "0" * 64}

    monkeypatch.setattr(hard, "inspect_source", inspect)
    hard.purchase_inspection("exact_identity", {}, 11, events)
    hard.purchase_inspection("mechanism", {}, 11, events)
    with pytest.raises(ValueError, match="budget exhausted"):
        hard.purchase_inspection("assay", {}, 11, events)
    assert reads == ["exact_identity", "mechanism"]
    assert [e["event"] for e in events] == ["reserved", "returned", "reserved", "returned"]
