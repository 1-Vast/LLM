"""Exploratory action-supported repair geometry on the existing SciPlex holdout.

This uses the frozen, previously evaluated response predictor. It tests the
decision arithmetic and candidate support in a matched single-study domain;
it is not a fresh confirmatory holdout or a biological mechanism assay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def action_gain(goal, initial, candidate, weights=None) -> float:
    """Predicted reduction in weighted square loss for a real action replacement."""
    g = np.asarray(goal, dtype=float)
    y0 = np.asarray(initial, dtype=float)
    y1 = np.asarray(candidate, dtype=float)
    if g.ndim != 1 or y0.shape != g.shape or y1.shape != g.shape or not len(g):
        raise ValueError("response_shape_mismatch")
    if weights is None:
        w = np.ones(len(g))
    else:
        w = np.asarray(weights, dtype=float)
    if w.shape != g.shape or not all(np.isfinite(v).all() for v in (g, y0, y1, w)) or np.any(w < 0):
        raise ValueError("invalid_response_or_weights")
    r, delta = g - y0, y1 - y0
    return float(2 * np.dot(w * r, delta) - np.dot(w * delta, delta))


def loss(response, goal, epsilon=1e-8) -> float:
    a, b = np.asarray(response), np.asarray(goal)
    return float(np.sum((a - b) ** 2) / (np.sum(b ** 2) + epsilon))


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def prepare(workspace: Path, output: Path) -> dict:
    """Freeze public candidate choices before exposing test responses to scoring."""
    root = workspace / "log/20260915/model_validation/training_v1"
    conditions_path = root / "conditions.csv"
    predictions_path = root / "heldout_predictions.npz"
    measurements_path = root / "measured_pseudobulk.npz"
    parameters_path = root / "model_parameters.npz"
    table = pd.read_csv(conditions_path)
    with np.load(predictions_path, allow_pickle=False) as archive:
        predicted = archive["multimodal_neural"].astype("float32")
    with np.load(measurements_path, allow_pickle=False) as archive:
        measured = archive["shift"]
        genes = archive["genes"]
    with np.load(parameters_path, allow_pickle=False) as archive:
        components = archive["target_components"].astype("float32")
        if not np.array_equal(archive["genes"], genes):
            raise ValueError("gene_order_mismatch")
    test_index = np.flatnonzero((table.split == "test").to_numpy())
    if len(test_index) != len(predicted):
        raise ValueError("test_prediction_alignment_mismatch")
    # Conditions are averaged across released replicate/plate rows. Their
    # source independence is not asserted; molecule identity is the cluster.
    groups = []
    for (smiles, context, dose), group in table.loc[table.split == "test"].groupby(
        ["smiles", "cell_line", "dose_value"], sort=True
    ):
        local = np.searchsorted(test_index, group.index.to_numpy())
        groups.append({"smiles": smiles, "context": context, "dose": float(dose),
                       "prediction": predicted[local].mean(axis=0) @ components.T,
                       "source_rows": group.index.to_numpy().tolist()})
    refs = []
    for (smiles, context, dose), group in table.loc[table.split == "validation"].groupby(
        ["smiles", "cell_line", "dose_value"], sort=True
    ):
        goal = measured[group.index.to_numpy()].mean(axis=0) @ components.T
        if float(np.sum(goal ** 2)) < 1e-4:
            continue
        refs.append((smiles, context, float(dose), goal))
    records = []
    for ref_smiles, context, dose, goal in refs:
        candidates = [i for i, item in enumerate(groups) if item["context"] == context and item["dose"] == dose]
        if len(candidates) < 9:
            continue
        key = f"{ref_smiles}|{context}|{dose}"
        initial = candidates[int(hashlib.sha256(key.encode()).hexdigest(), 16) % len(candidates)]
        rest = [i for i in candidates if i != initial]
        y0 = groups[initial]["prediction"]
        # Response mode means proximity to the current effect; the other menu
        # changes mode toward the target. Both are supported actual actions.
        same = sorted(rest, key=lambda i: (float(np.sum((groups[i]["prediction"] - y0) ** 2)), i))[:4]
        other = [i for i in rest if i not in same]
        switch = sorted(other, key=lambda i: (-action_gain(goal, y0, groups[i]["prediction"]), i))[:4]
        menu = same + switch
        analytic = min([initial] + menu, key=lambda i: (loss(groups[i]["prediction"], goal), i))
        nearest = min([initial] + menu, key=lambda i: (float(np.sum((groups[i]["prediction"] - goal) ** 2)), i))
        records.append({"task_id": hashlib.sha256(key.encode()).hexdigest()[:16],
                        "reference_smiles_sha256": hashlib.sha256(ref_smiles.encode()).hexdigest(),
                        "context": context, "dose": dose, "initial": initial,
                        "same_mode": same, "switch_mode": switch, "analytic_choice": analytic,
                        "nearest_choice": nearest, "target": goal.tolist(),
                        "predicted_gain": action_gain(goal, y0, groups[analytic]["prediction"])})
    output.mkdir(parents=True, exist_ok=False)
    public = {"schema": "maestro.asrg.pilot.v1", "status": "exploratory_inspected_holdout",
              "model": "existing_multimodal_neural_ensemble", "projection": "training_fitted_64d_SVD",
              "source_sha256": {p.name: _digest(p) for p in
                                (conditions_path, predictions_path, measurements_path, parameters_path)},
              "candidate_count": len(groups), "tasks": records,
              "candidate_registry": [{k: v for k, v in item.items() if k != "prediction"} for item in groups],
              "budget_note": "all 550 test predictions were precomputed in the historical model-validation run; this pilot does not claim four-query efficiency"}
    (output / "public_plan.json").write_text(json.dumps(public, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    # Private file is not opened by the policy step below. It is used only by
    # `evaluate`, after public_plan.json is frozen. File separation alone is not
    # an OS permission boundary and is reported as such.
    np.savez_compressed(output / "evaluator_private.npz",
                        responses=np.stack([measured[item["source_rows"]].mean(axis=0) @ components.T for item in groups]),
                        genes=genes)
    return {"tasks": len(records), "candidates": len(groups), "output": str(output)}


def evaluate(output: Path) -> dict:
    plan = json.loads((output / "public_plan.json").read_text(encoding="utf-8"))
    with np.load(output / "evaluator_private.npz", allow_pickle=False) as archive:
        observed = archive["responses"]
    rows = []
    for task in plan["tasks"]:
        goal = np.asarray(task["target"])
        scores = {name: loss(observed[task[name]], goal) for name in
                  ("initial", "analytic_choice", "nearest_choice")}
        rows.append({"task_id": task["task_id"], "cluster": task["reference_smiles_sha256"],
                     "initial_loss": scores["initial"], "analytic_loss": scores["analytic_choice"],
                     "nearest_loss": scores["nearest_choice"],
                     "analytic_gain": scores["initial"] - scores["analytic_choice"],
                     "analytic_worse": scores["analytic_choice"] > scores["initial"]})
    cluster_means = pd.DataFrame(rows).groupby("cluster").analytic_gain.mean().to_numpy()
    rng = np.random.default_rng(20260924)
    boot = cluster_means[rng.integers(len(cluster_means), size=(4000, len(cluster_means)))].mean(axis=1)
    report = {"schema": "maestro.asrg.pilot.result.v1", "tasks": len(rows),
              "reference_clusters": len({x["cluster"] for x in rows}),
              "mean_analytic_gain": float(np.mean([x["analytic_gain"] for x in rows])),
              "cluster_mean_gain": float(cluster_means.mean()),
              "cluster_bootstrap_ci95": np.quantile(boot, [0.025, 0.975]).tolist(),
              "worse_fraction": float(np.mean([x["analytic_worse"] for x in rows])),
              "analytic_equals_nearest": all(x["analytic_loss"] == x["nearest_loss"] for x in rows),
              "conclusion_scope": "exploratory arithmetic baseline on previously inspected single-study test data; no learned ASRG value model or fresh external validation",
              "rows": rows}
    (output / "evaluation.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return {k: v for k, v in report.items() if k != "rows"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "evaluate"))
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.workspace, args.output) if args.phase == "prepare" else evaluate(args.output)))


if __name__ == "__main__":
    main()
