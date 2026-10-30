"""One bounded public source action per explicit invocation; no retries/redirects."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent / "sources/root"
HERE.mkdir(parents=True, exist_ok=True)
tag, url, kind = sys.argv[1:]
assert tag.replace("_", "").isalnum()
output = HERE / f"{tag}.body"
assert not output.exists(), "No silent replay"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


ledger_path = HERE / "retrieval.jsonl"
if ledger_path.exists():
    for previous in reversed(ledger_path.read_text(encoding="utf-8").splitlines()):
        prior = json.loads(previous)
        if urllib.parse.urlsplit(prior["url"]).netloc == urllib.parse.urlsplit(url).netloc:
            ended = datetime.fromisoformat(prior["started_utc"]).timestamp() + prior["seconds"]
            time.sleep(max(0, ended + 1.05 - time.time()))
            break
started = time.monotonic()
record = {"tag": tag, "url": url, "kind": kind, "started_utc": datetime.now(timezone.utc).isoformat(),
          "timeout_seconds": 30, "max_body_bytes": 10000000, "automatic_retries": 0, "automatic_redirects": False}
request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-public-research/1.0", "Accept": "application/atom+xml,application/xml,text/html,application/pdf"})
try:
    response = urllib.request.build_opener(NoRedirect()).open(request, timeout=30)
except urllib.error.HTTPError as exc:
    response = exc
except Exception as exc:
    record.update(error=type(exc).__name__ + ": " + str(exc), bytes=0, status=None)
    data = b""
    response = None
if response is not None:
    with response:
        data = response.read(10000001)
        record.update(status=response.code, content_type=response.headers.get("Content-Type"), location=response.headers.get("Location"))
    if len(data) > 10000000:
        data = data[:10000000]
        record["error"] = "body_cap_exceeded; truncated and inadmissible"
output.write_bytes(data)
record.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), body_file=output.name, seconds=time.monotonic() - started)
with (HERE / "retrieval.jsonl").open("a", encoding="utf-8") as ledger:
    ledger.write(json.dumps(record, ensure_ascii=False) + "\n")
print(json.dumps({k: record[k] for k in ("tag", "kind", "status", "bytes", "seconds")}))
