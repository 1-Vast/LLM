"""Audit OOF masks, selected inner scores, replicate algebra and byte continuity."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_function_reliability'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


data = pd.read_csv(OUT / 'OOF_SOURCE.csv')
assert len(data) == data.pair.nunique() == 3160
membership = pd.read_csv(ROOT / 'log/20261022/norman_functional_contract/PAIR_SPLITS.csv').set_index('pair')
assert membership.loc[data.pair, 'split'].eq('source').all()
fold_map = dict(zip(data.pair, data.fold))
for row in data.itertuples():
    assert row.fold == int.from_bytes(hashlib.sha256(('MAESTRO_NORMAN_RELIABILITY_V1|' + row.pair).encode()).digest()[:8], 'big') % 5
selections = json.loads((OUT / 'SELECTIONS.json').read_text())
assert len(selections) == 20
for record in selections:
    train, validation = set(record['inner_train_pairs']), set(record['inner_validation_pairs'])
    assert not train & validation and len(record['candidates']) == 3
    assert all(fold_map[p] != record['fold'] for p in train | validation)
    assert record['selected_parameter'] == min(record['candidates'], key=lambda c: c['mse'])['parameter']
costs = json.loads((OUT / 'COSTS.json').read_text())
counts = dict(Counter(c['kind'] for c in costs))
assert counts == {'quadratic': 10, 'direct_RNA_ridge': 20, 'fusion_ridge': 20, 'identity_nuclear': 20, 'RNA_nuclear': 20}
moments = pd.read_csv(OUT / 'MOMENTS.csv')
reference = np.mean((data.replicate1 - data.replicate2) ** 2) / 4
for row in moments.itertuples():
    pred = data['prediction_' + row.model]
    assert np.isfinite(pred).all()
    e1, e2 = data.replicate1 - pred, data.replicate2 - pred
    mse = np.mean((data.growth - pred) ** 2)
    assert abs(mse - row.growth_mse) < 1e-14
    assert abs(np.mean(e1 * e2) - row.residual_cross_product) < 1e-14
    assert abs(np.mean(((data.replicate1 + data.replicate2) / 2 - pred) ** 2) - np.mean(e1 * e2) - reference) < 1e-14
for receipt_file in (OUT / 'root_sources').glob('*.receipt.json'):
    receipt = json.loads(receipt_file.read_text())
    body = receipt_file.with_name(receipt_file.name.removesuffix('.receipt.json') + '.body')
    assert receipt['status'] == 200 and body.stat().st_size == receipt['bytes'] and digest(body) == receipt['sha256']
previous = json.loads((ROOT / 'log/20261022/naiad_direct_baseline/VERIFICATION.json').read_text())
drift = [name for name, expected in previous['files'].items()
         if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
report = {'status': 'PASS_SAVED_DIAGNOSTIC', 'source_pairs': len(data), 'outer_predictions_checked': len(data) * len(moments),
          'nested_selections_checked': len(selections), 'fit_count': len(costs), 'fit_counts': counts,
          'fit_seconds_sum': sum(c['seconds'] for c in costs),
          'development_values_loaded': 0, 'protected_values_loaded': 0,
          'scope': 'Saved source prediction/moment/mask checks; no variance ceiling or independent experiment replication'}
(OUT / 'AUDIT.json').write_text(json.dumps(report, indent=2))
files = {}
for folder in (OUT, Path(__file__).resolve().parent):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'VERIFICATION.json':
            files[path.relative_to(ROOT).as_posix()] = digest(path)
verification = {'status': 'FAIL' if drift else 'PASS_LOCAL', 'predecessor_files_checked': len(previous['files']),
                'predecessor_drift': drift, 'scope': report['scope'], 'files': files}
(OUT / 'VERIFICATION.json').write_text(json.dumps(verification, indent=2))
print(json.dumps(report, indent=2))
print('Predecessor drift:', drift, 'Current files sealed:', len(files))
assert not drift
