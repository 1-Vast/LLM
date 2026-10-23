"""Resolve the original publisher resource through the exact article DOI."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/replogle_growth_acquisition/root_sources'
OUT.mkdir(parents=True, exist_ok=True)


def fetch(name, url):
    assert not (OUT / (name + '.body')).exists()
    response = requests.get(url, timeout=45)
    (OUT / (name + '.body')).write_bytes(response.content)
    (OUT / (name + '.receipt.json')).write_text(json.dumps({
        'url': url, 'final_url': response.url, 'status': response.status_code,
        'utc': datetime.now(timezone.utc).isoformat(), 'bytes': len(response.content),
        'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
    print(name, response.status_code, len(response.content), response.url)
    return response


with ThreadPoolExecutor(max_workers=2) as pool:
    crossref = pool.submit(fetch, 'crossref', 'https://api.crossref.org/works/10.1016/j.cell.2022.05.013')
    doi = pool.submit(fetch, 'publisher', 'https://doi.org/10.1016/j.cell.2022.05.013')
    result = crossref.result()
    result.raise_for_status()
    body = result.json()['message']
    print(json.dumps({key: body.get(key) for key in ('title', 'link', 'resource', 'relation', 'alternative-id')}, indent=2))
    doi.result()
