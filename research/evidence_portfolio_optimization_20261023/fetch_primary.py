"""Retain public primary-source bodies for the bounded portfolio review."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

OUT = Path("data/external/evidence_portfolio_optimization_20261023/primary_review")
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = {
    "eps_full.html": "https://arxiv.org/html/2609.26651v1",
    "proxy_full.html": "https://arxiv.org/html/2502.05715v2",
    "stopped_full.html": "https://arxiv.org/html/2502.08539v3",
    "sea_full.html": "https://arxiv.org/html/2607.00871v1",
    "cicd_icml.html": "https://icml.cc/virtual/2026/82618",
    "cicd_note.json": "https://api2.openreview.net/notes?id=4ob0d33A2l",
    "cicd_current.pdf": "https://openreview.net/pdf/c648a7f78bc07739748434607a0458242c4a99fd.pdf",
}
receipts = []
for name, url in SOURCES.items():
    started = datetime.now(timezone.utc).isoformat()
    try:
        response = requests.get(url, timeout=45)
        body = response.content
        (OUT / name).write_bytes(body)
        receipt = {"file": str(OUT / name), "url": url, "final_url": response.url,
                   "status": response.status_code, "content_type": response.headers.get("Content-Type"),
                   "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    except requests.RequestException as exc:
        receipt = {"file": name, "url": url, "error": str(exc)}
    receipt["started_utc"] = started
    receipt["ended_utc"] = datetime.now(timezone.utc).isoformat()
    receipts.append(receipt)
    print(json.dumps(receipt, ensure_ascii=True), flush=True)
(OUT / "RECEIPTS.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
