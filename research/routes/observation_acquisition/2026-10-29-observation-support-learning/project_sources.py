"""Small standard-library primary-text projection; original response bytes remain authoritative."""
from pathlib import Path
from html.parser import HTMLParser
import json
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent


class Projector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.current, self.rows, self.headings, self.equations = [], None, [], [], []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "math" and attrs.get("display") == "block":
            self.equations.append({"id": attrs.get("id") or next((s[1] for s in reversed(self.stack) if s[1]), None),
                                   "alttext": attrs.get("alttext")})
        if tag in ("p", "h1", "h2", "h3", "h4") and self.current is None:
            locator = attrs.get("id") or next((s[1] for s in reversed(self.stack) if s[1]), None)
            self.current = {"tag": tag, "id": locator, "parts": []}
        if tag not in ("meta", "link", "img", "br", "hr", "input", "source", "wbr"):
            self.stack.append((tag, attrs.get("id")))

    def handle_endtag(self, tag):
        if self.current and tag == self.current["tag"]:
            row = {"id": self.current["id"], "text": " ".join("".join(self.current["parts"]).split())}
            (self.rows if tag == "p" else self.headings).append(row)
            self.current = None
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.current:
            self.current["parts"].append(data)


projection, headings, equations = {}, {}, {}
for name in ("p4_every_eval.html", "p5_active_multiple.html"):
    parser = Projector()
    parser.feed((HERE / "sources" / name).read_text(encoding="utf-8"))
    projection[name], headings[name] = parser.rows, parser.headings
    equations[name] = parser.equations
(HERE / "primary_projection.json").write_text(json.dumps(projection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(HERE / "headings.json").write_text(json.dumps(headings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(HERE / "equations.json").write_text(json.dumps(equations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
root = ET.parse(HERE / "sources/p3_drug_support_records.xml").getroot()
rows = []
for article in root.findall("PubmedArticle"):
    rows.append({"pmid": article.findtext("MedlineCitation/PMID"), "title": "".join(article.find(".//ArticleTitle").itertext()),
                 "ids": {x.get("IdType"): x.text for x in article.findall("PubmedData/ArticleIdList/ArticleId")},
                 "abstract": " ".join("".join(t.itertext()) for t in article.findall(".//AbstractText"))})
(HERE / "pubmed_candidates.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"headings": headings, "PubMed": [{k: r[k] for k in ("pmid", "title", "ids")} for r in rows]}, ensure_ascii=False, indent=2))
