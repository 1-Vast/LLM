"""Targeted, non-inferential CDI pilot census for one predeclared target.

The target is FLT3 because it is explicitly used as the wet-lab example in
AdaMBind (the seed paper supplied by the user).  This script only counts
structure-mapped compounds, exact Kd rows, and shared PRISM response contexts;
it does not fit a model or claim FLT3 mediation.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"D:/MAESTRO")
EP = ROOT / "research/2026-10-30-cdi-r3"
TARGET = "CHEMBL1974"  # receptor-type tyrosine-protein kinase FLT3


def main() -> None:
    ids = pd.read_csv(EP / "prism_structure_identity_candidates.csv", low_memory=False)
    ids = ids[ids["mapping_status"].eq("exact_structure")].copy()
    ids["chembl_id"] = ids["exact_chembl_ids"].str.split(";").str[0]
    chembl_to_broad = {}
    for row in ids.itertuples(index=False):
        chembl_to_broad.setdefault(row.chembl_id, []).append(row.broad_id)

    kd = pd.read_csv(ROOT / "data/external/klaeger2017_chembl/klaeger2017_CHEMBL3991601_kd.csv", low_memory=False)
    kd = kd[kd["target_chembl_id"].eq(TARGET) & kd["molecule_chembl_id"].isin(chembl_to_broad)].copy()
    exact = kd[kd["standard_relation"].eq("=")].copy()
    mols = sorted(set(exact["molecule_chembl_id"]))

    # Read only treatment columns belonging to the target's structure-mapped compounds.
    tr = pd.read_csv(
        ROOT / "data/external/prism_19q4/raw/secondary-screen-replicate-treatment-info.csv",
        usecols=["column_name", "broad_id", "screen_id", "perturbation_type", "dose", "name", "target"],
        low_memory=False,
    )
    target_broads = sorted({b for m in mols for b in chembl_to_broad.get(m, [])})
    tr = tr[tr["broad_id"].isin(target_broads) & tr["perturbation_type"].eq("experimental_treatment")].copy()
    header = pd.read_csv(ROOT / "data/external/prism_19q4/raw/secondary-screen-logfold-change.csv", nrows=0).columns
    cols = [c for c in tr["column_name"] if c in set(header)]
    tr = tr[tr["column_name"].isin(cols)]
    resp = pd.read_csv(
        ROOT / "data/external/prism_19q4/raw/secondary-screen-logfold-change.csv",
        usecols=[header[0], *cols],
        index_col=0,
        dtype={c: np.float32 for c in cols},
        low_memory=False,
    )
    cell_sets = {}
    for (broad, screen), sub in tr.groupby(["broad_id", "screen_id"]):
        present = resp[list(sub["column_name"])].notna().any(axis=1)
        cell_sets[(broad, screen)] = set(resp.index[present].astype(str))

    rows = []
    for a, b in combinations(mols, 2):
        sa = exact[exact["molecule_chembl_id"].eq(a)]
        sb = exact[exact["molecule_chembl_id"].eq(b)]
        pair = {
            "target_chembl_id": TARGET,
            "target_pref_name": str(kd["target_pref_name"].iloc[0]),
            "chembl_a": a,
            "chembl_b": b,
            "a_kd_min_nM": float(sa["standard_value"].min()),
            "b_kd_min_nM": float(sb["standard_value"].min()),
            "delta_pKd_approx": float(np.log10(sb["standard_value"].min()) - np.log10(sa["standard_value"].min())),
            "a_broad_ids": ";".join(sorted(chembl_to_broad.get(a, []))),
            "b_broad_ids": ";".join(sorted(chembl_to_broad.get(b, []))),
        }
        contexts = []
        for ba in chembl_to_broad.get(a, []):
            for bb in chembl_to_broad.get(b, []):
                screens_a = {s for (x, s) in cell_sets if x == ba}
                screens_b = {s for (x, s) in cell_sets if x == bb}
                for screen in sorted(screens_a & screens_b):
                    shared = cell_sets[(ba, screen)] & cell_sets[(bb, screen)]
                    contexts.append({"screen_id": screen, "broad_a": ba, "broad_b": bb, "shared_cells": len(shared)})
        pair["n_same_screen_context_blocks"] = len(contexts)
        pair["max_shared_cells_in_block"] = max((x["shared_cells"] for x in contexts), default=0)
        pair["contexts_ge3_cells"] = sum(x["shared_cells"] >= 3 for x in contexts)
        pair["contexts_ge10_cells"] = sum(x["shared_cells"] >= 10 for x in contexts)
        rows.append(pair)

    out = pd.DataFrame(rows)
    out.to_csv(EP / "flt3_exact_pair_contexts.csv", index=False)
    summary = {
        "target_chembl_id": TARGET,
        "target_pref_name": str(kd["target_pref_name"].iloc[0]) if len(kd) else None,
        "kd_rows_for_exact_structure_mapped_molecules": int(len(kd)),
        "mapped_molecules_with_exact_kd": int(len(mols)),
        "mapped_molecules_with_secondary_prism_treatment": int(len(set(tr["broad_id"]) & set(target_broads))),
        "secondary_treatment_columns_used": int(len(cols)),
        "secondary_response_cells": int(resp.shape[0]),
        "response_matrix_columns_read": int(resp.shape[1]),
        "pair_rows": int(len(out)),
        "pair_rows_with_ge3_shared_cells": int((out["contexts_ge3_cells"] > 0).sum()) if len(out) else 0,
        "pair_rows_with_ge10_shared_cells": int((out["contexts_ge10_cells"] > 0).sum()) if len(out) else 0,
        "pair_rows_with_ge3_shared_cells_and_nonzero_delta_pKd": int(((out["contexts_ge3_cells"] > 0) & (out["delta_pKd_approx"].abs() > 0)).sum()) if len(out) else 0,
        "scientific_boundary": "This is a retrospective feasibility census. Kd is lysate/kinobead apparent binding, delta_pKd is a descriptive within-assay transform, and PRISM viability columns lack exposure time and cellular engagement; no causal target or Agent claim is made.",
    }
    (EP / "flt3_pilot_census.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if len(out):
        print(out.sort_values(["contexts_ge3_cells", "max_shared_cells_in_block"], ascending=False).head(12).to_string(index=False))


if __name__ == "__main__":
    main()
