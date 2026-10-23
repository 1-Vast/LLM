"""Check the remaining explicitly named repository metadata, no data files."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2]/'log/20261023/mechanism_reentry'
url = 'https://api.figshare.com/v2/articles/26096371'
receipt = dict(url=url, utc=datetime.now(timezone.utc).isoformat())
projection = {}
try:
    response = requests.get(url, timeout=35)
    (OUT/'all597_second_metadata.body').write_bytes(response.content)
    receipt.update(status=response.status_code, bytes=len(response.content),
                   sha256=hashlib.sha256(response.content).hexdigest())
    if response.status_code == 200:
        payload = response.json()
        projection = dict(title=payload.get('title'), description=payload.get('description'),
                          files=[{key: row.get(key) for key in ['name', 'size', 'download_url']}
                                 for row in payload.get('files', [])])
except Exception as error:
    receipt.update(error_type=type(error).__name__, error=str(error))
(OUT/'all597_second_metadata.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
(OUT/'ALL597_SECOND_METADATA.json').write_text(json.dumps(projection, indent=2), encoding='utf-8')
print(json.dumps(dict(receipt=receipt, metadata=projection), indent=2))
