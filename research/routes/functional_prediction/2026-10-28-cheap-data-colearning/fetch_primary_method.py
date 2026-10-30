"""Budgeted original PRISM-method lookup; no response matrices or retries."""
from pathlib import Path
import hashlib
import json
import time
import urllib.parse
import urllib.request

root = Path(__file__).resolve().parent / "sources" / "primary_method"
root.mkdir(exist_ok=True)

def fetch(name, url, ordinal, cap):
    receipt_path = root / (name + "_receipt.json")
    target = root / name
    assert not receipt_path.exists() and not target.exists(), "No automatic replay"
    receipt = {"url": url, "episode_http_ordinal": ordinal, "max_bytes": cap,
               "timeout_seconds": 25, "retries": 0,
               "purpose": "Resolve original primary-screen assay time and conditions only",
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "MAESTRO-research/1.0"}), timeout=25) as response:
            raw = response.read(cap + 1)
            assert len(raw) <= cap, "Byte budget exceeded"
            target.write_bytes(raw)
            receipt.update(status=response.status, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                           content_type=response.headers.get("Content-Type"))
            return raw
    except Exception as exc:
        receipt.update(state="failed_no_retry", error_type=type(exc).__name__, error=str(exc))
        return None
    finally:
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False))

lookup = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({
    "query": "DOI:10.1038/s43018-019-0018-6", "format": "json", "pageSize": 5, "resultType": "core"})
raw = fetch("lookup.json", lookup, 8, 1_000_000)
if raw:
    results = json.loads(raw).get("resultList", {}).get("result", [])
    matches = [r for r in results if r.get("doi", "").lower() == "10.1038/s43018-019-0018-6" and r.get("pmcid")]
    if len(matches) == 1:
        pmcid = matches[0]["pmcid"]
        fetch(pmcid + ".xml", f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML", 9, 5_000_000)
