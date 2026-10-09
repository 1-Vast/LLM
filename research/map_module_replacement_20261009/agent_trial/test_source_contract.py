"""Counterexamples for source interpretation, not tests of biological truth."""
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import pytest

spec = spec_from_file_location("map_agent_source_trial", Path(__file__).with_name("trial.py"))
trial = module_from_spec(spec)
spec.loader.exec_module(trial)


@pytest.mark.parametrize("flag", [True, 1])
def test_opposite_mode_is_retained_without_sign_or_causal_confirmation(flag):
    case = {"requested_gene": "DRD2", "requested_mode": "agonist"}
    source = {"identity_status": "exact"}
    card = {"id": "mechanism:1", "kind": "mechanism", "target_gene_symbols": ["DRD2"],
            "source_record": {"action_type": "ANTAGONIST", "direct_interaction": flag}}
    result = trial.deterministic(case, source, [card])
    assert result["reported_modes"] == ["ANTAGONIST"]
    assert not result["requested_mode_supported"]
    assert result["direct_interaction_assertion"]
    assert not result["case_measurement_supported"]
    assert not result["independent_biological_confirmation"]


def test_binding_assay_does_not_establish_mode_or_cell_case():
    case = {"requested_gene": "PTPN1", "requested_mode": "inhibit"}
    source = {"identity_status": "exact"}
    card = {"id": "activity:1", "kind": "activity", "target_gene_symbols": ["PTPN1"],
            "source_record": {"standard_type": "IC50", "standard_value": "0.001"},
            "assay_record": {"assay_type": "B", "confidence_score": 9, "assay_cell_type": "A549"}}
    result = trial.deterministic(case, source, [card])
    assert result["qualified_card_ids"] == ["activity:1"]
    assert result["binding_assay_annotation"] and not result["requested_mode_supported"]
    assert not result["case_measurement_supported"]
    ambiguous = deepcopy(card)
    ambiguous["assay_record"]["confidence_score"] = 8
    assert not trial.deterministic(case, source, [ambiguous])["qualified_card_ids"]


def test_full_component_block_suppresses_informative_parent_cards():
    case = {"requested_gene": "GNRHR", "requested_mode": "antagonist"}
    card = {"id": "mechanism:1", "kind": "mechanism", "target_gene_symbols": ["GNRHR"],
            "source_record": {"action_type": "ANTAGONIST", "direct_interaction": True}}
    result = trial.deterministic(case, {"identity_status": "blocked"}, [card])
    assert not result["qualified_card_ids"] and not result["reported_modes"]
    assert not result["requested_mode_supported"] and not result["binding_assay_annotation"] and not result["direct_interaction_assertion"]
    assert result["action_identifier"] == "verify_exact_identity"


def test_similar_target_substring_cannot_authorize_exact_symbol():
    case = {"requested_gene": "DRD2", "requested_mode": "antagonist"}
    card = {"id": "mechanism:1", "kind": "mechanism", "target_gene_symbols": ["DRD20"],
            "source_record": {"action_type": "ANTAGONIST", "direct_interaction": True}}
    result = trial.deterministic(case, {"identity_status": "exact"}, [card])
    assert not result["qualified_card_ids"] and not result["binding_assay_annotation"] and not result["direct_interaction_assertion"]
