"""Predeclared allowlist metadata inspection; never consume numeric cell values."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET

episode = Path(__file__).resolve().parent
source = episode / "sources/Fig_5C.xlsx"
output = episode / "sources/Fig_5C_header_inspection.json"
assert not output.exists(), "No repeated inspection without a changed question"
assert (episode / "sources/header_inspection_contract.md").exists()
numeric_like = re.compile(r"^[\s+\-0-9.,eE%/]+$")
words = set("trail tbq tcq dmso control untreated cell cells density change changes area occupied survival viable viability mean sem sd standard deviation error replicate replicates experiment experiments repeat repeats repetition repetitions time times hour hours h hr hrs day days phase phases cycle cycles first second third fourth naive tolerant treatment treated treatments resting rest before after initial population populations relative percentage percent normalized normalised of in to and with no drug drugs conditioned conditioning persisters persister".split())

def permitted(value):
    normalized = " ".join(value.split())
    if not normalized or numeric_like.fullmatch(normalized):
        return None
    tokens = re.findall(r"[A-Za-z]+|[0-9]+|[^\w\s]", normalized)
    lower = normalized.lower()
    has_id = bool(re.search(r"\b(?:experiment|replicate|repeat)\s*[0-9]+\b", lower))
    has_time = bool(re.search(r"(?:\b(?:time|hour|hours|day|days|phase)\b.*[0-9]|[0-9]\s*(?:h|hr|hrs|hours|days)\b)", lower))
    for token in tokens:
        if token.isalpha() and token.lower() not in words:
            return None
        if token.isdigit() and not (has_id or has_time):
            return None
        if not token.isalnum() and token not in "/-→>%():,;_":
            return None
    return normalized

result = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
          "contract": "sources/header_inspection_contract.md",
          "numeric_outcome_values_read": False, "formulas_read": False,
          "shared_string_bytes_screened_for_allowlisted_metadata": True, "worksheets": []}
with zipfile.ZipFile(source) as archive:
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strings = []
    if "xl/sharedStrings.xml" in archive.namelist():
        for item in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", ns):
            strings.append(permitted("".join(t.text or "" for t in item.findall(".//s:t", ns))))
    for name in archive.namelist():
        if not re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml", name):
            continue
        root = ET.fromstring(archive.read(name))
        item = {"member": name, "dimension": None, "approved_string_cells": [],
                "withheld_string_addresses": [], "formula_addresses": [],
                "numeric_or_other_addresses_without_values": [], "type_counts": {}}
        dimension = root.find("s:dimension", ns)
        item["dimension"] = dimension.get("ref") if dimension is not None else None
        counter = Counter()
        for cell in root.findall(".//s:c", ns):
            kind, address = cell.get("t", "numeric"), cell.get("r")
            counter[kind] += 1
            if cell.find("s:f", ns) is not None:
                item["formula_addresses"].append(address)
                continue
            if kind == "s":
                index = cell.find("s:v", ns)
                value = strings[int(index.text)] if index is not None else None  # string index, not an outcome
            elif kind == "inlineStr":
                value = permitted("".join(t.text or "" for t in cell.findall(".//s:t", ns)))
            else:
                item["numeric_or_other_addresses_without_values"].append(address)
                continue  # no numeric v/text access
            if value is None:
                item["withheld_string_addresses"].append(address)
            else:
                item["approved_string_cells"].append({"address": address, "label": value})
        item["type_counts"] = dict(counter)
        item["merge_ranges"] = [e.get("ref") for e in root.findall(".//s:mergeCell", ns)]
        result["worksheets"].append(item)
    if "xl/styles.xml" in archive.namelist():
        styles = ET.fromstring(archive.read("xl/styles.xml"))
        result["custom_number_format_codes"] = [e.get("formatCode") for e in styles.findall(".//s:numFmt", ns)]
output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
