"""Read public Dash callback metadata to resolve the documented dataset page."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
assert not (OUT / 'dependencies.body').exists()
response = requests.get('https://gwps.wi.mit.edu/_dash-dependencies', timeout=45)
(OUT / 'dependencies.body').write_bytes(response.content)
(OUT / 'dependencies.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
print(json.dumps(response.json(), indent=2)[:14000])
