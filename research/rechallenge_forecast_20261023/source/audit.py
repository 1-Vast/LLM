"""Independent Decimal reconstruction; never imports the forecast module."""
from decimal import Decimal, getcontext
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as X
import zipfile

getcontext().prec = 50
ROOT = Path(__file__).resolve().parents[3]
LOG = ROOT / 'log/20261023/rechallenge_forecast'
OUT = LOG / 'source'
D = Decimal
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def avg(v):
    return sum(v) / D(len(v))


def ols(xs, ys, qs):
    a, b = avg(xs), avg(ys)
    ss = sum((x-a)**2 for x in xs)
    slope = sum((x-a)*(y-b) for x, y in zip(xs, ys))/ss if ss else D(0)
    return [b+slope*(q-a) for q in qs]


def raw(n):
    path = ROOT / f'log/20261023/rechallenge_task/root/transition_exp{n}.body'
    curves = {}
    with zipfile.ZipFile(path) as z:
        rels = {v.get('Id'): v.get('Target') for v in X.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        for sh in X.fromstring(z.read('xl/workbook.xml')).find(NS+'sheets'):
            name = sh.get('name')
            if name not in ('AAAA', 'ANAN'):
                continue
            member = rels[sh.get(R)]
            member = member.lstrip('/') if member.startswith('/') else 'xl/'+member
            obs = {}
            for row in X.fromstring(z.read(member)).find(NS+'sheetData'):
                if int(row.get('r')) < 4:
                    continue
                pair = {}
                for c in row:
                    col = ''.join(x for x in c.get('r') if x.isalpha())
                    if col in ('A', 'B'):
                        assert c.find(NS+'f') is None and c.get('t', 'n') == 'n'
                        pair[col] = D(c.find(NS+'v').text)
                if not pair:
                    continue
                assert set(pair) == {'A', 'B'} and pair['A'] not in obs
                assert all(x.is_finite() for x in pair.values())
                obs[pair['A']] = pair['B']
            assert set(obs) == set(map(D, (0, 24, 48, 72, 96)))
            curves[name] = [obs[D(t)] for t in (0, 24, 48, 72, 96)]
    assert set(curves) == {'AAAA', 'ANAN'}
    return curves


def rates(curves):
    events = {'A': [], 'N': []}
    for r, vals in curves.items():
        for i in range(len(vals)-1):
            events[r[i]].append(vals[i+1]-vals[i])
    return events


def predictions(s, y):
    sr, tr = rates(s), rates(y)
    out = {}
    for r in ('AAAA', 'ANAN'):
        sv, tv = s[r], y[r]
        res = [tv[i]-sv[i] for i in range(3)]
        trend = ols(list(map(D, (0, 1, 2))), res, list(map(D, (3, 4))))
        m = {
            'persistence': [tv[2]]*2,
            'target_linear': ols(list(map(D, (0, 1, 2))), tv, list(map(D, (3, 4)))),
            'target_last_interval': [tv[2]+D(h)*(tv[2]-tv[1]) for h in (1, 2)],
            'source_curve': sv[3:],
            'source_offset': [x+avg(res) for x in sv[3:]],
            'source_affine': ols(sv[:3], tv, sv[3:]),
            'source_residual_trend': [x+t for x, t in zip(sv[3:], trend)],
        }
        for name, use_target in [('source_event', False), ('pooled_event_refit', True)]:
            fitted = {a: avg(sr[a]+(tr[a] if use_target else [])) for a in sr}
            now = tv[2]
            m[name] = []
            for action in r[2:]:
                now += fitted[action]
                m[name].append(now)
        out[r] = m
    return out


if __name__ == '__main__':
    checks = []
    def compare(label, expected, actual):
        difference = abs(expected-D(str(actual)))
        tolerance = D('1e-10') * max(D(1), abs(expected))
        assert difference <= tolerance, (label, str(expected), actual)
        checks.append((label, difference))

    freeze = json.loads((LOG/'FREEZE.json').read_text(encoding='utf-8'))
    for name, h in freeze['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == h
    forecasts = json.loads((LOG/'pilot/FORECASTS.json').read_text())
    seal = json.loads((LOG/'pilot/FORECAST_SEAL.json').read_text())
    assert seal['sha256'] == hashlib.sha256((LOG/'pilot/FORECASTS.json').read_bytes()).hexdigest()
    result = json.loads((LOG/'pilot/RESULT.json').read_text())
    data = {n: raw(n) for n in (3, 4)}
    summaries = {}
    groups = []
    for source, target in ((3, 4), (4, 3)):
        prefix = {r: v[:3] for r, v in data[target].items()}
        rec = next(f for f in forecasts if f['target'] == target)
        for r in data[source]:
            for i, v in enumerate(data[source][r]):
                compare(f'raw/source/{source}/{r}/{i}', v, rec['source_values'][r][i])
            for i, v in enumerate(prefix[r]):
                compare(f'raw/prefix/{target}/{r}/{i}', v, rec['target_prefix'][r][i])
        pred = predictions(data[source], prefix)
        for r, methods in pred.items():
            scored = next(g for g in result['scored'] if g['target'] == target and g['regimen'] == r)
            errors = {}
            for i, value in enumerate(data[target][r][3:]):
                compare(f'truth/{target}/{r}/{i}', value, scored['truth'][i])
            for method, values in methods.items():
                signed = [p-t for p, t in zip(values, data[target][r][3:])]
                squared, absolute = [x*x for x in signed], [abs(x) for x in signed]
                metric = {'signed': signed, 'squared': squared, 'absolute': absolute,
                          'mse': avg(squared), 'mae': avg(absolute)}
                for i, value in enumerate(values):
                    compare(f'prediction/{target}/{r}/{method}/{i}', value, rec['predictions'][r][method][i])
                for key, value in metric.items():
                    if isinstance(value, list):
                        for i, v in enumerate(value):
                            compare(f'error/{target}/{r}/{method}/{key}/{i}', v, scored['errors'][method][key][i])
                    else:
                        compare(f'metric/{target}/{r}/{method}/{key}', value, scored['errors'][method][key])
                errors[method] = metric
                summaries.setdefault(method, {'mse': [], 'mae': []})
                for k in ('mse', 'mae'):
                    summaries[method][k].append(metric[k])
            passed = all(errors['pooled_event_refit']['mse'] < errors[m]['mse'] for m in ('source_event', 'persistence'))
            groups.append({'target': target, 'regimen': r, 'gate': passed,
                           'mse': {m: str(e['mse']) for m, e in errors.items()},
                           'pooled_forecasts': list(map(str, methods['pooled_event_refit']))})
    summary = {m: {k: avg(v) for k, v in metrics.items()} for m, metrics in summaries.items()}
    for m in summary:
        for k, v in summary[m].items():
            compare('summary/'+m+'/'+k, v, result['summary'][m][k])
    assert result['descriptive_gate'] == all(g['gate'] for g in groups)
    assert result['decision'] == 'STOP_THIS_FIXED_POOLED_EVENT_UPDATE_CONFIGURATION'
    audit = {'status': 'PASS_ARITHMETIC_AUDIT_NOT_SCIENTIFIC_GATE', 'comparisons': len(checks),
             'max_absolute_difference': str(max(d for _, d in checks)),
             'raw_values': {str(n): {r: list(map(str,v)) for r,v in curves.items()} for n,curves in data.items()},
             'raw_response_count': sum(len(v) for c in data.values() for v in c.values()),
             'groups': groups, 'summary': {m:{k:str(v) for k,v in q.items()} for m,q in summary.items()},
             'shared_prefix_numeric_equality': {str(n): data[n]['AAAA'][:2] == data[n]['ANAN'][:2] for n in data},
             'scope': 'Independent raw OOXML and Decimal formulas; no main import, hypothesis revision or rescue.'}
    path = OUT/'RESULT_AUDIT.json'
    assert not path.exists()
    path.write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print(json.dumps(audit, indent=2))
