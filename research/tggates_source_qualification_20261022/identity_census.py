"""Read official identity CSV projections only; exclude CELL_VIABILITY links."""
import io
import json
from pathlib import Path
import zipfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_source_qualification"
ALLOWED = {"BARCODE", "ARR_DESIGN", "EXP_ID", "GROUP_ID", "INDIVIDUAL_ID", "ORGAN", "MATERIAL_ID", "COMPOUND_NAME", "COMPOUND_ABBREVIATION", "COMPOUND_NO", "SPECIES", "EXP_TEST_TYPE", "SINGLE_REPEAT_TYPE", "SEX_TYPE", "STRAIN_TYPE", "ADMINISTRATION_ROUTE_TYPE", "ANIMAL_AGE(week)", "SACRIFICE_PERIOD", "DOSE", "DOSE_UNIT", "DOSE_LEVEL"}


def read_archive(name):
    with zipfile.ZipFile(OUT / name) as archive:
        items = [x for x in archive.namelist() if x.endswith(".csv")]
        assert len(items) == 1
        data = archive.read(items[0])
    header = pd.read_csv(io.BytesIO(data), nrows=0, encoding="cp932").columns.tolist()
    return pd.read_csv(io.BytesIO(data), usecols=lambda x: x in ALLOWED, dtype=str, encoding="cp932", keep_default_na=False), header


def main():
    target = OUT / "IDENTITY_CENSUS.json"
    assert not target.exists()
    attrs, attrs_header = read_archive("CEL_ATTRIBUTES.zip")
    cells, cells_header = read_archive("CELL_SAMPLE.zip")
    human_a = attrs[attrs["SPECIES"].str.lower().str.contains("human")].copy()
    human_c = cells[cells["SPECIES"].str.lower().str.contains("human")].copy()
    group_cols = ["COMPOUND_NAME", "DOSE", "DOSE_UNIT", "SACRIFICE_PERIOD"]
    action_sizes = human_c.groupby(group_cols, dropna=False).size()
    compound_exp = human_c.groupby("COMPOUND_NAME")["EXP_ID"].nunique()
    condition_duplicates = human_c.duplicated(["EXP_ID", "GROUP_ID", "INDIVIDUAL_ID"]).sum()
    barcode_set = set(human_a["BARCODE"].dropna())
    # CELL_SAMPLE BARCODE is a join link, not a biological value.
    linked = human_c["BARCODE"].dropna()
    variants = {c: human_c[c].value_counts(dropna=False).to_dict() for c in ["SPECIES", "SACRIFICE_PERIOD", "DOSE_UNIT", "DOSE_LEVEL", "INDIVIDUAL_ID"]}
    result = {"columns": {"attributes": attrs_header, "cell_sample": cells_header},
              "projected_columns": sorted(ALLOWED), "human_attribute_rows": len(human_a), "human_cell_rows": len(human_c),
              "all_attribute_rows": len(attrs), "all_cell_rows": len(cells), "human_compounds": human_c["COMPOUND_NAME"].nunique(),
              "human_action_count": len(action_sizes), "rows_per_compound_dose_time": action_sizes.value_counts().to_dict(),
              "experiments_per_compound": compound_exp.value_counts().to_dict(), "duplicate_sample_keys": int(condition_duplicates),
              "human_metadata_values": variants,
              "lot_or_culture_columns": [c for c in attrs_header+cells_header if any(x in c.lower() for x in ["lot", "culture", "source", "donor"])],
              "human_barcode_examples": sorted(barcode_set)[:5], "cell_barcode_link_examples": linked.tolist()[:5],
              "cell_barcode_links_in_attribute_ids": sum(x in barcode_set for x in linked),
              "attribute_exp_test_type": human_a["EXP_TEST_TYPE"].value_counts().to_dict(),
              "material_ids": human_a["MATERIAL_ID"].value_counts().to_dict(),
              "individual_outcomes_read": False, "CELL_VIABILITY_column_read": False,
              "status": "CROSS_LOT_IDENTITY_NOT_QUALIFIED: no lot/culture/source field in either archive; six lots in paper do not authenticate matching actions"}
    human_c.to_json(OUT / "HUMAN_CELL_IDENTITIES.json", orient="records", indent=2)
    human_a.to_json(OUT / "HUMAN_CEL_IDENTITIES.json", orient="records", indent=2)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
