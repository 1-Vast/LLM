"""Bounded observation-law primary-source search; no assay values accessed."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/observation_law_search/root_sources'
QUERIES = [
    ('selection', '("single cell" OR "single-cell") AND ("survivor bias" OR "survivorship" OR "selection bias") AND ("perturbation" OR "drug") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
    ('population', '("unbalanced optimal transport" OR "population balance" OR "birth death") AND ("perturbation" OR "drug" OR "cell fate") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
    ('identifiable', '("cell state" OR "single-cell") AND ("identifiability" OR "identifiable") AND ("growth" OR "selection" OR "transport") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
]


def fetch(item):
    name, query = item
    receipt = {'name': name, 'query': query, 'started_utc': datetime.now(timezone.utc).isoformat()}
    try:
        response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                                params={'query': query, 'format': 'json', 'pageSize': 20}, timeout=35)
        body = response.content
        (OUT / (name + '.body')).write_bytes(body)
        receipt.update(status=response.status_code, url=response.url, bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest())
        if response.ok:
            payload = response.json()
            receipt.update(hit_count=payload.get('hitCount'), results=[{k: row.get(k) for k in
                           ['title', 'doi', 'id', 'source', 'pmcid', 'firstPublicationDate']} for row in
                           payload.get('resultList', {}).get('result', [])])
    except Exception as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(fetch, QUERIES))
    (OUT.parent / 'ROOT_SEARCH.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))
