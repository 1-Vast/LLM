"""One targeted metadata request, no biological data download or model call."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_signal_reassessment/root_sources'
OUT.mkdir(parents=True, exist_ok=True)
assert not (OUT / 'STARTED.json').exists()
query = '(TITLE_ABS:"Perturb-seq") AND (TITLE_ABS:fitness OR TITLE_ABS:viability) AND FIRST_PDATE:[2025-01-01 TO 2026-10-22]'
started = {'query': query, 'utc': datetime.now(timezone.utc).isoformat(), 'max_results': 10}
(OUT / 'STARTED.json').write_text(json.dumps(started, indent=2), encoding='utf-8')
try:
    response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                            params={'query': query, 'format': 'json', 'pageSize': 10, 'resultType': 'core'}, timeout=60)
    (OUT / 'search.body').write_bytes(response.content)
    receipt = dict(started, status=response.status_code, url=response.url, bytes=len(response.content),
                   sha256=hashlib.sha256(response.content).hexdigest())
    (OUT / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    response.raise_for_status()
    body = response.json()
    result = {'hitCount': body.get('hitCount'), 'entries': [
        {key: item.get(key) for key in ('id', 'title', 'doi', 'pmcid', 'firstPublicationDate', 'abstractText')}
        for item in body.get('resultList', {}).get('result', [])]}
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
except Exception as error:
    failure = dict(started, error_type=type(error).__name__)
    (OUT / 'FAILURE.json').write_text(json.dumps(failure, indent=2), encoding='utf-8')
    raise
