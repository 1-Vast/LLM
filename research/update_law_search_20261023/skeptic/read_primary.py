import hashlib
import json
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

OUT = Path('log/20261023/update_law_search/skeptic')
class Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)

receipts = []
for paper in ['2609.34205v1', '2610.10905v1', '2610.09604v1']:
    url = f'https://arxiv.org/html/{paper}'
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            body, status = response.read(), response.status
        (OUT / f'{paper}.html').write_bytes(body)
        parser = Extract()
        parser.feed(body.decode('utf-8'))
        (OUT / f'{paper}.txt').write_text('\n'.join(parser.parts), encoding='utf-8')
        receipts.append({'url': url, 'status': status, 'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body)})
    except Exception as error:
        receipts.append({'url': url, 'error': repr(error)})
(OUT / 'PRIMARY_RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
print(json.dumps(receipts, indent=2))
