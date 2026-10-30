"""One exact-title query for a public alternate version; no retries."""
from pathlib import Path
import hashlib
import json
import time
import urllib.parse
import urllib.request

out = Path(__file__).resolve().parent / "sources/public_version_check"
out.mkdir(exist_ok=True)
assert not (out / "receipt.json").exists(), "No automatic replay"
query = 'TITLE:"BCL11B predetermines a persister state in breast cancer"'
url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
    {"query": query, "format": "json", "resultType": "core", "pageSize": 10})
receipt = {"query": query, "url": url, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "timeout_seconds": 25, "max_bytes": 2000000, "retries": 0,
           "decision": "Could a verified public preprint supply unavailable protocol legends? Exact-title recovery only; no new scientific hypothesis."}
try:
    with urllib.request.urlopen(url, timeout=25) as response:
        raw = response.read(2000001)
        assert len(raw) <= 2000000
        receipt.update(status=response.status, content_type=response.headers.get("Content-Type"), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    (out / "query.json").write_bytes(raw)
    data = json.loads(raw)
    receipt["hit_count"] = data.get("hitCount")
    receipt["results"] = [{key: item.get(key) for key in ("id", "source", "title", "doi", "pubTypeList", "firstPublicationDate", "fullTextUrlList")}
                          for item in data.get("resultList", {}).get("result", [])]
except Exception as error:
    receipt["error"] = type(error).__name__ + ": " + str(error)
(out / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
