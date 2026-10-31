"""Project explicitly named worksheet columns; decode only selected shared strings."""
import io
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def sheets(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as book:
        rels = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        targets = {node.attrib["Id"]: node.attrib["Target"] for node in rels}
        result = []
        for node in ET.fromstring(book.read("xl/workbook.xml")).find(NS + "sheets"):
            target = targets[node.attrib[RID]]
            path = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            result.append((node.attrib["name"], path))
        return result


def project(payload, sheet, columns, first_row=1, last_row=None, mask_numeric=False):
    paths = dict(sheets(payload))
    wanted = set()
    rows = []
    with zipfile.ZipFile(io.BytesIO(payload)) as book:
        with book.open(paths[sheet]) as stream:
            for _, node in ET.iterparse(stream, events=("end",)):
                if node.tag != NS + "row":
                    continue
                number = int(node.attrib["r"])
                if last_row is not None and number > last_row:
                    break
                if number >= first_row:
                    selected = {"row": number, "cells": {}}
                    for cell in node.findall(NS + "c"):
                        column = re.sub(r"\d", "", cell.attrib["r"])
                        if columns is not None and column not in columns:
                            continue
                        kind = cell.attrib.get("t")
                        value = cell.find(NS + "v")
                        if cell.find(NS + "f") is not None:
                            selected["cells"][column] = "<formula>"
                        elif kind == "s" and value is not None:
                            index = int(value.text)
                            wanted.add(index)
                            selected["cells"][column] = {"shared_index": index}
                        elif kind == "inlineStr":
                            selected["cells"][column] = "".join(t.text or "" for t in cell.iter(NS + "t"))
                        elif value is not None:
                            selected["cells"][column] = "<numeric>" if mask_numeric else value.text
                    rows.append(selected)
                node.clear()
        lookup = {}
        if wanted and "xl/sharedStrings.xml" in book.namelist():
            index = 0
            with book.open("xl/sharedStrings.xml") as stream:
                for _, node in ET.iterparse(stream, events=("end",)):
                    if node.tag == NS + "si":
                        if index in wanted:
                            lookup[index] = "".join(t.text or "" for t in node.iter(NS + "t"))
                        node.clear()
                        index += 1
                        if len(lookup) == len(wanted):
                            break
        for row in rows:
            for column, value in row["cells"].items():
                if isinstance(value, dict):
                    row["cells"][column] = lookup[value["shared_index"]]
    return rows

