"""One bounded public source request; no automatic redirects or retries."""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


parser = argparse.ArgumentParser()
parser.add_argument("url")
parser.add_argument("stem")
args = parser.parse_args()
base = Path(__file__).resolve().parent
out = base / "sources"
out.mkdir(exist_ok=True)
receipt_path = out / (args.stem + "_request.json")
if receipt_path.exists():
    raise SystemExit("Refusing to overwrite a completed or failed request receipt")
receipt = {
    "url": args.url,
    "started_utc": datetime.now(timezone.utc).isoformat(),
    "timeout_seconds": 25,
    "body_byte_limit": 4_000_000,
    "automatic_retries": 0,
    "automatic_redirects": False,
    "role": "Original-source discovery/qualification; not raw response data",
}
start = time.monotonic()
body = bytearray()
try:
    try:
        response = build_opener(NoRedirect()).open(
            Request(args.url, headers={"User-Agent": "MAESTRO-research/1.0"}), timeout=25
        )
    except HTTPError as exc:
        response = exc
    with response:
        receipt.update(status=response.code, content_type=response.headers.get("Content-Type"),
                       location=response.headers.get("Location"))
        while len(body) < receipt["body_byte_limit"] and time.monotonic() - start < 25:
            chunk = response.read(min(65536, receipt["body_byte_limit"] - len(body)))
            if not chunk:
                break
            body.extend(chunk)
        receipt["complete_body"] = len(body) < receipt["body_byte_limit"]
except Exception as exc:
    receipt["error"] = type(exc).__name__ + ": " + str(exc)
finally:
    receipt["known_body_bytes"] = len(body)
    receipt["elapsed_seconds"] = round(time.monotonic() - start, 3)
    (out / (args.stem + "_body.bin")).write_bytes(body)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    usage_path = base / "usage.json"
    usage = json.loads(usage_path.read_text(encoding="utf-8"))
    usage["coordinator_requests"].append({"receipt": str(receipt_path.relative_to(base)),
                                          "http_requests": 1, "known_body_bytes": len(body)})
    usage["new_logical_http_requests"] += 1
    usage["known_new_body_bytes_read"] += len(body)
    usage_path.write_text(json.dumps(usage, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt))
