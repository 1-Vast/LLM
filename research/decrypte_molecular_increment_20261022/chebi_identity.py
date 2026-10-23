"""Fetch one official ChEBI identity entry; metadata only."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_molecular_increment/review/lexical_sources'
URL = 'https://www.ebi.ac.uk/chebi/backend/api/public/compound/31355/'
start = datetime.now(timezone.utc).isoformat()
try:
    with urllib.request.urlopen(URL, timeout=45) as r:
        body = r.read()
        receipt = {'url': URL, 'final_url': r.url, 'status': r.status, 'headers': dict(r.headers)}
    (OUT / 'CHEBI31355.body').write_bytes(body)
    receipt.update(start_utc=start, end_utc=datetime.now(timezone.utc).isoformat(), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    (OUT / 'CHEBI31355.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    parsed = json.loads(body)
    print(json.dumps(parsed, ensure_ascii=False)[:18000])
except Exception as error:
    (OUT / 'CHEBI31355.failure.json').write_text(json.dumps({'url': URL, 'start_utc': start, 'error': str(error)}, indent=2), encoding='utf-8')
    raise
