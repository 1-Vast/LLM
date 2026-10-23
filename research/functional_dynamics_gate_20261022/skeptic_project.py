"""Project retained search metadata and primary method paragraphs offline."""
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

BASE = Path("D:/MAESTRO/log/20261022/functional_dynamics_gate/skeptic")

search = json.loads((BASE / "FUNCTIONAL_METHOD_SEARCH.body").read_bytes())
rows = [{k: row.get(k) for k in ["id", "source", "pmcid", "doi", "title",
        "firstPublicationDate", "abstractText"]} for row in search["resultList"]["result"]]
(BASE / "FUNCTIONAL_METHOD_SEARCH_PROJECTION.json").write_text(
    json.dumps({"hitCount": search["hitCount"], "results": rows}, indent=2,
               ensure_ascii=False), encoding="utf-8")
print(json.dumps({"hitCount": search["hitCount"], "results": rows}, ensure_ascii=False, indent=2))

class ParagraphParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = None
        self.parts = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag in ["h1", "h2", "h3", "h4", "p"]:
            self.active = {"tag": tag, "id": dict(attrs).get("id")}
            self.parts = []

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.active and tag == self.active["tag"]:
            self.rows.append({**self.active, "text": " ".join(" ".join(self.parts).split())})
            self.active = None


parser = ParagraphParser()
parser.feed((BASE / "SPECRSI_PRIMARY.body").read_text(encoding="utf-8"))
pattern = re.compile(r"GVO|VATS|reset|carry|same.state|rollout|improver|guidance|verified", re.I)
paragraphs = [row for row in parser.rows if pattern.search(row["text"])]
(BASE / "SPECRSI_METHOD_PROJECTION.json").write_text(
    json.dumps(paragraphs, indent=2, ensure_ascii=False), encoding="utf-8")
print("SpecRSI method projection paragraphs:", len(paragraphs))

root = ET.fromstring((BASE / "BESTDR_PRIMARY.body").read_bytes())
bestdr = []
for section in root.findall(".//body//sec"):
    title = " ".join("".join(section.find("title").itertext()).split()) if section.find("title") is not None else ""
    texts = [" ".join("".join(p.itertext()).split()) for p in section.findall("p")]
    if texts:
        bestdr.append({"section": title, "paragraphs": texts})
bestdr.append({"section": "Data availability / availability-related paragraphs",
               "paragraphs": [" ".join("".join(p.itertext()).split()) for p in root.findall(".//p")
                              if re.search(r"github|availability|zenodo", "".join(p.itertext()), re.I)]})
(BASE / "BESTDR_NARRATIVE_METHOD_PROJECTION.json").write_text(
    json.dumps(bestdr, indent=2, ensure_ascii=False), encoding="utf-8")
print("BESTDR narrative sections:", len(bestdr))
