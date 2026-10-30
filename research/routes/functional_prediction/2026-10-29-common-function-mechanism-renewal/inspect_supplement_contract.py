"""Two declared public supplement reads; no raw response workbook access."""
from pathlib import Path
import hashlib
import json
import time
import urllib.error
import urllib.request

root = Path(__file__).resolve().parent / "root_sources"
root.mkdir(exist_ok=True)
ledger = root / "requests.jsonl"
if ledger.exists():
    raise SystemExit("Request ledger exists; no replay")
base = "https://static-content.springer-cdn.com/esm/art%3A10.1038%2Fs41467-026-71178-5/MediaObjects/"
names = ["41467_2026_71178_MOESM2_ESM.pdf", "41467_2026_71178_MOESM1_ESM.pdf"]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)
for name in names:
    record = {"url": base + name, "timeout_seconds": 25, "byte_limit": 4000000,
              "automatic_retries": 0, "purpose": "supplement layout, protocols and available data contract"}
    start = time.monotonic()
    try:
        with opener.open(record["url"], timeout=25) as response:
            body = response.read(4000001)
            record.update(status=response.status, bytes=len(body),
                          content_type=response.headers.get("Content-Type"))
            assert len(body) <= 4000000, "body above declared cap"
            assert body.startswith(b"%PDF"), "not a PDF"
            (root / name).write_bytes(body)
            record.update(saved=name, sha256=hashlib.sha256(body).hexdigest())
    except Exception as error:
        record.update(error_type=type(error).__name__, detail=str(error))
    record["elapsed_seconds"] = time.monotonic() - start
    with ledger.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")
    print(json.dumps(record))
