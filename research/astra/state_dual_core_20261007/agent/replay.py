"""Native-RNA acquisition replay. Policies never receive unpurchased outcomes.

The CSV contract is one dose-condition per row: condition_id, drug, dose_uM,
plate, cell, time_hours, split, observed_rms, reference_prediction,
state_prediction. All doses of a drug must share a split. This is a research
replay over public observations, not execution of new biological experiments.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from agent.case_store import CaseState, CaseStore, MeasurementResult
from agent.memory import RunLogger
from agent.prediction import PredictionCoordinator
from maestro.models import EvidenceAction, EvidenceActionKind, EvidenceKind
from virtual_cell.interface import (Intervention, ModelCapabilities, PredictionCache,
    PredictionRequest, QueryAssessment, QuerySupport, StatePrediction, SystemContext,
    prediction_request_errors)

ENDPOINT = "native_rna_delta_rms"
CONDITIONS = ("drug", "dose_uM", "plate", "cell", "time_hours")


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def load_records(path):
    records = pd.read_csv(path).rename(columns={"world_reference": "reference_prediction",
        "world_state": "state_prediction", "observed_magnitude": "observed_rms", "dose": "dose_uM"})
    required = {"condition_id", "split", "observed_rms", "reference_prediction",
                "state_prediction", *CONDITIONS}
    if required - set(records):
        raise ValueError("missing_columns:" + ",".join(sorted(required - set(records))))
    if records.condition_id.duplicated().any():
        raise ValueError("duplicate_condition")
    if records.groupby("drug").split.nunique().max() != 1:
        raise ValueError("drug_split_leakage")
    if "chemical_group" in records and records.groupby("chemical_group").split.nunique().max() != 1:
        raise ValueError("chemical_group_split_leakage")
    if not set(records.split) <= {"train", "development", "calibration", "evaluation"}:
        raise ValueError("unknown_partition")
    if not np.isfinite(records[["dose_uM", "time_hours", "observed_rms",
                               "reference_prediction", "state_prediction"]]).all().all():
        raise ValueError("nonfinite_record")
    if (records.dose_uM < 0).any():
        raise ValueError("negative_dose")
    return records


def paired_doses(records):
    """Same-cell/time low/high pairs; each dose uses its own source-plate controls.

    Dose and plate are confounded in this source. The empirical residual bridge
    therefore transports across BOTH, not a causal or continuous dose model.
    """
    pairs = []
    for _, group in records.groupby(["drug", "cell", "time_hours", "split"]):
        if "response_role" in group:
            if set(group.response_role) != {"screen", "technical_validation"} or len(group) != 2:
                raise ValueError("invalid_technical_screen_roles")
            screen = group[group.response_role == "screen"].iloc[0].to_dict()
            validation = group[group.response_role == "technical_validation"].iloc[0].to_dict()
            if any(screen[key] != validation[key] for key in CONDITIONS):
                raise ValueError("technical_screen_condition_mismatch")
            if screen["subset_sha256"] == validation["subset_sha256"]:
                raise ValueError("technical_screen_subset_identity_collision")
            pairs.append((screen, validation))
            continue
        group = group.sort_values(["dose_uM", "condition_id"])
        if group.dose_uM.nunique() < 2:
            continue
        if group.dose_uM.duplicated().any():
            raise ValueError("ambiguous_source_event")
        pairs.append((group.iloc[0].to_dict(), group.iloc[-1].to_dict()))
    return pairs


def fit_transfer(pairs, world):
    """One fixed regularized slope, training drugs only; no tuning opportunity."""
    train = [(lo, hi) for lo, hi in pairs if lo["split"] == "train"]
    if len(train) < 3:
        raise ValueError("insufficient_training_drug_pairs")
    column = world + "_prediction"
    low = np.array([lo["observed_rms"] - lo[column] for lo, _ in train])
    high = np.array([hi["observed_rms"] - hi[column] for _, hi in train])
    slope = float(low @ high / (low @ low + max(float(low @ low) * 0.1, 1e-12)))
    return {"slope": slope, "forecast_update_samples": (slope * low).tolist(),
            "unacquired_rmse": float(np.sqrt(np.mean(high ** 2))),
            "acquired_rmse": float(np.sqrt(np.mean((high - slope * low) ** 2))),
            "training_drugs": sorted({lo["drug"] for lo, _ in train}),
            "endpoint": ENDPOINT, "world": world,
            "transport": ("technical_screen_to_disjoint_cell_validation; same condition and shared reference denominator"
                if train[0][0].get("response_role") else "empirical_across_dose_and_source_plate; separate matched controls per dose"),
            "uncertainty_status": "training residual diagnostic, not calibrated probability"}


class FrozenForecasts:
    """Research receipt backend; does not rerun or replace the STATE checkpoint."""
    def __init__(self, public, world, version):
        self.public = {str(row["condition_id"]): row for row in public}
        self.world, self.version = world, version
        self.name = "native_rna_frozen_receipts:" + version

    def capabilities(self):
        return ModelCapabilities("native-rna-receipts", self.version, "audited frozen features",
            "exact observed categorical drug-dose", ("chemical",), True, False, False, None)

    def assess_query(self, request):
        row = self.public.get(request.observation_context.get("condition_id"))
        supported = row is not None and all((
            request.intervention.identifier == row["drug"],
            request.intervention.dose == row["dose_uM"],
            request.intervention.dose_unit == "uM",
            request.intervention.time_hours == row["time_hours"],
            request.context.identifier == row["cell"],
            request.observation_context.get("plate") == str(row["plate"]),
            request.observation_context.get("assay") == "single_cell_RNA",
            request.observation_context.get("response_role") == row.get("response_role", "full_pseudobulk"),
            request.observation_context.get("subset_sha256") == row.get("subset_sha256", "not_split"),
            request.observation_context.get("model_provenance_sha256") == row.get("model_provenance_sha256", "legacy_diagnostic"),
            request.readouts == (ENDPOINT,),
        ))
        return QueryAssessment(QuerySupport.SUPPORTED if supported else QuerySupport.UNSUPPORTED,
            (), () if supported else ("condition_receipt_mismatch",), self.capabilities())

    def predict(self, request):
        row = self.public[request.observation_context["condition_id"]]
        return StatePrediction(True, {ENDPOINT: float(row[self.world + "_prediction"])}, None,
            ("conditional_on_QC_valid_RNA_observation", "no_ATP_or_survival_claim"),
            supported_variables=(ENDPOINT,), request_id=request.request_id,
            model_version=self.version, confidence=None, in_distribution=None,
            uncertainty_components={"transport": "unquantified"}, compute_cost=0.0)


def public_rows(pairs):
    allowed = {"condition_id", "split", "reference_prediction", "state_prediction", "response_role", "subset_sha256",
               "model_provenance_sha256", *CONDITIONS}
    return [{key: value for key, value in row.items() if key in allowed}
            for pair in pairs for row in pair]


def make_request(row, case_id, plan_version, version, evidence_digest="none"):
    return PredictionRequest(f"{case_id}-{plan_version}-{row['condition_id']}", case_id,
        "native-rna-comparison", plan_version,
        Intervention(row["drug"], "chemical", (), float(row["dose_uM"]), "uM", float(row["time_hours"])),
        SystemContext(row["cell"], "Public historical RNA context", dataset_id=str(row["condition_id"]),
                      control_dataset_id=str(row["plate"]) + ":DMSO"),
        (ENDPOINT,), version, observation_context={"condition_id": str(row["condition_id"]),
            "plate": str(row["plate"]), "assay": "single_cell_RNA", "evidence_digest": evidence_digest,
            "response_role": row.get("response_role", "full_pseudobulk"),
            "subset_sha256": row.get("subset_sha256", "not_split"),
            "model_provenance_sha256": row.get("model_provenance_sha256", "legacy_diagnostic"),
            "head_update": "fixed_training_residual_transfer_v1"})


def action_for(row, kind="acquire"):
    return EvidenceAction(f"{kind}-{row['condition_id']}",
        "Retrieve source-bound public RNA screen/reference" if kind == "acquire" else "Reveal committed RNA validation outcome",
        1.0, (), kind=EvidenceActionKind.EVIDENCE_REVIEW,
        time_hours=float(row["time_hours"]), expected_conditions={
            "condition_id": str(row["condition_id"]), "dose_uM": str(row["dose_uM"]),
            "drug": row["drug"], "plate": str(row["plate"]), "assay": "single_cell_RNA",
            "response_role": row.get("response_role", "full_pseudobulk"),
            "subset_sha256": row.get("subset_sha256", "not_split")},
        execution_context=row["cell"], readout=ENDPOINT)


def purchase(store, case_id, row, kind="acquire", prediction=None):
    """Evaluator boundary: commit and reserve before reading the response scalar."""
    action = action_for(row, kind)
    snapshot = store.record_plan(case_id, [action], ready_to_measure=True, context_identifier=row["cell"])
    if snapshot.state is not CaseState.AWAITING_RESULT:
        raise ValueError("budget_or_plan_refused")
    if prediction is not None:
        store.record_prediction(case_id, snapshot.plan_version, action.identifier,
            prediction[0].request_id, {"request": prediction[0].to_dict(), "prediction": asdict(prediction[1])})
    started = time.perf_counter()
    observed = float(row["observed_rms"])
    result = MeasurementResult(action.identifier, "Retrieved historical native RNA endpoint; not a new experiment",
        "public_c39:" + str(row["condition_id"]), row["cell"], float(row["time_hours"]), None, True,
        conditions=action.expected_conditions, metrics={ENDPOINT: str(observed)},
        evidence_kind=EvidenceKind.RETRIEVED_SOURCE,
        limitations=("biological_replicate_count_unknown", "source_exposed_previously",),
        result_id=f"{case_id}-{snapshot.plan_version}-{row['condition_id']}", plan_version=snapshot.plan_version)
    imported = store.import_measurement(case_id, result)
    assert imported.created
    return observed, {"action": action.identifier, "result_id": result.result_id,
        "plan_version": snapshot.plan_version, "condition_id": str(row["condition_id"]),
        "kind": kind, "retrieval_seconds": time.perf_counter() - started,
        "laboratory_credits": 0, "replay_access_units": 1, "downloaded_bytes": 0,
        "response": observed, "result": result}


def sensitivity_choice(view):
    """Competent boundary policy: largest reducible variance / squared decision gap."""
    eligible = [row for row in view if not row["acquired"]]
    if not eligible:
        return None
    leader = max(float(row["forecast"]) for row in view)
    return max(eligible, key=lambda row: (row["reducible_variance"] /
        (1e-12 + (leader - row["forecast"]) ** 2 + row["sigma"] ** 2), row["condition_id"]))["condition_id"]


def empirical_value_choice(view):
    """Integrate the fixed training update distribution for each potential acquisition."""
    leader = max(row["forecast"] for row in view)
    choices = []
    for row in view:
        if row["acquired"]:
            continue
        alternatives = max(other["forecast"] for other in view if other["condition_id"] != row["condition_id"])
        samples = row["forecast_update_samples"]
        expected_gain = float(np.mean([max(alternatives, row["forecast"] + change) for change in samples])) - leader
        choices.append((expected_gain, row["condition_id"]))
    if not choices or max(choices)[0] <= 0:
        return None
    return max(choices)[1]


class LLMAcquisitionPolicy:
    """One bounded real API choice; deterministic admission and fallback stay external."""
    def __init__(self, client):
        self.client, self.receipts = client, []

    def __call__(self, view):
        started = time.perf_counter()
        request = {"objective": "Select the stronger measured high-dose native RNA perturbation magnitude.",
            "budget": "At most one public screen/reference observation before committing one validation candidate.",
            "scope": "One historical cell, same-plate controls, 24h RNA. No viability or therapeutic benefit implied.",
            "uncertainty": "RMSE is training residual error, not calibrated probability. Predictions may be wrong.",
            "update": "The fixed training-only residual transfer will update the acquired candidate's validation forecast. Response roles specify whether this is cross-dose transport or disjoint-cell technical screening. Technical validation is not an independent culture replicate.",
            "candidates": view, "sensitivity_recommendation": sensitivity_choice(view),
            "empirical_value_recommendation": empirical_value_choice(view),
            "response_schema": {"acquire_condition_id": "one listed acquisition condition_id or null to stop", "reason": "brief"}}
        try:
            answer, response = self.client.complete_json([
                {"role": "system", "content": "You choose a scientific information acquisition. Use only supplied facts. Return JSON; never invent outcomes or alter evidence permissions."},
                {"role": "user", "content": json.dumps(request, sort_keys=True)}], max_tokens=350)
            selected = answer.get("acquire_condition_id")
            if selected is not None and selected not in {row["condition_id"] for row in view if not row["acquired"]}:
                raise ValueError("invalid_llm_action")
            receipt = {"request": request, "answer": answer, "model": response.model,
                "usage": dict(response.usage), "status": "accepted", "api_calls": 1,
                "actual_billed_cost": None, "cost_status": "provider response supplies tokens, no billed amount"}
        except Exception as error:
            selected = sensitivity_choice(view)
            receipt = {"request": request, "status": "failed_deterministic_fallback", "error_type": type(error).__name__,
                "usage": dict(self.client.provider_usage), "api_calls": 1,
                "actual_billed_cost": None, "cost_status": "unknown; failed attempt retained"}
        receipt["elapsed_seconds"] = time.perf_counter() - started
        self.receipts.append(receipt)
        return selected


def replay_pair(pair, world, transfer, output, case_id, policy=sensitivity_choice, shared_acquisitions=None):
    output.mkdir(parents=True, exist_ok=True)
    store = CaseStore(output / "cases.sqlite")
    store.open_case(case_id, budget=2.0)  # one lower-dose access plus one committed high-dose reveal
    public = public_rows(pair)
    version = world + ":" + digest({"public": public, "transfer": transfer})
    coordinator = PredictionCoordinator(FrozenForecasts(public, world, version), RunLogger(output / "logs"), cache=PredictionCache())
    candidates, actions = [], []
    for low, high in pair:
        request = make_request(high, case_id, 1, version)
        _, prediction = coordinator.predict(request, case_id)
        if not prediction.applicable:
            raise ValueError("forecast_refused")
        candidates.append({"condition_id": str(low["condition_id"]), "drug": low["drug"],
            "forecast": prediction.state_change[ENDPOINT], "sigma": transfer["unacquired_rmse"],
            "reducible_variance": max(0, transfer["unacquired_rmse"] ** 2 - transfer["acquired_rmse"] ** 2),
            "acquired": False, "dose_uM": high["dose_uM"], "acquisition_dose_uM": low["dose_uM"],
            "target_plate": str(high["plate"]), "acquisition_plate": str(low["plate"]),
            "transport": ("technical_screen_to_disjoint_cells_shared_reference" if low.get("response_role")
                else "same_plate" if low["plate"] == high["plate"] else "across_dose_and_source_plate"),
            "acquisition_role": low.get("response_role", "lower_dose_reference"),
            "validation_role": high.get("response_role", "high_dose_pseudobulk"),
            "residual_transfer_slope": transfer["slope"]})
        candidates[-1]["forecast_update_samples"] = transfer.get("forecast_update_samples", [0.0])
    initial = max(range(2), key=lambda index: (candidates[index]["forecast"], candidates[index]["condition_id"]))
    # A policy sees only these legal forecasts and already acquired information.
    selected = (shared_acquisitions[0] if shared_acquisitions else None) if shared_acquisitions is not None else policy([dict(row) for row in candidates])
    if selected is not None:
        matches = [index for index, row in enumerate(candidates) if row["condition_id"] == selected]
        if len(matches) != 1:
            raise ValueError("policy_selected_unavailable_action")
        index = matches[0]
        low, _ = pair[index]
        observed, receipt = purchase(store, case_id, low)
        receipt.pop("result")
        actions.append(receipt)
        candidates[index]["forecast"] += transfer["slope"] * (observed - low[world + "_prediction"])
        candidates[index]["sigma"] = transfer["acquired_rmse"]
        candidates[index]["acquired"] = True
    chosen = max(range(2), key=lambda index: (candidates[index]["forecast"], candidates[index]["condition_id"]))
    high = pair[chosen][1]
    request = make_request(high, case_id, store.snapshot(case_id).plan_version + 1, version, digest(actions))
    _, prediction = coordinator.predict(request, case_id)
    prediction = replace(prediction, state_change={ENDPOINT: candidates[chosen]["forecast"]})
    observed, receipt = purchase(store, case_id, high, "confirm", (request, prediction))
    receipt.pop("result")
    actions.append(receipt)
    store.record_decision(case_id, status="decided")
    return {"case_id": case_id, "world": world, "drugs": [row[0]["drug"] for row in pair],
        "initial_choice": pair[initial][1]["condition_id"], "final_choice": high["condition_id"],
        "changed": initial != chosen, "observed_selected_rms": observed,
        "initial_selected_rms_for_posthoc_scoring_only": float(pair[initial][1]["observed_rms"]),
        "policy_view_after_acquisition": candidates, "actions": actions,
        "budget": store.budget_status(case_id), "api_calls": int(isinstance(policy, LLMAcquisitionPolicy))}


def opportunity(records, output, acquisition_rank="lowest", policy_name="sensitivity"):
    if acquisition_rank == "middle":
        records = records.sort_values("dose_uM").groupby("drug", group_keys=False).tail(2)
    elif acquisition_rank != "lowest":
        raise ValueError("unknown_acquisition_rank")
    pairs = paired_doses(records)
    policy = {"sensitivity": sensitivity_choice, "empirical_value": empirical_value_choice,
              "stop": lambda view: None}[policy_name]
    development = [pair for pair in pairs if pair[0]["split"] == "development"]
    results, summary = [], {}
    for world in ("reference", "state"):
        transfer = fit_transfer(pairs, world)
        cases = []
        for index, pair in enumerate(combinations(development, 2)):
            result = replay_pair(pair, world, transfer, output, f"development-{world}-{index}", policy=policy)
            # Diagnostic only: evaluate both possible acquisitions using exposed development outcomes.
            alternative = []
            for acquired in (0, 1):
                forecasts = [float(hi[world + "_prediction"]) for _, hi in pair]
                lo = pair[acquired][0]
                forecasts[acquired] += transfer["slope"] * (lo["observed_rms"] - lo[world + "_prediction"])
                chosen = max(range(2), key=lambda i: (forecasts[i], str(pair[i][0]["condition_id"])))
                alternative.append(float(pair[chosen][1]["observed_rms"]))
            base = result["initial_selected_rms_for_posthoc_scoring_only"]
            result["diagnostic_best_acquisition_gain"] = max([base, *alternative]) - base
            cases.append(result)
        results.extend(cases)
        gains = [row["observed_selected_rms"] - row["initial_selected_rms_for_posthoc_scoring_only"] for row in cases]
        summary[world] = {"cases": len(cases), "independent_drugs": len(development),
            "changed_comparisons": sum(row["changed"] for row in cases),
            "mean_gain": float(np.mean(gains)) if gains else None,
            "maximum_mean_acquisition_gain_diagnostic": float(np.mean([row["diagnostic_best_acquisition_gain"] for row in cases])) if cases else None,
            "median_absolute_development_transfer_error": float(np.median([
                abs(hi["observed_rms"] - hi[world + "_prediction"] - transfer["slope"] *
                    (lo["observed_rms"] - lo[world + "_prediction"])) for lo, hi in development])),
            "transfer": transfer}
    output.mkdir(parents=True, exist_ok=True)
    (output / "opportunity_cases.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (output / "opportunity.json").write_text(json.dumps({"partition": "development_only", "acquisition_rank": acquisition_rank,
        "policy": policy_name, "results": summary,
        "independence": "Pairs share drugs and one cell/source; pair count is not biological replication.",
        "no_oracle_policy": True, "api_calls": 0, "api_tokens": 0, "api_cost": 0}, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--acquisition-rank", choices=["lowest", "middle"], default="lowest")
    parser.add_argument("--policy", choices=["sensitivity", "empirical_value", "stop"], default="sensitivity")
    args = parser.parse_args()
    print(json.dumps(opportunity(load_records(args.records), args.output, args.acquisition_rank, args.policy), indent=2))
