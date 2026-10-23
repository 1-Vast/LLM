import concurrent.futures
import hashlib
import json
from pathlib import Path
import requests

OUT = Path('log/20261023/function_update_renewal/constructive')
QUERIES = {
    'update': 'learned optimizers gradient history 2025 2026',
    'perturb': 'perturbation response prediction functional feedback 2025 2026',
    'state': 'State virtual cell perturbation prediction 2025',
    'context': 'in context perturbation response prediction 2025 2026',
}

def fetch(item):
    name, query = item
    url = 'https://api.openalex.org/works'
    response = requests.get(url, params={'search': query, 'filter': 'from_publication_date:2025-01-01,to_publication_date:2026-10-23', 'per-page': 8}, timeout=50)
    body = response.content
    (OUT / f'{name}.body').write_bytes(body)
    receipt = {'url': response.url, 'status': response.status_code, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
    (OUT / f'{name}.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    response.raise_for_status()
    rows = [{'title': x['title'], 'doi': x.get('doi'), 'date': x.get('publication_date'), 'primary': x.get('primary_location'), 'abstract': x.get('abstract_inverted_index')} for x in response.json()['results']]
    (OUT / f'{name}.projection.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    return name, [{k: r[k] for k in ['title', 'doi', 'date']} for r in rows]

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for name, rows in pool.map(fetch, QUERIES.items()):
            print(name, json.dumps(rows, ensure_ascii=False))
