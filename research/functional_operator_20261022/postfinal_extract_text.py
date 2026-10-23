"""Extract readable publisher paragraphs without fetching assay supplements."""
from html.parser import HTMLParser
from pathlib import Path
import re


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_p = 0
        self.current = []
        self.lines = []

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "h1", "h2", "h3", "h4"):
            self.in_p += 1

    def handle_endtag(self, tag):
        if tag in ("p", "h1", "h2", "h3", "h4") and self.in_p:
            self.in_p -= 1
            if not self.in_p:
                text = " ".join("".join(self.current).split())
                if text:
                    self.lines.append(text)
                self.current = []

    def handle_data(self, data):
        if self.in_p:
            self.current.append(data)


base = Path("log/20261022/operator_renewal/functional/POSTFINAL_sources")
for name in ("chronos", "quantitative_microbiome"):
    parser = Paragraphs()
    parser.feed((base/(name+".html")).read_text(encoding="utf-8"))
    (base/(name+"_paragraphs.txt")).write_text("\n".join(parser.lines)+"\n", encoding="utf-8")
    html = (base/(name+".html")).read_text(encoding="utf-8")
    maths = re.findall(r'<span class="mathjax-tex">(.*?)</span>', html, re.S)
    (base/(name+"_equations.txt")).write_text("\n".join(maths)+"\n", encoding="utf-8")
