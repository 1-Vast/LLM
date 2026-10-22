"""Read only existing public publisher links/captions; no assay-value parsing."""
from html.parser import HTMLParser
import json
from pathlib import Path


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.current = [dict(attrs).get("href", ""), ""]

    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


parser = Links()
source = Path("log/20261022/native_operation/biology/nature.txt")
parser.feed(source.read_text(encoding="utf-8"))
selected = [{"href": href, "label": label.strip()} for href, label in parser.links
            if "MOESM" in href or "source data" in label.lower()]
out = Path("log/20261022/operator_renewal/functional/existing_author_links.json")
out.write_text(json.dumps(selected, indent=2)+"\n", encoding="utf-8")
print(json.dumps(selected, indent=2))
