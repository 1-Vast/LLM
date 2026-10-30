"""E006e: sign-reversal rate at a fixed readable separation.

This re-specifies the primary quantity in the form the independent challenge asked for:
an explicit alternative "some fraction of well-separated pairs reverse order in some
context", estimated as a RATE with a layout-clustered interval, instead of a p-value from
a self-authored null.

Rule (fixed a priori, not tuned): a unit pair qualifies when the viability gap exceeds
0.10 in BOTH compared vectors. 0.10 is the detectability bound measured in R4 for this
readout (2.5 x sigma_w). A reversal is opposite signs of the gap in the two vectors.

Same-cell control: the two replicate files of one cell, identical rule. Any reversal
there is residual technical/day noise, so the excess
    excess = rate(cross) - rate(same cell)
is the part attributable to comparing different cells (with their different experiments).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r5"
ANCHORS = {"high control", "low control"}
GAPS = (0.10, 0.15)
N_BOOT = 2000
SEED = 20261027


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rates(x: np.ndarray, y: np.ndarray, floor: float) -> tuple[int, int]:
    """(reversals, qualifying pairs) for two measurement vectors over the same units."""
    i, j = np.triu_indices(x.size, 1)
    gx = np.abs(x[i] - x[j])
    gy = np.abs(y[i] - y[j])
    keep = (gx >= floor) & (gy >= floor)
    if keep.sum() == 0:
        return 0, 0
    sx = np.sign(x[i][keep] - x[j][keep])
    sy = np.sign(y[i][keep] - y[j][keep])
    return int((sx != sy).sum()), int(keep.sum())


def main() -> None:
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")

    files = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], pd.to_numeric(g["Conc 1 (uM)"]).round(9),
                                  g["Drug 2"], pd.to_numeric(g["Conc 2 (uM)"]).round(9))))
        files[fname] = {"cell": g["Cell line"].iloc[0],
                        "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                        "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                        "combo": {w: (str(d1).lower() != "dmso" and str(d2).lower() != "dmso")
                                  for w, (d1, c1, d2, c2) in
                                  {w: (d1, c1, d2, c2) for w, d1, c1, d2, c2 in layout}.items()},
                        "qc": float(g["failed_qc"].mean())}
    groups = {}
    for f, s in files.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)

    def vec(fname: str, units: list[str]) -> np.ndarray:
        sub = df[(df["file"] == fname) & (~df["failed_qc"]) & df["y"].notna() & (~df["anchor"])]
        return sub.drop_duplicates("Well").set_index("Well")["y"].reindex(units).to_numpy(dtype=float)

    per_cell, per_cellpair = [], []
    for (it, h), cells in groups.items():
        if len(cells) < 3:
            continue
        good = [c for c in sorted(cells) if max(files[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        units = [u for u in sorted(files[cells[good[0]][0]]["combo"]) if files[cells[good[0]][0]]["combo"][u]]
        V = {c: [vec(f, units) for f in cells[c]] for c in good}
        if np.all(np.vstack([np.sum([~np.isnan(v) for v in V[c]], axis=0) > 0 for c in good]), axis=0).sum() < 20:
            continue
        for floor in GAPS:
            for c in good:
                if len(V[c]) < 2:
                    continue
                a, b = V[c][0], V[c][1]
                ok = ~np.isnan(a) & ~np.isnan(b)
                r, n = rates(a[ok], b[ok], floor)
                if n >= 20:
                    per_cell.append({"gap": floor, "layout": f"{it}/{h[:12]}", "cell": c,
                                     "reversals": r, "pairs": n, "rate": r / n})
            for ai, ca in enumerate(good):
                for cb in good[ai + 1:]:
                    rr = nn = 0
                    for fa in V[ca]:
                        for fb in V[cb]:
                            ok = ~np.isnan(fa) & ~np.isnan(fb)
                            r, n = rates(fa[ok], fb[ok], floor)
                            rr += r
                            nn += n
                    if nn >= 20:
                        per_cellpair.append({"gap": floor, "layout": f"{it}/{h[:12]}",
                                             "cell_a": ca, "cell_b": cb,
                                             "reversals": rr, "pairs": nn, "rate": rr / nn})

    res = {"kind": "sign_reversal_rate_at_fixed_readable_separation",
           "input_sha256": sha256(CSV), "rule": "gap >= threshold in BOTH compared vectors; reversal = opposite sign",
           "by_gap": {}}
    rng = np.random.default_rng(SEED)
    for floor in GAPS:
        half = pd.DataFrame([r for r in per_cell if r["gap"] == floor])
        cross = pd.DataFrame([r for r in per_cellpair if r["gap"] == floor])
        layouts = sorted(set(list(half["layout"].unique()) + list(cross["layout"].unique())))
        boots_h, boots_c, boots_d = [], [], []
        for _ in range(N_BOOT):
            pick = rng.choice(layouts, size=len(layouts), replace=True)
            hs = pd.concat([half[half["layout"] == p] for p in pick]) if len(half) else pd.DataFrame()
            cs = pd.concat([cross[cross["layout"] == p] for p in pick]) if len(cross) else pd.DataFrame()
            if len(hs) and len(cs):
                rh = float((hs["reversals"].sum()) / (hs["pairs"].sum()))
                rc = float((cs["reversals"].sum()) / (cs["pairs"].sum()))
                boots_h.append(rh)
                boots_c.append(rc)
                boots_d.append(rc - rh)
        agg_h = float(half["reversals"].sum() / half["pairs"].sum()) if len(half) else None
        agg_c = float(cross["reversals"].sum() / cross["pairs"].sum()) if len(cross) else None
        res["by_gap"][str(floor)] = {
            "same_cell_control": {"n_cells": int(len(half)), "pairs": int(half["pairs"].sum()) if len(half) else 0,
                                  "reversals": int(half["reversals"].sum()) if len(half) else 0,
                                  "rate": agg_h,
                                  "ci95_layout_clustered": [float(np.quantile(boots_h, 0.025)), float(np.quantile(boots_h, 0.975))] if boots_h else None},
            "cross_cell": {"n_cellpairs": int(len(cross)), "pairs": int(cross["pairs"].sum()) if len(cross) else 0,
                           "reversals": int(cross["reversals"].sum()) if len(cross) else 0,
                           "rate": agg_c,
                           "ci95_layout_clustered": [float(np.quantile(boots_c, 0.025)), float(np.quantile(boots_c, 0.975))] if boots_c else None},
            "excess_cross_minus_same_cell": {"point": (agg_c - agg_h) if (agg_c is not None and agg_h is not None) else None,
                                             "ci95_layout_clustered": [float(np.quantile(boots_d, 0.025)), float(np.quantile(boots_d, 0.975))] if boots_d else None},
            "n_layouts": len(layouts),
        }
    res["per_cell_same_cell"] = per_cell
    res["per_cellpair_cross_cell"] = per_cellpair
    res["limits"] = [
        "Threshold 0.10 in both vectors is a fixed pre-specified readable separation (2.5 sigma_w from R4); it is not tuned.",
        "Pairs are selected by response-derived gaps, so the absolute rates are conditional on that selection; the same rule is applied to the same-cell control, and only the excess is interpreted.",
        "Layouts are the BATCHIE Project_Validation plates drawn from the remaining combination space and already used as scoring endpoints by an earlier round: exploratory, not confirmatory.",
        "Different cells were measured on different days, so the excess mixes background with batch.",
        "No mechanism, target engagement, selectivity or clinical claim.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r5/e006e_reversal_rate.py",):
        p = ROOT / rel
        if p.exists():
            res.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E006E_REVERSAL_RATE.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    for floor in GAPS:
        d = res["by_gap"][str(floor)]
        print("gap>=%.2f | same-cell %d/%d = %.4f %s | cross %d/%d = %.4f %s | excess %.4f %s" % (
            floor, d["same_cell_control"]["reversals"], d["same_cell_control"]["pairs"],
            d["same_cell_control"]["rate"] or float("nan"), d["same_cell_control"]["ci95_layout_clustered"],
            d["cross_cell"]["reversals"], d["cross_cell"]["pairs"], d["cross_cell"]["rate"] or float("nan"),
            d["cross_cell"]["ci95_layout_clustered"],
            d["excess_cross_minus_same_cell"]["point"] or float("nan"), d["excess_cross_minus_same_cell"]["ci95_layout_clustered"]))


if __name__ == "__main__":
    main()
