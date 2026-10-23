"""Independent saved-output arithmetic review; no fitting or held-out labels."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[2]
p = root / 'log/20261022/norman_matched_guide'
oof = pd.read_csv(p / 'OOF_COMMON_PANEL.csv')
scores = pd.read_csv(p / 'COMMON_PANEL_SCORES.csv')
folds = pd.read_csv(p / 'COMMON_PANEL_FOLDS.csv')
costs = json.loads((p / 'COSTS.json').read_text())
selections = json.loads((p / 'SELECTIONS.json').read_text())
result = json.loads((p / 'RESULT.json').read_text())
assert len(oof) == oof.pair.nunique() == 3107
assert len(costs) == result['fit_count'] == 180
assert len(selections) == 40
summary = {}
for endpoint in ['average', 'chosen']:
    truth = oof['truth_' + endpoint]
    ss = scores[scores.endpoint.eq(endpoint)].set_index('model')
    for model in ss.index:
        err = (oof[f'prediction_{endpoint}_{model}'] - truth) ** 2
        assert np.isclose(err.mean(), ss.loc[model, 'mse'], atol=1e-15, rtol=1e-12)
        assert np.isclose(truth.var(ddof=0), ss.loc[model, 'endpoint_variance'])
        for fold, inds in oof.groupby('fold').groups.items():
            row = folds[folds.endpoint.eq(endpoint) & folds.model.eq(model) & folds.fold.eq(fold)].iloc[0]
            assert len(inds) == row.pairs and np.isclose(err.loc[inds].mean(), row.mse)
    gains = []
    for fold in range(5):
        ff = folds[folds.endpoint.eq(endpoint) & folds.fold.eq(fold)].set_index('model')
        gains.append(float(1 - ff.loc['RNA_nuclear', 'mse'] / ff.loc['identity_nuclear', 'mse']))
    rel = float(1 - ss.loc['RNA_nuclear', 'mse'] / ss.loc['identity_nuclear', 'mse'])
    absolute = float(ss.loc['identity_nuclear', 'mse'] - ss.loc['RNA_nuclear', 'mse'])
    assert np.isclose(rel, result['gains'][endpoint]['relative_RNA_gain'])
    assert np.isclose(absolute, result['gains'][endpoint]['absolute_RNA_gain'])
    summary[endpoint] = {'relative_gain': rel, 'absolute_gain': absolute, 'fold_relative_gains': gains}
delta = summary['chosen']['relative_gain'] - summary['average']['relative_gain']
assert np.isclose(delta, result['chosen_minus_average_relative_gain'])
assert result['fixed_prediction_hypothesis'] == ('DESCRIPTIVE_DIRECTION_SUPPORTED' if delta > 0 else 'STOP_FIXED_ALIGNMENT_BENEFIT_PREDICTION')
for selection in selections:
    assert set(selection['inner_pairs']).isdisjoint(selection['validation_pairs'])
    assert len(selection['candidates']) == 3
    assert selection['selected_parameter'] == min(selection['candidates'], key=lambda c: c['mse'])['parameter']
summary['fold_relative_gain_differences'] = (np.array(summary['chosen']['fold_relative_gains']) - np.array(summary['average']['fold_relative_gains'])).tolist()
summary['status'] = 'SAVED_OUTPUT_ARITHMETIC_PASS'
(p / 'reviews/interpretation_arithmetic.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
