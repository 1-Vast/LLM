"""One bounded metadata request. Never fetch the protected 24Q2 outcomes."""
from pathlib import Path
import hashlib
import json
import time
import urllib.request

out = Path(__file__).resolve().parent / "sources" / "public_prism"
target = out / "Repurposing_Public_24Q2_Readme.txt"
receipt_path = out / "readme_receipt.json"
assert not target.exists() and not receipt_path.exists(), "No automatic replay"
receipt = {
    "url": "https://ndownloader.figshare.com/files/46631143",
    "purpose": "Public metadata only: extended-matrix composition and QC/replicate definitions",
    "timeout_seconds": 25, "max_bytes": 20000, "retries": 0,
    "episode_http_ordinal": 7,
    "expected_bytes": 12930, "expected_md5": "4b630e332a4148e44aec3c1b0f6e4808",
    "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
try:
    request = urllib.request.Request(receipt["url"], headers={"User-Agent": "MAESTRO-research/1.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read(20001)
        assert len(raw) <= 20000, "Metadata byte cap exceeded"
        target.write_bytes(raw)
        receipt.update(status=response.status, final_url=response.url,
                       content_type=response.headers.get("Content-Type"), bytes=len(raw),
                       sha256=hashlib.sha256(raw).hexdigest(), md5=hashlib.md5(raw).hexdigest())
        receipt["identity_verified"] = (
            len(raw) == receipt["expected_bytes"] and receipt["md5"] == receipt["expected_md5"])
except Exception as exc:
    receipt.update(state="failed_no_retry", exception=type(exc).__name__, error=str(exc))
finally:
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
