"""Frozen exploratory prefix forecasts; no author code execution or future fitting."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
from zipfile import ZipFile

import numpy as np
import scipy
from scipy.optimize import least_squares
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/vuscope_prefix_diagnostic'
ARCHIVE = ROOT / 'log/20261023/functional_transition_law/root_sources/release.zip.body'
METHODS = ('vuscope6', 'moving_midpoint7', 'independent_logistic', 'direct_selected', 'persistence')


def logistic(t, k, loga):
    a = np.exp(loga)
    power = np.exp2(k * t)
    return a * power / (a - 1 + power)


def surface(p, dose, t, moving=False):
    ka, la, beta, gamma, kd, ld = p[:6]
    upper, lower = logistic(t, ka, la), logistic(t, kd, ld)
    midpoint = gamma + (p[6] * t / 2.75 if moving else 0)
    return lower + (upper - lower) * expit(-np.log(10) * beta * np.abs(upper-lower) * (dose-midpoint))


def fit_surface(doses, hours, y, forecast_hours, moving):
    t = (hours - 6) / 24
    te = (forecast_hours - 6) / 24
    z = np.log10(doses)
    zz, tt = np.meshgrid(z, t)
    zf, tf = np.meshgrid(z, te)
    bounds = ([0, np.log(1e-6), 0, z.min(), 0, np.log(1e-6)],
              [2, np.log(1e6), 1e3, z.max(), 2, np.log(1e6)])
    if moving:
        bounds[0].append(-np.ptp(z))
        bounds[1].append(np.ptp(z))
    best = None
    records = []
    for beta in (.1, 1., 10.):
        for gamma in (z.min(), np.median(z), z.max()):
            p = [1, np.log(100), beta, gamma, .5, np.log(10)] + ([0] if moving else [])
            result = least_squares(lambda q: (surface(q, zz, tt, moving)-y).ravel(),
                                   p, bounds=bounds, max_nfev=400)
            loss = float(np.mean(result.fun**2))
            records.append(dict(loss=loss, nfev=result.nfev, njev=result.njev,
                                status=result.status, params=result.x.tolist()))
            if best is None or loss < best[0]:
                best = (loss, result.x)
    return surface(best[1], zf, tf, moving), dict(starts=records, params=best[1].tolist())


def fit_independent(hours, y, forecast_hours):
    t, te = (hours-6)/24, (forecast_hours-6)/24
    predictions, records = [], []
    for column in y.T:
        attempts = []
        for k, a in ((1, 100), (.5, 10), (1, .5)):
            fit = least_squares(lambda q: logistic(t, *q)-column, [k, np.log(a)],
                                bounds=([0, np.log(1e-6)], [2, np.log(1e6)]), max_nfev=400)
            attempts.append(dict(loss=float(np.mean(fit.fun**2)), params=fit.x.tolist(),
                                 nfev=fit.nfev, njev=fit.njev, status=fit.status))
        best = min(attempts, key=lambda a: a['loss'])
        predictions.append(logistic(te, *best['params']))
        records.append(attempts)
    return np.array(predictions).T, dict(doses=records)


DIRECT = [(degree, ridge) for degree in (1, 2) for ridge in (1e-6, .01, .1)] + [('loglocal', 24), ('loglocal', 48)]


def direct_predict(config, hours, y, forecast_hours):
    degree, option = config
    if degree == 'loglocal':
        selected = hours >= hours.max()-option
        design = np.column_stack([np.ones(selected.sum()), (hours[selected]-6)/72])
        coef = np.linalg.lstsq(design, np.log1p(y[selected]), rcond=None)[0]
        pred = np.expm1(np.column_stack([np.ones(len(forecast_hours)), (forecast_hours-6)/72]) @ coef)
    else:
        design = np.vander((hours-6)/72, N=degree+1, increasing=True)
        penalty = np.diag([0] + [option]*degree)
        coef = np.linalg.solve(design.T@design + penalty, design.T@y)
        pred = np.vander((forecast_hours-6)/72, N=degree+1, increasing=True)@coef
    return np.maximum(pred, 0)


def fit_direct(hours, y, forecast_hours):
    train, validation = hours <= 48, hours > 48
    losses = [float(np.mean((direct_predict(c, hours[train], y[train], hours[validation])-y[validation])**2)) for c in DIRECT]
    winner = int(np.argmin(losses))
    return direct_predict(DIRECT[winner], hours, y, forecast_hours), dict(configs=DIRECT, validation_losses=losses, selected=winner)


def read_rows(archive, member, requested):
    with archive.open(member) as stream:
        for raw in stream:
            fields = raw.decode('utf-8-sig').strip().split('\t')
            if 'Elapsed' in fields:
                columns = fields[2:]
                assert len(columns) == len(set(columns)), 'Duplicate well header'
                break
        rows = {}
        for raw in stream:
            fields = raw.decode('utf-8-sig').strip().split('\t')
            if len(fields) < 2:
                continue
            hour = float(fields[1])
            if hour in requested:
                assert hour not in rows and len(fields[2:]) == len(columns)
                rows[hour] = {well: float(value) for well, value in zip(columns, fields[2:])}
    assert set(rows) == set(requested), 'Missing requested time'
    return rows


def assess_gate(metrics, summary):
    moving, fixed = summary['moving_midpoint7'], summary['vuscope6']
    cell_wins = [cell for cell in fixed['cells']
                 if all(moving['cells'][cell][field] < fixed['cells'][cell][field]
                        for field in ('mse120', 'mse_late'))]
    paired = {row['key']: row['mse120'] for row in metrics if row['method']=='vuscope6'}
    wins = sum(row['mse120'] < paired[row['key']] for row in metrics if row['method']=='moving_midpoint7')
    ordinary_wins = all(moving[field] < summary[method][field]
                        for method in ('independent_logistic','direct_selected')
                        for field in ('mse120','mse_late'))
    passed = len(cell_wins) >= 3 and wins > len(paired)/2 and ordinary_wins
    return dict(cell_wins_both=cell_wins, curve_wins_primary=wins, curves=len(paired),
                beats_both_ordinary_on_both=ordinary_wins,
                decision='RETAIN_FOR_SEPARATE_REVIEW_ONLY' if passed else 'STOP_THIS_MOVING_MIDPOINT_CONFIGURATION',
                boundary='Finite-panel directional screen, not application, algorithm, world, agent, inheritance or RSI validation')


if __name__ == '__main__':
    started = time.perf_counter()
    freeze = json.loads((OUT/'FREEZE.json').read_text())
    for name, expected in freeze['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected
    run = OUT/'pilot'
    run.mkdir(exist_ok=False)
    schedule = json.loads((OUT/'SCHEDULE.json').read_text())
    forecast_hours = np.arange(75, 121, 3, dtype=float)
    prefix_hours = np.arange(6, 73, 3, dtype=float)
    fits, package, exclusions = [], {}, []
    with ZipFile(ARCHIVE) as archive:
        for member, info in schedule['files'].items():
            cell = Path(member).name.split('_')[0]
            rows = read_rows(archive, member, set(prefix_hours))
            for label, entries in sorted(info['groups'].items()):
                entries = sorted(entries, key=lambda e: e['dose'])
                assert len(entries) == 6 and len(set(e['dose'] for e in entries)) == 6
                wells = [e['well'] for e in entries]
                raw = np.array([[rows[h][w] for w in wells] for h in prefix_hours])
                key = cell+'__'+label
                if not np.isfinite(raw).all() or (raw < 0).any() or (raw[0] <= 0).any():
                    exclusions.append(dict(key=key, reason='invalid prefix or nonpositive6h denominator'))
                    continue
                y = raw/raw[0]
                doses = np.array([e['dose'] for e in entries])
                package[key] = dict(member=member, cell=cell, label=label, wells=wells,
                                    doses=doses.tolist(), baseline=raw[0].tolist())
                for method in METHODS:
                    tick = time.perf_counter()
                    if method in ('vuscope6', 'moving_midpoint7'):
                        pred, record = fit_surface(doses, prefix_hours, y, forecast_hours, method == 'moving_midpoint7')
                    elif method == 'independent_logistic':
                        pred, record = fit_independent(prefix_hours, y, forecast_hours)
                    elif method == 'direct_selected':
                        pred, record = fit_direct(prefix_hours, y, forecast_hours)
                    else:
                        pred, record = np.tile(y[-1], (len(forecast_hours), 1)), {}
                    assert np.isfinite(pred).all() and (pred >= 0).all()
                    package[key][method] = pred.tolist()
                    fits.append(dict(key=key, method=method, seconds=time.perf_counter()-tick, **record))
            print(json.dumps(dict(cell=cell, complete_groups=sum(v['cell']==cell for v in package.values()))), flush=True)
        assert set(v['cell'] for v in package.values()) == {'LN229','LN308','T98G','UW228-3'}
        (run/'PREFIX_ELIGIBILITY.json').write_text(json.dumps(dict(eligible=list(package), exclusions=exclusions), indent=2), encoding='utf-8')
        (run/'PREFIX_FITS.json').write_text(json.dumps(fits, indent=2), encoding='utf-8')
        (run/'PREDICTIONS_BEFORE_OUTCOMES.json').write_text(json.dumps(package), encoding='utf-8')
        prediction_hash = hashlib.sha256((run/'PREDICTIONS_BEFORE_OUTCOMES.json').read_bytes()).hexdigest()
        (run/'PREDICTION_SEAL.json').write_text(json.dumps(dict(sha256=prediction_hash, utc=datetime.now(timezone.utc).isoformat())), encoding='utf-8')
        metrics, outcomes = [], {}
        for member in schedule['files']:
            rows = read_rows(archive, member, set(forecast_hours))
            for key, entry in package.items():
                if entry['member'] != member:
                    continue
                raw = np.array([[rows[h][w] for w in entry['wells']] for h in forecast_hours])
                assert np.isfinite(raw).all() and (raw >= 0).all(), 'Invalid late outcomes: stop, no posthoc exclusion'
                truth = raw/np.array(entry['baseline'])
                outcomes[key] = raw.tolist()
                for method in METHODS:
                    delta = np.array(entry[method])-truth
                    metrics.append(dict(key=key, cell=entry['cell'], label=entry['label'], method=method,
                                        mse120=float(np.mean(delta[-1]**2)), mse_late=float(np.mean(delta**2)),
                                        mae120=float(np.mean(abs(delta[-1]))),
                                        raw_mse120=float(np.mean((delta[-1]*entry['baseline'])**2))))
    summary = {}
    for method in METHODS:
        selected = [m for m in metrics if m['method']==method]
        summary[method] = dict(groups=len(selected), **{field:float(np.mean([m[field] for m in selected])) for field in ('mse120', 'mse_late', 'mae120', 'raw_mse120')},
                              cells={cell:{field:float(np.mean([m[field] for m in selected if m['cell']==cell])) for field in ('mse120','mse_late')} for cell in sorted(set(m['cell'] for m in selected))})
    (run/'OUTCOMES.json').write_text(json.dumps(outcomes), encoding='utf-8')
    (run/'METRICS.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    (run/'SUMMARY.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    gate = assess_gate(metrics, summary)
    (run/'GATE.json').write_text(json.dumps(gate, indent=2), encoding='utf-8')
    receipt = dict(utc=datetime.now(timezone.utc).isoformat(), seconds=time.perf_counter()-started,
                   git=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                   python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                   groups=len(package), methods=list(METHODS), exclusions=exclusions,
                   forecast_hours=forecast_hours.tolist(), prefix_hours=prefix_hours.tolist(),
                   seed='deterministic, no random initialization', new_http=0, new_api=0,
                   boundary='Exploratory same-well temporal holdout; no independent biological replication or drug identity claims')
    (run/'RUN_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(dict(summary=summary, gate=gate, receipt=receipt), indent=2))
