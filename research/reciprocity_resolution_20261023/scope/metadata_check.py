"""Independent metadata audit; never decode RNA response or assay numbers."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'log/20261022/norman_functional_contract/data'
SOURCE = ROOT / 'log/20261022/norman_numeric_qualification/SINGLE_RNA_FEATURES.npz'
OUT = ROOT / 'log/20261023/reciprocity_resolution/scope'
RENAMES = {'C3orf72': 'FOXL2NB', 'C19orf26': 'CBARP',
           'KIAA1804': 'RP5-862P8.2', 'RHOXF2': 'RHOXF2B'}

with np.load(SOURCE) as stored:
    genes = stored['genes'].tolist()
with gzip.open(BASE / 'GSE133344_raw_genes.tsv.gz', 'rt') as stream:
    features = [line.rstrip('\n').split('\t') for line in stream]
with gzip.open(BASE / 'GSE133344_raw_cell_identities.csv.gz', 'rt') as stream:
    target_strings = {row['guide_identity'].split('__')[0] for row in csv.DictReader(stream)}
rows = []
for canonical in genes:
    raw = next((key for key, value in RENAMES.items() if value == canonical), canonical)
    orientation = raw + '_NegCtrl0'
    if orientation not in target_strings:
        orientation = 'NegCtrl0_' + raw
    matched = [{'index': i, 'ensembl': row[0], 'symbol': row[1]}
               for i, row in enumerate(features) if row[1] == raw]
    resolved = matched if matched else [
        {'index': i, 'ensembl': row[0], 'symbol': row[1]}
        for i, row in enumerate(features) if row[1] == canonical]
    canonical_matches = [{'index': i, 'ensembl': row[0], 'symbol': row[1]}
                         for i, row in enumerate(features) if row[1] == canonical]
    rows.append({'canonical_target': canonical, 'source_raw_target': raw,
                 'selected_orientation_exists': orientation in target_strings,
                 'feature_matches': matched, 'exact_first_alias_fallback_matches': resolved,
                 'exact_first_alias_fallback_reason': 'raw_exact' if matched else 'frozen_alias_fallback',
                 'canonical_target_exact_raw_feature_matches': canonical_matches})
report = {'targets': len(genes), 'all_exact_raw_symbol_unique': all(len(row['feature_matches']) == 1 for row in rows),
          'all_canonical_target_exact_raw_feature_unique': all(len(row['canonical_target_exact_raw_feature_matches']) == 1 for row in rows),
          'distinct_canonical_target_exact_raw_features': len({match['index'] for row in rows for match in row['canonical_target_exact_raw_feature_matches']}),
          'all_exact_first_alias_fallback_unique': all(len(row['exact_first_alias_fallback_matches']) == 1 for row in rows),
          'distinct_exact_first_alias_fallback_features': len({match['index'] for row in rows for match in row['exact_first_alias_fallback_matches']}),
          'all_selected_orientation_exists': all(row['selected_orientation_exists'] for row in rows),
          'rows': rows, 'RNA_response_values_loaded': 0, 'numeric_assay_fields_decoded': 0,
          'scope': 'Exact historical strings, not molecular targeting or force equivalence',
          'inputs': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in [SOURCE, BASE / 'GSE133344_raw_genes.tsv.gz',
                                  BASE / 'GSE133344_raw_cell_identities.csv.gz']}}
(OUT / 'METADATA_CHECK.json').write_text(json.dumps(report, indent=2))
print(json.dumps({key: value for key, value in report.items() if key not in ['rows', 'inputs']}))
