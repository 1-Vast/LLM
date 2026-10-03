import json
from pathlib import Path

import pytest
from tools.datasets.state_evidence_followup import assess




ROOT = Path(__file__).resolve().parents[1]
COMMON = dict.fromkeys([
    "legal_predecision_state", "sample_linkage", "real_endpoint",
    "complete_attempt_denominator", "qc", "matched_resource_rules",
    "interference_handled", "physical_batch_mapping", "costs_authenticated",
], True)


@pytest.mark.parametrize("design,keys", [
    ("sister_panel", ["random_parent_split", "two_measured_actions", "matched_controls"]),
    ("random_policy", ["policy_randomization", "policy_arm_coverage"]),
    ("random_action_log", ["authenticated_propensities", "conditional_action_support"]),
])
def test_design_specific_identification(design, keys):
    evidence = dict(COMMON, **dict.fromkeys(keys, True))
    evidence["evidence_receipts"] = dict.fromkeys([*COMMON, *keys], "test fixture only")
    assert assess(design, evidence)["classification"] == "comparable"
    for key in (*COMMON, *keys):
        broken = dict(evidence, **{key: None})
        assert assess(design, broken)["classification"] == "replay_only"


def test_zero_support_cannot_be_repaired_by_known_propensity():
    evidence = dict(COMMON, authenticated_propensities=True, conditional_action_support=False)
    evidence["evidence_receipts"] = dict.fromkeys([*COMMON, "authenticated_propensities"], "test fixture only")
    assert assess("random_action_log", evidence)["missing"] == ["conditional_action_support"]


def test_cost_bounds_require_identified_attempts():
    evidence = dict(COMMON, policy_randomization=True, policy_arm_coverage=True,
                    costs_authenticated=None, credible_predeclared_cost_bounds=True)
    evidence["evidence_receipts"] = dict.fromkeys([*COMMON, "policy_randomization", "policy_arm_coverage"], "test fixture only")
    assert assess("random_policy", evidence)["classification"] == "predeclared_utility_interval_only"
    evidence["complete_attempt_denominator"] = None
    assert assess("random_policy", evidence)["classification"] == "replay_only"


def test_unsigned_declarations_cannot_qualify():
    evidence = dict(COMMON, policy_randomization=True, policy_arm_coverage=True)
    assert assess("random_policy", evidence)["classification"] == "replay_only"






def test_gross_current_review_corrects_only_controls():
    review = json.loads((ROOT / "tools/datasets/state_search_review_20261001.json").read_text())
    gross = next(r for r in review if r["candidate_id"] == "gross_hcc1143")
    assert "A1 A3 A5" in gross["field_gaps"]["controls"]
    assert gross["state_available_before_decision"] is False
    frozen = json.loads((ROOT / "tools/datasets/audit_results/20261001_state_search_build_v4/review.json").read_text())
    old = next(r for r in frozen if r["candidate_id"] == "gross_hcc1143")
    assert "A1 B1 C1" in old["field_gaps"]["controls"]
