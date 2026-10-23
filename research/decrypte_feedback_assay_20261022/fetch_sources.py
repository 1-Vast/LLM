"""Archive source-only metadata/method requests, never assay result endpoints."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

OUT = Path('log/20261022/decrypte_feedback_pilot/assay/source')
OUT.mkdir(parents=True, exist_ok=True)


def fetch(name, url):
    receipt = {'url': url, 'started_utc': datetime.now(timezone.utc).isoformat()}
    try:
        r = requests.get(url, timeout=(15, 45), headers={'User-Agent': 'MAESTRO-source-qualification/1.0'})
        body = r.content
        (OUT / (name + '.body')).write_bytes(body)
        receipt.update(status=r.status_code, final_url=r.url, headers=dict(r.headers),
                       bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    except requests.RequestException as exc:
        receipt['failure'] = repr(exc)
    receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ['url', 'status', 'bytes', 'failure'] if k in receipt}))


if __name__ == '__main__':
    import sys
    fetch(sys.argv[1], sys.argv[2])
