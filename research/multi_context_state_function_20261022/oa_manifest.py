"""Resolve the official PMC open-access package, if offered; do not download it."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
assert not (OUT / 'oa_manifest.body').exists()
response = requests.get('https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi', params={'id': 'PMC9380471'}, timeout=45)
(OUT / 'oa_manifest.body').write_bytes(response.content)
(OUT / 'oa_manifest.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
print(response.text[:5000])
