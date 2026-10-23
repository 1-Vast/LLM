"""Inspect the final author-linked metadata record for the independent assay files."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
assert not (OUT / 'figshare20022944.body').exists()
response = requests.get('https://api.figshare.com/v2/articles/20022944', timeout=45)
(OUT / 'figshare20022944.body').write_bytes(response.content)
(OUT / 'figshare20022944.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
body = response.json()
manifest = {key: body.get(key) for key in ('title', 'doi', 'version', 'description', 'files')}
(OUT / 'FIGSHARE_SEQUENCING_MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
