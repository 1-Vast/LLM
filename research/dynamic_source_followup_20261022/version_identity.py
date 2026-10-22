"""One explicitly authorized official version metadata GET; no file requests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/dynamic_source_followup/ncbi_scout/version_followup"
OUT.mkdir(parents=True, exist_ok=True)
ledger = OUT / "NETWORK.json"
target = OUT / "RECORD.json"
if ledger.exists() or target.exists():
    raise FileExistsError("Registered one request already attempted or source exists")
url = "https://zenodo.org/api/records/14064964"
receipt = {"url": url, "started_utc": datetime.now(timezone.utc).isoformat(),
           "cap_bytes": 3000000, "parent_status": 302,
           "parent_url": "https://zenodo.org/api/records/14064963"}
try:
    with requests.get(url, timeout=50, stream=True, allow_redirects=False) as response:
        body = response.raw.read(3000000, decode_content=True)
        target.write_bytes(body)
        receipt.update(status=response.status_code, body_bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
            complete_under_cap=len(body) < 3000000,
            location=response.headers.get("Location"))
except Exception as exc:
    receipt["exception"] = {"type": type(exc).__name__, "message": str(exc)}
finally:
    receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
    ledger.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt))
if receipt.get("status") != 200 or not receipt.get("complete_under_cap"):
    raise RuntimeError("Failure/redirect/cap reached; do not retry")
obj = json.loads(body)
metadata = obj.get("metadata", {})
projection = {"id": obj.get("id"), "doi": obj.get("doi"),
    "conceptdoi": obj.get("conceptdoi"), "conceptrecid": obj.get("conceptrecid"),
    "title": metadata.get("title"), "version": metadata.get("version"),
    "description_source_design_exposed": metadata.get("description"),
    "related_identifiers": metadata.get("related_identifiers"),
    "license": metadata.get("license"), "access_right": metadata.get("access_right"),
    "files": [{key: item.get(key) for key in ("key", "size", "checksum", "links")}
              for item in obj.get("files", [])], "links": obj.get("links")}
(OUT / "MANIFEST.json").write_text(
    json.dumps(projection, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(projection, ensure_ascii=False, indent=2))
