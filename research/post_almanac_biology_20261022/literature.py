"""Bounded primary metadata/method requests; no biological datasets."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import requests

out = Path('log/20261022/post_almanac_mechanism/biology/sources')
out.mkdir(parents=True, exist_ok=True)
name, mode, target = sys.argv[1:4]
url = target if mode == 'url' else 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + urlencode(
    {'query': target, 'format': 'json', 'resultType': 'core', 'pageSize': 8})
assert not (out / (name + '.body')).exists()
receipt = {'url': url, 'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'Primary text or metadata only'}
try:
    r = requests.get(url, timeout=40)
    body = r.content
    (out / (name + '.body')).write_bytes(body)
    receipt.update(status=r.status_code, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    if mode != 'url':
        data = r.json()
        summary = [{k: p.get(k) for k in ('id', 'pmcid', 'doi', 'title', 'firstPublicationDate', 'abstractText')}
                   for p in data.get('resultList', {}).get('result', [])]
        (out / (name + '.summary.json')).write_text(json.dumps(summary, indent=2), encoding='utf-8')
        print(json.dumps(summary, indent=2))
except Exception as exc:
    receipt['failure'] = repr(exc)
(out / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt))
