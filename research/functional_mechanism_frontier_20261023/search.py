"""Two bounded author-abstract index searches for functional model revision."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/functional_mechanism_frontier/root_sources'
QUERIES = [('revision', '(TITLE_ABS:"decision focused" OR TITLE_ABS:"model revision") AND (TITLE_ABS:drug OR TITLE_ABS:cell) AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
           ('feedback', '(TITLE_ABS:"closed loop" OR TITLE_ABS:"active learning") AND (TITLE_ABS:"drug response" OR TITLE_ABS:"cell state") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]')]


def get(item):
    name, query = item
    record = dict(utc=datetime.now(timezone.utc).isoformat(), query=query)
    try:
        response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                                params=dict(query=query, format='json', resultType='core', pageSize=12, sort='FIRST_PDATE_D desc'), timeout=40)
        (OUT / (name + '.body')).write_bytes(response.content)
        record.update(url=response.url, status=response.status_code, bytes=len(response.content),
                      sha256=hashlib.sha256(response.content).hexdigest())
        if response.status_code == 200:
            body = response.json()
            rows = [{k: row.get(k) for k in ['title', 'doi', 'pmcid', 'firstPublicationDate', 'abstractText']}
                    for row in body.get('resultList', {}).get('result', [])]
            record['hitCount'] = body.get('hitCount')
            (OUT / (name + '.entries.json')).write_text(json.dumps(rows, indent=2), encoding='utf-8')
            record['titles'] = [{k: row.get(k) for k in ['title', 'doi', 'pmcid', 'firstPublicationDate']} for row in rows]
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
    (OUT / (name + '.receipt.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    assert not list(OUT.glob('*.receipt.json')), 'Do not duplicate a completed search'
    with ThreadPoolExecutor(max_workers=2) as pool:
        print(json.dumps(list(pool.map(get, QUERIES)), indent=2))
