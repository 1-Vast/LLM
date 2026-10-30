"""Two remaining root source actions: primary method text and original GDSC manifest."""
from pathlib import Path
import hashlib
import json
import time
import urllib.request

out = Path(__file__).resolve().parent / "sources" / "root"
out.mkdir(parents=True, exist_ok=True)
sources = [
    ("P2_drp2026.xml", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13242297/fullTextXML", 5_000_000),
    ("P3_gdsc20_manifest.json", "https://api.figshare.com/v2/articles/22362739", 2_000_000),
]
for name, url, cap in sources:
    receipt_path = out / (name + ".receipt.json")
    assert not receipt_path.exists(), "No automatic replay"
    receipt = {"url": url, "timeout_seconds": 30, "max_bytes": cap, "retries": 0,
               "purpose": "Decision-changing primary-method or original-release identity/conditions",
               "public_action": name.split("_")[0], "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "MAESTRO-research/1.0"}), timeout=30) as response:
            raw = response.read(cap + 1)
            assert len(raw) <= cap
            (out / name).write_bytes(raw)
            receipt.update(status=response.status, content_type=response.headers.get("Content-Type"), bytes=len(raw),
                           sha256=hashlib.sha256(raw).hexdigest())
    except Exception as exc:
        receipt.update(state="failed_no_retry", error_type=type(exc).__name__, error=str(exc))
    finally:
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False))
