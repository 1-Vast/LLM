"""Inspect named first-row schemas only; no worksheet response values."""
from io import BytesIO
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent


def schema(blob, selected=None):
    result = []
    with zipfile.ZipFile(BytesIO(blob)) as archive:
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        namespace = book.tag.split("}", 1)[0].lstrip("{")
        ns = {"s": namespace}
        relations = {node.get("Id"): node.get("Target") for node in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(n.itertext()) for n in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        for sheet in book.findall("s:sheets/s:sheet", ns):
            name = sheet.get("name")
            if selected is not None and name not in selected:
                continue
            rid = next(v for k, v in sheet.attrib.items() if k.endswith("}id"))
            member = relations[rid]
            member = member.lstrip("/") if member.startswith("/") else "xl/" + member
            root = ET.fromstring(archive.read(member))
            dimension = root.find("s:dimension", ns)
            row = root.find("s:sheetData/s:row", ns)
            entry = {"sheet": name, "dimension": dimension.get("ref") if dimension is not None else None,
                     "first_stored_row": row.get("r") if row is not None else None, "headers": []}
            for cell in ([] if row is None else row):
                dtype = cell.get("t", "numeric/default")
                item = {"address": cell.get("r"), "type": dtype, "formula": cell.find("s:f", ns) is not None}
                text = None
                if dtype == "s":
                    node = cell.find("s:v", ns)
                    text = strings[int(node.text)] if node is not None else None
                elif dtype == "inlineStr":
                    node = cell.find("s:is", ns)
                    text = "".join(node.itertext()) if node is not None else None
                if text is not None and not item["formula"]:
                    if len(text) <= 160 and not re.fullmatch(r"\s*[-+0-9.eE%]+\s*", text):
                        item["text_header_candidate"] = text
                    else:
                        item["text_withheld"] = True
                entry["headers"].append(item)
            result.append(entry)
    return result


with zipfile.ZipFile(HERE / "sources/u1c-source.zip") as archive:
    raw = archive.read("Source data table.xlsx")
    member = HERE / "sources/u1c-source-table.xlsx"
    assert not member.exists()
    member.write_bytes(raw)
result = {
    "scope": "First stored row text/header candidates only; no response rows projected",
    "u1c_source": schema(raw),
    "lenkeit_selected_headers": schema((HERE / "sources/scsp-publisher-source.xlsx").read_bytes(),
        {"Fig1D", "Fig1E", "Fig2A", "Fig2C", "Fig3E", "Fig3F", "Fig4C", "Fig4D", "Fig4E", "Fig5A", "Fig5B", "Fig7C", "Fig7D"}),
}
(HERE / "additional_schemas.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
