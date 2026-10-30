"""One bounded fetch of the actual supplementary DOCX linked by the inspected HTML."""
import hashlib
import json
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
URL = "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-024-54728-7/MediaObjects/41467_2024_54728_MOESM1_ESM.docx"
CAP = 16 * 1024 * 1024
receipt = {"operation_id": "ROOT-R4", "round_external_operation": 6,
           "kind": "published_supplement_from_actual_html_link", "url": URL,
           "started_utc": datetime.now(timezone.utc).isoformat(), "timeout_seconds": 40,
           "byte_cap": CAP, "retries": 0,
           "decision": "Verify rechallenge/PINK1 timing and independent functional repeats, not outcome values."}
started = time.perf_counter()
body = bytearray()
try:
    request = urllib.request.Request(URL, headers={"User-Agent": "MAESTRO-public-research-source-check/1.0"})
    with urllib.request.urlopen(request, timeout=40) as response:
        receipt.update(http_status=response.status, final_url=response.url,
                       content_type=response.headers.get("Content-Type"))
        while True:
            chunk = response.read(min(65536, CAP + 1 - len(body)))
            if not chunk:
                break
            body.extend(chunk)
            if len(body) > CAP:
                raise ValueError("Byte cap reached; stopped without retry.")
    name = "punzi_2025_supplement.docx" if body.startswith(b"PK") else "punzi_2025_supplement.response"
    path = ROOT / "sources" / name
    with path.open("xb") as handle:
        handle.write(body)
    if name.endswith(".docx"):
        with zipfile.ZipFile(path) as archive:
            receipt["has_word_document_xml"] = "word/document.xml" in archive.namelist()
    receipt.update(status="received", saved_as=name, active_content_executed=False,
                   scientific_values_parsed=0)
except (urllib.error.URLError, TimeoutError, ValueError, zipfile.BadZipFile) as error:
    receipt.update(status="failed", error=str(error))
    if isinstance(error, urllib.error.HTTPError):
        receipt["http_status"] = error.code
receipt.update(bytes=len(body), elapsed_seconds=time.perf_counter()-started,
               sha256=hashlib.sha256(body).hexdigest() if body else None)
with (ROOT / "sources/punzi_supplement_receipt.json").open("x", encoding="utf-8") as handle:
    json.dump(receipt, handle, ensure_ascii=False, indent=2)
print(json.dumps(receipt, ensure_ascii=False))
