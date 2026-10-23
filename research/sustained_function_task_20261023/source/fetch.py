"""Bounded metadata/primary retrieval, never follow numerical file URLs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import urllib.request

out = Path('log/20261023/sustained_function_task/source')
out.mkdir(parents=True, exist_ok=True)
number, name, url, purpose = sys.argv[1:]
try:
    with urllib.request.urlopen(url, timeout=60) as response:
        body, status = response.read(), response.status
except Exception as exc:
    record = dict(request=int(number), url=url, error=repr(exc), purpose=purpose,
                  utc=datetime.now(timezone.utc).isoformat())
else:
    (out / name).write_bytes(body)
    record = dict(request=int(number), url=url, status=status, bytes=len(body),
                  sha256=hashlib.sha256(body).hexdigest(), purpose=purpose,
                  utc=datetime.now(timezone.utc).isoformat())
with (out / 'REQUESTS.jsonl').open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(record) + '\n')
print(json.dumps(record))
