"""Fetch author filter implementation only; no assay data are accessed."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

out = Path('log/20261023/rank_reversal_mechanism/source')
out.mkdir(parents=True, exist_ok=True)
commit = '218cf1bb8c83204da846256951ba5f6b0092890b'
url = f'https://raw.githubusercontent.com/samsonfong/SCHEMATIC/{commit}/src/decipher/datasets/decipher_data.py'
r = requests.get(url, timeout=40)
(out / 'author_decipher_data.py.body').write_bytes(r.content)
receipt = dict(url=url, final_url=r.url, status=r.status_code,
               bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest(),
               utc=datetime.now(timezone.utc).isoformat(), assay_values_read=False)
(out / 'FETCH_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt))
r.raise_for_status()
