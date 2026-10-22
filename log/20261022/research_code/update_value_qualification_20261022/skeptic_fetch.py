"""Bounded primary-source retrieval; no biological data or model execution."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/update_value_qualification/skeptic"


def fetch(name, url):
    OUT.mkdir(parents=True, exist_ok=True)
    ledger = OUT / "HTTP_RECEIPTS.jsonl"
    prior = ledger.read_text(encoding="utf-8").splitlines() if ledger.exists() else []
    if len(prior) >= 4 or (OUT / f"{name}.body").exists():
        raise RuntimeError("Four-GET bound or immutable source-name conflict")
    receipt = {"utc": datetime.now(timezone.utc).isoformat(), "name": name, "url": url,
               "request_index": len(prior) + 1, "status": None, "error": None}
    body = b""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-research-review/1.0"})
        try:
            response = urllib.request.urlopen(req, timeout=35)
        except urllib.error.HTTPError as error:
            response = error
            receipt["error"] = f"HTTPError: {error.code}"
        with response:
            receipt.update(status=response.status, final_url=response.url,
                           content_type=response.headers.get("Content-Type"))
            body = response.read(4 * 1024 * 1024 + 1)
            receipt["body_complete"] = len(body) <= 4 * 1024 * 1024
    except Exception as error:
        receipt.update(error=f"{type(error).__name__}: {error}", body_complete=False)
    (OUT / f"{name}.body").write_bytes(body)
    receipt.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    (OUT / f"{name}.receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("url")
    args = parser.parse_args()
    fetch(args.name, args.url)
