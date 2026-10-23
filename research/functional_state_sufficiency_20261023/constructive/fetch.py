"""One bounded public original-source question; preserve body and receipt."""
from pathlib import Path
import datetime
import hashlib
import json
import requests

OUT = Path(__file__).resolve().parents[3]/'log/20261023/functional_state_sufficiency/constructive'
OUT.mkdir(parents=True, exist_ok=True)
url = ('https://export.arxiv.org/api/query?search_query=all:%22state%20abstraction%22'
       '+AND+submittedDate:[202501010000+TO+202610232359]&max_results=3&sortBy=submittedDate&sortOrder=descending')
receipt = dict(question='Does a 2025-2026 primary state-abstraction method offer an explicit '
                       'update/closure operator beyond task-aware embedding?', url=url,
               utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
try:
    response = requests.get(url, timeout=45, allow_redirects=False)
    body = response.content
    (OUT/'GET1.body').write_bytes(body)
    receipt.update(status=response.status_code, bytes=len(body),
                   sha256=hashlib.sha256(body).hexdigest(), final_url=response.url)
except requests.RequestException as exc:
    receipt.update(error=type(exc).__name__+': '+str(exc))
(OUT/'GET1.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
