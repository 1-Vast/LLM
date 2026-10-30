"""One new authoritative attachment request; inspect ZIP sheet names only."""
from pathlib import Path
import datetime
import hashlib
import io
import json
import time
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

out = Path(__file__).resolve().parent / "sources"
out.mkdir(exist_ok=True)
receipt_path = out / "source_data_request.json"
assert not receipt_path.exists(), "No replay of a completed/uncertain request"
url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC13187417/bin/41467_2026_71178_MOESM18_ESM.xlsx"
receipt = {
    "url": url, "date_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "timeout_seconds": 25, "byte_limit": 8000000, "automatic_retries": 0,
    "role_frozen_before_request": "Acquire potential resource; inspect ZIP/workbook sheet names only. No worksheet/shared-string response values. Any later values are exploratory until a separate frozen qualified contract.",
    "prior_failed_routes_not_replayed": ["Springer SI PDFs", "EuropePMC supplementary archive"],
}
receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

started = time.monotonic()
opener = urllib.request.build_opener(NoRedirect)
try:
    with opener.open(urllib.request.Request(url, headers={"User-Agent": "MAESTRO-research-source-audit/1.0"}), timeout=25) as response:
        raw = response.read(8000000)
        receipt.update(status=response.status, bytes_read=len(raw), content_type=response.headers.get("Content-Type"), declared_content_length=response.headers.get("Content-Length"))
    is_zip = zipfile.is_zipfile(io.BytesIO(raw))
    receipt["is_parseable_zip"] = is_zip
    receipt["sha256"] = hashlib.sha256(raw).hexdigest()
    target = out / ("source_data.xlsx" if is_zip else "source_data_nonworkbook_body.bin")
    target.write_bytes(raw)
    receipt["saved_path"] = str(target)
    if is_zip:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            root = ET.fromstring(archive.read("xl/workbook.xml"))
            receipt["sheet_names_only"] = [e.get("name") for e in root.iter() if e.tag.rsplit("}", 1)[-1] == "sheet"]
            receipt["worksheet_values_read"] = False
            receipt["zip_member_count"] = len(archive.namelist())
except urllib.error.HTTPError as error:
    body = error.read(1000)
    receipt.update(status=error.code, bytes_read=len(body), location=error.headers.get("Location"), retry_after=error.headers.get("Retry-After"), error_type=type(error).__name__)
    (out / "source_data_http_error.bin").write_bytes(body)
except Exception as error:
    receipt.update(error_type=type(error).__name__, detail=str(error), body_telemetry_returned=False)
receipt["elapsed_seconds"] = round(time.monotonic() - started, 3)
receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt))
