"""Inspect the exact author-linked processed-data record without file payloads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
assert not (OUT / 'figshare20029387.body').exists()
response = requests.get('https://api.figshare.com/v2/articles/20029387', timeout=45)
(OUT / 'figshare20029387.body').write_bytes(response.content)
(OUT / 'figshare20029387.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
body = response.json()
manifest = {key: body.get(key) for key in ('title', 'doi', 'version', 'description', 'files')}
(OUT / 'FIGSHARE_PROCESSED_MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
tree = ET.fromstring((OUT / 'replogle.body').read_bytes())
supp = [{'id': item.get('id'), 'description': ' '.join(' '.join(item.itertext()).split()),
         'files': [node.get('{http://www.w3.org/1999/xlink}href') for node in item.iter('media')]}
        for item in tree.iter('supplementary-material')]
(OUT / 'SUPPLEMENT_DESCRIPTIONS.json').write_text(json.dumps(supp, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
print(json.dumps(supp, indent=2))
