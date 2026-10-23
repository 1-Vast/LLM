"""Follow the authenticated DOI to its primary article."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import requests

root = Path('log/20261022/next_mechanism/recursive')
url = 'https://www.nature.com/articles/s41586-025-09761-x'
receipt = dict(url=url, started=datetime.now(timezone.utc).isoformat())
try:
    r = requests.get(url, timeout=60)
    (root / 'discorl.html').write_bytes(r.content)
    receipt.update(status=r.status_code, final_url=r.url, bytes=len(r.content),
                   sha256=hashlib.sha256(r.content).hexdigest())
except requests.RequestException as exc:
    receipt['error'] = str(exc)
(root / 'DISCORL_ACQUISITION.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
