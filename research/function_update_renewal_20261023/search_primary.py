"""Bounded literature metadata retrieval; no biological labels accessed."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/function_update_renewal/root_sources'
QUERIES = [
    ('cell_update', '("perturbation" AND ("feedback" OR "active learning") AND ("cell" OR "drug")) AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
    ('function_state', '("genetic interaction" AND ("prediction" OR "learning")) AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
    ('adaptive_cell', '("virtual cell" OR "perturbation prediction") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
]


def retrieve(item):
    name, query = item
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
    response = requests.get(url, params={'query': query, 'format': 'json', 'pageSize': 30, 'sort': 'RELEVANCE'}, timeout=60)
    body = response.content
    (OUT / (name + '.body')).write_bytes(body)
    receipt = {'url': response.url, 'status': response.status_code, 'bytes': len(body),
               'sha256': hashlib.sha256(body).hexdigest(), 'utc': datetime.now(timezone.utc).isoformat(),
               'scope': 'Registry metadata search, not full-text novelty verification'}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2))
    response.raise_for_status()
    rows = response.json().get('resultList', {}).get('result', [])
    return {'query': query, 'hit_count': response.json().get('hitCount'), 'results': [
        {k: row.get(k) for k in ['title', 'authorString', 'firstPublicationDate', 'doi', 'id', 'source', 'pmcid']} for row in rows]}


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(retrieve, QUERIES))
    (OUT.parent / 'PRIMARY_SEARCH.json').write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
