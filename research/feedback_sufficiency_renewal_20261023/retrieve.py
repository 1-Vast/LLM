"""Public-source receipts; no biological endpoint parsing."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/feedback_sufficiency_renewal/root'


def get(name, url):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    if path.exists():
        raise FileExistsError(path)
    receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'url': url}
    try:
        response = requests.get(url, timeout=45, headers={'User-Agent': 'MAESTRO-research/1.0'})
        path.write_bytes(response.content)
        receipt.update(status=response.status_code, bytes=len(response.content),
                       sha256=hashlib.sha256(response.content).hexdigest(),
                       final_url=response.url, content_type=response.headers.get('Content-Type'))
    except requests.RequestException as error:
        receipt['error'] = str(error)
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    get(sys.argv[1], sys.argv[2])
