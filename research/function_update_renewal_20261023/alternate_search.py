"""Crossref metadata fallback after EuropePMC503; preserve every response."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/function_update_renewal/root_sources'
QUERIES = [('crossref_cell', 'active learning cellular perturbation virtual cell'),
           ('crossref_update', 'learning update rules world models adaptation feedback'),
           ('crossref_function', 'genetic interaction prediction active learning transcriptome')]


def retrieve(item):
    name, query = item
    response = requests.get('https://api.crossref.org/works', params={'query': query,
        'filter': 'from-pub-date:2025-01-01,until-pub-date:2026-10-23', 'rows': 12}, timeout=45)
    (OUT / (name + '.body')).write_bytes(response.content)
    (OUT / (name + '.receipt.json')).write_text(json.dumps({'url': response.url, 'status': response.status_code,
        'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest(),
        'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'Registry metadata only'}, indent=2))
    if response.status_code != 200:
        return {'query': query, 'status': response.status_code}
    return {'query': query, 'status': 200, 'results': [{k: row.get(k) for k in ['title', 'DOI', 'published', 'URL', 'abstract']} for row in response.json()['message']['items']]}


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(retrieve, QUERIES))
    (OUT.parent / 'ALTERNATE_SEARCH.json').write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
