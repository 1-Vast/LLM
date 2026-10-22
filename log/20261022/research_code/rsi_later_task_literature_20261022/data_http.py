"""Capture public primary-source HTTP pages and explicit receipts; no authentication."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import requests


OUT = Path(__file__).resolve().parents[2] / "log/20261022/rsi_later_task_literature/data"


def fetch(name, url):
    OUT.mkdir(parents=True, exist_ok=True)
    body_path = OUT / (name + ".body")
    meta_path = OUT / (name + ".http.json")
    if body_path.exists() or meta_path.exists():
        raise RuntimeError("Existing HTTP capture cannot be overwritten")
    receipt = {"started_utc": datetime.now(timezone.utc).isoformat(), "requested_url": url, "authentication": "none"}
    try:
        response = requests.get(url, timeout=45, headers={"User-Agent": "ResearchSourceAudit/1.0"})
        body = response.content
        body_path.write_bytes(body)
        receipt.update(status=response.status_code, final_url=response.url,
                       content_type=response.headers.get("Content-Type"), bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest(), body_file=body_path.name)
    except requests.RequestException as error:
        receipt.update(status=None, exception_type=type(error).__name__)
    receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
    meta_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    fetch(sys.argv[1], sys.argv[2])
