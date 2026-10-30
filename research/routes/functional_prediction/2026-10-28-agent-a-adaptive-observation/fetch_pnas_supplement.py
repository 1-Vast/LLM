"""One bounded, no-retry fetch of the supplementary PDF named in the source XML."""
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
URL = ("https://pmc.ncbi.nlm.nih.gov/articles/PMC12663926/bin/"
       "NIHMS2135134-supplement-Extended_methods__references__and_supplemental_figures.pdf")
CAP = 8 * 1024 * 1024
receipt = {"request_id": "ROOT-R4-SI", "kind": "same_paper_supplement",
           "url": URL, "started_utc": datetime.now(timezone.utc).isoformat(),
           "timeout_seconds": 45, "retry_count": 0,
           "decision": "Check support withdrawal/persistence and crossed-history protocols in PNAS2423894122.",
           "external_request_ordinal_in_round": 9}
started = time.perf_counter()
body = b""
try:
    request = urllib.request.Request(URL, headers={"User-Agent": "MAESTRO-research-source-check/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        receipt.update(http_status=response.status, final_url=response.url,
                       content_type=response.headers.get("Content-Type"))
        while True:
            chunk = response.read(min(65536, CAP + 1 - len(body)))
            if not chunk:
                break
            body += chunk
            if len(body) > CAP:
                raise ValueError("Response exceeds declared 8MiB cap; stopped without retry.")
    receipt["pdf_signature"] = body.startswith(b"%PDF-")
    name = "pnas2423894122_supplement.pdf" if receipt["pdf_signature"] else "pnas2423894122_supplement.response"
    with (ROOT / "sources" / name).open("xb") as handle:
        handle.write(body)
    receipt.update(saved_as=name, status="downloaded_pdf" if receipt["pdf_signature"] else "not_pdf")
except (urllib.error.URLError, TimeoutError, ValueError) as error:
    receipt.update(status="failed", error=str(error))
receipt.update(elapsed_seconds=time.perf_counter() - started, bytes=len(body),
               sha256=hashlib.sha256(body).hexdigest() if body else None)
with (ROOT / "sources/pnas_supplement_receipt.json").open("x", encoding="utf-8") as handle:
    json.dump(receipt, handle, ensure_ascii=False, indent=2)
print(json.dumps(receipt, ensure_ascii=False))
