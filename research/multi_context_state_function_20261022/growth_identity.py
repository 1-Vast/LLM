"""Inspect the author-linked extra-data manifest and original table captions."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
assert not (OUT / 'figshare21632564.body').exists()
response = requests.get('https://api.figshare.com/v2/articles/21632564', timeout=45)
(OUT / 'figshare21632564.body').write_bytes(response.content)
(OUT / 'figshare21632564.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
body = response.json()
manifest = {key: body.get(key) for key in ('title', 'doi', 'version', 'description', 'files')}
(OUT / 'FIGSHARE_EXTRA_MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
tree = ET.fromstring((OUT / 'replogle.body').read_bytes())
captions = []
for item in tree.iter():
    if item.tag in ('caption', 'title', 'label'):
        text = ' '.join(' '.join(item.itertext()).split())
        if 'Table S' in text:
            captions.append(text)
(OUT / 'TABLE_CAPTIONS.json').write_text(json.dumps(captions, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
print(json.dumps(captions, indent=2))
