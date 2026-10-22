"""Project retrieved primary metadata/HTML for bounded manual review."""
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/update_value_qualification/skeptic"


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        value = " ".join(data.split())
        if value:
            self.parts.append(value)


if __name__ == "__main__":
    name = sys.argv[1]
    body = (OUT / f"{name}.body").read_text(encoding="utf-8")
    if name.endswith("discovery"):
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entries = []
        for e in ET.fromstring(body).findall("a:entry", ns):
            entries.append({k: " ".join((e.findtext(f"a:{k}", default="", namespaces=ns)).split())
                            for k in ("id", "title", "published", "updated", "summary")})
        (OUT / f"{name}.projection.json").write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
        print(json.dumps([{k: e[k] for k in ("id", "title", "published")} for e in entries], indent=2))
    else:
        parser = Text()
        parser.feed(body)
        (OUT / f"{name}.projection.json").write_text(json.dumps(parser.parts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"name": name, "text_fragments": len(parser.parts)}))
