"""Single-run scalar calibration falsifier; no assay file reads."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/action_rule_search'


def rule(p, residual, sigma, n):
    tau = sigma*sigma/n
    bound = math.sqrt(2*sigma*sigma*math.log(20)/n)
    raw = p*residual/(p*p+tau)
    delta = min(bound, max(-bound, raw))
    objective = lambda d: (residual-p*d)**2+tau*d*d
    feasible = [0., -bound, bound]
    if -bound <= raw <= bound:
        feasible.append(raw)
    assert objective(delta) <= min(objective(d) for d in feasible)+1e-12
    return {'tau': tau, 'bound': bound, 'unbounded_ridge': raw, 'delta': delta,
            'prediction': p*delta, 'bounded_ridge_objective': objective(delta)}


def main():
    assert not (OUT / 'API_FALSIFIER_STARTED.json').exists(), 'Do not rerun'
    freeze = json.loads((OUT / 'API_FREEZE.json').read_text(encoding='utf-8'))
    for relative, expected in freeze['files'].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    started = datetime.now(timezone.utc).isoformat()
    (OUT / 'API_FALSIFIER_STARTED.json').write_text(json.dumps({'utc': started}), encoding='utf-8')
    tick = time.perf_counter()
    cases = []
    for n in [100, 10000, 1000000]:
        row = rule(1., .5, 1., n)
        row.update(n=n, api_squared_error=(.5-row['prediction'])**2,
                   unbounded_ridge_squared_error=(.5-row['unbounded_ridge'])**2)
        cases.append(row)
    converted = rule(10., 5., 10., 100)
    converted['prediction_in_original_units'] = converted['prediction']/10
    assert abs(converted['unbounded_ridge']-cases[0]['unbounded_ridge']) < 1e-12
    coefficient_change = converted['delta']-cases[0]['delta']
    assert coefficient_change > .1
    assert all(cases[i+1]['delta'] < cases[i]['delta'] for i in range(2))
    assert all(cases[i+1]['api_squared_error'] > cases[i]['api_squared_error'] for i in range(2))
    result = {'status': 'PASS_LITERAL_RULE_FALSIFIER', 'started_utc': started,
              'ended_utc': datetime.now(timezone.utc).isoformat(),
              'wall_seconds': time.perf_counter()-tick, 'python': platform.python_version(),
              'n_cases': cases, 'unit_converted_n100': converted,
              'dimensionless_coefficient_change': coefficient_change,
              'asymptotic': 'abs(delta_n)<=sqrt(2*sigma^2*log(20)/n) -> 0 regardless of residuals',
              'scope': 'Literal one-shot alpha=1+delta and functional-noise bound only; no biological performance claim',
              'model_fits': 0, 'random_draws': 0, 'biological_values_read': 0}
    (OUT / 'API_FALSIFIER.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
