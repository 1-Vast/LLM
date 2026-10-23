"""Validate raw matrix dimensions and identity alignment without expression values."""
import csv
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_functional_contract'
DATA = OUT / 'data'
with gzip.open(DATA / 'GSE133344_raw_matrix.mtx.gz', 'rt') as stream:
    signature = next(stream).strip()
    line = next(stream)
    while line.startswith('%'):
        line = next(stream)
    genes, cells, entries = map(int, line.split())
with gzip.open(DATA / 'GSE133344_raw_genes.tsv.gz', 'rt') as stream:
    gene_rows = sum(1 for _ in stream)
identities = set()
targets = set()
duplicate_identity_rows = 0
with gzip.open(DATA / 'GSE133344_raw_cell_identities.csv.gz', 'rt') as stream:
    rows = csv.DictReader(stream)
    header = rows.fieldnames
    for row in rows:
        barcode = row['cell_barcode']
        duplicate_identity_rows += barcode in identities
        identities.add(barcode)
        targets.add(row['guide_identity'].split('__')[0])
found = set()
with gzip.open(DATA / 'GSE133344_raw_barcodes.tsv.gz', 'rt') as stream:
    barcode_rows = 0
    for barcode_rows, line in enumerate(stream, 1):
        barcode = line.strip()
        if barcode in identities:
            found.add(barcode)
assert genes == gene_rows and cells == barcode_rows
result = {'matrix_signature': signature, 'matrix_shape': [genes, cells],
          'matrix_declared_entries': entries, 'gene_rows': gene_rows,
          'barcode_rows': barcode_rows, 'identity_rows_unique': len(identities),
          'identity_duplicate_rows': duplicate_identity_rows,
          'identity_barcodes_in_matrix': len(found),
          'identity_barcodes_missing_from_matrix': len(identities - found),
          'unique_raw_target_strings': len(targets), 'identity_header': header,
          'expression_entries_decoded': False, 'numeric_cell_fields_decoded': False,
          'qc_source_definition': '(number_of_cells == 1) & good_coverage & (guide_identity != "*")',
          'raw_umi_threshold_source': 2000, 'qc_applied': False}
(OUT / 'RAW_SCHEMA.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
