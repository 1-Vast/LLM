"""Pure state/sample/action evidence checks and source-hash helpers.

The historical lineage reconstruction command is checkout-local research:
``python -m research.astra.state_identifiability``. No scientific gate changes.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")


def state_gaps(state: dict | None) -> list[str]:
    """Require measured state, availability, treatment order and audited matching."""
    if not state:
        return ["no_audited_predecision_state"]
    gaps = []
    times = {}
    for name in ("measured_at", "available_at", "decision_at", "action_started_at"):
        try:
            value = datetime.fromisoformat(state[name].replace("Z", "+00:00"))
            if value.utcoffset() is None:
                raise ValueError("timezone_missing")
            times[name] = value
        except (KeyError, AttributeError, TypeError, ValueError):
            gaps.append(f"missing_or_invalid_{name}")
    if len(times) == 4 and not (
        times["measured_at"] <= times["available_at"] <= times["decision_at"]
        < times["action_started_at"]
    ):
        gaps.append("state_not_available_before_action_decision")
    if state.get("role") != "predecision_observation":
        gaps.append("post_treatment_or_unspecified_state_role")
    if state.get("matching_verified") is not True or state.get("relation") not in {
        "same_live_sample", "randomized_sister_aliquots", "barcoded_clonal_population"
    }:
        gaps.append("unverified_state_response_sample_relation")
    if not state.get("sample_id") or not state.get("response_parent_id"):
        gaps.append("missing_state_or_response_sample_identity")
    if (not re.fullmatch(r"[0-9a-f]{64}", str(state.get("source_sha256", "")))
            or not state.get("source_path") or not state.get("source_fields")):
        gaps.append("missing_raw_state_source_evidence")
    return gaps


def action_observed_and_matched(action: dict, state: dict | None) -> bool:
    """Require each action's own chronology and parent, not only task signoff."""
    if not state or state_gaps(state):
        return False
    try:
        names = ("action_started_at", "response_recorded_at", "outcome_available_at")
        times = [datetime.fromisoformat(action[name].replace("Z", "+00:00")) for name in names]
        decision = datetime.fromisoformat(state["decision_at"].replace("Z", "+00:00"))
        if any(value.utcoffset() is None for value in times) or not decision < times[0] <= times[1] <= times[2]:
            return False
    except (KeyError, AttributeError, TypeError, ValueError):
        return False
    return (
        action.get("executed") is True and action.get("outcome_link_verified") is True
        and action.get("sample_relation_verified") is True
        and action.get("response_parent_id") == state["response_parent_id"]
        and action.get("qc_status") in {"passed", "failed"}
        and bool(re.fullmatch(r"[0-9a-f]{64}", str(action.get("source_sha256", ""))))
        and bool(action.get("source_path")) and bool(action.get("source_fields"))
        and bool(action.get("action")) and bool(action.get("endpoint_id"))
    )


def assess_task(task: dict) -> dict:
    """Classify audited evidence; record-level discovery is never qualification."""
    gaps = state_gaps(task.get("predecision_state"))
    if task.get("state_blind_control_constructible") is not True:
        gaps.append("state_blind_control_unverified")
    actions = task.get("actions", [])
    observed = [action for action in actions if action_observed_and_matched(action, task.get("predecision_state"))]
    distinct = {action["action"] for action in observed}
    if len(distinct) < 2:
        gaps.append("fewer_than_two_comparable_observed_actions")
    if task.get("same_rules_declared") is not True:
        gaps.append("endpoint_cost_budget_qc_refusal_rules_unfrozen")
    if len({action["endpoint_id"] for action in observed}) > 1:
        gaps.append("candidate_endpoints_differ")
    state_and_links = not gaps
    full = len(observed) == len(actions) and task.get("attempt_denominator_verified") is True
    classification = ("comparable" if full else "utility_interval_only") if state_and_links else "replay_only"
    if state_and_links and not full:
        gaps.append("missing_action_outcome_or_attempt_denominator")
    return {
        "task_id": task["task_id"], "classification": classification,
        "state_gain_gate_passed": classification == "comparable",
        "action_count": len(actions), "comparable_observed_actions": len(distinct),
        "gaps": gaps, "physical_independence": task.get("physical_independence", "unverified"),
        "uncertainty": "not_estimable_this_audit; no_state_gain_experiment",
    }


def response_link_gaps(task: str, source: dict) -> list[str]:
    """Protocol result_valid does not resolve conflicting well/plate provenance."""
    if task == "sciplex3_B":
        return [] if int(source.get("raw_cells", "0")) > 0 else ["no_deposited_cells"]
    gaps = []
    if source.get("cache_expansion_agrees") != "True" and source.get("cache_vs_distinct_slots_agrees") != "True":
        gaps.append("well_source_link_unresolved")
    if source.get("cache_plate_agrees") != "True":
        gaps.append("plate_source_link_unresolved")
    if int(source.get("inst_rows", "0")) == 0:
        gaps.append("no_deposited_instance")
    return gaps
