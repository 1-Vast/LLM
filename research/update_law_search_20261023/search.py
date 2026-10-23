"""Bounded primary metadata search, retain all replies; no biological data."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/update_law_search/root_sources'
QUERIES = [
    ('identification', '("perturbation" AND ("system identification" OR "identifiability" OR "response operator")) AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
    ('update_rule', '("learned optimizer" OR "learning to optimize" OR "meta-learned update") AND ("biology" OR "perturbation" OR "inverse problem") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
    ('context_feedback', '("perturbation prediction" AND ("adaptation" OR "transfer" OR "feedback")) AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
]


def fetch(item):
    name, query = item
    result = {'name': name, 'query': query, 'started_utc': datetime.now(timezone.utc).isoformat()}
    try:
        response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                                params={'query': query, 'format': 'json', 'pageSize': 30}, timeout=35)
        body = response.content
        (OUT / (name + '.body')).write_bytes(body)
        result.update(status=response.status_code, url=response.url, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        if response.ok:
            payload = response.json()
            result.update(hit_count=payload.get('hitCount'), results=[{k: row.get(k) for k in
                          ['title', 'doi', 'id', 'source', 'pmcid', 'firstPublicationDate']} for row in
                          payload.get('resultList', {}).get('result', [])])
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error))
    (OUT / (name + '.receipt.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(fetch, QUERIES))
    (OUT.parent / 'ROOT_SEARCH.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))
