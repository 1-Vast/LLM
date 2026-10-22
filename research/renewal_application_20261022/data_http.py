"""At most four immutable metadata/narrative primary-source GETs; no data arrays."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/renewal_application/data'
OUT.mkdir(parents=True, exist_ok=True)
p = argparse.ArgumentParser()
p.add_argument('name')
p.add_argument('url')
a = p.parse_args()
body, receipt = OUT / (a.name + '.body'), OUT / (a.name + '.http.json')
assert not body.exists() and not receipt.exists()
assert len(list(OUT.glob('*.http.json'))) < 4
record = {'url': a.url, 'utc': datetime.now(timezone.utc).isoformat(),
          'purpose': 'Primary narrative/metadata only, no expression or functional outcome arrays',
          'automatic_retries': False, 'automatic_redirects': False, 'authentication': False,
          'body_cap_bytes': 4 * 1024 * 1024}
payload = b''
try:
    with requests.get(a.url, stream=True, timeout=30, allow_redirects=False,
                      headers={'User-Agent': 'MAESTRO-primary-metadata-audit/1.0'}) as response:
        record.update(status=response.status_code, headers={k: v for k, v in response.headers.items()
            if k.lower() not in ('set-cookie', 'cookie', 'authorization')})
        for part in response.iter_content(65536):
            remaining = record['body_cap_bytes'] - len(payload)
            payload += part[:remaining]
            if len(part) > remaining:
                record['truncated'] = True
                break
except Exception as error:
    record['error'] = repr(error)
body.write_bytes(payload)
record.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
receipt.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
