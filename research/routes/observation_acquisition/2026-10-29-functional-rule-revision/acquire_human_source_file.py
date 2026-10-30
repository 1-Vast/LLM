"""Acquire one listed human source workbook; read sheet names, never cell values."""
from pathlib import Path
import datetime
import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

out = Path(__file__).resolve().parent / "sources"
follow_observed = sys.argv[1:] == ["--follow-observed-redirect"]
assert not sys.argv[1:] or follow_observed
receipt_path = out / ("human_fig5c_redirect_request.json" if follow_observed else "human_fig5c_request.json")
assert not receipt_path.exists(), "No automatic replay"
accession = "S-SCDT-10_1038-S44320-025-00150-0"
filename = "Fig_5C.xlsx"
url = "https://www.ebi.ac.uk/biostudies/files/" + accession + "/" + filename
if follow_observed:
    previous = json.loads((out / "human_fig5c_request.json").read_text(encoding="utf-8"))
    assert previous["status"] == 302
    url = previous["location"]
    assert url.startswith("https://ftp.ebi.ac.uk/biostudies/") and url.endswith("/" + filename)
receipt = {"url": url, "date_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "filename_from_actual_metadata": filename, "metadata_expected_bytes": 9393,
           "timeout_seconds": 25, "byte_limit": 1000000, "automatic_retries": 0,
           "allocation": "observed public redirect, counted separately from initial request; unused scout request reallocated" if follow_observed else "one coordinator reserve request; new source acquisition, not a scientific test",
           "role_frozen_before_request": "Metadata qualification only. Read ZIP/workbook.xml sheet names; do not open worksheets, sharedStrings or numeric/response cells. No confirmatory outcome role assigned."}
receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

started = time.monotonic()
try:
    with urllib.request.build_opener(NoRedirect).open(url, timeout=25) as response:
        raw = response.read(1000000)
        receipt.update(status=response.status, bytes_read=len(raw), content_type=response.headers.get("Content-Type"), sha256=hashlib.sha256(raw).hexdigest())
    is_zip = zipfile.is_zipfile(io.BytesIO(raw))
    receipt["is_parseable_zip"] = is_zip
    target = out / (filename if is_zip else "human_fig5c_nonworkbook_body.bin")
    target.write_bytes(raw)
    receipt["saved_path"] = str(target)
    if is_zip:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            root = ET.fromstring(archive.read("xl/workbook.xml"))
            receipt["sheet_names_only"] = [e.get("name") for e in root.iter() if e.tag.rsplit("}", 1)[-1] == "sheet"]
            receipt["zip_member_count"] = len(archive.namelist())
            receipt["worksheet_values_read"] = False
except urllib.error.HTTPError as error:
    raw = error.read(1000)
    (out / "human_fig5c_error.bin").write_bytes(raw)
    receipt.update(status=error.code, bytes_read=len(raw), error_type=type(error).__name__, location=error.headers.get("Location"), retry_after=error.headers.get("Retry-After"))
except Exception as error:
    receipt.update(error_type=type(error).__name__, detail=str(error), body_telemetry_returned=False)
receipt["elapsed_seconds"] = round(time.monotonic() - started, 3)
receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt))
