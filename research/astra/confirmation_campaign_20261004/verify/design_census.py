"""DESIGN-ONLY census for data qualification (verify workstream, Task 3). No outcome column is parsed.

File summary
- Path: research/astra/confirmation_campaign_20261004/verify/design_census.py
- Purpose: count, from identifier / plate / dose columns only, (1) the overlap between the exposed
  Jaaks 2022 anchored screen (line x unordered drug pair, matched by normalised drug name) and the
  outcome-unread GDSC matrix releases gdsc-007..010 and sandpiper-01, i.e. whether a matrix
  measurement could serve as an untouched cross-protocol verification of a Jaaks screen
  measurement; (2) the BATCHIE random-validation round's overlap with the adaptive screen
  (same dose pair? which lines? pair history for a joint rate).
- Core points: pandas `usecols`; a guard refuses any column whose name hints at an outcome.
- Interfaces: `python -m research.astra.confirmation_campaign_20261004.verify.design_census`;
  writes verify/design_census.json (refuses to overwrite).
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
GD = ROOT / "data/external/gdsc_combinations"
OUT = HERE / "design_census.json"
OUT_ADDENDUM = HERE / "design_census_addendum1.json"   # BATCHIE re-count with control wells excluded
MATRIX = ["gdsc-007", "gdsc-008", "gdsc-009", "gdsc-010", "sandpiper-01"]
MCOLS = ["BARCODE", "DRUGSET_ID", "SIDM", "TISSUE", "CELL_LINE_NAME", "lib1_ID", "lib1_name", "lib1_minc", "lib1_maxc",
         "lib2_ID", "lib2_name", "lib2_minc", "lib2_maxc"]
JCOLS = ["BARCODE", "Tissue", "SIDM", "ANCHOR_ID", "ANCHOR_NAME", "ANCHOR_CONC", "LIBRARY_ID", "LIBRARY_NAME",
         "LIBRARY_CONC"]
BCOLS = ["Well", "Cell line", "Drug 1", "Drug 2", "Conc 1 (uM)", "Conc 2 (uM)", "Iteration", "Plate"]
FORBIDDEN = ("maxe", "ic50", "rmse", "delta", "bliss", "hsa", "window", "day1", "growth", "doubling", "emax",
             "synergy", "viab", "raw count", "failed", "intensity", "inhibition")


def guard(cols):
    bad = [c for c in cols if any(h in c.lower() for h in FORBIDDEN)]
    if bad:
        raise SystemExit(f"FORBIDDEN_COLUMN: {bad}")


def norm(x) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(x).upper())


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jaaks_pairs() -> pd.DataFrame:
    guard(JCOLS)
    j = pd.read_csv(GD / "jaaks2022_figshare/original_screen_all_tissues_fitted.csv", usecols=JCOLS,
                    dtype=str, low_memory=False)
    a, b = j["ANCHOR_NAME"].map(norm), j["LIBRARY_NAME"].map(norm)
    j["pair"] = np.where(a < b, a + "|" + b, b + "|" + a)
    j["SIDM"] = j["SIDM"].str.strip()
    return j


def matrix_overlap(j: pd.DataFrame) -> dict:
    jl = j.groupby(["SIDM", "pair"]).agg(tissue=("Tissue", "first"), plates=("BARCODE", "nunique"),
                                        orientations=("ANCHOR_NAME", "nunique")).reset_index()
    jkeys = set(zip(jl["SIDM"], jl["pair"]))
    jlines = set(jl["SIDM"])
    jdrugs = set(j["ANCHOR_NAME"].map(norm)) | set(j["LIBRARY_NAME"].map(norm))
    out = {}
    for name in MATRIX:
        guard(MCOLS)
        f = pd.read_csv(GD / f"{name}_matrix_results.csv.gz", usecols=MCOLS, low_memory=False)
        f["SIDM"] = f["SIDM"].astype(str).str.strip()
        a, b = f["lib1_name"].map(norm), f["lib2_name"].map(norm)
        f["pair"] = np.where(a < b, a + "|" + b, b + "|" + a)
        per = f.groupby(["SIDM", "pair"]).agg(plates=("BARCODE", "nunique"), tissue=("TISSUE", "first"),
                                             name=("CELL_LINE_NAME", "first")).reset_index()
        keys = set(zip(per["SIDM"], per["pair"]))
        both = keys & jkeys
        mdrugs = set(a) | set(b)
        pairs_in_both_any_line = set(per["pair"]) & set(jl["pair"])
        sub = per[[k in both for k in zip(per["SIDM"], per["pair"])]]
        out[name] = {
            "matrix_lines": int(per["SIDM"].nunique()), "matrix_pairs": int(per["pair"].nunique()),
            "matrix_lines_also_in_jaaks": int(len(set(per["SIDM"]) & jlines)),
            "matrix_drugs_also_in_jaaks": sorted(mdrugs & jdrugs),
            "pairs_in_both_screens_any_line": sorted(pairs_in_both_any_line),
            "line_x_pair_in_both": int(len(both)),
            "lines_with_overlap": int(sub["SIDM"].nunique()),
            "pairs_with_overlap": int(sub["pair"].nunique()),
            "overlap_matrix_plates_ge2": int((sub["plates"] >= 2).sum()),
            "overlap_by_tissue": {k: int(v) for k, v in sub.groupby("tissue").size().items()},
            "overlap_pairs_line_counts": {k: int(v) for k, v in sub.groupby("pair")["SIDM"].nunique().items()},
        }
    return out


def batchie() -> dict:
    path = ROOT / "data/external/batchie_zenodo_13871987/PAIR_SCREEN.csv"
    guard(BCOLS)
    f = pd.read_csv(path, usecols=BCOLS, low_memory=False)
    controls = {"dmso", "low control", "high control", "nan", ""}
    f = f[~f["Drug 1"].astype(str).str.strip().str.lower().isin(controls)
          & ~f["Drug 2"].astype(str).str.strip().str.lower().isin(controls)]   # addendum 1: controls excluded
    d1, d2 = f["Drug 1"].astype(str), f["Drug 2"].astype(str)
    c1, c2 = f["Conc 1 (uM)"].round(6).astype(str), f["Conc 2 (uM)"].round(6).astype(str)
    swap = d1 > d2
    f["pair"] = np.where(swap, d2 + "|" + d1, d1 + "|" + d2)
    f["dose"] = np.where(swap, c2 + "|" + c1, c1 + "|" + c2)
    it = f["Iteration"].astype(str)
    f["phase"] = np.where(it.str.contains("random"), "random_validation",
                          np.where(it.str.contains("validation"), "selected_validation", "adaptive"))
    g = f.groupby(["Cell line", "pair", "phase"]).agg(wells=("Well", "size"), doses=("dose", "nunique"),
                                                      plates=("Plate", "nunique")).reset_index()
    rv = g[g["phase"] == "random_validation"]
    ad = g[g["phase"] == "adaptive"]
    keys_rv = set(zip(rv["Cell line"], rv["pair"]))
    keys_ad = set(zip(ad["Cell line"], ad["pair"]))
    both = keys_rv & keys_ad
    # same dose pair in both phases?
    dd = f.groupby(["Cell line", "pair", "phase"])["dose"].agg(lambda s: set(s)).unstack("phase")
    same_dose = 0
    for k in both:
        row = dd.loc[k]
        if isinstance(row.get("random_validation"), set) and isinstance(row.get("adaptive"), set):
            same_dose += int(bool(row["random_validation"] & row["adaptive"]))
    # history for a joint rate: for each overlapping (line, pair), other lines where the same pair has two phases
    two = {}
    for (line, pair) in both:
        two.setdefault(pair, set()).add(line)
    hist_lines = [len(two[p]) - 1 for (_, p) in both]
    rv_pairs_lines = rv.groupby("pair")["Cell line"].nunique()
    return {
        "source_sha256": sha(path), "columns_parsed": BCOLS,
        "random_validation": {"pair_x_line": int(len(keys_rv)), "pairs": int(rv["pair"].nunique()),
                              "lines": int(rv["Cell line"].nunique()),
                              "lines_list": sorted(rv["Cell line"].unique().tolist()),
                              "wells_per_pair_line_median": float(rv["wells"].median()),
                              "doses_per_pair_line_max": int(rv["doses"].max()),
                              "pairs_measured_in_ge2_lines": int((rv_pairs_lines >= 2).sum())},
        "random_validation_and_adaptive": {"pair_x_line": int(len(both)), "same_dose_pair_in_both": int(same_dose),
                                           "lines": int(len({k[0] for k in both})),
                                           "pairs": int(len({k[1] for k in both})),
                                           "per_line": {l: int(sum(1 for k in both if k[0] == l))
                                                        for l in sorted({k[0] for k in both})},
                                           "other_lines_with_same_pair_in_both_phases_max": int(max(hist_lines, default=0)),
                                           "share_with_any_such_history_line": float(np.mean([h > 0 for h in hist_lines])) if hist_lines else 0.0}}


def addendum() -> int:
    """Addendum 1 (12:5x): the first BATCHIE count treated drug + dmso/control wells as pairs."""
    if OUT_ADDENDUM.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT_ADDENDUM}")
    receipt = {"rule": "DESIGN-ONLY; supersedes the 'batchie' section of design_census.json, which counted wells "
                       "whose Drug 1 or Drug 2 is dmso / low control / high control as pairs",
               "batchie": batchie()}
    with OUT_ADDENDUM.open("x", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=1, sort_keys=True)
    print(json.dumps(receipt["batchie"], indent=1))
    return 0


def main() -> int:
    import sys
    if "--addendum" in sys.argv:
        return addendum()
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    j = jaaks_pairs()
    receipt = {"rule": "DESIGN-ONLY (pandas usecols; guard refuses outcome-like columns); no outcome column parsed",
               "columns_parsed": {"jaaks_original_screen (exposed)": JCOLS, "gdsc_matrix (unopened)": MCOLS,
                                  "batchie PAIR_SCREEN (unopened)": BCOLS},
               "jaaks_lines": int(j["SIDM"].nunique()),
               "matrix_vs_jaaks": matrix_overlap(j), "batchie": batchie()}
    with OUT.open("x", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=1, sort_keys=True)
    print(json.dumps({k: v for k, v in receipt["matrix_vs_jaaks"].items()}, indent=1)[:6000])
    print(json.dumps(receipt["batchie"], indent=1)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
