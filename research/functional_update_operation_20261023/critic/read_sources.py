"""Project local original articles without script/style text; no HTTP or fitting."""
import hashlib
import json
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261023/functional_update_operation/critic'
SRC = ROOT / 'log/20261023/function_update_renewal/constructive'

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if tag in ('p', 'section', 'h1', 'h2', 'h3', 'div') and not self.skip:
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

receipts = []
for name in ('skillgrad', 'patchworld'):
    path = SRC / (name + '.body')
    blob = path.read_bytes()
    receipt = json.loads((SRC / (name + '.receipt.json')).read_text())
    digest = hashlib.sha256(blob).hexdigest()
    assert digest == receipt['sha256']
    parser = Text()
    parser.feed(blob.decode())
    lines = [' '.join(x.split()) for x in ''.join(parser.parts).splitlines()]
    lines = [x for x in lines if x]
    (OUT / (name + '.selected.txt')).write_text('\n'.join(lines), encoding='utf-8')
    receipts.append({'name': name, 'source_path': str(path), 'original_receipt': receipt,
                     'sha256_verified': digest, 'new_http_requests': 0})
    print(name)
    for i, line in enumerate(lines):
        if any(word in line.lower() for word in ('skill-wise', 'skillgrad', 'projection', 'patching', 'patchworld', 'methodology', 'orthogonal', 'invariance', 'invariant', 'modular')):
            print(i, line[:1900])
(OUT / 'LOCAL_SOURCE_RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
