"""E028: on the GDSC combination screen, is synergy a property of the combination or of the cell?

Pre-registered in PROTOCOL_E028.md. Reads the local Jaaks 2022 GDSC files only.

Unit = (combination, anchor concentration, library concentration); the metric is
SYNERGY_DELTA_AUC. Reports the between-combination variance share, a split-half
reliability of combination means across cells, and a permutation null that breaks the
combination-cell pairing.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
BASE = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare"
ORIG = BASE / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r28"
METRIC = "SYNERGY_DELTA_AUC"
N_PERM = 200
N_SPLIT = 20
SEED = 20261027


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def corr(a, b) -> float:
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    if len(a) < 5 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    o = pd.read_csv(ORIG, low_memory=False,
                    usecols=["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
                             "ANCHOR_CONC", "LIBRARY_CONC", METRIC, "Synergy", "ANCHOR_VIABILITY"])
    o = o[np.isfinite(pd.to_numeric(o[METRIC], errors="coerce"))].copy()
    o["combo"] = o["ANCHOR_NAME"].astype(str) + " + " + o["LIBRARY_NAME"].astype(str)
    o["conc_key"] = o["ANCHOR_CONC"].astype(str) + "/" + o["LIBRARY_CONC"].astype(str)
    o["unit"] = o["combo"] + "@" + o["conc_key"]

    # variance decomposition on the unit level
    d = o.dropna(subset=[METRIC])
    grand = float(d[METRIC].mean())
    unit_means = d.groupby("unit")[METRIC].mean()
    unit_n = d.groupby("unit")[METRIC].size()
    between = float((unit_n * (unit_means - grand) ** 2).sum() / unit_n.sum())
    total = float(((d[METRIC] - grand) ** 2).mean())
    between_share = between / total if total > 0 else float("nan")
    within_sd = d.groupby("unit")[METRIC].std()

    # split-half reliability of unit means across cells
    rng = np.random.default_rng(SEED)
    units = [u for u, g in d.groupby("unit") if g["CELL_LINE_NAME"].nunique() >= 10]
    rel = []
    for _ in range(N_SPLIT):
        a_mean, b_mean = [], []
        for u in units:
            g = d[d["unit"] == u]
            cells = g["CELL_LINE_NAME"].to_numpy()
            uniq = np.unique(cells)
            rng.shuffle(uniq)
            half = len(uniq) // 2
            if half < 3:
                continue
            A = g[g["CELL_LINE_NAME"].isin(uniq[:half])][METRIC].mean()
            B = g[g["CELL_LINE_NAME"].isin(uniq[half:])][METRIC].mean()
            a_mean.append(A)
            b_mean.append(B)
        if len(a_mean) > 20:
            rel.append(corr(a_mean, b_mean))
    rel = [r for r in rel if np.isfinite(r)]

    # permutation null: shuffle cell labels across units, keep unit sizes
    perm = []
    for _ in range(N_PERM):
        vals = d[[METRIC]].to_numpy(float).ravel()
        rng.shuffle(vals)
        d2 = d.copy()
        d2[METRIC] = vals
        um = d2.groupby("unit")[METRIC].mean()
        un = d2.groupby("unit")[METRIC].size()
        gr = float(d2[METRIC].mean())
        bt = float((un * (um - gr) ** 2).sum() / un.sum())
        tt = float(((d2[METRIC] - gr) ** 2).mean())
        perm.append(bt / tt if tt > 0 else np.nan)
    perm = [p for p in perm if np.isfinite(p)]

    res = {"kind": "gdsc_external_synergy_combination_vs_cell",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"metric": METRIC, "n_perm": N_PERM, "n_split": N_SPLIT, "seed": SEED},
           "audit": {"rows": int(len(d)), "cells": int(d["CELL_LINE_NAME"].nunique()),
                     "tissues": int(d["Tissue"].nunique()), "combos": int(d["combo"].nunique()),
                     "units": int(d["unit"].nunique()),
                     "cells_per_unit_median": float(d.groupby("unit")["CELL_LINE_NAME"].nunique().median()),
                     "grand_mean": grand, "total_var": total},
           "results": {"between_unit_share": between_share,
                       "within_unit_sd_median": float(within_sd.median()),
                       "split_half_reliability": {"mean": float(np.mean(rel)) if rel else None,
                                                  "ci95": [float(np.quantile(rel, 0.025)), float(np.quantile(rel, 0.975))] if rel else None,
                                                  "n_splits": len(rel)},
                       "permutation_null": {"mean": float(np.mean(perm)) if perm else None,
                                            "q975": float(np.quantile(perm, 0.975)) if perm else None}},
           "files": {}}

    b = res["results"]["between_unit_share"]
    r = res["results"]["split_half_reliability"]["mean"]
    h067 = bool(np.isfinite(b) and b >= 0.50 and r is not None and r >= 0.70)
    h068 = bool(perm and np.isfinite(b) and b > float(np.quantile(perm, 0.975)))
    h069 = bool(res["results"]["within_unit_sd_median"] > 0.02)
    res["decisions"] = {"H067_combination_is_the_main_property": h067,
                        "H068_beats_permutation_null": h068,
                        "H069_cell_variation_is_not_negligible": h069}
    res["decisions"]["verdict"] = ("synergy_is_mainly_a_combination_property" if h067
                                   else "synergy_is_mainly_a_cell_property")
    res["limits"] = [
        "GDSC uses a single concentration pair per row, not a dose grid; this is a different design from BATCHIE.",
        "SYNERGY_DELTA_AUC is a model-fitted quantity, not a raw measurement.",
        "Only three tissues; tissue is not a cell line.",
        "Descriptive external check; no mechanism, no clinical or drug-choice claim.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r28/PROTOCOL_E028.md",
                "research/2026-10-27-agent-cell-identifiability-r28/e028_gdsc_synergy.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E028_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("rows=%d cells=%d combos=%d units=%d cells/unit median=%.0f" % (
        len(d), d["CELL_LINE_NAME"].nunique(), d["combo"].nunique(), d["unit"].nunique(),
        d.groupby("unit")["CELL_LINE_NAME"].nunique().median()))
    print("between-unit share=%.4f" % between_share)
    print("within-unit sd median=%.4f" % res["results"]["within_unit_sd_median"])
    print("split-half reliability=%s" % json.dumps(res["results"]["split_half_reliability"], ensure_ascii=False))
    print("permutation null=%s" % json.dumps(res["results"]["permutation_null"], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
