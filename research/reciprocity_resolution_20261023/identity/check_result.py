"""Independent source/direction/count review of the completed saved result."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/reciprocity_resolution'
result = json.loads((OUT / 'RESULT.json').read_text())
identity = json.loads((OUT / 'IDENTITY.json').read_text())
prior = json.loads((OUT / 'identity/METADATA_AUDIT.json').read_text())
with np.load(ROOT / 'log/20261022/norman_numeric_qualification/SINGLE_RNA_FEATURES.npz') as stored:
    genes, features = stored['genes'].tolist(), stored['features']
with np.load(OUT / 'RESPONSE_MATRIX.npz') as stored:
    matrix = stored['response']
    assert genes == stored['genes'].tolist() == identity['targets']
with gzip.open(ROOT / 'log/20261022/norman_functional_contract/data/GSE133344_raw_genes.tsv.gz', 'rt') as stream:
    rows = [line.strip().split('\t') for line in stream]
indices = [identity['indices'][g] for g in genes]
assert len(genes) == len(set(indices)) == 103
assert all(rows[i][1] == g for i, g in zip(indices, genes))
assert np.array_equal(matrix, features[:, indices].T)
assert matrix.shape == (103, 103)
for rel, expected in identity['input_hashes'].items():
    assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected
assert prior['source_sha256']['rna'] == identity['input_hashes']['log\\20261022\\norman_numeric_qualification\\SINGLE_RNA_FEATURES.npz']
i, j = np.triu_indices(103, 1)
a, b = matrix[i, j], matrix[j, i]
counts = {'exact_nonpositive_diagonal': int(np.sum(np.diag(matrix) <= 0)),
          'exact_opposite_sign_pairs': int(np.sum((a != 0) & (b != 0) & (np.sign(a) != np.sign(b)))),
          'exact_one_sided_zero_pairs': int(np.sum((a == 0) != (b == 0)))}
assert all(result[k] == v for k, v in counts.items())
pairs = json.loads((OUT / 'PAIRS.json').read_text())
assert len(pairs) == len(a) == 5253
for p, x, y in zip(pairs, i, j):
    assert p['gene_i'] == genes[x] and p['gene_j'] == genes[y]
    assert p['R_ij'] == matrix[x, y] and p['R_ji'] == matrix[y, x]
report = {'status': 'PASS_SOURCE_DIRECTION_EXACT_COUNTS', 'counts': counts,
          'nonpositive_diagonals': [{'target': genes[k], 'reference_index': indices[k],
                                    'ensembl_id': rows[indices[k]][0], 'value': float(matrix[k, k])}
                                   for k in range(103) if matrix[k, k] <= 0],
          'source_unchanged_since_metadata_audit': True, 'all_103_exact_symbols_and_unique': True,
          'matrix_exactly_original_features_transpose': True,
          'note': 'Reads already-exposed single-RNA only; no functional, development or protected source opened.'}
(OUT / 'identity/RESULT_CHECK.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
