"""Save one explicit HTTP response and receipt; never follow redirects."""
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
import requests

url, stem = sys.argv[1:]
out = Path(__file__).resolve().parents[3] / 'log/20261023/grounded_feedback_renewal/critic'
body = out / (stem + '.body')
assert not body.exists()
response = requests.get(url, timeout=90, allow_redirects=False,
                        headers={'User-Agent': 'MAESTRO research primary-source audit'})
body.write_bytes(response.content)
(out / (stem + '.receipt.json')).write_text(json.dumps(dict(
    url=url, utc=datetime.now(timezone.utc).isoformat(), status=response.status_code,
    headers=dict(response.headers), bytes=len(response.content),
    sha256=hashlib.sha256(response.content).hexdigest(), logical_requests=1,
    redirect_followed=False), indent=2), encoding='utf-8')
print(response.status_code, len(response.content), body)
