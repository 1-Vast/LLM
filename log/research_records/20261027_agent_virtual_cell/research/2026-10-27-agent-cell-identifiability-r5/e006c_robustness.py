"""E006c: robustness checks for the split-half vs cross-context result.

Three checks, all declared after the primary run and therefore reported as robustness,
not as new pre-registered tests:
  1. per-cell summary (each cell's own ceiling vs its mean cross-context agreement),
     because cell pairs inside one layout are not independent.
  2. censoring control: recompute on interior units only (Viability < 1 in both vectors),
     so differential ceiling saturation cannot manufacture the drop.
  3. QC-drop audit: which cells were dropped and what the layout set loses.
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
N_SUB = 60
N_REDRAW = 50
SEED = 20261027


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 3:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


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
        unit = {w: (d1, c1, d2, c2) for w, d1, c1, d2, c2 in layout}
        files[fname] = {"cell": g["Cell line"].iloc[0],
                        "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                        "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                        "combo": {w: (str(d1).lower() != "dmso" and str(d2).lower() != "dmso")
                                  for w, (d1, c1, d2, c2) in unit.items()},
                        "qc": float(g["failed_qc"].mean()), "layout": layout}
    groups = {}
    for f, s in files.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)

    def vec(fname: str, units: list[str]) -> np.ndarray:
        sub = df[(df["file"] == fname) & (~df["failed_qc"]) & df["y"].notna() & (~df["anchor"])]
        return sub.drop_duplicates("Well").set_index("Well")["y"].reindex(units).to_numpy(dtype=float)

    rng = np.random.default_rng(SEED)
    cell_rows, interior_rows, qc_rows = [], [], []
    for (it, h), cells in groups.items():
        if len(cells) < 3:
            continue
        good = [c for c in sorted(cells) if max(files[f]["qc"] for f in cells[c]) <= 0.20]
        for c in sorted(cells):
            if c not in good:
                qc_rows.append({"layout": f"{it}/{h[:12]}", "cell": c,
                                "qc_frac": round(max(files[f]["qc"] for f in cells[c]), 3)})
        if len(good) < 3:
            continue
        units = [u for u in sorted(files[cells[good[0]][0]]["combo"]) if files[cells[good[0]][0]]["combo"][u]]
        V = {c: [vec(f, units) for f in cells[c]] for c in good}
        avail_all = np.all(np.vstack([np.sum([~np.isnan(v) for v in V[c]], axis=0) > 0 for c in good]), axis=0)
        if avail_all.sum() < 20:
            continue
        sub_idx = [rng.choice(len(units), N_SUB, replace=False) for _ in range(N_REDRAW)]

        def tau(va, vb, interior=False):
            vals = []
            for idx in sub_idx:
                a, b = va[idx], vb[idx]
                ok = ~np.isnan(a) & ~np.isnan(b)
                if interior:
                    ok &= (a < 1.0) & (b < 1.0)
                if ok.sum() < 20:
                    continue
                vals.append(spearman(a[ok], b[ok]))
            return float(np.nanmean(vals)) if vals else float("nan")

        half, half_int = {}, {}
        for c in good:
            if len(V[c]) >= 2:
                half[c] = tau(V[c][0], V[c][1])
                half_int[c] = tau(V[c][0], V[c][1], interior=True)
        for c in good:
            partners = []
            partners_int = []
            for d in good:
                if d == c:
                    continue
                ts = [tau(fa, fb) for fa in V[c] for fb in V[d]]
                ts_i = [tau(fa, fb, interior=True) for fa in V[c] for fb in V[d]]
                partners.append(np.nanmean(ts))
                partners_int.append(np.nanmean(ts_i))
            ceil = half.get(c, float("nan"))
            cell_rows.append({"layout": f"{it}/{h[:12]}", "cell": c, "tau_half": ceil,
                              "tau_cross_mean": float(np.nanmean(partners)),
                              "drop": ceil - float(np.nanmean(partners)),
                              "ceiling_frac": float(np.nanmean([(v == 1.0).mean() for v in V[c] if not np.isnan(v).all()])),
                              "tau_half_interior": half_int.get(c, float("nan")),
                              "tau_cross_interior_mean": float(np.nanmean(partners_int)),
                              "drop_interior": half_int.get(c, float("nan")) - float(np.nanmean(partners_int))})
            interior_rows.append(cell_rows[-1])

    cr = pd.DataFrame(cell_rows).dropna(subset=["tau_half", "tau_cross_mean"])
    ir = pd.DataFrame(interior_rows).dropna(subset=["tau_half_interior", "tau_cross_interior_mean"])
    out = {
        "kind": "robustness_checks_after_primary",
        "input_sha256": sha256(CSV),
        "per_cell_summary": {
            "n_cells_with_ceiling": int(len(cr)),
            "n_cells_cross_below_half": int((cr["drop"] > 0).sum()),
            "frac_cells_cross_below_half": float((cr["drop"] > 0).mean()) if len(cr) else None,
            "median_tau_half": float(cr["tau_half"].median()) if len(cr) else None,
            "median_tau_cross_mean": float(cr["tau_cross_mean"].median()) if len(cr) else None,
            "median_drop": float(cr["drop"].median()) if len(cr) else None,
            "iqr_drop": [float(cr["drop"].quantile(0.25)), float(cr["drop"].quantile(0.75))] if len(cr) else None,
            "note": "cell pairs inside a layout are dependent; this per-cell view is the independent-ish summary",
        },
        "censoring_control": {
            "n_cells": int(len(ir)),
            "n_cells_cross_below_half_interior": int((ir["drop_interior"] > 0).sum()),
            "median_tau_half_interior": float(ir["tau_half_interior"].median()) if len(ir) else None,
            "median_tau_cross_interior": float(ir["tau_cross_interior_mean"].median()) if len(ir) else None,
            "median_drop_interior": float(ir["drop_interior"].median()) if len(ir) else None,
            "note": "only units with Viability < 1 in both vectors, so differential ceiling saturation is excluded",
        },
        "qc_drops": qc_rows,
        "correlation_ceiling_frac_vs_drop": float(cr[["ceiling_frac", "drop"]].corr().iloc[0, 1]) if len(cr) > 2 else None,
        "per_cell_table": cr.round(4).to_dict("records"),
    }
    for rel in ("research/2026-10-27-agent-cell-identifiability-r5/e006c_robustness.py",):
        p = ROOT / rel
        if p.exists():
            out.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E006C_ROBUSTNESS.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print("PER-CELL: n=%d cross<half in %d (%.2f) | median half=%.3f cross=%.3f drop=%.3f IQR=%s" % (
        len(cr), out["per_cell_summary"]["n_cells_cross_below_half"],
        out["per_cell_summary"]["frac_cells_cross_below_half"] or float("nan"),
        cr["tau_half"].median() if len(cr) else float("nan"),
        cr["tau_cross_mean"].median() if len(cr) else float("nan"),
        cr["drop"].median() if len(cr) else float("nan"), out["per_cell_summary"]["iqr_drop"]))
    print("INTERIOR-ONLY (no ceiling ties): n=%d cross<half in %d | median half=%.3f cross=%.3f drop=%.3f" % (
        len(ir), out["censoring_control"]["n_cells_cross_below_half_interior"],
        ir["tau_half_interior"].median() if len(ir) else float("nan"),
        ir["tau_cross_interior_mean"].median() if len(ir) else float("nan"),
        ir["drop_interior"].median() if len(ir) else float("nan")))
    print("corr(ceiling fraction, drop) =", out["correlation_ceiling_frac_vs_drop"])
    print("QC-dropped cells:", len(qc_rows), sorted({r["cell"] for r in qc_rows}))


if __name__ == "__main__":
    main()
