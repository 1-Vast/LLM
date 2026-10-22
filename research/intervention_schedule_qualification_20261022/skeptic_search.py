"""Limited primary-source search for real sequential perturbation datasets."""
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_schedule_qualification/skeptic_sources"
queries = {
    "sequence_screen": '(TITLE_ABS:"sequential" AND (TITLE_ABS:"drug combinations" OR TITLE_ABS:"drug combination") AND (TITLE_ABS:"screen" OR TITLE_ABS:"transcriptomic" OR TITLE_ABS:"proteomic"))',
    "order_screen": '((TITLE_ABS:"drug order" OR TITLE_ABS:"order-dependent" OR TITLE_ABS:"drug sequence") AND (TITLE_ABS:"screen" OR TITLE_ABS:"transcriptomic" OR TITLE_ABS:"proteomic"))',
    "washout": '((TITLE_ABS:"washout" OR TITLE_ABS:"wash-out") AND (TITLE_ABS:"RNA-seq" OR TITLE_ABS:"transcriptomic" OR TITLE_ABS:"proteomic") AND (TITLE_ABS:"drug" OR TITLE_ABS:"treatment"))',
    "schedule_omics": '((TITLE_ABS:"sequential treatment" OR TITLE_ABS:"sequential drug" OR TITLE_ABS:"drug scheduling") AND (TITLE_ABS:"single-cell" OR TITLE_ABS:"transcriptome" OR TITLE_ABS:"proteomics" OR TITLE_ABS:"high-throughput"))',
    "systematic_sequence": '((TITLE_ABS:"sequential" OR TITLE_ABS:"sequence-dependent") AND TITLE_ABS:"drug" AND (TITLE_ABS:"systematic" OR TITLE_ABS:"large-scale") AND (TITLE_ABS:"cancer" OR TITLE_ABS:"cell"))',
    "priming_screen": '(TITLE_ABS:"priming" AND TITLE_ABS:"screen" AND (TITLE_ABS:"transcriptomic" OR TITLE_ABS:"proteomic" OR TITLE_ABS:"single-cell") AND TITLE_ABS:"drug")',
}
ledger = []
for name, query in queries.items():
    query += ' AND FIRST_PDATE:[1900-01-01 TO 2026-10-22] NOT DOI:10.1016/j.cell.2012.03.031'
    path = OUT / f"{name}.json"
    if path.exists():
        raise FileExistsError(path)
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({"query": query, "format": "json", "resultType": "core", "pageSize": "30", "sort": "RELEVANCE desc"})
    receipt = {"name": name, "query": query, "url": url}
    try:
        with urllib.request.urlopen(url, timeout=45) as response:
            payload = response.read(2_000_001)
            receipt["status"] = response.status
        if len(payload) > 2_000_000:
            raise RuntimeError("Literature response ceiling exceeded")
        path.write_bytes(payload)
        data = json.loads(payload)
        receipt.update({"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "hitCount": data.get("hitCount")})
        abstracts = [{field: item.get(field) for field in ("id", "source", "pmcid", "doi", "title", "firstPublicationDate", "abstractText", "fullTextUrlList")} for item in data.get("resultList", {}).get("result", [])]
        (OUT / f"{name}_abstracts.json").write_text(json.dumps(abstracts, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        receipt["error"] = str(exc)
    ledger.append(receipt)
    (OUT / "SEARCH_NETWORK.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(ledger))
