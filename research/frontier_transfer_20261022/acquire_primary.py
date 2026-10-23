"""Retain exact primary-source HTTP bodies and acquisition receipts."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import requests

ROOT = Path('D:/MAESTRO/log/20261022/frontier_transfer')
ROOT.mkdir(parents=True, exist_ok=True)
SOURCES = ROOT / 'sources'
SOURCES.mkdir(exist_ok=True)

def fetch(label, url):
    receipt = {'label': label, 'requested_url': url,
               'utc': datetime.now(timezone.utc).isoformat()}
    try:
        r = requests.get(url, timeout=90, headers={'User-Agent': 'MAESTRO research primary source audit/1.0'})
        path = SOURCES / (label + '.body')
        path.write_bytes(r.content)
        receipt.update(status=r.status_code, final_url=r.url,
                       headers=dict(r.headers), bytes=len(r.content),
                       sha256=hashlib.sha256(r.content).hexdigest(), file=str(path))
    except Exception as exc:
        receipt['error'] = repr(exc)
    (SOURCES / (label + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))

if __name__ == '__main__':
    for name, paper in [('titans', '2501.00663'), ('seal', '2506.10943'), ('dgm', '2505.22954')]:
        fetch(name + '_abs', 'https://arxiv.org/abs/' + paper)
        fetch(name + '_html_v1', 'https://arxiv.org/html/' + paper + 'v1')
