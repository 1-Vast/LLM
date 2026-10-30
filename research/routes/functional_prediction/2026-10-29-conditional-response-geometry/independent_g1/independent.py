"""Independent G1.v1.1 implementation. No coordinator implementation imported."""
import csv
import ctypes as ct
from ctypes import wintypes as wt
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
EP = OUT.parent
PY = sys.executable


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError('design_invalid: ' + reason)


def numeric():
    import numpy as np
    return np


def fit(y, groups):
    np = numeric()
    z = y - y.mean(axis=1, keepdims=True)
    mean = z.mean(axis=0)
    categories = sorted(set(groups))
    blocks = {g: z[np.array(groups) == g] for g in categories}
    degrees = sum(max(len(b) - 1, 0) for b in blocks.values())
    require(degrees > 0, 'no pooled covariance degrees of freedom')
    pooled = sum((b - b.mean(axis=0)).T @ (b - b.mean(axis=0)) for b in blocks.values()) / degrees
    trace = float(np.trace(pooled))
    require(trace > 1e-12, 'pooled covariance trace too small')
    p = np.eye(8) - np.ones((8, 8)) / 8
    ridge = 1e-6 * trace / 8 * p
    centers, shapes = {}, {}
    for g, b in blocks.items():
        n = len(b)
        centers[g] = (n * b.mean(axis=0) + 8 * mean) / (n + 8)
        shape = pooled
        if n >= 2:
            cov = (b - b.mean(axis=0)).T @ (b - b.mean(axis=0)) / (n - 1)
            if float(np.trace(cov)) > 1e-12:
                cov = cov * trace / np.trace(cov)
            else:
                cov = pooled
            gamma = (n - 1) / (n - 1 + 8)
            shape = (1 - gamma) * pooled + gamma * cov
        shapes[g] = shape + ridge
    return mean, pooled + ridge, centers, shapes, trace


def center_shape(model, group, conditional):
    return model[2].get(group, model[0]), model[3].get(group, model[1]) if conditional else model[1]


def corrected(mu, covariance, q, r, delta):
    direction = covariance[:, q] - covariance[:, r]
    denominator = covariance[q, q] + covariance[r, r] - 2 * covariance[q, r]
    require(denominator > 0, 'nonpositive observation variance')
    return mu + direction / denominator * (delta - mu[q] + mu[r])


def first_optimum(values, maximize=False):
    best = max(values) if maximize else min(values)
    return next(i for i, v in enumerate(values) if abs(v - best) <= 1e-12 * max(1, abs(best)))


def plan():
    np = numeric()
    data = load(OUT / 'predictor_training_input.json')
    y, groups, pairs = np.array(data['y']), data['groups'], data['pairs']
    pair_q, pair_r = np.array(pairs).T
    fold_rows = []
    totals = {method: np.zeros(28) for method in ('B0', 'B1')}
    for excluded in range(len(y)):
        retain = np.arange(len(y)) != excluded
        model = fit(y[retain], [g for i, g in enumerate(groups) if i != excluded])
        true = y[excluded, pair_q] - y[excluded, pair_r]
        for method in totals:
            mu, covariance = center_shape(model, groups[excluded], method == 'B1')
            for k, (q, r) in enumerate(pairs):
                pred = corrected(mu, covariance, q, r, float(y[excluded, q] - y[excluded, r]))
                loss = float(np.mean((pred[pair_q] - pred[pair_r] - true) ** 2))
                totals[method][k] += loss
                fold_rows.append([data['conditions'][excluded], method, q, r, loss])
    with (OUT / 'loo_fold_pair_losses.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['left_out_condition', 'method', 'q', 'r', 'raw_pair_MSE'])
        writer.writerows(fold_rows)
    fixed = {method: first_optimum((values / len(y)).tolist()) for method, values in totals.items()}
    save('loo_selection.json', {'pair_order': pairs, 'raw_MSE': {k: (v / len(y)).tolist() for k, v in totals.items()}, 'fixed_pair_index': fixed, 'folds': len(y), 'all_components_refitted_each_fold': True})
    model = fit(y, groups)
    arrays = {'global_mean': model[0], 'global_cov': model[1], 'trace_pre_ridge': np.array(model[4])}
    categories = sorted(model[2])
    for i, g in enumerate(categories):
        arrays['mean_' + str(i)] = model[2][g]
        arrays['cov_' + str(i)] = model[3][g]
    np.savez(OUT / 'training_model.npz', **arrays)
    save('model_categories.json', categories)
    development = load(OUT / 'predictor_development_metadata.json')
    actions, gain_rows = [], []
    for row in development:
        mu, covariance = center_shape(model, row['group'], True)
        gains = []
        for q, r in pairs:
            direction = covariance[:, q] - covariance[:, r]
            variance = covariance[q, q] + covariance[r, r] - 2 * covariance[q, r]
            gains.append(float(direction @ direction / variance))
        gain_rows.append({'condition': row['condition'], 'values': gains})
        for method in ('B0', 'B1', 'C'):
            index = first_optimum(gains, True) if method == 'C' else fixed[method]
            q, r = pairs[index]
            actions.append({'condition': row['condition'], 'group': row['group'], 'method': method, 'pair_index': index, 'q': q, 'r': r})
    save('C_gain_all_pairs.json', {'pair_order': pairs, 'gains': gain_rows})
    save('actions_frozen.json', actions)
    save('action_freeze_receipt.json', {'timestamp_ns': time.time_ns(), 'actions_sha256': sha(OUT / 'actions_frozen.json'), 'count': len(actions), 'delta_file_exists': (OUT / 'signed_delta_releases.json').exists(), 'D': 2 * model[4] / 7})


def predict():
    np = numeric()
    arrays = np.load(OUT / 'training_model.npz')
    categories = load(OUT / 'model_categories.json')
    outputs = []
    for release in load(OUT / 'signed_delta_releases.json'):
        g = release['group']
        i = categories.index(g) if g in categories else None
        mu = arrays['mean_' + str(i)] if i is not None else arrays['global_mean']
        covariance = arrays['cov_' + str(i)] if i is not None and release['method'] != 'B0' else arrays['global_cov']
        pred = corrected(mu, covariance, release['q'], release['r'], release['delta'])
        outputs.append({**release, 'prediction': pred.tolist()})
    save('predictions.json', outputs)
    save('no_query_predictions.json', [{'condition': row['condition'], 'prediction': (arrays['mean_' + str(categories.index(row['group']))] if row['group'] in categories else arrays['global_mean']).tolist()} for row in load(OUT / 'predictor_development_metadata.json')])


def scorer():
    np = numeric()
    freeze = load(EP / 'input_freeze_v1_1.json')
    receipt = load(EP / 'preexecution_freeze_receipt.json')
    hashes = {}
    for name in ('protocol_g1_v1_1.md', 'input_freeze_v1_1.json'):
        hashes[str(EP / name)] = sha(EP / name)
        require(hashes[str(EP / name)] == receipt['sha256'][name], name + ' changed')
    hashes[str(EP / 'preexecution_freeze_receipt.json')] = sha(EP / 'preexecution_freeze_receipt.json')
    dependencies = [(Path(freeze['source']), freeze['source_sha256']), (EP / 'metadata_projection.json', freeze['metadata_projection_sha256']), (Path(freeze['metadata_window_dependency']['path']), freeze['metadata_window_dependency']['sha256'])]
    for path, expected in dependencies:
        hashes[str(path)] = sha(path)
        require(hashes[str(path)] == expected, str(path) + ' SHA mismatch')
    save('verified_input_hashes.json', hashes)
    projection = load(EP / 'metadata_projection.json')
    require(Path(freeze['source']).stat().st_size == 20355833 == projection['source_B'], 'frozen source byte size')
    windows = {row['id']: row for row in load(dependencies[2][0])['conditions']}
    records = {row['condition']: row for row in freeze['conditions']}
    panel = freeze['panel']
    train, dev = freeze['train_conditions'], freeze['development_conditions']
    require(len(records) == 173 and len(train) == 125 and len(dev) == 48, 'condition counts')
    require(set(train).isdisjoint(dev) and set(train + dev) == set(records), 'split disjoint and exhaustive')
    require(freeze['pairs'] == [[q, r] for q in range(8) for r in range(q + 1, 8)], 'pair ordering')
    for condition in records:
        require((int(hashlib.sha256(('geometry-dev-v1:' + condition).encode()).hexdigest(), 16) % 4 == 0) == (condition in dev), 'split hash')
    group = {}
    drug_to_condition = {}
    for condition, record in records.items():
        require(len(record['drug_ids']) == len(record['drug_names']) == len(record['pathways']) == 1, 'identity annotation ambiguity')
        require(record['drug_ids'][0] not in drug_to_condition, 'duplicate frozen drug ID')
        drug_to_condition[record['drug_ids'][0]] = condition
        group[condition] = record['pathways'][0]
        for k in ('min_conc_raw', 'max_conc_raw'):
            require(record[k] == windows[condition][k], 'window dependency strings')
        require(record['drug_ids'][0] == windows[condition]['drug_id'] and record['drug_names'][0] == windows[condition]['drug_name'], 'window identity dependency')
        p = next(x for x in projection['conditions'] if x['condition'] == condition)
        require(all(p[k] == record[k] for k in ('drug_names', 'drug_ids', 'pathways', 'panel_metadata_present')), 'projection annotation identity')
    require([row['sidm'] for row in projection['metadata_only_candidate_panel']] == panel, 'metadata frozen panel')
    # The scorer alone sees development absolute labels. Predictor children receive no scorer memory.
    values = {}
    allowed = ['DRUG_ID', 'DRUG_NAME', 'SANGER_MODEL_ID', 'PATHWAY_NAME', 'MIN_CONC', 'MAX_CONC', 'LN_IC50']
    source_rows = 0
    with open(freeze['source'], newline='', encoding='utf-8-sig') as stream:
        reader = csv.reader(stream)
        header = next(reader)
        indices = {name: header.index(name) for name in allowed}
        for raw in reader:
            source_rows += 1
            # Access only seven declared columns, including the sole outcome LN_IC50.
            drug, sidm = raw[indices['DRUG_ID']], raw[indices['SANGER_MODEL_ID']]
            if drug not in drug_to_condition or sidm not in panel:
                continue
            condition = drug_to_condition[drug]
            record = records[condition]
            low, high = Decimal(raw[indices['MIN_CONC']]), Decimal(raw[indices['MAX_CONC']])
            if low != Decimal(record['min_conc_raw']) or high != Decimal(record['max_conc_raw']):
                continue
            require(raw[indices['DRUG_NAME']] == record['drug_names'][0] and raw[indices['PATHWAY_NAME']] == group[condition], 'row name/pathway conflict')
            key = (condition, sidm)
            require(key not in values, 'duplicate crossing at exact Decimal window')
            response = float(raw[indices['LN_IC50']])
            require(math.isfinite(response), 'nonfinite LN_IC50')
            values[key] = response
    require(len(values) == 173 * 8, 'complete frozen crossing')
    clusters = sorted(set(group[c] for c in dev))
    require(len(clusters) >= 8 and clusters == freeze['bootstrap']['cluster_order'], 'bootstrap categories')
    save('qualification.json', {'status': 'eligible', 'source_rows_scanned': source_rows, 'selected_crossings': len(values), 'columns_accessed': allowed, 'no_response_filtering_or_panel_changes': True, 'training_conditions': len(train), 'development_conditions': len(dev), 'clusters': clusters})
    save('predictor_training_input.json', {'conditions': train, 'groups': [group[c] for c in train], 'y': [[values[c, s] for s in panel] for c in train], 'pairs': freeze['pairs']})
    save('predictor_development_metadata.json', [{'condition': c, 'group': group[c]} for c in dev])
    subprocess.run([PY, __file__, 'plan'], check=True)
    actions = load(OUT / 'actions_frozen.json')
    action_receipt = load(OUT / 'action_freeze_receipt.json')
    require(not action_receipt['delta_file_exists'] and action_receipt['count'] == 144, 'all actions before delta release')
    require(sha(OUT / 'actions_frozen.json') == action_receipt['actions_sha256'], 'action hash stable')
    releases = []
    for action in actions:
        c, q, r = action['condition'], action['q'], action['r']
        require(q < r and [q, r] == freeze['pairs'][action['pair_index']], 'signed pair direction')
        releases.append({**action, 'delta': values[c, panel[q]] - values[c, panel[r]], 'curve_attempts': 2})
    save('signed_delta_releases.json', releases)
    save('delta_release_receipt.json', {'timestamp_ns': time.time_ns(), 'action_sha256_verified': sha(OUT / 'actions_frozen.json'), 'delta_sha256': sha(OUT / 'signed_delta_releases.json'), 'per_strategy_curves': 96, 'development_absolute_values_delivered': False})
    subprocess.run([PY, __file__, 'predict'], check=True)
    losses = {method: {} for method in ('B0', 'B1', 'C', 'no_query')}
    pair_q, pair_r = np.array(freeze['pairs']).T
    D = action_receipt['D']
    details = []
    for row in load(OUT / 'predictions.json') + [{**r, 'method': 'no_query'} for r in load(OUT / 'no_query_predictions.json')]:
        c, method = row['condition'], row['method']
        y = np.array([values[c, s] for s in panel])
        pred = np.array(row['prediction'])
        require(bool(np.all(np.isfinite(pred))), 'nonfinite predictions')
        raw = float(np.mean(((pred[pair_q] - pred[pair_r]) - (y[pair_q] - y[pair_r])) ** 2))
        losses[method][c] = raw / D
        details.append({'condition': c, 'group': group[c], 'method': method, 'raw_pair_MSE': raw, 'normalized_loss': raw / D})
    save('per_drug_losses.json', details)
    draws = np.random.Generator(np.random.PCG64(20261029)).integers(0, 18, size=(9999, 18))
    np.save(OUT / 'bootstrap_shared_draws.npy', draws)
    sizes = np.array([sum(group[c] == g for c in dev) for g in clusters])
    comparisons, replicate_arrays = {}, {}
    for method in ('B0', 'B1'):
        delta = np.array([losses[method][c] - losses['C'][c] for c in dev])
        sums = np.array([sum(delta[i] for i, c in enumerate(dev) if group[c] == g) for g in clusters])
        bootstrap = sums[draws].sum(axis=1) / sizes[draws].sum(axis=1)
        lo, hi = np.quantile(bootstrap, [.025, .975], method='linear')
        comparisons[method + '_minus_C'] = {'mean': float(delta.mean()), 'CI95': [float(lo), float(hi)], 'gate': bool(delta.mean() > 0 and lo > 0), 'per_condition_delta': dict(zip(dev, delta.tolist()))}
        replicate_arrays[method + '_minus_C'] = bootstrap
    np.savez(OUT / 'bootstrap_replicates.npz', **replicate_arrays)
    distinct = sorted(set((a['q'], a['r']) for a in actions if a['method'] == 'C'))
    summary = {'version': 'G1.v1.1', 'D': D, 'mean_losses': {m: sum(v.values()) / len(v) for m, v in losses.items()}, 'comparisons': comparisons, 'C_distinct_pairs': [list(x) for x in distinct], 'C_action_diversity_gate': len(distinct) >= 2, 'phenomenon_development_support': all(v['gate'] for v in comparisons.values()) and len(distinct) >= 2, 'quantile': 'numpy.quantile(method=linear)', 'bootstrap_draw_sha256': sha(OUT / 'bootstrap_shared_draws.npy'), 'numpy_version': np.__version__, 'interpretation': 'Fitted-label local necessary phenomenon only; no new algorithm, biology or common-learning claim.'}
    save('summary.json', summary)
    save('self_checks.json', {'independent_implementation': True, 'coordinator_implementation_or_numbers_seen': False, 'all_125_LOO_folds_full_refit': True, '28_fixed_action_candidates': True, 'pre_delta_action_freeze_verified': True, 'predictor_has_only_training_labels_development_metadata_and_signed_delta_files': True, 'raw_LOO_no_fold_D': True, 'full_training_pre_ridge_D': True, 'shared_draw_matrix_and_linear_quantile': True, 'source_qualification': 'eligible'})


# Windows job-object supervision: aggregate memory hard limit, hard user-CPU limit,
# and total user+kernel CPU / output-volume kill guards sampled every 10 ms.
class BASIC(ct.Structure):
    _fields_ = [('process_time', ct.c_longlong), ('job_time', ct.c_longlong), ('flags', wt.DWORD), ('min_ws', ct.c_size_t), ('max_ws', ct.c_size_t), ('active_limit', wt.DWORD), ('affinity', ct.c_size_t), ('priority', wt.DWORD), ('scheduling', wt.DWORD)]


class IO(ct.Structure):
    _fields_ = [(name, ct.c_ulonglong) for name in ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]


class EXTENDED(ct.Structure):
    _fields_ = [('basic', BASIC), ('io', IO), ('process_memory', ct.c_size_t), ('job_memory', ct.c_size_t), ('peak_process_memory', ct.c_size_t), ('peak_job_memory', ct.c_size_t)]


class ACCOUNTING(ct.Structure):
    _fields_ = [('user', ct.c_longlong), ('kernel', ct.c_longlong), ('period_user', ct.c_longlong), ('period_kernel', ct.c_longlong), ('faults', wt.DWORD), ('processes', wt.DWORD), ('active', wt.DWORD), ('terminated', wt.DWORD)]


class MEMORY(ct.Structure):
    _fields_ = [('size', wt.DWORD), ('faults', wt.DWORD), ('peak_ws', ct.c_size_t), ('ws', ct.c_size_t), ('peak_paged', ct.c_size_t), ('paged', ct.c_size_t), ('peak_nonpaged', ct.c_size_t), ('nonpaged', ct.c_size_t), ('pagefile', ct.c_size_t), ('peak_pagefile', ct.c_size_t)]


def supervise():
    kernel = ct.WinDLL('kernel32', use_last_error=True)
    psapi = ct.WinDLL('psapi', use_last_error=True)
    kernel.CreateJobObjectW.restype = wt.HANDLE
    kernel.OpenProcess.restype = wt.HANDLE
    kernel.SetInformationJobObject.argtypes = [wt.HANDLE, ct.c_int, ct.c_void_p, wt.DWORD]
    kernel.QueryInformationJobObject.argtypes = [wt.HANDLE, ct.c_int, ct.c_void_p, wt.DWORD, ct.c_void_p]
    kernel.AssignProcessToJobObject.argtypes = [wt.HANDLE, wt.HANDLE]
    kernel.TerminateJobObject.argtypes = [wt.HANDLE, wt.UINT]
    kernel.ResumeThread.argtypes = [wt.HANDLE]
    kernel.CloseHandle.argtypes = [wt.HANDLE]
    kernel.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    psapi.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ct.c_void_p, wt.DWORD]
    job = kernel.CreateJobObjectW(None, None)
    limits = EXTENDED()
    limits.basic.flags = 0x4 | 0x200 | 0x2000  # job user CPU, job memory, kill on close
    limits.basic.job_time = 120 * 10_000_000
    limits.job_memory = 1073741824
    require(bool(kernel.SetInformationJobObject(job, 9, ct.byref(limits), ct.sizeof(limits))), 'job limits unavailable')
    environment = os.environ.copy()
    environment.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    started = time.perf_counter()
    # Suspended creation ensures no functional-data access before assigning the hard job limits.
    import _winapi
    startup = subprocess.STARTUPINFO()
    command = subprocess.list2cmdline([PY, __file__, 'scorer'])
    creationflags = 0x4 | 0x08000000
    # Popen cannot expose the suspended thread; use native CreateProcess directly.
    process_handle, thread_handle, pid, tid = _winapi.CreateProcess(PY, command, None, None, False, creationflags, environment, str(OUT), startup)
    require(bool(kernel.AssignProcessToJobObject(job, wt.HANDLE(process_handle))), 'job assignment failed')
    require(kernel.ResumeThread(wt.HANDLE(thread_handle)) != 0xFFFFFFFF, 'resume failed')
    _winapi.CloseHandle(thread_handle)
    peak_ws = 0
    peak_ws_by_pid = {}
    killed = None
    while True:
        accounting = ACCOUNTING()
        require(bool(kernel.QueryInformationJobObject(job, 1, ct.byref(accounting), ct.sizeof(accounting), None)), 'job accounting failed')
        # Variable length process-ID list; capacity exceeds this run's concurrency.
        class PIDS(ct.Structure):
            _fields_ = [('assigned', wt.DWORD), ('listed', wt.DWORD), ('ids', ct.c_size_t * 16)]
        pids = PIDS()
        if kernel.QueryInformationJobObject(job, 3, ct.byref(pids), ct.sizeof(pids), None):
            working_sets = []
            for child_pid in pids.ids[:pids.listed]:
                handle = kernel.OpenProcess(0x410, False, child_pid)
                if handle:
                    mem = MEMORY()
                    mem.size = ct.sizeof(mem)
                    if psapi.GetProcessMemoryInfo(handle, ct.byref(mem), ct.sizeof(mem)):
                        peak_ws_by_pid[str(child_pid)] = max(peak_ws_by_pid.get(str(child_pid), 0), int(mem.peak_ws))
                        working_sets.append(int(mem.ws))
                    kernel.CloseHandle(handle)
            peak_ws = max(peak_ws, sum(working_sets))
        total_bytes = sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
        total_cpu = (accounting.user + accounting.kernel) / 10_000_000
        if total_cpu > 120 or total_bytes > 50_000_000 or peak_ws > 1073741824:
            killed = 'CPU' if total_cpu > 120 else 'disk' if total_bytes > 50_000_000 else 'working_set'
            kernel.TerminateJobObject(job, 91)
        if accounting.active == 0:
            break
        time.sleep(.01)
    elapsed = time.perf_counter() - started
    kernel.QueryInformationJobObject(job, 9, ct.byref(limits), ct.sizeof(limits), None)
    exitcode = _winapi.GetExitCodeProcess(process_handle)
    _winapi.CloseHandle(process_handle)
    files = {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in OUT.iterdir() if p.is_file() and p.name not in ('execution_receipt.json', 'file_hash_manifest.json')}
    save('file_hash_manifest.json', files)
    save('execution_receipt.json', {'wall_seconds': elapsed, 'process_CPU_user_seconds': accounting.user / 10_000_000, 'process_CPU_kernel_seconds': accounting.kernel / 10_000_000, 'process_CPU_total_seconds': total_cpu, 'Windows_peak_working_set_per_PID_bytes': peak_ws_by_pid, 'sampled_peak_sum_working_sets_bytes': peak_ws, 'Windows_job_peak_commit_bytes': int(limits.peak_job_memory), 'hard_job_memory_limit_bytes': 1073741824, 'hard_job_user_CPU_seconds': 120, 'total_CPU_and_output_guard_sample_seconds': .01, 'hard_guard_termination': killed, 'output_bytes_before_receipt': sum(v['bytes'] for v in files.values()), 'output_limit_bytes': 50_000_000, 'exit_code': exitcode, 'python': PY, 'code_sha256': sha(__file__), 'process_count': accounting.processes, 'single_experiment_attempt': True, 'GPU': 0, 'installed_packages': 0, 'external_model_API_calls': 0, 'retry': 0})
    kernel.CloseHandle(job)
    if exitcode:
        raise SystemExit(exitcode)


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'supervise'
    try:
        {'plan': plan, 'predict': predict, 'scorer': scorer, 'supervise': supervise}[mode]()
    except Exception as exc:
        save('failure_' + mode + '.json', {'exception': type(exc).__name__, 'message': str(exc), 'timestamp_ns': time.time_ns()})
        raise
