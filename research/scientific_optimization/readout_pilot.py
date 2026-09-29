"""Exposed-data pilot: direct signed RNA endpoint regression, not mechanism validation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from virtual_cell.learned_response import transcript_readouts
from virtual_cell.biology import GeneSet


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def group_weights(groups):
    _, inverse, counts = np.unique(groups, return_inverse=True, return_counts=True)
    weights = 1. / counts[inverse]
    return weights * len(weights) / weights.sum()


def fit_readouts(x_fit, y_fit, fit_groups, x_val, y_val, val_groups, x_train, y_train, train_groups, x_test):
    """Fit from training/validation outcomes only; test outcomes are not an argument."""
    scores = {}
    for alpha in (1., 10., 100., 1000.):
        model = Ridge(alpha=alpha, fit_intercept=False, solver="lsqr", tol=1e-6)
        model.fit(x_fit, y_fit, sample_weight=group_weights(fit_groups))
        error = np.square(model.predict(x_val) - y_val).mean(axis=1)
        scores[alpha] = float(np.average(error, weights=group_weights(val_groups)))
    alpha = min(scores, key=lambda a: (scores[a], -a))
    model = Ridge(alpha=alpha, fit_intercept=False, solver="lsqr", tol=1e-6)
    model.fit(x_train, y_train, sample_weight=group_weights(train_groups))
    return model.predict(x_test), {"alpha": alpha, "validation_mse": scores}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, default=ROOT / "outputs/biological_depth_20260926/prepared")
    parser.add_argument("--cv", type=Path, default=ROOT / "outputs/biological_depth_20260926/cv")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    conditions = pd.read_csv(args.prepared / "conditions.csv")
    compounds = pd.read_csv(args.prepared / "compounds.csv").set_index("compound")
    genes = pd.read_csv(args.prepared / "genes.csv").symbol.to_numpy()
    definitions = json.loads((args.prepared / "gene_sets.json").read_text())
    source_digest = digest(args.prepared / "gene_sets.json")
    panels = tuple(GeneSet(k, tuple(v), "previously restricted SciPlex3 Hallmark panels", source_digest,
                           "mean RNA shift") for k, v in sorted(definitions.items()))
    gene_index = {gene: i for i, gene in enumerate(genes)}
    if len(gene_index) != len(genes):
        raise ValueError("duplicate_gene_coordinates")
    projection = np.zeros((len(genes), len(panels)))
    for j, panel in enumerate(panels):
        for gene in panel.members:
            projection[gene_index[gene], j] = 1. / len(panel.members)
    measured = np.load(args.prepared / "shifts.npz")["shift"]
    y = measured @ projection
    # Confirm the pilot's vectorised projection agrees with the serving interface.
    readouts = tuple("rna_set:" + panel.identifier for panel in panels)
    served, _ = transcript_readouts(measured[:1], genes, readouts, panels)
    np.testing.assert_allclose(list(served.values()), y[0], atol=1e-7)
    groups = conditions.compound.map(compounds.skeleton).to_numpy()
    folds = conditions.fold.to_numpy()
    if pd.DataFrame({"group": groups, "fold": folds}).groupby("group").fold.nunique().max() != 1:
        raise ValueError("identity_group_crosses_outer_folds")
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fingerprints = {name: generator.GetFingerprintAsNumPy(Chem.MolFromSmiles(row.smiles))
                    for name, row in compounds.iterrows()}
    fp = np.stack([fingerprints[name] for name in conditions.compound]).astype(float)
    cells = pd.get_dummies(conditions.cell_line, dtype=float).to_numpy()
    dose = np.log1p(conditions.dose.to_numpy()) / np.log1p(10000.)
    x = np.c_[(fp[:, None, :] * cells[:, :, None]).reshape(len(fp), -1), cells] * dose[:, None]
    predictions = {"readout_ridge": np.full_like(y, np.nan)}
    selections = []
    baseline_names = ("zero", "systematic", "ridge_chem", "knn_chem", "mlp_existing", "latent_pca", "latent_jepa")
    for fold in range(5):
        test = np.flatnonzero(folds == fold)
        train = np.flatnonzero(folds != fold)
        ranked = sorted(set(groups[train]), key=lambda s: hashlib.sha256(("maestro-biodepth-inner|" + s).encode()).hexdigest())
        validation_groups = ranked[:max(1, int(round(len(ranked) * .15)))]
        val = train[np.isin(groups[train], validation_groups)]
        fit = train[~np.isin(groups[train], validation_groups)]
        p, selection = fit_readouts(x[fit], y[fit], groups[fit], x[val], y[val], groups[val],
                                   x[train], y[train], groups[train], x[test])
        predictions["readout_ridge"][test] = p
        selections.append({"fold": fold, "fit_units": len(set(groups[fit])),
                           "validation_units": len(set(groups[val])), "test_units": len(set(groups[test])), **selection})
        with np.load(args.cv / f"fold{fold}.npz") as archive:
            np.testing.assert_array_equal(archive["test"], test)
            for name in baseline_names:
                predictions.setdefault(name, np.full_like(y, np.nan))[test] = archive[name + "__prediction"] @ projection
        print(f"fold {fold}: alpha={selection['alpha']}; {len(test)} out-of-fold conditions", flush=True)
    metrics, losses = {}, {}
    for name, p in predictions.items():
        if not np.isfinite(p).all():
            raise ValueError("incomplete_predictions:" + name)
        loss = pd.Series(np.square(p - y).mean(axis=1)).groupby(groups).mean()
        losses[name] = loss
        sign = np.mean((np.sign(p) == np.sign(y)) & (p != 0), axis=1)
        metrics[name] = {"equal_unit_mse": float(loss.mean()),
                         "equal_unit_sign_agreement": float(pd.Series(sign).groupby(groups).mean().mean())}
    contrasts = {}
    for name in baseline_names:
        delta = (losses["readout_ridge"] - losses[name]).to_numpy()
        rng = np.random.default_rng(20260927)
        boot = delta[rng.integers(len(delta), size=(2000, len(delta)))].mean(axis=1)
        contrasts[name] = {"candidate_minus_baseline_mse": float(delta.mean()),
                           "ci95": np.quantile(boot, [.025, .975]).tolist()}
    gate = all(contrasts[name]["ci95"][1] < 0 for name in ("zero", "systematic", "ridge_chem", "knn_chem"))
    sources = [args.prepared / n for n in ("conditions.csv", "compounds.csv", "genes.csv", "gene_sets.json", "shifts.npz")]
    sources += [args.cv / f"fold{i}.npz" for i in range(5)]
    result = {"status": "development_unregistered", "conditions": len(y), "compounds": conditions.compound.nunique(),
              "independent_connectivity_groups": len(set(groups)), "readouts": len(panels), "metrics": metrics,
              "paired_contrasts": contrasts, "folds": selections,
              "prediction_research_gate": "PASS" if gate else "FAIL", "default_promotion": False,
              "decision_gain": "NOT_EVALUATED", "premise_repair_interaction": "NOT_READY",
              "limitations": ["Previously exposed data and annotation-stratified historical folds.",
                              "Connectivity groups are not Murcko scaffolds; only three cell lines and one study.",
                              "Restricted Hallmark mean RNA shift is not functional activity.",
                              "Intervals are descriptive development estimates; no multiplicity correction.",
                              "No calibrated forecast, new assay label or independent decision benefit."],
              "hashes": {str(p.relative_to(ROOT)): digest(p) for p in sources},
              "protocol_sha256": digest(Path(__file__).with_name("PROTOCOL.md")),
              "code_sha256": {str(p.relative_to(ROOT)): digest(p) for p in
                              (Path(__file__), ROOT / "src/virtual_cell/learned_response.py", ROOT / "src/virtual_cell/biology.py")},
              "environment": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__}}
    np.savez_compressed(args.output / "predictions.npz", **predictions)
    (args.output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"gate": result["prediction_research_gate"], "metrics": metrics, "contrasts": contrasts}, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=4):
        main()
