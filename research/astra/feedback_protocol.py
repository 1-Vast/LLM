"""Seal a full-menu pilot design and explicit scientific execution blockers."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


PILOT = "research/astra/results/20261002_gdsc_randomized_pilot_v2_retry1"


def freeze(root: Path, out: Path) -> dict:
    source = root / PILOT
    manifest = json.loads((source / "manifest.json").read_text())
    for name, expected in manifest.items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"pilot_source_hash_mismatch:{name}")
    def rows(name):
        with (source / name).open(encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream))
    roster, cultures, wells = (rows(name) for name in
                               ("proposed_roster.csv", "planned_cultures.csv", "randomized_wells.csv"))
    if len(roster) != 12 or len(cultures) != 24 or len(wells) != 480:
        raise ValueError("pilot_allocation_shape_mismatch")
    measured = sum(row["executed"].lower() == "true" for row in wells)
    if measured or any(row["raw_result_id"] or row["endpoint_value"] for row in wells):
        raise ValueError("design_freeze_cannot_open_measured_outcomes")
    prior = json.loads((source / "protocol.json").read_text())
    menu = [{"action_id": f"gdsc:{drug}:{dose:g}uM", "drug_id": drug, "intervention": name,
             "mode": "drug", "dose": dose, "dose_unit": "uM", "time_hours": 72,
             "readout": "ATP", "endpoint_unit": "blank-corrected fraction of matched vehicle"}
            for drug, name, dose in prior["menu"]]
    protocol = {
        "schema": "full_menu_background_pilot_v1",
        "registration": "sealed design and admission rules; execution and confirmation blocked",
        "task": "validate precommitted cheap-background recommendations against fixed interventions on a complete measured menu",
        "population": "the twelve named, recommendation-stratified pilot lines only; no representative-population claim",
        "actions": menu,
        "design": {"culture_starts": 24, "verified_independent_starts": 0,
                   "randomization_seed": prior["seed"], "randomized_allocation": PILOT + "/randomized_wells.csv",
                   "terminal_wells": 360, "baseline_and_blank_wells": 120,
                   "physical_unit": "verified separately initiated culture; sister aliquots share parent",
                   "dependencies": "technical wells share culture and controls; plates/day share environment; do not count wells as independent",
                   "split": "no pilot fitting or confirmation claim; future whole culture/day/parent-connected components remain in one split",
                   "timing": "24 h seeding wait, then 72 h treatment; proposal, not certified historical timing"},
        "inputs": {"background": "cell identity and precommitted roster recommendation only; usable-before-decision receipt required",
                   "state": "not used in primary pilot; destructive sister ATP is not same-cell state or a registered state-gain input",
                   "forbidden": ["future ATP", "target-derived action labels", "test-driven thresholds", "filled-in missing responses"]},
        "policies": {"primary": "frozen_original_C_roster_lookup", "primary_comparator": "fixed:gdsc:1032:2uM",
                     "secondary_fixed_actions": [action["action_id"] for action in menu],
                     "selection_strategy": "precommitted_lookup; no orchestrator default or online policy search",
                     "parameters": "C_action integer indexes the frozen ordered menu; never refit on pilot",
                     "predictions": "precommitted diagnostic/recommendation asset; no STATE or mechanism-conditional model claim",
                     "model_version": "original frozen recommendation; training checkpoint contract remains unknown",
                     "rule_version": "full_menu_background_pilot_v1",
                     "stop": "no new interventions, readouts, policy fitting, thresholds or repeats selected from pilot outcomes"},
        "analysis": {"normalized_readout": "(ATP_action - mean matched terminal blanks) / (mean matched terminal vehicle - mean matched terminal blanks)",
                     "response_utility": "1 - normalized_readout; no clipping, no death/GR/clinical interpretation",
                     "technical_aggregation": "prespecified QC-passing technical wells averaged within culture/action; retain every failed attempt",
                     "primary_estimand": "equal cell-line mean of within-culture recommendation utility minus fixed Afatinib utility",
                     "uncertainty": "pilot descriptive differences only; no physical confidence interval without certified culture/batch independence",
                     "action_contrast": "report complete-menu within-culture pair differences and reproducibility across the two starts; no state interaction claim",
                     "missing_actions": "unidentified unless trusted outcome/cost bounds were registered before outcomes; never substitute model output",
                     "qc": "matched culture/control/plate required, finite raw values and positive vehicle-minus-blank range; numeric assay thresholds require independent validation before execution",
                     "costs": "record failed/unexecuted attempts, measurement, preparation, time and compute; unknown prices remain unknown",
                     "abstention": "no new policy refusal threshold; invalid/unsupported records are unassessable with their costs retained",
                     "minimum_meaningful_net_gain": None, "failure_utility": None, "refusal_cost": None,
                     "cost_bound": None, "numeric_qc_thresholds": None, "power_and_confirmation_sample_size": None},
        "before_execution": ["verify actual culture/parent/sister identities and independent starts",
                             "operator-approved medium, controls, handling and numeric assay QC",
                             "background availability -> decision -> allocation -> actual execution chronology",
                             "full attempt, failure and outcome ledger with raw files and hashes",
                             "pre-outcome approved prices, failure/refusal utility and minimum meaningful gain"],
        "later_state_comparison": {"status": "blocked; requires a separate registration",
                    "design": "within-background full menu; background vs background plus cheap measured confluence/cell count, condition-local state permutation, same-input simple predictor",
                    "availability": "state processing complete and readable before decision; record collection/wait/drift/cost and legal sister linkage",
                    "freeze_before_outcomes": ["state modality and units", "independent development and blind-reference cultures",
                                             "whole physical batches into splits", "preprocessing/model/checkpoint/exposure audit",
                                             "action selector/budget/QC/cost/refusal/minimum gain", "analysis code"],
                    "stop": "if state only predicts common response magnitude or action contrasts do not generalize, stop the action-gain claim"},
        "mechanism_comparison": {"status": "blocked; ATP pilot cannot resolve mechanism",
                    "missing": ["same-target genetic/pharmacological menu", "measured engagement/knockdown",
                                "proximal function and phenotype", "calibrated competing-mechanism outcome predictions"]},
        "source_files": {PILOT + "/" + name: digest for name, digest in manifest.items()},
        "historical_exposure": "prior GDSC retrospective outcomes were already reviewed; only new unexecuted pilot outcomes could be held out",
    }
    blockers = list(protocol["before_execution"])
    readiness = {"schema": "scientific_readiness_v1", "status": "blocked", "physical_executions": measured,
                 "qualified_scientific_task": False, "blockers": blockers,
                 "unknown_contract_fields": [key for key, value in protocol["analysis"].items() if value is None],
                 "will_not_run": ["background policy value", "state gain", "agent acquisition gain", "mechanism benefit"],
                 "continue": "fill independent pre-outcome records and sign a new immutable execution registration; collect full menu",
                 "modify": "replace unsupported conditions or re-scope population before seeing new outcomes; new version required",
                 "stop": "failure to supply provenance/chronology or complete menu blocks evaluation; no reconstruction substitutes for measurements"}
    out.mkdir(parents=True, exist_ok=False)
    for name, value in (("protocol.json", protocol), ("readiness.json", readiness)):
        (out / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    files = {name: hashlib.sha256((out / name).read_bytes()).hexdigest() for name in ("protocol.json", "readiness.json")}
    files["builder_source"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (out / "freeze.json").write_text(json.dumps(files, indent=2) + "\n", encoding="utf-8")
    return readiness


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.root, args.out)))
