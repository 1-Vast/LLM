"""Resolve the one previously identified multi-context primary preprint."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/plk1_payload_qualification/alternative'
OUT.mkdir(parents=True, exist_ok=True)
assert not (OUT / 'biorxiv.body').exists()
response = requests.get('https://api.biorxiv.org/details/biorxiv/10.64898/2026.08.24.746802', timeout=45)
(OUT / 'biorxiv.body').write_bytes(response.content)
(OUT / 'biorxiv.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
result = response.json()
collection = result.get('collection', [])
print(json.dumps({'messages': result.get('messages'), 'records': len(collection)}, indent=2))
for item in collection:
    print(json.dumps({key: item.get(key) for key in ('title', 'doi', 'version', 'date', 'jatsxml', 'published')}, indent=2))
