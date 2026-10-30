"""One bounded public supplementary-files request; no retries."""
from pathlib import Path
import hashlib
import io
import json
import time
import urllib.error
import urllib.request
import zipfile

out = Path(__file__).resolve().parent / "sources/bcl11b_supplement"
out.mkdir(parents=True, exist_ok=True)
receipt_file = out / "receipt.json"
assert not receipt_file.exists(), "Do not automatically repeat a recorded request"
url = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13557094/supplementaryFiles"
receipt = {"url": url, "timeout_seconds": 25, "byte_cap": 30000000,
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "retries": 0}
try:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "MAESTRO-research/1.0"}), timeout=25) as response:
        data = response.read(30000001)
        assert len(data) <= 30000000, "Public-source byte budget exceeded"
        receipt.update(status=response.status, content_type=response.headers.get("Content-Type"),
                       bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    if zipfile.is_zipfile(io.BytesIO(data)):
        (out / "supplementary_files.zip").write_bytes(data)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            receipt["members"] = [{"name": x.filename, "bytes": x.file_size} for x in archive.infolist()]
            matches = [x for x in archive.namelist() if x.endswith("sciadv.aec5436_sm.pdf")]
            if len(matches) == 1:
                pdf = archive.read(matches[0])
                assert pdf.startswith(b"%PDF-"), "Not a PDF"
                (out / "sciadv.aec5436_sm.pdf").write_bytes(pdf)
                receipt["pdf_sha256"] = hashlib.sha256(pdf).hexdigest()
                receipt["pdf_bytes"] = len(pdf)
    else:
        (out / "response.bin").write_bytes(data)
        receipt["format_error"] = "Not a supplementary ZIP; not accepted as PDF"
except urllib.error.HTTPError as error:
    receipt.update(status=error.code, error=str(error))
except Exception as error:
    receipt.update(error=type(error).__name__ + ": " + str(error))
receipt_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
