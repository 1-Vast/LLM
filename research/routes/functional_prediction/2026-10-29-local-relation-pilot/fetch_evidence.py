"""One bounded primary-source request; no automatic retry."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
import urllib.request

HERE = Path(__file__).resolve().parent


def fetch(name, url):
    ledger = HERE / "retrieval.jsonl"
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert len(rows) < 6
    assert name == Path(name).name and not any(r.get("name") == name or r.get("url") == url for r in rows)
    target = HERE / "sources" / name
    target.parent.mkdir(exist_ok=True)
    assert not target.exists()
    cap = min(8000000, 12000000 - sum(r.get("bytes", 0) for r in rows))
    assert cap > 0
    row = {"action": "primary_fetch", "name": name, "url": url, "started_utc": datetime.now(timezone.utc).isoformat(),
           "timeout_seconds": 30, "max_bytes": cap, "automatic_retries": 0}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-research/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(cap + 1)
            row.update(status=response.status, content_type=response.headers.get("Content-Type"), final_url=response.url)
        if len(body) > cap:
            raise ValueError("Body exceeds declared cap; not saved")
        target.write_bytes(body)
        row.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    except Exception as exc:
        row.update(error_type=type(exc).__name__, error=str(exc))
    with ledger.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    fetch(sys.argv[1], sys.argv[2])
