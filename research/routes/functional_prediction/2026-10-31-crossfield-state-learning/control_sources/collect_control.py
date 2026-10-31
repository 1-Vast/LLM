"""Bounded source acquisition and source reuse; no data/model execution."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import urllib.request
from bs4 import BeautifulSoup
import fitz

ROOT = Path(__file__).resolve().parent
LIB = Path('D:/MAESTRO/reference')
ids = ['1207.4167', '2106.03926', '2106.10316', '2505.14266']
manifest = []
for aid in ids:
    src = LIB / 'papers' / ('arxiv-' + aid) / ('paper.html' if aid == '2505.14266' else 'paper.pdf')
    raw = src.read_bytes()
    if src.suffix == '.pdf':
        with fitz.open(src) as doc:
            txt = '\n'.join(f'PAGE {i+1}\n' + p.get_text() for i, p in enumerate(doc))
    else:
        soup = BeautifulSoup(raw, 'html.parser')
        for tag in soup(['script', 'style']):
            tag.decompose()
        # Separate blocks to retain section IDs and equations for locators.
        txt = '\n'.join(f'SECTION {sec.get("id", "")}\n' + sec.get_text(' ', strip=True)
                        for sec in soup.find_all('section', recursive=True))
    out = ROOT / ('arxiv-' + aid + '.txt')
    out.write_text(txt, encoding='utf-8')
    manifest.append(dict(arxiv_id=aid, source_path=str(src), bytes=len(raw),
                         sha256=hashlib.sha256(raw).hexdigest(),
                         extracted_path=str(out), source_url='https://arxiv.org/' + ('html/' if src.suffix == '.html' else 'pdf/') + aid + ('v1' if aid != '2106.10316' else 'v2')))

receipts = []
# One live official refresh; a failed refresh is retained and does not invalidate the saved original.
url = 'https://arxiv.org/abs/2505.14266'
rec = dict(url=url, requested_at=datetime.now(timezone.utc).isoformat(), purpose='Refresh official identity/version for the selected real 2025 method update', redirects_count_as_requests=True)
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-source-audit/1.0'})
    with urllib.request.urlopen(req, timeout=35) as response:
        body = response.read(2 * 1024 * 1024 + 1)
        if len(body) > 2 * 1024 * 1024:
            raise RuntimeError('Response exceeds 2 MiB per-request cap')
        rec.update(status=response.status, final_url=response.url, content_type=response.headers.get('Content-Type'), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        (ROOT / 'live_2505.14266_abs.html').write_bytes(body)
except Exception as exc:
    rec.update(error=f'{type(exc).__name__}: {exc}')
receipts.append(rec)
(ROOT / 'reuse_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
(ROOT / 'http_receipts.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
print(json.dumps(receipts, indent=2))
print('Reused original works:', len(manifest))
