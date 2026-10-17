"""Build the development tables from exposed PRISM 19Q4 and estimate the probe noise.

File summary
- Path: research/indication_triage_20261016/build.py
- Purpose: one cached `tables.npz` that the development run reads, plus BUILD.json with digests,
  shapes and the probe-noise estimate the protocol freezes.
- Core points:
  - Responses: PRISM 19Q4 primary log2 fold change at 2.5 uM, collapsed to the Broad core (runs
    of one core averaged per line), for the 4,528 cores of the knowledge-reality development set
    and the 545 panel lines of the sealed census. Using the sealed panel's lines in development
    keeps the two populations on the same columns.
  - Folds and families: copied from `knowledge_reality_20261013/compounds.csv` (MoA-family folds
    0-4); nothing is re-split.
  - Structure: Morgan radius 2, 2,048 bits, from the first parsable SMILES of the core.
  - Probe noise: the replicate-level PRISM 19Q4 secondary screen at 2.5 uM gives within-condition
    replicate spread on the same platform. A probe is simulated as a fresh replicate-collapsed
    measurement, so its disagreement with the published collapsed value has variance
    2 x var(median of 3 replicates). The factor for a median of three normal replicates is
    computed by simulation, not assumed.
  - No PRISM 24Q2 response value is read; only the census's line list.
- Output: tmp/indication_triage_20261016/tables.npz and BUILD.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import (CACHE, DEPMAP_INFO, DEV_COMPOUNDS, HERE, PRISM_LFC, PRISM_SECONDARY_REPLICATE_INFO,
                    PRISM_SECONDARY_REPLICATES, PRISM_TREATMENTS, SEALED_CENSUS, SEED, sha256, write_json)

PROBE_DOSE = 2.5       # uM, the primary screen's single dose


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


def median3_factor(draws: int = 400000) -> float:
    """var(median of 3 iid standard normals), by simulation with a fixed seed."""

    x = np.random.default_rng(SEED).standard_normal((draws, 3))
    return float(np.median(x, axis=1).var())


def probe_noise(lines: list[str]) -> dict:
    info = pd.read_csv(PRISM_SECONDARY_REPLICATE_INFO,
                       usecols=["column_name", "broad_id", "dose", "perturbation_type", "screen_id", "compound_plate", "well"])
    info = info[(info["perturbation_type"] == "experimental_treatment") & ((info["dose"] - PROBE_DOSE).abs() < 0.2)]
    header = pd.read_csv(PRISM_SECONDARY_REPLICATES, nrows=0).columns
    info = info[info["column_name"].isin(set(header))]
    lfc = pd.read_csv(PRISM_SECONDARY_REPLICATES, index_col=0, usecols=[header[0], *info["column_name"]])
    lfc = lfc.reindex(index=[l for l in lines if l in lfc.index])
    sq, df, centre, groups = [], [], [], 0
    for _, grp in info.groupby(["broad_id", "screen_id", "compound_plate", "well"]):
        cols = list(grp["column_name"])
        if len(cols) < 2:
            continue
        m = lfc[cols].to_numpy(np.float64)
        ok = np.isfinite(m).sum(1) >= 2
        if not ok.any():
            continue
        m = m[ok]
        groups += 1
        k = np.isfinite(m).sum(1)
        mean = np.nanmean(m, axis=1)
        sq.append(np.nansum((m - mean[:, None]) ** 2, axis=1))
        df.append(k - 1)
        centre.append(np.nanmedian(m, axis=1))
    sq, df, centre = np.concatenate(sq), np.concatenate(df), np.concatenate(centre)
    sigma = float(np.sqrt(sq.sum() / df.sum()))
    bins = {}
    for name, lo, hi in (("le_-2", -np.inf, -2.0), ("-2_-1", -2.0, -1.0), ("-1_0", -1.0, 0.0), ("gt_0", 0.0, np.inf)):
        sel = (centre > lo) & (centre <= hi)
        bins[name] = {"cells": int(sel.sum()), "sigma_replicate": float(np.sqrt(sq[sel].sum() / max(df[sel].sum(), 1)))}
    factor = median3_factor()
    return {"source": "PRISM 19Q4 secondary, replicate level, experimental treatments at 2.5 uM",
            "conditions": groups, "cells": int(len(sq)), "lines_used": int(len(lfc.index)),
            "sigma_replicate": sigma, "median3_variance_factor": factor,
            "sigma_probe": float(np.sqrt(2.0 * factor) * sigma),
            "sigma_replicate_by_centre": bins,
            "rule": "probe = published value + N(0, sigma_probe^2); sigma_probe^2 = 2 x factor x sigma_replicate^2"}


def main() -> None:
    census = json.loads(SEALED_CENSUS.read_text(encoding="utf-8"))
    panel = list(census["panel_lines"])
    comp = pd.read_csv(DEV_COMPOUNDS)
    info = pd.read_csv(PRISM_TREATMENTS)
    info["core"] = info["broad_id"].str[:13]
    lfc = pd.read_csv(PRISM_LFC, index_col=0)
    cols = info.set_index("column_name")["core"]
    lfc = lfc.loc[:, [c for c in lfc.columns if c in cols.index]]
    by_core = lfc.T.groupby(cols.reindex(lfc.columns).values).mean()
    missing_lines = [l for l in panel if l not in by_core.columns]
    lines = [l for l in panel if l in by_core.columns]
    cores = [c for c in comp["core"] if c in by_core.index]
    Y = by_core.loc[cores, lines].to_numpy(np.float32)
    smiles = info.sort_values(["core", "screen_id"]).groupby("core")["smiles"].first()
    fp = fingerprints([smiles.get(c, "") for c in cores])
    c2 = comp.set_index("core").loc[cores]
    sample = pd.read_csv(DEPMAP_INFO, index_col=0)
    lineage = sample.reindex(lines)["lineage"].fillna("unknown").to_numpy(dtype=str)
    noise = probe_noise(lines)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE / "tables.npz", cores=np.array(cores), lines=np.array(lines), Y=Y, fp=fp,
                        fold=c2["fold"].to_numpy(np.int8), family=c2["family"].to_numpy(dtype=str), lineage=lineage)
    finite = np.isfinite(Y)
    write_json(HERE / "BUILD.json", {
        "compounds": len(cores), "lines": len(lines), "panel_lines_missing_in_19q4": missing_lines,
        "fold_sizes": {str(k): int(v) for k, v in pd.Series(c2["fold"]).value_counts().sort_index().items()},
        "response_finite_fraction": float(finite.mean()),
        "compounds_with_100_finite_lines": int((finite.sum(1) >= 100).sum()),
        "fingerprint_empty": int((fp.sum(1) == 0).sum()),
        "lineages": int(len(set(lineage))),
        "probe_noise": noise,
        "inputs": {"prism_lfc": sha256(PRISM_LFC), "prism_treatments": sha256(PRISM_TREATMENTS),
                   "secondary_replicates": sha256(PRISM_SECONDARY_REPLICATES),
                   "secondary_replicate_info": sha256(PRISM_SECONDARY_REPLICATE_INFO),
                   "dev_compounds": sha256(DEV_COMPOUNDS), "sealed_census": sha256(SEALED_CENSUS),
                   "depmap_info": sha256(DEPMAP_INFO)},
        "tables_sha256": sha256(CACHE / "tables.npz"),
        "reads_24q2_outcomes": False,
    })
    print(len(cores), len(lines), noise["sigma_replicate"], noise["sigma_probe"])


if __name__ == "__main__":
    main()
