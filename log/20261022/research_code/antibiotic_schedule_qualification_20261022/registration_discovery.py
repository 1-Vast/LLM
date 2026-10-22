"""Two exact-DOI metadata queries, streamed under a combined body budget."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_schedule_qualification/registration_sources"
OUT.mkdir(parents=True, exist_ok=True)
ledger_path = OUT / "NETWORK.json"
if ledger_path.exists():
    raise FileExistsError("Refusing registered stage rerun")
doi = "10.1101/2025.10.30.684665"
queries = [
    ("DATACITE.json", "https://api.datacite.org/dois?" + urlencode({
        "query": f'relatedIdentifiers.relatedIdentifier:"{doi}" OR relatedIdentifiers.relatedIdentifier:"https://doi.org/{doi}"',
        "page[size]": 10})),
    ("ZENODO.json", "https://zenodo.org/api/records/?" + urlencode({
        "q": f'"{doi}"', "size": 10})),
]
receipts = []
total = 0
for name, url in queries:
    target = OUT / name
    if target.exists():
        raise FileExistsError("Refusing source overwrite before request")
    with requests.get(url, timeout=45, stream=True) as response:
        chunks = []
        truncated = False
        for chunk in response.iter_content(8192):
            remaining = 1_000_000 - total
            if len(chunk) > remaining:
                chunks.append(chunk[:remaining])
                total = 1_000_000
                truncated = True
                break
            chunks.append(chunk)
            total += len(chunk)
        body = b"".join(chunks)
        target.write_bytes(body)
        receipts.append({"name": name, "url": url, "status": response.status_code,
            "retained_body_bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
            "utc": datetime.now(timezone.utc).isoformat(), "body_truncated_at_budget": truncated})
        ledger_path.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
        print(name, response.status_code, len(body), "truncated", truncated)
        if response.status_code == 200 and not truncated:
            obj = json.loads(body)
            if name.startswith("DATACITE"):
                print("meta", json.dumps(obj.get("meta"), ensure_ascii=False))
                for item in obj.get("data", []):
                    at = item.get("attributes", {})
                    print(json.dumps({k: at.get(k) for k in ("doi", "titles", "url", "relatedIdentifiers", "types", "sizes", "formats")}, ensure_ascii=False))
            else:
                print("hits", json.dumps(obj.get("hits", {}).get("total"), ensure_ascii=False))
                for item in obj.get("hits", {}).get("hits", []):
                    print(json.dumps({"id": item.get("id"), "metadata": item.get("metadata"), "files": [{k: f.get(k) for k in ("key", "size", "type")} for f in item.get("files", [])]}, ensure_ascii=False))
        if total >= 1_000_000:
            break
print("retained_bytes", total)
