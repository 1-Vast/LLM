"""One explicit source request; bounded bodies, no retry or redirect."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

here = Path(__file__).resolve().parent / "sources/root"
here.mkdir(parents=True, exist_ok=True)
tag, url, kind = sys.argv[1:]
assert tag.replace("_", "").isalnum()
body = here / (tag + ".body")
assert not body.exists(), "No silent replay"
ledger = here / "retrieval.jsonl"
past = [json.loads(s) for s in ledger.read_text(encoding="utf-8").splitlines()] if ledger.exists() else []
assert len(past) < 7, "Root seven-original cap after explicit reassignment"
remaining = 20000000 - sum(r["bytes"] for r in past if r.get("status") == 200)
limit = min(8000000, remaining)
assert limit > 0
host = urllib.parse.urlsplit(url).netloc
for record in reversed(past):
    if urllib.parse.urlsplit(record["url"]).netloc == host:
        ended = datetime.fromisoformat(record["started_UTC"]).timestamp() + record["seconds"]
        time.sleep(max(0, ended + 1.1 - time.time()))
        break


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


record = {"tag": tag, "url": url, "kind": kind, "started_UTC": datetime.now(timezone.utc).isoformat(),
          "timeout_seconds": 30, "body_cap_bytes": limit, "automatic_retries": 0, "automatic_redirects": 0}
with (here / "request_intents.jsonl").open("a", encoding="utf-8") as f:
    f.write(json.dumps(record) + "\n")
started = time.monotonic()
request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-public-research/1.0", "Accept": "text/html,application/pdf,application/xml"})
try:
    response = urllib.request.build_opener(NoRedirect()).open(request, timeout=30)
except urllib.error.HTTPError as exc:
    response = exc
except Exception as exc:
    response = None
    record.update(status=None, error=type(exc).__name__ + ": " + str(exc))
data = b""
if response is not None:
    with response:
        record.update(status=response.code, content_type=response.headers.get("Content-Type"), redirect_target=response.headers.get("Location"))
        data = response.read(limit + 1)
    if len(data) > limit:
        data = data[:limit]
        record["error"] = "body cap exceeded; truncated and inadmissible"
body.write_bytes(data)
record.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), body_file=body.name, seconds=time.monotonic()-started)
with ledger.open("a", encoding="utf-8") as f:
    f.write(json.dumps(record, ensure_ascii=False) + "\n")
print(json.dumps({k: record.get(k) for k in ("tag", "status", "bytes", "seconds", "error")}))
