"""Bounded primary-source retrieval; no datasets or model weights."""
from pathlib import Path
from html.parser import HTMLParser
import datetime
import hashlib
import json
import sys
import requests

BASE = Path('log/20261022/query_teacher_resolution/frontier/sources')

class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        value = data.strip()
        if value:
            self.parts.append(value)

def get(name, url):
    BASE.mkdir(parents=True, exist_ok=True)
    assert len(list(BASE.glob('*.receipt.json'))) < 3
    assert not (BASE / (name + '.receipt.json')).exists()
    record = {'url': url, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        response = requests.get(url, timeout=50)
        body = response.content
        (BASE / (name + '.body')).write_bytes(body)
        record.update(status=response.status_code, final_url=response.url,
                      bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        parser = Reader()
        parser.feed(response.text)
        (BASE / (name + '.txt')).write_text('\n'.join(parser.parts), encoding='utf8')
    except Exception as error:
        record['error'] = repr(error)
    (BASE / (name + '.receipt.json')).write_text(json.dumps(record, indent=2), encoding='utf8')
    print(json.dumps(record, indent=2))

if __name__ == '__main__':
    get(sys.argv[1], sys.argv[2])
