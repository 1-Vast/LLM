"""One scoped primary-source request, measured bytes, no retries or redirects."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

folder = Path(__file__).resolve().parent / "sources"
folder.mkdir(exist_ok=True)
tag, url = sys.argv[1:]
assert tag.replace("_", "").isalnum()
target = folder / f"{tag}.body"
assert not target.exists(), "No automatic replay"
ledger = folder / "retrieval.jsonl"
prior = [json.loads(s) for s in ledger.read_text(encoding="utf-8").splitlines()] if ledger.exists() else []
assert len(prior) < 8
used = sum(r["bytes"] for r in prior if r.get("status") == 200)
remaining = 20_000_000 - used
assert remaining > 0
for r in reversed(prior):
    if urllib.parse.urlsplit(r["url"]).netloc == urllib.parse.urlsplit(url).netloc:
        ended = datetime.fromisoformat(r["started_utc"]).timestamp() + r["seconds"]
        time.sleep(max(0, ended + 1.1 - time.time()))
        break


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


record = {"tag": tag, "url": url, "started_utc": datetime.now(timezone.utc).isoformat(),
          "timeout_seconds": 30, "automatic_retries": 0, "automatic_redirects": False}
started = time.monotonic()
request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-public-research/1.0"})
response, body = None, b""
try:
    response = urllib.request.build_opener(NoRedirect()).open(request, timeout=30)
except urllib.error.HTTPError as exc:
    response = exc
except Exception as exc:
    record.update(status=None, error=type(exc).__name__ + ": " + str(exc))
if response is not None:
    with response:
        cap = min(10_000_000, remaining)
        body = response.read(cap + 1)
        record.update(status=response.code, content_type=response.headers.get("Content-Type"),
                      location=response.headers.get("Location"))
    if len(body) > cap:
        body = body[:cap]
        record["error"] = "Body cap exceeded; saved prefix inadmissible"
target.write_bytes(body)
record.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), body_file=target.name,
              seconds=time.monotonic() - started)
with ledger.open("a", encoding="utf-8") as f:
    f.write(json.dumps(record, ensure_ascii=False) + "\n")
print(json.dumps({k: record[k] for k in ("tag", "status", "bytes", "seconds")}))
