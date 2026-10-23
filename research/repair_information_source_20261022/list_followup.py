"""Two exact author-code/list requests; do not execute JS or download data."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import requests

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/repair_information_opportunity/source/list_followup'

def fetch(label, url, cap):
    prior = list(OUT.glob('request_*.receipt.json'))
    assert len(prior) < 2, 'Follow-up two-request bound exhausted'
    stem = OUT / f'request_{len(prior)+1}_{label}'
    receipt = dict(url=url, started_utc=datetime.now(timezone.utc).isoformat(),
                   body_cap=cap, automatic_redirects=False)
    body = bytearray()
    try:
        with requests.get(url, stream=True, timeout=45, allow_redirects=False) as response:
            receipt.update(status=response.status_code, final_url=response.url,
                           headers=dict(response.headers), encoding=response.encoding)
            for chunk in response.iter_content(16384):
                if len(body) + len(chunk) > cap:
                    receipt['body_capped'] = True
                    break
                body.extend(chunk)
    except requests.RequestException as exc:
        receipt['error'] = repr(exc)
    stem.with_suffix('.body').write_bytes(body)
    receipt.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    stem.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    fetch(sys.argv[1], sys.argv[2], int(sys.argv[3]))
