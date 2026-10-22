"""One official supplementary archive; directory and exact PDF identity only."""
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import zipfile

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/serial_antibiotic_alternatives/supplement_followup"
URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12164588/supplementaryFiles"


def main():
    target = OUT / "NETWORK.json"
    if target.exists():
        raise FileExistsError(target)
    receipt = {"url": URL, "utc": datetime.now(timezone.utc).isoformat()}
    body = b""
    try:
        with requests.get(URL, stream=True, timeout=55, allow_redirects=False) as response:
            receipt.update(status=response.status_code, content_type=response.headers.get("Content-Type"))
            body = response.raw.read(20_000_000, decode_content=True)
        receipt.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        (OUT / "SUPPLEMENT_ARCHIVE.body").write_bytes(body)
        if receipt["status"] != 200 or len(body) >= 20_000_000:
            raise ValueError("HTTP failure or body ceiling; no archive parsing")
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            files = [{"name": item.filename, "size": item.file_size, "compressed": item.compress_size}
                     for item in archive.infolist()]
            (OUT / "MANIFEST.json").write_text(json.dumps(files, indent=2), encoding="utf-8")
            matches = [item for item in archive.infolist()
                       if PurePosixPath(item.filename).name == "msaf115_supplementary_data.pdf"]
            if len(matches) != 1:
                raise ValueError("Exact referenced PDF not uniquely identified")
            member = matches[0]
            if member.file_size > 20_000_000 or ".." in PurePosixPath(member.filename).parts:
                raise ValueError("PDF member outside registered bound")
            pdf = archive.read(member)
            if not pdf.startswith(b"%PDF-"):
                raise ValueError("Referenced file does not have PDF signature")
            (OUT / "msaf115_supplementary_data.pdf").write_bytes(pdf)
            receipt.update(exact_pdf_found=True, pdf_bytes=len(pdf), pdf_sha256=hashlib.sha256(pdf).hexdigest())
    except Exception as exc:
        receipt.update(error_type=type(exc).__name__, error=str(exc))
    receipt["code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    target.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
