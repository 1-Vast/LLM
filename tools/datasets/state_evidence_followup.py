"""Design-specific evidence admission; no controller replay or biological estimation."""
from tools.case_memory import sha256




def assess(design, evidence):
    """Positive evidence is required; unknown is never equivalent to passed."""
    common = {"legal_predecision_state", "sample_linkage", "real_endpoint",
              "complete_attempt_denominator", "qc", "matched_resource_rules",
              "interference_handled", "physical_batch_mapping"}
    designs = {
        "sister_panel": {"random_parent_split", "two_measured_actions", "matched_controls"},
        "random_policy": {"policy_randomization", "policy_arm_coverage"},
        "random_action_log": {"authenticated_propensities", "conditional_action_support"},
    }
    if design not in designs:
        raise ValueError("unknown comparison design")
    required = common | designs[design]
    missing = sorted(k for k in required if evidence.get(k) is not True)
    receipts = evidence.get("evidence_receipts", {})
    missing += sorted(k + "_missing_evidence" for k in required
                      if evidence.get(k) is True and not receipts.get(k))
    if missing:
        return {"classification": "replay_only", "missing": missing}
    if evidence.get("costs_authenticated") is True:
        return {"classification": "comparable", "missing": []}
    if evidence.get("credible_predeclared_cost_bounds") is True:
        return {"classification": "predeclared_utility_interval_only", "missing": ["costs_authenticated"]}
    return {"classification": "replay_only", "missing": ["costs_or_credible_bounds"]}
