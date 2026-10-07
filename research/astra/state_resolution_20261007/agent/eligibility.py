"""Fail-closed research admission; no automatic dual-core claim from a fallback."""
import json


class StudyNotEligible(ValueError):
    pass


def require_dual_core_opportunity(records, development_summary):
    reasons = []
    if "state_representation_active" not in records:
        reasons.append("missing_STATE_representation_activity_receipt")
    elif not records["state_representation_active"].map(lambda value: value is True or str(value).lower() == "true").all():
        reasons.append("STATE_representation_inactive_gamma_zero_fallback")
    if development_summary.get("endpoint") != "signed_noise_corrected_mean_squared_native_rna_delta":
        reasons.append("unsupported_or_noise_dominated_endpoint")
    gains = []
    for world in ("reference", "state"):
        evidence = development_summary.get(world, {})
        if not {"myopic", "lookahead"} <= evidence.keys():
            reasons.append("missing_sequential_development_evidence:" + world)
            continue
        myopic = evidence["myopic"]
        lookahead = evidence["lookahead"]
        # Stop is a competent comparator whenever acquiring makes things worse.
        gains.append(lookahead["mean_gain_vs_no_update"] - max(0.0, myopic["mean_gain_vs_no_update"]))
    if not gains or max(gains) <= 0:
        reasons.append("no_development_gain_over_myopic_and_stop")
    if reasons:
        raise StudyNotEligible("dual_core_evaluation_refused:" + ";".join(reasons))
    return {"eligible": True, "development_gains_over_strong_comparator": gains}
