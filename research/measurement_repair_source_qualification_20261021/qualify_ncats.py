"""Metadata only: official source catalogue and data dictionary, no assay rows."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import time

import openpyxl
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261021/measurement_repair_source_qualification"
LIMIT = 500_000


def main():
    start = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "METADATA_RECEIPT.json").exists():
        raise RuntimeError("Metadata receipt exists; inspect rather than repeat acquisition")
    ledger = {"limit_bytes": LIMIT, "body_bytes": 0, "requests": []}
    def get(url):
        chunks = []
        with requests.get(url, timeout=25, stream=True) as response:
            for chunk in response.iter_content(16384):
                ledger["body_bytes"] += len(chunk)
                if ledger["body_bytes"] > LIMIT:
                    raise RuntimeError("Metadata budget exceeded")
                chunks.append(chunk)
            data = b"".join(chunks)
            ledger["requests"].append({"url": response.url, "status": response.status_code,
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "last_modified": response.headers.get("Last-Modified"), "etag": response.headers.get("ETag")})
            (OUT / "NETWORK.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
            response.raise_for_status()
            return data
    directory = get("https://opendata.ncats.nih.gov/public/odp/assay/")
    (OUT / "official_directory.html").write_bytes(directory)
    archive = json.loads(get("https://zenodo.org/api/records/20429398"))
    files = [{"key": x["key"], "size": x["size"], "checksum": x["checksum"], "links": x["links"]} for x in archive["files"]]
    dictionary = next(x for x in files if x["key"].endswith(".xlsx"))
    content = get(dictionary["links"]["self"])
    checksum = dictionary["checksum"]
    if checksum.startswith("md5:") and hashlib.md5(content).hexdigest() != checksum.removeprefix("md5:"):
        raise RuntimeError("Data dictionary checksum mismatch")
    (OUT / "data_dictionary.xlsx").write_bytes(content)
    workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    sheets = {sheet.title: [[v for v in row] for row in sheet.iter_rows(values_only=True)] for sheet in workbook}
    workbook.close()
    (OUT / "DATA_DICTIONARY.json").write_text(json.dumps(sheets, indent=2, default=str), encoding="utf-8")
    receipt = {"record_id": archive["id"], "publication_date": archive["metadata"].get("publication_date"),
               "version": archive["metadata"].get("version"), "licence": archive["metadata"].get("license"),
               "files": files, "dictionary_sha256": hashlib.sha256(content).hexdigest(),
               "full_assay_csv_downloaded": False, "individual_outcomes_exposed": False,
               "wall_seconds": time.perf_counter() - start, "network_body_bytes": ledger["body_bytes"]}
    (OUT / "METADATA_RECEIPT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
