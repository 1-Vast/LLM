"""Retain primary-index discovery, never fit outcome data."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/next_asset/sources'
QUERIES = {
    'dynamic_pharmacology': '("drug response" AND ("live-cell" OR "time-resolved") AND (phosphoproteomics OR "cell state")) AND OPEN_ACCESS:Y',
    'dream_primary': '("DREAM" AND "breast cancer" AND ("network" OR "signaling")) AND OPEN_ACCESS:Y',
    'drug_adaptation': '("drug" AND "adaptation" AND "single-cell" AND "dynamics") AND OPEN_ACCESS:Y',
}

def fetch(item):
    name, query = item
    response = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params={'query': query, 'format': 'json', 'pageSize': 20, 'resultType': 'core'}, timeout=90)
    path = OUT / (name + '.body')
    with path.open('xb') as f:
        f.write(response.content)
    receipt = {'url': response.url, 'status': response.status_code, 'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    data = response.json()
    rows = [{k: row.get(k) for k in ('id', 'pmcid', 'doi', 'title', 'firstPublicationDate', 'abstractText')} for row in data.get('resultList', {}).get('result', [])]
    (OUT / (name + '.summary.json')).write_text(json.dumps({'hitCount': data.get('hitCount'), 'rows': rows}, indent=2), encoding='utf-8')
    return {'name': name, **receipt, 'titles': [{'pmcid': row['pmcid'], 'doi': row['doi'], 'title': row['title']} for row in rows]}

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fetch, QUERIES.items()):
            print(json.dumps(result))
