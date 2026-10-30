"""One human-cell study metadata request; no experimental response values read."""
from pathlib import Path
import datetime
import hashlib
import json
import time
import urllib.error
import urllib.request

out = Path(__file__).resolve().parent / "sources"
out.mkdir(exist_ok=True)
receipt_path = out / "human_source_index_request.json"
assert not receipt_path.exists(), "No replay"
url = "https://www.ebi.ac.uk/biostudies/api/v1/studies/S-SCDT-10_1038-S44320-025-00150-0"
receipt = {"url": url, "date_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "timeout_seconds": 25, "byte_limit": 4000000, "automatic_retries": 0,
           "role_frozen_before_request": "Official metadata/file identities for human-cell P3 original source availability ID. No worksheet/response values, hypothesis or performance test.",
           "allocation": "second source-qualification request after PMC attachment returned challenge HTML; compatible human functional scope after neutral-agent platform rejection"}
receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

started = time.monotonic()
try:
    with urllib.request.build_opener(NoRedirect).open(url, timeout=25) as response:
        raw = response.read(4000000)
        receipt.update(status=response.status, bytes_read=len(raw), content_type=response.headers.get("Content-Type"), sha256=hashlib.sha256(raw).hexdigest())
    (out / "human_source_index.json").write_bytes(raw)
    data = json.loads(raw)
    files = []
    def visit(value):
        if isinstance(value, dict):
            if "path" in value and isinstance(value["path"], str):
                files.append({k: value.get(k) for k in ["path", "size", "type"]})
            for sub in value.values():
                visit(sub)
        elif isinstance(value, list):
            for sub in value:
                visit(sub)
    visit(data)
    receipt.update(accession=data.get("accno"), file_metadata_only=files)
except urllib.error.HTTPError as error:
    raw = error.read(1000)
    (out / "human_source_index_error.bin").write_bytes(raw)
    receipt.update(status=error.code, bytes_read=len(raw), error_type=type(error).__name__, location=error.headers.get("Location"), retry_after=error.headers.get("Retry-After"))
except Exception as error:
    receipt.update(error_type=type(error).__name__, detail=str(error), body_telemetry_returned=False)
receipt["elapsed_seconds"] = round(time.monotonic() - started, 3)
receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt))
