"""Retain capped public method-source responses; never open functional datasets."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification/dose_sources"
DOMAINS = {"www.ncbi.nlm.nih.gov", "pmc.ncbi.nlm.nih.gov", "www.ebi.ac.uk",
           "academic.oup.com", "oup.silverchair-cdn.com", "toxico.nibiohn.go.jp",
           "dbarchive.biosciencedbc.jp", "europepmc.org", "ftp.ncbi.nlm.nih.gov"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("name")
    args = parser.parse_args()
    if urlparse(args.url).hostname not in DOMAINS or any(s in args.url.lower() for s in ["cell_viability", ".cel"]):
        raise ValueError("URL outside methods scope")
    if Path(args.name).name != args.name:
        raise ValueError("Output must be a basename")
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / args.name
    if target.exists():
        raise ValueError("Retained source already exists")
    ledger_path = OUT / "NETWORK.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"requests": [], "body_bytes": 0}
    if len(ledger["requests"]) >= 12:
        raise RuntimeError("Methods request bound reached")
    record = {"url": args.url, "utc": datetime.now(timezone.utc).isoformat()}
    start = time.perf_counter()
    body = bytearray()
    try:
        with requests.get(args.url, timeout=35, stream=True) as response:
            record.update({"status": response.status_code, "final_url": response.url,
                           "content_type": response.headers.get("Content-Type"),
                           "etag": response.headers.get("ETag")})
            for chunk in response.iter_content(16384):
                ledger["body_bytes"] += len(chunk)
                if ledger["body_bytes"] > 5_000_000:
                    raise RuntimeError("Methods body bound exceeded")
                body.extend(chunk)
            target.write_bytes(body)
            record.update({"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
            response.raise_for_status()
    except Exception as exc:
        record["failure_type"] = type(exc).__name__
        raise
    finally:
        record["seconds"] = time.perf_counter() - start
        ledger["requests"].append(record)
        ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    print(json.dumps(record))


if __name__ == "__main__":
    main()
