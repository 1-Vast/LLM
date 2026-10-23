"""One frozen, scale-invariant exploratory allocation gate; no new method."""
from itertools import combinations
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

import numeric_identity as identity
import source_schema as source

OUT = source.OUT / 'rank_pilot'
RAW = source.OUT / 'redirect_followup/pbio.3002970.s001.raw.xlsx'
EXPECTED = '273cc82c826f245be228a7fd21673fca13eaee1b949183f3b179b86bbce1fb27'
SALT = 'efaecalis-rank-gate-v1'
METHODS = ['ridge6', 'day6', 'ridge1', 'prefix_mean', 'knn3', 'calendar']
COMPARATORS = ['day6', 'ridge1']


def digest_id(kind, ident):
    return hashlib.sha256(f'{SALT}|{kind}|{int(ident)}'.encode()).hexdigest()


def split_ids():
    ids = sorted(range(1, 21), key=lambda i: digest_id('split', i))
    return ids[:10], ids[10:]


def ranks(values):
    """Percentiles along the final axis; ties are observed empirical mass."""
    values = np.asarray(values, dtype=float)
    if not np.isfinite(values).all() or values.shape[-1] == 0:
        raise ValueError('rank_input_invalid')
    other = values[..., None, :]
    own = values[..., :, None]
    return (np.sum(other < own, axis=-1) + .5*np.sum(other == own, axis=-1))/values.shape[-1]


def ridge(train_x, train_y, test_x):
    mean_x, mean_y = train_x.mean(axis=0), train_y.mean()
    centered = train_x - mean_x
    coef = np.linalg.solve(centered.T@centered + np.eye(train_x.shape[1]), centered.T@(train_y-mean_y))
    return (test_x-mean_x)@coef + mean_y


def predict(prefix, dev_future, dev_ids, test_ids):
    """Test futures are absent from this interface."""
    dev_idx, test_idx = np.array(dev_ids)-1, np.array(test_ids)-1
    train_x = ranks(prefix[:, dev_idx]).T
    test_x = ranks(prefix[:, test_idx]).T
    target = ranks(dev_future).mean(axis=0)
    near = []
    for row in test_x:
        distances = np.sum((train_x-row)**2, axis=1)
        order = sorted(range(len(dev_ids)), key=lambda j: (distances[j], digest_id('tie', dev_ids[j])))
        near.append(float(target[order[:3]].mean()))
    return {'ridge6': ridge(train_x, target, test_x), 'day6': test_x[:, -1],
            'ridge1': ridge(train_x[:, -1:], target, test_x[:, -1:]),
            'prefix_mean': test_x.mean(axis=1), 'knn3': np.array(near),
            'calendar': np.full(len(test_ids), .5)}


def roster(pred, ids):
    return sorted(range(len(ids)), key=lambda j: (float(pred[j]), digest_id('tie', ids[j]), j))[:3]


def score(predictions, future, ids):
    quality = 1-ranks(future).mean(axis=0)
    selected = {m: roster(predictions[m], ids) for m in METHODS}
    utility = {m: float(quality[selected[m]].mean()) for m in METHODS}
    return utility, selected, quality


def sensitivity(predictions, future, ids, draws=10000):
    rng = np.random.default_rng(20261022)
    bootstrap = {m: [] for m in COMPARATORS}
    for _ in range(draws):
        idx = rng.integers(0, len(ids), len(ids))
        p = {m: predictions[m][idx] for m in METHODS}
        u, _, _ = score(p, future[:, idx], [ids[i] for i in idx])
        for m in COMPARATORS:
            bootstrap[m].append(u['ridge6']-u[m])
    deletion = []
    for removed in combinations(range(len(ids)), 2):
        idx = [i for i in range(len(ids)) if i not in removed]
        p = {m: predictions[m][idx] for m in METHODS}
        u, _, _ = score(p, future[:, idx], [ids[i] for i in idx])
        deletion.append({'removed_ids': [ids[i] for i in removed],
                         'differences': {m: u['ridge6']-u[m] for m in COMPARATORS}})
    return bootstrap, deletion


def response_allowlist():
    return {'Fig4B': {f'{identity.column(c)}{r}' for c in range(4, 24)
                      for r in [*range(35, 41), *range(42, 48)]}}


def read_responses(path):
    values = identity.read_allowed(path, response_allowlist())['Fig4B']
    prefix = np.array([[float(values[f'{identity.column(c)}{r}']) for c in range(4, 24)]
                       for r in range(35, 41)])
    future = np.array([[float(values[f'{identity.column(c)}{r}']) for c in range(4, 24)]
                       for r in range(42, 48)])
    if not np.isfinite(prefix).all() or not np.isfinite(future).all():
        raise ValueError('finite_decimal_overflows_float')
    return prefix, future, values


def freeze():
    if source.sha(RAW) != EXPECTED:
        raise ValueError('source_hash_mismatch')
    inputs = [OUT/'PROTOCOL.md', Path(__file__), Path(__file__).with_name('test_rank_pilot.py'),
              OUT/'SYNTHETIC_TESTS.json', RAW,
              Path(identity.__file__), Path(source.__file__),
              Path(__file__).with_name('redirect_followup.py'),
              OUT/'INDEPENDENT_CODE_REVIEW.md',
              source.OUT/'RANK_PILOT_INDEPENDENT_REVIEW.md',
              source.OUT/'numeric_identity/FINAL_CHECKS.json']
    source.write_json(OUT/'FREEZE.json', {
        'utc': source.utc(), 'runtime': sys.executable, 'development_ids': split_ids()[0],
        'test_ids': split_ids()[1], 'response_coordinates': sorted(response_allowlist()['Fig4B']),
        'files': [{'path': str(p), 'sha256': source.sha(p)} for p in inputs],
        'status': 'FROZEN_BEFORE_FINITE_RESPONSE_READ', 'http_requests': 0})


def main():
    try:
        if len(sys.argv) == 2 and sys.argv[1] == 'freeze':
            freeze()
            print('Frozen before response read.')
            return 0
        if len(sys.argv) != 2 or sys.argv[1] != 'run':
            raise ValueError('expected_freeze_or_run')
        if (OUT/'READ_STARTED.json').exists():
            raise ValueError('single_open_already_started')
        frozen = json.loads((OUT/'FREEZE.json').read_text(encoding='utf-8'))
        if any(source.sha(f['path']) != f['sha256'] for f in frozen['files']):
            raise ValueError('frozen_input_changed')
        source.write_json(OUT/'READ_STARTED.json', {'utc': source.utc(), 'coordinates': 240,
                          'http_requests': 0, 'source_sha256': source.sha(RAW)})
        wall_start, cpu_start = time.perf_counter(), time.process_time()
        prefix, future, values = read_responses(RAW)
        source.write_json(OUT/'OPENED_RESPONSES.json', {'sheet': 'Fig4B', 'values': values,
                          'days_prefix': list(range(1, 7)), 'days_future': list(range(8, 14)),
                          'ids_in_source_column_order': list(range(1, 21)), 'source_sha256': source.sha(RAW)})
        dev, test = split_ids()
        predictions = predict(prefix, future[:, np.array(dev)-1], dev, test)
        test_future = future[:, np.array(test)-1]
        utility, selected, quality = score(predictions, test_future, test)
        boot, deletion = sensitivity(predictions, test_future, test)
        differences = {m: utility['ridge6']-utility[m] for m in COMPARATORS}
        intervals = {m: np.quantile(boot[m], [.025, .5, .975]).tolist() for m in COMPARATORS}
        passed = all(differences[m] >= .10 and intervals[m][0] > 0 for m in COMPARATORS)
        checks = [{'path': f['path'], 'unchanged': source.sha(f['path']) == f['sha256']}
                  for f in frozen['files']]
        if not all(c['unchanged'] for c in checks):
            raise ValueError('frozen_input_changed_after_run')
        source.write_json(OUT/'SENSITIVITY.json', {'bootstrap_paired_differences': boot,
                          'delete_two': deletion, 'fixed_fit': True, 'nominal_CI_claim': False})
        result = {'utc': source.utc(), 'runtime': sys.executable, 'http_requests': 0,
                  'status': 'PASS_TO_ONE_NARROW_ALLOCATION_FOLLOWUP' if passed else
                            'STOP_THIS_SOURCE_CONFIGURATION_FOR_FRAMEWORK_EXPANSION',
                  'development_ids': dev, 'test_ids': test, 'utilities': utility,
                  'selected_ids': {m: [test[i] for i in selected[m]] for m in METHODS},
                  'predictions': {m: predictions[m].tolist() for m in METHODS},
                  'test_future_relative_rank_quality': quality.tolist(),
                  'primary_differences': differences, 'bootstrap_sensitivity_quantiles': intervals,
                  'delete_two_difference_ranges': {m: [min(d['differences'][m] for d in deletion),
                      max(d['differences'][m] for d in deletion)] for m in COMPARATORS},
                  'response_census': {'plain_finite_numeric': 240, 'excluded': 0, 'imputed': 0},
                  'budget': {'development_prefix': 60, 'development_future': 60, 'test_prefix': 60,
                             'test_future_evaluation': 60, 'future_verification_slots_per_arm': 18},
                  'execution_resources': {'wall_seconds': time.perf_counter()-wall_start,
                      'process_cpu_seconds': time.process_time()-cpu_start,
                      'ridge_fits': 2, 'hyperparameter_trials': 0, 'API_calls': 0,
                      'bootstrap_draws': 10000, 'delete_two_subsets': 45,
                      'scope': 'single root execution only; excludes prior source qualification and reviewer inference'},
                  'frozen_checks': checks,
                  'claims': {'world_model': 'NOT_TESTED', 'agent': 'NOT_TESTED',
                             'inheritance': 'NOT_TESTED', 'RSI': 'NOT_TESTED', 'novel_algorithm': False}}
        source.write_json(OUT/'RESULT.json', result)
        print(json.dumps({k: result[k] for k in ['status', 'utilities', 'primary_differences',
                         'bootstrap_sensitivity_quantiles', 'delete_two_difference_ranges']}))
        return 0
    except Exception as error:
        failure = {'utc': source.utc(), 'status': 'STOP_EXECUTION_FAILURE',
                   'error_type': type(error).__name__, 'http_requests': 0,
                   'reason': str(error) if isinstance(error, (ValueError, identity.Failure)) else 'inspect_trace_locally'}
        path = OUT/'FAILURE.json'
        if not path.exists():
            source.write_json(path, failure)
        print(json.dumps(failure))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
