"""Bounded primary-source GET with retained original and receipt."""
import datetime
import hashlib
import json
from pathlib import Path
import sys

import requests

OUT = Path('D:/MAESTRO/log/20261023/functional_state_sufficiency/biology')
OUT.mkdir(parents=True, exist_ok=True)
name, url = sys.argv[1:]
response = requests.get(url, timeout=60, headers={'User-Agent': 'MAESTRO scientific source audit'})
body = response.content
(OUT/(name+'.body')).write_bytes(body)
receipt = dict(url=url, final_url=response.url, status=response.status_code,
               utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
               scope='One logical public GET; redirects may add wire requests')
(OUT/(name+'.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt))
