"""Acquire small concrete payloads and inspect identifiers only, never numeric assays."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_functional_contract/data'
OUT.mkdir(parents=True, exist_ok=True)
revision = '3b25109aeb9c0c2026bd70abd50304a0ad4e5395'
files = ['processed_fitnesses.csv', 'processed_perturbseq_fitnesses.csv',
         'single_fitnesses.csv', 'processed_emap.csv']
urls = [(file, f'https://raw.githubusercontent.com/thomasmaxwellnorman/Perturbseq_GI/{revision}/final_emaps/{file}') for file in files]
urls.append(('GSE133344_filtered_cell_identities.csv.gz', 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE133nnn/GSE133344/suppl/GSE133344_filtered_cell_identities.csv.gz'))


def fetch(item):
    name, url = item
    response = requests.get(url, timeout=60)
    data = response.content
    (OUT / name).write_bytes(data)
    receipt = {'url': url, 'status': response.status_code, 'bytes': len(data),
               'sha256': hashlib.sha256(data).hexdigest(), 'utc': datetime.now(timezone.utc).isoformat(),
               'body': name}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if response.status_code != 200:
        return receipt
    decoded = gzip.decompress(data).decode() if name.endswith('.gz') else data.decode()
    rows = csv.reader(io.StringIO(decoded))
    header = next(rows)
    if name.endswith('.gz'):
        schema = {'header': header, 'numeric_fields_decoded': False}
    else:
        identities = [row[0] for row in rows]
        schema = {'header': header, 'row_ids': identities, 'row_count': len(identities),
                  'numeric_assays_decoded': False}
    (OUT / (name + '.schema.json')).write_text(json.dumps(schema, indent=2), encoding='utf-8')
    return receipt


with ThreadPoolExecutor(max_workers=3) as pool:
    for result in pool.map(fetch, urls):
        print(json.dumps(result))
