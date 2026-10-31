"""One explicitly requested, receipt-bearing public HTTP attempt; no retries/redirects."""
import gzip
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
LEDGER = OUT / "http_receipts.jsonl"
LIMIT_ATTEMPTS = 10
LIMIT_BYTES = 8_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    url, stem = sys.argv[1:3]
    old = [json.loads(x) for x in LEDGER.read_text(encoding="utf-8").splitlines()] if LEDGER.exists() else []
    used = sum(x.get("completed_decoded_body_bytes", 0) for x in old)
    if len(old) >= LIMIT_ATTEMPTS or used >= LIMIT_BYTES:
        raise SystemExit("Declared HTTP allocation exhausted")
    origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
    last = [x for x in old if x["origin"] == origin]
    if last:
        time.sleep(max(0, 1.05 - (time.time() - last[-1]["finished_epoch"])))
    receipt = {"attempt": len(old) + 1, "url": url, "origin": origin,
               "started_utc": datetime.now(timezone.utc).isoformat(),
               "policy": "No retries; no automatic redirects; Accept-Encoding identity"}
    request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-independent-protocol-review/1.0", "Accept-Encoding": "identity"})
    response = None
    try:
        opener = urllib.request.build_opener(NoRedirect())
        try:
            response = opener.open(request, timeout=30)
        except urllib.error.HTTPError as error:
            response = error
        receipt["status"] = response.code
        receipt["headers"] = dict(response.headers.items())
        raw = response.read(LIMIT_BYTES - used + 1)
        raw_path = OUT / (stem + ".raw")
        raw_path.write_bytes(raw)
        receipt["raw_path"] = str(raw_path.relative_to(OUT))
        receipt["raw_bytes"] = len(raw)
        receipt["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        if len(raw) > LIMIT_BYTES - used:
            receipt["known_partial_raw_bytes"] = len(raw)
            receipt["error"] = "Body exceeded remaining allocation; response closed, completed decoded body unavailable"
        else:
            encoding = response.headers.get("Content-Encoding", "identity").lower()
            if encoding not in ("identity", "gzip", ""):
                receipt["error"] = "Unsupported content encoding; raw bytes preserved"
            else:
                body = gzip.decompress(raw) if encoding == "gzip" else raw
                receipt["completed_decoded_body_bytes"] = len(body)
                receipt["decoded_sha256"] = hashlib.sha256(body).hexdigest()
                decoded_path = OUT / (stem + ".body")
                decoded_path.write_bytes(body)
                receipt["decoded_path"] = str(decoded_path.relative_to(OUT))
    except Exception as error:
        receipt["error"] = type(error).__name__ + ": " + str(error)
    finally:
        if response is not None:
            response.close()
        receipt["finished_epoch"] = time.time()
        receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
        with LEDGER.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(receipt, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
