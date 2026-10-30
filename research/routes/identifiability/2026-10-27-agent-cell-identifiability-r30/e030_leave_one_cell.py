"""E030: leave-one-cell-line-out on GDSC - is tissue a usable scope condition?

Pre-registered in PROTOCOL_E030.md. Reads the local Jaaks 2022 GDSC file only.

Unit = (cell line, combination) with the mean SYNERGY_DELTA_AUC. For each held-out cell,
prediction A uses all other cells and prediction B uses same-tissue cells only. Both are
scored by Spearman against the held-out cell's own profile.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r30"
METRIC = "SYNERGY_DELTA_AUC"
MIN_SOURCES = 5
N_BOOT = 1000
SEED = 20261027


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a, b) -> float:
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    if len(a) < 20 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra -= ra.mean()
    rb -= rb.mean()
    return float((ra * rb).sum() / math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum())))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False,
                    usecols=["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", METRIC])
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    piv = d.pivot_table(index="combo", columns="CELL_LINE_NAME", values=METRIC, aggfunc="mean")
    tissue = d.drop_duplicates("CELL_LINE_NAME").set_index("CELL_LINE_NAME")["Tissue"].to_dict()

    rows = []
    for cell in piv.columns:
        own = piv[cell].dropna()
        others_all = [c for c in piv.columns if c != cell]
        same = [c for c in others_all if tissue.get(c) == tissue.get(cell)]
        combos = own.index
        # require MIN_SOURCES elsewhere
        avail_all = piv.loc[combos, others_all].notna().sum(axis=1)
        avail_same = piv.loc[combos, same].notna().sum(axis=1) if same else pd.Series(0, index=combos)
        sel = (avail_all >= MIN_SOURCES) & (avail_same >= MIN_SOURCES)
        if sel.sum() < 30:
            continue
        idx = combos[sel]
        y = own.loc[idx].to_numpy(float)
        pa = piv.loc[idx, others_all].mean(axis=1, skipna=True).to_numpy(float)
        pb = piv.loc[idx, same].mean(axis=1, skipna=True).to_numpy(float)
        rows.append({"cell": cell, "tissue": tissue.get(cell), "n_combos": int(sel.sum()),
                     "n_same_tissue_sources": len(same),
                     "rho_all": spearman(pa, y), "rho_same": spearman(pb, y)})

    r = pd.DataFrame(rows)
    res = {"kind": "leave_one_cell_line_out_tissue_as_scope_condition",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"min_sources": MIN_SOURCES, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"cells_scored": int(len(r)),
                     "cells_total": int(piv.shape[1]),
                     "combos_total": int(piv.shape[0]),
                     "tissues": {k: int(v) for k, v in r["tissue"].value_counts().items()} if len(r) else {}},
           "per_cell": rows, "files": {}}

    def bsum(v, off):
        v = np.asarray(v, float)
        v = v[np.isfinite(v)]
        if not len(v):
            return None
        rng = np.random.default_rng(SEED + off)
        b = [float(np.mean(rng.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
        return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)),
                "iqr": float(np.quantile(v, 0.75) - np.quantile(v, 0.25)),
                "ci95": [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))]}

    if len(r) >= 20:
        diff = (r["rho_same"] - r["rho_all"]).to_numpy(float)
        res["summary"] = {"rho_all": bsum(r["rho_all"], 101), "rho_same": bsum(r["rho_same"], 102),
                          "rho_diff": bsum(diff, 103),
                          "frac_cells_same_better": float(np.nanmean(diff > 0))}
        res["by_tissue"] = {t: {"n": int(len(g)), "rho_all": float(np.nanmedian(g["rho_all"])),
                                "rho_same": float(np.nanmedian(g["rho_same"]))}
                            for t, g in r.groupby("tissue") if len(g) >= 5}
        ra = res["summary"]["rho_all"]
        rd = res["summary"]["rho_diff"]
        h073 = bool(ra["median"] > 0.10 and ra["ci95"][0] > 0)
        h074 = bool(rd["median"] > 0 and rd["ci95"][0] > 0)
        h075 = bool(ra["iqr"] > 0.20)
    else:
        h073 = h074 = h075 = False
    res["decisions"] = {"H073_unseen_cell_predictable": h073, "H074_tissue_is_a_scope_condition": h074,
                        "H075_heterogeneous": h075}
    res["decisions"]["verdict"] = ("tissue_is_a_usable_scope_condition" if h074 else
                                   "unseen_cell_predictable_but_tissue_adds_nothing" if h073 else
                                   "neither_predictable_nor_conditionable")
    res["limits"] = [
        "Predictions come only from other cells; no cell annotation or feature is used.",
        "Only three tissues, and cells within a tissue still differ widely.",
        "SYNERGY_DELTA_AUC is a model-fitted quantity; one or two concentrations per (cell, combination).",
        "No mechanistic, clinical or drug-choice claim.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r30/PROTOCOL_E030.md",
                "research/2026-10-27-agent-cell-identifiability-r30/e030_leave_one_cell.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E030_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E030_per_cell.csv", index=False)

    print("cells scored=%d of %d | combos=%d" % (len(r), piv.shape[1], piv.shape[0]))
    for k in ("rho_all", "rho_same", "rho_diff"):
        if "summary" in res and res["summary"].get(k):
            v = res["summary"][k]
            print("  %-9s median=%.4f mean=%.4f IQR=%.3f CI=[%.4f,%.4f] n=%d" % (
                k, v["median"], v["mean"], v["iqr"], v["ci95"][0], v["ci95"][1], v["n"]))
    if "summary" in res:
        print("  frac cells same-tissue better=%.2f" % res["summary"]["frac_cells_same_better"])
    if "by_tissue" in res:
        print("  by tissue:", json.dumps(res["by_tissue"], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
