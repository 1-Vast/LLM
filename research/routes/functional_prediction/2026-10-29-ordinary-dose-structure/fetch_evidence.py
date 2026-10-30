"""Bounded public-source retrieval; one receipt per attempt and no automatic retry."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import urllib.request

HERE = Path(__file__).resolve().parent


def fetch(name, url, query=False):
    ledger = HERE / "retrieval.jsonl"
    rows = [json.loads(s) for s in ledger.read_text(encoding="utf-8").splitlines()] if ledger.exists() else []
    assert len(rows) < 8 and sum(bool(r["query"]) for r in rows) + query <= 2
    assert name == Path(name).name and not any(r["name"] == name or r["url"] == url for r in rows)
    target = HERE / "sources" / name
    target.parent.mkdir(exist_ok=True)
    assert not target.exists()
    limit = min(8_000_000, 20_000_000 - sum(r.get("bytes", 0) for r in rows))
    assert limit > 0
    row = {"name": name, "url": url, "query": bool(query), "retries": 0,
           "started_utc": datetime.now(timezone.utc).isoformat(), "timeout_seconds": 30,
           "max_bytes": limit}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-research/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(limit + 1)
            row.update(status=response.status, content_type=response.headers.get("Content-Type"), final_url=response.url)
        if len(body) > limit:
            row["discarded_prefix_bytes"] = len(body)
            raise ValueError("Acquisition size cap exceeded; prefix not saved")
        target.write_bytes(body)
        row.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    except Exception as exc:
        row.update(error_type=type(exc).__name__, error=str(exc))
    with ledger.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    fetch(sys.argv[1], sys.argv[2], sys.argv[3:] == ["--query"])
