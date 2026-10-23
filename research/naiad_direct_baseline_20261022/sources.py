"""Acquire primary paper and author metadata with byte receipts."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/naiad_direct_baseline/root_sources'
OUT.mkdir(parents=True, exist_ok=True)
urls = [('paper_page', 'https://proceedings.mlr.press/v267/qin25g.html'),
        ('paper', 'https://raw.githubusercontent.com/mlresearch/v267/main/assets/qin25g/qin25g.pdf'),
        ('repo', 'https://api.github.com/repos/NeptuneBio/NAIAD'),
        ('tree', 'https://api.github.com/repos/NeptuneBio/NAIAD/git/trees/HEAD?recursive=1')]


def fetch(item):
    name, url = item
    response = requests.get(url, timeout=60)
    data = response.content
    (OUT / (name + '.body')).write_bytes(data)
    receipt = {'url': url, 'status': response.status_code, 'bytes': len(data),
               'sha256': hashlib.sha256(data).hexdigest(), 'utc': datetime.now(timezone.utc).isoformat()}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if name == 'paper' and response.status_code == 200 and data.startswith(b'%PDF'):
        import io
        from pypdf import PdfReader
        text = '\n\n'.join(page.extract_text() or '' for page in PdfReader(io.BytesIO(data)).pages)
        (OUT / 'paper.text').write_text(text, encoding='utf-8')
    return receipt


with ThreadPoolExecutor(max_workers=4) as pool:
    for result in pool.map(fetch, urls):
        print(json.dumps(result))
