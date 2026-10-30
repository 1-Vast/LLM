"""Bounded, dependency-free reading of stored original HTML."""
import argparse
import csv
from html.parser import HTMLParser
from pathlib import Path


class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.sections, self.headings = [], {}, []
        self.heading = None
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag in ("script", "style"):
            self.ignored += 1
        if tag == "section":
            key = data.get("id", "unnamed")
            self.stack.append(key)
            self.sections.setdefault(key, [])
        if tag in ("h1", "h2", "h3", "h4"):
            self.heading = [self.stack[-1] if self.stack else "document", tag, []]

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.ignored = max(0, self.ignored - 1)
        if tag == "section" and self.stack:
            self.stack.pop()
        if tag in ("h1", "h2", "h3", "h4") and self.heading:
            self.headings.append((self.heading[0], self.heading[1], " ".join(self.heading[2])))
            self.heading = None

    def handle_data(self, value):
        if self.ignored or not value.strip():
            return
        value = value.strip()
        if self.heading:
            self.heading[2].append(value)
        for key in self.stack:
            self.sections[key].append(value)


parser = argparse.ArgumentParser()
parser.add_argument("paper_id")
parser.add_argument("--section")
parser.add_argument("--start", type=int, default=0)
parser.add_argument("--limit", type=int, default=3500)
args = parser.parse_args()
root = Path(r"D:\MAESTRO\reference")
row = next(row for row in csv.DictReader((root / "papers.tsv").open(encoding="utf-8"), delimiter="\t") if row["paper_id"] == args.paper_id and row["local_path"])
reader = Reader()
reader.feed((root / row["local_path"]).read_text(encoding="utf-8"))
print(args.paper_id, row["sha256"][:12], row["local_path"])
if args.section is None:
    for key, tag, title in reader.headings:
        print(key, tag, title)
else:
    text = " ".join(reader.sections[args.section])
    print("section", args.section, "total_chars", len(text), "start", args.start)
    print(text[args.start:args.start + args.limit])
