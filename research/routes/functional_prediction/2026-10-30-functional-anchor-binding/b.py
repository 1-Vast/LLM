"""Fixed morphology-relation countertest; no core or agent integration."""
import os
for option in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[option] = "4"
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]
META = ROOT / "cpjump_source"
RAW = PROJECT / "data/external/functional_anchor_binding_20261030/cpjump"
OUT = PROJECT / "data/processed/functional_anchor_binding_20261030/b"
CELLS = ["A549", "U2OS"]
METHODS = ["fixed_same", "fixed_opposite", "global_mean", "gene_shrink10", "pooled_ridge100",
    "pooled_rbf1", "conditional_ridge100", "conditional_rbf1", "cell_mean",
    "gene_cell_shrink10", "spatial_ridge100", "conditional_spatial_ridge100"]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, obj):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)

def position(well):
    row, column = ord(well[0]) - ord("A"), int(well[1:]) - 1
    r, c = -1 + 2 * row / 15, -1 + 2 * column / 23
    return np.r_[np.eye(16)[row], np.eye(24)[column], r, c, r*r, c*c, r*c,
                 float(row < 2 or row >= 14 or column < 2 or column >= 22)]

def conditional(x, cell):
    return np.c_[x, cell, x * cell[:, None]]

def predict(a, b, y, kernel=False):
    mean, sd = a.mean(0), a.std(0)
    varying = np.count_nonzero(sd)
    sd[sd == 0] = 1
    a, b = (a - mean) / sd, (b - mean) / sd
    if kernel:
        gamma = 1 / max(1, varying)
        def rbf(left, right):
            distance = (left*left).sum(1)[:, None] + (right*right).sum(1)[None, :] - 2 * left @ right.T
            return np.exp(-gamma * np.maximum(distance, 0))
        gram, cross = rbf(a, a), rbf(b, a)
        colmean, grand = gram.mean(0), gram.mean()
        gram = gram - colmean[:, None] - colmean[None, :] + grand
        cross = cross - cross.mean(1)[:, None] - colmean[None, :] + grand
        alpha = 1
    else:
        gram, cross, alpha = a @ a.T, b @ a.T, 100
    return np.clip(y.mean() + cross @ np.linalg.solve(gram + alpha * np.eye(len(a)), y - y.mean()), -1, 1)

def read_profiles(metadata):
    access = {"status": "running", "decoded_rows": 0, "decoded_numeric_cells": 0,
        "skipped_rows": 0, "per_plate": {}, "all_hashes_checked": True, "protected_CGI_access": False}
    plates, features = {}, None
    try:
        for plate in sorted(metadata.Metadata_Plate.unique()):
            rows = metadata[metadata.Metadata_Plate.eq(plate)]
            by_well = {r["Metadata_Well"]: r for r in rows.to_dict("records")}
            path = RAW / f"{plate}.csv"
            detail = {"path": str(path), "decoded_rows": 0, "control_rows": 0,
                "treatment_rows": 0, "skipped_rows": 0, "allowed_wells": []}
            access["per_plate"][plate] = detail
            values, identities, seen = [], [], set()
            with path.open(encoding="utf-8-sig", newline="") as stream:
                header = next(csv.reader([next(stream)]))
                assert header[:2] == ["Metadata_Plate", "Metadata_Well"] and len(header) == 5794
                if features is None:
                    features = header[2:]
                assert features == header[2:]
                for line in stream:
                    prefix = line.split(",", 2)
                    assert len(prefix) == 3
                    row_plate, well = next(csv.reader([",".join(prefix[:2])]))
                    assert row_plate == plate and well in by_well and well not in seen
                    seen.add(well)
                    identity = by_well[well]
                    is_control = identity["Metadata_control_type"] == "negcon"
                    admitted = identity["Metadata_pert_type"] == "trt" or is_control
                    if not admitted:
                        access["skipped_rows"] += 1; detail["skipped_rows"] += 1
                        continue
                    feature_cells = next(csv.reader([prefix[2]]))
                    assert len(feature_cells) == 5792
                    numeric = np.array([float(v) if v else np.nan for v in feature_cells])
                    access["decoded_rows"] += 1; detail["decoded_rows"] += 1
                    access["decoded_numeric_cells"] += len(numeric)
                    detail["control_rows" if is_control else "treatment_rows"] += 1
                    detail["allowed_wells"].append(well)
                    values.append(numeric); identities.append(identity)
            assert seen == set(by_well)
            plates[plate] = (pd.DataFrame(identities), np.asarray(values))
            write(OUT / "access_receipt.json", access)
        access["status"] = "complete"
        return plates, np.array(features)
    except Exception as exc:
        access.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write(OUT / "access_receipt.json", access)

def preprocess(plates, features, split):
    centers, scales, counts = [], [], []
    plate_ids = sorted(plates)
    mask = np.ones(len(features), dtype=bool)
    for plate in plate_ids:
        identity, values = plates[plate]
        control = values[identity.Metadata_control_type.eq("negcon").to_numpy()]
        center = np.median(control, axis=0)
        scale = 1.4826 * np.median(np.abs(control - center), axis=0)
        centers.append(center); scales.append(scale); counts.append(len(control))
        mask &= np.isfinite(control).all(0) & np.isfinite(scale) & (scale > 1e-12)
    if mask.sum() < 100:
        raise RuntimeError("INSUFFICIENT_CONTROL_VALID_FEATURES")
    genes = sorted(set(split.target))
    chemical = np.empty((260, 2, 2, mask.sum()))
    orf = np.empty((len(genes), 2, 2, mask.sum()))
    for cell_index, cell in enumerate(CELLS):
        for modality, destination, field, identities in [
            ("Compound", chemical, "Metadata_broad_sample", split.broad_sample.tolist()),
            ("ORF", orf, "Metadata_gene", genes)]:
            selected = [p for p in plate_ids if plates[p][0].Metadata_cell_line.iloc[0] == cell
                        and plates[p][0].Metadata_experiment_type.iloc[0] == modality]
            assert len(selected) == 2
            for repeat, plate in enumerate(selected):
                identity, values = plates[plate]
                i = plate_ids.index(plate)
                retained = values[:, mask]
                if not np.isfinite(retained).all():
                    raise RuntimeError("DATA_NONFINITE")
                normalized = np.clip((retained - centers[i][mask]) / scales[i][mask], -10, 10)
                for j, key in enumerate(identities):
                    selected_rows = identity[field].eq(key) & identity.Metadata_pert_type.eq("trt")
                    assert selected_rows.sum() == (1 if modality == "Compound" else 2)
                    destination[j, cell_index, repeat] = np.median(normalized[selected_rows], axis=0)
    return {"feature_names": features, "retained_mask": mask, "plate_ids": np.array(plate_ids),
        "control_centers": np.array(centers), "control_scales": np.array(scales),
        "control_counts": np.array(counts), "chemical_effects": chemical,
        "orf_effects": orf, "orf_genes": np.array(genes)}

def relation_grid(chemical, orf):
    grid = np.empty((len(chemical), 2, 2, 2))
    for ci in range(2):
        for oi in range(2):
            a, b = chemical[:, :, ci], orf[:, :, oi]
            denominator = np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1)
            grid[:, :, ci, oi] = np.divide((a * b).sum(-1), denominator,
                out=np.zeros(denominator.shape), where=denominator > 0)
    return np.clip(grid, -1, 1)

def inputs(split, metadata):
    archive = np.load(ROOT / "b_chemical_features.npz", allow_pickle=False)
    assert np.array_equal(archive["compounds"], split.broad_sample.to_numpy())
    genes = sorted(set(split.target))
    target = np.eye(len(genes))[[genes.index(g) for g in split.target]]
    pooled = np.repeat(np.c_[archive["fingerprints"], target], 2, axis=0)
    spatial = []
    for row in split.itertuples():
        for cell in CELLS:
            q = metadata[metadata.Metadata_cell_line.eq(cell)]
            chemical = q[q.Metadata_experiment_type.eq("Compound") & q.Metadata_broad_sample.eq(row.broad_sample)]
            orf = q[q.Metadata_experiment_type.eq("ORF") & q.Metadata_gene.eq(row.target) & q.Metadata_pert_type.eq("trt")]
            assert len(chemical) == 2 and len(orf) == 4
            spatial.append(np.r_[np.mean([position(w) for w in chemical.Metadata_Well], axis=0),
                                  np.mean([position(w) for w in orf.Metadata_Well], axis=0)])
    cell = np.tile([-1., 1.], len(split))
    cond, space = conditional(pooled, cell), conditional(np.array(spatial), cell)
    return pooled, cond, space, np.c_[cond, space]

def model_matrix(split, relation, feature_sets, receipt):
    pooled, cond, space, augmented = feature_sets
    folds, targets = np.repeat(split.fold.to_numpy(), 2), np.repeat(split.target.to_numpy(), 2)
    cells, y = np.tile(np.arange(2), len(split)), relation.ravel()
    result = np.full((12, len(y)), np.nan)
    for fold in sorted(set(folds)):
        train, query = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
        source_y = y[train]
        result[0, query], result[1, query] = 1, -1
        result[2, query] = source_y.mean()
        for q in query:
            same_gene = train[targets[train] == targets[q]]
            same_cell = train[cells[train] == cells[q]]
            gene_cell = same_cell[targets[same_cell] == targets[q]]
            result[3, q] = (y[same_gene].sum() + 10 * source_y.mean()) / (len(same_gene) + 10)
            result[8, q] = y[same_cell].mean()
            result[9, q] = (y[gene_cell].sum() + 10 * y[same_cell].mean()) / (len(gene_cell) + 10)
        for method, features, kernel in [(4, pooled, False), (5, pooled, True), (6, cond, False),
            (7, cond, True), (10, space, False), (11, augmented, False)]:
            result[method, query] = predict(features[train], features[query], source_y, kernel)
        temporary = OUT / "predictions.partial.tmp.npz"
        np.savez_compressed(temporary, methods=np.array(METHODS), predictions=result.reshape(12, 260, 2))
        temporary.replace(OUT / "predictions.partial.npz")
        receipt["completed_folds"] += 1
        write(OUT / "run.json", receipt)
    assert np.isfinite(result).all()
    return result.reshape(12, 260, 2)

def synthetic():
    rng = np.random.default_rng(1030)
    a, b, y = rng.normal(size=(12, 4)), rng.normal(size=(3, 4)), rng.normal(size=12)
    mean, sd = a.mean(0), a.std(0)
    aa, bb = (a - mean) / sd, (b - mean) / sd
    primal = np.clip(y.mean() + bb @ np.linalg.solve(aa.T @ aa + 100*np.eye(4), aa.T @ (y-y.mean())), -1, 1)
    error = float(np.max(np.abs(primal - predict(a, b, y))))
    assert error < 1e-12 and position("A01").shape == (46,) and position("A01")[-1] == 1
    assert position("H12")[-1] == 0
    example = np.array([[[[1., 0.], [0., 0.]], [[1., 0.], [0., 0.]]]])
    assert np.array_equal(relation_grid(example, example), [[[ [1.,0.],[0.,0.] ],[[1.,0.],[0.,0.]]]])
    print(json.dumps({"primal_dual_ridge_error": error, "zero_cosine_and_spatial_basis": "PASS"}))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / "run.json").exists(), "No replay or overwrite"
    started, cpu = time.perf_counter(), time.process_time()
    receipt = {"status": "running", "threads": 4, "completed_folds": 0,
        "python": sys.executable, "numpy": np.__version__, "failure": None,
        "settings": {"n_bootstrap": 2000, "bootstrap_seed": 20261032, "alpha_ridge": 100, "alpha_rbf": 1}}
    write(OUT / "run.json", receipt)
    try:
        freeze = json.loads((ROOT / "b_execution_freeze.json").read_text())
        for path, expected in freeze["sha256"].items():
            assert sha(path) == expected, f"Hash changed: {path}"
        receipt["freeze"] = freeze
        split = pd.read_csv(ROOT / "b_compound_split.tsv", sep="\t", dtype={"fold": int}, keep_default_na=False)
        metadata = pd.read_csv(META / "selected_well_identity_freeze.tsv", sep="\t", dtype=str, keep_default_na=False)
        plates, features = read_profiles(metadata)
        prep = preprocess(plates, features, split)
        np.savez_compressed(OUT / "preprocessing.npz", **prep)
        lookup = {g: i for i, g in enumerate(prep["orf_genes"])}
        grid = relation_grid(prep["chemical_effects"], prep["orf_effects"][[lookup[g] for g in split.target]])
        relation = grid.mean(axis=(2, 3))
        np.savez_compressed(OUT / "labels.npz", compounds=split.broad_sample.to_numpy(dtype=str),
            cells=np.array(CELLS), groups=split.group.to_numpy(dtype=str), folds=split.fold.to_numpy(),
            targets=split.target.to_numpy(dtype=str), relations=relation, relation_grid=grid)
        with threadpool_limits(limits=4):
            predictions = model_matrix(split, relation, inputs(split, metadata), receipt)
        utility = np.sign(predictions) * relation
        regret = np.abs(relation) - utility
        np.savez_compressed(OUT / "predictions.npz", methods=np.array(METHODS), predictions=predictions, utility=utility, regret=regret)
        mean = utility.mean(axis=(1, 2))
        rivals = [i for i in range(12) if i != 6]
        direct = rivals[int(np.argmax(mean[rivals]))]
        difference = utility[6] - utility[direct]
        groups = split.group.to_numpy()
        names = np.unique(groups)
        sums = np.array([difference[groups == g].sum() for g in names])
        counts = np.array([2 * np.count_nonzero(groups == g) for g in names])
        rng = np.random.default_rng(20261032)
        draws = rng.integers(0, len(names), size=(2000, len(names)))
        interval = np.quantile(sums[draws].sum(1) / counts[draws].sum(1), [.025, .975]).tolist()
        action_difference = np.sign(predictions[6]) - np.sign(predictions[direct])
        repeats = grid.mean(axis=3)
        repeat_gain = (action_difference[:, :, None] * repeats).mean(axis=(0, 1)).tolist()
        diagonal = (grid[:, :, 0, 0] + grid[:, :, 1, 1]) / 2
        off_diagonal = (grid[:, :, 0, 1] + grid[:, :, 1, 0]) / 2
        sensitivity = [float((action_difference * r).mean()) for r in (diagonal, off_diagonal)]
        supported = sum(any((split.fold != row.fold) & split.target.eq(row.target)) for row in split.itertuples())
        summary = {"methods": METHODS, "mean_utility": mean.tolist(), "mean_regret": regret.mean(axis=(1, 2)).tolist(),
            "mean_mse": ((predictions - relation)**2).mean(axis=(1, 2)).tolist(),
            "per_cell_utility": utility.mean(axis=1).tolist(), "oracle_mean_utility": float(np.abs(relation).mean()),
            "candidate_method": METHODS[6], "best_direct_method": METHODS[direct],
            "selected_gain": float(difference.mean()), "paired_identity_interval95": interval,
            "chemical_repeat_gains": repeat_gain, "diagonal_offdiagonal_gains": sensitivity,
            "retained_feature_count": int(prep["retained_mask"].sum()), "compounds": 260, "groups": len(names),
            "target_support_queries": int(supported), "source_unseen_target_queries": 260 - int(supported),
            "mean_absolute_relation": float(np.abs(relation).mean()),
            "replicate_sign_agreement": float((np.sign(repeats[:, :, 0]) == np.sign(repeats[:, :, 1])).mean())}
        write(OUT / "summary.json", summary)
        gate = bool(difference.mean() > 0 and min(repeat_gain) > 0 and interval[0] > 0)
        write(OUT / "decision.json", {"status": "EXPLORATORY_ONLY", "information_gate_pass": gate,
            "robust_benefit_established": False, "core_promotion": False, "Agent": False})
        receipt.update(status="complete", shapes={"relations": list(relation.shape), "predictions": list(predictions.shape)})
    except Exception as exc:
        receipt.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        write(OUT / "decision.json", {"status": "EXPLORATORY_ONLY", "information_gate_pass": False,
            "robust_benefit_established": False, "core_promotion": False, "Agent": False, "failure": receipt["failure"]})
        raise
    finally:
        receipt.update(wall_seconds=time.perf_counter()-started, cpu_seconds=time.process_time()-cpu)
        write(OUT / "run.json", receipt)

if __name__ == "__main__":
    if "--synthetic" in sys.argv:
        synthetic()
    else:
        main()
