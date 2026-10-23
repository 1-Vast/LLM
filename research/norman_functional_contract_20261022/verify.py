"""Verify local source acquisition and frozen identity splits; no performance claim."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_functional_contract'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


previous = json.loads((ROOT / 'log/20261022/replogle_growth_acquisition/VERIFICATION.json').read_text())
drift = [name for name, expected in previous['files'].items()
         if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
statuses = Counter()
for receipt_file in sorted(OUT.rglob('*.receipt.json')):
    receipt = json.loads(receipt_file.read_text())
    body = receipt_file.with_name(receipt.get('body', receipt_file.name.removesuffix('.receipt.json') + '.body'))
    assert body.stat().st_size == receipt['bytes'], body
    assert digest(body) == receipt['sha256'], body
    if receipt.get('content_length') is not None:
        assert body.stat().st_size == int(receipt['content_length'])
    statuses[receipt['status']] += 1
assert dict(statuses) == {200: 21}, statuses
schema = json.loads((OUT / 'RAW_SCHEMA.json').read_text())
assert schema['matrix_shape'] == [schema['gene_rows'], schema['barcode_rows']]
assert schema['identity_rows_unique'] == schema['identity_barcodes_in_matrix'] == 114870
assert schema['identity_barcodes_missing_from_matrix'] == schema['identity_duplicate_rows'] == 0
assert not schema['expression_entries_decoded'] and not schema['numeric_cell_fields_decoded']
with (OUT / 'PAIR_SPLITS.csv').open(newline='', encoding='utf-8') as stream:
    rows = list(csv.DictReader(stream))
assert len(rows) == len({r['pair'] for r in rows}) == 5460
for row in rows:
    assert row['gene_a'] < row['gene_b'] and row['pair'] == row['gene_a'] + '|' + row['gene_b']
    bucket = int.from_bytes(hashlib.sha256(('MAESTRO_NORMAN_FUNCTION_V1|' + row['pair']).encode()).digest()[:8], 'big') % 100
    assert int(row['bucket']) == bucket
    assert row['split'] == ('source' if bucket < 60 else 'development' if bucket < 80 else 'protected')
pair_counts = dict(Counter(row['split'] for row in rows))
assert pair_counts == {'source': 3286, 'development': 1091, 'protected': 1083}
pair_seal = json.loads((OUT / 'PAIR_SPLITS.seal.json').read_text())
assert digest(OUT / 'PAIR_SPLITS.csv') == pair_seal['sha256']
files = {}
for folder in (OUT, Path(__file__).resolve().parent):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'VERIFICATION.json':
            files[path.relative_to(ROOT).as_posix()] = digest(path)
result = {'status': 'FAIL' if drift else 'PASS_LOCAL', 'http_status_counts': dict(statuses),
          'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
          'potential_pairs_by_split': pair_counts,
          'scope': 'Local receipts and recorded schema plus actual identity-only split; no function completeness/performance/global provenance repair',
          'files': files}
(OUT / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))
print('Current files sealed:', len(files))
assert not drift
