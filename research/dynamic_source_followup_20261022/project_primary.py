"""Project the selected paper's methods/availability without response tables."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/dynamic_source_followup/ncbi_scout"
target = OUT / "PRIMARY_METHODS_AVAILABILITY.json"
if target.exists():
    raise FileExistsError("Refusing projection overwrite")
article = ET.parse(OUT / "PRIMARY.xml").getroot()
def text(node):
    return " ".join(node.itertext()).strip() if node is not None else ""
headings = [{"title": text(sec.find("title")), "type": sec.get("sec-type")}
            for sec in article.iter("sec")]
methods = []
for section in article.iter("sec"):
    title = text(section.find("title"))
    if section.get("sec-type") == "methods" or title.casefold() in ("methods", "materials and methods"):
        for sec in section.iter("sec"):
            methods.append({"title": text(sec.find("title")),
                "paragraphs": [text(p) for p in sec.findall("p")]})
availability = []
for node in article.iter():
    if node.tag in ("custom-meta", "notes", "fn", "sec"):
        label = " ".join((node.get("notes-type", ""), node.get("fn-type", ""),
                          node.get("sec-type", ""), text(node.find("meta-name")),
                          text(node.find("title"))))
        if any(term in label.casefold() for term in ("data availability", "data-availability", "code availability", "code-availability")):
            availability.append({"tag": node.tag, "label": label.strip(), "text": text(node),
                "links": [link.attrib for link in node.iter("ext-link")]})
manifest = [{"id": node.get("id"), "label": text(node.find("label")),
    "caption": text(node.find("caption")), "attributes": node.attrib,
    "media": [item.attrib for item in node.iter("media")],
    "links": [item.attrib for item in node.iter("ext-link")]}
    for node in article.iter("supplementary-material")]
result = {"headings": headings, "methods": methods, "availability": availability,
          "supplementary_manifest": manifest, "response_table_arrays_projected": False}
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"headings": headings, "availability": availability,
                  "supplementary_manifest": manifest}, ensure_ascii=False, indent=2))
