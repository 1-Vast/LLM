"""Additive data-pack extension for the v5 dual-core run (genetic tier).

File summary
- Path: research/viability_contrast/prepare5.py
- Purpose: write outputs/viability_contrast_20260928/prepared/genetic.npz and
  class_gene.json for the registered phase-G5 genetic tier (protocol5.json). Annotation-only
  class-to-gene map (mode of the first-listed target symbol among the class's pack
  compounds; no reading data enters the map) plus the CRISPR Chronos matrix sliced to the
  menu pool lines with CRISPR x the union of mapped class genes, with per-gene pool-line
  marginal median/MAD as the D-prior. Descriptive construction only: no template, arm or
  outcome is computed here. This is an addition, not a rebuild: the v1-v4 pack files stay
  byte-identical and freeze5.json covers these files.
- Depends on: research/viability_contrast/prepare.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import prepare

OUT = prepare.OUT


def symbol(col: str) -> str:
    return col.split(" (")[0].strip()


def build() -> dict:
    pack = prepare.load_pack()
    classes = pack["menu"]["classes"]
    pool_crispr = pack["menu"]["pool_lines_with_crispr"]

    # Class -> primary target gene (annotation-only).
    cols = ["broad_id", "name", "moa", "target"]
    df = pd.read_csv(prepare.PRISM, usecols=cols, low_memory=False)
    df["compound"] = df["broad_id"].map(prepare.compound_id)
    df["moa_main"] = df["moa"].str.split(",").str[0].str.strip()
    df["gene1"] = df["target"].fillna("").str.split(",").str[0].str.strip()
    first = df.drop_duplicates("compound").set_index("compound")["gene1"]
    meta = pack["meta"]
    class_gene = {}
    for c in classes:
        genes = [first.get(x, "") for x in meta.index[meta["moa_main"] == c]]
        genes = [g for g in genes if g]
        class_gene[c] = pd.Series(genes).mode().iloc[0] if genes else None

    # CRISPR slice to pool lines x mapped genes.
    crispr = pd.read_csv(prepare.CRISPR, index_col=0)
    sym_of = {col: symbol(col) for col in crispr.columns}
    col_of_gene = {}
    for col, sym in sym_of.items():
        col_of_gene.setdefault(sym, col)
    genes = sorted({g for g in class_gene.values() if g})
    kept = {g: col_of_gene[g] for g in genes if g in col_of_gene}
    lines = [l for l in pack["lines"]]
    line_pos = {l: i for i, l in enumerate(lines)}
    pool_pos = np.array([line_pos[l] for l in pool_crispr], dtype=int)
    sub = crispr.reindex(pool_crispr)
    gene_list = sorted(kept)
    dep = np.full((len(pool_crispr), len(gene_list)), np.nan, dtype=np.float32)
    for j, g in enumerate(gene_list):
        dep[:, j] = sub[kept[g]].to_numpy(dtype=np.float32)
    med = np.nanmedian(dep, axis=0)
    mad = 1.4826 * np.nanmedian(np.abs(dep - med[None, :]), axis=0)

    np.savez_compressed(
        OUT / "genetic.npz",
        dep=dep,
        pool_pos=pool_pos,
        genes=np.array(gene_list),
        dep_med=med.astype(np.float32),
        dep_mad=np.maximum(mad, 0.05).astype(np.float32),
    )
    (OUT / "class_gene.json").write_text(json.dumps(class_gene, indent=1), encoding="utf-8")
    return {
        "classes_with_gene": int(sum(1 for g in class_gene.values() if g)),
        "genes_mapped": len(gene_list),
        "pool_lines_with_crispr": len(pool_crispr),
        "dep_density": float(np.isfinite(dep).mean()),
    }


def load_genetic():
    z = np.load(OUT / "genetic.npz", allow_pickle=False)
    return {
        "dep": z["dep"].astype(np.float64),
        "pool_pos": z["pool_pos"],
        "genes": [str(g) for g in z["genes"]],
        "dep_med": z["dep_med"].astype(np.float64),
        "dep_mad": z["dep_mad"].astype(np.float64),
        "class_gene": json.loads((OUT / "class_gene.json").read_text(encoding="utf-8")),
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=1))
