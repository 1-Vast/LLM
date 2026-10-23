"""Stream exact GEO objects with byte receipts; no expression-value decoding."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_functional_contract/data'
base = 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE133nnn/GSE133344/suppl/'
names = ['GSE133344_raw_matrix.mtx.gz', 'GSE133344_raw_cell_identities.csv.gz',
         'GSE133344_raw_genes.tsv.gz', 'GSE133344_raw_barcodes.tsv.gz']
assert shutil.disk_usage(OUT).free > 4_000_000_000


def fetch(name):
    target = OUT / name
    assert not target.exists(), 'Do not silently overwrite/restart existing acquisition'
    record = {'url': base + name, 'method': 'GET', 'utc_start': datetime.now(timezone.utc).isoformat(), 'body': name}
    (OUT / (name + '.started.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    response = requests.get(base + name, stream=True, timeout=(30, 60))
    record.update(status=response.status_code, content_length=response.headers.get('Content-Length'))
    value = hashlib.sha256()
    size = 0
    with target.open('wb') as stream:
        for chunk in response.iter_content(1024 * 1024):
            stream.write(chunk)
            value.update(chunk)
            size += len(chunk)
    record.update(bytes=size, sha256=value.hexdigest(), utc_end=datetime.now(timezone.utc).isoformat())
    (OUT / (name + '.receipt.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record), flush=True)
    assert response.status_code == 200
    if record['content_length'] is not None:
        assert size == int(record['content_length'])
    return name


with ThreadPoolExecutor(max_workers=3) as pool:
    list(pool.map(fetch, names))
