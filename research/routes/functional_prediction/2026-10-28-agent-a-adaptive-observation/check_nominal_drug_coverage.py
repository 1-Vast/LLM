"""Count opaque drug-field presence, without parsing or exporting any response."""
import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
source = ROOT / "sources/gmu_subclones_original.xlsx"
crosswalk = json.loads((ROOT / "workbook_id_crosswalk.json").read_text(encoding="utf-8"))
assert hashlib.sha256(source.read_bytes()).hexdigest() == crosswalk["source_sha256"]
identities = {r["row"]: re.sub(r" [AB]$", "", r["total_id"]) for r in crosswalk["rows"]}
summary = {drug: {"nonempty_records": 0, "numeric_typed_records": 0,
                  "formula_cells": 0, "error_typed_cells": 0}
           for drug in ("osimertinib", "gefitinib")}
sets = {drug: set() for drug in summary}
numeric_sets = {drug: set() for drug in summary}
paired = set()
numeric_paired = set()
with zipfile.ZipFile(source) as archive:
    rows = ET.fromstring(archive.read("xl/worksheets/sheet1.xml")).findall("s:sheetData/s:row", NS)
    for row in rows:
        number = row.get("r")
        if number not in identities:
            continue
        present = []
        numeric_present = []
        for column, drug in (("D", "osimertinib"), ("E", "gefitinib")):
            cell = next((c for c in row if c.get("r") == column + number), None)
            if cell is None:
                present.append(False)
                numeric_present.append(False)
                continue
            value = cell.find("s:v", NS)
            nonempty = value is not None and bool(value.text and value.text.strip())
            stat = summary[drug]
            stat["nonempty_records"] += nonempty
            stat["numeric_typed_records"] += nonempty and cell.get("t", "n") == "n"
            stat["formula_cells"] += cell.find("s:f", NS) is not None
            stat["error_typed_cells"] += cell.get("t") == "e"
            present.append(nonempty)
            numeric = nonempty and cell.get("t", "n") == "n"
            numeric_present.append(numeric)
            if nonempty:
                sets[drug].add(identities[number])
            if numeric:
                numeric_sets[drug].add(identities[number])
        if all(present):
            paired.add(identities[number])
        if all(numeric_present):
            numeric_paired.add(identities[number])
for drug, values in sets.items():
    summary[drug]["unique_base_identities_with_nonempty_field"] = len(values)
    summary[drug]["unique_base_identities_with_numeric_typed_field"] = len(numeric_sets[drug])
out = {"source_sha256": crosswalk["source_sha256"], "drug_field_presence": summary,
       "base_identities_with_both_fields_in_a_record": len(paired),
       "base_identities_with_both_numeric_typed_fields_in_a_record": len(numeric_paired),
       "numeric_response_values_parsed": 0, "response_values_exported": 0,
       "qualification": "Nominal field presence only; exposure, repeat and normalization semantics unresolved."}
with (ROOT / "nominal_drug_coverage_v2.json").open("x", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=2)
print(json.dumps(out, ensure_ascii=False))
