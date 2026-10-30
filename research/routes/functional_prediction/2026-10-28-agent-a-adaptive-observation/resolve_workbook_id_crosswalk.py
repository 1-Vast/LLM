"""Check clone identity and author replicate labels; no assay values."""
import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "sources/gmu_subclones_original.xlsx"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
prior = json.loads((ROOT / "workbook_ids_v3.json").read_text(encoding="utf-8"))
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == prior["source_sha256"]
with zipfile.ZipFile(SOURCE) as archive:
    strings = ["".join(si.itertext()) for si in
               ET.fromstring(archive.read("xl/sharedStrings.xml"))]
    rows = ET.fromstring(archive.read("xl/worksheets/sheet1.xml")).findall("s:sheetData/s:row", NS)
    labels = {}
    for row in rows:
        cell = next((c for c in row if c.get("r") == "B" + row.get("r")), None)
        if cell is None or row.get("r") == "1":
            continue
        value = cell.find("s:v", NS)
        if cell.get("t") == "s" and value is not None:
            labels[row.get("r")] = strings[int(value.text)]
        elif cell.get("t") == "inlineStr":
            labels[row.get("r")] = "".join(cell.find("s:is", NS).itertext())

total, egfr = (s["identifier_rows"] for s in prior["sheets"])
assert len(total) == len(egfr)
crosswalk = []
for left, right in zip(total, egfr):
    number = left["cell"][1:]
    assert left["cell"] == right["cell"]
    a, b = left["id_token"], right["id_token"]
    label = labels.get(number, "").strip()
    combined = a if re.search(r" [AB]$", a) or label not in ("A", "B") else a + " " + label
    crosswalk.append({"row": number, "total_id": a, "total_replicate_label": label,
                      "total_combined_id": combined, "egfr_id": b,
                      "clone_match": re.sub(r" [AB]$", "", a) == re.sub(r" [AB]$", "", b),
                      "combined_id_match": combined == b})
summary = {"records": len(crosswalk),
           "base_clone_unique": len({re.sub(r" [AB]$", "", r["total_id"]) for r in crosswalk}),
           "clone_matches": sum(r["clone_match"] for r in crosswalk),
           "combined_id_matches": sum(r["combined_id_match"] for r in crosswalk),
           "unresolved_replicate_rows": [r["row"] for r in crosswalk if not r["combined_id_match"]],
           "numeric_response_values_parsed": 0,
           "independent_culture_repeats_qualified": False,
           "interpretation": "Row/clone correspondence only; author labels do not establish independent cultures."}
with (ROOT / "workbook_id_crosswalk.json").open("x", encoding="utf-8") as handle:
    json.dump({"source_sha256": prior["source_sha256"], "summary": summary,
               "rows": crosswalk}, handle, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False))
