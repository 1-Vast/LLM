"""Freeze common-resource identities and roles, without consuming response columns."""
from collections import Counter, defaultdict
from pathlib import Path
import csv
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
SOURCE = Path(r"D:\MAESTRO\tmp\extq1\GDSC2_fitted_dose_response.csv")
assert not (HERE / "metadata_freeze.json").exists(), "No replacement of frozen metadata"
cells, records = {}, []
with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
    for index, full_row in enumerate(csv.DictReader(handle)):
        # Deliberately never select LN_IC50, AUC, RMSE or Z_SCORE.
        row = {key: full_row[key] for key in ("DATASET", "SANGER_MODEL_ID", "COSMIC_ID", "CELL_LINE_NAME",
                "TCGA_DESC", "DRUG_ID", "DRUG_NAME", "MIN_CONC", "MAX_CONC", "WEBRELEASE", "NLME_RESULT_ID")}
        if row["DATASET"] != "GDSC2" or not re.fullmatch(r"SIDM\d+", row["SANGER_MODEL_ID"]):
            continue
        cell_id = row["SANGER_MODEL_ID"]
        cells.setdefault(cell_id, {"id": cell_id, "name": row["CELL_LINE_NAME"], "tissue": row["TCGA_DESC"]})
        row["source_row_index"] = index
        row["name_key"] = re.sub(r"[^a-z0-9]", "", row["DRUG_NAME"].lower())
        records.append(row)
cell_list = sorted(cells.values(), key=lambda r: hashlib.sha256(("C4-cell|" + r["id"]).encode()).hexdigest())
ntrain = int(.7 * len(cell_list))
train_ids = {r["id"] for r in cell_list[:ntrain]}
for i, row in enumerate(cell_list):
    row["role"] = "train" if i < ntrain else "model_unseen_exposed_development"
groups = defaultdict(list)
for row in records:
    if row["name_key"]:
        groups[row["name_key"]].append(row)
conditions = []
for name, rows in groups.items():
    counts = Counter((r["DRUG_ID"], r["MIN_CONC"], r["MAX_CONC"]) for r in rows if r["SANGER_MODEL_ID"] in train_ids)
    if not counts:
        continue
    drug, low, high = min(counts, key=lambda k: (-counts[k], k))
    matching = [r for r in rows if (r["DRUG_ID"], r["MIN_CONC"], r["MAX_CONC"]) == (drug, low, high)]
    conditions.append({"id": name, "drug_id": drug, "drug_name": matching[0]["DRUG_NAME"],
        "min_conc_raw": low, "max_conc_raw": high, "train_record_count": counts[(drug, low, high)],
        "all_drug_ids_for_name": sorted({r["DRUG_ID"] for r in rows})})
conditions.sort(key=lambda r: hashlib.sha256(("C4-drug|" + r["id"]).encode()).hexdigest())
hash_source = hashlib.sha256()
md5_source = hashlib.md5()
with SOURCE.open("rb") as handle:
    for block in iter(lambda: handle.read(1 << 20), b""):
        hash_source.update(block)
        md5_source.update(block)
manifest = json.loads((HERE / "sources/root/P3_gdsc20_manifest.json").read_text(encoding="utf-8"))
result = {"source": str(SOURCE), "source_bytes": SOURCE.stat().st_size, "source_sha256": hash_source.hexdigest(),
          "source_md5": md5_source.hexdigest(), "matches_current_author_manifest": md5_source.hexdigest() == manifest["files"][0]["computed_md5"],
          "source_host": "author-deposited GDSC2 comparison data on Figshare, not a newly obtained Sanger release",
          "license_in_current_manifest": manifest["license"], "cell_count": len(cell_list), "ntrain": ntrain,
          "ntest": len(cell_list)-ntrain, "conditions_count": len(conditions), "metadata_records": len(records),
          "cells": cell_list, "conditions": conditions, "numeric_function_values_consumed": 0,
          "boundary": "CSV reader processes raw strings; only listed metadata fields are selected, no functional floats/values consumed"}
(HERE / "metadata_freeze.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: result[key] for key in ("source_bytes", "matches_current_author_manifest", "cell_count", "ntrain", "ntest", "conditions_count", "metadata_records", "numeric_function_values_consumed")}))
