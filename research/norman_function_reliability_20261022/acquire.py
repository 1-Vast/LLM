"""Acquire pinned exact replicate objects; inspect string axes only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_function_reliability/root_sources'
OUT.mkdir(parents=True, exist_ok=True)
REVISION = '3b25109aeb9c0c2026bd70abd50304a0ad4e5395'


def fetch(rep):
    name = f'CRISPRa_K562_replicate{rep}_phenotypeMatrix_abbaAveraged.txt'
    url = f'https://raw.githubusercontent.com/thomasmaxwellnorman/Perturbseq_GI/{REVISION}/final_emaps/filter15/{name}'
    response = requests.get(url, timeout=60)
    data = response.content
    (OUT / (str(rep) + '.body')).write_bytes(data)
    receipt = {'url': url, 'status': response.status_code, 'bytes': len(data),
               'sha256': hashlib.sha256(data).hexdigest(), 'utc': datetime.now(timezone.utc).isoformat()}
    (OUT / (str(rep) + '.receipt.json')).write_text(json.dumps(receipt, indent=2))
    if response.status_code == 200:
        rows = csv.reader(io.StringIO(data.decode()), delimiter='\t')
        header = next(rows)
        ids = [row[0] for row in rows]
        schema = {'header': header, 'row_ids': ids, 'row_count': len(ids), 'column_count': len(header) - 1,
                  'numeric_assay_values_decoded': False}
        (OUT / (str(rep) + '.schema.json')).write_text(json.dumps(schema, indent=2))
    return receipt


with ThreadPoolExecutor(max_workers=3) as pool:
    for result in pool.map(fetch, ['1', '2', 'Average']):
        print(json.dumps(result))
