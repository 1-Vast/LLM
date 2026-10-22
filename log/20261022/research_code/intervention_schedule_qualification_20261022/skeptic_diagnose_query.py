"""One explicitly amended diagnostic request; no retry sweep."""
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_schedule_qualification/skeptic_sources"
path = OUT / "SIMPLE_QUERY.json"
if path.exists() or (OUT / "SIMPLE_ERROR.body").exists():
    raise FileExistsError("Diagnostic request already made")
query = '"sequential drug treatment" AND FIRST_PDATE:[1900-01-01 TO 2026-10-22]'
url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({"query": query, "format": "json", "resultType": "core", "pageSize": "10"})
receipt = {"query": query, "url": url}
try:
    with urllib.request.urlopen(url, timeout=45) as response:
        payload = response.read(2_000_001)
        receipt["status"] = response.status
    if len(payload) > 2_000_000:
        raise RuntimeError("Literature response ceiling exceeded")
    path.write_bytes(payload)
    data = json.loads(payload)
    receipt.update({"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "hitCount": data.get("hitCount")})
    abstracts = [{field: item.get(field) for field in ("id", "source", "pmcid", "doi", "title", "firstPublicationDate", "abstractText", "fullTextUrlList")} for item in data.get("resultList", {}).get("result", []) if item.get("doi") != "10.1016/j.cell.2012.03.031"]
    (OUT / "SIMPLE_ABSTRACTS.json").write_text(json.dumps(abstracts, ensure_ascii=False, indent=2), encoding="utf-8")
except urllib.error.HTTPError as exc:
    body = exc.read()
    (OUT / "SIMPLE_ERROR.body").write_bytes(body)
    receipt.update({"error": str(exc), "status": exc.code, "error_body_bytes": len(body), "error_body_sha256": hashlib.sha256(body).hexdigest()})
except Exception as exc:
    receipt["error"] = str(exc)
(OUT / "DIAGNOSTIC_NETWORK.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(receipt))
