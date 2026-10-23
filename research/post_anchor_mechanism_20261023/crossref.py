"""Bounded alternative primary-index requests after retained EPMC 503s."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261023/post_anchor_mechanism/root_sources'
QUERIES = [('crossref_cell', 'single cell perturbation functional response active learning'),
           ('crossref_world', 'world model self improvement learned optimizer')]
def fetch(item):
    name, query = item
    receipt = dict(query=query, utc=datetime.now(timezone.utc).isoformat())
    try:
        r = requests.get('https://api.crossref.org/works', params={
            'query':query, 'filter':'from-pub-date:2025-01-01,until-pub-date:2026-10-23',
            'rows':12, 'select':'DOI,title,published,URL,abstract'}, timeout=40)
        (OUT/(name+'.body')).write_bytes(r.content)
        receipt.update(status=r.status_code, url=r.url, sha256=hashlib.sha256(r.content).hexdigest())
        if r.ok:
            receipt['results']=r.json()['message']['items']
    except Exception as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    (OUT/(name+'.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:
        result=list(pool.map(fetch,QUERIES))
    print(json.dumps(result,indent=2))
