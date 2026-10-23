"""Project availability notes and source manifests from already acquired XML."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/chemical_genetics_qualification"
target = OUT / "AVAILABILITY_SOURCE_MANIFEST.json"
if target.exists():
    raise FileExistsError("Refusing projection overwrite")
article = ET.parse(OUT / "sources/PAPER.xml").getroot()
availability = []
for item in article.iter("notes"):
    if item.get("notes-type") in ("data-availability", "code-availability"):
        availability.append({"type": item.get("notes-type"), "text": " ".join(item.itertext()),
            "links": [link.attrib for link in item.iter("ext-link")]})
methods = []
for sec in article.iter("sec"):
    title = sec.find("title")
    if title is not None and " ".join(title.itertext()).strip() == "Methods":
        for child in sec.findall("sec"):
            title = child.find("title")
            methods.append({"heading": " ".join(title.itertext()) if title is not None else "",
                "paragraphs": [" ".join(p.itertext()) for p in child.findall("p")]})
reference_ids = set()
for item in article.iter("sec"):
    title = item.find("title")
    if title is not None and " ".join(title.itertext()).strip() == "Data sources and preprocessing":
        first = item.find("p")
        if first is not None:
            reference_ids.update(x.get("rid") for x in first.iter("xref") if x.get("ref-type") == "bibr")
references = [{"id": item.get("id"), "citation": " ".join(item.itertext())}
    for item in article.iter("ref") if item.get("id") in reference_ids]
manifests = []
for item in article.iter():
    if item.tag in ("supplementary-material", "media"):
        manifests.append({"tag": item.tag, "attributes": item.attrib,
            "label": item.findtext("label"), "title": item.findtext("caption/title"),
            "media": [m.attrib for m in item.iter("media")],
            "external_links": [m.attrib for m in item.iter("ext-link")]})
result = {"availability": availability, "methods_with_subheadings": methods,
    "chemical_genetics_prior_references": references, "supplementary_manifest_only": manifests,
    "results_body_or_measurement_tables_projected": False,
    "code_availability_note_found": any(item["type"] == "code-availability" for item in availability)}
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "methods_with_subheadings"}, ensure_ascii=False, indent=2))
