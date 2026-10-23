"""Project retained primary narrative only, never biological response arrays."""
import json
from pathlib import Path
import re
from html.parser import HTMLParser


class NarrativeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = []
        self.records = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in ("title", "h1", "h2", "h3", "p") or (
            tag == "blockquote" and "abstract" in attributes.get("class", "")
        ) or (tag == "div" and "dateline" in attributes.get("class", "")):
            self.active.append([tag, []])

    def handle_data(self, data):
        for _, pieces in self.active:
            pieces.append(data)

    def handle_endtag(self, tag):
        for index in range(len(self.active) - 1, -1, -1):
            if self.active[index][0] == tag:
                name, pieces = self.active.pop(index)
                self.records.append((name, " ".join(" ".join(pieces).split())))
                break


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "log/20261022/intervention_program_renewal/novelty_advocate/sources"
for stem in ("01_hyperagents", "02_aide2"):
    parser = NarrativeParser()
    parser.feed((SOURCE / f"{stem}.body").read_text(encoding="utf-8"))
    paragraphs = [content for tag, content in parser.records if tag != "title"]
    selected = [p for p in paragraphs if re.search(
        r"meta.agent|reset|held.out|cross.domain|recursive|self.improv|Submitted on", p, re.I)]
    projection = {"title": next(content for tag, content in parser.records if tag == "title"),
                  "paragraphs": paragraphs, "selected": selected,
                  "exposure": "Primary method/results narrative; no assay arrays"}
    (SOURCE / f"{stem}_PROJECTION.json").write_text(
        json.dumps(projection, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"source": stem, "title": projection["title"],
                      "selected_count": len(selected), "preview": selected[:12]}, ensure_ascii=False))
