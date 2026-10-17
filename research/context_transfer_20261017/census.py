"""Metadata-only census of the Beat AML 2.0 confirmation domain (no outcome column is read).

File summary
- Path: research/context_transfer_20261017/census.py
- Purpose: count samples, patients, inhibitors and measured design pairs before the protocol is
  frozen, reading only identifier and design columns of the curve-fit table.
- Core points:
  - Columns read: dbgap_subject_id, dbgap_dnaseq_sample, dbgap_rnaseq_sample, inhibitor, type,
    status, paper_inclusion. AUC, IC50, fit coefficients and curve flags are never parsed.
  - Expression is a pre-treatment feature and its sample identifiers are read from its header.
  - Writes CENSUS.json with the file digests, so the confirmation run can prove it used the same
    bytes.
- Interfaces: `python -B census.py`.
"""
from __future__ import annotations

import pandas as pd

from common import BEATAML, HERE, sha256, write_json

PROBIT = BEATAML / "beataml_probit_curve_fits_v4_dbgap.txt"
EXPR = BEATAML / "beataml_waves1to4_norm_exp_dbgap.txt"
DESIGN_COLUMNS = ["dbgap_subject_id", "dbgap_dnaseq_sample", "dbgap_rnaseq_sample", "inhibitor",
                  "type", "status", "paper_inclusion"]


def main():
    d = pd.read_csv(PROBIT, sep="\t", usecols=DESIGN_COLUMNS, dtype=str)
    header = pd.read_csv(EXPR, sep="\t", nrows=0).columns.tolist()
    out = {
        "read_columns": DESIGN_COLUMNS,
        "rows": len(d),
        "type_counts": d["type"].value_counts().to_dict(),
        "status_counts": d["status"].value_counts().to_dict(),
        "paper_inclusion_counts": d["paper_inclusion"].value_counts().to_dict(),
        "inhibitors": int(d["inhibitor"].nunique()),
        "rnaseq_samples_in_fits": int(d["dbgap_rnaseq_sample"].nunique()),
        "subjects_in_fits": int(d["dbgap_subject_id"].nunique()),
        "expression_header_first": header[:6],
        "expression_columns": len(header),
    }
    inc = d[d["paper_inclusion"].str.upper() == "TRUE"]
    single = inc[~inc["inhibitor"].str.contains(" - ", regex=False)]
    out["included_rows"] = len(inc)
    out["included_single_agent_rows"] = len(single)
    out["included_single_agents"] = int(single["inhibitor"].nunique())
    expr_samples = set(header)
    with_expr = single[single["dbgap_rnaseq_sample"].isin(expr_samples)]
    out["single_agent_rows_with_expression"] = len(with_expr)
    out["samples_with_expression"] = int(with_expr["dbgap_rnaseq_sample"].nunique())
    out["subjects_with_expression"] = int(with_expr["dbgap_subject_id"].nunique())
    per_sample = with_expr.groupby("dbgap_rnaseq_sample")["inhibitor"].nunique()
    out["drugs_per_sample"] = {"min": int(per_sample.min()), "median": float(per_sample.median()),
                               "max": int(per_sample.max())}
    per_drug = with_expr.groupby("inhibitor")["dbgap_rnaseq_sample"].nunique()
    out["samples_per_drug"] = {"min": int(per_drug.min()), "median": float(per_drug.median()),
                               "max": int(per_drug.max()), "drugs_with_ge_100": int((per_drug >= 100).sum())}
    dup = with_expr.groupby(["dbgap_rnaseq_sample", "inhibitor"]).size()
    out["duplicate_sample_drug_rows"] = int((dup > 1).sum())
    out["sha256"] = {p.name: sha256(p) for p in sorted(BEATAML.iterdir()) if p.is_file()}
    write_json(HERE / "CENSUS.json", out)
    for k, v in out.items():
        if k != "sha256":
            print(k, v)


if __name__ == "__main__":
    main()
