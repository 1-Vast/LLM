"""Review A2: DESIGN-ONLY census for new-data qualification (no outcome column is parsed).

File summary
- Path: research/astra/reproducible_allocation_20261003/review/design_census.py
- Purpose: decide whether the downloaded but outcome-unread GDSC matrix releases (gdsc-007..010,
  sandpiper-01) hold repeated plates of the same combination x line that could act as independent
  verification for a complete declared menu, and whether the portal anchor_combo files are the
  Jaaks 2022 data. Plan: review/plan.json (A2).
- Core points:
  - pandas `usecols` restricts parsing to identifier / plate / dose columns (listed in the receipt);
    forbidden columns are never parsed.
  - Matrix: plates per pair x line; whether repeats share drug set, concentrations and matrix slot;
    complete drug-set replicates per line (every matrix of a drug set measured on >= 2 plates);
    cross-release overlap of pair x line at identical concentrations.
  - Anchor: (line, anchor, library, anchor conc) overlap of portal anchor_combo with the Jaaks
    original screen and its rescreen (design columns of already-opened files).
- Interfaces: `python -m research.astra.reproducible_allocation_20261003.review.design_census`;
  writes review/design_census.json (refuses to overwrite).
- Depends on: pandas, numpy.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA = ROOT / "data/external/gdsc_combinations"
OUT = HERE / "design_census.json"
MATRIX = ["gdsc-007", "gdsc-008", "gdsc-009", "gdsc-010", "sandpiper-01"]
MCOLS = ["BARCODE", "DRUGSET_ID", "cmatrix", "CELL_LINE_NAME", "SIDM", "TISSUE", "lib1_ID", "lib1_name",
         "lib1_minc", "lib1_maxc", "lib2_ID", "lib2_name", "lib2_minc", "lib2_maxc"]
ACOLS = ["Cell Line name", "SDIM", "Tissue", "Anchor Name", "Anchor Conc", "Library Name", "Maxc"]
JCOLS = ["BARCODE", "Tissue", "SIDM", "ANCHOR_NAME", "ANCHOR_CONC", "LIBRARY_NAME", "LIBRARY_CONC"]
FORBIDDEN_HINTS = ("MaxE", "IC50", "RMSE", "Delta", "Bliss", "HSA", "window", "day1", "growth", "doubling",
                   "Emax", "Synergy", "VIAB", "SYNERGY", "Xmid", "XMID")


def norm(x) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(x).upper())


def guard(cols: list[str]) -> None:
    bad = [c for c in cols if any(h.lower() in c.lower() for h in FORBIDDEN_HINTS)]
    if bad:
        raise SystemExit(f"FORBIDDEN_COLUMN: {bad}")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matrix_census(name: str) -> tuple[dict, pd.DataFrame]:
    path = DATA / f"{name}_matrix_results.csv.gz"
    guard(MCOLS)
    f = pd.read_csv(path, usecols=MCOLS, low_memory=False)
    a, b = f["lib1_ID"].astype(str), f["lib2_ID"].astype(str)
    f["pair"] = np.where(a < b, a + "|" + b, b + "|" + a)
    f["conc"] = (f["lib1_maxc"].round(6).astype(str) + "/" + f["lib1_minc"].round(6).astype(str) + "|"
                 + f["lib2_maxc"].round(6).astype(str) + "/" + f["lib2_minc"].round(6).astype(str))
    per = f.groupby(["pair", "SIDM"]).agg(plates=("BARCODE", "nunique"), rows=("BARCODE", "size"),
                                          drugsets=("DRUGSET_ID", "nunique"), concs=("conc", "nunique"),
                                          cmatrix=("cmatrix", "nunique")).reset_index()
    rep = per[per["plates"] >= 2]
    # drug-set level: is a whole plate layout replicated on >= 2 plates of the same line?
    ds = f.groupby(["DRUGSET_ID", "SIDM"]).agg(plates=("BARCODE", "nunique"), pairs=("pair", "nunique")).reset_index()
    ds_pairs = f.groupby("DRUGSET_ID")["pair"].nunique()
    ds_lines = f.groupby("DRUGSET_ID")["SIDM"].nunique()
    # lines in which every pair of the release measured in that line has >= 2 plates
    per_line = per.groupby("SIDM").agg(pairs=("pair", "size"), rep_pairs=("plates", lambda s: int((s >= 2).sum())))
    full_rep_lines = per_line[(per_line["rep_pairs"] == per_line["pairs"])]
    heavy = per[per["plates"] >= 5]
    heavy_lines = f[f["SIDM"].isin(heavy["SIDM"])].groupby("SIDM")["CELL_LINE_NAME"].first()
    # pairs repeated in many lines
    pair_rep_lines = rep.groupby("pair")["SIDM"].nunique().sort_values(ascending=False)
    lines_per_pair = per.groupby("pair")["SIDM"].nunique()
    # plate-level: barcodes per line and spread of barcodes for repeated pair-lines (barcode is a plate id, not a date)
    bc = f[["pair", "SIDM", "BARCODE"]].drop_duplicates()
    rep_keys = set(zip(rep["pair"], rep["SIDM"]))
    bc_rep = bc[[k in rep_keys for k in zip(bc["pair"], bc["SIDM"])]]
    spread = bc_rep.groupby(["pair", "SIDM"])["BARCODE"].agg(lambda s: int(s.max() - s.min()) if np.issubdtype(s.dtype, np.number) else -1)
    out = {
        "file": path.name, "sha256": sha(path), "bytes": path.stat().st_size, "columns_parsed": MCOLS,
        "rows": int(len(f)), "plates": int(f["BARCODE"].nunique()), "lines": int(f["SIDM"].nunique()),
        "pairs": int(f["pair"].nunique()), "drugsets": int(f["DRUGSET_ID"].nunique()),
        "pairs_per_drugset": {str(k): int(v) for k, v in ds_pairs.items()},
        "lines_per_drugset": {str(k): int(v) for k, v in ds_lines.items()},
        "rows_per_plate_median": float(f.groupby("BARCODE").size().median()),
        "pair_x_line": int(len(per)),
        "pair_x_line_with_2plus_plates": int(len(rep)),
        "share_pair_x_line_repeated": round(len(rep) / max(len(per), 1), 4),
        "repeated_same_drugset_share": round(float((rep["drugsets"] == 1).mean()), 4) if len(rep) else None,
        "repeated_same_concentrations_share": round(float((rep["concs"] == 1).mean()), 4) if len(rep) else None,
        "drugset_x_line": int(len(ds)),
        "drugset_x_line_with_2plus_plates": int((ds["plates"] >= 2).sum()),
        "lines_with_any_drugset_replicated": int(ds[ds["plates"] >= 2]["SIDM"].nunique()),
        "lines_with_every_pair_repeated": int(len(full_rep_lines)),
        "pairs_per_line_median": float(per_line["pairs"].median()),
        "lines_with_5plus_plates_for_some_pair": {str(k): str(v) for k, v in heavy_lines.items()},
        "pairs_repeated_in_most_lines_top5": {str(k): int(v) for k, v in pair_rep_lines.head(5).items()},
        "lines_per_pair_median": float(lines_per_pair.median()),
        "repeated_barcode_spread_median": float(spread.median()) if len(spread) else None,
    }
    return out, f[["pair", "SIDM", "conc", "BARCODE"]].assign(release=name)


def anchor_vs_jaaks() -> dict:
    guard(ACOLS)
    guard(JCOLS)
    portal = []
    for t in ("breast", "colon", "pancreas"):
        p = pd.read_csv(DATA / f"{t}_anchor_combo.csv.gz", usecols=ACOLS, low_memory=False)
        p = p.assign(file=t)
        portal.append(p)
    p = pd.concat(portal)
    p["key"] = p["SDIM"].astype(str) + "|" + p["Anchor Name"].map(norm) + "|" + p["Library Name"].map(norm)
    p["keyc"] = p["key"] + "|" + p["Anchor Conc"].astype(float).round(6).astype(str)
    res = {"portal_rows": int(len(p)), "portal_lines": int(p["SDIM"].nunique()),
           "portal_ordered_combo_x_line": int(p["key"].nunique()),
           "portal_ordered_combo_x_line_x_anchorconc": int(p["keyc"].nunique())}
    for label, fn in (("jaaks_original", "original_screen_all_tissues_fitted.csv"),
                      ("jaaks_rescreen", "validation_screen_all_tissues_fitted.csv")):
        j = pd.read_csv(DATA / "jaaks2022_figshare" / fn, usecols=JCOLS, dtype={"ANCHOR_CONC": str}, low_memory=False)
        j["key"] = j["SIDM"].astype(str) + "|" + j["ANCHOR_NAME"].map(norm) + "|" + j["LIBRARY_NAME"].map(norm)
        j["keyc"] = j["key"] + "|" + pd.to_numeric(j["ANCHOR_CONC"], errors="coerce").round(6).astype(str)
        pk, jk = set(p["key"]), set(j["key"])
        pkc, jkc = set(p["keyc"]), set(j["keyc"])
        res[label] = {"rows": int(len(j)), "lines": int(j["SIDM"].nunique()), "plates": int(j["BARCODE"].nunique()),
                      "ordered_combo_x_line": len(jk), "shared_with_portal": len(pk & jk),
                      "portal_share_in_this": round(len(pk & jk) / max(len(pk), 1), 4),
                      "this_share_in_portal": round(len(pk & jk) / max(len(jk), 1), 4),
                      "with_anchor_conc_shared": len(pkc & jkc),
                      "portal_share_in_this_with_conc": round(len(pkc & jkc) / max(len(pkc), 1), 4)}
    return res


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    receipt = {"rule": "DESIGN-ONLY: pandas usecols restricted to the listed identifier/plate/dose columns; no outcome column parsed",
               "matrix": {}, "cross_release": {}}
    frames = []
    for name in MATRIX:
        info, frame = matrix_census(name)
        receipt["matrix"][name] = info
        frames.append(frame)
    allf = pd.concat(frames)
    trip = allf.groupby(["pair", "SIDM"]).agg(releases=("release", "nunique"), concs=("conc", "nunique"),
                                              plates=("BARCODE", "nunique")).reset_index()
    multi = trip[trip["releases"] >= 2]
    receipt["cross_release"] = {
        "pair_x_line_in_2plus_releases": int(len(multi)),
        "of_which_same_concentrations": int((multi["concs"] == 1).sum()),
        "pairs_involved": int(multi["pair"].nunique()), "lines_involved": int(multi["SIDM"].nunique()),
        "pairs_x_lines_complete_rectangle": None}
    if len(multi):
        pl = multi.groupby("pair")["SIDM"].nunique()
        receipt["cross_release"]["lines_per_shared_pair"] = {str(k): int(v) for k, v in pl.items()}
    receipt["anchor_vs_jaaks"] = anchor_vs_jaaks()
    OUT.write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    print(json.dumps(receipt, indent=1)[:12000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
