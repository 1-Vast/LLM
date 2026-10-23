"""Four-request public code/metadata discovery; no clone or numerical payload."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_schedule_qualification/code_discovery/sources"
OUT.mkdir(parents=True, exist_ok=True)
ledger_path = OUT / "NETWORK.json"
receipts = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
if len(receipts) >= 4:
    raise RuntimeError("Registered four-request limit reached")
name, url = sys.argv[1:3]
target = OUT / name
if target.exists():
    raise FileExistsError("Refusing output overwrite before request")
used = sum(item["retained_body_bytes"] for item in receipts)
remaining = 2_000_000 - used
if remaining <= 0:
    raise RuntimeError("Registered metadata body limit reached")
with requests.get(url, headers={"Accept": "application/vnd.github+json"}, timeout=45, stream=True) as response:
    body = response.raw.read(remaining, decode_content=True)
    complete = len(body) < remaining
    target.write_bytes(body)
    receipts.append({"name": name, "url": url, "status": response.status_code,
        "retained_body_bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
        "utc": datetime.now(timezone.utc).isoformat(), "complete_under_budget": complete})
    ledger_path.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    print(response.status_code, len(body), "complete_under_budget", complete)
    response.raise_for_status()
    if name.endswith(".json") and complete:
        obj = json.loads(body)
        if isinstance(obj, dict) and "items" in obj:
            print("total_count", obj.get("total_count"), "incomplete_results", obj.get("incomplete_results"))
            for item in obj["items"]:
                print(json.dumps({k: item.get(k) for k in ("full_name", "html_url", "description", "default_branch", "created_at", "updated_at", "size", "homepage")}, ensure_ascii=False))
        elif isinstance(obj, dict) and "tree" in obj:
            print("tree_sha", obj.get("sha"), "truncated", obj.get("truncated"), "entries", len(obj["tree"]))
            for item in obj["tree"]:
                print(json.dumps({k: item.get(k) for k in ("path", "type", "size", "sha")}, ensure_ascii=False))
        else:
            print(json.dumps(obj, ensure_ascii=False)[:18000])
