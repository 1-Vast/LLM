"""Read ZIP inventory, CSV headers and the original glossary; no CSV data rows."""
from pathlib import Path
import csv
import hashlib
import io
import json
import time
import zipfile
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RAW = ROOT / "tmp/extq1/gsdc_well_stats.zip"
started = time.monotonic()
manifest = json.loads((ROOT / "research/2026-10-28-az-export-coverage/receipts/download_manifest_x2.json").read_text(encoding="utf-8"))
expected = manifest["raw_well_zip"]["file"]["sha256"].lower()
sha, md5 = hashlib.sha256(), hashlib.md5()
with RAW.open("rb") as stream:
    for block in iter(lambda: stream.read(1 << 20), b""):
        sha.update(block)
        md5.update(block)
assert sha.hexdigest() == expected, "Existing raw archive changed; stop before inspection"
article = json.loads((HERE / "sources/figshare_raw_article.json").read_text(encoding="utf-8"))
out = {
    "raw_path": str(RAW), "raw_bytes": RAW.stat().st_size,
    "sha256": sha.hexdigest(), "md5": md5.hexdigest(),
    "matches_existing_manifest_sha256": True,
    "current_public_article": {
        "id": article["id"], "url": article.get("url"),
        "license": article.get("license"), "files": article.get("files"),
        "is_public": article.get("is_public"), "published_date": article.get("published_date")
    },
    "members": [], "csv_headers": {}, "csv_data_rows_read": 0,
    "response_numbers_parsed": 0
}
with zipfile.ZipFile(RAW) as archive:
    for member in archive.infolist():
        out["members"].append({"name": member.filename, "bytes": member.file_size})
        if member.filename.endswith(".csv"):
            with archive.open(member) as stream:
                header = stream.readline(16_384)
            assert header.endswith(b"\n"), "Header exceeds fixed inspection limit"
            out["csv_headers"][member.filename] = next(csv.reader(io.StringIO(header.decode("utf-8-sig"))))
        if Path(member.filename).name == "Glossary_combo_well_stats.pdf":
            raw_pdf = archive.read(member)
            target = HERE / "sources/well_glossary.pdf"
            assert not target.exists(), "Do not overwrite an existing source"
            target.write_bytes(raw_pdf)
            document = PdfReader(io.BytesIO(raw_pdf))
            pages = [{"page": i + 1, "text": page.extract_text()} for i, page in enumerate(document.pages)]
            (HERE / "sources/well_glossary_text.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            out["glossary"] = {"source_member": member.filename, "local_path": str(target),
                               "bytes": len(raw_pdf), "sha256": hashlib.sha256(raw_pdf).hexdigest(), "pages": len(pages)}
out["seconds"] = round(time.monotonic() - started, 3)
assert out["seconds"] < 120
(HERE / "raw_metadata.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
