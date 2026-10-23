"""Bounded public primary-source retrieval with original receipts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import urllib.error

out = Path(__file__).resolve().parents[3] / 'log/20261023/response_law_revision/critic'
out.mkdir(parents=True, exist_ok=True)
name, url = sys.argv[1:]
req = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-research/1.0'})
try:
    with urllib.request.urlopen(req, timeout=40) as response:
        data, status, final_url = response.read(), response.status, response.url
except urllib.error.HTTPError as error:
    data, status, final_url = error.read(), error.code, error.url
(out / (name + '.body')).write_bytes(data)
receipt = dict(url=url, final_url=final_url, status=status,
               utc=datetime.now(timezone.utc).isoformat(), bytes=len(data),
               sha256=hashlib.sha256(data).hexdigest())
(out / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))


