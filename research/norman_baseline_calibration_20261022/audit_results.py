"""Recompute development scores and gene-incidence sensitivity from saved predictions."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_baseline_calibration'
INP = ROOT / 'log/20261022/norman_numeric_qualification'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


scores = pd.read_csv(OUT / 'ALL_SCORES.csv')
saved = json.loads((OUT / 'DEVELOPMENT_PREDICTIONS.json').read_text())
truth = np.asarray(saved['truth'])
pairs = saved['pairs']
assert len(truth) == len(set(pairs)) == 1051
exported = pd.read_csv(INP / 'FUNCTION_SOURCE_DEVELOPMENT.csv').set_index('pair')
assert exported.loc[pairs, 'split'].eq('development').all()
assert np.allclose(truth, exported.loc[pairs, 'growth'])
assert len(scores) == len(saved['predictions']) == 51
prediction_map = {}
for record, (_, row) in zip(saved['predictions'], scores.iterrows()):
    assert record['budget'] == row.budget_source_pairs and record['model'] == row.model
    pred = np.asarray(record['pred'])
    assert np.isfinite(pred).all()
    mse = float(np.mean((pred - truth) ** 2))
    assert np.isclose(mse, row.development_mse, atol=1e-15, rtol=0)
    prediction_map[(record['budget'], record['model'], str(record['parameter']))] = pred
selected = pd.read_csv(OUT / 'DEVELOPMENT_SELECTED.csv')
assert len(selected) == 21
for row in selected.itertuples():
    candidates = scores[(scores.budget_source_pairs == row.budget_source_pairs) & (scores.model == row.model)]
    assert np.isclose(row.development_mse, candidates.development_mse.min(), rtol=0, atol=1e-15)
largest = selected[selected.budget_source_pairs.eq(2048)].set_index('model')
models = ['RNA_side_nuclear_completion', 'identity_nuclear_completion', 'identity_RNA_fusion_residual_ridge']
chosen = {name: prediction_map[(2048, name, str(largest.loc[name, 'parameter']))] for name in models}
genes = sorted({g for pair in pairs for g in pair.split('|')})
rows = []
for gene in genes:
    incident = np.array([gene in pair.split('|') for pair in pairs])
    row = {'gene': gene, 'incident_development_pairs': int(incident.sum())}
    for name, pred in chosen.items():
        row[name + '_mse'] = float(np.mean((pred[incident] - truth[incident]) ** 2))
    rows.append(row)
pd.DataFrame(rows).to_csv(OUT / 'GENE_INCIDENCE_SENSITIVITY.csv', index=False)
report = {'candidate_evaluations_recomputed': len(scores), 'all_predictions_finite': True,
          'unique_development_pairs': len(pairs), 'nonconverged_completion_candidates': int(scores.converged.eq(False).sum()),
          'selected_completion_candidates_converged': bool(selected[selected.model.str.contains('completion')].converged.all()),
          'function_fits': 48, 'mean_candidates': 3,
          'sum_recorded_candidate_seconds': float(scores.seconds.sum()),
          'source_dev_label_exposure': {'source_pool': 3160, 'development': 1051},
          'gene_incidence_count': len(genes),
          'genes_with_RNA_better_than_noRNA_completion': sum(r[models[0] + '_mse'] < r[models[1] + '_mse'] for r in rows),
          'genes_with_RNA_better_than_simple_fusion': sum(r[models[0] + '_mse'] < r[models[2] + '_mse'] for r in rows),
          'gene_incidence_is_independent_replication': False, 'protected_values_loaded': 0,
          'scope': 'Root-only saved-prediction audit, not independent code or external performance validation'}
(OUT / 'RESULT_AUDIT.json').write_text(json.dumps(report, indent=2))
previous = json.loads((INP / 'VERIFICATION.json').read_text())
drift = [name for name, expected in previous['files'].items()
         if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
files = {}
for folder in (OUT, Path(__file__).resolve().parent):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'VERIFICATION.json':
            files[path.relative_to(ROOT).as_posix()] = digest(path)
verification = {'status': 'FAIL' if drift else 'PASS_LOCAL',
                'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
                'scope': report['scope'], 'files': files}
(OUT / 'VERIFICATION.json').write_text(json.dumps(verification, indent=2))
print(json.dumps(report, indent=2))
print('Predecessor drift:', drift, 'Current files sealed:', len(files))
assert not drift
