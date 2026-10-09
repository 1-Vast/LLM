from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location("offline_source_guard", Path(__file__).with_name("offline_guard.py"))
guard = module_from_spec(spec)
spec.loader.exec_module(guard)


def evidence():
    return {"molecule_status": "exact", "qualified_card_ids": ["mechanism:1"], "reported_modes": ["ANTAGONIST"], "requested_mode_supported": False,
            "binding_assay_annotation": False, "direct_interaction_assertion": True, "target_scope": "family_membership", "source_conflict_detected": True,
            "case_measurement_supported": False, "independent_biological_confirmation": False, "action_identifier": "measure_case_target_engagement"}


def test_null_metadata_is_rejected_without_coercion():
    original = evidence()
    original["binding_assay_annotation"] = None
    assert guard.admission(original, evidence()) == ["invalid_schema"]
    assert original["binding_assay_annotation"] is None


def test_uninspected_card_and_selective_scope_are_rejected():
    original = evidence()
    original["qualified_card_ids"] = ["mechanism:2"]
    original["target_scope"] = "single_protein_annotation"
    reasons = guard.admission(original, evidence())
    assert "unauthorized_qualified_card_ids" in reasons
    assert "unauthorized_target_scope" in reasons


def test_omission_is_allowed_but_does_not_become_correct_or_complete():
    original = evidence()
    original["qualified_card_ids"] = []
    original["reported_modes"] = []
    original["source_conflict_detected"] = False
    assert not guard.admission(original, evidence())
    assert original != evidence()


def test_cell_or_independence_overclaim_never_admitted():
    for key in ("case_measurement_supported", "independent_biological_confirmation"):
        original = evidence()
        original[key] = True
        assert "unauthorized_" + key in guard.admission(original, evidence())
