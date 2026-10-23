"""Bounded original-paper search/metadata only; never downloads datasets."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_decrypte_renewal/skeptic/source'
OUT.mkdir(parents=True, exist_ok=True)
query = 'TITLE:"CellPhe"'
url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + urllib.parse.urlencode({'query': query, 'format': 'json', 'resultType': 'core'})
start = datetime.now(timezone.utc).isoformat()
with urllib.request.urlopen(url, timeout=45) as response:
    body = response.read()
    receipt = {'url': url, 'final_url': response.url, 'status': response.status,
               'headers': dict(response.headers), 'started_utc': start,
               'completed_utc': datetime.now(timezone.utc).isoformat(),
               'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
(OUT / 'cellphe_search.body').write_bytes(body)
(OUT / 'cellphe_search.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
for r in json.loads(body)['resultList']['result']:
    print(json.dumps({k: r.get(k) for k in ('title','doi','pmcid','firstPublicationDate','abstractText')}, ensure_ascii=False))
