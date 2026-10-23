"""Request the full view of the publisher's declared open-access article."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/replogle_growth_acquisition/root_sources'
assert not (OUT / 'full_view.body').exists()
response = requests.get('https://api.elsevier.com/content/article/pii/S0092867422005979',
                        params={'view': 'FULL', 'httpAccept': 'text/xml'}, timeout=45)
(OUT / 'full_view.body').write_bytes(response.content)
(OUT / 'full_view.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
print(response.status_code, len(response.content))
response.raise_for_status()
tree = ET.fromstring(response.content)
links = []
for node in tree.iter():
    for key, value in node.attrib.items():
        if key.endswith(('href', 'url', 'locator')):
            links.append({'tag': node.tag, 'key': key, 'value': value})
(OUT / 'FULL_VIEW_LINKS.json').write_text(json.dumps(links, indent=2), encoding='utf-8')
print(json.dumps(links, indent=2)[:20000])
