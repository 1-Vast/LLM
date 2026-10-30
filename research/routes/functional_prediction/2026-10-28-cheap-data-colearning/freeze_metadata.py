"""Freeze a metadata-only 19Q4 development cohort. No numeric responses."""
from pathlib import Path
import hashlib
import json
import re
import pandas as pd
from rdkit import Chem, RDLogger

HERE = Path(__file__).resolve().parent
RAW = Path(r"D:\MAESTRO\data\external\prism_19q4\raw")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    target = HERE / "metadata_freeze.json"
    assert not target.exists(), "Metadata freeze exists; do not replace it"
    RDLogger.DisableLog("rdApp.*")
    treatment = pd.read_csv(RAW / "primary-screen-replicate-collapsed-treatment-info.csv")
    cells = pd.read_csv(RAW / "primary-screen-cell-line-info.csv")
    treatment = treatment[(treatment.screen_id == "HTS") & (treatment.dose == 2.5)].copy()
    records = []
    for row in treatment.itertuples(index=False):
        mol = Chem.MolFromSmiles(str(row.smiles))
        if mol is None:
            continue
        fragments = Chem.GetMolFrags(mol, asMols=True)
        parent = sorted(fragments, key=lambda m: (-m.GetNumHeavyAtoms(), Chem.MolToSmiles(m)))[0]
        key = Chem.MolToInchiKey(parent).split("-")[0]
        if not key:
            continue
        records.append({"column_name": row.column_name, "broad_id": row.broad_id,
                        "name": row.name, "dose_uM": float(row.dose), "screen_id": row.screen_id,
                        "connectivity": key, "core": str(row.broad_id)[:13],
                        "normalized_name": re.sub(r"[^a-z0-9]", "", str(row.name).lower())})
    records.sort(key=lambda r: r["column_name"])
    parent = list(range(len(records)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    seen = {}
    for i, row in enumerate(records):
        for field in ("connectivity", "core", "normalized_name"):
            key = (field, row[field])
            if not key[1] or key[1] == "nan":
                continue
            if key in seen:
                a, b = find(i), find(seen[key])
                parent[max(a, b)] = min(a, b)
            else:
                seen[key] = i
    groups = {}
    for i, row in enumerate(records):
        groups.setdefault(find(i), []).append(row)
    conditions = []
    for members in groups.values():
        keep = dict(members[0])
        keep["group_id"] = min(m["connectivity"] for m in members)
        keep["aliases"] = [m["column_name"] for m in members]
        conditions.append(keep)
    conditions.sort(key=lambda r: r["group_id"])
    cells = cells[(cells.passed_str_profiling == True) & cells.depmap_id.astype(str).str.fullmatch(r"ACH-\d+")]
    cells = cells.sort_values("row_name").drop_duplicates("depmap_id")
    cell_records = cells[["row_name", "depmap_id", "ccle_name"]].to_dict("records")
    cell_records.sort(key=lambda r: hashlib.sha256(("C2-cell|" + r["depmap_id"]).encode()).hexdigest())
    ntrain = int(0.7 * len(cell_records))
    for i, row in enumerate(cell_records):
        row["role"] = "train" if i < ntrain else "model_unseen_development"
    result = {"protocol": "protocol_v1.md", "protocol_sha256": digest(HERE / "protocol_v1.md"),
              "input_sha256": {name: digest(RAW / name) for name in (
                  "primary-screen-replicate-collapsed-treatment-info.csv", "primary-screen-cell-line-info.csv", "primary-screen-readme.txt")},
              "source_exposure": "historically exposed internal development; never fresh confirmation",
              "numeric_responses_read": 0, "matching_HTS_2_5_columns": len(treatment),
              "parsable_columns": len(records), "unique_groups": len(conditions),
              "ntrain": ntrain, "ntest": len(cell_records) - ntrain,
              "conditions": conditions, "cells": cell_records}
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("numeric_responses_read", "matching_HTS_2_5_columns", "parsable_columns", "unique_groups", "ntrain", "ntest")}))

if __name__ == "__main__":
    main()
