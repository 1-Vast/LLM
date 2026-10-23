"""Cross-check new saved singles/counts with old extraction; no raw matrix scan."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/mixed_feedback_estimator'
data = np.load(OUT / 'STATE_BY_GEM.npz')
old = np.load(ROOT / 'log/20261022/norman_numeric_qualification/SINGLE_RNA_FEATURES.npz')
old_counts = pd.read_csv(ROOT / 'log/20261022/norman_numeric_qualification/RNA_QC_COUNTS.csv')
names, gems = data['group_names'].tolist(), data['gems'].tolist()
lookup = {(name, int(gem)): i for i, (name, gem) in enumerate(zip(names, gems))}
for row in old_counts.itertuples():
    assert data['counts'][lookup[(row.target, row.gemgroup)]] == row.retained_cells
old_map = {name: i for i, name in enumerate(old['genes'].tolist())}
errors = []
for gene in data['genes'].tolist():
    weighted = np.zeros(103)
    count = 0
    for gem in range(1, 9):
        i, control = lookup[(gene, gem)], lookup[('CONTROL', gem)]
        weighted += data['counts'][i] * (data['mean_log1pCP10K'][i] - data['mean_log1pCP10K'][control])
        count += data['counts'][i]
    reference = old['features'][old_map[gene], data['raw_feature_indices']]
    errors.append(float(np.max(np.abs(weighted / count - reference))))
assert max(errors) < 1e-13
metadata = pd.read_csv(OUT / 'support/SOURCE_PAIR_METADATA.csv')
supported = metadata[metadata.identity_qc_cells > 0]
for row in supported.itertuples():
    retained = sum(data['counts'][lookup[(row.pair, gem)]] for gem in range(1, 9))
    assert retained == row.identity_qc_cells
report = {'status': 'PASS_LOCAL_SAVED_EXTRACTION_COMPARISON', 'old_single_control_groups_checked': len(old_counts),
          'old_single_coordinates_checked': 103 * 103, 'max_single_feature_discrepancy': max(errors),
          'source_pair_counts_checked': len(supported), 'source_pair_cells': int(supported.identity_qc_cells.sum()),
          'scope': 'Old saved single/control counts and normalized target coordinates reproduced; pair identity-QC counts retained. Not an independent raw double-expression extraction.'}
(OUT / 'EXTRACTION_AUDIT.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
