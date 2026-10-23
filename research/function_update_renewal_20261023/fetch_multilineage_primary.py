"""Acquire the primary lead page, never assay outcome matrices."""
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/function_update_renewal/root_sources'


class Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']:
            self.skip += 1
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())


url = 'https://www.nature.com/articles/s41588-024-01971-9'
response = requests.get(url, timeout=45)
(OUT / 'multilineage.body').write_bytes(response.content)
(OUT / 'multilineage.receipt.json').write_text(json.dumps({'url': url, 'final_url': response.url,
    'status': response.status_code, 'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest(),
    'utc': datetime.now(timezone.utc).isoformat()}, indent=2))
if response.status_code == 200:
    parser = Extract()
    parser.feed(response.text)
    (OUT / 'multilineage.text.txt').write_text('\n'.join(parser.parts), encoding='utf-8')
    (OUT / 'multilineage.links.json').write_text(json.dumps(sorted(set(parser.links)), indent=2))
print(json.dumps({'status': response.status_code, 'bytes': len(response.content)}))
