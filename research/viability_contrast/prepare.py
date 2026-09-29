"""Prepare the frozen data pack for the viability-contrast task (protocol viability-contrast-1).

File summary
- Path: research/viability_contrast/prepare.py
- Purpose: build the frozen data pack (AUC matrix, annotations, connectivity-block units,
  folds, menu pool, eligibility, class set) with a SHA-256 manifest. Descriptive construction
  only: no template, k value, arm or outcome is computed here.
- Interfaces / data: reads data/raw/prism/secondary-screen-dose-response-curve-parameters.csv and
  data/raw/depmap/CRISPRGeneEffect.csv (line index only); writes
  outputs/viability_contrast_20260928/prepared/{auc.npz, meta.csv, folds.json, menu.json, manifest.json}.
- Depends on: research/viability_contrast/protocol.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")

ROOT = Path(__file__).resolve().parents[2]
PRISM = ROOT / "data/raw/prism/secondary-screen-dose-response-curve-parameters.csv"
CRISPR = ROOT / "data/raw/depmap/CRISPRGeneEffect.csv"
OUT = ROOT / "outputs/viability_contrast_20260928/prepared"
KEY = "viability-contrast-1"
N_FOLDS = 5
LINE_COVERAGE = 0.8
ROW_COVERAGE = 0.8
MIN_CLASS_UNITS = 8


def compound_id(broad_id: str) -> str:
    parts = str(broad_id).split("-")
    return "-".join(parts[:2]) if len(parts) >= 2 else str(broad_id)


def unit_block(smiles: str):
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    mol = Chem.MolFromSmiles(smiles.split(",")[0].strip())
    return Chem.MolToInchiKey(mol)[:14] if mol is not None else None


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def build() -> dict:
    cols = ["broad_id", "depmap_id", "screen_id", "auc", "name", "moa", "smiles"]
    df = pd.read_csv(PRISM, usecols=cols, low_memory=False)
    df["compound"] = df["broad_id"].map(compound_id)
    df = df[df["screen_id"].isin(["MTS010", "HTS002"])]
    df["prio"] = (df["screen_id"] == "MTS010").astype(int)
    df = df.sort_values("prio").drop_duplicates(["compound", "depmap_id"], keep="last")

    piv = df.pivot_table(index="compound", columns="depmap_id", values="auc")

    meta = df.drop_duplicates("compound")[["compound", "name", "moa", "smiles"]].set_index("compound")
    meta["moa_main"] = meta["moa"].str.split(",").str[0].str.strip()
    meta["unit"] = meta["smiles"].map(unit_block)
    ann = meta.dropna(subset=["moa_main", "unit"])
    ann = ann[~ann.duplicated(["moa_main", "unit"])]

    # Class set over compounds present in the matrix.
    present = ann.index.intersection(piv.index)
    ann = ann.loc[present]
    big = ann.groupby("moa_main").size()
    big = big[big >= MIN_CLASS_UNITS].index
    cand = ann[ann["moa_main"].isin(big)].index
    sub = piv.loc[cand]

    # Menu pool: lines measured for >= LINE_COVERAGE of candidate compounds.
    pool = list(sub.columns[sub.notna().mean() >= LINE_COVERAGE])
    pool.sort()
    sub = sub[pool]
    # Eligibility: >= ROW_COVERAGE of pool lines measured.
    elig = sub.index[sub.notna().mean(axis=1) >= ROW_COVERAGE]
    sub = sub.loc[elig]
    ann = ann.loc[elig]
    classes = sorted(ann["moa_main"].unique())

    # Folds: within each class stratum (alphabetical class order), units sorted by
    # SHA256(KEY|unit) and assigned round-robin; a unit spanning classes takes the
    # fold of its first stratum.
    fold_of: dict[str, int] = {}
    for cls in classes:
        units = sorted(ann.loc[ann["moa_main"] == cls, "unit"].unique(), key=lambda u: sha(f"{KEY}|{u}"))
        for rank, u in enumerate(units):
            if u not in fold_of:
                fold_of[u] = rank % N_FOLDS
    ann = ann.copy()
    ann["fold"] = ann["unit"].map(fold_of)

    # CRISPR line membership (index column only).
    crispr_lines = set(pd.read_csv(CRISPR, usecols=[0]).iloc[:, 0])
    pool_crispr = sorted(set(pool) & crispr_lines)

    OUT.mkdir(parents=True, exist_ok=True)
    compounds = list(sub.index)
    lines = list(sub.columns)
    auc = sub.to_numpy(dtype=np.float32)
    np.savez_compressed(
        OUT / "auc.npz",
        auc=auc,
        compounds=np.array(compounds),
        lines=np.array(lines),
    )
    ann_out = ann[["name", "moa_main", "unit", "fold"]].reset_index()
    ann_out.to_csv(OUT / "meta.csv", index=False)
    folds = {str(f): sorted(ann.index[ann["fold"] == f].tolist()) for f in range(N_FOLDS)}
    (OUT / "folds.json").write_text(json.dumps(folds, indent=1), encoding="utf-8")
    menu = {
        "pool_lines": pool,
        "pool_lines_with_crispr": pool_crispr,
        "classes": classes,
        "params": {
            "line_coverage": LINE_COVERAGE,
            "row_coverage": ROW_COVERAGE,
            "min_class_units": MIN_CLASS_UNITS,
            "n_folds": N_FOLDS,
        },
    }
    (OUT / "menu.json").write_text(json.dumps(menu, indent=1), encoding="utf-8")

    manifest = {
        "key": KEY,
        "source_sha256": {"prism_curves": file_sha(PRISM)},
        "outputs_sha256": {p.name: file_sha(p) for p in sorted(OUT.iterdir()) if p.is_file()},
        "shape": {
            "compounds": len(compounds),
            "lines": len(lines),
            "classes": len(classes),
            "pool_lines_with_crispr": len(pool_crispr),
            "matrix_density": float(np.isfinite(auc).mean()),
            "units": int(ann["unit"].nunique()),
            "per_fold": {str(f): len(folds[str(f)]) for f in range(N_FOLDS)},
        },
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_pack():
    """Load the frozen pack; callers must verify manifest digests first (freeze.verify)."""
    z = np.load(OUT / "auc.npz", allow_pickle=False)
    auc = z["auc"].astype(np.float64)
    compounds = [str(c) for c in z["compounds"]]
    lines = [str(c) for c in z["lines"]]
    meta = pd.read_csv(OUT / "meta.csv").set_index("compound")
    folds = json.loads((OUT / "folds.json").read_text(encoding="utf-8"))
    menu = json.loads((OUT / "menu.json").read_text(encoding="utf-8"))
    return {
        "auc": auc,
        "compounds": compounds,
        "lines": lines,
        "meta": meta,
        "folds": folds,
        "menu": menu,
        "index": {c: i for i, c in enumerate(compounds)},
        "line_index": {l: i for i, l in enumerate(lines)},
    }


if __name__ == "__main__":
    m = build()
    print(json.dumps(m["shape"], indent=1))
