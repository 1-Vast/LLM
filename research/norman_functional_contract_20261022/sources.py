"""Acquire exact author source and primary bibliography, without assay-value decoding."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_functional_contract/root_sources'
OUT.mkdir(parents=True, exist_ok=True)
tree = json.loads((ROOT / 'log/20261022/replogle_growth_acquisition/biology/norman_tree.body').read_text())
paths = [item['path'] for item in tree['tree']]
selected = [p for p in paths if 'README' in p.upper()]
selected += ['GI_dimensionality_reduction_and_statistics.ipynb']
urls = [(f'author_{i}', f'https://raw.githubusercontent.com/thomasmaxwellnorman/Perturbseq_GI/{tree["sha"]}/{p}') for i, p in enumerate(selected)]
urls.append(('primary_search', 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE:%22Exploring%20genetic%20interaction%20manifolds%22&format=json'))


def fetch(item):
    name, url = item
    response = requests.get(url, timeout=60)
    data = response.content
    (OUT / (name + '.body')).write_bytes(data)
    receipt = {'url': url, 'status': response.status_code, 'bytes': len(data),
               'sha256': hashlib.sha256(data).hexdigest(), 'utc': datetime.now(timezone.utc).isoformat()}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if response.status_code == 200 and url.endswith('.ipynb'):
        book = response.json()
        text = '\n\n'.join(''.join(c.get('source', [])) for c in book['cells'])
        (OUT / (name + '.source.txt')).write_text(text, encoding='utf-8')
    return receipt


with ThreadPoolExecutor(max_workers=3) as pool:
    for result in pool.map(fetch, urls):
        print(json.dumps(result))
