"""Acquire the author-linked small annotation CSV and inspect only its header."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
manifest = json.loads((OUT / 'FIGSHARE_EXTRA_MANIFEST.json').read_text(encoding='utf-8'))
entry = next(item for item in manifest['files'] if item['id'] == 38349302)
assert not (OUT / entry['name']).exists()
response = requests.get(entry['download_url'], timeout=45)
(OUT / entry['name']).write_bytes(response.content)
receipt = {'url': entry['download_url'], 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
           'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest(),
           'md5': hashlib.md5(response.content).hexdigest()}
(OUT / 'annotation.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
response.raise_for_status()
assert receipt['bytes'] == entry['size'] and receipt['md5'] == entry['computed_md5']
header = response.content.splitlines()[0].decode('utf-8')
(OUT / 'ANNOTATION_HEADER.json').write_text(json.dumps({'header': header}, indent=2), encoding='utf-8')
print(header)
