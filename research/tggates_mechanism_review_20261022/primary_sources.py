"""Outcome-blind primary literature receipts for the independent mechanism review."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification/advocate_sources"
OUT.mkdir(parents=True, exist_ok=True)
QUERIES = {
    "virtual_cell_recent": '"virtual cell" FIRST_PDATE:[2025-01-01 TO 2026-10-22]',
    "temporal_perturbation_recent": 'perturbation dynamics single-cell FIRST_PDATE:[2025-01-01 TO 2026-10-22]',
    "scnode": 'TITLE:"scNODE"',
    "cellflow": 'TITLE:"CellFlow"',
    "state": 'TITLE:"State predicts cellular responses"',
    "tggates_early_response": 'TITLE:"Data mining reveals a network of early-response genes"',
    "learned_optimizer": '(TITLE_ABS:"learned optimizer" OR TITLE_ABS:"learned optimisation") AND FIRST_PDATE:[2025-01-01 TO 2026-10-22]',
}
receipts = []
summary = {}
for name, query in QUERIES.items():
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode({
        "query": query, "format": "json", "resultType": "core", "pageSize": 50,
    })
    response = requests.get(url, timeout=45)
    target = OUT / (name + ".json")
    target.write_bytes(response.content)
    receipts.append({"name": name, "url": url, "status": response.status_code,
        "bytes": len(response.content), "sha256": hashlib.sha256(response.content).hexdigest(),
        "utc": datetime.now(timezone.utc).isoformat()})
    (OUT / "NETWORK.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    if response.status_code != 200:
        summary[name] = {"hit_count": None, "results": [], "error": "HTTP " + str(response.status_code)}
        continue
    obj = response.json()
    summary[name] = {"hit_count": obj.get("hitCount"), "results": [
        {k: item.get(k) for k in ("id", "source", "pmcid", "doi", "title", "firstPublicationDate", "authorString", "abstractText")}
        for item in obj.get("resultList", {}).get("result", [])
    ]}
(OUT / "SEARCH_SUMMARY.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
(OUT / "NETWORK.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
paper = ET.parse(ROOT / "log/20261022/tggates_source_qualification/PAPER.xml").getroot()
paragraphs = [" ".join(p.itertext()) for p in paper.iter("p")]
selected = [p for p in paragraphs if any(x in p.lower() for x in ("dose", "hepatocytes", "dna", "ldh", "viability", "2 h", "8 h", "24 h"))]
(OUT / "TGGATES_METHOD_EXCERPTS.json").write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
for name, result in summary.items():
    print(name, result["hit_count"])
    for item in result["results"][:12]:
        print(item["firstPublicationDate"], item["title"], item["doi"], item["pmcid"])
print("http_bytes", sum(x["bytes"] for x in receipts))
