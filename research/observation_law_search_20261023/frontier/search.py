"""Bounded original metadata search; retain replies, never biological labels."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT = Path('log/20261023/observation_law_search/frontier')
QUERIES = {
    'observability': 'all:"world model" AND (all:observability OR all:"observation model" OR all:identifiability) AND submittedDate:[202501010000 TO 202610232359]',
    'multiview': 'all:"causal" AND (all:"multi-view" OR all:"measurement") AND all:"representation" AND submittedDate:[202501010000 TO 202610232359]',
    'cell_observation': '("perturbation" AND ("observation model" OR "measurement error" OR "identifiable")) AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]',
}

def fetch(item):
    name, query = item
    receipt = {'query': query, 'utc': datetime.now(timezone.utc).isoformat()}
    endpoint = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search' if name == 'cell_observation' else 'https://export.arxiv.org/api/query'
    params = {'query': query, 'format': 'json', 'pageSize': 15} if name == 'cell_observation' else {'search_query': query, 'max_results': 15, 'sortBy': 'submittedDate', 'sortOrder': 'descending'}
    try:
        r = requests.get(endpoint, params=params, timeout=45)
        (OUT / f'{name}.body').write_bytes(r.content)
        receipt.update(url=r.url, status=r.status_code, bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest())
        if r.ok and name == 'cell_observation':
            receipt['results'] = r.json()
        elif r.ok:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.content)
            ns = {'a': 'http://www.w3.org/2005/Atom'}
            receipt['results'] = [{k: e.findtext('a:' + k, namespaces=ns) for k in ['id', 'title', 'summary', 'published']} for e in root.findall('a:entry', ns)]
    except Exception as e:
        receipt['error'] = repr(e)
    (OUT / f'{name}.receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    return receipt

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        print(json.dumps(list(pool.map(fetch, QUERIES.items())), ensure_ascii=False, indent=2))
