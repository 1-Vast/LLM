import datetime
import hashlib
import json
from pathlib import Path
import requests
from html.parser import HTMLParser

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)

out = Path('log/20261023/mixed_feedback_estimator/prior')
receipts = []
for name, url in [('tlora', 'https://aclanthology.org/2026.acl-long.1348/'),
                  ('loraga', 'https://arxiv.org/html/2407.05000v2')]:
    response = requests.get(url, timeout=50)
    body = response.content
    (out / (name + '.html')).write_bytes(body)
    parser = Text()
    parser.feed(response.text)
    text = ' '.join(' '.join(parser.parts).split())
    (out / (name + '.txt')).write_text(text, encoding='utf-8')
    receipts.append({'name': name, 'url': url, 'status': response.status_code,
                     'sha256': hashlib.sha256(body).hexdigest(),
                     'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
(out / 'PRIMARY_RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
for receipt in receipts:
    print(receipt)
    print((out / (receipt['name'] + '.txt')).read_text(encoding='utf-8')[:13000])
