"""Independent saved-prediction arithmetic review; no fitting or protected outcomes."""
from collections import Counter
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_matched_guide'
d = pd.read_csv(OUT / 'OOF_COMMON_PANEL.csv')
s = pd.read_csv(OUT / 'COMMON_PANEL_SCORES.csv')
f = pd.read_csv(OUT / 'COMMON_PANEL_FOLDS.csv')
c = json.loads((OUT / 'COSTS.json').read_text())
sel = json.loads((OUT / 'SELECTIONS.json').read_text())
r = json.loads((OUT / 'RESULT.json').read_text())
assert len(d) == d.pair.nunique() == 3107
fold_gains = {}
for endpoint in ['average', 'chosen']:
    y = d['truth_' + endpoint].to_numpy()
    for row in s[s.endpoint.eq(endpoint)].itertuples():
        p = d['prediction_' + endpoint + '_' + row.model].to_numpy()
        assert np.isfinite(p).all()
        assert abs(np.mean((y-p)**2) - row.mse) < 1e-14
        assert abs(np.var(y)-row.endpoint_variance) < 1e-14
        for fold in range(5):
            mask = d.fold.eq(fold)
            saved = f[f.endpoint.eq(endpoint) & f.model.eq(row.model) & f.fold.eq(fold)]
            assert len(saved) == 1
            assert abs(np.mean((y[mask]-p[mask])**2)-saved.mse.iloc[0]) < 1e-14
    z = f[f.endpoint.eq(endpoint)].pivot(index='fold', columns='model', values='mse')
    fold_gains[endpoint] = (1-z.RNA_nuclear/z.identity_nuclear).tolist()
assert len(c) == 180 and len(sel) == 40
assert all(v['selected_parameter'] == min(v['candidates'], key=lambda x:x['mse'])['parameter'] for v in sel)
nc = [x for x in c if 'converged' in x]
report = {'fold_gains':fold_gains,
          'paired_gain_delta':[b-a for a,b in zip(fold_gains['average'],fold_gains['chosen'])],
          'fit_counts':dict(Counter(x['kind'] for x in c)),
          'fit_seconds':{kind:sum(x['seconds'] for x in c if x['kind']==kind) for kind in sorted(set(x['kind'] for x in c))},
          'nuclear_candidates_and_refits':len(nc),
          'all_nuclear_stop_heuristic_unmet':sum(not x['converged'] for x in nc),
          'selected_outer_stop_heuristic_unmet':sum(not x['outer_refit'].get('converged',True) for x in sel),
          'nuclear_iterations_range':[min(x['iterations'] for x in nc),max(x['iterations'] for x in nc)],
          'wall_seconds':r['wall_seconds'], 'status':'PASS_SAVED_ARITHMETIC'}
(OUT / 'reviews/result_audit_calculations.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
