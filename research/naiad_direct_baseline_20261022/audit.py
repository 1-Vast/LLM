"""Audit author-code receipts, permitted prediction outputs and predeclared seed summaries."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/naiad_direct_baseline'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


scores = pd.read_csv(OUT / 'SCORES.csv')
saved = json.loads((OUT / 'PREDICTIONS.json').read_text())
assert len(scores) == len(saved['records']) == 18
assert len(saved['pairs']) == len(set(saved['pairs'])) == 1051
truth = np.asarray(saved['truth'])
prior_saved = json.loads((ROOT / 'log/20261022/norman_baseline_calibration/DEVELOPMENT_PREDICTIONS.json').read_text())
assert saved['pairs'] == prior_saved['pairs'] and np.array_equal(truth, prior_saved['truth'])
for row, prediction in zip(scores.itertuples(), saved['records']):
    assert (row.budget, row.model_type, row.seed) == (prediction['budget'], prediction['model_type'], prediction['seed'])
    pred = np.asarray(prediction['prediction'])
    assert np.isfinite(pred).all()
    assert abs(np.mean((pred - truth) ** 2) - row.development_mse) < 1e-15
costs = json.loads((OUT / 'COSTS.json').read_text())
assert len(costs) == 36 and Counter(c['stage'] for c in costs) == {'inner': 18, 'final': 18}
assert all(c['epochs'] == 500 for c in costs if c['stage'] == 'inner')
history = json.loads((OUT / 'INNER_HISTORIES.json').read_text())
for record in history:
    row = scores[(scores.budget == record['budget']) & (scores.model_type == record['model_type']) & (scores.seed == record['seed'])].iloc[0]
    assert len(record['mse']) == 500
    assert row.selected_epoch == int(np.argmin(record['mse'])) + 1
    assert np.isclose(row.inner_validation_mse, min(record['mse']), atol=1e-15, rtol=0)
summary = scores.groupby(['budget', 'model_type']).development_mse.agg(['mean', 'std', 'min', 'max']).reset_index()
summary.to_csv(OUT / 'SEED_SUMMARY.csv', index=False)
receipts = Counter()
for receipt_file in (OUT / 'root_sources').glob('*.receipt.json'):
    receipt = json.loads(receipt_file.read_text())
    body = receipt_file.with_name(receipt_file.name.removesuffix('.receipt.json') + '.body')
    assert body.stat().st_size == receipt['bytes'] and digest(body) == receipt['sha256']
    receipts[receipt['status']] += 1
assert receipts == {200: 12}
for source, vendor in [('naiad__models.py.body', 'naiad_models.py'), ('LICENSE.body', 'LICENSE')]:
    assert digest(OUT / 'root_sources' / source) == digest(Path(__file__).resolve().parent / 'vendor' / vendor)
inputs = json.loads((OUT / 'INPUT_LEDGER.json').read_text())
for name, expected in inputs['inputs'].items():
    assert digest(ROOT / 'log/20261022/norman_numeric_qualification' / name) == expected
previous = json.loads((ROOT / 'log/20261022/norman_feedback_transport/VERIFICATION.json').read_text())
drift = [name for name, expected in previous['files'].items()
         if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
report = {'saved_predictions_recomputed': len(scores), 'fits': len(costs),
          'optimizer_steps': sum(c['optimizer_steps'] for c in costs),
          'inner_checkpoint_evaluations': sum(len(h['mse']) for h in history),
          'fit_seconds_sum': sum(c['seconds'] for c in costs), 'http_status_counts': dict(receipts),
          'protected_values_loaded': 0, 'independent_biological_tasks': 1,
          'scope': 'Saved scores and checkpoint-selection arithmetic plus exact vendor/input bytes; not external replication'}
(OUT / 'AUDIT.json').write_text(json.dumps(report, indent=2))
files = {}
for folder in (OUT, Path(__file__).resolve().parent):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'VERIFICATION.json':
            files[path.relative_to(ROOT).as_posix()] = digest(path)
verification = {'status': 'FAIL' if drift else 'PASS_LOCAL', 'predecessor_files_checked': len(previous['files']),
                'predecessor_drift': drift, 'scope': report['scope'], 'files': files}
(OUT / 'VERIFICATION.json').write_text(json.dumps(verification, indent=2))
print(summary.to_string(index=False))
print(json.dumps(report, indent=2))
print('Predecessor drift:', drift, 'Current files sealed:', len(files))
assert not drift
