"""Create a local reading aid; originals and their HTML IDs remain authoritative."""
from html.parser import HTMLParser
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent


class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.rows, self.links, self.meta, self.maths = [], [], [], [], []
        self.capture, self.parts, self.identifier = None, [], ""
        self.skip_math = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            self.meta.append(attrs)
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "math":
            self.maths.append({"id": next((a.get("id") for _, a in reversed(self.stack) if a.get("id")), ""),
                               "alttext": attrs.get("alttext", "")})
            if self.capture and attrs.get("alttext"):
                self.parts.append(" "+attrs["alttext"]+" ")
            self.skip_math += 1
        if tag in ("p", "h1", "h2", "h3", "h4") and not self.capture:
            self.capture, self.parts = tag, []
            self.identifier = attrs.get("id") or next((a.get("id") for _, a in reversed(self.stack) if a.get("id")), "")
        if tag not in ("meta", "link", "img", "br", "hr", "input", "source", "wbr"):
            self.stack.append((tag, attrs))

    def handle_endtag(self, tag):
        if tag == "math":
            self.skip_math = max(0, self.skip_math-1)
        if tag == self.capture:
            self.rows.append({"id": self.identifier, "tag": tag, "text": " ".join("".join(self.parts).split())})
            self.capture, self.parts = None, []
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data):
        if self.capture and not self.skip_math:
            self.parts.append(data)


if __name__ == "__main__":
    result = []
    for path in sorted((HERE / "sources").glob("p*.html")):
        parser = Reader()
        parser.feed(path.read_text(encoding="utf-8"))
        result.append({"file": path.name, "rows": parser.rows, "meta": parser.meta, "maths": parser.maths,
                       "links": sorted(set(parser.links))})
        print(json.dumps({"file": path.name, "rows": len(parser.rows),
              "headings": [r for r in parser.rows if r["tag"] != "p"][:22],
              "code_links": [s for s in parser.links if "github.com" in s]}, ensure_ascii=False))
    (HERE / "reading_extracts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
