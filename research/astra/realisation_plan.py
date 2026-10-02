"""Emit an unexecuted, measured-realisation development design and intake templates."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
from pathlib import Path


REFERENCE_FILES = {
    "workflow.py": "tools/case_memory/workflow.py",
    "learned_response.py": "src/virtual_cell/learned_response.py",
    "external_data.py": "tools/datasets/lincs_pack.py",
    "orchestrator.py": "src/agent/orchestrator.py",
    "DUAL_CORE_OPTIMIZATION.md": "research/astra/DUAL_CORE_OPTIMIZATION.md",
}

TABLES = {
    "conditions.csv": ("case_id", "plan_version", "action_id", "attempt_id", "culture_id", "parent_id",
                       "physical_batch_id", "cell_background", "target_id", "modality", "intervention_id",
                       "dose", "dose_unit", "schedule", "assigned_at", "executed_at", "execution_status",
                       "failure_reason", "matched_control_attempt_id"),
    "measurements.csv": ("result_id", "case_id", "plan_version", "action_id", "attempt_id", "sample_id",
                         "parent_id", "physical_batch_id", "quantity", "value", "unit", "sampled_at",
                         "processing_completed_at", "available_at", "qc_passed", "qc_reason",
                         "source_record_id", "source_file", "source_row", "source_file_sha256"),
    "events_costs.csv": ("case_id", "plan_version", "attempt_id", "event", "occurred_at", "resource",
                        "amount", "unit", "unit_price", "currency", "cost", "price_source", "failure_reason",
                        "source_record_id", "source_file", "source_file_sha256"),
}


def audit_review_inputs(directory: Path, root: Path) -> list[dict]:
    """Inspect supplied files without importing or executing their contents."""
    rows = []
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        reference = REFERENCE_FILES.get(path.name)
        row = dict(path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                   role="unreviewed_input", reference=reference, measured_observations=None)
        if path.suffix == ".py":
            tree = ast.parse(raw.decode("utf-8-sig"))
            row.update(role="source_code", measured_observations=False,
                       top_level_definitions=[node.name for node in tree.body
                                              if isinstance(node, (ast.FunctionDef, ast.ClassDef))])
        elif path.name in REFERENCE_FILES:
            row.update(role="review_report", measured_observations=False)
        if reference:
            current = (root / reference).read_bytes()
            row.update(reference_sha256=hashlib.sha256(current).hexdigest(),
                       byte_equal_to_current=raw == current)
        rows.append(row)
    return rows


def specification() -> dict:
    return {
        "status": "design_only_not_registered_not_executed",
        "scientific_question": "Does predicting measured intervention realisation improve held-out intervention contrasts?",
        "candidate_scope": {
            "background": "PC9 EGFR-mutant NSCLC; availability and identity authentication unconfirmed",
            "target": "EGFR",
            "menu": ["vehicle", "two development-fixed osimertinib doses", "two independent EGFR CRISPRi guides",
                     "non-targeting guide and matched delivery controls"],
            "doses_and_schedules": None,
            "claim_domain": "One background, unseen culture batches and registered conditions; no cross-lineage claim",
        },
        "cheap_inputs": ["authenticated background", "nominal intervention identity", "dose and schedule",
                         "decision-available cell count and growth/viability markers"],
        "optional_input": "RNA only for a separately authenticated backend; not required by this design",
        "measurements": {
            "realisation": "Absolute phospho-EGFR relative to matched vehicle and loading control; retain total EGFR separately",
            "proximal_function": "Phospho-ERK with total/loading controls; pathway proxy, not unique mechanism proof",
            "phenotype": "ATP with vehicle, blank and independent cell-count control; fixed endpoint time pending",
            "timing": "Pilot fixes modality-specific preparation and matched comparison horizons; do not assume CRISPRi and drug onset equal",
        },
        "training_comparison": {
            "direct": "phenotype = h(cheap covariates, nominal intervention)",
            "constrained": "realisation_hat = f(cheap covariates, nominal intervention); phenotype = g(covariates, realisation_hat, modality)",
            "training_features": "Use inner-batch out-of-fold realisation predictions to fit g; never fit preprocessing or f on an outer validation/test batch",
            "leakage_guard": "Measured post-action realisation is a training target. At decision time use predicted realisation; newly measured values enter only after a real feedback event",
            "validation": "Whole physical batches held out; development-only preprocessing, calibration, hyperparameters and contrast margins",
            "outcomes": ["realisation prediction error and calibration", "phenotype error", "paired action-difference error",
                         "rank changes", "measured utility and refusal contribution if separately admitted"],
            "limitations": "A supervised effect predictor does not identify causal mediation or mechanism-conditional likelihoods",
        },
        "two_round_feedback": {
            "round_1": "Select a registered intervention/readout/time bundle under a frozen budget; commit exact plan and prediction identities",
            "feedback": "Import actual matched result/QC/failure/cost records; update only through the existing evidence admission authority",
            "round_2": "Choose registered orthogonal function/rescue evidence, additional measurement or stopping based on admitted results",
            "likelihood_boundary": "No numerical mechanism Bayes factors or information gain without separately validated hypothesis-conditional probabilities",
            "controls": ["simple agent + simple predictor", "proposed agent + simple predictor",
                         "simple agent + constrained predictor", "proposed agent + constrained predictor",
                         "fixed action", "state permutation", "modality/realisation ablations"],
        },
        "blocking_unknowns": ["actual matched realisation/function/phenotype observations", "dose/time/QC specification",
                              "complete execution and failure denominator", "assay and compute prices",
                              "minimum meaningful gain and refusal loss", "physical variance and confirmation sample size"],
        "stop_rules": ["Stop training until measurement identities, controls, units and raw provenance are audited",
                       "Stop this decision task if development action differences lack meaningful headroom",
                       "Modify the model if realised-action contrast prediction fails independent development validation",
                       "Promote no scientific default without frozen independent matched-budget confirmation"],
        "planned_attempts_executed": 0,
        "training_executed": False,
        "biological_comparison_executed": False,
    }


def run(inputs: Path, output: Path, root: Path) -> dict:
    rows = audit_review_inputs(inputs, root)
    output.mkdir(parents=True, exist_ok=False)
    unknown = [row["path"] for row in rows if row["role"] == "unreviewed_input"]
    report = {"inputs": rows, "unknown_input_files": unknown,
              "matched_training_table_present": None if unknown else False, "design": specification()}
    (output / "readiness.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for name, fields in TABLES.items():
        with (output / name).open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerow(fields)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    report = run(args.inputs, args.out, root)
    print(json.dumps({"input_files": len(report["inputs"]), "unknown_files": len(report["unknown_input_files"]),
                      "status": report["design"]["status"], "training_executed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
