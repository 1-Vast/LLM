"""Inspect reference-key structure in the already declared fixed prefix; no outcomes."""
from pathlib import Path
import json
import time
import zipfile
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent.parent / "tmp/extq1/gsdc_well_stats.zip"
COLS = ["BARCODE", "MASTER_CELL_ID", "lib1_drug_id", "lib1_drug", "lib1_conc",
        "lib2_drug_id", "lib2_drug", "lib2_conc"]
started = time.monotonic()
with zipfile.ZipFile(RAW) as archive:
    with archive.open("combo_well_stats_GDSC_007_05May22.csv") as stream:
        frame = pd.read_csv(stream, usecols=COLS, nrows=20_000, dtype=str)
parts = []
for side in (1, 2):
    part = frame[["BARCODE", "MASTER_CELL_ID", f"lib{side}_drug_id", f"lib{side}_drug", f"lib{side}_conc"]].copy()
    part.columns = ["plate", "cell", "drug", "ref", "conc"]
    parts.append(part)
refs = pd.concat(parts, ignore_index=True).dropna()
matches = [r.startswith(b + "_") for r, b in zip(refs["ref"], refs["plate"])]
groups = refs.groupby("ref")
coverage = groups["conc"].nunique().value_counts().sort_index()
out = {
    "selection": "Same fixed GDSC007 first20000 rows; identity and dose fields only",
    "columns": COLS, "reference_appearances": len(refs), "unique_reference_strings": refs["ref"].nunique(),
    "ref_begins_with_current_plate_underscore": sum(matches),
    "ref_does_not_begin_with_current_plate_underscore": len(matches) - sum(matches),
    "refs_mapping_to_more_than_one_current_plate": int((groups["plate"].nunique() > 1).sum()),
    "refs_mapping_to_more_than_one_cell": int((groups["cell"].nunique() > 1).sum()),
    "refs_mapping_to_more_than_one_drug": int((groups["drug"].nunique() > 1).sum()),
    "number_of_refs_by_distinct_concentration_strings": {str(k): int(v) for k, v in coverage.items()},
    "first_five_public_identity_examples": refs[["plate", "cell", "drug", "ref"]].drop_duplicates().head(5).to_dict(orient="records"),
    "response_or_fit_columns_retained_or_numerically_parsed": [],
    "interpretation": "A naming pattern does not certify a source well or independent measurement. No response equality, replicate independence, global coverage or scientific outcome is tested."
}
out["seconds"] = round(time.monotonic() - started, 3)
assert out["seconds"] < 120
(HERE / "source_key_structure.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
