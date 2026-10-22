"""Bounded primary-source receipts only; never downloads biological matrices."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

BASE = Path(__file__).resolve().parents[2] / "log/20261022/renewal_application/advocate"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("name")
    p.add_argument("url")
    a = p.parse_args()
    BASE.mkdir(parents=True, exist_ok=True)
    ledger = BASE / "HTTP_RECEIPTS.jsonl"
    prior = ledger.read_text(encoding="utf-8").splitlines() if ledger.exists() else []
    if len(prior) >= 4 or (BASE / (a.name + ".body")).exists():
        raise SystemExit("cap_or_duplicate")
    record = {"attempt": len(prior) + 1, "name": a.name, "url": a.url,
              "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "max_bytes": 3145728, "timeout_seconds": 25,
              "redirects": False, "retries": 0}
    body = b""
    try:
        request = urllib.request.Request(a.url, headers={"User-Agent": "MAESTRO-source-qualification/1.0"})
        with urllib.request.build_opener(NoRedirect).open(request, timeout=25) as response:
            record.update(status=response.status, headers=dict(response.headers))
            body = response.read(3145729)
            record["truncated_at_cap"] = len(body) > 3145728
    except urllib.error.HTTPError as e:
        record.update(status=e.code, error=repr(e), headers=dict(e.headers))
        body = e.read(3145729)
        record["truncated_at_cap"] = len(body) > 3145728
    except Exception as e:
        record.update(status=None, error=repr(e))
    body = body[:3145728]
    (BASE / (a.name + ".body")).write_bytes(body)
    record.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    (BASE / (a.name + ".receipt.json")).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
