"""Static CDI feasibility census after exact structure mapping.

The output is a data gate, not a biological result.  It counts same-assay
Kd pair candidates and the number of PRISM secondary-screen cell contexts
where both compounds have a non-missing viability entry.  No response model
or causal interpretation is fitted here.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"D:/MAESTRO")
EP = ROOT / "research/2026-10-30-cdi-r3"
DATA = ROOT / "data/external"


def main() -> None:
    ids = pd.read_csv(EP / "prism_structure_identity_candidates.csv", low_memory=False)
    ids = ids[ids["mapping_status"] == "exact_structure"].copy()
    ids["chembl_id"] = ids["exact_chembl_ids"].str.split(";").str[0]
    broad_to_chembl = dict(zip(ids["broad_id"], ids["chembl_id"]))

    kd = pd.read_csv(
        DATA / "klaeger2017_chembl/klaeger2017_CHEMBL3991601_kd.csv",
        low_memory=False,
    )
    kd = kd[kd["molecule_chembl_id"].isin(set(broad_to_chembl.values()))].copy()
    # Only same ChEMBL assay + same target is counted as a comparable affinity block.
    block = (
        kd.groupby(["target_chembl_id", "target_pref_name", "assay_chembl_id"], dropna=False)
        .agg(
            mapped_molecules=("molecule_chembl_id", "nunique"),
            exact_molecules=(
                "molecule_chembl_id",
                lambda s: s[kd.loc[s.index, "standard_relation"].eq("=")].nunique(),
            ),
            rows=("activity_id", "size"),
        )
        .reset_index()
    )
    block = block[block["mapped_molecules"] >= 2].copy()
    block["pair_count"] = block["mapped_molecules"] * (block["mapped_molecules"] - 1) // 2
    block["exact_pair_count"] = block["exact_molecules"] * (block["exact_molecules"] - 1) // 2

    # Retain molecule identities per target-assay for explicit pair rows.
    pairs = []
    for (target, target_name, assay), sub in kd.groupby(
        ["target_chembl_id", "target_pref_name", "assay_chembl_id"], dropna=False
    ):
        mids = sorted(set(sub["molecule_chembl_id"]))
        if len(mids) < 2:
            continue
        for a, b in combinations(mids, 2):
            sa = sub[sub["molecule_chembl_id"] == a]
            sb = sub[sub["molecule_chembl_id"] == b]
            pairs.append(
                {
                    "target_chembl_id": target,
                    "target_pref_name": target_name,
                    "assay_chembl_id": assay,
                    "chembl_a": a,
                    "chembl_b": b,
                    "a_exact_kd": bool((sa["standard_relation"] == "=").any()),
                    "b_exact_kd": bool((sb["standard_relation"] == "=").any()),
                    "a_kd_min_nM": float(sa.loc[sa["standard_relation"] == "=", "standard_value"].min())
                    if (sa["standard_relation"] == "=").any()
                    else None,
                    "b_kd_min_nM": float(sb.loc[sb["standard_relation"] == "=", "standard_value"].min())
                    if (sb["standard_relation"] == "=").any()
                    else None,
                }
            )

    # PRISM secondary treatment identity and wide response matrix.
    tr = pd.read_csv(
        DATA / "prism_19q4/raw/secondary-screen-replicate-treatment-info.csv",
        usecols=["column_name", "broad_id", "screen_id", "perturbation_type"],
        low_memory=False,
    )
    tr = tr[tr["broad_id"].isin(set(broad_to_chembl))]
    tr = tr[tr["perturbation_type"].eq("experimental_treatment")]
    response = pd.read_csv(
        DATA / "prism_19q4/raw/secondary-screen-logfold-change.csv",
        index_col=0,
        dtype=np.float32,
        low_memory=False,
    )
    tr = tr[tr["column_name"].isin(response.columns)].copy()
    cell_sets: dict[tuple[str, str], set[str]] = {}
    for (broad, screen), sub in tr.groupby(["broad_id", "screen_id"]):
        cols = list(sub["column_name"])
        present = response[cols].notna().any(axis=1)
        cell_sets[(broad, screen)] = set(response.index[present].astype(str))

    # Convert each affinity pair to available broad IDs, then summarize shared contexts.
    chembl_to_broad: dict[str, list[str]] = {}
    for broad, chembl in broad_to_chembl.items():
        chembl_to_broad.setdefault(chembl, []).append(broad)
    pair_rows = []
    for row in pairs:
        ba = chembl_to_broad.get(row["chembl_a"], [])
        bb = chembl_to_broad.get(row["chembl_b"], [])
        contexts = []
        for broad_a in ba:
            for broad_b in bb:
                for screen in sorted({s for (b, s) in cell_sets if b == broad_a} & {s for (b, s) in cell_sets if b == broad_b}):
                    shared = cell_sets[(broad_a, screen)] & cell_sets[(broad_b, screen)]
                    if shared:
                        contexts.append({"broad_a": broad_a, "broad_b": broad_b, "screen_id": screen, "shared_cells": len(shared)})
        row = dict(row)
        row["n_same_screen_context_blocks"] = len(contexts)
        row["max_shared_cells_in_block"] = max([x["shared_cells"] for x in contexts], default=0)
        row["contexts_ge3_cells"] = sum(x["shared_cells"] >= 3 for x in contexts)
        row["contexts_ge10_cells"] = sum(x["shared_cells"] >= 10 for x in contexts)
        pair_rows.append(row)

    pair_df = pd.DataFrame(pair_rows)
    pair_df.to_csv(EP / "same_target_assay_pairs.csv", index=False)
    summary = {
        "mapped_exact_broad_ids": len(broad_to_chembl),
        "mapped_exact_chembl_ids": len(set(broad_to_chembl.values())),
        "same_target_assay_blocks_ge2_molecules": int(len(block)),
        "same_target_assay_pair_rows": int(len(pair_df)),
        "same_target_assay_pairs_both_exact_kd": int((pair_df["a_exact_kd"] & pair_df["b_exact_kd"]).sum()) if len(pair_df) else 0,
        "pair_rows_with_any_shared_prism_secondary_block": int((pair_df["n_same_screen_context_blocks"] > 0).sum()) if len(pair_df) else 0,
        "pair_rows_with_block_ge3_cells": int((pair_df["contexts_ge3_cells"] > 0).sum()) if len(pair_df) else 0,
        "pair_rows_with_block_ge10_cells": int((pair_df["contexts_ge10_cells"] > 0).sum()) if len(pair_df) else 0,
        "response_matrix_rows": int(response.shape[0]),
        "response_matrix_columns": int(response.shape[1]),
        "treatment_columns_used": int(len(tr)),
        "scientific_boundary": "This is a retrospective metadata/response-availability census. It does not establish same exposure time, target engagement, independent biological replication, causal mediation, or prospective Agent benefit.",
    }
    (EP / "pair_census.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if len(pair_df):
        print(pair_df.sort_values(["contexts_ge3_cells", "max_shared_cells_in_block"], ascending=False).head(10).to_string(index=False))


if __name__ == "__main__":
    main()
