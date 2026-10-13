"""Build the analysis tables: responses, basal context of target genes, fingerprints and knowledge.

File summary
- Path: research/knowledge_reality_20261013/build.py
- Purpose: turn the census and the raw sources into one cached `tables.npz` the models read.
- Core points:
  - Responses: PRISM 19Q4 primary log2 fold change at 2.5 uM, compound (core) by line, restricted
    to census compounds and to lines with CCLE 19Q4 expression. The compound's own values are the
    outcome. No model input reads them for that compound at T0.
  - Basal context, per (gene, line), for every gene that carries a kept edge:
    - expression z across lines (log2 TPM+1);
    - expressed: log2 TPM+1 >= 1;
    - hotspot mutation;
    - deleterious mutation.
    These describe the cell line, not the compound.
  - Fingerprints: Morgan radius 2, 2,048 bits.
  - Knowledge: the census edge table (T0 and T1 edges, outcome-proximal and metabolic removed),
    as integer arrays.
  - PRISM secondary (8-dose, same platform) area under the curve is attached for the compounds
    that have it, as the format-shift readout.
- Output: tmp/knowledge_reality_20261013/tables.npz and BUILD.json (digests and shapes).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from sources import (CACHE, HERE, PRISM_LFC, PRISM_SECONDARY, PRISM_SECONDARY_TREATMENTS, load_ccle, sha256,
                     write_json)

PROV_GROUP = {"curated_hub": 0, "curated_mechanism": 0, "binding_aggregate": 1, "assay_biochemical": 1,
              "assay_cell_engagement": 2}
RELATION_INDEX = {"inh": 0, "act": 1, "bind": 2}


def fingerprints(smiles: list[str]) -> np.ndarray:
    from rdkit import Chem, DataStructs, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*")
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    out = np.zeros((len(smiles), 2048), dtype=np.uint8)
    for i, s in enumerate(smiles):
        for part in str(s).split(","):
            mol = Chem.MolFromSmiles(part.strip())
            if mol is not None:
                arr = np.zeros((2048,), dtype=np.uint8)
                DataStructs.ConvertToNumpyArray(gen.GetFingerprint(mol), arr)
                out[i] = arr
                break
    return out


def secondary_auc(cores: list[str], lines: list[str]) -> tuple[np.ndarray, list[str]]:
    """Trapezoid area under the secondary dose-response (log2 FC over log10 dose), per core and line."""

    info = pd.read_csv(PRISM_SECONDARY_TREATMENTS)
    info["core"] = info["broad_id"].str[:13]
    info = info[info["core"].isin(cores)]
    lfc = pd.read_csv(PRISM_SECONDARY, index_col=0)
    lfc = lfc.reindex(index=lines)
    out = np.full((len(cores), len(lines)), np.nan, dtype=np.float32)
    pos = {c: i for i, c in enumerate(cores)}
    for core, grp in info.groupby("core"):
        # One screen per core: the one with the most doses, earliest id on ties.
        best = grp.groupby("screen_id")["dose"].nunique().sort_values(ascending=False).index[0]
        g = grp[(grp["screen_id"] == best) & grp["column_name"].isin(lfc.columns)].sort_values("dose")
        if g["dose"].nunique() < 4:
            continue
        doses = np.log10(g.groupby("dose").size().index.values)
        m = np.stack([lfc[g[g["dose"] == d]["column_name"]].mean(axis=1).values for d in sorted(g["dose"].unique())], axis=1)
        full = np.isfinite(m).all(1)
        vals = np.full(len(lines), np.nan)
        vals[full] = np.trapezoid(m[full], doses, axis=1) / (doses[-1] - doses[0])
        for li in np.where(~full & (np.isfinite(m).sum(1) >= 4))[0]:
            f = np.isfinite(m[li])
            vals[li] = np.trapezoid(m[li][f], doses[f]) / (doses[f][-1] - doses[f][0])
        out[pos[core]] = vals
    return out, sorted(info["core"].unique())


def main() -> None:
    comp = pd.read_csv(HERE / "compounds.csv")
    edges = pd.read_csv(CACHE / "edges.csv")
    lfc = pd.read_csv(PRISM_LFC, index_col=0)
    from sources import PRISM_TREATMENTS
    info = pd.read_csv(PRISM_TREATMENTS)
    info["core"] = info["broad_id"].str[:13]
    cols = info.set_index("column_name")["core"]
    lfc = lfc.loc[:, [c for c in lfc.columns if c in cols.index]]
    by_core = lfc.T.groupby(cols.reindex(lfc.columns).values).mean()
    cores = [c for c in comp["core"] if c in by_core.index]
    genes = sorted(set(edges["gene"]))
    ccle = load_ccle(list(by_core.columns), set(genes))
    lines = ccle["lines"]
    Y = by_core.loc[cores, lines].to_numpy(np.float32)
    expr = ccle["expression"]
    genes = [g for g in genes if g in expr.columns]
    E = expr[genes].to_numpy(np.float32)                                  # line x gene
    sd = E.std(0)
    Z = np.where(sd > 1e-6, (E - E.mean(0)) / np.maximum(sd, 1e-6), 0.0).astype(np.float32)
    gi = {g: j for j, g in enumerate(genes)}
    li = {l: i for i, l in enumerate(lines)}
    hot = np.zeros((len(lines), len(genes)), dtype=np.uint8)
    dele = np.zeros_like(hot)
    for g, l in ccle["mutations"]["hotspot"]:
        if g in gi and l in li:
            hot[li[l], gi[g]] = 1
    for g, l in ccle["mutations"]["deleterious"]:
        if g in gi and l in li:
            dele[li[l], gi[g]] = 1
    smiles = pd.read_csv(PRISM_TREATMENTS).assign(core=lambda d: d["broad_id"].str[:13]).groupby("core")["smiles"].first()
    fp = fingerprints([smiles.get(c, "") for c in cores])
    ci = {c: i for i, c in enumerate(cores)}
    e = edges[edges["core"].isin(ci) & edges["gene"].isin(gi) & edges["provenance"].isin(PROV_GROUP)]
    moa = pd.read_csv(PRISM_TREATMENTS).assign(core=lambda d: d["broad_id"].str[:13]).groupby("core")["moa"].apply(
        lambda s: sorted({x.strip() for v in s.dropna() for x in str(v).split(",") if x.strip()}))
    moa_names = sorted({m for c in cores for m in moa.get(c, [])})
    mi = {m: j for j, m in enumerate(moa_names)}
    moa_pairs = np.array([(ci[c], mi[m]) for c in cores for m in moa.get(c, [])], dtype=np.int32).reshape(-1, 2)
    sec, sec_cores = secondary_auc(cores, lines)
    c2 = comp.set_index("core").loc[cores]
    np.savez_compressed(
        CACHE / "tables.npz",
        cores=np.array(cores), lines=np.array(lines), genes=np.array(genes), Y=Y, expr_z=Z,
        expressed=(E >= 1.0).astype(np.uint8), hotspot=hot, deleterious=dele, fp=fp,
        expr_sd=sd.astype(np.float32), expr_mean=E.mean(0).astype(np.float32),
        edge_drug=e["core"].map(ci).to_numpy(np.int32), edge_gene=e["gene"].map(gi).to_numpy(np.int32),
        edge_rel=e["relation"].map(RELATION_INDEX).to_numpy(np.int8),
        edge_prov=e["provenance"].map(PROV_GROUP).to_numpy(np.int8),
        edge_source=e["provenance"].to_numpy(dtype="U24"),
        moa_names=np.array(moa_names), moa_pairs=moa_pairs,
        fold=c2["fold"].to_numpy(np.int8), family=c2["family"].to_numpy(dtype=str), unit=c2["unit"].to_numpy(dtype=str),
        strict_new_target=c2["strict_new_target"].to_numpy(bool), secondary=sec,
        lineage=ccle["info"]["lineage"].fillna("unknown").to_numpy(dtype=str) if "lineage" in ccle["info"] else
        ccle["info"]["disease"].fillna("unknown").to_numpy(dtype=str))
    write_json(HERE / "BUILD.json", {
        "compounds": len(cores), "lines": len(lines), "genes_with_context": len(genes),
        "edges_used": int(len(e)), "edges_by_group": {str(k): int(v) for k, v in e["provenance"].value_counts().items()},
        "secondary_compounds": int(np.isfinite(sec).any(1).sum()),
        "response_finite_fraction": float(np.isfinite(Y).mean()),
        "inputs": {"prism_lfc": sha256(PRISM_LFC), "prism_secondary": sha256(PRISM_SECONDARY),
                   "edges_csv": sha256(CACHE / "edges.csv"), "compounds_csv": sha256(HERE / "compounds.csv")},
        "tables_sha256": sha256(CACHE / "tables.npz"),
    })
    print(len(cores), len(lines), len(genes), len(e))


if __name__ == "__main__":
    main()
