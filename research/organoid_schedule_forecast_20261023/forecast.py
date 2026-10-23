"""Fixed ordinary schedule-response predictors; all scores follow forecast sealing."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import time
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/organoid_schedule_forecast'
ARCHIVE = ROOT / 'log/20261023/organoid_schedule_qualification/root/zenodo_archive.body'
DIGEST = '997cbcdab23b754b1e0d94817ecac1b7f9fc8674a717c475d3e93fd4457bff82'
CONFIG = {'FAC': (tuple('abcdef'), 4, 8), 'OLA-IBET': (tuple('ab'), 3, 9)}


def features(actions, categories, mu, sd):
    z = (np.array([[r['t0'], r['t1']] for r in actions], dtype=float) - mu) / sd
    onehot = np.array([[float(r['seq'] == c) for c in categories] for r in actions])
    return np.column_stack((z, onehot, onehot * z[:, :1], onehot * z[:, 1:2]))


def predict_batch(initial, history, queries, categories):
    if any('cv' in q for q in queries):
        raise ValueError('Query labels forbidden')
    base = np.array([[r['t0'], r['t1']] for r in initial], dtype=float)
    mu, sd = base.mean(axis=0), base.std(axis=0)
    sd = np.where(sd == 0, 1.0, sd)
    xq = features(queries, categories, mu, sd)
    result = {}
    for prefix, training in [('frozen', initial), ('cumulative', history)]:
        x = features(training, categories, mu, sd)
        y = np.array([r['cv'] for r in training], dtype=float)
        xc, yc = x - x.mean(axis=0), y - y.mean()
        beta = np.linalg.solve(xc.T @ xc + np.eye(x.shape[1]), xc.T @ yc)
        result[prefix + '_ridge'] = (y.mean() + (xq - x.mean(axis=0)) @ beta).tolist()
        result[prefix + '_mean'] = [float(y.mean())] * len(queries)
        local = []
        for q in queries:
            distances = np.array([sum(((q[k] - r[k]) / sd[j]) ** 2
                                      for j, k in enumerate(('t0', 't1')))
                                  + 2 * (q['seq'] != r['seq']) for r in training])
            local.append(float(y[distances == distances.min()].mean()))
        result[prefix + '_nn'] = local
    if not all(math.isfinite(v) for values in result.values() for v in values):
        raise ValueError('Nonfinite prediction')
    return result


def action(row):
    return dict(seq=row['seq'], t0=float(row['t0']), t1=float(row['t1']),
                gen=int(row['gen']), number=int(row['number']))


def labelled(row):
    return dict(action(row), cv=float(row['cv']))


def read_tables():
    data = ARCHIVE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == DIGEST
    tables = {}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for campaign, (categories, ng, n) in CONFIG.items():
            matches = [x for x in archive.namelist()
                       if x.endswith(f'/{campaign}/sequential/data/data_{campaign}_seq.csv')]
            assert len(matches) == 1
            rows = list(csv.DictReader(io.StringIO(archive.read(matches[0]).decode('utf-8-sig'))))
            assert len(rows) == ng * n
            ids, actions = set(), set()
            for row in rows:
                a = action(row)
                assert row['gen'] == str(a['gen']) and row['number'] == str(a['number'])
                assert 0 <= a['gen'] < ng and 1 <= a['number'] <= n and a['seq'] in categories
                assert all(math.isfinite(float(row[k])) for k in ('t0', 't1', 'cv'))
                ident, key = (a['gen'], a['number']), (a['seq'], a['t0'], a['t1'])
                assert ident not in ids and key not in actions
                ids.add(ident)
                actions.add(key)
            assert all(sum(int(r['gen']) == g for r in rows) == n for g in range(ng))
            tables[campaign] = rows
    return tables


def metric(truth, pred):
    delta = np.array(pred) - np.array(truth)
    result = dict(mae=float(np.abs(delta).mean()), mse=float((delta ** 2).mean()))
    if not all(math.isfinite(v) for v in result.values()):
        raise ValueError('Nonfinite metric')
    return result


def forecast_campaign(campaign, rows, categories, ng):
    initial = [labelled(r) for r in rows if int(r['gen']) == 0]
    forecasts = []
    for g in range(1, ng):
        history = [labelled(r) for r in rows if int(r['gen']) < g]
        queries = [action(r) for r in rows if int(r['gen']) == g]
        predictions = predict_batch(initial, history, queries, categories)
        if g == 1:
            assert all(predictions['frozen_' + m] == predictions['cumulative_' + m]
                       for m in ('mean', 'ridge', 'nn'))
        forecasts.append(dict(campaign=campaign, gen=g, initial=initial,
                              history=history, queries=queries, predictions=predictions))
    return forecasts


def main():
    start = time.perf_counter()
    pilot = OUT / 'pilot'
    pilot.mkdir(parents=True, exist_ok=False)
    tables = read_tables()
    forecasts = []
    for campaign, rows in tables.items():
        categories, ng, _ = CONFIG[campaign]
        forecasts.extend(forecast_campaign(campaign, rows, categories, ng))
    target = pilot / 'FORECASTS.json'
    target.write_text(json.dumps(forecasts, indent=2, allow_nan=False), encoding='utf-8')
    (pilot / 'FORECAST_SEAL.json').write_text(json.dumps(dict(
        sha256=hashlib.sha256(target.read_bytes()).hexdigest(), scored=False,
        secure_blinding=False), indent=2), encoding='utf-8')
    batches, campaigns = [], {}
    for item in forecasts:
        truth = [float(r['cv']) for r in tables[item['campaign']] if int(r['gen']) == item['gen']]
        losses = {method: metric(truth, pred) for method, pred in item['predictions'].items()}
        pairs = {m: {k: losses['cumulative_' + m][k] - losses['frozen_' + m][k]
                     for k in ('mae', 'mse')} for m in ('mean', 'ridge', 'nn')}
        batches.append(dict(campaign=item['campaign'], gen=item['gen'], truth=truth,
                            losses=losses, paired_differences=pairs))
    for campaign in CONFIG:
        selected = [x for x in forecasts if x['campaign'] == campaign and x['gen'] >= 2]
        # File order is the same as generation order in this release; align explicitly.
        truth = [float(r['cv']) for x in selected for r in tables[campaign] if int(r['gen']) == x['gen']]
        campaigns[campaign] = {method: metric(truth, [v for x in selected for v in x['predictions'][method]])
                               for method in selected[0]['predictions']}
    gate = all(x['losses']['cumulative_ridge']['mae'] < x['losses']['frozen_ridge']['mae']
               for x in batches if x['gen'] >= 2)
    gate = gate and all(loss['cumulative_ridge']['mae'] < loss[m]['mae']
                        for loss in campaigns.values() for m in ('cumulative_mean', 'cumulative_nn'))
    result = dict(batches=batches, campaigns=campaigns, descriptive_gate=gate,
                  decision='GO_ORDINARY_FEEDBACK_UTILITY_ONLY' if gate else
                  'STOP_EXPANDING_THIS_FIXED_RIDGE_FEEDBACK_CONFIGURATION',
                  wall_seconds=time.perf_counter() - start, python=platform.python_version(),
                  numpy=np.__version__, random_operations=False,
                  scope='Historical adaptive campaign endpoint prediction; no novel updater or RSI')
    (pilot / 'RESULT.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps(dict(campaigns=campaigns, descriptive_gate=gate, decision=result['decision']), indent=2))


if __name__ == '__main__':
    main()
