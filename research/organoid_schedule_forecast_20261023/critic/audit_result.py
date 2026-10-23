"""Independent stored-result audit; never import/execute the predictor."""
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
LOG = ROOT / 'log/20261023/organoid_schedule_forecast'
forecasts = json.loads((LOG / 'pilot/FORECASTS.json').read_text())
result = json.loads((LOG / 'pilot/RESULT.json').read_text())
freeze = json.loads((LOG / 'FREEZE.json').read_text())
assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
           for p, h in freeze['files'].items())
seal = json.loads((LOG / 'pilot/FORECAST_SEAL.json').read_text())
assert hashlib.sha256((LOG / 'pilot/FORECASTS.json').read_bytes()).hexdigest() == seal['sha256']
assert seal['scored'] is False and seal['secure_blinding'] is False
assert json.loads((LOG / 'EXECUTION.json').read_text())['returncode'] == 0
archive = ROOT / 'log/20261023/organoid_schedule_qualification/root/zenodo_archive.body'
tables = {}
with zipfile.ZipFile(archive) as z:
    for campaign in ('FAC', 'OLA-IBET'):
        name, = [n for n in z.namelist() if n.endswith(f'/{campaign}/sequential/data/data_{campaign}_seq.csv')]
        tables[campaign] = list(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))))

differences = []
def close(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    assert a.shape == b.shape
    differences.extend(np.abs(a - b).ravel().tolist())
    assert np.allclose(a, b, atol=1e-9, rtol=1e-11)

def record(r, labels=False):
    d = dict(seq=r['seq'], t0=float(r['t0']), t1=float(r['t1']), gen=int(r['gen']), number=int(r['number']))
    if labels:
        d['cv'] = float(r['cv'])
    return d

def losses(y, p):
    errors = [float(a) - float(b) for a, b in zip(y, p)]
    return dict(mae=sum(abs(x) for x in errors) / len(errors), mse=sum(x*x for x in errors) / len(errors))

assert [(f['campaign'], f['gen']) for f in forecasts] == [('FAC', 1), ('FAC', 2), ('FAC', 3), ('OLA-IBET', 1), ('OLA-IBET', 2)]
batchloss = {}
for f, b in zip(forecasts, result['batches']):
    campaign, g = f['campaign'], f['gen']
    rows = tables[campaign]
    assert f['initial'] == [record(r, True) for r in rows if int(r['gen']) == 0]
    assert f['history'] == [record(r, True) for r in rows if int(r['gen']) < g]
    assert f['queries'] == [record(r) for r in rows if int(r['gen']) == g]
    assert all(r['gen'] < g for r in f['history'])
    assert all(set(r) == {'seq', 't0', 't1', 'gen', 'number'} for r in f['queries'])
    categories = tuple('abcdef') if campaign == 'FAC' else tuple('ab')
    base = np.array([[r['t0'], r['t1']] for r in f['initial']])
    mu, sd = base.mean(0), base.std(0)
    sd[sd == 0] = 1
    def design(records):
        values = []
        for r in records:
            u, v = (np.array([r['t0'], r['t1']]) - mu) / sd
            cat = [float(r['seq'] == c) for c in categories]
            values.append([1., u, v] + cat + [a*u for a in cat] + [a*v for a in cat])
        return np.array(values)
    qx = design(f['queries'])
    for prefix, train in [('frozen', f['initial']), ('cumulative', f['history'])]:
        x = design(train)
        y = np.array([r['cv'] for r in train])
        penalty = np.eye(x.shape[1]); penalty[0, 0] = 0
        coefficients = np.linalg.solve(x.T @ x + penalty, x.T @ y)
        close(qx @ coefficients, f['predictions'][prefix + '_ridge'])
        close([sum(y)/len(y)] * len(qx), f['predictions'][prefix + '_mean'])
        nn = []
        for q in f['queries']:
            ds = [sum(((q[k]-r[k])/sd[j])**2 for j, k in enumerate(('t0', 't1'))) + (0 if q['seq'] == r['seq'] else 2) for r in train]
            nearest = [r['cv'] for r, d in zip(train, ds) if d == min(ds)]
            nn.append(sum(nearest)/len(nearest))
        close(nn, f['predictions'][prefix + '_nn'])
    if g == 1:
        assert all(f['predictions']['frozen_' + m] == f['predictions']['cumulative_' + m] for m in ('mean', 'ridge', 'nn'))
    truth = [float(r['cv']) for r in rows if int(r['gen']) == g]
    assert b['campaign'] == campaign and b['gen'] == g
    close(truth, b['truth'])
    batchloss[campaign, g] = {}
    for method, p in f['predictions'].items():
        computed = losses(truth, p)
        for metric in ('mae', 'mse'):
            close(computed[metric], b['losses'][method][metric])
        batchloss[campaign, g][method] = computed
    for m in ('ridge', 'mean', 'nn'):
        for k in ('mae', 'mse'):
            close(b['losses']['cumulative_' + m][k] - b['losses']['frozen_' + m][k], b['paired_differences'][m][k])

for campaign, stored in result['campaigns'].items():
    chosen = [f for f in forecasts if f['campaign'] == campaign and f['gen'] >= 2]
    truth = [float(r['cv']) for f in chosen for r in tables[campaign] if int(r['gen']) == f['gen']]
    for method in stored:
        computed = losses(truth, [p for f in chosen for p in f['predictions'][method]])
        for k in computed:
            close(computed[k], stored[method][k])
gate_batch = all(v['cumulative_ridge']['mae'] < v['frozen_ridge']['mae'] for (c, g), v in batchloss.items() if g >= 2)
gate_controls = all(v['cumulative_ridge']['mae'] < v[m]['mae'] for v in result['campaigns'].values() for m in ('cumulative_mean', 'cumulative_nn'))
assert (gate_batch and gate_controls) == result['descriptive_gate'] == False
assert result['decision'] == 'STOP_EXPANDING_THIS_FIXED_RIDGE_FEEDBACK_CONFIGURATION'
output = dict(status='PASS', comparisons=len(differences), maximum_absolute_difference=max(differences),
              freeze_hashes_match=True, forecast_hash_matches=True, source_objects_match=True,
              independently_reconstructed_predictions=True, gate_batch=gate_batch,
              gate_controls=gate_controls, decision=result['decision'],
              disclosure='Root exposed gate and campaign ridge summary before audit. No result-blind claim; no predictor import/main execution; no peer result read.')
(LOG / 'critic/AUDIT.json').write_text(json.dumps(output, indent=2, allow_nan=False))
print(json.dumps(output, indent=2))
