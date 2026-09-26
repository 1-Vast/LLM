"""Five-fold compound-grouped cross-validation of every pre-registered arm.

File summary
- Path: research/biological_depth/run_cv.py
- Purpose: produce out-of-fold predictions for all compounds, so every metric scores a model on
  compounds it never saw, with all doses and lines of a compound held out together.
- Core points:
  - A pathway class present only in the held-out fold maps to the zero "unknown" embedding.
  - Timings and per-fold selections are written beside the predictions.
- Run: python research/biological_depth/run_cv.py --prepared <dir> --output <dir> [--folds 0,1,2,3,4]
- Depends on: common.py, models.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import common
import models

LINES = ("A549", "K562", "MCF7")
ARMS = ("zero", "systematic", "ridge_chem", "knn_chem", "mlp_existing", "latent_pca", "latent_mae",
        "latent_jepa", "latent_jepa_moa", "latent_jepa_moa_shuffled")


def load(prepared: Path) -> dict:
    conditions = pd.read_csv(prepared / "conditions.csv", index_col="condition_id")
    compounds = pd.read_csv(prepared / "compounds.csv")
    groups = pd.read_csv(prepared / "groups.csv", index_col="group_id")
    shifts = np.load(prepared / "shifts.npz")
    chunks = np.load(prepared / "chunks.npz")
    return {"conditions": conditions, "compounds": compounds, "groups": groups, "shift": shifts["shift"],
            "group_mean": np.load(prepared / "pseudobulk.npz")["group_mean"], "chunk_mean": chunks["chunk_mean"],
            "chunk_group": chunks["chunk_group"]}


def build(data: dict, fold: int) -> models.FoldData:
    conditions, compounds, groups = data["conditions"], data["compounds"], data["groups"]
    compound_index = {c: i for i, c in enumerate(compounds.compound)}
    cond_compound = conditions.compound.map(compound_index).to_numpy()
    folds = compounds.fold.to_numpy()
    test = np.flatnonzero(conditions.fold.to_numpy() == fold)
    train = np.flatnonzero(conditions.fold.to_numpy() != fold)
    train_compounds = np.flatnonzero(folds != fold)
    inner = common.inner_validation(sorted(compounds.skeleton[train_compounds].unique()))
    val = train[np.isin(compounds.skeleton.to_numpy()[cond_compound[train]], list(inner))]
    classes = sorted(compounds.pathway_level_2.dropna().unique())
    seen = set(compounds.pathway_level_2[train_compounds].dropna())
    moa = np.array([classes.index(c) + 1 if c in seen else 0 for c in compounds.pathway_level_2], dtype=np.int64)
    by_skeleton = compounds.drop_duplicates("skeleton")[["skeleton", "pathway_level_2"]].reset_index(drop=True)
    permuted = by_skeleton.pathway_level_2.to_numpy()[np.random.default_rng(20260926).permutation(len(by_skeleton))]
    shuffled_label = dict(zip(by_skeleton.skeleton, permuted))
    moa_shuffled = np.array([classes.index(shuffled_label[s]) + 1 if shuffled_label[s] in seen else 0
                             for s in compounds.skeleton], dtype=np.int64)
    smiles = compounds.smiles.tolist()
    shift = data["shift"].copy()
    shift[test] = np.nan  # a held-out response cannot be read, even by accident
    d = models.FoldData(
        lines=LINES, cond_line=conditions.cell_line.map({l: i for i, l in enumerate(LINES)}).to_numpy(),
        cond_compound=cond_compound, cond_dose=conditions.dose.to_numpy(dtype=np.float32), shift=shift,
        train=train, val=val, test=test, fp2048=models.morgan(smiles, 2048), fp512=models.morgan(smiles, 512),
        moa=moa, n_moa=len(classes) + 1, chunk_mean=data["chunk_mean"], chunk_group=data["chunk_group"],
        group_line=groups.cell_line.map({l: i for i, l in enumerate(LINES)}).to_numpy(),
        group_compound=groups.compound.map(compound_index).fillna(-1).astype(int).to_numpy(),
        group_dose=groups.dose.to_numpy(dtype=np.float32),
        group_rep=groups.replicate.map({"rep1": 0, "rep2": 1}).to_numpy(),
        group_mean=data["group_mean"], train_compounds=train_compounds)
    d.extras["moa_shuffled"] = moa_shuffled
    return d


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--folds", default="0,1,2,3,4")
    parser.add_argument("--arms", default=",".join(ARMS))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    protocol = common.load_protocol()
    cfg, seeds = protocol["latent"], protocol["latent"]["seeds"]
    data = load(args.prepared)
    n, genes = data["shift"].shape
    arms = [a for a in args.arms.split(",") if a]
    for fold in (int(f) for f in args.folds.split(",")):
        started = time.time()
        d = build(data, fold)
        record = {"fold": fold, "test_conditions": len(d.test), "train_conditions": len(d.train),
                  "inner_validation_conditions": len(d.val), "arms": {}}

        def log(message):
            print(f"[fold {fold}] {time.time() - started:7.1f}s {message}", flush=True)

        predictions: dict[str, dict] = {}
        simple = {"zero": models.predict_zero, "systematic": models.predict_systematic,
                  "ridge_chem": models.predict_ridge, "knn_chem": models.predict_knn,
                  "mlp_existing": lambda x: models.predict_mlp_existing(x, seeds)}
        for arm, fn in simple.items():
            if arm in arms:
                t = time.time()
                predictions[arm] = fn(d)
                record["arms"][arm] = {"seconds": round(time.time() - t, 1),
                                       **{k: v for k, v in predictions[arm].items() if k in ("selected_alpha",)}}
                log(f"{arm} done")
        if any(a.startswith("latent") for a in arms):
            t = time.time()
            latent = models.latent_arms(d, cfg, seeds, d.extras["moa_shuffled"], log=log)
            record["latent_diagnostics"] = latent.pop("_diagnostics")
            record["arms"]["latent_all"] = {"seconds": round(time.time() - t, 1)}
            predictions.update({k: v for k, v in latent.items() if k in arms})
        out = {"test": d.test}
        for arm, value in predictions.items():
            out[f"{arm}__prediction"] = value["prediction"].astype(np.float32)
            if "spread" in value:
                out[f"{arm}__spread"] = np.asarray(value["spread"], dtype=np.float32)
            if "log10_ec50" in value:
                out[f"{arm}__log10_ec50"] = np.asarray(value["log10_ec50"], dtype=np.float32)
        np.savez_compressed(args.output / f"fold{fold}.npz", **out)
        record["seconds"] = round(time.time() - started, 1)
        common.write_json(args.output / f"fold{fold}.json", record)
        log("fold written")
    common.write_json(args.output / "run_identity.json", {
        "protocol_hashes": common.frozen_hashes(),
        "runner_sha256": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                          for name in ("run_cv.py", "models.py", "common.py")},
        "device": models.DEVICE, "conditions": n, "genes": genes})


if __name__ == "__main__":
    main()
