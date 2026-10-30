"""Explicit public-source fetch after the user's quantity-limit removal; no retry."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request

here = Path(__file__).resolve().parent / "sources/root"
tag, url = sys.argv[1:]
assert tag.replace("_", "").isalnum()
target = here / (tag + ".body")
assert not target.exists(), "Preserve every previous attempt; no silent replay"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


record = {"tag": tag, "url": url, "started_UTC": datetime.now(timezone.utc).isoformat(),
          "timeout_seconds": 45, "quantity_limit": None, "automatic_retries": 0,
          "automatic_redirects": 0, "authorization": "User: research and download quantity unlimited"}
with (here / "request_intents.jsonl").open("a", encoding="utf-8") as f:
    f.write(json.dumps(record) + "\n")
started = time.monotonic()
request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-public-research/1.0"})
try:
    response = urllib.request.build_opener(NoRedirect()).open(request, timeout=45)
except urllib.error.HTTPError as exc:
    response = exc
except Exception as exc:
    response = None
    record.update(status=None, error=type(exc).__name__ + ": " + str(exc))
digest = hashlib.sha256()
size = 0
with target.open("xb") as out:
    if response is not None:
        with response:
            record.update(status=response.code, content_type=response.headers.get("Content-Type"),
                          content_length=response.headers.get("Content-Length"),
                          redirect_target=response.headers.get("Location"))
            try:
                while chunk := response.read(1048576):
                    out.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            except Exception as exc:
                record["error"] = type(exc).__name__ + ": " + str(exc)
record.update(bytes=size, sha256=digest.hexdigest(), body_file=target.name,
              seconds=round(time.monotonic() - started, 3))
with (here / "retrieval.jsonl").open("a", encoding="utf-8") as f:
    f.write(json.dumps(record) + "\n")
print(json.dumps(record))
