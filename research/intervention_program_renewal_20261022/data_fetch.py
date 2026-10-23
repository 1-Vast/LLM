"""Retain bounded, explicit metadata GETs for the functional-task audit."""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_program_renewal/data_auditor"
LIMIT = 8 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("url")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    attempts = list(OUT.glob("*_RECEIPT.json"))
    if len(attempts) >= 8:
        raise SystemExit("Eight-attempt cap reached")
    target = OUT / args.name
    if target.with_suffix(".body").exists():
        raise SystemExit("Refusing to replace a retained body")
    receipt = {"attempt": len(attempts) + 1, "url": args.url,
               "utc": datetime.now(timezone.utc).isoformat(),
               "timeout_seconds": 30, "body_cap_bytes": LIMIT,
               "automatic_redirects": False, "automatic_retries": False,
               "purpose": "Metadata or primary narrative; numerical outcome arrays prohibited"}
    start = time.monotonic()
    body = b""
    response = None
    try:
        req = urllib.request.Request(args.url, headers={"User-Agent": "MAESTRO-research-source-audit/1.0"})
        try:
            response = urllib.request.build_opener(NoRedirect).open(req, timeout=30)
        except urllib.error.HTTPError as error:
            response = error
        receipt.update(status=response.code, headers=dict(response.headers))
        body = response.read(LIMIT + 1)
        receipt["truncated"] = len(body) > LIMIT
        body = body[:LIMIT]
    except Exception as error:
        receipt["error"] = repr(error)
    finally:
        if response is not None:
            response.close()
        receipt.update(elapsed_seconds=time.monotonic() - start,
                       retained_bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        target.with_suffix(".body").write_bytes(body)
        target.with_name(target.name + "_RECEIPT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
