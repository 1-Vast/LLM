"""Read only header strings, column-A identifiers and their styles."""
import hashlib
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "sources/gmu_subclones_original.xlsx"
EXPECTED = "852c85ad4fc400f3cab696c59c246c987d287bc3c6eb85be3981c9a50eb2a63f"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def column(cell):
    return "".join(ch for ch in cell.get("r") if ch.isalpha())


assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
with zipfile.ZipFile(SOURCE) as archive:
    strings = ["".join(si.itertext()) for si in
               ET.fromstring(archive.read("xl/sharedStrings.xml"))]

    def token(cell, allow_numeric_id=False):
        if cell is None:
            return None
        value = cell.find("s:v", NS)
        if cell.get("t") == "s" and value is not None:
            return strings[int(value.text)]  # Shared-string index only.
        if cell.get("t") == "inlineStr":
            return "".join(cell.find("s:is", NS).itertext())
        if allow_numeric_id and cell.get("t", "n") == "n" and value is not None:
            return value.text  # An ID token, never converted to a number.
        return None

    relationships = {r.get("Id"): r.get("Target") for r in
                     ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
    styles = ET.fromstring(archive.read("xl/styles.xml"))
    fonts, fills, xfs = (styles.find("s:" + name, NS)
                         for name in ("fonts", "fills", "cellXfs"))
    sheets = []
    for sheet in ET.fromstring(archive.read("xl/workbook.xml")).find("s:sheets", NS):
        target = relationships[sheet.get("{" + REL + "}id")]
        member = target.lstrip("/") if target.startswith("/") else "xl/" + target
        xml = ET.fromstring(archive.read(member))
        rows = xml.findall("s:sheetData/s:row", NS)
        header = next(row for row in rows if row.get("r") == "1")
        a1 = next(cell for cell in header if cell.get("r") == "A1")
        ids = []
        for row in rows:
            if row.get("r") == "1":
                continue
            cell = next((c for c in row if column(c) == "A"), None)
            value = token(cell, allow_numeric_id=True)
            if value is None or not value.strip():
                continue
            xf = xfs[int(cell.get("s", "0"))]
            ids.append({"cell": cell.get("r"), "id_token": value,
                        "source_cell_type": cell.get("t", "n"),
                        "font_xml": ET.tostring(fonts[int(xf.get("fontId"))], encoding="unicode"),
                        "fill_xml": ET.tostring(fills[int(xf.get("fillId"))], encoding="unicode")})
        values = [r["id_token"] for r in ids]
        sheets.append({"sheet": sheet.get("name"), "dimension": xml.find("s:dimension", NS).get("ref"),
                       "xml_rows": len(rows), "original_a1": token(a1),
                       "header_string_count": sum(token(c) is not None for c in header),
                       "header_cells": len(header), "id_rows": len(ids),
                       "unique_ids": len(set(values)),
                       "duplicate_ids": sorted({v for v in values if values.count(v) > 1}),
                       "identifier_rows": ids})

by_name = {s["sheet"]: s for s in sheets}
total, egfr = by_name["Total RPPA data"], by_name["EGFR activation"]
assert egfr["original_a1"] == "Original MCP ID (plus replicates A/B where applicable)"
assert total["original_a1"] == "`"
total_ids = [r["id_token"] for r in total["identifier_rows"]]
egfr_ids = [r["id_token"] for r in egfr["identifier_rows"]]
comparison = {"same_id_sequence": total_ids == egfr_ids,
              "same_id_set": set(total_ids) == set(egfr_ids),
              "only_total": sorted(set(total_ids) - set(egfr_ids)),
              "only_egfr": sorted(set(egfr_ids) - set(total_ids))}
output = {"source_sha256": EXPECTED,
          "protocol_sha256": hashlib.sha256((ROOT / "SCHEMA_READ_PROTOCOL_v3.md").read_bytes()).hexdigest(),
          "sheets": sheets, "comparison": comparison,
          "numeric_response_values_parsed": 0, "active_content_executed": False,
          "mapping_status": "readme_and_id_sequence_supported" if comparison["same_id_sequence"]
                            else "main_id_correspondence_unresolved",
          "replicate_interpretation": "Author labels/styles retained; independence not established."}
with (ROOT / "workbook_ids_v3.json").open("x", encoding="utf-8") as handle:
    json.dump(output, handle, ensure_ascii=False, indent=2)
print(json.dumps({"sheets": [{k: s[k] for k in
      ("sheet", "dimension", "header_string_count", "header_cells", "id_rows", "unique_ids")}
      for s in sheets], "comparison": comparison, "mapping_status": output["mapping_status"],
      "numeric_response_values_parsed": 0}, ensure_ascii=False))
