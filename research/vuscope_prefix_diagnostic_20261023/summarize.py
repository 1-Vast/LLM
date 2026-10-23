"""Report frozen outcomes and optimization/accounting limits without refitting."""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/vuscope_prefix_diagnostic'

if __name__ == '__main__':
    run = OUT/'pilot'
    fits = json.loads((run/'PREFIX_FITS.json').read_text())
    metrics = json.loads((run/'METRICS.json').read_text())
    by = {(m['key'],m['method']):m for m in metrics}
    keys = sorted(set(m['key'] for m in metrics))
    fitby = {(f['key'],f['method']):f for f in fits}
    fixed_losses = {k:min(s['loss'] for s in fitby[k,'vuscope6']['starts']) for k in keys}
    moving_losses = {k:min(s['loss'] for s in fitby[k,'moving_midpoint7']['starts']) for k in keys}
    comparison = {}
    for method in ('moving_midpoint7','independent_logistic','direct_selected','persistence'):
        delta = [by[k,method]['mse120']-by[k,'vuscope6']['mse120'] for k in keys]
        comparison[method] = dict(wins_primary=sum(x<0 for x in delta), median_paired_delta=float(np.median(delta)),
                                  mean_paired_delta=float(np.mean(delta)))
    accounting = {}
    for method in ('vuscope6','moving_midpoint7','independent_logistic','direct_selected','persistence'):
        selected = [f for f in fits if f['method']==method]
        attempts = []
        for fit in selected:
            attempts.extend(fit.get('starts', []))
            for dose in fit.get('doses', []):
                attempts.extend(dose)
        accounting[method] = dict(seconds=sum(f['seconds'] for f in selected),
                                   nonlinear_starts=len(attempts),
                                   solver_nfev=sum(a['nfev'] for a in attempts),
                                   solver_njev=sum(a['njev'] or 0 for a in attempts),
                                   budget_limited_starts=sum(a['status']==0 for a in attempts),
                                   scope='nfev/njev are solver counters, not all numerical-Jacobian calls or matched FLOPs')
    report = dict(comparison=comparison, accounting=accounting,
                  nested_optimizer=dict(moving_worse_prefix_sse=[k for k in keys if moving_losses[k] > fixed_losses[k]+1e-10],
                                        fixed_sse=fixed_losses,moving_sse=moving_losses),
                  direct_selections={k:fitby[k,'direct_selected']['selected'] for k in keys},
                  boundary='Post-result arithmetic only; no fitting, parameter selection, subgroup rescue or new biological task')
    target = OUT/'POST_RESULT_SUMMARY.json'
    assert not target.exists()
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(comparison=comparison,accounting=accounting,
                         moving_worse_prefix_groups=len(report['nested_optimizer']['moving_worse_prefix_sse'])), indent=2))
