"""Read only the author's repository README, pinned to the retrieved tree."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/replogle_growth_acquisition/root_sources'
tree = json.loads((OUT / 'author_tree.body').read_bytes())
url = 'https://raw.githubusercontent.com/josephreplogle/CRISPRi-dual-sgRNA-screens/' + tree['sha'] + '/README.md'
assert not (OUT / 'author_readme.body').exists()
response = requests.get(url, timeout=45)
(OUT / 'author_readme.body').write_bytes(response.content)
(OUT / 'author_readme.receipt.json').write_text(json.dumps({
    'url': url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
print(response.text[:12000])
