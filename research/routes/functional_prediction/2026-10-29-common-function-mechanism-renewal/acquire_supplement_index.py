"""One public supplemental archive read; enumerate entries without outcome parsing."""
from pathlib import Path
import hashlib
import json
import time
import urllib.request
import zipfile

root = Path(__file__).resolve().parent / "root_sources"
ledger = root / "supplement_request.json"
assert not ledger.exists(), "No automatic request replay"
record = {"url": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13187417/supplementaryFiles",
          "request_allocation": "one of four final-feasibility requests; prior39 plus extension11 retained",
          "timeout_seconds": 25, "byte_limit": 16000000, "automatic_retries": 0,
          "purpose": "verify available filenames/layout, no workbook response interpretation"}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
start = time.monotonic()
try:
    with urllib.request.build_opener(NoRedirect).open(record["url"], timeout=25) as response:
        record.update(status=response.status, content_type=response.headers.get("Content-Type"),
                      content_length=response.headers.get("Content-Length"))
        if record["content_length"] is not None:
            assert int(record["content_length"]) <= 16000000, "advertised body exceeds cap; no body read"
        body = response.read(16000001)
        record["bytes_read"] = len(body)
        assert len(body) <= 16000000, "incomplete body above cap"
        archive = root / "PMC13187417_supplementary.zip"
        archive.write_bytes(body)
        record["sha256"] = hashlib.sha256(body).hexdigest()
        with zipfile.ZipFile(archive) as source:
            entries = [{"name": item.filename, "bytes": item.file_size,
                        "compressed_bytes": item.compress_size} for item in source.infolist()]
            (root / "supplement_archive_index.json").write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
            # Only the file-description PDF is eligible for extraction in this operation.
            selected = [item for item in source.infolist() if item.filename.endswith("41467_2026_71178_MOESM2_ESM.pdf")]
            for item in selected:
                assert item.file_size <= 2000000
                (root / "supplement_file_description.pdf").write_bytes(source.read(item))
            record.update(entries=len(entries), outcome_workbooks_opened=0,
                          description_pdf_extracted=bool(selected))
except Exception as error:
    record.update(error_type=type(error).__name__, detail=str(error))
record["elapsed_seconds"] = time.monotonic() - start
ledger.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record))
