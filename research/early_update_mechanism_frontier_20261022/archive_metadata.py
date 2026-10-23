"""Persist original metadata/version dates for the six retrieved algorithm papers."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/early_update_mechanism/frontier/source'
IDS = ['2501.00663', '2512.24695', '2506.10943', '2505.22954', '2601.16175', '2610.05950']
NS = {'a': 'http://www.w3.org/2005/Atom'}
target = OUT / 'METHOD_METADATA.xml'
assert not target.exists()
response = requests.get('https://export.arxiv.org/api/query', params={'id_list': ','.join(IDS)}, timeout=60)
target.write_bytes(response.content)
record = {'url': response.url, 'status': response.status_code,
          'sha256': hashlib.sha256(response.content).hexdigest(), 'entries': []}
if response.status_code == 200:
    for entry in ET.fromstring(response.content).findall('a:entry', NS):
        record['entries'].append({key: entry.findtext('a:' + key, namespaces=NS) for key in ('id', 'title', 'published', 'updated')})
(OUT / 'METHOD_METADATA.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
