"""Acquire a pinned public table, project only identity columns, retain receipts."""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pyarrow.parquet as pq
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/dose_update_qualification'
REV = 'f2a0be6b02f731553657f0115c345b20bb020ede'

if __name__ == '__main__':
    result_path = OUT / 'IDENTITY_RESULT.json'
    receipt_path = OUT / 'IDENTITY_RECEIPT.json'
    assert not result_path.exists() and not receipt_path.exists()
    url = f'https://huggingface.co/datasets/tahoebio/EmeraldBay/resolve/{REV}/metadata/summary_statistics.parquet'
    receipt = dict(requested_url=url, start=datetime.now(timezone.utc).isoformat(),
        allowed_projection=['cell_line', 'condition'], response_values_decoded=False)
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    response = requests.get(url, timeout=60)
    payload = response.content
    source = OUT / 'summary_statistics.parquet'
    source.write_bytes(payload)
    receipt.update(status=response.status_code, bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(), end=datetime.now(timezone.utc).isoformat())
    # Signed CDN URLs are unnecessary for reproduction; retain requested pinned URL.
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    response.raise_for_status()
    parquet = pq.ParquetFile(source)
    schema = [(field.name, str(field.type)) for field in parquet.schema_arrow]
    identities = pq.read_table(source, columns=['cell_line', 'condition']).to_pylist()
    pairs = Counter((row['cell_line'], row['condition']) for row in identities)
    cells = sorted({row['cell_line'] for row in identities})
    conditions = sorted({row['condition'] for row in identities})
    menu = []
    for condition in conditions:
        parsed = ast.literal_eval(condition)
        assert isinstance(parsed, list) and all(len(item) == 3 for item in parsed)
        menu.append(dict(condition=condition, compounds=parsed,
            control=all(str(item[0]).startswith('DMSO') for item in parsed)))
    single = [row for row in menu if len(row['compounds']) == 1 and not row['control']]
    result = dict(scope='identity projection only; public response values not decoded',
        revision=REV, schema=schema, raw_rows=parquet.metadata.num_rows,
        projected_rows=len(identities), distinct_cells=len(cells), distinct_conditions=len(menu),
        unique_cell_condition_pairs=len(pairs), duplicated_pairs=sum(n > 1 for n in pairs.values()),
        excess_duplicate_rows=sum(n-1 for n in pairs.values()),
        pair_multiplicity_histogram=dict(sorted(Counter(pairs.values()).items())),
        single_drug_noncontrol_conditions=len(single),
        distinct_single_drugs=len({row['compounds'][0][0] for row in single}),
        units=sorted({str(item[2]) for row in menu for item in row['compounds']}),
        identity_sample_or_run_column_present=any(name in ['sample', 'run', 'plate'] for name, _ in schema),
        cell_ids=cells, menu=menu)
    result_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ['menu', 'cell_ids']}, indent=2))
