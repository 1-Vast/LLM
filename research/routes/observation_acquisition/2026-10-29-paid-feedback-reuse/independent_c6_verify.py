"""Independent C6 replay. Real data requires explicit --run-authorized.

No import of the author replay, no training, and no automatic rerun after receipt.
--synthetic-only opens no frozen artifacts or source CSV.
--compare-only opens only already persisted replay arrays and summaries.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

import argparse
import csv
import ctypes
import hashlib
import json
from pathlib import Path
import time
import traceback

import numpy as np
from scipy.special import ndtr

HERE = Path(__file__).resolve().parent
FROZEN = Path(r'D:\MAESTRO\research\2026-10-29-common-functional-transfer')
ARMS = ['rank8', 'static_global13', 'static_tissue13', 'matched_blind',
        'random13', 'rank1', 'knn5']
EXPECTED = {
    'metadata_freeze.json': 'a86a320aa7bb471cdec43f0e13e626db39bf1bc8e38bc978a6d74636e7cbdc77',
    'training_freeze.json': '3d4cd7542fc02772e1bb0fe81dae4e6bb234aff3244d3ee81ef16ba662965003',
    'training_model.npz': '221f52890cb4f6b45a037680d3eee166a9196e407cb323aa5a4f896bf240489e',
    'candidate_c6_v1.md': '7d2c92f75473b6613fa328e22df685a5f8f4427be23ade704843b51abb11d765',
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def check_budget(start):
    if time.process_time() - start > 600:
        raise RuntimeError('Independent CPU budget exceeded 600 seconds')
    if os.name == 'nt':
        class Counters(ctypes.Structure):
            _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong)] + [
                (n, ctypes.c_size_t) for n in ('PeakWorkingSetSize', 'WorkingSetSize',
                'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
        c = Counters()
        c.cb = ctypes.sizeof(c)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        psapi = ctypes.WinDLL('psapi', use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        if max(c.PeakWorkingSetSize, c.PeakPagefileUsage) > 2 * 1024 ** 3:
            raise RuntimeError('Independent memory budget exceeded 2 GiB')


def order(scores, exclude=()):
    allowed = np.ones(len(scores), dtype=bool)
    allowed[list(exclude)] = False
    ix = np.flatnonzero(allowed)
    return ix[np.argsort(-np.asarray(scores)[ix], kind='stable')]


def posterior(a, mean, cov, variance, indices, response):
    """Full-history Gaussian precision solve; no sequential update code reuse."""
    keep = np.isfinite(response)
    if not np.any(keep):
        return mean.copy(), cov.copy()
    ix = np.asarray(indices)[keep]
    design = a[ix]
    precision0 = np.linalg.solve(cov, np.eye(len(mean)))
    precision = precision0 + design.T @ (design / variance[ix, None])
    rhs = precision0 @ mean + design.T @ (np.asarray(response)[keep] / variance[ix])
    updated_cov = np.linalg.solve(precision, np.eye(len(mean)))
    return np.linalg.solve(precision, rhs), updated_cov


def probabilities(a, mean, cov, noise, mu, sd, low, high):
    loc = a @ mean
    scale = np.sqrt(np.einsum('ij,jk,ik->i', a, cov, a) + noise)
    lower = (mu - np.minimum(high, 0.0)) / sd
    upper = (mu - low) / sd
    prob = ndtr((upper - loc) / scale) - ndtr((lower - loc) / scale)
    return np.where(upper > lower, np.clip(prob, 0, 1), 0.0)


def event_labels(y, low, high):
    # Endpoint convention inherited from C4, confirmed before real replay.
    return np.isfinite(y) & (y > low + 1e-8) & (y < high - 1e-8) & (y <= 0.0)


def knn_prediction(model, ix, response):
    usable = np.isfinite(response)
    if not np.any(usable):
        return model['global_rate'].copy()
    distance = np.mean((model['s'][:, np.asarray(ix)[usable]] - response[usable]) ** 2, axis=1)
    nearest = np.argsort(distance, kind='stable')[:5]
    weights = 1 / (distance[nearest] + 0.1)
    known = model['finite'][nearest]
    denominator = np.sum(weights[:, None] * known, axis=0)
    numerator = np.sum(weights[:, None] * model['event'][nearest], axis=0)
    answer = model['global_rate'].copy()
    np.divide(numerator, denominator, out=answer, where=denominator > 0)
    return answer


def paired_bounds(left, right, events, finite):
    # Shared unknown entries cancel before constructing each extremal difference.
    left_only = np.setdiff1d(left, right)
    right_only = np.setdiff1d(right, left)
    known = int(events[left_only].sum()) - int(events[right_only].sum())
    return [known - int((~finite[right_only]).sum()),
            known + int((~finite[left_only]).sum())]


def retain_record(chosen, key, rank, raw_ln):
    if key not in chosen or rank < chosen[key][0]:
        chosen[key] = (rank, raw_ln)


def build_raw_index(path, ids, menu):
    targets = {(d['drug_id'], d['min_conc_raw'], d['max_conc_raw']): j
               for j, d in enumerate(menu)}
    cell_index = {v: i for i, v in enumerate(ids)}
    chosen = {}
    duplicate_count = 0
    with path.open('r', encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        required = {'DATASET', 'SANGER_MODEL_ID', 'DRUG_ID', 'MIN_CONC', 'MAX_CONC',
                    'NLME_RESULT_ID', 'LN_IC50'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('CSV required columns absent')
        for row_number, row in enumerate(reader, start=2):
            if row['DATASET'] != 'GDSC2' or row['SANGER_MODEL_ID'] not in cell_index:
                continue
            j = targets.get((row['DRUG_ID'], row['MIN_CONC'], row['MAX_CONC']))
            if j is None:
                continue
            key = (cell_index[row['SANGER_MODEL_ID']], j)
            rank = (int(row['NLME_RESULT_ID']), row_number)
            if key in chosen:
                duplicate_count += 1
            retain_record(chosen, key, rank, row['LN_IC50'])
    return chosen, duplicate_count


class DecisionOracle:
    def __init__(self, raw, first6):
        self.raw, self.first6 = raw, first6
        self.requests = []

    def feedback(self, cell, indices):
        if not np.array_equal(indices, self.first6[cell]):
            raise ValueError('Oracle request differs from frozen first6')
        result = [parse_ln(self.raw.get((cell, int(j)))) for j in indices]
        self.requests.append({'cell_index': int(cell), 'requested': 6,
                              'effective_finite': int(np.isfinite(result).sum()),
                              'unknown': int((~np.isfinite(result)).sum())})
        return np.asarray(result)


def parse_ln(record):
    if record is None or record[1].strip().lower() in ('', 'na', 'nan', 'null'):
        return np.nan
    value = float(record[1])
    return value if np.isfinite(value) else np.nan


def summarize(arrays):
    metrics, comparisons = {}, {}
    for j, name in enumerate(ARMS):
        h, u = arrays['hits'][:, j], arrays['unknown'][:, j]
        metrics[name] = {'candidate_count_lower': float(h.mean()),
                         'candidate_count_upper': float((h + u).mean()),
                         'mean_unknown_attempts': float(u.mean()), 'attempts_per_cell': 13}
    for j, name in enumerate(ARMS[1:]):
        bounds = arrays['paired_bounds'][:, j]
        ci = np.quantile(bounds[:, 0][arrays['bootstrap_indices']].mean(axis=1),
                         [0.025, 0.975], method='linear')
        comparisons[name] = {'mean_difference_lower': float(bounds[:, 0].mean()),
                             'mean_difference_upper': float(bounds[:, 1].mean()),
                             'difference_lower_bootstrap_ci95': ci.tolist(),
                             'passes_point_and_ci': bool(bounds[:, 0].mean() >= .5 and ci[0] > 0)}
    joint = all(comparisons[k]['passes_point_and_ci'] for k in
                ('static_global13', 'static_tissue13', 'matched_blind'))
    return {'strategy_order': ARMS, 'metrics': metrics, 'comparisons': comparisons,
            'joint': joint, 'mechanism_adjudication': 'not performed'}


def run_authorized():
    receipt = HERE / 'independent_receipt.json'
    if receipt.exists():
        raise RuntimeError('Independent receipt exists; automatic rerun prohibited')
    save_json(receipt, {'status': 'started', 'authorization': 'explicit --run-authorized',
                        'script_sha256': digest(Path(__file__))})
    start = time.process_time()
    arrays, exposure = {}, {'requests': [], 'development_role': 'model_unseen_exposed_development',
                            'development_previously_exposed': True, 'fresh_confirmation': False,
                            'numeric_columns_converted': ['LN_IC50'], 'network_calls': 0,
                            'installations': 0, 'training_parameter_refit': False}
    try:
        for filename, expected in EXPECTED.items():
            path = HERE / filename if filename == 'candidate_c6_v1.md' else FROZEN / filename
            if digest(path) != expected:
                raise ValueError('Frozen hash mismatch: ' + filename)
        metadata = json.loads((FROZEN / 'metadata_freeze.json').read_text(encoding='utf-8-sig'))
        freeze = json.loads((FROZEN / 'training_freeze.json').read_text(encoding='utf-8-sig'))
        train, dev, menu = freeze['train_ids'], freeze['test_ids'], freeze['menu']
        cells = {c['id']: c for c in metadata['cells']}
        assert len(train) == 566 and len(dev) == 243 and len(menu) == 64
        assert len(set(train + dev)) == 809 and 'probes' in freeze
        assert all(cells[v]['role'] == 'train' for v in train)
        assert all(cells[v]['role'] == 'model_unseen_exposed_development' for v in dev)
        with np.load(FROZEN / 'training_model.npz', allow_pickle=False) as z:
            keys = ('train_y', 'mu', 'sd', 'low', 'high', 's', 'finite', 'event', 'probes',
                    'global_rate', 'a1', 'm1', 'p1', 'noise1', 'a8', 'm8', 'p8', 'noise8')
            model = {k: z[k].copy() for k in keys}
        assert model['train_y'].shape == (566, 64)
        assert np.array_equal(model['probes'], freeze['probes'])
        assert np.allclose(model['s'], np.where(model['finite'],
                           (model['mu'] - model['train_y']) / model['sd'], 0), atol=0, rtol=0)
        assert np.array_equal(model['event'], event_labels(model['train_y'], model['low'], model['high']))
        source = Path(metadata['source'])
        if digest(source) != metadata['source_sha256'] or source.stat().st_size != metadata['source_bytes']:
            raise ValueError('Original CSV hash/size mismatch')
        args_probability = [model[k] for k in ('mu', 'sd', 'low', 'high')]
        prior = probabilities(model['a8'], model['m8'], model['p8'], model['noise8'], *args_probability)
        tissue_scores = {}
        for tissue in {cells[v]['tissue'] for v in dev}:
            rows = np.array([cells[v]['tissue'] == tissue for v in train])
            tissue_scores[tissue] = ((model['event'][rows].sum(axis=0) + 5 * model['global_rate']) /
                                    (model['finite'][rows].sum(axis=0) + 5))
        first6 = np.array([order(tissue_scores[cells[v]['tissue']])[:6] for v in dev])
        arrays['first6'] = first6
        arrays['development_ids'] = np.array(dev)
        arrays['strategy_order'] = np.array(ARMS)
        arrays['prior_probabilities'] = np.broadcast_to(prior, (243, 64)).copy()
        np.savez_compressed(HERE / 'independent_decision_plan.npz', **arrays)
        raw, duplicate_count = build_raw_index(source, dev, menu)
        exposure['duplicate_records_ignored'] = duplicate_count
        oracle = DecisionOracle(raw, first6)
        exposure['requests'] = oracle.requests
        actions = np.full((243, 7, 13), -1, dtype=np.int64)
        arrays['actions'] = actions
        for rank, dim in ((1, 2), (8, 9)):
            arrays[f'posterior_m{rank}'] = np.full((243, dim), np.nan)
            arrays[f'posterior_p{rank}'] = np.full((243, dim, dim), np.nan)
            arrays[f'post_probabilities{rank}'] = np.full((243, 64), np.nan)
        for i, sidm in enumerate(dev):
            check_budget(start)
            ix = first6[i]
            feedback = oracle.feedback(i, ix)
            response = (model['mu'][ix] - feedback) / model['sd'][ix]
            prob = {}
            for rank in (1, 8):
                m, p = posterior(model[f'a{rank}'], model[f'm{rank}'], model[f'p{rank}'],
                                 model[f'noise{rank}'], ix, response)
                prob[rank] = probabilities(model[f'a{rank}'], m, p, model[f'noise{rank}'], *args_probability)
                arrays[f'posterior_m{rank}'][i] = m
                arrays[f'posterior_p{rank}'][i] = p
                arrays[f'post_probabilities{rank}'][i] = prob[rank]
            tissue = tissue_scores[cells[sidm]['tissue']]
            actions[i, 0] = np.r_[ix, order(prob[8], ix)[:7]]
            actions[i, 1] = order(model['global_rate'])[:13]
            actions[i, 2] = order(tissue)[:13]
            actions[i, 3] = np.r_[ix, order(prior, ix)[:7]]
            actions[i, 4] = sorted(range(64), key=lambda j:
                hashlib.sha256(f"C6-random|{sidm}|{menu[j]['id']}".encode()).hexdigest())[:13]
            actions[i, 5] = np.r_[ix, order(prob[1], ix)[:7]]
            actions[i, 6] = np.r_[ix, order(knn_prediction(model, ix, response), ix)[:7]]
            assert np.array_equal(np.r_[ix, order(tissue, ix)[:7]], actions[i, 2])
            assert all(len(np.unique(a)) == 13 for a in actions[i])
        arrays['probability_predictions'] = np.stack((arrays['prior_probabilities'],
                                                     arrays['post_probabilities8']), axis=1)
        arrays['bootstrap_indices'] = np.random.default_rng(20261029).integers(0, 243, (2000, 243))
        np.savez_compressed(HERE / 'independent_actions_frozen.npz', **arrays)
        save_json(HERE / 'independent_exposure.json', exposure)
        # Only after every action is persisted does scoring convert selected truth.
        hits, unknown = np.zeros((243, 7), dtype=np.int64), np.zeros((243, 7), dtype=np.int64)
        bounds = np.zeros((243, 6, 2), dtype=np.int64)
        arrays.update(hits=hits, unknown=unknown, paired_bounds=bounds)
        for i in range(243):
            check_budget(start)
            y = np.full(64, np.nan)
            for j in np.unique(actions[i]):
                y[j] = parse_ln(raw.get((i, int(j))))
            finite = np.isfinite(y)
            events = event_labels(y, model['low'], model['high'])
            for a in range(7):
                hits[i, a] = events[actions[i, a]].sum()
                unknown[i, a] = (~finite[actions[i, a]]).sum()
            for a in range(1, 7):
                bounds[i, a - 1] = paired_bounds(actions[i, 0], actions[i, a], events, finite)
        np.savez_compressed(HERE / 'independent_replay_arrays.npz', **arrays)
        summary = summarize(arrays)
        summary['exposure_boundary'] = exposure
        summary['requested_attempts_per_cell'] = 13
        summary['effective_finite_attempts_per_cell'] = {
            name: float(13 - unknown[:, j].mean()) for j, name in enumerate(ARMS)}
        summary['input_hashes'] = EXPECTED
        summary['cpu_seconds'] = time.process_time() - start
        save_json(HERE / 'independent_experiment_summary.json', summary)
        save_json(receipt, {'status': 'completed', 'script_sha256': digest(Path(__file__)),
                            'cpu_seconds': time.process_time() - start,
                            'array_sha256': digest(HERE / 'independent_replay_arrays.npz')})
    except BaseException as exc:
        np.savez_compressed(HERE / 'independent_partial.npz', **arrays)
        save_json(HERE / 'independent_exposure.json', exposure)
        save_json(receipt, {'status': 'failed_no_automatic_retry', 'error': repr(exc),
                            'traceback': traceback.format_exc(), 'cpu_seconds': time.process_time() - start})
        raise


def compare_only(main_directory):
    # This function intentionally never opens CSV, model, or protocol inputs.
    report = {'arrays': {}, 'summaries': {}, 'mechanism_adjudication': 'not performed'}
    names = ('actions', 'first6', 'probability_predictions', 'posterior_m8', 'posterior_p8',
             'posterior_m1', 'posterior_p1', 'bootstrap_indices', 'hits', 'unknown', 'paired_bounds')
    with np.load(HERE / 'independent_replay_arrays.npz', allow_pickle=False) as independent:
        with np.load(main_directory / 'replay_arrays.npz', allow_pickle=False) as author:
            for k in names:
                x, y = independent[k], author[k]
                same_shape = x.shape == y.shape
                equal = bool(same_shape and np.array_equal(x, y))
                delta = float(np.max(np.abs(x - y))) if same_shape else None
                report['arrays'][k] = {'shape_equal': same_shape, 'exact_equal': equal,
                    'max_abs_difference': delta, 'within_1e8': bool(same_shape and np.allclose(x, y, atol=1e-8, rtol=0))}
    own = json.loads((HERE / 'independent_experiment_summary.json').read_text(encoding='utf-8'))
    other = json.loads((main_directory / 'experiment_summary.json').read_text(encoding='utf-8-sig'))
    for group in ('metrics', 'comparisons'):
        for arm, values in own[group].items():
            for field, value in values.items():
                target = other.get(group, {}).get(arm, {}).get(field)
                key = f'{group}.{arm}.{field}'
                report['summaries'][key] = bool(target is not None and np.allclose(value, target, atol=1e-12, rtol=0))
    exact = ('actions', 'first6', 'bootstrap_indices', 'hits', 'unknown', 'paired_bounds')
    report['all_compared_match'] = bool(all(report['arrays'][k]['exact_equal'] for k in exact)
        and all(v['within_1e8'] for v in report['arrays'].values())
        and all(report['summaries'].values()))
    save_json(HERE / 'independent_comparison.json', report)
    print(json.dumps({'all_compared_match': report['all_compared_match']}))


def synthetic_only():
    assert order([1, 1, 1]).tolist() == [0, 1, 2]
    assert order([1, 1, 1], [1]).tolist() == [0, 2]
    events, finite = np.array([False, True, False]), np.array([False, True, False])
    assert paired_bounds([0, 1], [0, 2], events, finite) == [0, 1]
    assert paired_bounds([0], [0], events, finite) == [0, 0]
    duplicates = {}
    for rank, raw in [((10, 3), 'A'), ((9, 8), 'B'), ((9, 4), 'C'), ((11, 2), 'D')]:
        retain_record(duplicates, (0, 0), rank, raw)
    assert duplicates[(0, 0)] == ((9, 4), 'C')
    rng = np.random.default_rng(4)
    a, m, p, noise = rng.normal(size=(6, 3)), rng.normal(size=3), np.eye(3), np.full(6, .4)
    response = rng.normal(size=6)
    direct_m, direct_p = posterior(a, m, p, noise, np.arange(6), response)
    sequential_m, sequential_p = m.copy(), p.copy()
    for j in range(6):
        gain = sequential_p @ a[j] / (a[j] @ sequential_p @ a[j] + noise[j])
        sequential_m += gain * (response[j] - a[j] @ sequential_m)
        sequential_p -= np.outer(gain, a[j] @ sequential_p)
    assert np.allclose(direct_m, sequential_m, atol=1e-12, rtol=0)
    assert np.allclose(direct_p, sequential_p, atol=1e-12, rtol=0)
    no_m, no_p = posterior(a, m, p, noise, np.arange(6), np.full(6, np.nan))
    assert np.array_equal(no_m, m) and np.array_equal(no_p, p)
    assert event_labels(np.array([-1., -2., 0.]), -2, 1).tolist() == [True, False, True]
    print('Synthetic-only checks passed; no real source or frozen artifacts opened.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--synthetic-only', action='store_true')
    mode.add_argument('--run-authorized', action='store_true')
    mode.add_argument('--compare-only', type=Path, metavar='MAIN_OUTPUT_DIRECTORY')
    args = parser.parse_args()
    if args.synthetic_only:
        synthetic_only()
    elif args.compare_only:
        compare_only(args.compare_only)
    else:
        run_authorized()
