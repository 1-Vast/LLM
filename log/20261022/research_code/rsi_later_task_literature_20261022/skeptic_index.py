"""Print/save compact primary discovery metadata; no peer drafts or AZ data."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[2] / "log/20261022/rsi_later_task_literature/skeptic"
stem = sys.argv[1]
path = BASE / (stem + ".body")
root = ET.fromstring(path.read_bytes())
ns = {"a": "http://www.w3.org/2005/Atom"}
entries = [{name: " ".join(e.findtext("a:" + name, namespaces=ns).split())
            for name in ("id", "title", "published", "updated", "summary")}
           for e in root.findall("a:entry", ns)]
(BASE / (stem + ".index.json")).write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
for entry in entries:
    print(entry["id"], entry["published"], entry["title"])
    print(entry["summary"][:700])
