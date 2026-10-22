"""Inspect only downloaded public literature bodies, never experiment artifacts."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/rsi_later_task_literature/advocate"


if __name__ == "__main__":
    result = {}
    if "--versions" in sys.argv:
        atom = ET.fromstring((OUT / "discovery_versions.body").read_bytes())
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for e in atom.findall("a:entry", ns):
            print(json.dumps({k: e.findtext("a:" + k, namespaces=ns) for k in ("id", "title", "published", "updated")}))
        raise SystemExit(0)
    atom = ET.fromstring((OUT / "discovery_arxiv.body").read_bytes())
    ns = {"a": "http://www.w3.org/2005/Atom"}
    result["arxiv"] = [{k: e.findtext("a:" + k, namespaces=ns) for k in ("id", "title", "published", "updated", "summary")}
                       for e in atom.findall("a:entry", ns)]
    data = json.loads((OUT / "discovery_openalex.body").read_bytes())
    result["openalex"] = [{k: r.get(k) for k in ("title", "publication_date", "doi", "primary_location")}
                          for r in data["results"]]
    (OUT / "DISCOVERY_INDEX.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    for source, rows in result.items():
        print(source)
        for r in rows:
            print(json.dumps({k: v for k, v in r.items() if k != "summary" and k != "primary_location"}))
