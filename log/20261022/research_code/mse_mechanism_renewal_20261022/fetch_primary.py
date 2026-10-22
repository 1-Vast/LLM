"""Retain bounded public primary/metadata retrieval with exact-body receipts."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
import requests

label, url = sys.argv[1:3]
out = Path(__file__).resolve().parents[2] / 'log/20261022/mse_mechanism_renewal/sources'
out.mkdir(exist_ok=True)
receipt = dict(label=label, requested_url=url, utc=datetime.now(timezone.utc).isoformat())
if (out / (label + '.receipt.json')).exists():
    raise FileExistsError(label)
try:
    response = requests.get(url, timeout=45, headers={'User-Agent': 'MAESTRO mechanism qualification/1.0'})
    body = response.content
    with (out / (label + '.body')).open('xb') as f:
        f.write(body)
    receipt.update(status=response.status_code, final_url=response.url, headers=dict(response.headers),
                   bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
except Exception as exc:
    receipt.update(error_type=type(exc).__name__)
with (out / (label + '.receipt.json')).open('x', encoding='utf-8') as f:
    json.dump(receipt, f, indent=2)
print(json.dumps({k:v for k,v in receipt.items() if k != 'headers'}))
