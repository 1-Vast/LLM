"""Project container, sheet and conservative first-row header metadata only."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "sources/scsp-publisher-source.xlsx"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE = "http://schemas.openxmlformats.org/package/2006/relationships"
assert (HERE / "data_inspection_contract.md").is_file()
result = {"source_bytes": SOURCE.stat().st_size, "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          "scope": "Container/sheets/dimensions/first stored-row types; conservative headers only; no response cells projected", "sheets": []}
with zipfile.ZipFile(SOURCE) as archive:
    result["zip_members"] = [{"name": info.filename, "bytes": info.file_size} for info in archive.infolist()]
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    links = {n.get("Id"): n.get("Target") for n in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
    strings = []
    if "xl/sharedStrings.xml" in archive.namelist():
        strings = ["".join(n.itertext()) for n in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
    for sheet in workbook.findall("s:sheets/s:sheet", NS):
        target = links[sheet.get("{" + REL + "}id")]
        member = target.lstrip("/") if target.startswith("/") else "xl/" + target
        root = ET.fromstring(archive.read(member))
        row = root.find("s:sheetData/s:row", NS)
        item = {"name": sheet.get("name"), "member": member,
                "dimension": root.find("s:dimension", NS).get("ref") if root.find("s:dimension", NS) is not None else None,
                "merged_ranges": [n.get("ref") for n in root.findall("s:mergeCells/s:mergeCell", NS)],
                "first_stored_row": row.get("r") if row is not None else None, "first_row_cells": []}
        for cell in ([] if row is None else row):
            dtype = cell.get("t", "numeric/default")
            entry = {"address": cell.get("r"), "type": dtype, "formula": cell.find("s:f", NS) is not None}
            label = None
            if dtype == "s":
                node = cell.find("s:v", NS)
                label = strings[int(node.text)] if node is not None else None
            elif dtype == "inlineStr":
                node = cell.find("s:is", NS)
                label = "".join(node.itertext()) if node is not None else None
            if label is not None:
                if re.search(r"gene|exon|chr|start|end|sample|replicate|treatment|control|compound|condition|psi|count|risdiplam|nvs|u1|dmso|figure|source data|sequence|concentration|dose|binding|affinity|time", label, re.I) and not re.fullmatch(r"\s*[-+0-9.eE%]+\s*", label):
                    entry["header_candidate"] = label
                else:
                    entry["text_withheld"] = True
            item["first_row_cells"].append(entry)
        result["sheets"].append(item)
(HERE / "publisher_schema_initial.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"source_bytes": result["source_bytes"], "sheets": result["sheets"]}, ensure_ascii=False))
