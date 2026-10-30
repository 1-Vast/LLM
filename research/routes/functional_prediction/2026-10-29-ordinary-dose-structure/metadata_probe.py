"""Fixed-prefix identity/dose probe; outcome and fit columns are excluded by usecols."""
from pathlib import Path
import json
import time
import zipfile
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent.parent / "tmp/extq1/gsdc_well_stats.zip"
MEMBER = "combo_well_stats_GDSC_007_05May22.csv"
ROW_CAP = 20_000
USECOLS = ["PROJECT_ID", "BARCODE", "MASTER_CELL_ID", "CELL_ID", "POSITION", "cmatrix", "treatment",
           "lib1_drug_id", "lib1_conc", "lib1_drug", "lib2_drug_id", "lib2_conc", "lib2_drug"]
started = time.monotonic()
with zipfile.ZipFile(RAW) as archive:
    with archive.open(MEMBER) as stream:
        frame = pd.read_csv(stream, usecols=USECOLS, nrows=ROW_CAP, dtype=str)
refs = []
for side in (1, 2):
    part = frame[["PROJECT_ID", "MASTER_CELL_ID", f"lib{side}_drug", f"lib{side}_drug_id", f"lib{side}_conc"]].copy()
    part.columns = ["project", "cell", "ref", "drug", "conc"]
    refs.append(part)
refs = pd.concat(refs, ignore_index=True).dropna()
key = ["project", "cell", "ref", "conc"]
counts = refs.groupby(key, dropna=False).size()
mapping = refs.groupby(["project", "cell", "ref"], dropna=False)["drug"].nunique()
concentrations = pd.to_numeric(refs["conc"], errors="coerce")
out = {
    "selection": "First20000 data rows of fixed GDSC007 member; no outcome-dependent filter; incomplete prefix, not full dataset coverage",
    "raw_path": str(RAW), "member": MEMBER, "row_cap": ROW_CAP,
    "rows_projected": len(frame), "allowed_columns": USECOLS,
    "csv_row_bytes_include_outcomes": True,
    "outcome_columns_retained_or_numerically_parsed": [],
    "fitted_curve_columns_retained_or_numerically_parsed": [],
    "cell_models": frame["MASTER_CELL_ID"].nunique(),
    "stock_expansion_ids": frame["CELL_ID"].nunique(),
    "plate_barcodes": frame["BARCODE"].nunique(),
    "plate_matrices": len(frame[["BARCODE", "cmatrix"]].drop_duplicates()),
    "drug_ids": pd.concat([frame["lib1_drug_id"], frame["lib2_drug_id"]]).nunique(),
    "treatment_counts": frame["treatment"].value_counts(dropna=False).to_dict(),
    "reference_appearances_with_complete_keys": len(refs),
    "unique_project_cell_reference_concentration_keys": len(counts),
    "reference_keys_appearing_more_than_once": int((counts > 1).sum()),
    "max_reference_key_multiplicity": int(counts.max()),
    "reference_keys_mapping_to_multiple_drug_ids": int((mapping > 1).sum()),
    "numeric_concentration_count": int(concentrations.notna().sum()),
    "numeric_concentration_range_uM": [float(concentrations.min()), float(concentrations.max())],
    "first_unique_concentration_strings": refs["conc"].drop_duplicates().head(8).tolist(),
    "interpretation_boundary": "Repeated reference fields are not independent measured wells; exact source-assay mapping remains unverified. CELL_ID is a stock-expansion identifier, not certified independent culture. Prefix counts cannot qualify global drug/cell/dose/replicate coverage."
}
out["seconds"] = round(time.monotonic() - started, 3)
assert out["seconds"] < 120
(HERE / "metadata_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
