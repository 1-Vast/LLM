"""Audit real predecision-state eligibility without fitting or invoking a model.

The raw lineage scripts are retained as historical implementations. This entry
point reruns their metadata joins into a fresh directory, links every frozen
episode/action, and combines independently inspected source-field receipts.
No prediction, selection, outcome imputation or state-gain score is computed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "outputs/protocol_v2_1_20260927/e_data1/tables"
RAW_SOURCES = {
    "sciplex3_B": ["data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad"],
    "l1000_LT": [f"data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_{name}.txt.gz"
                 for name in ("inst_info", "sig_info", "sig_metrics")],
}


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


def _jsonl(path: Path, rows) -> None:
    with path.open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as handle:
            for row in rows:
                handle.write((json.dumps(row, sort_keys=True, allow_nan=False) + "\n").encode())


def _lineage(out: Path, task: str) -> dict:
    module = "lineage_sciplex3" if task == "sciplex3_B" else "lineage_l1000"
    command = [sys.executable, "-m", f"research.identifiability_audit.{module}", "--out", str(out)]
    out.mkdir()
    with (out / "command.txt").open("x", encoding="utf-8") as handle:
        handle.write(subprocess.list2cmdline(command) + "\n")
    with (out / "execution.txt").open("xb") as handle:
        result = subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"raw_lineage_failed:{task}; preserved_receipt={out}")
    with (out / "action_source.csv").open(encoding="utf-8", newline="") as handle:
        return {(row["compound"], row["action"]): row for row in csv.DictReader(handle)}


def run(out: Path, review: Path) -> dict:
    """A fresh audit, preserving raw joins and all failed/not-run decisions."""
    out, review = out.resolve(), review.resolve()
    out.mkdir(parents=True, exist_ok=False)
    review_files = sorted(path for name in ("raw_review", "checkpoint_review", "public_review")
                          for path in (review / name).rglob("*") if path.is_file())
    if not review_files:
        raise ValueError("independent_source_review_required")
    inputs = {path.relative_to(ROOT).as_posix(): sha256(path) for path in review_files}
    table_paths = [path for task in ("sciplex3_B", "l1000_LT") for path in sorted(TABLES.glob(f"{task}_*.jsonl.gz"))]
    manifest_path = TABLES.parent / "manifest.json"
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for path in table_paths:
        actual = sha256(path)
        if actual != source_manifest["outputs_sha256"][f"tables/{path.name}"]:
            raise ValueError(f"frozen_table_changed:{path.name}")
        inputs[path.relative_to(ROOT).as_posix()] = actual
    inputs[manifest_path.relative_to(ROOT).as_posix()] = sha256(manifest_path)
    raw_hashes = {task: {name: sha256(ROOT / name) for name in names} for task, names in RAW_SOURCES.items()}
    for hashes in raw_hashes.values():
        inputs.update(hashes)
    for name in (
        "outputs/protocol_v2_1_20260927/design/sciplex3_design.csv",
        "outputs/protocol_v2_1_20260927/design/l1000_design.csv",
        "outputs/dynamic_world_model_20260926/prepared/conditions.csv",
        "outputs/dynamic_world_model_20260926/prepared/wells.csv",
        "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv",
        "data/external/lincs_l1000_phase1/subset48/conditions.json",
    ):
        inputs[name] = sha256(ROOT / name)
    source_paths = [Path(__file__), ROOT / "research/identifiability_audit/lineage_sciplex3.py",
                    ROOT / "research/identifiability_audit/lineage_l1000.py",
                    ROOT / "research/biological_depth/prepare.py"]
    code = {path.relative_to(ROOT).as_posix(): sha256(path) for path in source_paths}
    write_json(out / "freeze.json", {
        "scope": "stage_1_metadata_and_identifiability_only; not an efficacy preregistration",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "code_sha256": code, "input_sha256": inputs,
        "command": [sys.executable, *sys.argv], "environment": {
            "python": sys.version, "interpreter": sys.executable,
            "packages": {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "h5py", "pytest")}},
        "new_training": False, "model_inference": False, "api_calls": 0,
        "exposure_scope": "Existing development labels reread for provenance; LINCS2020 review explicitly records newly inspected header/first-row QC metadata; no further matrix or QC read.",
    })
    rows, episode_rows = [], []
    lineage_hashes = {}
    for task in ("sciplex3_B", "l1000_LT"):
        raw = _lineage(out / task, task)
        lineage_hashes[task] = sha256(out / task / "action_source.csv")
        for path in sorted(TABLES.glob(f"{task}_*.jsonl.gz")):
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                for line in handle:
                    episode = json.loads(line)
                    episode_id = "|".join(map(str, (task, episode["fold"], episode["compound"], episode["h1"], episode["h2"])))
                    actions = []
                    for action, outcome in sorted(episode["outcomes"].items()):
                        source = raw[(episode["compound"], action)]
                        executed = int(source["raw_cells" if task == "sciplex3_B" else "inst_rows"]) > 0
                        qc = source["qc_rule_passed" if task == "sciplex3_B" else "prep_qc"] == "True"
                        link_gaps = response_link_gaps(task, source)
                        row = {
                            "episode_id": episode_id, "task_id": task, "compound": episode["compound"],
                            "independent_unit": episode["unit"], "chemical_scaffold": episode.get("scaffold"),
                            "fold": episode["fold"], "action": action, "derived_join_fields": source,
                            "raw_join_sha256": lineage_hashes[task], "episode_table_sha256": inputs[path.relative_to(ROOT).as_posix()],
                            "source_sha256": next(iter(raw_hashes[task].values())),
                            "source_path": next(iter(raw_hashes[task])),
                            "source_fields": ["cell_line", "perturbation", "dose_value", "time", "plate", "well", "replicate"]
                                if task == "sciplex3_B" else ["inst_id", "pert_id", "cell_id", "pert_dose", "pert_time", "rna_plate", "rna_well"],
                            "raw_record_locator": {"cell_line": source["cell_line"], "compound": source["compound"],
                                                   "treatment_duration": source["time"], "dose": source["dose"],
                                                   "inst_ids": source.get("inst_ids"), "plates": source.get("raw_plates", source.get("inst_plate_names")),
                                                   "wells": source.get("raw_wells", source.get("inst_well_names"))},
                            "raw_source_sha256": raw_hashes[task], "executed": executed,
                            "execution_basis": "deposited_cell_or_RNA_instance_record; not_all_attempts",
                            "outcome_link_verified": not link_gaps, "response_source_link_gaps": link_gaps,
                            "qc_status": "passed" if qc else "failed",
                            "qc_basis": "historical_protocol_rule; not_laboratory_failure_receipt",
                            "outcome": outcome, "predecision_state": None,
                            "state_measured_at": None, "state_available_at": None, "decision_at": None,
                            "state_response_relation": "unverified", "unexecuted_reason": None,
                            "attempt_denominator": "unspecified", "lab_failure_reason": None,
                            "cost_days": source_manifest["settings"][task]["days"][action],
                            "cost_basis": "declared_historical_protocol; not_actual_lab_invoice",
                            "exposure": "previously_exposed_development_replay; STATE_condition_exposure_unverified; WorldV2_prior_fitting_history",
                            "classification": "replay_only", "state_gain_gate_passed": False,
                        }
                        rows.append(row)
                        actions.append(row)
                    audited = assess_task({
                        "task_id": episode_id, "actions": actions, "predecision_state": None,
                        "state_blind_control_constructible": False, "same_rules_declared": True,
                        "attempt_denominator_verified": False, "physical_independence": "one_shared-control_connected_component_in_prior_audit",
                    })
                    episode_rows.append({**audited, "menu": sorted(episode["outcomes"]),
                                         "rules": source_manifest["settings"][task]})
    _jsonl(out / "episode_action_audit.jsonl.gz", rows)
    _jsonl(out / "episode_task_audit.jsonl.gz", episode_rows)
    raw_review = json.loads((review / "raw_review/raw_source_review.json").read_text(encoding="utf-8"))
    candidate_reviews = raw_review["task_assessments"]
    write_json(out / "candidate_task_audit.json", candidate_reviews)
    public_review = json.loads((review / "public_review/candidate_questions.json").read_text(encoding="utf-8"))
    public_questions = public_review["questions"]
    write_json(out / "public_task_audit.json", public_questions)
    public_actions = [{"question_id": question["id"], "record": action,
                       "legal_action_menu": "unfrozen", "predecision_state": question.get("predecision_state"),
                       "classification": question["classification"], "state_gain_gate_passed": question["state_gain_gate_passed"]}
                      for question in public_questions for action in question["actions"]]
    _jsonl(out / "public_action_audit.jsonl.gz", public_actions)
    with (out / "field_gaps.csv").open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["question_id", "scope", "requirement", "status", "evidence_receipt_sha256"])
        writer.writeheader()
        for task in candidate_reviews:
            for requirement in task["required_missing_fields"]:
                writer.writerow({"question_id": task["task_id"], "scope": "local_raw_source_review",
                                 "requirement": requirement, "status": "unverified_or_absent_in_inspected_source",
                                 "evidence_receipt_sha256": inputs[(review / "raw_review/raw_source_review.json").relative_to(ROOT).as_posix()]})
        for question in public_questions:
            for requirement in question["required_field_gaps"]:
                writer.writerow({"question_id": question["id"], "scope": "public_source_review",
                                 "requirement": requirement, "status": "unverified_or_absent_in_inspected_source",
                                 "evidence_receipt_sha256": inputs[(review / "public_review/candidate_questions.json").relative_to(ROOT).as_posix()]})
    eligible = sum(row["state_gain_gate_passed"] for row in episode_rows) + sum(
        row["state_gain_gate_pass"] is True for row in candidate_reviews) + sum(
        row["state_gain_gate_passed"] is True for row in public_questions)
    write_json(out / "summary.json", {
        "stage_1_gate": "PASS" if eligible else "FAIL", "eligible_state_gain_tasks": eligible,
        "episodes": len(episode_rows), "episode_action_rows": len(rows),
        "classification_counts": dict(Counter(row["classification"] for row in episode_rows)),
        "source_join_hashes": lineage_hashes,
        "local_candidate_task_families": len(candidate_reviews),
        "public_candidate_questions": len(public_questions), "public_action_records": len(public_actions),
        "candidate_classification_counts": dict(Counter(row["classification"] for row in [*candidate_reviews, *public_questions])),
        "stop_reason": "No audited available-at/decision-at state with legal state-response sample relation." if not eligible else None,
        "ran": ["raw_metadata_lineage_reconstruction", "episode_action_source_audit", "checkpoint_and_public_source_review"],
        "not_run": ["stage_2_efficacy_freeze", "stage_3_state_gain_experiment", "state_shuffle", "state_removal",
                    "STATE_inference", "WorldV2_inference", "ReferenceWorld_substitution", "new_model_fit", "live_API_calls"],
        "questions": {question: "requires_stage_2_and_3" if eligible else "not_identifiable_from_audited_data" for question in (
            "state_gain", "prediction_gain", "selection_gain", "terminal_utility_gain")},
    })
    changed = [name for name, digest in {**inputs, **code}.items() if sha256(ROOT / name) != digest]
    write_json(out / "integrity.json", {"passed": not changed, "changed_inputs": changed,
                                      "output_sha256": {path.relative_to(out).as_posix(): sha256(path)
                                                        for path in sorted(out.rglob("*")) if path.is_file()}})
    if changed:
        raise RuntimeError("audit_input_changed")
    return json.loads((out / "summary.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True, help="Completed immutable independent review directory.")
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.out, arguments.review), indent=2))
