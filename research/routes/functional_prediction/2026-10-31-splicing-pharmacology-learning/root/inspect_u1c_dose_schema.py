"""Stream to workbook headers only; never project treatment/PSI rows."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "sources/u1c-dose-sample-data2.xlsx"
result = {"file_bytes": SOURCE.stat().st_size, "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          "scope": "ZIP/workbook/first-row headers only; no response records", "sheets": []}
with zipfile.ZipFile(SOURCE) as archive:
    result["members"] = [{"name": n.filename, "uncompressed_bytes": n.file_size} for n in archive.infolist()]
    book = ET.fromstring(archive.read("xl/workbook.xml"))
    ns = {"s": book.tag.split("}", 1)[0].lstrip("{")}
    relations = {n.get("Id"): n.get("Target") for n in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
    needed = set()
    for sheet in book.findall("s:sheets/s:sheet", ns):
        target = relations[next(v for k, v in sheet.attrib.items() if k.endswith("}id"))]
        target = target.lstrip("/") if target.startswith("/") else "xl/" + target
        entry = {"sheet": sheet.get("name"), "member": target, "first_row_cells": []}
        with archive.open(target) as stream:
            for event, node in ET.iterparse(stream, events=("end",)):
                if node.tag.endswith("}dimension"):
                    entry["dimension"] = node.get("ref")
                if node.tag.endswith("}row"):
                    entry["first_stored_row"] = node.get("r")
                    for cell in node:
                        dtype = cell.get("t", "numeric/default")
                        item = {"address": cell.get("r"), "type": dtype, "formula": cell.find("s:f", ns) is not None}
                        if dtype == "s":
                            index = int(cell.find("s:v", ns).text)
                            needed.add(index)
                            item["string_index"] = index
                        elif dtype == "inlineStr":
                            item["text_header_candidate"] = "".join(cell.find("s:is", ns).itertext())
                        entry["first_row_cells"].append(item)
                    break
        result["sheets"].append(entry)
    strings = {}
    if needed:
        with archive.open("xl/sharedStrings.xml") as stream:
            index = 0
            for event, node in ET.iterparse(stream, events=("end",)):
                if node.tag.endswith("}si"):
                    if index in needed:
                        strings[index] = "".join(node.itertext())
                    index += 1
                    node.clear()
                    if index > max(needed):
                        break
    for sheet in result["sheets"]:
        for cell in sheet["first_row_cells"]:
            if "string_index" in cell:
                cell["text_header_candidate"] = strings[cell.pop("string_index")]
(HERE / "u1c_dose_schema.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"file_bytes": result["file_bytes"], "sheets": result["sheets"]}, ensure_ascii=False))
