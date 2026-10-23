"""One targeted metadata request for outer-trained local credit assignment."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/query_teacher_resolution/root_prior'
OUT.mkdir(parents=True, exist_ok=True)
assert not (OUT / 'query.body').exists()
response = requests.get('https://export.arxiv.org/api/query', params={
    'search_query': '(all:"meta-learning backpropagation" OR all:"meta-learning credit assignment" OR all:"meta-learning local")',
    'max_results': 10, 'sortBy': 'relevance'}, timeout=60)
(OUT / 'query.body').write_bytes(response.content)
(OUT / 'query.receipt.json').write_text(json.dumps({
    'url': response.url, 'utc': datetime.now(timezone.utc).isoformat(), 'status': response.status_code,
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
ns = {'a': 'http://www.w3.org/2005/Atom'}
entries = [{key: ' '.join(entry.findtext(f'a:{key}', default='', namespaces=ns).split())
            for key in ('id', 'title', 'published', 'summary')}
           for entry in ET.fromstring(response.content).findall('a:entry', ns)]
(OUT / 'RESULT.json').write_text(json.dumps(entries, indent=2), encoding='utf-8')
print(json.dumps(entries, indent=2))
