"""PublicTargetGOKernel: auxiliary retrospective prediction, NOT STATE or TxPert.

Freeze public target/GO features and plate/chemical splits before reading X_hvg
responses. All c39 data remain historically exposed development material.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import h5py
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.linalg import cho_factor, cho_solve
from threadpoolctl import threadpool_limits

from src.virtual_cell.state_runner import _column
from tools.datasets.state_prospective_input import CONTROL, CONTEXT, KEY, PERT, digest, write_json


def chemical_group(smiles):
    from rdkit import Chem
    from rdkit.Chem.MolStandardize import rdMolStandardize

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("unparseable chemical structure")
    parent = rdMolStandardize.FragmentParent(mol)
    parent = rdMolStandardize.Uncharger().uncharge(parent)
    return Chem.MolToInchiKey(parent).split("-")[0]


def normalize_rows(matrix):
    norm = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=1)).reshape(-1))
    return sparse.diags(1 / np.where(norm > 0, norm, 1)) @ matrix


def frozen_features(drugs, graph):
    """Only fixed public metadata and gene graph are accepted, never expression."""
    nodes = sorted(set(graph.source) | set(graph.target))
    lookup = {node: i for i, node in enumerate(nodes)}
    node_edges = sparse.coo_matrix((graph.importance.to_numpy(float),
                                   ([lookup[x] for x in graph.source], [lookup[x] for x in graph.target])),
                                  shape=(len(nodes), len(nodes))).tocsr()
    # A weighted union of self + GO neighbors; no result-derived graph edges.
    neighborhood = normalize_rows(node_edges + sparse.eye(len(nodes)))
    rows, cols, values, provenance = [], [], [], []
    for i, row in drugs.iterrows():
        original = [] if pd.isna(row.targets) else [x.strip() for x in str(row.targets).split(",")]
        matched = sorted({x for x in original if x in lookup})
        for gene in matched:
            rows.append(i)
            cols.append(lookup[gene])
            values.append(1.0 / len(matched))
        provenance.append({"drug": row.drug, "source_row_parquet_zero_based": int(i),
                           "provider_targets": original, "matched_graph_genes": matched,
                           "unmatched_tokens": sorted(set(original) - set(matched)),
                           "knowledge_status": "provider target annotation, not uniformly independently confirmed"})
    direct = normalize_rows(sparse.coo_matrix((values, (rows, cols)), shape=(len(drugs), len(nodes))).tocsr())
    expanded = normalize_rows(direct @ neighborhood)
    return direct, expanded, provenance, nodes


def split_indices(records, fold):
    test = np.flatnonzero(records.fold.to_numpy() == fold)
    held_groups = set(records.iloc[test].chemical_group)
    train = np.flatnonzero((records.fold.to_numpy() != fold) & ~records.chemical_group.isin(held_groups).to_numpy())
    if set(records.iloc[train].plate) & set(records.iloc[test].plate):
        raise ValueError("plate leakage")
    if set(records.iloc[train].chemical_group) & held_groups:
        raise ValueError("chemical identity leakage")
    return train, test


def kernel_predict(kernel, train, test, outcomes, alpha):
    # Index before calculating any fit statistic: held-out outcomes cannot enter.
    y_train = outcomes[train]
    center = y_train.mean(axis=0)
    ktrain = kernel[np.ix_(train, train)].copy()
    ktrain.flat[::len(train) + 1] += alpha
    factor = cho_factor(ktrain, lower=True, check_finite=True)
    weights = cho_solve(factor, y_train - center, check_finite=True)
    return kernel[np.ix_(test, train)] @ weights + center


def run(root, sources, out):
    out.mkdir(parents=True, exist_ok=False)
    (out / ".gitattributes").write_text("* binary\n", encoding="utf-8")
    (out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    asset = root / "data/external/arc_state/tahoe_metadata_source/c39.h5ad"
    axis_path = root / "data/virtual_cell/tahoe_c39_x_hvg_feature_names.json"
    axis = json.loads(axis_path.read_text(encoding="utf-8"))
    if digest(asset) != axis["dataset_sha256"]:
        raise ValueError("registered expression asset hash mismatch")
    drugs = pd.read_parquet(sources / "tahoe_drugs.raw").reset_index(drop=True)
    graph = pd.read_csv(sources / "txpert_go.raw")
    cells = pd.read_parquet(sources / "tahoe_cells.raw")
    direct, expanded, knowledge_rows, nodes = frozen_features(drugs, graph)
    target_kernel = (direct @ direct.T).toarray()
    go_kernel = (expanded @ expanded.T).toarray()
    # Only observation metadata are inspected at this stage.
    with h5py.File(asset) as handle:
        obs = pd.DataFrame({key: _column(handle["obs"], key) for key in ("cell_name", PERT, "plate", "sample")})
    if set(obs.cell_name) != {CONTEXT}:
        raise ValueError("wrong context")
    drug_lookup = {name: i for i, name in enumerate(drugs.drug)}
    rows, rejected = [], []
    for (plate, label), part in obs.groupby(["plate", PERT], sort=True):
        if label == CONTROL:
            continue
        description = ast.literal_eval(label)
        if len(description) != 1:
            raise ValueError("single intervention required")
        name, dose, unit = description[0]
        record = dict(plate=plate, label=label, drug=name, dose=float(dose), unit=unit,
                      cells=len(part), source_rows_zero_based=part.index.tolist(), sample_ids=sorted(set(part["sample"])))
        reason = None
        if name not in drug_lookup:
            reason = "no_exact_public_drug_metadata_match"
        elif not knowledge_rows[drug_lookup[name]]["matched_graph_genes"]:
            reason = "no_exact_public_target_gene_in_graph"
        elif len(part) < 5:
            reason = "fewer_than_five_deposited_cells_metadata_rule"
        elif unit != "uM" or dose not in (0.05, 0.5, 5.0):
            reason = "outside_prespecified_dose_set"
        if reason:
            rejected.append(dict(record, reason=reason))
            continue
        try:
            record["chemical_group"] = chemical_group(drugs.loc[drug_lookup[name], "canonical_smiles"])
        except (ValueError, TypeError) as exc:
            rejected.append(dict(record, reason=str(exc)))
            continue
        record["drug_index"] = drug_lookup[name]
        rows.append(record)
    records = pd.DataFrame(rows)
    # Shuffle only represented drugs: using all metadata rows would introduce
    # zero-feature drugs into this covered cohort and weaken the capacity control.
    eligible_drugs = np.unique(records.drug_index)
    permutation = np.arange(len(drugs))
    permutation[eligible_drugs] = np.random.default_rng(42).permutation(eligible_drugs)
    permuted_kernel = go_kernel[np.ix_(permutation, permutation)]
    plates = sorted(set(obs.plate))
    order = np.random.default_rng(42).permutation(plates)
    plate_folds = {str(plate): i % 5 for i, plate in enumerate(order)}
    records["fold"] = records.plate.map(plate_folds)
    splits = {}
    for fold in range(5):
        train, test = split_indices(records, fold)
        if min(len(train), len(test)) < 10:
            raise ValueError("insufficient purged train/test support")
        splits[str(fold)] = {"train": train.tolist(), "test": test.tolist(),
                             "training_plates": sorted(set(records.iloc[train].plate)),
                             "test_plates": sorted(set(records.iloc[test].plate))}
    coordinates = [i for i, name in enumerate(axis["names"]) if name is not None]
    write_json(out / "knowledge_rows.json", knowledge_rows)
    write_json(out / "eligible_metadata.json", records.to_dict("records"))
    write_json(out / "excluded_metadata.json", rejected)
    source_hashes = {p.name: digest(p) for p in [asset, axis_path, sources / "tahoe_drugs.raw", sources / "tahoe_cells.raw", sources / "txpert_go.raw", Path(__file__)]}
    freeze = {"frozen_before_this_run_reads_response_matrix_utc": datetime.now(timezone.utc).isoformat(),
              "study": "PublicTargetGOKernel retrospective prediction; not STATE, not TxPert",
              "exposure": "entire c39 asset previously used in local development; no claim of fresh confirmatory test",
              "source_hashes": source_hashes, "folds": splits, "plate_folds": plate_folds,
              "seed": 42, "ridge_alpha": 1.0, "hyperparameter_trials": 1,
              "audit_refits_per_model_fold": 1,
              "models": ["dose_only", "public_targets", "public_target_GO", "permuted_target_GO"],
              "reference": "only training-plate control RNA; no held-out control or treated expression enters fitting or features",
              "prediction_target": "equal-well mean log1p expression minus same-plate control mean; 1969 named frozen coordinates",
              "endpoint_coordinates": coordinates, "primary_comparison": "public_target_GO minus dose_only MSE, equal weight per held-out chemical identity",
              "secondary": "MAE, Pearson delta, descriptive calibration slope; no predictive interval fitted",
              "fairness": "same cohort/splits/endpoints/one closed-form fit per model/fold/alpha/selector absent; permuted graph controls feature capacity",
              "physical_independence": "unknown; plate-disjoint evaluation, no physical confidence interval",
              "state_factor_B_D": "not_run; post-treatment controls are not legal predecision state",
              "query_outcome_leakage_test": "replace held-out outcomes before fit; predictions must remain bitwise identical",
              "cost": "unknown", "permuted_drug_rows": permutation.tolist()}
    write_json(out / "freeze.json", freeze)
    np.savez_compressed(out / "knowledge_kernels.npz", targets=target_kernel, go=go_kernel, permuted=permuted_kernel)
    # Response access begins only after the above freeze. This is not a claim that
    # c39 biological outcomes had never been explored historically.
    with h5py.File(asset) as handle:
        matrix = np.asarray(handle["obsm"][KEY], dtype=np.float64)[:, coordinates]
    controls = {}
    for plate in plates:
        selected = obs[(obs.plate == plate) & (obs[PERT] == CONTROL)]
        if selected.empty:
            raise ValueError("missing exact plate control; no global fallback")
        controls[plate] = np.mean([matrix[part.index].mean(axis=0) for _, part in selected.groupby("sample")], axis=0)
    outcomes = []
    for row in records.to_dict("records"):
        selected = obs.loc[row["source_rows_zero_based"]]
        mean = np.mean([matrix[part.index].mean(axis=0) for _, part in selected.groupby("sample")], axis=0)
        outcomes.append(mean - controls[row["plate"]])
    outcomes = np.stack(outcomes)
    drug_indices = records.drug_index.to_numpy()
    dose_match = (records.dose.to_numpy()[:, None] == records.dose.to_numpy()[None, :]).astype(float)
    kernels = {"dose_only": dose_match,
               "public_targets": dose_match * (1 + target_kernel[np.ix_(drug_indices, drug_indices)]),
               "public_target_GO": dose_match * (1 + go_kernel[np.ix_(drug_indices, drug_indices)]),
               "permuted_target_GO": dose_match * (1 + permuted_kernel[np.ix_(drug_indices, drug_indices)])}
    predictions = {key: np.full_like(outcomes, np.nan) for key in kernels}
    leakage_checks, run_receipts = [], []
    with threadpool_limits(limits=2):
        for fold in range(5):
            train, test = split_indices(records, fold)
            reference = np.mean([controls[p] for p in splits[str(fold)]["training_plates"]], axis=0)
            np.save(out / f"blind_reference_fold{fold}.npy", reference)
            for name, kernel in kernels.items():
                started = time.perf_counter()
                pred = kernel_predict(kernel, train, test, outcomes, 1.0)
                predictions[name][test] = pred
                poisoned = outcomes.copy()
                poisoned[test] = 987654.0
                invariant = np.array_equal(pred, kernel_predict(kernel, train, test, poisoned, 1.0))
                leakage_checks.append(dict(fold=fold, model=name, passed=invariant))
                run_receipts.append(dict(fold=fold, model=name, training_records=len(train), test_records=len(test),
                                         elapsed_seconds=time.perf_counter() - started, cost="unknown"))
            print(f"fold {fold}: train={len(train)}, test={len(test)}, four models completed", flush=True)
    if not all(c["passed"] for c in leakage_checks) or any(not np.isfinite(p).all() for p in predictions.values()):
        raise ValueError("leakage check failed or missing predictions")
    # The nonfitted no-change predictor is essential when most perturbations are weak.
    predictions["no_change"] = np.zeros_like(outcomes)
    metric_rows, aggregate = [], {}
    for name, pred in predictions.items():
        mse = np.mean((pred - outcomes) ** 2, axis=1)
        mae = np.mean(np.abs(pred - outcomes), axis=1)
        pc = pred - pred.mean(axis=1, keepdims=True)
        yc = outcomes - outcomes.mean(axis=1, keepdims=True)
        denom = np.sqrt(np.sum(pc ** 2, axis=1) * np.sum(yc ** 2, axis=1))
        pearson = np.divide(np.sum(pc * yc, axis=1), denom, out=np.full(len(pred), np.nan), where=denom > 0)
        temp = records[["plate", "fold", "chemical_group", "drug", "dose", "cells"]].copy()
        temp["model"], temp["mse"], temp["mae"], temp["pearson_delta"] = name, mse, mae, pearson
        metric_rows.append(temp)
        chemical = temp.groupby("chemical_group")[["mse", "mae", "pearson_delta"]].mean()
        # Descriptive calibration of pooled gene/condition deltas, never coverage.
        x, y = pred.reshape(-1), outcomes.reshape(-1)
        slope = float(np.dot(x - x.mean(), y - y.mean()) / np.sum((x - x.mean()) ** 2)) if np.std(x) else None
        aggregate[name] = {"chemical_macro_MSE": float(chemical.mse.mean()), "chemical_macro_MAE": float(chemical.mae.mean()),
                           "chemical_macro_Pearson_delta": float(chemical.pearson_delta.mean()) if chemical.pearson_delta.notna().any() else None,
                           "pooled_calibration_slope": slope, "pooled_calibration_intercept": float(y.mean() - slope * x.mean()) if slope is not None else None}
    metrics = pd.concat(metric_rows, ignore_index=True)
    metrics.to_csv(out / "prediction_metrics.csv", index=False)
    np.savez_compressed(out / "predictions_and_observations.npz", observed=outcomes, **predictions)
    base = aggregate["dose_only"]["chemical_macro_MSE"]
    kg = aggregate["public_target_GO"]["chemical_macro_MSE"]
    by_chemical = metrics.groupby(["chemical_group", "model"]).mse.mean().unstack()
    delta = by_chemical.public_target_GO - by_chemical.dose_only
    by_plate = metrics.groupby(["plate", "model"]).mse.mean().unstack()
    summary = {"study": freeze["study"], "context": CONTEXT, "records": len(records), "chemical_identities": len(by_chemical),
               "drug_names": records.drug.nunique(), "assay_plates": len(plates), "genes": len(coordinates),
               "excluded_condition_plate_groups": len(rejected), "knowledge_graph_nodes": len(nodes), "knowledge_graph_edges": len(graph),
               "metrics": aggregate, "primary_MSE_difference": kg - base, "relative_MSE_reduction": (base - kg) / base,
               "chemicals_improved": int((delta < 0).sum()), "chemicals_worsened": int((delta > 0).sum()),
               "plates_improved_descriptive": int((by_plate.public_target_GO < by_plate.dose_only).sum()),
               "leakage_checks": leakage_checks, "run_receipts": run_receipts,
               "physical_confidence_interval": "not_reported; independently initiated cultures unknown",
               "knowledge_gain_status": "retrospective point estimate only; assess no-change and permutation comparators",
               "state_gain": "not_run", "action_change": "not_run", "terminal_utility": "not_identified", "deployment_value": "not_identified",
               "TxPert_checkpoint_calls": 0, "STATE_checkpoint_calls": 0,
               "hypothesis": "public drug-target annotations and GO functional similarity can share drug-response information; no treatment susceptibility is inferred solely from a target or mutation",
               "context_knowledge": cells[cells.cell_name == CONTEXT].where(pd.notna(cells), None).to_dict("records")}
    write_json(out / "summary.json", summary)
    write_json(out / "manifest.json", {p.name: digest(p) for p in out.iterdir() if p.is_file()})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.root.resolve(), args.sources.resolve(), args.out.resolve())
    print(json.dumps({k: report[k] for k in ("records", "chemical_identities", "metrics", "primary_MSE_difference", "relative_MSE_reduction")}, indent=2))
