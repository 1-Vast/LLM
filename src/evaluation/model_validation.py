"""Real public-data training, held-out drug evaluation and modal ablations.

Run: python -m evaluation.model_validation --workspace D:/MAESTRO --output <fresh path>
The protocol is frozen before fitting. Test labels never select features or models.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import torch

from virtual_cell.learned_response import fit_response


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=1, allow_nan=False) + "\n", encoding="utf-8")


def column(group, name):
    item = group[name]
    if isinstance(item, h5py.Group):
        codes = item["codes"][:]
        categories = item["categories"].asstr()[:]
        return np.array([categories[c] if c >= 0 else "unknown" for c in codes])
    return item.asstr()[:] if item.dtype.kind in "OS" else item[:]


def compound_key(name):
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\([^)]*\)", "", name).lower())


HGNC_TABLE = "data/external/hgnc/hgnc_complete_set.txt"


def verified_feature_labels(workspace, published, vehicle_sum, columns):
    """Realign a published label table to the matrix columns, or refuse by name.

    Vehicle means per cell line decide the alignment through identity markers; the published
    table is never trusted as printed. Returns the per-column Ensembl labels ('' when a column
    has no label row) and the marker evidence for the audit record.
    """

    from virtual_cell.identity_markers import resolve_label_offset, shift_labels

    table = Path(workspace) / HGNC_TABLE
    if not table.is_file():
        raise ValueError(f"gene_identity_table_missing:{HGNC_TABLE}")
    hgnc = pd.read_csv(table, sep="\t", dtype=str, usecols=["symbol", "ensembl_gene_id"]).dropna()
    symbol = dict(zip(hgnc.ensembl_gene_id, hgnc.symbol))
    offset, checks, refusal = resolve_label_offset(
        {line: np.asarray(values, dtype=float) for line, values in vehicle_sum.items()},
        [symbol.get(str(label)) for label in published])
    if refusal:
        raise ValueError(f"{refusal}:{[check.payload() for check in checks]}")
    labels = [label if label is not None else "" for label in shift_labels([str(x) for x in published], offset, columns)]
    return {"labels": labels, "offset": offset, "first_published_label": str(published[0]),
            "checks": [check.payload() for check in checks]}


def molecular_split(smiles):
    unique = sorted(set(smiles), key=lambda s: hashlib.sha256(("maestro-validation-v1|" + s).encode()).hexdigest())
    n = len(unique)
    return {value: ("train" if i < int(n * .6) else "validation" if i < int(n * .75)
                    else "calibration" if i < int(n * .85) else "test") for i, value in enumerate(unique)}


def prepare(workspace, output, protocol):
    raw = workspace / "data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad"
    with raw.open("rb") as stream:
        digest = hashlib.file_digest(stream, "md5").hexdigest()
    if digest != protocol["required_md5"]:
        raise ValueError("public_asset_digest_mismatch")
    # The old local file supplies chemistry metadata only; no expression/HVG/split is read.
    chemistry = {}
    with h5py.File(workspace / "data/raw/sciplex3/sciplex_complete_middle_subset.h5ad", "r") as f:
        obs = f["obs"]
        names = obs["__categories/product_name"].asstr()[:][obs["product_name"][:]]
        structures = obs["__categories/SMILES"].asstr()[:][obs["SMILES"][:]]
        for name, structure in set(zip(names, structures)):
            mol = Chem.MolFromSmiles(structure)
            if mol is not None:
                chemistry.setdefault(compound_key(name), set()).add(Chem.MolToSmiles(mol))
    with h5py.File(raw, "r") as f:
        obs = f["obs"]
        meta = pd.DataFrame({key: column(obs, key) for key in
                             ["cell_line", "perturbation", "dose_value", "time", "replicate", "plate"]})
        control = (meta.perturbation == "control") & (meta.dose_value == 0)
        mappings = {}
        for drug in sorted(set(meta.perturbation) - {"control"}):
            values = chemistry.get(compound_key(drug), set())
            if len(values) == 1:
                mappings[drug] = next(iter(values))
        splits = molecular_split(mappings.values())
        meta["smiles"] = meta.perturbation.map(mappings).fillna("")
        meta["split"] = meta.smiles.map(splits).fillna("excluded")
        selected = (meta.time == protocol["time_hours"]) & (control | meta.perturbation.isin(mappings))
        group_cols = ["cell_line", "perturbation", "dose_value", "time", "replicate", "plate", "smiles", "split"]
        index = pd.MultiIndex.from_frame(meta[group_cols])
        codes, levels = pd.factorize(index, sort=True)
        groups = levels.to_frame(index=False)
        groups.columns = group_cols
        counts = np.bincount(codes[selected], minlength=len(groups))
        groups["cells"] = counts
        manifest = {"source_md5": digest, "split": splits, "compound_structures": mappings,
                    "excluded_compounds": sorted(set(meta.perturbation) - set(mappings) - {"control"}),
                    "counts_by_split": {s: list(splits.values()).count(s) for s in set(splits.values())},
                    "metadata_only_structure_source": "existing SciPlex3 chemistry metadata; aliases matched uniquely; expression never read",
                    "time_hours": protocol["time_hours"]}
        write(output / "split_manifest.json", manifest)
        published = column(f["var"], "ensembl_id")
        matrix = f["X"]
        ptr = matrix["indptr"][:]
        shape = tuple(matrix.attrs["shape"])
        def blocks():
            for start in range(0, shape[0], 4096):
                stop = min(start + 4096, shape[0])
                a, b = ptr[start], ptr[stop]
                x = sparse.csr_matrix((matrix["data"][a:b], matrix["indices"][a:b],
                                       ptr[start:stop + 1] - a), shape=(stop - start, shape[1]))
                yield start, stop, x
        train_sum = np.zeros(shape[1])
        lines = sorted(set(meta.cell_line.dropna()))
        vehicle_sum = {line: np.zeros(shape[1]) for line in lines}
        for start, stop, x in blocks():
            train = selected.iloc[start:stop].to_numpy() & (meta.split.iloc[start:stop].to_numpy() == "train")
            train_sum += np.asarray(x[train].sum(axis=0)).ravel()
            vehicle = (selected & control).iloc[start:stop].to_numpy()
            for line in lines:
                rows = vehicle & (meta.cell_line.iloc[start:stop].to_numpy() == line)
                if rows.any():
                    vehicle_sum[line] += np.asarray(x[rows].sum(axis=0)).ravel()
        # This release's feature table opens with a stray header row, so the published label of
        # row j names the gene in column j - 1. Labels are realigned only where cell-identity
        # markers confirm the alignment; an unconfirmed table is refused, never used as printed.
        label_check = verified_feature_labels(workspace, published, vehicle_sum, shape[1])
        genes = np.array(label_check.pop("labels"), dtype=object)
        # Human-reference features only; drop repeated ENSG IDs rather than silently double count.
        unique = pd.Series(genes).duplicated(keep=False).to_numpy() & (genes != "")
        human = np.array([g.startswith("ENSG") for g in genes]) & ~unique
        candidates = np.flatnonzero(human & (train_sum > 0))
        features = np.sort(candidates[np.argsort(train_sum[candidates], kind="stable")[-2000:]])
        if len(features) != 2000:
            raise ValueError("insufficient_training_genes")
        totals = np.zeros((len(groups), len(features)), dtype=np.float64)
        for start, stop, x in blocks():
            keep = selected.iloc[start:stop].to_numpy()
            rows = np.flatnonzero(keep)
            if not len(rows):
                continue
            library = np.asarray(x[:, human].sum(axis=1)).ravel()
            values = x[:, features].astype(np.float64).multiply((10000 / np.maximum(library, 1))[:, None]).tocsr()
            values.data = np.log1p(values.data)
            aggregator = sparse.csr_matrix((np.ones(len(rows)), (codes[start:stop][rows], rows)),
                                           shape=(len(groups), stop - start))
            totals += (aggregator @ values).toarray()
        means = totals / np.maximum(counts, 1)[:, None]
    viable = groups.cells >= protocol["minimum_cells_per_condition_replicate"]
    controls = {}
    for i, row in groups[viable & (groups.perturbation == "control")].iterrows():
        controls[(row.cell_line, row.time, row.replicate, row.plate)] = i
    rows, base, refused = [], [], []
    for i, row in groups[viable & (groups.dose_value > 0)].iterrows():
        key = (row.cell_line, row.time, row.replicate, row.plate)
        if key not in controls:
            refused.append({"group": int(i), "reason": "matched_plate_control_missing"})
        else:
            rows.append(i)
            base.append(controls[key])
    table = groups.iloc[rows].copy().reset_index(drop=True)
    table["control_cells"] = counts[base]
    y, baseline = means[rows] - means[base], means[base]
    table.to_csv(output / "conditions.csv", index=False)
    np.savez_compressed(output / "measured_pseudobulk.npz", shift=y.astype("float32"),
                        baseline=baseline.astype("float32"), genes=genes[features].astype(str))
    write(output / "data_audit.json", {"source_cells": int(shape[0]), "source_features": int(shape[1]),
          "selected_human_features": len(features), "model_rows": len(table),
          "matched_control_rule": "context,time,replicate,plate", "refused_groups": refused,
          "low_cell_or_excluded_groups": int((~viable).sum()),
          "statistical_unit": "molecular identity, not individual cells; source replicates not independently audited",
          "gene_selection": "top training-cell count sum; no held-out counts in ranking",
          "feature_label_check": label_check,
          "gene_symbol_issue": ("Published symbols are missing and the published Ensembl table is offset by a "
                                "stray header row; labels are realigned by identity markers and recorded above")})
    return table, y.astype("float32"), baseline.astype("float32"), genes[features].astype(str)


def paired_interval(delta, groups, seed=20260915):
    means = pd.DataFrame({"delta": delta, "group": groups}).groupby("group").delta.mean().to_numpy()
    rng = np.random.default_rng(seed)
    values = means[rng.integers(len(means), size=(2000, len(means)))].mean(axis=1)
    return {"mean": float(means.mean()), "ci95": np.quantile(values, [.025, .975]).tolist(), "clusters": len(means)}


def train_and_evaluate(table, y, baseline, genes, output, protocol):
    masks = {name: (table.split == name).to_numpy() for name in ["train", "validation", "calibration", "test"]}
    if any(not m.any() for m in masks.values()):
        raise ValueError("empty_partition")
    train, val, cal, test = [masks[k] for k in masks]
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=512)
    cache = {s: gen.GetFingerprintAsNumPy(Chem.MolFromSmiles(s)) for s in table.smiles.unique()}
    chem = np.array([cache[s] for s in table.smiles], dtype="float32")
    dose = np.log1p(table.dose_value.to_numpy(dtype="float32")) / np.log1p(10000.)
    context = pd.get_dummies(table.cell_line).to_numpy(dtype="float32")
    bsvd = TruncatedSVD(n_components=16, random_state=11).fit(baseline[train])
    rna = bsvd.transform(baseline).astype("float32")
    # Uncentered target projection preserves the zero-shift boundary.
    svd = TruncatedSVD(n_components=64, random_state=11).fit(y[train])
    target = svd.transform(y).astype("float32")
    designs = {"context_dose": np.c_[context, dose], "chemistry_dose": np.c_[chem, dose],
               "chemistry_context_dose": np.c_[chem, context, dose], "multimodal": np.c_[chem, rna, dose]}
    predictions = {"zero_shift": np.zeros_like(y), "train_mean_shift": np.tile(y[train].mean(0), (len(y), 1))}
    details, checkpoints = {}, {}
    neural_predictions = {}
    for name, raw_x in designs.items():
        scale = StandardScaler().fit(raw_x[train])
        x = scale.transform(raw_x).astype("float32")
        linear_x = np.c_[x, np.ones(len(x))] * dose[:, None]
        candidates = []
        for alpha in [.1, 1., 10., 100.]:
            fit = Ridge(alpha=alpha, fit_intercept=False).fit(linear_x[train], target[train])
            error = float(np.square(fit.predict(linear_x[val]) @ svd.components_ - y[val]).mean())
            candidates.append((error, alpha, fit))
        error, alpha, fit = min(candidates, key=lambda item: (item[0], -item[1]))
        key = name + "_ridge"
        predictions[key] = (fit.predict(linear_x) @ svd.components_).astype("float32")
        details[key] = {"selected_alpha": alpha, "validation_gene_mse": error}
        checkpoints[key] = {"coefficients": fit.coef_, "feature_mean": scale.mean_, "feature_scale": scale.scale_}
        if name not in {"chemistry_context_dose", "multimodal"}:
            continue
        key = "chemistry_context_neural" if name == "chemistry_context_dose" else "multimodal_neural"
        fits = []
        for seed in protocol["seeds"]:
            result = fit_response(x[train], dose[train], target[train], x[val], dose[val], target[val],
                                  seed=seed, epochs=protocol["epochs"], patience=protocol["patience"],
                                  device="cuda" if torch.cuda.is_available() else "cpu")
            pred = result.predict(x, dose) @ svd.components_
            fits.append(pred.astype("float32"))
            write(output / f"{key}_{seed}_training.json", {"seed": seed, "selected_epoch": result.selected_epoch,
                  "history": result.history, "device": str(next(result.network.parameters()).device)})
            torch.save(result.network.cpu().state_dict(), output / f"{key}_{seed}.pt")
            if name == "multimodal":
                order = np.random.default_rng(20260915).permutation(np.flatnonzero(test))
                permuted = raw_x.copy()
                permuted[test, 512:528] = raw_x[order, 512:528]
                px = scale.transform(permuted).astype("float32")
                neural_predictions.setdefault("permuted_rna", []).append(result.predict(px, dose) @ svd.components_)
            assert np.all(result.predict(x[:2], np.zeros(2)) == 0), "zero_dose_anchor_failed"
        predictions[key] = np.mean(fits, axis=0)
        neural_predictions[key] = fits
        details[key] = {"seeds": protocol["seeds"], "prediction": "mean across all prespecified seeds"}
        checkpoints[key] = {"feature_mean": scale.mean_, "feature_scale": scale.scale_}
        print("trained", key, flush=True)
    predictions["multimodal_neural_permuted_rna"] = np.mean(neural_predictions["permuted_rna"], axis=0)
    # Freeze all fitted parameters and predictions before the test scoring block.
    arrays = {"genes": genes, "target_components": svd.components_, "baseline_components": bsvd.components_,
              **{name + "_" + key: value for name, params in checkpoints.items() for key, value in params.items()}}
    np.savez_compressed(output / "model_parameters.npz", **arrays)
    np.savez_compressed(output / "heldout_predictions.npz", observed=y[test], **{k: v[test] for k, v in predictions.items()})
    errors, scores, intervals = {}, {}, {}
    for name, prediction in predictions.items():
        mse = np.square(prediction - y).mean(axis=1)
        errors[name] = mse[test]
        cosine = np.sum(prediction[test] * y[test], axis=1) / np.maximum(np.linalg.norm(prediction[test], axis=1) * np.linalg.norm(y[test], axis=1), 1e-12)
        scores[name] = {"gene_mse": paired_interval(mse[test], table.smiles[test]),
                        "gene_mae": float(np.abs(prediction[test] - y[test]).mean()),
                        "shift_cosine": float(cosine.mean()), "selection": details.get(name, {})}
        scalar_error = np.abs(np.sqrt(np.square(prediction).mean(1)) - np.sqrt(np.square(y).mean(1)))
        residual = pd.DataFrame({"drug": table.smiles[cal], "error": scalar_error[cal]}).groupby("drug").error.max().to_numpy()
        rank = math.ceil((len(residual) + 1) * .9)
        width = float(np.sort(residual)[rank - 1]) if rank <= len(residual) else None
        group_error = pd.DataFrame({"drug": table.smiles[test], "error": scalar_error[test]}).groupby("drug").error.max()
        intervals[name] = {"level": .9, "half_width": width, "calibration_drugs": len(residual),
                           "test_drug_simultaneous_coverage": float((group_error <= width).mean()) if width is not None else None,
                           "scope": "scalar transcript-shift RMS only; drug exchangeability assumed; not a gene-wise or biological confidence interval"}
    contrasts = {}
    for a, b in [("multimodal_neural", "chemistry_context_neural"), ("multimodal_ridge", "chemistry_context_dose_ridge"),
                 ("multimodal_neural", "multimodal_ridge"), ("multimodal_neural", "zero_shift"),
                 ("multimodal_neural_permuted_rna", "multimodal_neural")]:
        contrasts[a + " minus " + b] = paired_interval(errors[a] - errors[b], table.smiles[test])
    seed_scores = {key: [float(np.square(p[test] - y[test]).mean()) for p in vals]
                   for key, vals in neural_predictions.items() if key != "permuted_rna"}
    gain = contrasts["multimodal_neural minus chemistry_context_neural"]["ci95"][1] < 0
    report = {"scores": scores, "paired_differences": contrasts, "calibration": intervals,
              "seed_gene_mse": seed_scores, "multimodal_benefit_supported": gain,
              "rows": {k: int(v.sum()) for k, v in masks.items()},
              "molecular_identities": {k: int(table.smiles[v].nunique()) for k, v in masks.items()},
              "biological_mechanism_identified": False,
              "claim_boundary": "Real raw-count training and held-out molecular-identity prediction; chemical/RNA integration, not two measured biological modalities, independent-lab validation or a new biological mechanism."}
    write(output / "metrics.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol_path = args.workspace / "research/model_validation_protocol.json"
    protocol = json.loads(protocol_path.read_text())
    write(args.output / "protocol.json", protocol)
    write(args.output / "run_identity.json", {"protocol_sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
          "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "start_unix": time.time()})
    table, y, baseline, genes = prepare(args.workspace, args.output, protocol)
    print("prepared", len(table), "condition-replicate-plate rows", flush=True)
    report = train_and_evaluate(table, y, baseline, genes, args.output, protocol)
    print(json.dumps({"multimodal_benefit_supported": report["multimodal_benefit_supported"], "rows": report["rows"]}), flush=True)


if __name__ == "__main__":
    main()
