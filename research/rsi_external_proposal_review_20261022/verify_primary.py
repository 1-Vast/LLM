"""Acquire two exact primary documents for a bounded proposal citation check."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/rsi_external_proposal_review/primary'
TARGETS = [('aide2', 'https://arxiv.org/html/2609.26457v1'),
           ('failure_feedback', 'https://arxiv.org/html/2610.14662v1')]


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(' '.join(data.split()))


def acquire(target):
    name, url = target
    receipt = {'name': name, 'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
    try:
        req = Request(url, headers={'User-Agent': 'MAESTRO-public-research-citation-check/1.0'})
        with urlopen(req, timeout=40) as response:
            body = response.read()
            receipt.update(status=response.status, resolved_url=response.url)
    except HTTPError as error:
        body = error.read()
        receipt.update(status=error.code, error=str(error))
    except Exception as error:
        body = b''
        receipt.update(error=type(error).__name__ + ': ' + str(error))
    receipt.update(bytes=len(body), sha256=sha256(body).hexdigest())
    (OUT / (name + '.body')).write_bytes(body)
    if receipt.get('status') == 200:
        parser = Text()
        parser.feed(body.decode('utf-8', errors='replace'))
        lines = parser.parts
        (OUT / (name + '.txt')).write_text('\n'.join(lines), encoding='utf-8')
        hits = []
        terms = ('ignition', 'insufficient', 'not sufficient', 'self-improvement efficiency',
                 'targeted repair', 'held-out', 'held out', 'feedback shuffle')
        for i, line in enumerate(lines):
            if any(term in line.lower() for term in terms):
                hits.append({'line': i + 1, 'context': lines[max(0, i-2):i+4]})
        (OUT / (name + '_excerpts.json')).write_text(
            json.dumps(hits, ensure_ascii=False, indent=2), encoding='utf-8')
    return receipt


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / 'RECEIPTS.json').exists(), 'Do not repeat recorded requests'
    with ThreadPoolExecutor(max_workers=2) as executor:
        receipts = list(executor.map(acquire, TARGETS))
    (OUT / 'RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
    print(json.dumps(receipts))
