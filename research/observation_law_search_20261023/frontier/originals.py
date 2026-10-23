from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import requests
from html.parser import HTMLParser

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

OUT = Path('log/20261023/observation_law_search/frontier')
IDS = ['2610.29435v1', '2610.27914v1', '2610.30125v1']

def fetch(identifier):
    url = f'https://arxiv.org/html/{identifier}'
    receipt = {'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
    try:
        r = requests.get(url, timeout=45)
        (OUT / f'{identifier}.html').write_bytes(r.content)
        receipt.update(status=r.status_code, bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest())
        if r.ok:
            parser = TextParser()
            parser.feed(r.text)
            (OUT / f'{identifier}.txt').write_text('\n'.join(parser.parts), encoding='utf-8')
    except Exception as e:
        receipt['error'] = repr(e)
    (OUT / f'{identifier}.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        print(json.dumps(list(pool.map(fetch, IDS)), indent=2))
