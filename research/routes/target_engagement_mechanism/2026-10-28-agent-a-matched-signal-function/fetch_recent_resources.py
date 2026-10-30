"""One recorded Q2 for matched signaling/function resources; no model or outcome analysis."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import urllib.parse
import urllib.request

OUT = Path(__file__).resolve().parent / "sources"
QUERY = '(TITLE_ABS:phosphoproteomic* OR TITLE_ABS:RPPA OR TITLE_ABS:"signaling dynamics") AND (TITLE_ABS:viability OR TITLE_ABS:proliferation) AND (TITLE_ABS:"drug combinations" OR TITLE_ABS:perturbation) AND FIRST_PDATE:[2025-01-01 TO 2026-10-28]'


def main():
    OUT.mkdir(exist_ok=True)
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
        {"query": QUERY, "format": "json", "resultType": "core", "pageSize": 25}
    )
    receipt = {"query_id": "Q2", "query": QUERY, "url": url,
               "retrieved_utc": datetime.now(timezone.utc).isoformat(),
               "scope": "first page only, bounded targeted resource search, not a systematic survey"}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "MAESTRO-Research/1.0"}), timeout=45) as response:
            body = response.read(5_000_001)
            receipt.update(status=response.status, content_type=response.headers.get("Content-Type"), final_url=response.url)
        assert len(body) <= 5_000_000
        (OUT / "q2_recent_resources.json").write_bytes(body)
        payload = json.loads(body)
        receipt.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), hit_count=payload.get("hitCount"),
                       next_cursor=payload.get("nextCursorMark"), returned=len(payload.get("resultList", {}).get("result", [])))
        for row in payload.get("resultList", {}).get("result", []):
            print(json.dumps({k: row.get(k) for k in ("id", "pmcid", "doi", "title", "firstPublicationDate")}, ensure_ascii=False))
    except Exception as exc:
        receipt["error"] = str(exc)
    (OUT / "q2_recent_resources_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
