"""Unauthenticated, bounded primary narrative/metadata GET; never data responses."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

p = argparse.ArgumentParser()
p.add_argument('name')
p.add_argument('url')
a = p.parse_args()
out = Path(__file__).resolve().parents[2] / 'log/20261022/update_value_qualification/data'
out.mkdir(parents=True, exist_ok=True)
body_path, receipt_path = out / (a.name + '.body'), out / (a.name + '.http.json')
if body_path.exists() or receipt_path.exists() or len(list(out.glob('*.http.json'))) >= 4:
    raise SystemExit('Immutable captures / four-request budget')
receipt = {'url': a.url, 'utc': datetime.now(timezone.utc).isoformat(),
           'purpose': 'Primary paper or source metadata only', 'authentication': False,
           'automatic_redirects': False, 'body_cap_bytes': 4 * 1024 * 1024}
raw = b''
try:
    with requests.get(a.url, timeout=30, stream=True, allow_redirects=False,
                      headers={'User-Agent': 'MAESTRO-metadata-review/1.0'}) as r:
        receipt.update(status=r.status_code, headers={k: v for k, v in r.headers.items()
            if k.lower() not in ('set-cookie', 'cookie', 'authorization')})
        for block in r.iter_content(65536):
            raw += block
            if len(raw) > receipt['body_cap_bytes']:
                raise ValueError('Narrative/metadata body exceeded bound')
except Exception as e:
    receipt['error'] = repr(e)
body_path.write_bytes(raw)
receipt.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt))
