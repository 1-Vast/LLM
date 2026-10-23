"""Bounded public landing requests for full PTDS independent identity metadata."""
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
import sys
import requests

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/repair_information_opportunity/source'

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.links = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style'):
            self.skip += 1
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.text.append(data.strip())

def fetch(label, url):
    receipts = sorted(OUT.glob('request_*.receipt.json'))
    assert len(receipts) < 3, 'Three-request bound already reached'
    stem = OUT / f'request_{len(receipts)+1}_{label}'
    receipt = dict(url=url, started_utc=datetime.now(timezone.utc).isoformat(),
                   automatic_redirects=False, body_cap=1000000)
    body = bytearray()
    try:
        with requests.get(url, stream=True, timeout=45, allow_redirects=False) as response:
            receipt.update(status=response.status_code, final_url=response.url, headers=dict(response.headers))
            for chunk in response.iter_content(16384):
                if len(body) + len(chunk) > 1000000:
                    receipt['body_capped'] = True
                    break
                body.extend(chunk)
            receipt['encoding'] = response.encoding
    except requests.RequestException as exc:
        receipt['error'] = repr(exc)
    stem.with_suffix('.body').write_bytes(body)
    receipt.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    stem.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    text = body.decode(receipt.get('encoding') or 'utf-8', errors='replace')
    page = Page()
    page.feed(text)
    extracted = dict(text=page.text, links=page.links)
    stem.with_suffix('.page.json').write_text(json.dumps(extracted, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(receipt=receipt, page=extracted), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    fetch(sys.argv[1], sys.argv[2])
