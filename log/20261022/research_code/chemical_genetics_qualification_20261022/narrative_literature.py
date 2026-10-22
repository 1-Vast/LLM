"""Project deliberately exposed primary narrative; never read workbook cells."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/chemical_genetics_qualification"
source = OUT / "sources/PAPER.xml"
target = OUT / "NARRATIVE_LITERATURE.json"
if target.exists():
    raise FileExistsError(target)


def text(element):
    return " ".join(" ".join(element.itertext()).split()) if element is not None else ""


article = ET.parse(source).getroot()
body = article.find("body")
sections = []
narrative = []
for sec in body.findall("sec"):
    title = text(sec.find("title"))
    sections.append({"id": sec.get("id"), "title": title})
    if title.casefold() in {"results", "discussion"}:
        narrative.append({"title": title, "paragraphs": [text(p) for p in sec.iter("p")]})
result = {
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "scope": "DESIGN_EXPOSED_PUBLISHED_NARRATIVE_AND_FIGURE_CAPTIONS",
    "abstracts": [text(a) for a in article.findall("front/article-meta/abstract")],
    "body_section_headings": sections,
    "narrative": narrative,
    "figure_captions": [{"id": f.get("id"), "label": text(f.find("label")),
                         "caption": text(f.find("caption"))} for f in article.iter("fig")],
    "response_workbooks_opened": False,
    "new_http_requests": 0,
}
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"output": str(target), "sections": len(sections),
                  "narrative_sections": len(narrative),
                  "figure_captions": len(result["figure_captions"])}))
