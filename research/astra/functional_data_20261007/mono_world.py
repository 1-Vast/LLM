"""Small condition-dependent mono response world; separate observation task."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from research.astra.functional_data_20261007.acquire import HERE, ROOT
from research.astra.drylab_followup_20261007.reproduce import load_replay

CONTEXT = ROOT / "research/astra/knowledge_transfer_20261004/context/pathway_125_lines.csv"
KEY = ["drug_id", "dose_uM"]


def training_data(points):
    lib = points[points.role.eq("library") & points.assay.eq("Glo") & points.seed_to_read_days.eq(4)].copy()
    top = lib.sort_values("dose_uM").groupby(["sidm", "event", "drug_id"]).tail(1)
    return top.groupby(["sidm", "tissue"] + KEY, as_index=False).agg(viability=("viability", "mean"), source_events=("event", "nunique"))


def predict(train, queries, context, with_state=False, lam=10., fits=None):
    fits = {} if fits is None else fits
    outputs = []
    groups = {key: g for key, g in train.groupby(KEY)}
    for q in queries.itertuples(index=False):
        g = groups.get((q.drug_id, q.dose_uM))
        if g is None:
            outputs.append(dict(prediction=np.nan, baseline=np.nan, support=0, status="no_exact_drug_dose_history"))
            continue
        means = g.groupby("tissue").viability.mean().to_dict()
        global_mean = float(g.viability.mean())
        base = float(means.get(q.tissue, global_mean))
        value, status = base, "tissue_reference" if q.tissue in means else "global_transport"
        # Fit once per drug/dose per call and reuse through a cache below.
        if with_state and len(g) >= 10 and q.sidm in context.index:
            fit_key = (q.drug_id, q.dose_uM)
            if fit_key not in fits:
                X = context.reindex(g.sidm).to_numpy(float)
                valid = np.isfinite(X).all(axis=1)
                X = X[valid]
                z = g.loc[valid]
                if len(X) >= 10:
                    center, scale = X.mean(axis=0), X.std(axis=0)
                    scale[scale < 1e-8] = 1.
                    residual = z.viability.to_numpy() - z.tissue.map(means).to_numpy()
                    X = (X - center) / scale
                    beta = np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ residual)
                    fits[fit_key] = center, scale, beta
                else:
                    fits[fit_key] = None
            fit = fits[fit_key]
            if fit is not None:
                center, scale, beta = fit
                x = context.loc[q.sidm].to_numpy(float)
                if np.isfinite(x).all():
                    value = base + float(((x - center) / scale) @ beta)
                    status = "context_conditional_reference"
        outputs.append(dict(prediction=value, baseline=global_mean, support=len(g), status=status))
    return pd.DataFrame(outputs, index=queries.index)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=HERE / "data_run3")
    parser.add_argument("--output", type=Path, default=HERE / "world_results")
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    protocol = HERE / "WORLD_PROTOCOL.json"
    frozen = json.loads((HERE / "WORLD_FREEZE.json").read_text())
    assert hashlib.sha256(protocol.read_bytes()).hexdigest() == frozen["sha256"]
    context = pd.read_csv(CONTEXT, index_col=0)
    points = pd.read_csv(args.data / "mono_event_points.csv.gz", dtype={"sidm": str, "drug_id": str})
    data = training_data(points)
    _, _, menu = load_replay().load_data()
    assert not set(data.sidm) & set(menu.SIDM)
    assert set(data.sidm) <= set(context.index)
    rng = np.random.default_rng(20261007)
    folds = {}
    for tissue, g in data[["sidm", "tissue"]].drop_duplicates().groupby("tissue"):
        for i, s in enumerate(rng.permutation(sorted(g.sidm))):
            folds[s] = i % 5
    shuffled = context.copy()
    for _, g in data[["sidm", "tissue"]].drop_duplicates().groupby("tissue"):
        ids = sorted(g.sidm)
        shuffled.loc[ids] = context.loc[rng.permutation(ids)].to_numpy()
    records = []
    with threadpool_limits(limits=1):
        for fold in range(5):
            train = data[data.sidm.map(folds).ne(fold)]
            test = data[data.sidm.map(folds).eq(fold)]
            assert not set(train.sidm) & set(test.sidm)
            for arm, state, ctx in [("tissue_reference", False, context), ("state_ridge", True, context),
                                    ("state_shuffled", True, shuffled)]:
                result = predict(train, test, ctx, state, fits={})
                result = pd.concat([test, result], axis=1)
                result["arm"], result["fold"] = arm, fold
                records.append(result)
                if arm == "tissue_reference":
                    global_result = result.copy()
                    global_result["prediction"] = global_result.baseline
                    global_result["arm"] = "drug_dose_mean"
                    records.append(global_result)
        # Target context enters predictions, never the training labels or their evaluation.
        queries = menu[["SIDM", "Tissue", "LIBRARY_ID", "LIBRARY_CONC"]].drop_duplicates().rename(
            columns={"SIDM": "sidm", "Tissue": "tissue", "LIBRARY_ID": "drug_id", "LIBRARY_CONC": "dose_uM"})
        queries["dose_uM"] = queries.dose_uM.astype(float)
        target = predict(data, queries, context, True, fits={})
        pd.concat([queries, target], axis=1).to_csv(args.output / "target_reference_predictions.csv", index=False)
    predictions = pd.concat(records, ignore_index=True)
    predictions["abs_error"] = abs(predictions.prediction - predictions.viability)
    predictions["sq_error"] = (predictions.prediction - predictions.viability) ** 2
    assert predictions.prediction.notna().all(), "complete_test_coverage_required"
    predictions.to_csv(args.output / "heldout_predictions.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    cell = predictions.groupby(["arm", "sidm", "tissue"])[["abs_error", "sq_error"]].mean().reset_index()
    cell.to_csv(args.output / "per_cell.csv", index=False)
    summary = cell.groupby("arm").agg(mae=("abs_error", "mean"), mse=("sq_error", "mean"), cells=("sidm", "nunique"))
    summary["rmse"] = np.sqrt(summary.mse)
    summary.to_csv(args.output / "summary.csv")
    cell.groupby(["arm", "tissue"])[["abs_error", "sq_error"]].mean().to_csv(args.output / "by_tissue.csv")
    pivot = cell.pivot(index="sidm", columns="arm", values="abs_error")
    delta = pivot.state_ridge - pivot.tissue_reference
    boot = delta.to_numpy()[rng.integers(len(delta), size=(2000, len(delta)))].mean(axis=1)
    meta = {"status": "Exploratory prediction task, not confirmed-decision benefit", "history_cells": len(folds),
            "mono_cell_drug_dose_rows": len(data), "target_own_labels_used": False,
            "state_minus_tissue_mae": float(delta.mean()), "cell_bootstrap_ci95": np.quantile(boot, [.025, .975]).tolist(),
            "target_prediction_rows": len(queries), "target_refusal_rows": int(target.prediction.isna().sum()),
            "limits": "Same-screen mono viability; repeated drugs/dependent source events; no held-out-pair or clinical inference",
            "context_sha256": hashlib.sha256(CONTEXT.read_bytes()).hexdigest(), "protocol_sha256": frozen["sha256"]}
    (args.output / "manifest.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(summary.to_string())
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
