"""Archive public primary algorithm text, status and hashes; no biological data."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/early_update_mechanism/frontier/source'
IDS = ['2501.00663', '2512.24695', '2506.10943', '2505.22954', '2601.16175', '2610.05950']


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.chunks = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = False

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.chunks.append(data.strip())


def retrieve(identifier):
    url = 'https://arxiv.org/html/' + identifier
    target = OUT / (identifier + '.html')
    assert not target.exists()
    response = requests.get(url, timeout=60)
    target.write_bytes(response.content)
    parser = TextParser()
    parser.feed(response.text)
    text = '\n'.join(parser.chunks)
    text_path = target.with_suffix('.txt')
    text_path.write_text(text, encoding='utf-8')
    return {'id': identifier, 'url': response.url, 'status': response.status_code,
            'utc': datetime.now(timezone.utc).isoformat(), 'bytes': len(response.content),
            'sha256': hashlib.sha256(response.content).hexdigest(),
            'text_sha256': hashlib.sha256(text_path.read_bytes()).hexdigest()}


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(retrieve, IDS))
    (OUT / 'METHODS_MANIFEST.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    for record in records:
        print(json.dumps(record))
