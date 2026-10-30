"""Local text projections for source navigation; original files remain authoritative."""
from pathlib import Path
from html.parser import HTMLParser
import json
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent


class Blocks(HTMLParser):
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
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, text):
        if self.current:
            self.current["parts"].append(text)


out = {}
for name in ("p5_autorasor.html", "p6_atomistic_coupling.html"):
    parser = Blocks()
    parser.feed((HERE / "sources" / name).read_text(encoding="utf-8"))
    out[name] = parser.rows
    print(name)
    for i, row in enumerate(parser.rows):
        if row["tag"] != "p":
            print(i, row["id"], row["text"])
(HERE / "paragraphs.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
pdf = HERE / "sources/p7_multitask_probe.pdf"
assert pdf.read_bytes()[:5] == b"%PDF-"
pages = [{"page": i + 1, "text": page.extract_text()} for i, page in enumerate(PdfReader(pdf).pages)]
(HERE / "p7_text.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("p7_multitask_probe.pdf pages", len(pages))
