"""Bounded primary-paper retrieval; never reads biological response data."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET
import requests

OUT = Path('log/20261022/post_almanac_mechanism/frontier')
SOURCES = OUT / 'sources'
QUERIES = {
    'learned_update': '(all:"learned optimizer" OR all:"test-time memorization") AND submittedDate:[202501010000 TO 202610222359]',
    'experiment_design': '(all:"experimental design" AND (all:"regret" OR all:"amortized")) AND submittedDate:[202501010000 TO 202610222359]',
    'model_revision': '(all:"world model" AND (all:"falsification" OR all:"epistemic")) AND submittedDate:[202501010000 TO 202610222359]',
}

def get(name, url, params=None):
    start = time.time()
    record = {'name': name, 'url': url, 'params': params, 'started_unix': start}
    try:
        response = requests.get(url, params=params, timeout=55)
        path = SOURCES / (name + '.txt')
        path.write_bytes(response.content)
        record.update(status=response.status_code, final_url=response.url, bytes=len(response.content), sha256=hashlib.sha256(response.content).hexdigest(), path=str(path), elapsed=time.time()-start)
    except Exception as exc:
        record.update(error=repr(exc), elapsed=time.time()-start)
    (OUT / (name + '_receipt.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record

if __name__ == '__main__':
    jobs = [(name, 'https://export.arxiv.org/api/query', {'search_query': query, 'start': 0, 'max_results': 12, 'sortBy': 'submittedDate', 'sortOrder': 'descending'}) for name, query in QUERIES.items()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(lambda args: get(*args), jobs))
    print(json.dumps(records, indent=2))
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    for record in records:
        if record.get('status') != 200:
            continue
        root = ET.parse(record['path']).getroot()
        for entry in root.findall('a:entry', ns):
            print(entry.findtext('a:id', namespaces=ns), entry.findtext('a:title', namespaces=ns), entry.findtext('a:summary', namespaces=ns))
