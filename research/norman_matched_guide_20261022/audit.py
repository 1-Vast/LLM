"""Recompute saved common-panel metrics, selection masks and local continuity."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_matched_guide'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data = pd.read_csv(OUT / 'OOF_COMMON_PANEL.csv')
    source = pd.read_csv(OUT / 'SOURCE_MATCHED_ENDPOINT.csv').set_index('pair')
    membership = pd.read_csv(ROOT / 'log/20261022/norman_functional_contract/PAIR_SPLITS.csv').set_index('pair')
    assert len(data) == data.pair.nunique() == 3107
    assert set(data.pair) == set(source.index)
    assert membership.loc[data.pair, 'split'].eq('source').all()
    assert len(set(data.gene_a) | set(data.gene_b)) == 102
    for row in data.itertuples():
        assert row.pair == row.gene_a + '|' + row.gene_b and row.gene_a < row.gene_b
        assert row.fold == int.from_bytes(hashlib.sha256(('MAESTRO_NORMAN_RELIABILITY_V1|' + row.pair).encode()).digest()[:8], 'big') % 5
    scores = pd.read_csv(OUT / 'COMMON_PANEL_SCORES.csv')
    folds = pd.read_csv(OUT / 'COMMON_PANEL_FOLDS.csv')
    result = json.loads((OUT / 'RESULT.json').read_text())
    assert len(scores) == 10 and len(folds) == 50
    models = {'quadratic', 'direct_RNA_ridge', 'fusion_ridge', 'identity_nuclear', 'RNA_nuclear'}
    expected_scores = {(endpoint, model) for endpoint in ['average', 'chosen'] for model in models}
    assert set(zip(scores.endpoint, scores.model)) == expected_scores
    assert set(zip(folds.endpoint, folds.fold, folds.model)) == {(e, f, m) for e, m in expected_scores for f in range(5)}
    gains = {}
    for endpoint, target in [('average', 'original_gene_average_growth'), ('chosen', 'chosen_processed_growth')]:
        truth = data['truth_' + endpoint].to_numpy()
        assert np.allclose(truth, source.loc[data.pair, target], rtol=0, atol=1e-14)
        q_mse = np.mean((truth - data['prediction_' + endpoint + '_quadratic']) ** 2)
        for row in scores[scores.endpoint.eq(endpoint)].itertuples():
            pred = data['prediction_' + endpoint + '_' + row.model].to_numpy()
            assert np.isfinite(pred).all()
            mse = np.mean((truth - pred) ** 2)
            assert abs(mse - row.mse) < 1e-14
            assert abs(np.var(truth) - row.endpoint_variance) < 1e-14
            assert abs(mse / q_mse - row.mse_over_quadratic_mse) < 1e-12
            for fold in range(5):
                mask = data.fold.eq(fold)
                saved = folds[folds.endpoint.eq(endpoint) & folds.model.eq(row.model) & folds.fold.eq(fold)].iloc[0]
                assert saved.pairs == mask.sum()
                assert abs(np.mean((truth[mask] - pred[mask]) ** 2) - saved.mse) < 1e-14
        sub = scores[scores.endpoint.eq(endpoint)].set_index('model').mse
        gain = 1 - sub.RNA_nuclear / sub.identity_nuclear
        assert abs(gain - result['gains'][endpoint]['relative_RNA_gain']) < 1e-12
        gains[endpoint] = float(gain)
    delta = gains['chosen'] - gains['average']
    assert abs(delta - result['chosen_minus_average_relative_gain']) < 1e-12
    assert result['fixed_prediction_hypothesis'] == ('DESCRIPTIVE_DIRECTION_SUPPORTED' if delta > 0 else 'STOP_FIXED_ALIGNMENT_BENEFIT_PREDICTION')
    selections = json.loads((OUT / 'SELECTIONS.json').read_text())
    assert len(selections) == 40
    assert {(s['endpoint'], s['fold'], s['model']) for s in selections} == {(e, f, m) for e, m in expected_scores if m != 'quadratic' for f in range(5)}
    for record in selections:
        train = data[data.fold.ne(record['fold'])].pair.tolist()
        train.sort(key=lambda p: membership.loc[p, 'source_order'])
        boundary = 3 * len(train) // 4
        assert record['inner_pairs'] == train[:boundary]
        assert record['validation_pairs'] == train[boundary:]
        assert len(record['candidates']) == 3
        assert record['selected_parameter'] == min(record['candidates'], key=lambda c: c['mse'])['parameter']
    costs = json.loads((OUT / 'COSTS.json').read_text())
    counts = dict(Counter(c['kind'] for c in costs))
    assert counts == {'quadratic': 20, 'direct_RNA_ridge': 40, 'fusion_ridge': 40, 'identity_nuclear': 40, 'RNA_nuclear': 40}
    assert result['fit_count'] == len(costs) == 180
    assert result['selected_nuclear_stop_heuristic_unmet'] == sum(not s['outer_refit'].get('converged', True) for s in selections)
    fold_gains = []
    for endpoint in ['average', 'chosen']:
        for fold in range(5):
            sub = folds[folds.endpoint.eq(endpoint) & folds.fold.eq(fold)].set_index('model').mse
            fold_gains.append({'endpoint': endpoint, 'fold': fold,
                               'relative_RNA_gain': float(1 - sub.RNA_nuclear / sub.identity_nuclear),
                               'absolute_RNA_gain': float(sub.identity_nuclear - sub.RNA_nuclear)})
    pd.DataFrame(fold_gains).to_csv(OUT / 'FOLD_GAINS.csv', index=False)
    for receipt_file in (OUT / 'root_sources').glob('*.receipt.json'):
        receipt = json.loads(receipt_file.read_text())
        body = receipt_file.with_name(receipt_file.name.removesuffix('.receipt.json') + '.body')
        assert receipt['status'] == 200 and body.stat().st_size == receipt['bytes'] and digest(body) == receipt['sha256']
    previous = json.loads((ROOT / 'log/20261022/norman_function_reliability/VERIFICATION.json').read_text())
    drift = [name for name, expected in previous['files'].items() if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
    assert not drift, drift
    report = {'status': 'PASS_SAVED_COMMON_PANEL', 'pairs': len(data), 'predictions_checked': 31070,
              'selections_checked': len(selections), 'fits': len(costs), 'fit_counts': counts,
              'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
              'fit_seconds_sum': sum(c['seconds'] for c in costs),
              'scope': 'Saved arithmetic and static access review; not independent biological replication or global provenance repair'}
    (OUT / 'AUDIT.json').write_text(json.dumps(report, indent=2))
    files = {}
    for folder in (OUT, Path(__file__).resolve().parent):
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path.name != 'VERIFICATION.json':
                files[path.relative_to(ROOT).as_posix()] = digest(path)
    (OUT / 'VERIFICATION.json').write_text(json.dumps({**report, 'status': 'PASS_LOCAL', 'files': files}, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
