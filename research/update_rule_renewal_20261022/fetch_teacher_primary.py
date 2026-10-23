"""Fetch one identified primary, preserving failures rather than guessing claims."""
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_rule_renewal/root_prior'
assert not (OUT / 'static_synthetic.body').exists()
url = 'https://arxiv.org/html/2009.09675v1'
response = requests.get(url, timeout=60)
(OUT / 'static_synthetic.body').write_bytes(response.content)
(OUT / 'static_synthetic.receipt.json').write_text(json.dumps({
    'url': url, 'status': response.status_code, 'bytes': len(response.content),
    'sha256': hashlib.sha256(response.content).hexdigest(),
    'utc': datetime.now(timezone.utc).isoformat()}, indent=2), encoding='utf-8')
response.raise_for_status()


class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
    def handle_data(self, value):
        if value.strip():
            self.text.append(value.strip())


reader = Reader()
reader.feed(response.text)
content = '\n'.join(reader.text)
(OUT / 'static_synthetic.txt').write_text(content, encoding='utf-8')
lines = content.splitlines()
selected = []
for i, line in enumerate(lines):
    if any(word in line.lower() for word in ('meta-learning', 'meta learning', 'outer loop', 'query', 'support', 'second-order', 'second order')):
        selected.append({'line': i, 'text': '\n'.join(lines[max(0, i-3):i+7])})
(OUT / 'SELECTED_PASSAGES.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
print(json.dumps(selected[:25], indent=2))
