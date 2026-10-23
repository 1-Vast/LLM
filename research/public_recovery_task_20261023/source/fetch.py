"""Bounded GitHub metadata/code retrieval; never fetch outcome datasets."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import urllib.request
import urllib.error

out = Path('log/20261023/public_recovery_task/source')
out.mkdir(parents=True, exist_ok=True)
number, name, url, purpose = sys.argv[1:]
record = dict(request=int(number), url=url, purpose=purpose,
              utc=datetime.now(timezone.utc).isoformat())
try:
    response = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-source-qualification'}), timeout=60)
except urllib.error.HTTPError as exc:
    response = exc
except Exception as exc:
    record['error'] = repr(exc)
if 'error' not in record:
    with response:
        body = response.read()
        record.update(status=response.status, final_url=response.geturl(),
                      bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    (out / name).write_bytes(body)
with (out / 'REQUESTS.jsonl').open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(record) + '\n')
print(json.dumps(record))
