"""Print one bounded original-HTML section; no network or third-party parser."""
import sys
from html.parser import HTMLParser
from pathlib import Path


class SectionReader(HTMLParser):
    def __init__(self, section):
        super().__init__()
        self.section = section
        self.depth = 0
        self.active = False
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "section":
            if self.active:
                self.depth += 1
            elif attributes.get("id") == self.section:
                self.active, self.depth = True, 1

    def handle_data(self, data):
        if self.active:
            self.chunks.append(data)

    def handle_endtag(self, tag):
        if tag == "section" and self.active:
            self.depth -= 1
            if self.depth == 0:
                self.active = False


path, section = Path(sys.argv[1]), sys.argv[2]
parser = SectionReader(section)
parser.feed(path.read_text(encoding="utf-8"))
text = " ".join(" ".join(parser.chunks).split())
start, length = (int(sys.argv[3]) if len(sys.argv) > 3 else 0), (int(sys.argv[4]) if len(sys.argv) > 4 else 6000)
print(f"path={path}; section={section}; total_characters={len(text)}; start={start}")
print(text[start:start+length])
print(f"next_start={start+length if start+length < len(text) else None}")
