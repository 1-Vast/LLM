"""Bounded primary-source metadata/fulltext acquisition; never assay data."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import requests

OUT = Path('D:/MAESTRO/log/20261022/native_operation/proposer/sources')
OUT.mkdir(parents=True, exist_ok=True)
URLS = {
    'dgm_abs': 'https://arxiv.org/abs/2505.22954',
    'dgm_html': 'https://arxiv.org/html/2505.22954v1',
    'sequential_cell_search': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE:%22Sequential%20application%20of%20anticancer%20drugs%22&format=json',
    'lie_2025_search': 'https://api.crossref.org/works?query.title=learning%20Lie%20brackets%20dynamics&filter=from-pub-date:2025-01-01,until-pub-date:2026-10-22&rows=5',
}
receipts = []
for name, url in URLS.items():
    p = OUT / (name + '.body')
    if p.exists():
        raise RuntimeError('Refusing overwrite: ' + str(p))
    row = {'name': name, 'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
    try:
        response = requests.get(url, timeout=35)
        payload = response.content
        p.write_bytes(payload)
        row.update(status=response.status_code, final_url=response.url,
                   content_type=response.headers.get('Content-Type'), bytes=len(payload),
                   sha256=hashlib.sha256(payload).hexdigest())
    except Exception as exc:
        row.update(error=repr(exc))
    receipts.append(row)
    print(json.dumps(row))
(OUT / 'RECEIPTS.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
