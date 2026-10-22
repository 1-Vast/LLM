"""Acquire two version-pinned primary fulltexts selected by retained abstracts."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import requests

class Projection(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lines, self.title, self.ignore, self.in_title = [], [], False, False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.ignore = True
        if tag == 'title':
            self.in_title = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.ignore = False
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if not self.ignore and data.strip():
            self.lines.append(data.strip())
            if self.in_title:
                self.title.append(data.strip())

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/native_operation/root/sources'
SOURCES = {'network_algorithm_world': '2610.01048v1', 'autonovo': '2610.16232v1'}


def main():
    label = sys.argv[1]
    url = 'https://arxiv.org/html/' + SOURCES[label]
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / (label + '.receipt.json')).exists()
    receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'requested_url': url,
               'selection': 'Retained abstract specifies world-evaluated program search/independent-model transfer',
               'max_bytes': 6000000, 'timeout_seconds': 45}
    try:
        response = requests.get(url, timeout=45)
        assert len(response.content) <= receipt['max_bytes']
        with (OUT / (label + '.body')).open('xb') as handle:
            handle.write(response.content)
        projection = Projection()
        projection.feed(response.text)
        text = '\n'.join(projection.lines)
        with (OUT / (label + '.txt')).open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(text)
        receipt.update(status=response.status_code, final_url=response.url, bytes=len(response.content),
                       sha256=hashlib.sha256(response.content).hexdigest(),
                       projection_sha256=hashlib.sha256(text.encode()).hexdigest(),
                       html_title=' '.join(projection.title))
    except Exception as exc:
        receipt.update(error_type=type(exc).__name__)
    with (OUT / (label + '.receipt.json')).open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, indent=2)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
