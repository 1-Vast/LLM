"""Archive targeted primary-method retrieval; no biological files are accessed."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/early_update_mechanism/frontier/source'
QUERIES = {
    'titans': 'ti:"Titans" AND (cat:cs.LG OR cat:cs.AI)',
    'nested': 'ti:"Nested Learning"',
    'self_adapting': 'ti:"Self-Adapting Language Models"',
    'discovery': 'ti:"Test-Time Training" AND (all:discovery OR all:discover)',
    'dgm': 'ti:"Darwin Godel Machine"',
}
NS = {'a': 'http://www.w3.org/2005/Atom'}


def get_query(item):
    name, query = item
    path = OUT / (name + '_query.xml')
    assert not path.exists()
    params = {'search_query': query, 'max_results': 8, 'sortBy': 'submittedDate', 'sortOrder': 'descending'}
    response = requests.get('https://export.arxiv.org/api/query', params=params, timeout=60)
    path.write_bytes(response.content)
    entries = []
    if response.status_code == 200:
        for entry in ET.fromstring(response.content).findall('a:entry', NS):
            entries.append({key: entry.findtext('a:' + key, namespaces=NS) for key in ('id', 'title', 'published', 'summary')})
    return {'query': query, 'url': response.url, 'status': response.status_code,
            'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(response.content).hexdigest(),
            'entries': entries}


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(get_query, QUERIES.items()))
    (OUT / 'SEARCH_MANIFEST.json').write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'results': results}, indent=2), encoding='utf-8')
    for result in results:
        print(json.dumps({key: result[key] for key in ('query', 'status', 'entries')}))
