"""Project primary methods, availability and withdrawal-design prose only."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_dynamics_renewal/advocate"
target = OUT / "PRIMARY_METHODS_DESIGN.json"
if target.exists():
    raise FileExistsError("Refusing projection overwrite")
article = ET.parse(OUT / "PRIMARY.xml").getroot()
def tx(node):
    return " ".join(node.itertext()).strip() if node is not None else ""
methods = []
availability = []
headings = []
for sec in article.iter("sec"):
    title = tx(sec.find("title"))
    headings.append(title)
    if title.casefold() in ("star★methods", "star methods", "methods", "materials and methods") or sec.get("sec-type", "") in ("methods", "materials|methods"):
        for item in sec.iter("sec"):
            methods.append({"title": tx(item.find("title")),
                            "paragraphs": [tx(p) for p in item.findall("p")]})
    if any(x in title.casefold() for x in ("data and code", "data availability", "code availability", "resource availability")):
        availability.append({"title": title, "text": tx(sec),
                             "links": [link.attrib for link in sec.iter("ext-link")]})
design = []
for sec in article.iter("sec"):
    title = tx(sec.find("title"))
    if any(x in title.casefold() for x in ("revers", "withdraw", "switch", "model")):
        design.append({"title": title, "paragraphs": [tx(p) for p in sec.findall("p")]})
manifest = [{"id": x.get("id"), "label": tx(x.find("label")), "caption": tx(x.find("caption")),
             "media": [m.attrib for m in x.iter("media")]}
            for x in article.iter("supplementary-material")]
result = {"scope": "PUBLISHED_METHODS_AVAILABILITY_DESIGN_EXPOSED", "headings": headings,
          "methods": methods, "availability": availability,
          "withdrawal_model_design": design, "supplementary_manifest": manifest,
          "response_table_arrays_projected": False}
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
