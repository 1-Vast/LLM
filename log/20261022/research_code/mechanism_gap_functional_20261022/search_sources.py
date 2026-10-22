"""Bounded metadata-only cancer adaptation source queries, no outcomes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

BASE = Path("log/20261022/mechanism_gap/functional")
QUERIES = [
    '(TITLE_ABS:"drug resistance") AND (TITLE_ABS:barcode OR TITLE_ABS:lineage) AND (TITLE_ABS:reversible OR TITLE_ABS:reprogramming) AND FIRST_PDATE:[2023-01-01 TO 2026-10-22]',
    '(TITLE_ABS:"drug tolerance") AND (TITLE_ABS:washout OR TITLE_ABS:rechallenge) AND TITLE_ABS:"single-cell"',
    '(TITLE_ABS:Rewind OR TITLE_ABS:MemorySeq OR TITLE_ABS:FateMap) AND (TITLE_ABS:drug OR TITLE_ABS:cancer)',
    '(TITLE_ABS:"drug resistance") AND TITLE_ABS:selection AND TITLE_ABS:adaptation AND (TITLE_ABS:"second drug" OR TITLE_ABS:sequential)',
]


def request(url, path):
    rec = {"url": url, "utc": datetime.now(timezone.utc).isoformat()}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MAESTRO metadata research"})
        with urllib.request.urlopen(req, timeout=40) as response:
            body = response.read()
            rec.update(status=response.status, bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest())
        path.write_bytes(body)
    except Exception as exc:
        rec["error"] = repr(exc)
    return rec


if __name__ == "__main__":
    results = []
    for index, query in enumerate(QUERIES, 1):
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"+urllib.parse.urlencode({
            "query": query, "format": "json", "resultType": "core", "pageSize": 12,
        })
        path = BASE/f"query_{index}.json"
        rec = request(url, path)
        rec["query"] = query
        if rec.get("status") == 200:
            data = json.loads(path.read_bytes())
            rec["hitCount"] = data.get("hitCount")
            rec["items"] = [{key: item.get(key) for key in
                             ("id", "pmcid", "doi", "title", "firstPublicationDate", "abstractText")}
                            for item in data.get("resultList", {}).get("result", [])]
        results.append(rec)
    (BASE/"SEARCH_RECEIPTS.json").write_text(json.dumps(results, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
