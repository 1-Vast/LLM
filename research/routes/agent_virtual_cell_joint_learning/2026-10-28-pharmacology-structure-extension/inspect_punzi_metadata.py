"""Read protocol labels only; never export numeric cells or formula values."""
from pathlib import Path
import hashlib
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
source = root / "sources/punzi/41467_2024_54728_MOESM8_ESM.zip"
member = "Source Data/Extended Data 5.xlsx"
main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ns = {"m": main}
words = re.compile(r"FOLFOX|FOLFIRI|HCT.?116|DMSO|control|CTRL|untreated|treatment|re.?challenge|holiday|replicate|experiment|oxaliplatin|irinotecan|5-?FU", re.I)
raw = source.read_bytes()
with zipfile.ZipFile(io.BytesIO(raw)) as outer:
    book = outer.read(member)
with zipfile.ZipFile(io.BytesIO(book)) as archive:
    strings = []
    if "xl/sharedStrings.xml" in archive.namelist():
        strings = ["".join(node.itertext()) for node in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si", ns)]
    relations = {node.attrib["Id"]: node.attrib["Target"] for node in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
    sheets = []
    for node in ET.fromstring(archive.read("xl/workbook.xml")).findall("m:sheets/m:sheet", ns):
        target = relations[node.attrib[f"{{{rel}}}id"]]
        target = target.lstrip("/") if target.startswith("/") else "xl/" + target
        tree = ET.fromstring(archive.read(target))
        dimension = tree.find("m:dimension", ns)
        item = {"sheet": node.attrib["name"], "dimension": dimension.attrib.get("ref") if dimension is not None else None,
                "counts": {"numeric_or_other": 0, "formula": 0, "string": 0, "unexported_string": 0}, "protocol_labels": []}
        for cell in tree.findall(".//m:sheetData/m:row/m:c", ns):
            if cell.find("m:f", ns) is not None:
                item["counts"]["formula"] += 1
                continue
            kind = cell.attrib.get("t")
            if kind not in ("s", "inlineStr"):
                item["counts"]["numeric_or_other"] += 1
                continue
            item["counts"]["string"] += 1
            value = strings[int(cell.find("m:v", ns).text)] if kind == "s" else "".join(cell.find("m:is", ns).itertext())
            if len(value) <= 140 and words.search(value):
                item["protocol_labels"].append({"cell": cell.attrib["r"], "text": value})
            else:
                item["counts"]["unexported_string"] += 1
        sheets.append(item)
result = {"scope": "protocol-label whitelist; no numeric cells or formulas exported", "source_zip": str(source),
          "zip_sha256": hashlib.sha256(raw).hexdigest(), "member": member,
          "workbook_sha256": hashlib.sha256(book).hexdigest(), "sheets": sheets}
(root / "punzi_metadata.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
