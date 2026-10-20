"""Audit 1 engineering tests (software integrity level). They test behaviour of the audit rules and the stored artefacts, not biology."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import audit_logic as al  # noqa: E402
import mutation  # noqa: E402

import logic  # noqa: E402
import records as rec  # noqa: E402


def _load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def test_grade_gate_blocks_qualitative_and_unbounded_negatives():
    assert al.can_update("numeric_with_uncertainty", False, "test_only")
    assert not al.can_update("reported_qualitatively", False, "test_only")
    assert not al.can_update("numeric_without_uncertainty", False, "test_only")
    assert not al.can_update("numeric_with_uncertainty", True, "test_only")
    assert al.can_update("numeric_with_uncertainty", True, "equivalence_margin")


def test_open_explanation_is_never_removed():
    model = al.aurora_model_v2()
    gs = al.GradedState(model)
    for a, o in (("A_T217D_RESCUE", "rescued"), ("A_JB211_ACTIVITY", "not_inhibited"), ("A_JB211_ACTIVITY", "inhibited")):
        gs.observe(a, o, "numeric_with_uncertainty", "equivalence_margin", False)
        assert al.OPEN in gs.compatible()


def test_jb211_catalytic_premise_separate_from_occupancy_and_exposure():
    model = al.aurora_model_v2()
    names = set(model.assays)
    assert {"A_JB211_OCCUPANCY", "A_JB211_EXPOSURE", "A_JB211_ACTIVITY"} <= names
    assert "A_JB211_ENGAGE" not in names


def test_all_nondiscriminative_menu_returns_indistinguishable():
    model = al.aurora_model_v2()
    menu = {a["action_id"]: dict(a) for a in rec.ACTIONS if a["outcome_in_records"]}
    p = al.propose_v2(model, logic.initial_state(), menu, set())
    assert p["decision"] in {"unknown", "still_indistinguishable"} or p["decision"].startswith("NONE_")
    assert al.OPEN in p["compatible"]


def test_label_validator_flags_assumed_inhibition_and_inactive_relabel():
    bad = json.loads(json.dumps(rec.COMPOUNDS))
    bad["JB211"]["catalytic_inhibition_assumed"] = True
    assert al.validate_compound_labels(bad)
    bad = json.loads(json.dumps(rec.COMPOUNDS))
    bad["JB211"]["mode"] = "inactive_control"
    assert al.validate_compound_labels(bad)
    assert not al.validate_compound_labels(rec.COMPOUNDS)


def test_cost_counts_duplicated_bundle_once():
    acts = [{"action_id": "X", "wells_min": 18, "turnaround_days": 3, "cost_currency": None}]
    once = al.cost_total_unique(acts, ["X"])
    twice = al.cost_total_unique(acts, ["X", "X"])
    assert once == twice and once["wells"] == 18 and once["missing_price_fields"] == 1


def test_all_mutation_checks_pass_and_stored_results_match():
    results = mutation.run_all()
    assert len(results) == 10 and all(r["passed"] for r in results)
    stored = {r["id"]: r["passed"] for r in _load("MUTATION_RESULTS.json")["results"]}
    assert stored == {r["id"]: r["passed"] for r in results}


def test_no_audit_rule_raises_a_level_and_no_level3_unit():
    g = _load("GATE_DECISIONS_AUDIT1.json")
    assert g["G0"]["counts"]["level_3_units"] == 0 and g["G0"]["counts"]["level_4_units"] == 0
    assert all(not r["can_exceed_v1_level"] for r in g["G0"]["requalification"])
    assert g["G0"]["g0_decision"] == "QUALIFIED_FOR_LOGIC_TEST" and g["G0"]["research_level_status"] == "ASSET_BLOCKED"
    assert g["G1"]["g1_biological"] == "BIOLOGICAL_DISCRIMINATION_NOT_ESTABLISHED"
    assert g["G1"]["g2_information_value_inferred"] is False
    assert all(g[k] == "NOT_EXECUTED" for k in ("G2", "G3", "G4", "G5"))


def test_jb211_status_has_required_wording_and_unresolved_premise():
    j = _load("JB211_PREMISE_STATUS.json")
    assert j["wording"] == ("CRBN-null close analog; AURKA binding is asserted in the source, but direct intracellular engagement and catalytic inhibition "
                            "remain unresolved in the extracted evidence.")
    assert j["premise_P_catalytic_inhibition_by_JB211"] == "UNRESOLVED"
    assert {"crbn_recruitment", "aurka_occupancy_or_binding", "intracellular_exposure", "catalytic_activity", "protein_abundance", "terminal_phenotype"} <= set(j["variables"])
    assert j["variables"]["catalytic_activity"]["status"] == "not_reported"


def test_compound_57_has_no_terminal_inactivity_claim():
    c = _load("CCT57_TERMINAL_STATUS.json")
    assert c["terminal_functional_result"]["status"] == "not_reported" and c["terminal_inactivity_claim_allowed"] is False


def test_manifest_flags_and_commits():
    m = _load("AUDIT_MANIFEST.json")
    assert m["post_hoc_audit"] is True and m["not_preregistered"] is True and m["independent_confirmation"] is False and m["sources_exposed"] is True
    assert m["head_at_audit_start"] == m["v1_base_commit"] == "f997c157c1b6b01026652beb0d4fc49879199086"
    assert m["actual_expenditure"]["api_calls"] == 0 and m["actual_expenditure"]["usd"] == 0.0
    assert all(m["mutation_summary"].values())


def test_records_v2_preserve_v1_ids_and_carry_grades():
    rows = [json.loads(x) for x in (HERE / "records_v2.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(r["version"] == 2 and r["evidence_grade"] in al.GRADES for r in rows)
    v1_observed = {r["id"] for r in rec.RECORDS if r["evidence_type"] == rec.OBSERVED}
    assert v1_observed <= {r["id"] for r in rows}
    for r in rows:
        if r["supersedes"]:
            assert r["supersedes_digest"] == al.canonical_digest({x["id"]: x for x in rec.RECORDS}[r["supersedes"]])


def test_h_labels_appear_only_as_undefined_and_unused():
    for p in HERE.glob("*.json"):
        text = p.read_text(encoding="utf-8")
        if "H_E" in text:
            assert "undefined" in text and "not used" in text, p.name
