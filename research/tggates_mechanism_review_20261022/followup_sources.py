"""Primary follow-up evidence; no experimental values are accessed."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification/advocate_sources"
requests_to_make = [
    ("time_warp_primary", "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode({
        "query": 'TITLE:"Aligning gene expression time series with time warping algorithms"',
        "format": "json", "resultType": "core", "pageSize": 5})),
    ("scNODE_FULL", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11373355/fullTextXML"),
    ("LCD_FULL", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13663777/fullTextXML"),
]
receipts = []
for name, url in requests_to_make:
    response = requests.get(url, timeout=45)
    suffix = ".json" if name.endswith("primary") else ".xml"
    (OUT / (name + suffix)).write_bytes(response.content)
    receipts.append({"name": name, "url": url, "status": response.status_code,
        "bytes": len(response.content), "sha256": hashlib.sha256(response.content).hexdigest(),
        "utc": datetime.now(timezone.utc).isoformat()})
    (OUT / "FOLLOWUP_NETWORK.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    print(name, response.status_code, len(response.content))
    if suffix == ".xml" and response.status_code == 200:
        article = ET.fromstring(response.content)
        paragraphs = [" ".join(p.itertext()) for p in article.iter("p")]
        selected = [p for p in paragraphs if any(s in p.lower() for s in (
            "time", "measurement", "noise", "identif", "dynamic", "linear", "learn"))]
        (OUT / (name + "_EXCERPTS.json")).write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
