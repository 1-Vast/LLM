"""Acquire the exact primary XML, projecting methods/availability only."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/chemical_genetics_qualification"
SRC = OUT / "sources"
SRC.mkdir(parents=True, exist_ok=True)
ledger_path = SRC / "NETWORK.json"
receipts = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
if len(receipts) >= 2:
    raise RuntimeError("Registered two-request limit reached")
name, url = sys.argv[1:3]
target = SRC / name
if target.exists():
    raise FileExistsError("Refusing source overwrite before request")
limit = 2_000_000 - sum(x["body_bytes"] for x in receipts)
if limit <= 0:
    raise RuntimeError("Registered response body budget reached")
with requests.get(url, timeout=50, stream=True) as response:
    body = response.raw.read(limit, decode_content=True)
    target.write_bytes(body)
    complete = len(body) < limit
    receipts.append({"name": name, "url": url, "status": response.status_code,
        "body_bytes": len(body), "complete_under_budget": complete,
        "sha256": hashlib.sha256(body).hexdigest(), "utc": datetime.now(timezone.utc).isoformat()})
    ledger_path.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    print(response.status_code, len(body), "complete", complete)
    response.raise_for_status()
    if not complete:
        raise RuntimeError("Response reached budget; no parsing")
if name.endswith(".xml"):
    article = ET.fromstring(body)
    allowed = []
    links = []
    for sec in article.iter("sec"):
        title = sec.find("title")
        heading = " ".join(title.itertext()) if title is not None else ""
        sec_type = sec.get("sec-type", "")
        if any(token in (heading + " " + sec_type).casefold() for token in ("method", "data avail", "code avail", "data and code")):
            paragraphs = []
            for child in sec.iter("p"):
                paragraphs.append(" ".join(child.itertext()))
                links.extend(x.attrib for x in child.iter("ext-link"))
            allowed.append({"heading": heading, "sec_type": sec_type, "paragraphs": paragraphs})
    (OUT / "METHODS_AVAILABILITY.json").write_text(json.dumps(allowed, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "METHODS_AVAILABILITY_LINKS.json").write_text(json.dumps(links, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(allowed, ensure_ascii=False, indent=2))
    print("links", json.dumps(links, ensure_ascii=False))
else:
    obj = json.loads(body)
    metadata = obj.get("metadata", {})
    projection = {
        "id": obj.get("id"), "doi": obj.get("doi"),
        "title": metadata.get("title"),
        "creators": metadata.get("creators"),
        "related_identifiers": metadata.get("related_identifiers"),
        "license": metadata.get("license"),
        "access_right": metadata.get("access_right"),
        "files": [{key: item.get(key) for key in
                   ("key", "size", "checksum", "type", "links")}
                  for item in obj.get("files", [])],
        "links": obj.get("links"),
    }
    (OUT / "ZENODO_MANIFEST.json").write_text(
        json.dumps(projection, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(projection, ensure_ascii=False, indent=2))
