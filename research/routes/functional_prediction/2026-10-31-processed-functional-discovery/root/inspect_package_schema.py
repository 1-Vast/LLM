"""Read worksheet identities and row-one headers only; no response cells."""
import io
import json
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
SELECTED = {1, 2, 7, 8, 10, 16, 17}
output = []
with zipfile.ZipFile(HERE / "sources/proteintalks-tables.zip") as outer:
    for member in outer.infolist():
        match = re.match(r"TableS(\d+)_", member.filename)
        if not match or int(match[1]) not in SELECTED:
            continue
        if member.file_size > 80 * 1024 * 1024:
            raise ValueError("Workbook exceeds metadata read bound")
        with zipfile.ZipFile(io.BytesIO(outer.read(member))) as workbook:
            relationships = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
            targets = {r.attrib["Id"]: r.attrib["Target"] for r in relationships}
            book = ET.fromstring(workbook.read("xl/workbook.xml"))
            records = []
            wanted = set()
            for sheet in book.find(NS + "sheets"):
                target = targets[sheet.attrib[RID]]
                path = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
                headers = []
                dimension = None
                with workbook.open(path) as stream:
                    for event, node in ET.iterparse(stream, events=("end",)):
                        if node.tag == NS + "dimension":
                            dimension = node.attrib.get("ref")
                        if node.tag == NS + "row":
                            if node.attrib.get("r") == "1":
                                for cell in node.findall(NS + "c"):
                                    kind = cell.attrib.get("t")
                                    value = cell.find(NS + "v")
                                    formula = cell.find(NS + "f")
                                    if formula is not None:
                                        header = {"address": cell.attrib["r"], "value": "<formula>"}
                                    elif kind == "s" and value is not None:
                                        index = int(value.text)
                                        wanted.add(index)
                                        header = {"address": cell.attrib["r"], "shared_index": index}
                                    elif kind == "inlineStr":
                                        text = "".join(t.text or "" for t in cell.iter(NS + "t"))
                                        header = {"address": cell.attrib["r"], "value": text}
                                    else:
                                        header = {"address": cell.attrib["r"], "value": "<numeric-or-empty>"}
                                    headers.append(header)
                            break
                records.append({"sheet": sheet.attrib["name"], "dimension": dimension,
                                "header_cell_count": len(headers), "headers": headers})
            strings = {}
            if wanted and "xl/sharedStrings.xml" in workbook.namelist():
                index = 0
                with workbook.open("xl/sharedStrings.xml") as stream:
                    for event, node in ET.iterparse(stream, events=("end",)):
                        if node.tag == NS + "si":
                            if index in wanted:
                                strings[index] = "".join(t.text or "" for t in node.iter(NS + "t"))
                            node.clear()
                            index += 1
                            if len(strings) == len(wanted):
                                break
            for record in records:
                for header in record["headers"]:
                    if "shared_index" in header:
                        header["value"] = strings.get(header.pop("shared_index"), "<unresolved>")
                if len(record["headers"]) > 60:
                    record["headers"] = record["headers"][:25] + record["headers"][-3:]
                    record["header_output_truncated"] = True
            output.append({"member": member.filename, "worksheets": records})
result = {"scope": "Workbook identities and row-one schema only; no response cells parsed or emitted",
          "selected_table_numbers": sorted(SELECTED), "workbooks": output}
(HERE / "package_schema.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
for book in output:
    print(json.dumps(book, ensure_ascii=False))

