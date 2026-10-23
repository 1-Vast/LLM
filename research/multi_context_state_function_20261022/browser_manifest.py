"""Resolve the author's browser and inventory nonnumeric primary resource links."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
tree = ET.fromstring((OUT / 'replogle.body').read_bytes())
links = []
for node in tree.iter():
    href = node.get('{http://www.w3.org/1999/xlink}href')
    if href and any(term in href.lower() for term in ('gwps', 'figshare', 'zenodo', 'github', 's3', 'ncbi.nlm.nih.gov/geo')):
        links.append({'href': href, 'text': ' '.join(' '.join(node.itertext()).split())})
(OUT / 'REPlOGLE_RESOURCE_LINKS.json').write_text(json.dumps(links, indent=2), encoding='utf-8')
assert not (OUT / 'browser.body').exists()
response = requests.get('https://gwps.wi.mit.edu/', timeout=45)
(OUT / 'browser.body').write_bytes(response.content)
(OUT / 'browser.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
print(json.dumps({'status': response.status_code, 'bytes': len(response.content), 'links': links}, indent=2))
response.raise_for_status()
print(response.text[:10000])
