"""Bounded new primary-index search; retain receipts and no biological outcomes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/post_anchor_mechanism/root_sources'
QUERIES = [
    ('adaptive_cell', '("perturbation" OR "drug response") AND ("active learning" OR "adaptive experimental design" OR "meta-learning") AND ("single-cell" OR "cell state") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
    ('state_function', '("drug" OR "perturbation") AND ("transcriptomic" OR "cell state") AND ("functional response" OR "viability prediction" OR "phenotypic response") AND FIRST_PDATE:[2026-01-01 TO 2026-10-23]'),
    ('improver', '("recursive self-improvement" OR "learning update rules" OR "self-improving world model" OR "learned optimizers") AND FIRST_PDATE:[2025-01-01 TO 2026-10-23]'),
]

def fetch(item):
    name, query = item
    receipt = dict(name=name, query=query, start=datetime.now(timezone.utc).isoformat())
    try:
        response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',
            params=dict(query=query, format='json', pageSize=18, resultType='core', sort='FIRST_PDATE_D'), timeout=40)
        body = response.content
        (OUT / (name+'.body')).write_bytes(body)
        receipt.update(status=response.status_code, url=response.url, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        if response.ok:
            payload = response.json()
            receipt.update(hit_count=payload.get('hitCount'), results=[{k: row.get(k) for k in
                ['title','doi','pmcid','firstPublicationDate','abstractText']} for row in payload.get('resultList',{}).get('result',[])])
    except Exception as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    (OUT / (name+'.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(fetch, QUERIES))
    (OUT.parent / 'ROOT_SEARCH.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps([{k: v for k,v in r.items() if k!='results'} | dict(results=[
        {k:v for k,v in p.items() if k!='abstractText'} for p in r.get('results',[])]) for r in results], indent=2))
