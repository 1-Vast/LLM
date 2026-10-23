"""Check unchanged readout identities and exact/tolerance distinctions, no RNA values."""
import json
from pathlib import Path
import numpy as np
from run import diagnostic, OUT

record = json.loads((OUT / 'IDENTITY.json').read_text())
assert record['response_values_loaded'] == 0 and len(record['targets']) == 103
assert len(set(record['indices'].values())) == 103
assert record['indices']['RHOXF2B'] == 14109
assert record['ensembl_ids']['RHOXF2B'] == 'ENSG00000203989'
assert 14112 not in record['indices'].values()
matrix = np.array([[2., .1], [.1, 1.]]) @ np.diag([1e-13, 1.])
result, _ = diagnostic.examine(matrix)
assert result['exact_nonpositive_diagonal'] == result['exact_opposite_sign_pairs'] == result['exact_one_sided_zero_pairs'] == 0
assert result['one_sided_numerical_zero_pairs'] == 1
(OUT / 'ADAPTER_TEST.json').write_text(json.dumps({'status': 'PASS', 'RNA_response_values_loaded': 0,
    'checks': ['unchanged_exact_symbol_join', 'all_targets_unique', 'separate_RHOXF2_features', 'exact_vs_numerical_zero']}, indent=2))
print('PASS metadata join and numerical classification')
