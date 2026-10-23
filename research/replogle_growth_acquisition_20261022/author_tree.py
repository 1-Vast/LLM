"""Inspect the newly discovered author's CRISPRi dual-guide repository tree."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/replogle_growth_acquisition/root_sources'
assert not (OUT / 'author_tree.body').exists()
url = 'https://api.github.com/repos/josephreplogle/CRISPRi-dual-sgRNA-screens/git/trees/main?recursive=1'
response = requests.get(url, timeout=45)
(OUT / 'author_tree.body').write_bytes(response.content)
(OUT / 'author_tree.receipt.json').write_text(json.dumps({
    'url': url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
body = response.json()
paths = [item['path'] for item in body.get('tree', [])]
assert not body.get('truncated')
(OUT / 'AUTHOR_REPOSITORY_PATHS.json').write_text(json.dumps(paths, indent=2), encoding='utf-8')
print(json.dumps(paths, indent=2))
