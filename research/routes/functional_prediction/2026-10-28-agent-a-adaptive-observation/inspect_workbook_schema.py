"""Metadata and identifier inspection only; no numerical response conversion."""
import hashlib
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "sources" / "gmu_subclones_original.xlsx"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
EXPECTED = "852c85ad4fc400f3cab696c59c246c987d287bc3c6eb85be3981c9a50eb2a63f"


def column(cell):
    return "".join(c for c in cell.attrib["r"] if c.isalpha())


with zipfile.ZipFile(SOURCE) as archive:
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    strings = ["".join(si.itertext()) for si in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
    def string(cell):
        value = cell.find("s:v", NS)
        if cell.get("t") == "s" and value is not None:
            return strings[int(value.text)]  # Index, never an assay value.
        if cell.get("t") == "inlineStr":
            return "".join(cell.find("s:is", NS).itertext())
        return None

    relationships = {r.get("Id"): r.get("Target") for r in
                     ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
    style = ET.fromstring(archive.read("xl/styles.xml"))
    fonts, fills, xfs = (style.find("s:" + part, NS) for part in ("fonts", "fills", "cellXfs"))
    results = []
    for sheet in ET.fromstring(archive.read("xl/workbook.xml")).find("s:sheets", NS):
        target = relationships[sheet.get("{" + NS["r"] + "}id")]
        member = target.lstrip("/") if target.startswith("/") else "xl/" + target
        xml = ET.fromstring(archive.read(member))
        rows = xml.findall("s:sheetData/s:row", NS)
        identifiers = [(row, cell) for row in rows for cell in row if
                       "".join((string(cell) or "").lower().split()) == "originalmcpid"]
        result = {"sheet": sheet.get("name"), "member": member,
                  "dimension": xml.find("s:dimension", NS).get("ref"),
                  "xml_row_count": len(rows), "numeric_response_values_parsed": 0}
        if len(identifiers) != 1:
            result.update(status="schema_unresolved", id_header_matches=len(identifiers))
            results.append(result)
            continue
        header, id_cell = identifiers[0]
        id_column, header_number = column(id_cell), int(header.get("r"))
        result.update(status="header_located", header_row=header_number, id_column=id_column,
                      header_cells=[{"cell": cell.get("r"), "string": string(cell),
                                     "type": cell.get("t", "n")} for cell in header])
        ids = []
        for row in rows:
            if int(row.get("r")) <= header_number:
                continue
            cell = next((c for c in row if column(c) == id_column), None)
            if cell is None or string(cell) is None:
                continue
            xf = xfs[int(cell.get("s", "0"))]
            ids.append({"cell": cell.get("r"), "id": string(cell), "style_index": int(cell.get("s", "0")),
                        "font_xml": ET.tostring(fonts[int(xf.get("fontId"))], encoding="unicode"),
                        "fill_xml": ET.tostring(fills[int(xf.get("fillId"))], encoding="unicode")})
        result["identifier_rows_with_style_only"] = ids
        results.append(result)
    output = {"source_sha256": EXPECTED, "protocol_sha256": hashlib.sha256(
        (ROOT / "SCHEMA_READ_PROTOCOL.md").read_bytes()).hexdigest(),
        "active_content_executed": False, "sheets": results,
        "scope": "Header strings and identifier-cell formatting only; all assay values remain unparsed."}
    with (ROOT / "workbook_schema.json").open("x", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
    print(json.dumps({"sheets": [{"sheet": x["sheet"], "status": x["status"],
        "dimension": x["dimension"], "id_rows": len(x.get("identifier_rows_with_style_only", [])),
        "header_row": x.get("header_row")} for x in results], "numeric_responses_parsed": 0}))
