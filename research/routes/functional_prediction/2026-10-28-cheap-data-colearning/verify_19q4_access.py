"""One bounded official discovery request, then one exact article manifest if found."""
from pathlib import Path
import hashlib
import json
import time
import urllib.request

out = Path(__file__).resolve().parent / "sources" / "public_prism"

def request(name, url, ordinal, payload=None):
    receipt_path = out / (name + "_receipt.json")
    assert not receipt_path.exists(), "No replay"
    receipt = {"url": url, "episode_http_ordinal": ordinal, "method": "POST" if payload else "GET",
               "query": payload, "timeout_seconds": 25, "max_bytes": 1_000_000, "retries": 0,
               "purpose": "Verify common 19Q4 original release availability and exact byte/permission terms",
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    try:
        data = json.dumps(payload).encode() if payload else None
        req = urllib.request.Request(url, data=data, headers={"User-Agent": "MAESTRO-research/1.0", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read(1_000_001)
            assert len(raw) <= 1_000_000
            (out / (name + ".json")).write_bytes(raw)
            receipt.update(status=response.status, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            return json.loads(raw)
    except Exception as exc:
        receipt.update(state="failed_no_retry", error_type=type(exc).__name__, error=str(exc))
        return None
    finally:
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False))

records = request("search19q4", "https://api.figshare.com/v2/articles/search", 9,
                  {"search_for": '"PRISM" "19Q4"', "page_size": 40})
if records:
    matches = [r for r in records if "19q4" in r.get("title", "").lower() and "prism" in r.get("title", "").lower()]
    print(json.dumps({"exact_title_matches": [{"id": r["id"], "title": r["title"]} for r in matches]}))
    if len(matches) == 1:
        detail = request("release19q4", matches[0]["url"], 10)
        if detail:
            files = detail.get("files", [])
            print(json.dumps({"title": detail.get("title"), "doi": detail.get("doi"), "license": detail.get("license"),
                "selected_files": [{k: f.get(k) for k in ("id", "name", "size", "download_url", "computed_md5")} for f in files
                                   if "primary-screen" in f["name"] and any(s in f["name"] for s in ("replicate-collapsed", "cell-line-info", "readme"))]}, ensure_ascii=False))
