"""Local paragraph/heading projection only; originals remain the evidence."""
from pathlib import Path
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
import json

HERE = Path(__file__).resolve().parent


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.rows, self.current = [], [], None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("p", "h1", "h2", "h3", "h4") and self.current is None:
            self.current = {"tag": tag, "id": attrs.get("id") or next((s[1] for s in reversed(self.stack) if s[1]), None), "parts": []}
        if tag not in ("meta", "link", "img", "br", "hr", "input", "source", "wbr"):
            self.stack.append((tag, attrs.get("id")))

    def handle_endtag(self, tag):
        if self.current and tag == self.current["tag"]:
            self.rows.append({"tag": tag, "id": self.current["id"], "text": " ".join("".join(self.current["parts"]).split())})
            self.current = None
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, text):
        if self.current:
            self.current["parts"].append(text)


out = {}
for name in ("p4_hiddenkinematics.html", "p7_physcap.html"):
    parser = Paragraphs()
    parser.feed((HERE / "sources" / name).read_text(encoding="utf-8"))
    out[name] = parser.rows
for name in ("p5_bchem.xml", "p6_regformer.xml"):
    root = ET.parse(HERE / "sources" / name).getroot()
    rows = []
    for sec in root.findall(".//sec"):
        if sec.find("title") is not None:
            rows.append({"tag": "h", "id": sec.get("id"), "text": " ".join("".join(sec.find("title").itertext()).split())})
        for i, para in enumerate(sec.findall("p")):
            rows.append({"tag": "p", "id": f"{sec.get('id')}.p{i+1}", "text": " ".join("".join(para.itertext()).split())})
    out[name] = rows
(HERE / "paragraphs.json").write_text(json.dumps(out, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
for name, rows in out.items():
    print(name, "paragraphs", sum(r["tag"] == "p" for r in rows))
    for i, row in enumerate(rows):
        if row["tag"] != "p":
            print(i, row["id"], row["text"])
