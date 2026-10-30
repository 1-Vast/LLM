"""Fetch one bounded public Europe PMC OA supplementary archive, without executing it."""
import hashlib
import json
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12663926/supplementaryFiles"
CAP = 16 * 1024 * 1024
receipt = {"operation_id": "ROOT-R2", "kind": "independent_public_oa_supplementary_archive",
           "url": URL, "started_utc": datetime.now(timezone.utc).isoformat(),
           "timeout_seconds": 40, "byte_cap": CAP, "retries": 0,
           "decision": "Check published experimental timing and withdrawal protocol, without parsing response matrices."}
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
                raise ValueError("Byte cap reached; no retry and no matrix parsing.")
    name = "pnas_supplementary_archive.zip" if body.startswith(b"PK") else "pnas_supplementary_archive.response"
    path = ROOT / "sources" / name
    with path.open("xb") as handle:
        handle.write(body)
    receipt.update(saved_as=name, status="received")
    if name.endswith(".zip"):
        with zipfile.ZipFile(path) as archive:
            receipt["archive_members_metadata_only"] = [{"name": m.filename, "bytes": m.file_size}
                                                         for m in archive.infolist()]
        receipt["scientific_values_parsed"] = 0
except (urllib.error.URLError, TimeoutError, ValueError, zipfile.BadZipFile) as error:
    receipt.update(status="failed", error=str(error))
    if isinstance(error, urllib.error.HTTPError):
        receipt["http_status"] = error.code
receipt.update(bytes=len(body), elapsed_seconds=time.perf_counter() - started,
               sha256=hashlib.sha256(body).hexdigest() if body else None)
with (ROOT / "sources/epmc_supplementary_receipt.json").open("x", encoding="utf-8") as handle:
    json.dump(receipt, handle, ensure_ascii=False, indent=2)
print(json.dumps(receipt, ensure_ascii=False))
