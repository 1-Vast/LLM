"""Review A2/A4: DESIGN-ONLY census of the BATCHIE prospective pair screen (Tosh et al. 2025).

File summary
- Path: research/astra/reproducible_allocation_20261003/review/design_census_batchie.py
- Purpose: decide whether the BATCHIE prospective release (Zenodo 10.5281/zenodo.13871987,
  PAIR_SCREEN.csv, downloaded by this workstream) can support a full-menu replay of alternative
  screening/verification policies, using design columns only.
- Core points:
  - pandas `usecols` = Well, Cell line, Drug 1, Drug 2, Conc 1 (uM), Conc 2 (uM), Iteration, file,
    Plate. Raw count, Viability and Failed QC are never parsed.
  - Reports drugs, lines, pairs, iterations, the fraction of the pair x line space measured, and
    whether a pair x line is measured on >= 2 plates or in >= 2 iterations (potential verification).
- Interfaces: `python -m research.astra.reproducible_allocation_20261003.review.design_census_batchie`;
  writes review/design_census_batchie.json (refuses to overwrite).
- Depends on: pandas, numpy.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SRC = ROOT / "data/external/batchie_zenodo_13871987/PAIR_SCREEN.csv"
OUT = HERE / "design_census_batchie.json"
COLS = ["Well", "Cell line", "Drug 1", "Drug 2", "Conc 1 (uM)", "Conc 2 (uM)", "Iteration", "file", "Plate"]


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"REFUSE_OVERWRITE: {OUT}")
    with open(SRC, encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split(",")
    f = pd.read_csv(SRC, usecols=COLS, low_memory=False)
    d1 = f["Drug 1"].astype(str).str.strip()
    d2 = f["Drug 2"].astype(str).str.strip()
    empty = {"", "nan", "None", "DMSO", "dmso", "control", "Control"}
    combo = ~d1.isin(empty) & ~d2.isin(empty)
    c = f[combo].copy()
    a, b = d1[combo], d2[combo]
    c["pair"] = np.where(a < b, a + "|" + b, b + "|" + a)
    drugs = sorted(set(d1[~d1.isin(empty)]) | set(d2[~d2.isin(empty)]))
    lines = sorted(f["Cell line"].astype(str).unique())
    per = c.groupby(["pair", "Cell line"]).agg(plates=("Plate", "nunique"), iterations=("Iteration", "nunique"),
                                               wells=("Well", "size"),
                                               dose_cells=("Conc 1 (uM)", "nunique")).reset_index()
    n_pairs_possible = len(drugs) * (len(drugs) - 1) // 2
    it = c.groupby("Iteration").agg(plates=("Plate", "nunique"), pair_lines=("pair", "size"))
    out = {
        "rule": "DESIGN-ONLY: usecols restricted; Raw count, Viability and Failed QC never parsed",
        "source": {"path": str(SRC.relative_to(ROOT)).replace("\\", "/"), "bytes": SRC.stat().st_size,
                   "sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(), "header": header, "columns_parsed": COLS},
        "rows": int(len(f)), "combination_rows": int(combo.sum()),
        "drugs": len(drugs), "cell_lines": len(lines), "plates": int(f["Plate"].nunique()),
        "iterations": {str(k): {"plates": int(v["plates"]), "combination_wells": int(v["pair_lines"])} for k, v in it.iterrows()},
        "pairs_measured": int(c["pair"].nunique()), "pairs_possible": n_pairs_possible,
        "pair_x_line_measured": int(len(per)), "pair_x_line_possible": n_pairs_possible * len(lines),
        "share_of_pair_x_line_space_measured": round(len(per) / max(n_pairs_possible * len(lines), 1), 4),
        "pair_x_line_on_2plus_plates": int((per["plates"] >= 2).sum()),
        "pair_x_line_in_2plus_iterations": int((per["iterations"] >= 2).sum()),
        "wells_per_pair_x_line_median": float(per["wells"].median()),
        "lines_per_pair_median": float(per.groupby("pair")["Cell line"].nunique().median()),
        "pairs_per_line_median": float(per.groupby("Cell line")["pair"].nunique().median()),
        "pairs_measured_in_every_line": int((per.groupby("pair")["Cell line"].nunique() == len(lines)).sum()),
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    slim = dict(out)
    slim["source"] = {k: v for k, v in out["source"].items() if k != "header"}
    print(json.dumps(slim, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
