"""Inventory source containers without decoding response or trajectory values."""
import io
import json
from pathlib import Path
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
result = {"scope": "Archive and workbook structure only; first-row types, no cell values decoded", "workbooks": {}}

for name in ("ampicillin-Fig2_S2.xlsx.hop1", "ampicillin-Fig2b_c.xlsx.hop1", "ampicillin-Fig4.xlsx.hop1"):
    data = (HERE / "sources" / name).read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as book:
        rels = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        targets = {x.attrib["Id"]: x.attrib["Target"] for x in rels}
        records = []
        for sheet in ET.fromstring(book.read("xl/workbook.xml")).find(NS + "sheets"):
            target = targets[sheet.attrib[RID]]
            path = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            xml = book.read(path)
            dim = re.search(rb'<dimension\b[^>]*\bref="([^"]+)"', xml)
            types = []
            with book.open(path) as stream:
                for _, node in ET.iterparse(stream, events=("end",)):
                    if node.tag == NS + "row":
                        for cell in node.findall(NS + "c"):
                            types.append({"coordinate": cell.attrib["r"], "type": cell.attrib.get("t", "numeric/default"),
                                          "formula": cell.find(NS + "f") is not None,
                                          "has_value": cell.find(NS + "v") is not None or cell.find(NS + "is") is not None})
                        break
            records.append({"sheet": sheet.attrib["name"], "dimension": dim.group(1).decode() if dim else None,
                            "first_stored_row_cell_types": types,
                            "merged_ranges": [x.decode() for x in re.findall(rb'<mergeCell\b[^>]*\bref="([^"]+)"', xml)]})
        result["workbooks"][name] = records

with zipfile.ZipFile(HERE / "sources/trail-figures-code-data.zip") as archive:
    result["TRAIL_archive"] = [{"name": x.filename, "bytes": x.file_size, "directory": x.is_dir()}
                               for x in archive.infolist()]

(HERE / "source_structure.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"workbooks": {n: [{"sheet": x["sheet"], "dimension": x["dimension"],
                                    "first_row_types": sorted({c["type"] for c in x["first_stored_row_cell_types"]})}
                                   for x in values] for n, values in result["workbooks"].items()},
                  "TRAIL_archive": result["TRAIL_archive"]}, ensure_ascii=False))
