"""Serial, capped retrieval of explicitly requested TG-GATEs metadata sources."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_source_qualification"
CAP = 2_000_000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("name")
    args = parser.parse_args()
    if Path(args.name).name != args.name:
        raise ValueError("Source name must be a basename")
    if not args.url.startswith(("https://dbarchive.biosciencedbc.jp/", "https://www.ebi.ac.uk/europepmc/", "https://pmc.ncbi.nlm.nih.gov/", "https://www.nature.com/", "https://static-content.springer-cdn.com/")):
        raise ValueError("Unapproved source domain")
    if "viab" in args.url.lower() or args.url.lower().endswith(".cel"):
        raise ValueError("Endpoint and CEL payloads prohibited")
    target = OUT / args.name
    if target.exists():
        raise ValueError("Existing source must not be overwritten")
    ledger_path = OUT / "NETWORK.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"cap": CAP, "body_bytes": 0, "requests": []}
    start = time.perf_counter()
    chunks = []
    record = {"url": args.url}
    try:
        with requests.get(args.url, timeout=40, stream=True) as response:
            record.update({"final_url": response.url, "status": response.status_code,
                           "content_type": response.headers.get("Content-Type"), "etag": response.headers.get("ETag")})
            for chunk in response.iter_content(16384):
                ledger["body_bytes"] += len(chunk)
                if ledger["body_bytes"] > CAP:
                    raise RuntimeError("Metadata response body cap exceeded")
                chunks.append(chunk)
            body = b"".join(chunks)
            record.update({"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
            target.write_bytes(body)
            response.raise_for_status()
    except Exception as exc:
        record["failure"] = str(exc)
        raise
    finally:
        record["wall_seconds"] = time.perf_counter() - start
        ledger["requests"].append(record)
        ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    print(json.dumps(record))


if __name__ == "__main__":
    main()
