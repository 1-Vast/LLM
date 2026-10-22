"""Expose only selected methods and availability from the saved primary HTML."""
import html
import json
import re
from pathlib import Path

BASE = Path("log/20261022/mechanism_gap/functional")


def plain(value):
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", value)).split())


if __name__ == "__main__":
    source = (BASE / "PMC10628994.pmc.html").read_text(encoding="utf-8")
    headings = list(re.finditer(r"<h[234][^>]*>.*?</h[234]>", source, re.S))
    active = False
    sections = {}
    for index, match in enumerate(headings):
        title = plain(match.group())
        if title == "Methods":
            active = True
        if title == "Extended Data":
            active = False
        if active or title in ("Data availability", "Code availability"):
            end = headings[index + 1].start()
            sections[title] = plain(source[match.end():end])
    (BASE / "FateMap2023.methods.json").write_text(
        json.dumps(sections, indent=2) + "\n", encoding="utf-8")
    selected = [
        "Drug treatment experiments", "Cell lines and culture",
        "Flow sorting of barcoded cells", "scRNA-seq",
        "Vemurafenib-resistant colony isolation and expansion",
        "Silencing plate cell culture, imaging and analysis",
        "Spheroid assay", "Data availability", "Code availability",
    ]
    print(json.dumps({key: sections.get(key) for key in selected}, indent=2))
