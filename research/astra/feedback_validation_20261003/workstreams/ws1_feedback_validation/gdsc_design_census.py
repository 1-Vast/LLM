"""WS1 step 3f: DESIGN-ONLY census of the GDSC Combinations releases (Jaaks et al. 2022 anchor screens
and the GDSC_007-010 / Sandpiper-01 7x7 matrix projects).

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws1_feedback_validation/gdsc_design_census.py
- Purpose: decide whether these never-opened releases can serve as an untouched, qualified
  evaluation of "validated hits found by a policy", WITHOUT reading any outcome column. Only the
  header row and the identifier / dose / plate columns listed in DESIGN_* are read; every column
  read is written into the receipt so the release can still be frozen and then opened once.
- Core points: per release - rows, cell lines, tissues, drug pairs, rows per pair x line (plate
  replicates), panel completeness within tissue, overlap of pair x line triples between the anchor
  screens and the matrix projects and among matrix projects (independent re-measurement).
- Interfaces: run the file with PYTHONPATH="src;.".
- Depends on: pandas, numpy.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DATA = ROOT / "data/external/gdsc_combinations"
ANCHOR = ["breast_anchor_combo.csv.gz", "colon_anchor_combo.csv.gz", "pancreas_anchor_combo.csv.gz"]
MATRIX = ["gdsc-007_matrix_results.csv.gz", "gdsc-008_matrix_results.csv.gz", "gdsc-009_matrix_results.csv.gz",
          "gdsc-010_matrix_results.csv.gz", "sandpiper-01_matrix_results.csv.gz"]
# identifier, dose and plate columns only; no viability, Emax, IC50, AUC, synergy or pass column
# (the released anchor files are summarised per line x anchor conc x library: no plate barcode, no drug ID)
DESIGN_ANCHOR = ["Cell Line name", "SDIM", "Tissue", "Cancer Type", "Anchor Name", "Anchor Conc", "Library Name", "Maxc"]
DESIGN_MATRIX = ["BARCODE", "DRUGSET_ID", "cmatrix", "CELL_LINE_NAME", "SIDM", "TISSUE", "CANCER_TYPE",
                 "lib1_ID", "lib1_name", "lib1_minc", "lib1_maxc", "lib2_ID", "lib2_name", "lib2_minc", "lib2_maxc"]


def norm(name) -> str:
    import re
    return re.sub(r"[^A-Z0-9]", "", str(name).upper())


def header(path: Path) -> list[str]:
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        return handle.readline().rstrip("\n").split(",")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def census(frame: pd.DataFrame, a: str, b: str) -> tuple[dict, pd.DataFrame]:
    na, nb = frame[a].map(norm), frame[b].map(norm)
    f = frame.assign(pair=np.where(na < nb, na + "|" + nb, nb + "|" + na))
    if "BARCODE" not in f:
        f = f.assign(BARCODE="NA")
    per = f.groupby(["pair", "SIDM"]).agg(rows=("BARCODE", "size"), plates=("BARCODE", "nunique")).reset_index()
    lines = f["SIDM"].nunique()
    pairs = f["pair"].nunique()
    out = {"rows": int(len(f)), "cell_lines": int(lines), "drug_pairs": int(pairs),
           "drugs": int(len(set(f[a].map(norm)) | set(f[b].map(norm)))),
           "tissues": {str(k): int(v) for k, v in f.groupby("TISSUE")["SIDM"].nunique().items()},
           "pair_x_line_measured": int(len(per)),
           "completeness_pairs_x_lines": round(len(per) / max(lines * pairs, 1), 4),
           "plates_per_pair_line": {str(k): int(v) for k, v in per["plates"].value_counts().sort_index().head(8).items()},
           "rows_per_pair_line_median": float(per["rows"].median()),
           "plates": int(f["BARCODE"].nunique())}
    return out, per


def main() -> int:
    receipt = {"rule": "design-only: header row plus the listed identifier/dose/plate columns; no outcome value read",
               "files": {}, "anchor": {}, "matrix": {}}
    triples = {}
    for name in ANCHOR + MATRIX:
        path = DATA / name
        cols = header(path)
        design = DESIGN_ANCHOR if name in ANCHOR else DESIGN_MATRIX
        use = [c for c in design if c in cols]
        receipt["files"][name] = {"sha256": sha(path), "bytes": path.stat().st_size, "all_columns": cols,
                                  "columns_read": use, "design_columns_missing": [c for c in design if c not in cols]}
        frame = pd.read_csv(path, usecols=use, low_memory=False)
        if name in ANCHOR:
            frame = frame.rename(columns={"SDIM": "SIDM", "Tissue": "TISSUE"})
            info, per = census(frame, "Anchor Name", "Library Name")
            ori = frame.groupby(["Anchor Name", "Library Name"]).size().reset_index()
            rev = set(zip(ori["Library Name"], ori["Anchor Name"]))
            info["ordered_combinations"] = int(len(ori))
            info["ordered_combinations_screened_in_both_orientations"] = int(
                sum((a, l) in rev for a, l in zip(ori["Anchor Name"], ori["Library Name"])))
            info["anchor_concs_per_combo_line_median"] = float(
                frame.groupby(["Anchor Name", "Library Name", "SIDM"])["Anchor Conc"].nunique().median())
            info["rows_per_ordered_combo_line_anchorconc"] = {str(k): int(v) for k, v in frame.groupby(
                ["Anchor Name", "Library Name", "SIDM", "Anchor Conc"]).size().value_counts().sort_index().head(6).items()}
            receipt["anchor"][name] = info
        else:
            info, per = census(frame, "lib1_name", "lib2_name")
            info["drugsets"] = int(frame["DRUGSET_ID"].nunique())
            info["max_conc_settings_per_pair"] = float(frame.groupby(["lib1_name", "lib2_name"])[["lib1_maxc", "lib2_maxc"]].nunique().max(axis=1).median())
            receipt["matrix"][name] = info
        triples[name] = set(zip(per["pair"], per["SIDM"]))
    # overlaps (pair x line identity by Sanger drug ID and SIDM)
    ov = {}
    names = ANCHOR + MATRIX
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            n = len(triples[a] & triples[b])
            if n:
                ov[f"{a} & {b}"] = n
    receipt["triple_overlaps"] = ov
    anchor_all = set().union(*(triples[n] for n in ANCHOR))
    matrix_all = set().union(*(triples[n] for n in MATRIX))
    receipt["anchor_triples"] = len(anchor_all)
    receipt["matrix_triples"] = len(matrix_all)
    receipt["anchor_matrix_overlap_triples"] = len(anchor_all & matrix_all)
    receipt["anchor_matrix_overlap_pairs"] = len({p for p, _ in anchor_all} & {p for p, _ in matrix_all})
    receipt["anchor_matrix_overlap_lines"] = len({s for _, s in anchor_all} & {s for _, s in matrix_all})
    out = HERE / "receipts" / "step3f_gdsc_design_census.json"
    out.write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    slim = {k: v for k, v in receipt.items() if k != "files"}
    slim["columns"] = {n: {"read": f["columns_read"], "n_all": len(f["all_columns"])} for n, f in receipt["files"].items()}
    print(json.dumps(slim, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
