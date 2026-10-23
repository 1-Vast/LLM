"""Acquire exactly the registered official functional archive without parsing it."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification"
URL = "https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/open_tggates_cell_viability.zip"


def main():
    assert (OUT / "PROTOCOL.md").is_file()
    target = OUT / "sealed_source/open_tggates_cell_viability.zip"
    receipt = OUT / "NETWORK.json"
    if target.exists() or receipt.exists():
        raise RuntimeError("Acquisition already recorded; no overwrite or retry")
    target.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    record = {"url": URL, "cap_bytes": 2_000_000,
              "started_utc": datetime.now(timezone.utc).isoformat()}
    received = 0
    try:
        with requests.get(URL, stream=True, timeout=40) as response:
            record.update({"final_url": response.url, "status": response.status_code,
                           "headers": dict(response.headers)})
            parts = []
            for part in response.iter_content(16384):
                received += len(part)
                if received > record["cap_bytes"]:
                    raise RuntimeError("Response body cap exceeded")
                parts.append(part)
            response.raise_for_status()
            body = b"".join(parts)
            target.write_bytes(body)
            record["sha256"] = hashlib.sha256(body).hexdigest()
            record["archive_parsed"] = False
    except Exception as exc:
        record["failure_type"] = type(exc).__name__
        raise RuntimeError("Official archive acquisition failed; see receipt") from None
    finally:
        record.update({"received_body_bytes": received,
                       "receipt_utc": datetime.now(timezone.utc).isoformat(),
                       "wall_seconds": time.perf_counter() - start})
        receipt.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({k: record[k] for k in ["status", "received_body_bytes", "sha256", "archive_parsed"]}))


if __name__ == "__main__":
    main()
