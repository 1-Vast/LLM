"""Acquire exact original source objects and inspect only their string schemas."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_matched_guide/root_sources'
OUT.mkdir(parents=True, exist_ok=True)
REVISION = '3b25109aeb9c0c2026bd70abd50304a0ad4e5395'
PATHS = [('chosen_final', 'final_emaps/20180821_guides_chosen_for_perturbseq.csv'),
         ('chosen_sharing', 'data_sharing/20180821_guides_chosen_for_perturbseq.csv'),
         ('unfiltered_pairs', 'final_emaps/filter0/CRISPRa_K562_replicateAverage_phenotypeMatrix_abbaAveraged.txt'),
         ('unfiltered_singles', 'final_emaps/filter0/CRISPRa_K562_replicateAverage_singlePhenotypes_abbaAveraged.txt')]


def fetch(item):
    name, path = item
    url = f'https://raw.githubusercontent.com/thomasmaxwellnorman/Perturbseq_GI/{REVISION}/{path}'
    response = requests.get(url, timeout=60)
    data = response.content
    (OUT / (name + '.body')).write_bytes(data)
    receipt = {'url': url, 'status': response.status_code, 'bytes': len(data),
               'sha256': hashlib.sha256(data).hexdigest(), 'utc': datetime.now(timezone.utc).isoformat()}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2))
    if response.status_code == 200:
        delimiter = ',' if path.endswith('.csv') else '\t'
        reader = csv.reader(io.StringIO(data.decode()), delimiter=delimiter)
        header = next(reader)
        rows = list(reader)
        record = {'header': header, 'row_ids': [r[0] for r in rows], 'row_count': len(rows),
                  'numeric_assay_values_decoded': False}
        if name.startswith('chosen'):
            record['gene_to_guide_id'] = {r[0]: r[header.index('guide_id')] for r in rows}
        (OUT / (name + '.schema.json')).write_text(json.dumps(record, indent=2))
    return receipt


with ThreadPoolExecutor(max_workers=4) as pool:
    for record in pool.map(fetch, PATHS):
        print(json.dumps(record))
