"""Audit stored forecasts/scores; does not rerun forecasting or read raw assay CSV."""
from pathlib import Path
import hashlib
import json
import math
from statistics import mean

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'log/20261023/public_recovery_task'
prefix_path = BASE / 'pilot/PREFIX_FORECASTS.json'
prefixes = json.loads(prefix_path.read_text())
result = json.loads((BASE / 'pilot/RESULT.json').read_text())
freeze = json.loads((BASE / 'NUMERIC_FREEZE.json').read_text())
for name, expected in freeze['files'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
seal = json.loads((BASE / 'pilot/PREDICTION_SEAL.json').read_text())
assert hashlib.sha256(prefix_path.read_bytes()).hexdigest() == seal['sha256']
assert seal['query_values_converted'] is False
differences = []
for prefix, scored in zip(prefixes, result['scored']):
    assert (prefix['sample'], prefix['schedule']) == (scored['sample'], scored['schedule'])
    m = prefix['means']
    a, b = m['7'] / m['0'], m['14'] / m['0']
    q = b / a
    expected = {'persistence': [b, b], 'global_exp': [b ** 1.5, b ** 2],
                'latest_interval': [b * q, b * q ** 2]}
    expected['first_cycle'] = ([b * a, b ** 2] if prefix['schedule'] == 'Intermittent'
                               else expected['latest_interval'])
    for method, predictions in expected.items():
        differences.extend(abs(x-y) for x,y in zip(predictions, prefix['predictions'][method]))
        errors = [(p-y)**2 for p,y in zip(predictions, scored['truth'])]
        absolute = [abs(p-y) for p,y in zip(predictions, scored['truth'])]
        s = scored['scores'][method]
        differences.extend(abs(x-y) for x,y in zip(errors, s['squared_error']))
        differences.extend(abs(x-y) for x,y in zip(absolute, s['absolute_error']))
        differences.extend((abs(s['mse28']-errors[1]), abs(s['late_mse']-mean(errors)),
                            abs(s['mae28']-absolute[1])))
    if prefix['schedule'] == 'Continuous':
        assert expected['first_cycle'] == expected['latest_interval']
    else:
        assert expected['first_cycle'][1] == expected['global_exp'][1]
for method, scores in result['summary'].items():
    for metric, value in scores.items():
        differences.append(abs(value - mean(s['scores'][method][metric] for s in result['scored'])))
intermittent = [r for r in result['scored'] if r['schedule'] == 'Intermittent']
gate = all(r['scores']['first_cycle']['late_mse'] < r['scores']['latest_interval']['late_mse']
           for r in intermittent)
assert gate is result['descriptive_gate']
assert max(differences) < 1e-12
patterns = []
for prefix, scored in zip(prefixes, result['scored']):
    if prefix['schedule'] != 'Intermittent':
        continue
    a = prefix['means']['7'] / prefix['means']['0']
    b = prefix['means']['14'] / prefix['means']['0']
    y21, y28 = scored['truth']
    patterns.append(dict(sample=prefix['sample'], early_on_factor=a, early_off_factor=b/a,
                         later_on_factor=y21/b,
                         later_off_factor=(y28/y21 if y21 else None)))
report = dict(scope='Stored artifact arithmetic/hash audit; no new forecast or raw CSV parsing',
              max_abs_discrepancy=max(differences), comparisons=len(differences),
              all_freeze_hashes_match=True, prefix_seal_matches=True,
              descriptive_gate=gate, intermittent_patterns=patterns)
(BASE / 'critic/RESULT_AUDIT.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
