"""Retrieve bounded arXiv primary metadata; retain exact responses."""
import hashlib
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('log/20261023/update_law_search/skeptic')
OUT.mkdir(parents=True, exist_ok=True)
QUERIES = {
    'optimizers': '(ti:"learned optimizer" OR ti:"learning to optimize" OR ti:"optimizer discovery") AND submittedDate:[202501010000 TO 202610232359]',
    'model_revision': '(ti:"model revision" OR ti:"system identification" OR ti:"model adaptation") AND (all:"active" OR all:"meta") AND submittedDate:[202501010000 TO 202610232359]',
}
receipts, entries = [], []
ns = {'a': 'http://www.w3.org/2005/Atom'}
for label, query in QUERIES.items():
    url = 'https://export.arxiv.org/api/query?' + urllib.parse.urlencode({'search_query': query, 'max_results': 25, 'sortBy': 'submittedDate', 'sortOrder': 'descending'})
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            body, status = response.read(), response.status
        (OUT / f'{label}.xml').write_bytes(body)
        receipts.append({'label': label, 'url': url, 'status': status, 'utc': datetime.now(timezone.utc).isoformat(), 'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body)})
        for entry in ET.fromstring(body).findall('a:entry', ns):
            entries.append({'query': label, **{k: entry.findtext('a:' + k, namespaces=ns) for k in ['id', 'title', 'published', 'summary']}})
    except Exception as error:
        receipts.append({'label': label, 'url': url, 'error': repr(error)})
(OUT / 'SEARCH_RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
(OUT / 'SEARCH_ENTRIES.json').write_text(json.dumps(entries, indent=2), encoding='utf-8')
for entry in entries:
    print(entry['id'], entry['title'].replace('\n', ' '))
