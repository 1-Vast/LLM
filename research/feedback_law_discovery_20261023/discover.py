"""Purposeful primary-index discovery; retain responses and explicit status."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/feedback_law_discovery/root_sources'
QUERIES = [
    ('update', '(TITLE_ABS:"meta learning" OR TITLE_ABS:"test time" OR TITLE_ABS:"adaptation") AND (TITLE_ABS:"perturbation prediction" OR TITLE_ABS:"drug response") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
    ('law', '(TITLE_ABS:"drug response" OR TITLE_ABS:"perturbation") AND (TITLE_ABS:"measurement error" OR TITLE_ABS:"observation model" OR TITLE_ABS:"feedback learning") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]')]


def fetch(item):
    name, query = item
    record = dict(utc=datetime.now(timezone.utc).isoformat(), query=query)
    try:
        response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                                params=dict(query=query, format='json', resultType='core', pageSize=15), timeout=45)
        (OUT/(name+'.body')).write_bytes(response.content)
        record.update(url=response.url, status=response.status_code, bytes=len(response.content),
                      sha256=hashlib.sha256(response.content).hexdigest())
        if response.status_code == 200:
            body = response.json()
            rows = [{k: row.get(k) for k in ['title', 'doi', 'pmcid', 'firstPublicationDate', 'abstractText']}
                    for row in body.get('resultList', {}).get('result', [])]
            (OUT/(name+'.entries.json')).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
            record.update(hitCount=body.get('hitCount'), titles=[{k:v for k,v in r.items() if k!='abstractText'} for r in rows])
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
    (OUT/(name+'.receipt.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    assert not list(OUT.glob('*.receipt.json')), 'Do not repeat initiated requests'
    with ThreadPoolExecutor(max_workers=2) as pool:
        print(json.dumps(list(pool.map(fetch, QUERIES)), indent=2))
