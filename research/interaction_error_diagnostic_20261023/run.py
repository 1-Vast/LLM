"""Completed-screen development diagnostic; never cast lung score values."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import scipy
import sklearn
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics.pairwise import rbf_kernel
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/interaction_error_diagnostic'
DATA = ROOT / 'log/20261023/update_law_search/task/interaction_supplement.body'
DEV = ['MCF7', 'MDAMB231', 'MCF10A', 'CAL27', 'CAL33']
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path=DATA, expected_sha='4a10d978247ebc5009284ca95c7c59c096530f502638932823db17093d842230'):
    assert digest(path) == expected_sha
    with zipfile.ZipFile(path) as archive:
        shared = [''.join(s.itertext()) for s in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))

    def value(cell):
        v = cell.find('m:v', NS)
        if v is None:
            return ''.join(cell.itertext())
        return shared[int(v.text)] if cell.attrib.get('t') == 's' else v.text

    rows = sheet.findall('m:sheetData/m:row', NS)
    headers = {''.join(c for c in cell.attrib['r'] if c.isalpha()): value(cell) for cell in rows[0]}
    cols = {col: DEV.index(name) for col, name in headers.items() if name in DEV}
    assert len(cols) == 5 and not {'H', 'I'} & cols.keys()
    grouped = {}
    for row in rows[1:]:
        ids, scores = {}, np.full(5, np.nan)
        for cell in row:
            col = ''.join(c for c in cell.attrib['r'] if c.isalpha())
            if col in ('A', 'B'):
                ids[col] = value(cell)
            elif col in cols:
                text = value(cell)
                if text and cell.attrib.get('t') != 'e':
                    try:
                        scores[cols[col]] = float(text)
                    except ValueError:
                        assert text.lower() in ('nan', 'na', 'n/a', 'none'), text
            # Explicitly do not call value() on H/I or other nondevelopment cells.
        key = tuple(sorted((ids['A'], ids['B'])))
        if key in grouped:
            assert np.allclose(grouped[key], scores, rtol=0, atol=1e-10, equal_nan=True), key
        else:
            grouped[key] = scores
    retained, exclusions = {}, Counter()
    for pair, scores in grouped.items():
        if pair[0] == pair[1]:
            exclusions['self'] += 1
        elif set(pair) & {'AAVS', 'nontargeting'}:
            exclusions['control'] += 1
        elif not np.isfinite(scores).all():
            exclusions['incomplete_five_dev'] += 1
        else:
            retained[pair] = scores
    pairs = sorted(retained)
    genes = sorted({g for pair in pairs for g in pair})
    positions = {g: i for i, g in enumerate(genes)}
    z = np.zeros((len(pairs), len(genes)))
    for i, pair in enumerate(pairs):
        for gene in pair:
            z[i, positions[gene]] = 1
    y = np.array([retained[pair] for pair in pairs])
    metadata = dict(raw_rows=len(rows)-1, canonical=len(grouped), eligible=len(pairs),
                    genes=len(genes), exclusions=dict(exclusions),
                    parsed_score_columns=DEV, unparsed_score_columns=['A549', 'A427'])
    return pairs, y, z, metadata


def order(pairs, salt):
    return np.array(sorted(range(len(pairs)), key=lambda i: hashlib.sha256(
        (str(salt) + '|' + '|'.join(pairs[i])).encode()).hexdigest()))


def fit_predict(spec, x, z, y, train, query):
    kind, param = spec
    if kind == 'mean':
        return x[query].mean(axis=1)
    if kind == 'targetmean':
        return np.full(len(query), y[train].mean())
    if kind == 'calibration':
        a, b = x[train].mean(axis=1), x[query].mean(axis=1)
        model = Ridge(alpha=1).fit(a[:, None], y[train])
        return model.predict(b[:, None])
    if kind == 'trees':
        model = ExtraTreesRegressor(n_estimators=128, min_samples_leaf=param,
                                    random_state=0, n_jobs=1)
        return model.fit(x[train], y[train]).predict(x[query])
    if kind in ('rbf', 'jointkernel'):
        gamma, alpha = param
        k = rbf_kernel(x[train], x[train], gamma=gamma)
        q = rbf_kernel(x[query], x[train], gamma=gamma)
        if kind == 'jointkernel':
            k += z[train] @ z[train].T
            q += z[query] @ z[train].T
        intercept = y[train].mean()
        coef = np.linalg.solve(k + alpha*np.eye(len(train)), y[train] - intercept)
        return intercept + q @ coef
    if kind == 'ridge':
        return Ridge(alpha=param).fit(x[train], y[train]).predict(x[query])
    if kind == 'joint':
        features = np.column_stack((x, z))
        return Ridge(alpha=param).fit(features[train], y[train]).predict(features[query])
    assert kind == 'residual'
    base = Ridge(alpha=1).fit(x[train], y[train])
    residual = y[train] - base.predict(x[train])
    updater = Ridge(alpha=param).fit(z[train], residual)
    return base.predict(x[query]) + updater.predict(z[query])


def metrics(prediction, truth):
    assert np.isfinite(prediction).all()
    nomination = np.argsort(prediction, kind='stable')[:20]
    optimal = np.sort(truth)[:20].mean()
    return dict(mse=float(np.mean((truth-prediction)**2)),
                bottom20_mean=float(truth[nomination].mean()),
                bottom20_regret=float(truth[nomination].mean()-optimal))


SCORE = [('ridge', a) for a in (.1, 1, 10, 100)] + [('trees', l) for l in (2, 8, 24)] + [
    ('rbf', (g, a)) for g in (.25, 1) for a in (1, 10)]
IDENTITY = [(k, a) for k in ('joint', 'residual') for a in (1, 10, 100)] + [
    ('jointkernel', (g, a)) for g in (.25, 1) for a in (1, 10)]


def main():
    target = OUT / 'RESULTS.json'
    assert not target.exists()
    started = time.perf_counter()
    pairs, all_y, z, metadata = load()
    assert len(pairs) > 1024
    records, arrays = [], {'development_scores': all_y, 'gene_incidence': z}
    (OUT/'PAIR_IDS.json').write_text(json.dumps(pairs), encoding='utf-8')
    for context, name in enumerate(DEV):
        raw_x = np.delete(all_y, context, axis=1)
        # Only source columns, no target outcomes, determine the feature transform.
        x = (raw_x - raw_x.mean(axis=0)) / np.maximum(raw_x.std(axis=0), 1e-12)
        y = all_y[:, context]
        for salt in (0, 1):
            idx = order(pairs, salt)
            query = idx[512:]
            for budget in (128, 512):
                support = idx[:budget]
                n_train = int(.8*budget)
                train, valid = support[:n_train], support[n_train:]
                choices, elapsed = {}, time.perf_counter()
                calls = []
                prefix = f'{name}_{salt}_{budget}'
                arrays[prefix+'_support'] = support
                arrays[prefix+'_inner_train'] = train
                arrays[prefix+'_inner_valid'] = valid
                arrays[prefix+'_query'] = query
                arrays[prefix+'_truth'] = y[query]

                def evaluate(spec, response, fitting, predicting, stage):
                    begin = time.perf_counter()
                    prediction = fit_predict(spec, x, z, response, fitting, predicting)
                    kind = spec[0]
                    calls.append(dict(spec=spec, stage=stage, seconds=time.perf_counter()-begin,
                                      estimator_fits=2 if kind == 'residual' else int(kind in (
                                          'ridge', 'trees', 'joint', 'calibration')),
                                      linear_solves=int(kind in ('rbf', 'jointkernel'))))
                    return prediction

                validation = []
                for family, grid in [('score_direct', SCORE), ('identity_ordinary', IDENTITY)]:
                    results = []
                    for spec in grid:
                        pred = evaluate(spec, y, train, valid, 'validation')
                        loss = float(np.mean((pred-y[valid])**2))
                        results.append((loss, spec))
                        validation.append(dict(family=family, spec=spec, mse=loss))
                    choices[family] = min(results, key=lambda item: item[0])[1]
                outcomes = {}
                for label, spec in [('source_mean', ('mean', None)),
                                    ('support_mean', ('targetmean', None)),
                                    ('calibration', ('calibration', None)), *choices.items()]:
                    # The source mean is computed in original score units below.
                    if label == 'source_mean':
                        pred = raw_x[query].mean(axis=1)
                    elif label == 'calibration':
                        begin = time.perf_counter()
                        pred = fit_predict(spec, raw_x, z, y, support, query)
                        calls.append(dict(spec=spec, stage='final', seconds=time.perf_counter()-begin,
                                          estimator_fits=1, linear_solves=0))
                    else:
                        pred = evaluate(spec, y, support, query, 'final')
                    outcomes[label] = metrics(pred, y[query])
                    arrays[prefix+'_'+label] = pred
                shuffled = y.copy()
                shuffled[support] = np.random.default_rng(314159).permutation(y[support])
                pred = evaluate(choices['identity_ordinary'], shuffled, support, query, 'negative_control')
                outcomes['identity_permuted_labels'] = metrics(pred, y[query])
                arrays[prefix+'_identity_permuted_labels'] = pred
                coverage = np.any(z[support] != 0, axis=0)
                record = dict(context=name, salt=salt, budget=budget, query_n=len(query),
                              support_hash=hashlib.sha256(support.tobytes()).hexdigest(),
                              query_hash=hashlib.sha256(query.tobytes()).hexdigest(),
                              endpoint_unseen_fraction=float(np.mean((z[query][:, ~coverage].sum(axis=1)) > 0)),
                              chosen=choices, validation=validation, metrics=outcomes,
                              pipeline_calls=len(calls), calls=calls,
                              estimator_fits=sum(c['estimator_fits'] for c in calls),
                              kernel_linear_solves=sum(c['linear_solves'] for c in calls),
                              seconds=time.perf_counter()-elapsed)
                records.append(record)
                print(json.dumps({k: record[k] for k in ('context', 'salt', 'budget', 'seconds', 'chosen')}), flush=True)
    aggregate = []
    for budget in (128, 512):
        per_context = []
        for name in DEV:
            rows = [r for r in records if r['context'] == name and r['budget'] == budget]
            comparison = {}
            for metric in ('mse', 'bottom20_regret'):
                comparison[metric] = {method: float(np.mean([r['metrics'][method][metric] for r in rows]))
                                      for method in rows[0]['metrics']}
            win = all(comparison[m]['identity_ordinary'] < comparison[m]['score_direct']
                      for m in ('mse', 'bottom20_regret'))
            per_context.append(dict(context=name, joint_win=win, comparison=comparison))
        aggregate.append(dict(budget=budget, joint_wins=sum(r['joint_win'] for r in per_context), contexts=per_context))
    np.savez_compressed(OUT/'PREDICTIONS.npz', **arrays)
    report = dict(utc=datetime.now(timezone.utc).isoformat(), data=metadata, records=records,
                  aggregate=aggregate, screening_gate=all(a['joint_wins'] >= 4 for a in aggregate),
                  total_seconds=time.perf_counter()-started,
                  environment=dict(python=platform.python_version(), numpy=np.__version__,
                                   scipy=scipy.__version__, sklearn=sklearn.__version__),
                  git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  code_sha256=digest(Path(__file__)),
                  prediction_sha256=digest(OUT/'PREDICTIONS.npz'), pair_ids_sha256=digest(OUT/'PAIR_IDS.json'),
                  plan_sha256=digest(OUT/'PLAN.md'), amendment_sha256=digest(OUT/'AMENDMENT_BEFORE_VALUES.md'),
                  scope='Exploratory completed-screen GI transport; ordinary models, no wet savings, no RSI')
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(dict(data=metadata, screening_gate=report['screening_gate'],
                         joint_wins=[a['joint_wins'] for a in aggregate], total_seconds=report['total_seconds'])))


if __name__ == '__main__':
    with threadpool_limits(limits=1):
        main()
