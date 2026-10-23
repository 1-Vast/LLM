"""Identity-only source acquisition for an actual drug-order study."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_schedule_qualification/advocate_sources"
OUT.mkdir(parents=True, exist_ok=True)
stage = sys.argv[1]
network_path = OUT / "NETWORK.json"
receipts = json.loads(network_path.read_text(encoding="utf-8")) if network_path.exists() else []

def fetch(name, url):
    if len(receipts) >= 6:
        raise RuntimeError("Registered six-request limit reached")
    path = OUT / name
    if path.exists():
        raise FileExistsError("Refusing source overwrite")
    response = requests.get(url, timeout=40)
    path.write_bytes(response.content)
    receipts.append({"name": name, "url": url, "status": response.status_code,
        "bytes": len(response.content), "sha256": hashlib.sha256(response.content).hexdigest(),
        "utc": datetime.now(timezone.utc).isoformat()})
    network_path.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    response.raise_for_status()
    return response

if stage == "metadata":
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode({
        "query": "DOI:10.1016/j.cell.2012.03.031", "format": "json", "resultType": "core", "pageSize": 5})
    data = fetch("LEE_METADATA.json", url).json()
    for entry in data.get("resultList", {}).get("result", []):
        print(json.dumps({k: entry.get(k) for k in ("title", "pmcid", "id", "doi", "abstractText", "dataLinksTagsList")}, ensure_ascii=False))
elif stage == "fulltext":
    metadata = json.loads((OUT / "LEE_METADATA.json").read_text(encoding="utf-8"))
    pmcid = metadata["resultList"]["result"][0]["pmcid"]
    response = fetch("LEE_FULL.xml", f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML")
    article = ET.fromstring(response.content)
    paragraphs = [" ".join(p.itertext()) for p in article.iter("p")]
    (OUT / "LEE_TEXT.txt").write_text("\n\n".join(paragraphs), encoding="utf-8")
    for p in paragraphs:
        if any(token in p.lower() for token in ("accession", "omnibus", "deposited", "supplement", "geo", "microarray", "protein", "apoptosis", "sequential")):
            print(p[:4500])
    print("external_links", json.dumps([x.attrib for x in article.iter("ext-link")], ensure_ascii=False))
elif stage == "url":
    response = fetch(sys.argv[2], sys.argv[3])
    print(response.status_code, len(response.content))
else:
    raise ValueError("Unknown stage")
