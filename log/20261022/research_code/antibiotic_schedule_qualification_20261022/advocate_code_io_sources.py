"""Retrieve two pinned public source blobs for reading only, never execute them."""
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_schedule_qualification/code_io_followup/sources"
OUT.mkdir(parents=True, exist_ok=True)
ledger_path = OUT / "NETWORK.json"
if ledger_path.exists():
    raise FileExistsError("Refusing source retrieval stage rerun")
items = [
    ("COLONY", "f4a48f96172fa803d1506c505dd46dcb2b1499a8", 14280),
    ("CALCULATION", "4472a4bf24c001e66980755fb2b07cf9cb5d828f", 9694),
]
receipts = []
total = 0
for name, sha, size in items:
    target = OUT / (name + ".json")
    decoded = OUT / (name + ".m")
    if target.exists() or decoded.exists():
        raise FileExistsError("Refusing source overwrite before request")
    url = "https://api.github.com/repos/Uchicago-TAY/LIST/git/blobs/" + sha
    with requests.get(url, headers={"Accept": "application/vnd.github+json"}, timeout=45, stream=True) as response:
        limit = 100000 - total
        body = response.raw.read(limit, decode_content=True)
        total += len(body)
        complete = len(body) < limit
        target.write_bytes(body)
        receipt = {"name": name, "url": url, "status": response.status_code,
            "complete_response": complete, "body_bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
            "utc": datetime.now(timezone.utc).isoformat()}
        receipts.append(receipt)
        ledger_path.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
        response.raise_for_status()
        if not complete:
            raise RuntimeError("Source body reached budget; no decoding")
        obj = json.loads(body)
        source = base64.b64decode(obj["content"])
        computed = hashlib.sha1(b"blob " + str(len(source)).encode("ascii") + b"\0" + source).hexdigest()
        assert computed == obj["sha"] == sha
        assert len(source) == obj["size"] == size
        decoded.write_bytes(source)
        receipt.update({"decoded_bytes": len(source), "git_blob_sha_verified": computed,
            "decoded_sha256": hashlib.sha256(source).hexdigest(), "third_party_code_executed": False})
        ledger_path.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
        print(name, len(source), computed, "verified")
print("http_body_bytes", total)
