"""Metadata-only qualification of a PRISM 19Q4 / LINCS L1000 (GSE92742) intersection.

File summary
- Path: research/observable_state_20261018/qualify_l1000.py
- Reads ONLY metadata tables (PRISM primary-screen treatment and cell-line info; L1000 pert_info, cell_info, sig_info).
  No log-fold-change matrix and no L1000 expression matrix is opened. Writes QUALIFICATION_L1000.json.
- Questions: do drug identity, cell identity, dose and time overlap enough to ask whether a molecular readout can replace
  later functional assays, and what would still differ (endpoint, dose, time, provenance).
- Matching keys are deliberately simple and recorded: compound = first 13 characters of the Broad id (BRD-Kxxxxxxxx);
  cell = L1000 cell_id against the PRISM ccle_name stem (text before the first underscore), uppercased, punctuation removed.
  A structure-based (InChIKey) match is NOT attempted here; salt/batch identity is therefore unverified.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
EXT = HERE.parents[1] / "data" / "external"


def norm(s):
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


def main() -> dict:
    tr = pd.read_csv(EXT / "prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv", usecols=["broad_id", "dose", "name", "moa"])
    cl = pd.read_csv(EXT / "prism_19q4/raw/primary-screen-cell-line-info.csv", usecols=["ccle_name", "primary_tissue"])
    L = EXT / "lincs_l1000_gse92742"
    pert = pd.read_csv(L / "GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", usecols=["pert_id", "pert_iname", "pert_type", "inchi_key"])
    sig = pd.read_csv(L / "GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", usecols=["pert_id", "pert_type", "cell_id", "pert_dose", "pert_dose_unit", "pert_time", "pert_time_unit"])
    sig = sig[sig.pert_type == "trt_cp"]
    tr["cmp"] = tr.broad_id.astype(str).str[:13]
    prism_c = set(tr.cmp.dropna())
    l1_c = set(sig.pert_id.astype(str))
    both_c = prism_c & l1_c
    prism_cells = {norm(x.split("_")[0]): x for x in cl.ccle_name.dropna()}
    l1_cells = {norm(c) for c in sig.cell_id.unique()}
    both_cells = sorted(set(prism_cells) & l1_cells)
    s = sig[sig.pert_id.isin(both_c) & sig.cell_id.map(norm).isin(both_cells)]
    pairs = s.drop_duplicates(["pert_id", "cell_id"])
    per_cell = pairs.groupby(pairs.cell_id.map(norm)).size().sort_values(ascending=False)
    doses = tr.dose.round(2).value_counts().head(5)
    out = {
        "scope": "metadata only; no outcome matrix opened; key = BRD-K 13-char compound id and normalised cell name; structure/salt identity unverified",
        "prism_compounds": len(prism_c), "l1000_trt_cp_compounds": len(l1_c), "compound_overlap": len(both_c),
        "prism_lines": len(prism_cells), "l1000_cell_ids": len(l1_cells), "cell_overlap": len(both_cells),
        "compound_cell_pairs_in_l1000_for_overlap": int(len(pairs)),
        "overlap_lines_with_>=100_overlap_compounds": int((per_cell >= 100).sum()),
        "overlap_lines_with_>=1000_overlap_compounds": int((per_cell >= 1000).sum()),
        "top_overlap_lines": {k: int(v) for k, v in per_cell.head(12).items()},
        "prism_primary_doses_um_top": {str(k): int(v) for k, v in doses.items()},
        "l1000_dose_top": {f"{k[0]} {k[1]}": int(v) for k, v in s.groupby(["pert_dose", "pert_dose_unit"]).size().sort_values(ascending=False).head(5).items()},
        "l1000_time_top": {f"{k[0]} {k[1]}": int(v) for k, v in s.groupby(["pert_time", "pert_time_unit"]).size().sort_values(ascending=False).head(4).items()},
        "mismatches_that_remain": ["endpoint: 5-day pooled viability log-fold change versus 6/24 h transcription (landmark z-scores)",
                                   "dose: PRISM primary ~2.5 uM versus L1000 mostly 10 uM and other doses",
                                   "time: 5 d versus 6/24 h", "provenance: different centres/batches; identity by 13-char Broad id only"],
        "prior_exposure": "earlier blocks (N, P, Q) already used PRISM/L1000 intersections and sealed GSE70138; any new L1000 use is development, not confirmation",
        "decision_rule": "if the overlap lacks >=3 lines with >=1000 matched compounds (the >=100 count is inflated by ~156-compound lines) or the dose/time mismatch cannot be modelled as a declared covariate, run PRISM-only campaigns; the assay-escalation question is then answered only as a structural option (not a result)",
    }
    (HERE / "QUALIFICATION_L1000.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
