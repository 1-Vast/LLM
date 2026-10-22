"""Sequential, receipt-preserving, outcome-free literature/manifest acquisition."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_schedule_qualification/advocate_sources"
OUT.mkdir(parents=True, exist_ok=True)
ledger = OUT / "NETWORK.json"
receipts = json.loads(ledger.read_text(encoding="utf-8")) if ledger.exists() else []
if len(receipts) >= 3:
    raise RuntimeError("Registered three-request limit reached")
name, url = sys.argv[1:3]
target = OUT / name
if target.exists():
    raise FileExistsError("Refusing source overwrite before request")
response = requests.get(url, timeout=45)
target.write_bytes(response.content)
receipts.append({"name": name, "url": url, "status": response.status_code,
    "bytes": len(response.content), "sha256": hashlib.sha256(response.content).hexdigest(),
    "utc": datetime.now(timezone.utc).isoformat()})
ledger.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
print(response.status_code, len(response.content))
response.raise_for_status()
if name.endswith(".xml"):
    article = ET.fromstring(response.content)
    paragraphs = [" ".join(p.itertext()) for p in article.iter("p")]
    (OUT / "PAPER_TEXT.txt").write_text("\n\n".join(paragraphs), encoding="utf-8")
    for p in paragraphs:
        if any(token in p.lower() for token in ("data availability", "code availability", "deposited", "zenodo", "github", "figshare", "upon request", "data and code", "data are", "accession")):
            print(p[:6500])
    print("links", json.dumps([x.attrib for x in article.iter("ext-link")], ensure_ascii=False))
