"""WS1 step 3g: DESIGN-ONLY census of Jaaks et al. 2022 fitted original and validation screens (figshare).

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws1_feedback_validation/jaaks_design_census.py
- Purpose: establish, without reading any outcome column, whether the original anchored screen is
  a complete panel that a policy can be replayed on, which independent re-measurements exist
  (separate plates; reversed anchor/library orientation; the authors' validation rescreen), how
  the validation subset was composed, and how much of it overlaps the original panel.
- Core points: reads only the header and DESIGN columns (identifiers, concentrations, plate
  barcode); the columns read are written to the receipt so the release can be frozen and opened once.
- Interfaces: run the file with PYTHONPATH="src;.".
- Depends on: pandas, numpy.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DATA = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare"
FILES = {"original": "original_screen_all_tissues_fitted.csv", "validation": "validation_screen_all_tissues_fitted.csv"}
DESIGN = ["BARCODE", "COMBI_ID", "Tissue", "CELL_LINE_NAME", "SIDM", "ANCHOR_ID", "ANCHOR_NAME", "ANCHOR_CONC",
          "LIBRARY_ID", "LIBRARY_NAME", "LIBRARY_CONC"]


def load(name: str) -> pd.DataFrame:
    f = pd.read_csv(DATA / FILES[name], usecols=DESIGN, low_memory=False)
    a, b = f["ANCHOR_ID"].astype(str), f["LIBRARY_ID"].astype(str)   # some IDs are composite, e.g. '1032|1372'
    f["pair"] = np.where(a < b, a + "~" + b, b + "~" + a)
    f["ordered"] = a + ">" + b
    return f


def describe(f: pd.DataFrame) -> dict:
    out = {"rows": int(len(f)), "plates": int(f["BARCODE"].nunique()), "tissues": {}}
    for tissue, g in f.groupby("Tissue"):
        lines, pairs = g["SIDM"].nunique(), g["pair"].nunique()
        per = g.groupby(["pair", "SIDM"]).agg(plates=("BARCODE", "nunique"), orientations=("ordered", "nunique"))
        orient = g.groupby("pair")["ordered"].nunique()
        out["tissues"][str(tissue)] = {
            "cell_lines": int(lines), "drugs": int(len(set(g["ANCHOR_ID"]) | set(g["LIBRARY_ID"]))),
            "unordered_pairs": int(pairs), "ordered_combinations": int(g["ordered"].nunique()),
            "pairs_in_both_orientations": int((orient == 2).sum()),
            "pair_x_line_measured": int(len(per)), "completeness": round(len(per) / (lines * pairs), 4),
            "pair_x_line_with_2plus_plates": int((per["plates"] >= 2).sum()),
            "pair_x_line_with_both_orientations": int((per["orientations"] == 2).sum()),
            "anchor_concs_per_ordered_combo_line_median": float(g.groupby(["ordered", "SIDM"])["ANCHOR_CONC"].nunique().median()),
        }
    return out


def main() -> int:
    orig, val = load("original"), load("validation")
    receipt = {"rule": "design-only; no viability, Emax, IC50, AUC, synergy, day-1 or growth column read",
               "columns_read": DESIGN, "original": describe(orig), "validation": describe(val), "overlap": {}}
    for tissue in sorted(set(val["Tissue"])):
        vo, oo = val[val["Tissue"] == tissue], orig[orig["Tissue"] == tissue]
        vt, ot = set(zip(vo["pair"], vo["SIDM"])), set(zip(oo["pair"], oo["SIDM"]))
        vord, oord = set(zip(vo["ordered"], vo["SIDM"])), set(zip(oo["ordered"], oo["SIDM"]))
        receipt["overlap"][str(tissue)] = {
            "validation_pair_x_line": len(vt), "in_original": len(vt & ot),
            "validation_ordered_x_line_in_original": len(vord & oord),
            "validation_lines": int(vo["SIDM"].nunique()), "validation_lines_in_original": len(set(vo["SIDM"]) & set(oo["SIDM"])),
            "validation_pairs": int(vo["pair"].nunique()), "validation_pairs_in_original": len(set(vo["pair"]) & set(oo["pair"])),
            "original_lines": int(oo["SIDM"].nunique()), "original_pairs": int(oo["pair"].nunique()),
            "validation_plates_shared_with_original": len(set(vo["BARCODE"]) & set(oo["BARCODE"])),
            "validation_completeness_pairs_x_lines": round(len(vt) / max(vo["pair"].nunique() * vo["SIDM"].nunique(), 1), 4),
            "same_conc_design_share": round(float(np.mean([
                (r.ANCHOR_CONC, r.LIBRARY_CONC) in set(zip(oo.loc[oo["ordered"] == r.ordered, "ANCHOR_CONC"],
                                                           oo.loc[oo["ordered"] == r.ordered, "LIBRARY_CONC"]))
                for r in vo.drop_duplicates(["ordered", "ANCHOR_CONC"]).itertuples()])), 3),
        }
    out = HERE / "receipts" / "step3g_jaaks_design_census.json"
    out.write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    print(json.dumps(receipt, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
