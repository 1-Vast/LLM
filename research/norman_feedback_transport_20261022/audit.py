"""Audit saved common-start results and current local continuity, no protected data."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_feedback_transport'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


scores = pd.read_csv(OUT / 'RESULTS.csv')
saved = json.loads((OUT / 'PREDICTIONS.json').read_text())
truth = np.asarray(saved['truth'])
assert len(saved['development_pairs']) == len(set(saved['development_pairs'])) == len(truth) == 1051
assert len(saved['records']) == len(scores) == 51
baseline_predictions = []
for record, row in zip(saved['records'], scores.itertuples()):
    prediction = np.asarray(record['prediction'])
    assert np.isfinite(prediction).all()
    assert row.model == record['model'] and row.later_n == record['later_n']
    assert abs(np.mean((prediction - truth) ** 2) - row.development_mse) < 1e-15
    if row.model == 'common_start':
        baseline_predictions.append(prediction)
assert all(np.array_equal(pred, baseline_predictions[0]) for pred in baseline_predictions)
selections = json.loads((OUT / 'SELECTIONS.json').read_text())
for selection in selections:
    if not selection['tag'].startswith('nuclear'):
        assert len(selection['scores']) == 9
        assert not set(selection['train_pairs']) & set(selection['validation_pairs'])
costs = json.loads((OUT / 'COSTS.json').read_text())
counts = pd.Series([c['kind'] for c in costs]).value_counts().to_dict()
assert counts == {'kernel_fit': 81, 'nuclear_fit': 12, 'quadratic_fit': 11}
primary = scores[scores.later_n.eq(512)].set_index('model')
fixed = primary.loc['lateronly_fixedRNA_earlyselected', 'development_mse']
adaptive = primary.loc['lateronly_mixture_earlyselected', 'development_mse']
strong = primary.loc['unionrefit_RNA_nuclear', 'development_mse']
report = {'saved_scores_recomputed': len(scores), 'common_start_exactly_identical': True,
          'all_selection_train_validation_pairs_disjoint': True, 'fit_counts': counts,
          'fit_count_total': sum(counts.values()), 'fit_seconds_sum': sum(c['seconds'] for c in costs),
          'primary_adaptive_vs_fixed_relative_MSE_improvement': float(1 - adaptive / fixed),
          'primary_union_nuclear_vs_adaptive_relative_MSE_improvement': float(1 - strong / adaptive),
          'protected_values_loaded': 0, 'scope': 'Saved prediction and split audit, not independent performance replication'}
(OUT / 'AUDIT.json').write_text(json.dumps(report, indent=2))
previous = json.loads((ROOT / 'log/20261022/norman_baseline_calibration/VERIFICATION.json').read_text())
drift = [name for name, expected in previous['files'].items()
         if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
files = {}
for folder in (OUT, Path(__file__).resolve().parent):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'VERIFICATION.json':
            files[path.relative_to(ROOT).as_posix()] = digest(path)
result = {'status': 'FAIL' if drift else 'PASS_LOCAL', 'predecessor_files_checked': len(previous['files']),
          'predecessor_drift': drift, 'scope': report['scope'], 'files': files}
(OUT / 'VERIFICATION.json').write_text(json.dumps(result, indent=2))
print(json.dumps(report, indent=2))
print('Predecessor drift:', drift, 'Current files sealed:', len(files))
assert not drift
