"""Bounded official source retrieval, never executing downloaded code."""
import datetime
import hashlib
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/update_strategy_renewal/critic'

name, url = sys.argv[1:3]
receipt = {'requested_url': url, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
    request = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-literature-audit/1.0'})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read(8 * 1024 * 1024)
        receipt.update(status=response.status, final_url=response.url, headers=dict(response.headers))
    (OUT / (name + '.body')).write_bytes(body)
    receipt.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
except Exception as error:
    receipt.update(error=type(error).__name__ + ': ' + str(error))
(OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt))


