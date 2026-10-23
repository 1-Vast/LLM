"""Fetch closest baseline sources and official state accession metadata."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_functional_contract/root_sources'
revision = '3b25109aeb9c0c2026bd70abd50304a0ad4e5395'
urls = [(name, f'https://raw.githubusercontent.com/thomasmaxwellnorman/Perturbseq_GI/{revision}/{file}')
        for name, file in [('prediction', 'GI_prediction.ipynb'),
                           ('prediction_comparison', 'GI_prediction_performance_comparison.ipynb')]]
urls.append(('geo', 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE133344&targ=self&form=text&view=full'))


def fetch(item):
    name, url = item
    response = requests.get(url, timeout=60)
    data = response.content
    (OUT / (name + '.body')).write_bytes(data)
    receipt = {'url': url, 'status': response.status_code, 'bytes': len(data),
               'sha256': hashlib.sha256(data).hexdigest(), 'utc': datetime.now(timezone.utc).isoformat()}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if response.status_code == 200 and url.endswith('.ipynb'):
        text = '\n\n'.join(''.join(c.get('source', [])) for c in response.json()['cells'])
        (OUT / (name + '.source.txt')).write_text(text, encoding='utf-8')
    return receipt


with ThreadPoolExecutor(max_workers=3) as pool:
    for result in pool.map(fetch, urls):
        print(json.dumps(result))
