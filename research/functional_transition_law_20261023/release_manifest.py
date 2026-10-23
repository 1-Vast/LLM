"""Inspect only the exact public release named by the already-read kinetic primary."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2]/'log/20261023/functional_transition_law/root_sources'


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT/'zenodo.receipt.json'
    assert not target.exists(), 'Do not repeat an initiated request'
    url = 'https://zenodo.org/api/records/17610533'
    receipt = dict(utc=datetime.now(timezone.utc).isoformat(), url=url,
                   purpose='Read exact declared VUScope release file manifest for early-count to later-function law; no data files')
    try:
        response = requests.get(url, timeout=45)
        (OUT/'zenodo.body').write_bytes(response.content)
        receipt.update(status=response.status_code, bytes=len(response.content),
                       sha256=hashlib.sha256(response.content).hexdigest())
        if response.status_code == 200:
            body = response.json()
            projection = dict(id=body.get('id'), doi=body.get('doi'), title=body.get('metadata',{}).get('title'),
                              description=body.get('metadata',{}).get('description'),
                              files=[dict(key=f.get('key'), size=f.get('size'), checksum=f.get('checksum'), links=f.get('links')) for f in body.get('files',[])])
            (OUT/'zenodo.MANIFEST.json').write_text(json.dumps(projection, indent=2), encoding='utf-8')
            receipt.update(title=projection['title'], files=projection['files'])
    except Exception as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    target.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))
