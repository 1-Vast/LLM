"""Fetch pinned method implementation and tutorial source, not outputs/data values."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/naiad_direct_baseline/root_sources'
tree = json.loads((OUT / 'tree.body').read_text())
paths = ['README.md', 'LICENSE', 'naiad/models.py', 'naiad/naiad.py', 'naiad/utils.py',
         'pyproject.toml', 'tutorials/naiad_tutorial.ipynb', 'tutorials/data_preparation_tutorial.ipynb']


def fetch(path):
    name = path.replace('/', '__')
    url = f'https://raw.githubusercontent.com/NeptuneBio/NAIAD/{tree["sha"]}/{path}'
    response = requests.get(url, timeout=60)
    data = response.content
    (OUT / (name + '.body')).write_bytes(data)
    record = {'url': url, 'status': response.status_code, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(), 'utc': datetime.now(timezone.utc).isoformat()}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(record, indent=2))
    if path.endswith('.ipynb') and response.status_code == 200:
        source = '\n\n'.join(''.join(c.get('source', [])) for c in response.json()['cells'])
        (OUT / (name + '.source.txt')).write_text(source, encoding='utf-8')
    return record


with ThreadPoolExecutor(max_workers=4) as pool:
    for record in pool.map(fetch, paths):
        print(json.dumps(record))
