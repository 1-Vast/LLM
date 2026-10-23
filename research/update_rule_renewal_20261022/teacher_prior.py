"""Bounded primary metadata query addressing a specific novelty uncertainty."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_rule_renewal/root_prior'
OUT.mkdir(parents=True, exist_ok=True)
assert not (OUT / 'query.body').exists()
url = 'https://export.arxiv.org/api/query'
params = {'search_query': 'all:"synthetic gradient" AND (all:meta OR all:"learning to learn")',
          'max_results': 12, 'sortBy': 'relevance'}
response = requests.get(url, params=params, timeout=60)
(OUT / 'query.body').write_bytes(response.content)
(OUT / 'query.receipt.json').write_text(json.dumps({
    'utc': datetime.now(timezone.utc).isoformat(), 'url': response.url, 'status': response.status_code,
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
ns = {'a': 'http://www.w3.org/2005/Atom'}
entries = []
for entry in ET.fromstring(response.content).findall('a:entry', ns):
    entries.append({key: ' '.join(entry.findtext(f'a:{key}', default='', namespaces=ns).split())
                    for key in ('id', 'title', 'published', 'summary')})
(OUT / 'RESULT.json').write_text(json.dumps(entries, indent=2), encoding='utf-8')
print(json.dumps(entries, indent=2))
