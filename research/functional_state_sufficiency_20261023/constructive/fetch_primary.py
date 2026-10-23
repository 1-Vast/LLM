"""Fetch the one primary selected by the bounded arXiv source query."""
from pathlib import Path
import datetime
import hashlib
import json
import requests
from html.parser import HTMLParser

OUT = Path(__file__).resolve().parents[3]/'log/20261023/functional_state_sufficiency/constructive'
url = 'https://arxiv.org/html/2610.19046v1'
receipt = dict(question='Does calibrated reward-agnostic exploration supply a usable '
                       'state-sufficiency mechanism when functional objectives adapt?',
               url=url, utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
try:
    response = requests.get(url, timeout=45, allow_redirects=False)
    body = response.content
    (OUT/'GET2.body').write_bytes(body)
    receipt.update(status=response.status_code, bytes=len(body),
                   sha256=hashlib.sha256(body).hexdigest(), final_url=response.url)
    class Text(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []
        def handle_data(self, data):
            if data.strip():
                self.parts.append(data.strip())
    parser = Text()
    parser.feed(response.text)
    (OUT/'PRIMARY_TEXT.txt').write_text('\n'.join(parser.parts), encoding='utf-8')
except requests.RequestException as exc:
    receipt.update(error=type(exc).__name__+': '+str(exc))
(OUT/'GET2.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
