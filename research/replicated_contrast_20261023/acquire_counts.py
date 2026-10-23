"""Acquire the linked text artifact opaquely; emit only its first-line schema."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/replicated_contrast'
links = json.loads((OUT/'SOURCE_INDEX.json').read_text())['links']
url = next(x['url'] for x in links if 'MOESM3_ESM.txt' in x['url'] and 'Data 1' in x['label'])
body = OUT/'counts.body'
assert not body.exists()
receipt = dict(url=url, utc=datetime.now(timezone.utc).isoformat(), complete=False,
               scope='Opaque downloaded bytes and first header line only; no count values decoded/cast')
total, digest = 0, hashlib.sha256()
try:
    request = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO public-source research'})
    with urllib.request.urlopen(request, timeout=50) as response, body.open('wb') as target:
        receipt.update(status=response.status, final_url=response.url,
                       content_length=response.headers.get('Content-Length'),
                       content_type=response.headers.get('Content-Type'))
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                receipt['complete'] = True
                break
            target.write(chunk)
            digest.update(chunk)
            total += len(chunk)
            if total >= 512*(1 << 20):
                receipt['stop_reason'] = '512MiB bounded acquisition limit'
                break
except (urllib.error.URLError, TimeoutError, OSError) as error:
    receipt.update(error_type=type(error).__name__, error=str(error))
receipt.update(bytes=total, sha256=digest.hexdigest())
(OUT/'counts.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt), flush=True)
if receipt['complete'] and receipt.get('status') == 200:
    with body.open('rb') as source:
        header = source.readline(65537)
    assert len(header) < 65537
    fields = header.decode('utf-8-sig').rstrip('\r\n').split('\t')
    schema = dict(columns=fields, column_count=len(fields), body_sha256=digest.hexdigest(),
                  scope='First text header only; body values never selected or decoded')
    (OUT/'COUNT_HEADER.json').write_text(json.dumps(schema, indent=2), encoding='utf-8')
    print(json.dumps(schema))
