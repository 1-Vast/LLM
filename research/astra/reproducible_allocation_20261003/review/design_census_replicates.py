"""Review A2 addendum: DESIGN-ONLY detail of complete drug-set replicates in the GDSC matrix releases.

File summary
- Path: research/astra/reproducible_allocation_20261003/review/design_census_replicates.py
- Purpose: design_census.json showed that only a few lines per matrix release have every pair on
  >= 2 plates. This addendum lists, per release and over releases, which lines those are, their
  tissues, menu sizes, whether the repeated plates are adjacent barcodes (a hint of a same-batch
  technical duplicate; barcodes are plate ids, not dates) and how many plates each line has.
- Core points: the same restricted `usecols` as design_census.py; no outcome column parsed.
- Interfaces: `python -m research.astra.reproducible_allocation_20261003.review.design_census_replicates`;
  writes review/design_census_replicates.json (refuses to overwrite).
- Depends on: pandas, numpy; design_census.MCOLS, MATRIX, DATA, guard.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .design_census import DATA, MATRIX, MCOLS, guard

HERE = Path(__file__).resolve().parent
OUT = HERE / "design_census_replicates.json"
REFERENCE_LINES = {"HT-29", "PC-14", "MHH-ES-1", "A375", "SW620", "C32", "U-2-OS"}


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    guard(MCOLS)
    res = {"rule": "DESIGN-ONLY (usecols restricted; no outcome column parsed)", "releases": {}}
    union = {}
    for name in MATRIX:
        f = pd.read_csv(DATA / f"{name}_matrix_results.csv.gz", usecols=MCOLS, low_memory=False)
        a, b = f["lib1_ID"].astype(str), f["lib2_ID"].astype(str)
        f["pair"] = np.where(a < b, a + "|" + b, b + "|" + a)
        per = f.groupby(["SIDM", "pair"])["BARCODE"].nunique().reset_index(name="plates")
        line = per.groupby("SIDM").agg(pairs=("pair", "size"), rep=("plates", lambda s: int((s >= 2).sum())),
                                       min_plates=("plates", "min"), max_plates=("plates", "max"))
        full = line[line["rep"] == line["pairs"]].copy()
        meta = f.groupby("SIDM").agg(name=("CELL_LINE_NAME", "first"), tissue=("TISSUE", "first"))
        full = full.join(meta)
        # barcode adjacency for the replicated drug sets of the full-replicate lines
        sub = f[f["SIDM"].isin(full.index)][["SIDM", "DRUGSET_ID", "BARCODE"]].drop_duplicates()
        gaps = []
        for (_, _), g in sub.groupby(["SIDM", "DRUGSET_ID"]):
            bc = np.sort(g["BARCODE"].to_numpy())
            if bc.size >= 2:
                gaps.extend(np.diff(bc).tolist())
        gaps = np.array(gaps)
        res["releases"][name] = {
            "full_replicate_lines": int(len(full)),
            "of_which_reference_qc_lines": int(full["name"].isin(REFERENCE_LINES).sum()),
            "tissues": {str(k): int(v) for k, v in full["tissue"].value_counts().items()},
            "menu_pairs_median": float(full["pairs"].median()) if len(full) else None,
            "plates_per_pair_min_median": float(full["min_plates"].median()) if len(full) else None,
            "consecutive_barcode_gap_share_eq1": float((gaps == 1).mean()) if gaps.size else None,
            "consecutive_barcode_gap_share_le5": float((gaps <= 5).mean()) if gaps.size else None,
            "consecutive_barcode_gap_median": float(np.median(gaps)) if gaps.size else None,
            "lines": {str(k): {"name": str(r["name"]), "tissue": str(r["tissue"]), "pairs": int(r["pairs"]),
                               "min_plates": int(r["min_plates"]), "max_plates": int(r["max_plates"])}
                      for k, r in full.iterrows()}}
        for k, r in full.iterrows():
            union.setdefault(str(k), {"name": str(r["name"]), "tissue": str(r["tissue"]), "pairs": 0, "releases": []})
            union[str(k)]["pairs"] += int(r["pairs"])
            union[str(k)]["releases"].append(name)
    non_ref = {k: v for k, v in union.items() if v["name"] not in REFERENCE_LINES}
    tissues = pd.Series([v["tissue"] for v in non_ref.values()]).value_counts()
    res["union"] = {"distinct_full_replicate_lines": len(union),
                    "excluding_reference_qc_lines": len(non_ref),
                    "non_reference_tissues": {str(k): int(v) for k, v in tissues.items()},
                    "non_reference_menu_pairs_median": float(np.median([v["pairs"] for v in non_ref.values()])) if non_ref else None,
                    "non_reference_lines_in_2plus_releases": int(sum(len(v["releases"]) >= 2 for v in non_ref.values()))}
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    slim = {k: {kk: vv for kk, vv in v.items() if kk != "lines"} for k, v in res["releases"].items()}
    print(json.dumps({"releases": slim, "union": res["union"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
