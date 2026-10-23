"""One bounded exact public author-code request; no biological data access."""
import hashlib
import json
from pathlib import Path
import time

import requests

OUT = Path(__file__).resolve().parents[2] / "log/20261022/cdk_middle_feedback/review"
URL = "https://raw.githubusercontent.com/douglas-russo/GuarducciAbravanel2026_barcoding-scRNAseq/main/cell-line-barcoding.qmd"
BODY = OUT / "author_cell_line_barcoding.qmd"
RECEIPT = OUT / "author_cell_line_barcoding.receipt.json"
if BODY.exists() or RECEIPT.exists():
    raise FileExistsError("Refuse to repeat source request or overwrite evidence")
record = {"requested_url": URL, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "limit_bytes": 2_000_000, "attempts": 1}
try:
    response = requests.get(URL, stream=True, timeout=(15, 60))
    record.update(status=response.status_code, final_url=response.url,
                  redirects=[{"url": r.url, "status": r.status_code,
                              "location": r.headers.get("Location")} for r in response.history],
                  content_type=response.headers.get("Content-Type"))
    data = bytearray()
    for chunk in response.iter_content(65536):
        data.extend(chunk)
        if len(data) > record["limit_bytes"]:
            raise ValueError("Source exceeds frozen byte limit")
    BODY.write_bytes(data)
    record.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
except Exception as error:
    record["error"] = repr(error)
    raise
finally:
    RECEIPT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, indent=2))
