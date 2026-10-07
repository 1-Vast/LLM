"""Bounded sequential screen selection with explicit train-only forecast uncertainty.

This is a non-LLM decision agent. It does not establish biological independence
or learn cross-drug correlations from a single culture. Actual evidence remains
in the existing CaseStore; forecasts use the existing PredictionCoordinator.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
LEGACY = ROOT / "research/astra/state_dual_core_20261007/agent/replay.py"
spec = importlib.util.spec_from_file_location("frozen_native_replay", LEGACY)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
LEGACY_ENDPOINT = r.ENDPOINT


class BoundForecasts(r.FrozenForecasts):
    def assess_query(self, request):
        result = super().assess_query(request)
        row = self.public.get(request.observation_context.get("condition_id"))
        if row and row.get("control_subset_sha256") != request.observation_context.get("control_subset_sha256"):
            return replace(result, support=r.QuerySupport.UNSUPPORTED,
                           limitations=("control_subset_identity_mismatch",))
        return result


def request_for(row, *args):
    request = r.make_request(row, *args)
    if row.get("control_subset_sha256"):
        request = replace(request, observation_context={**request.observation_context,
            "control_subset_sha256": str(row["control_subset_sha256"])})
    return request


def load_study_records(path):
    table = pd.read_csv(path)
    if "endpoint" in table:
        endpoints = set(table.endpoint)
        if len(endpoints) != 1:
            raise ValueError("mixed_endpoints")
        endpoint = next(iter(endpoints))
        if endpoint != "signed_noise_corrected_mean_squared_native_rna_delta":
            raise ValueError("unregistered_new_endpoint")
        if "observed_value" not in table:
            raise ValueError("signed_observed_value_required")
        table = table.rename(columns={"observed_value": "observed_rms"})
        # The old frozen module is privately loaded above. Its generic numeric
        # receipt contract is reused under an explicitly different readout;
        # neither its source nor old frozen studies are altered.
        r.ENDPOINT = endpoint
    else:
        r.ENDPOINT = LEGACY_ENDPOINT
        table = r.load_records(path)
    if table.condition_id.duplicated().any() or table.groupby("drug").split.nunique().max() != 1:
        raise ValueError("condition_or_partition_identity_error")
    if not np.isfinite(table[["observed_rms", "reference_prediction", "state_prediction"]]).all().all():
        raise ValueError("nonfinite_endpoint")
    return table


def expected_best(means, available, samples, depth, counts=None):
    """Exact finite empirical integral; residual marginals are exchangeable.

    This independent-marginal planning approximation is not an estimated joint
    biological law. It is frozen and shared by both policies. Only the selected
    action is updated from real purchased evidence during replay.
    """
    stop = float(max(means))
    scores = {}
    if depth <= 0:
        return stop, scores
    for index in available:
        if counts is not None:
            counts["action_integrals"] += 1
            counts["empirical_outcomes"] += len(samples)
        remaining = tuple(other for other in available if other != index)
        if depth == 1:
            alternative = max(value for other, value in enumerate(means) if other != index)
            score = float(np.maximum(alternative, means[index] + samples).mean())
        else:
            outcomes = []
            for update in samples:
                updated = means.copy()
                updated[index] += update
                future, _ = expected_best(updated, remaining, samples, depth - 1, counts)
                outcomes.append(future)
            score = float(np.mean(outcomes))
        scores[index] = score
    return max([stop, *scores.values()]), scores


def choose(view, remaining, samples, policy):
    started = time.perf_counter()
    means = np.array([row["forecast"] for row in view], dtype=float)
    available = tuple(index for index, row in enumerate(view) if not row["acquired"])
    depth = 1 if policy == "myopic" else min(remaining, 2)
    if policy == "stop" or not available or not remaining:
        return None, {"stop_value": float(means.max()), "action_values": {}, "depth": 0}
    counts = {"action_integrals": 0, "empirical_outcomes": 0}
    _, scores = expected_best(means, available, np.asarray(samples), depth, counts)
    maximum = max(scores.values())
    tied = [index for index in scores if maximum - scores[index] <= 1e-12]
    best = max(tied, key=lambda index: view[index]["condition_id"])
    action = best if scores[best] > float(means.max()) + 1e-12 else None
    return action, {"stop_value": float(means.max()), "action_values": {
        view[index]["condition_id"]: value for index, value in scores.items()}, "depth": depth,
        "compute_counts": counts, "planning_seconds": time.perf_counter() - started}


def episode(candidates, world, transfer, output, case_id, policy, max_screens=2, shared_actions=None):
    output.mkdir(parents=True, exist_ok=True)
    store = r.CaseStore(output / "cases.sqlite")
    store.open_case(case_id, budget=float(max_screens + 1))
    public = r.public_rows(candidates)
    for public_row, original in zip(public, [row for pair in candidates for row in pair]):
        if original.get("control_subset_sha256"):
            public_row["control_subset_sha256"] = str(original["control_subset_sha256"])
    version = world + ":sequential:" + r.digest({"public": public, "transfer": transfer,
                                                "legacy_source": sha256(LEGACY.read_bytes()).hexdigest()})
    coordinator = r.PredictionCoordinator(BoundForecasts(public, world, version),
        r.RunLogger(output / "logs"), cache=r.PredictionCache())
    view, steps = [], []
    started = time.perf_counter()
    for screen, validation in candidates:
        request = request_for(validation, case_id, 1, version)
        _, answer = coordinator.predict(request, case_id)
        if not answer.applicable:
            raise ValueError("unsupported_candidate")
        view.append({"condition_id": screen["condition_id"], "drug": screen["drug"],
            "forecast": answer.state_change[r.ENDPOINT], "acquired": False,
            "screen_dose_uM": screen["dose_uM"], "plate": screen["plate"],
            "role": "technical_screen_to_disjoint_cell_validation"})
    initial = max(range(len(view)), key=lambda i: (view[i]["forecast"], view[i]["condition_id"]))
    for turn in range(max_screens):
        index, values = choose(view, max_screens - turn, transfer["forecast_update_samples"], policy)
        if shared_actions is not None:
            action_id = shared_actions[turn] if turn < len(shared_actions) else None
            index = next((i for i, row in enumerate(view) if row["condition_id"] == action_id), None)
            if action_id is not None and index is None:
                raise ValueError("unavailable_shared_action")
        step = {"turn": turn, "public_view": [dict(row) for row in view], "planning": values,
                "selected": None if index is None else view[index]["condition_id"]}
        if index is None:
            steps.append(step)
            break
        if view[index]["acquired"]:
            raise ValueError("duplicate_acquisition")
        screen = candidates[index][0]
        observed, receipt = r.purchase(store, case_id, screen)
        receipt.pop("result")
        delta = transfer["slope"] * (observed - screen[world + "_prediction"])
        view[index]["forecast"] += delta
        view[index]["acquired"] = True
        step.update(receipt=receipt, forecast_update=delta)
        steps.append(step)
    selected = max(range(len(view)), key=lambda i: (view[i]["forecast"], view[i]["condition_id"]))
    validation = candidates[selected][1]
    request = request_for(validation, case_id, store.snapshot(case_id).plan_version + 1, version, r.digest(steps))
    _, prediction = coordinator.predict(request, case_id)
    prediction = replace(prediction, state_change={r.ENDPOINT: view[selected]["forecast"]})
    observed, receipt = r.purchase(store, case_id, validation, "confirm", (request, prediction))
    receipt.pop("result")
    store.record_decision(case_id, status="decided")
    return {"case_id": case_id, "world": world, "policy": policy,
        "drugs": [pair[0]["drug"] for pair in candidates], "steps": steps,
        "initial_choice": candidates[initial][1]["condition_id"],
        "final_choice": validation["condition_id"], "endpoint": r.ENDPOINT, "selected_value": observed,
        "validation_receipt": receipt, "budget": store.budget_status(case_id),
        "elapsed_seconds": time.perf_counter() - started,
        "no_update_value_postdecision": float(candidates[initial][1]["observed_rms"])}


def hindsight(candidates, world, transfer):
    """Development diagnostic upper bound. Not called by any action policy."""
    base = np.array([validation[world + "_prediction"] for _, validation in candidates])
    values = []
    for count in range(3):
        for acquired in combinations(range(len(candidates)), count):
            forecast = base.copy()
            for index in acquired:
                screen = candidates[index][0]
                forecast[index] += transfer["slope"] * (screen["observed_rms"] - screen[world + "_prediction"])
            selected = max(range(len(forecast)), key=lambda i: (forecast[i], candidates[i][0]["condition_id"]))
            values.append(float(candidates[selected][1]["observed_rms"]))
    return max(values)


def development(records_path, output):
    if output.exists():
        raise FileExistsError("preserve_existing_run")
    all_pairs = r.paired_doses(load_study_records(records_path))
    development_pairs = [pair for pair in all_pairs if pair[0]["split"] == "development"]
    rows = []
    for world in ("reference", "state"):
        transfer = r.fit_transfer(all_pairs, world)
        for index, candidates in enumerate(combinations(development_pairs, 4)):
            for policy in ("myopic", "lookahead"):
                row = episode(candidates, world, transfer, output, f"dev-{world}-{policy}-{index}", policy)
                row["hindsight_ceiling"] = hindsight(candidates, world, transfer)
                rows.append(row)
    summary = {world: {policy: {"mean_selected_value": float(np.mean([x["selected_value"] for x in rows if x["world"] == world and x["policy"] == policy])),
         "mean_gain_vs_no_update": float(np.mean([x["selected_value"] - x["no_update_value_postdecision"] for x in rows if x["world"] == world and x["policy"] == policy])),
         "mean_gap_to_hindsight_ceiling": float(np.mean([x["hindsight_ceiling"] - x["selected_value"] for x in rows if x["world"] == world and x["policy"] == policy])),
         "mean_screens": float(np.mean([sum(step["selected"] is not None for step in x["steps"]) for x in rows if x["world"] == world and x["policy"] == policy]))}
         for policy in ("myopic", "lookahead")} for world in ("reference", "state")}
    summary["limitations"] = ["15 overlapping four-candidate development menus from six drugs, not independent units",
        "independent residual marginals are a planning approximation; joint cross-drug biological correlation unidentifiable",
        "same-source technical screen and validation share control denominator; no independent biological confirmation"]
    summary["resources"] = {"replay_units": sum(row["budget"]["recorded_use"] for row in rows),
        "episode_seconds": sum(row["elapsed_seconds"] for row in rows), "API_calls": 0, "API_tokens": 0,
        "dollars": 0, "downloaded_bytes": 0, "laboratory_credits": 0}
    summary["endpoint"] = r.ENDPOINT
    (output / "episodes.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(development(args.records, args.output), indent=2))
