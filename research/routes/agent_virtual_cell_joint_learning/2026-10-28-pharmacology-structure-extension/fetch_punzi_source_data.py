"""One new original source access; inspect archive identities before any values."""
from pathlib import Path
import hashlib
import io
import json
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent / "sources/punzi"
ROOT.mkdir(parents=True, exist_ok=True)
path = ROOT / "41467_2024_54728_MOESM8_ESM.zip"
receipt_path = ROOT / "receipt.json"
if receipt_path.exists():
    raise SystemExit("Receipt exists; no automatic retry.")
url = "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-024-54728-7/MediaObjects/41467_2024_54728_MOESM8_ESM.zip"
receipt = {"date": "2026-10-28", "url": url, "source": "original publisher HTML attachment link MOESM8",
           "max_bytes": 25_000_000, "timeout_seconds": 25, "automatic_retry": False,
           "functional_values_consumed": False}
try:
    request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO original metadata qualification"})
    with urllib.request.urlopen(request, timeout=25) as response:
        size = response.headers.get("Content-Length")
        if size and int(size) > receipt["max_bytes"]:
            raise ValueError("Content-Length exceeds declared source budget")
        body = response.read(receipt["max_bytes"] + 1)
        assert len(body) <= receipt["max_bytes"]
        receipt.update(status=response.status, content_type=response.headers.get("Content-Type"), final_url=response.url,
                       bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    archive = zipfile.ZipFile(io.BytesIO(body))
    members = [{"name": entry.filename, "bytes": entry.file_size, "compressed_bytes": entry.compress_size}
               for entry in archive.infolist()]
    path.write_bytes(body)
    (ROOT / "members.json").write_text(json.dumps(members, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt["state"] = "downloaded_original_archive_directory_only"
    print(json.dumps({"state": receipt["state"], "bytes": len(body), "members": members}, ensure_ascii=False))
except Exception as error:
    receipt.update(state="unavailable_or_budget_stop", error=f"{type(error).__name__}: {error}")
    print(json.dumps({"state": receipt["state"], "error": receipt["error"]}))
receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
