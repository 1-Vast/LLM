"""Derive inspectable text from captured public HTML, without fetching new pages."""
from pathlib import Path
from html.parser import HTMLParser
import sys


OUT = Path(__file__).resolve().parents[2] / "log/20261022/rsi_later_task_literature/data"
source = OUT / (sys.argv[1] + ".body")
target = OUT / (sys.argv[1] + ".txt")
if target.exists():
    raise RuntimeError("Derived text already exists")
class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if tag in ("p", "div", "section", "h1", "h2", "h3", "h4", "li", "tr"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden -= 1
        if tag in ("p", "div", "section", "h1", "h2", "h3", "h4", "li", "tr"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


parser = Text()
parser.feed(source.read_text(encoding="utf-8"))
target.write_text("\n".join(line.strip() for line in "".join(parser.parts).splitlines() if line.strip()), encoding="utf-8")
print(target)
