import datetime
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

name, url = sys.argv[1:]
out = Path('log/20261023/grounded_feedback_renewal/constructive')
out.mkdir(parents=True, exist_ok=True)
request = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO research/1.0'})
try:
    with urllib.request.urlopen(request, timeout=45) as response:
        body, status = response.read(), response.status
except urllib.error.HTTPError as response:
    body, status = response.read(), response.code
(out / (name + '.body')).write_bytes(body)
receipt = dict(url=url, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               status=status, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
(out / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
