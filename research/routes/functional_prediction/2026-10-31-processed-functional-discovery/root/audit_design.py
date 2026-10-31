"""Design-only projection, under metadata_projection_contract.md."""
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xlsx_projection import project

HERE = Path(__file__).resolve().parent
all_rows = {}
with zipfile.ZipFile(HERE / "sources/proteintalks-tables.zip") as package:
    members = {name.split("_", 1)[0]: name for name in package.namelist()}
    specifications = [
        ("S2_metadata", "TableS2", "A_Metadata", set("ABCDEFGHIJKL")),
        ("S8_metadata", "TableS8", "A_metadata", set("ABCDEFH")),
        ("S1_function_keys", "TableS1", "C_Efficacy", set("AB")),
        ("S7_function_keys", "TableS7", "B", set("AB")),
    ]
    for label, table, sheet, columns in specifications:
        rows = project(package.read(members[table]), sheet, columns, first_row=2)
        all_rows[label] = [row["cells"] for row in rows if row["cells"]]

for filename, sheets in (
    ("repair-data1.xlsx", {"raw_data": set("ABCD"), "calculated_relative_data": set("ABCD")}),
    ("repair-data3.xlsx", {"Raw_data": set("ABCDE"), "Relative_data": set("ABCDE"), "Controls": set("AB")}),
):
    payload = (HERE / "sources" / filename).read_bytes()
    for sheet, columns in sheets.items():
        all_rows[filename + ":" + sheet] = [
            row["cells"] for row in project(payload, sheet, columns, first_row=2) if row["cells"]
        ]

summary = {"scope": "Only columns frozen in metadata_projection_contract.md; no workbook response cells interpreted"}
s2 = all_rows["S2_metadata"]
s8 = all_rows["S8_metadata"]
for label, rows, time_column in (("S2", s2, "D"), ("S8", s8, "F")):
    times = defaultdict(set)
    drugs = defaultdict(set)
    paired_times = defaultdict(set)
    for row in rows:
        cell, drug, time = row.get("B"), row.get("F" if label == "S2" else "D"), row.get(time_column)
        times[cell].add(time)
        drugs[cell].add(drug)
        paired_times[(cell, drug)].add(time)
    summary[label] = {
        "rows": len(rows), "cell_lines": sorted(times),
        "time_values_by_cell": {k: sorted(v) for k, v in times.items()},
        "drug_identity_counts_by_cell": {k: len(v) for k, v in drugs.items()},
        "sample_type_counts": dict(Counter(row.get("L" if label == "S2" else "H") for row in rows)),
        "plate_counts_by_cell": {k: len({r.get("C") for r in rows if r.get("B") == k}) for k in times},
        "unique_cell_drug_keys": len(paired_times),
        "cell_drug_time_count_histogram": dict(Counter(len(v) for v in paired_times.values())),
    }
    if label == "S2":
        summary[label]["drug_num_counts"] = dict(Counter(row.get("E") for row in rows))
        function_keys = {(r.get("A"), r.get("B")) for r in all_rows["S1_function_keys"]}
        matching = set(paired_times) & function_keys
        summary[label]["exact_function_key_matches"] = len(matching)
        summary[label]["dose_fields_present_not_unit_qualified"] = True
    else:
        summary[label]["dose_field_present"] = False

summary["function_identity_rows"] = {
    name: {"rows": len(all_rows[name]),
           "unique_keys": len({tuple(r.get(k) for k in "AB") for r in all_rows[name]}),
           "cell_lines": sorted({r.get("A") for r in all_rows[name]})}
    for name in ("S1_function_keys", "S7_function_keys")
}
summary["repair"] = {}
for name, rows in all_rows.items():
    if not name.startswith("repair-"):
        continue
    data3 = name.startswith("repair-data3")
    compound_col = "C" if data3 and not name.endswith(":Controls") else "B"
    dose_col = "E" if data3 else "C"
    summary["repair"][name] = {
        "metadata_rows": len(rows),
        "distinct_nonempty_compound_names": len({r.get(compound_col) for r in rows if r.get(compound_col)}),
        "first_identity_strings": [r.get("A") for r in rows[:6]],
        "distinct_dose_identity_strings": sorted({r[dose_col] for r in rows if dose_col in r}),
        "explicit_locus_background_repeat_fields_present": False,
    }
summary["repair"]["data1_metadata_rows_equal"] = (
    all_rows["repair-data1.xlsx:raw_data"] == all_rows["repair-data1.xlsx:calculated_relative_data"]
)
summary["repair"]["data3_metadata_rows_equal"] = (
    all_rows["repair-data3.xlsx:Raw_data"] == all_rows["repair-data3.xlsx:Relative_data"]
)
(HERE / "design_metadata_projection.json").write_text(json.dumps(all_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(HERE / "design_audit.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))

