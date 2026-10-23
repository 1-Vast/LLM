"""Record official raw-state object headers before a potentially large download."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_functional_contract/root_sources'
base = 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE133nnn/GSE133344/suppl/'
names = ['GSE133344_raw_matrix.mtx.gz', 'GSE133344_raw_cell_identities.csv.gz', 'GSE133344_raw_genes.tsv.gz']


def head(name):
    response = requests.head(base + name, timeout=60)
    body = response.content
    (OUT / (name + '.head.body')).write_bytes(body)
    record = {'url': base + name, 'method': 'HEAD', 'status': response.status_code,
              'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
              'headers': dict(response.headers), 'utc': datetime.now(timezone.utc).isoformat()}
    (OUT / (name + '.head.receipt.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    return {k: record[k] for k in ('url', 'status', 'headers')}


with ThreadPoolExecutor(max_workers=3) as pool:
    for result in pool.map(head, names):
        print(json.dumps(result))
