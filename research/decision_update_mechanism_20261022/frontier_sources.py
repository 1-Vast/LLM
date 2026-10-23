"""Two targeted primary bodies selected from already saved arXiv metadata."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import datetime
import requests
import sys

BASE = Path('log/20261022/decision_update_mechanism/frontier/sources')

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())

def retrieve(name, url):
    BASE.mkdir(parents=True, exist_ok=True)
    assert len(list(BASE.glob('*.receipt.json'))) < 2
    assert not (BASE / (name + '.receipt.json')).exists()
    record = {'url': url, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        response = requests.get(url, timeout=45)
        body = response.content
        (BASE / (name + '.body')).write_bytes(body)
        record.update(status=response.status_code, final_url=response.url, bytes=len(body),
                      sha256=hashlib.sha256(body).hexdigest())
        parser = Text()
        parser.feed(response.text)
        (BASE / (name + '.txt')).write_text('\n'.join(parser.parts), encoding='utf8')
    except Exception as error:
        record['error'] = repr(error)
    (BASE / (name + '.receipt.json')).write_text(json.dumps(record, indent=2), encoding='utf8')
    print(json.dumps(record, indent=2))

if __name__ == '__main__':
    retrieve(sys.argv[1], sys.argv[2])
