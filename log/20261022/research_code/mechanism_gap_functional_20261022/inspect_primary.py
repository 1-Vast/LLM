"""Acquire one primary article and extract design-only sections, not results."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from search_sources import BASE, request


def content(node):
    return " ".join("".join(node.itertext()).split())


if __name__ == "__main__":
    article = "PMC10628994"
    path = BASE / (article + ".xml")
    receipt = request(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/"
        + article + "/fullTextXML", path)
    (BASE / (article + ".receipt.json")).write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if receipt.get("status") != 200:
        raise SystemExit(receipt)
    root = ET.fromstring(path.read_bytes())
    sections = []
    for node in root.findall(".//sec"):
        title = node.find("title")
        if title is not None:
            sections.append({"id": node.get("id"), "title": content(title)})
    (BASE / (article + ".section_index.json")).write_text(
        json.dumps(sections, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": receipt, "sections": sections}, indent=2))
