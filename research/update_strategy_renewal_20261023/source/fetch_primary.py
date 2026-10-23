"""Bounded primary-text retrieval; no biological value files are downloaded."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import urllib.request

out = Path('log/20261023/update_strategy_renewal/source')
url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12537995/fullTextXML'
with urllib.request.urlopen(url, timeout=60) as response:
    body = response.read()
    status = response.status
(out / 'GET2_PMC12537995.xml').write_bytes(body)
record = dict(request=2, url=url, status=status,
              sha256=hashlib.sha256(body).hexdigest(),
              purpose='Authenticate serial NK killing, contact/detachment observations, methods and public data availability in selected 2025 primary paper',
              utc=datetime.now(timezone.utc).isoformat())
with (out / 'REQUESTS.jsonl').open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(record) + '\n')
print(json.dumps(record))
