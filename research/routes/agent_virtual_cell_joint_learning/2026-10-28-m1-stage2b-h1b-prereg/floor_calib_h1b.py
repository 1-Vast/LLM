#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M1-S2B-H1B-PREREG floor calibration: oracle two-sample TV floor for the NEW H1b measurement
protocol, calibration-only. No C-MDN training, no effect, no real data.
"""
import sys
import os
import json
import math
import hashlib
import time

sys.dont_write_bytecode = True
import numpy as np

ROOT = r'D:\MAESTRO'
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-m1-stage2b-h1b-prereg')
M1S2 = os.path.join(ROOT, 'research', '2026-10-28-m1-stage2-prep')
DIAG = os.path.join(ROOT, 'research', '2026-10-28-m1-stage2-fail-diag')
RERUN = os.path.join(ROOT, 'research', '2026-10-28-m1-stage2-rerun')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'floor_calib_h1b.json')
SCHEMA = os.path.join(OUTDIR, 'schema_h1b.json')

PARAM_SEED = 20261301
TRAIN_SEED = 20261302
EVAL_SEED = 20261303
FLOOR_SEED_BASE = 20261801
EXEC_SEED_BASE = 20261811
CAPS = {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8, 'new_wells': 0}

B_GRID = [16, 32, 64, 128, 256]
N_EVAL_GRID = [2048, 8192, 16384, 32768]
K_GRID = [1, 4, 16]
D_GRID = [8, 16, 32, 64]
N_TRAIN_GRID = [512, 1024, 2048, 4096]
MC_REPS = 300
P_EST_N = 400000


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest().upper()


def rq(x, nd=8):
    if x is None:
        return None
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        v = float(x)
        if not math.isfinite(v):
            return None
        return float(round(v, nd))
    return x


def sanitize(obj):
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return rq(float(obj))
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, float):
        return rq(obj)
    return obj


def write_json(obj, path):
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(sanitize(obj), fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write('\n')


def make_theta():
    rng = np.random.default_rng(PARAM_SEED)
    c = rng.normal(scale=0.5, size=(4, 3, 4))
    M = rng.normal(scale=0.1, size=(4, 3, 4, 64))
    d = rng.normal(scale=0.1, size=(4, 3, 64))
    w = np.array([0.5, 0.3, 0.2])
    return c, M, d, w


def oracle_y(dim, n, rng, theta):
    """Sample Y for action a=0, X~N(0,I_dim), truncated GMM; returns (n,4)."""
    c, M, d, w = theta
    out = []
    got = 0
    while got < n:
        m = min(100000, n - got)
        x = rng.normal(size=(m, dim))
        k = rng.choice(3, size=m, p=w)
        mu = c[0, k] + np.einsum('mk, mkj->mj', x, M[0, k][:, :, :dim].transpose(0, 2, 1)) if False else None
        # mu[m,j] = c[0,k[m],j] + sum_l x[m,l]*M[0,k[m],j,l]
        mu = c[0, k].copy()
        for j in range(4):
            mu[:, j] += np.sum(x * M[0, k, j, :dim], axis=1)
        sig = 0.1 + 0.4 / (1.0 + np.exp(-np.sum(x * d[0, k, :dim], axis=1)))
        eps = rng.normal(size=(m, 4))
        y = mu + sig[:, None] * eps
        ok = np.all((y >= -2.0) & (y <= 2.0), axis=1)
        out.append(y[ok])
        got += int(ok.sum())
    return np.concatenate(out, axis=0)[:n]


def hash_cells(y, B):
    q = np.floor((y + 2.0) / 4.0 * 256.0).astype(np.int64)
    q = np.clip(q, 0, 255)
    code = q[:, 0] + 256 * q[:, 1] + 65536 * q[:, 2] + 16777216 * q[:, 3]
    return code % B


def main():
    t0 = time.time()
    say = lambda m: print(m, flush=True)
    say('[1/6] frozen Pθ params (param_seed 20261301) + floor MC seeds ...')
    theta = make_theta()
    say('    c%s M%s d%s w=%s' % (theta[0].shape, theta[1].shape, theta[2].shape, theta[3]))

    say('[2/6] estimate oracle cell probabilities per d/B (MC, calibration only) ...')
    p_by_d = {}
    floor_seeds = [FLOOR_SEED_BASE + i for i in range(10)]  # 20261801..20261810
    for dim in D_GRID:
        rng = np.random.default_rng(FLOOR_SEED_BASE + dim)
        ys = oracle_y(dim, P_EST_N, rng, theta)
        p_by_d[dim] = {}
        for B in B_GRID:
            cells = hash_cells(ys, B)
            cnt = np.bincount(cells, minlength=B).astype(float)
            p = cnt / cnt.sum()
            p_by_d[dim][B] = p
        say('    d=%d sampled=%d' % (dim, len(ys)))

    say('[3/6] two-sample TV floor over B×N×K (multinomial MC, calibration only) ...')
    floor_rows = []
    worst = {}
    for B in B_GRID:
        for N in N_EVAL_GRID:
            for K in K_GRID:
                # worst-case q95 across d-specific oracle distributions
                q95_list = []
                mean_list = []
                for dim in D_GRID:
                    p = p_by_d[dim][B]
                    rng = np.random.default_rng(FLOOR_SEED_BASE + 1000 + B * 100 + N + K + dim)
                    vals = []
                    for rep in range(MC_REPS):
                        tvs = []
                        for kk in range(K):
                            c1 = rng.multinomial(N, p)
                            c2 = rng.multinomial(N, p)
                            tvs.append(0.5 * np.abs(c1 / N - c2 / N).sum())
                        vals.append(float(np.mean(tvs)))
                    vals = np.asarray(vals)
                    mean_list.append(float(vals.mean()))
                    q95_list.append(float(np.quantile(vals, 0.95)))
                row = {'B': B, 'N_eval': N, 'K': K,
                       'mean_worst': rq(max(mean_list)), 'q95_worst': rq(max(q95_list)),
                       'q95_by_d': {str(d): rq(q) for d, q in zip(D_GRID, q95_list)},
                       'mean_by_d': {str(d): rq(m) for d, m in zip(D_GRID, mean_list)},
                       'estimated_cost_units': int(B * N * K)}
                floor_rows.append(row)
                key = (B, N, K)
                worst[key] = row
    say('    floor rows=%d' % len(floor_rows))

    say('[4/6] select measurement parameters (pre-registered rule) ...')
    # Rule: choose eligible combos with q95_worst <= 0.02; among them minimize estimated cost units
    # (B*N*K), tie-break smaller floor q95. If none, take minimum q95_worst combo; if min q95 > 0.03 -> stop.
    eligible = [r for r in floor_rows if r['q95_worst'] <= 0.02]
    if eligible:
        selected = min(eligible, key=lambda r: (r['estimated_cost_units'], r['q95_worst']))
        selection_rule = 'eligible q95_worst<=0.02; minimize B*N*K; tie-break q95'
        decision = 'selected'
    else:
        selected = min(floor_rows, key=lambda r: r['q95_worst'])
        selection_rule = 'no combo q95<=0.02; choose minimum q95_worst; if >0.03 stop'
        decision = 'stop_precision_insufficient' if selected['q95_worst'] > 0.03 else 'selected_min_floor'
    say('    selected B=%d N=%d K=%d q95=%.5f decision=%s' % (
        selected['B'], selected['N_eval'], selected['K'], selected['q95_worst'], decision))

    say('[5/6] tolerance table / decidability arithmetic ...')
    tol_by_d = {}
    required_by_d = {}
    detectable_excess_by_d = {}
    for dim in D_GRID:
        q95 = float(selected['q95_by_d'][str(dim)])
        tol = math.ceil((3.0 * q95) * 1000.0) / 1000.0
        tol_by_d[str(dim)] = rq(tol)
        required_by_d[str(dim)] = rq(tol)
        detectable_excess_by_d[str(dim)] = rq(max(0.0, tol - q95))
    global_tol = max(tol_by_d.values())
    old_excess_median = 0.0599  # C217 diagnostic median C-MDN minus oracle
    old_excess_max = 0.2037
    # detection power approximation: candidate TV ~ excess + floor noise; floor noise distribution from MC
    # reuse selected floor q95/mean; normal approx with sd ~ (q95-mean)/1.645
    power_rows = {}
    for dim in D_GRID:
        q95 = float(selected['q95_by_d'][str(dim)])
        mean = float(selected['mean_by_d'][str(dim)])
        sd = max((q95 - mean) / 1.645, 1e-6)
        tol = tol_by_d[str(dim)]
        # pass if candidate TV <= tol; candidate TV approx excess + floor TV (floor mean/sd)
        p_detect_old = float(1.0 - 0.5 * (1.0 + math.erf(((tol - (old_excess_median + mean)) / (sd * math.sqrt(2))))))
        # power to detect excess > detectable (fraction floor <= tol-excess)
        power_rows[str(dim)] = {'tol': tol, 'floor_mean': rq(mean), 'floor_q95': rq(q95),
                                'required_candidate_TV_to_pass': tol,
                                'detectable_excess_above_floor': rq(max(0.0, tol - q95)),
                                'old_C217_excess_median': old_excess_median,
                                'approx_power_to_detect_old_excess': rq(p_detect_old),
                                'approx_pass_prob_if_old_excess': rq(1.0 - p_detect_old)}
    decidability = {
        'selected_measurement': {'B': selected['B'], 'N_eval': selected['N_eval'], 'K': selected['K']},
        'tolerance_rule': 'tol_d = ceil(3 * floor_q95_d * 1000)/1000; pass if H1b TV_d <= tol_d',
        'floor_rule': 'oracle-vs-oracle two-sample TV at same B/N_eval/K, worst-case over d; q95 <= tol/3 by construction',
        'tolerance_table': tol_by_d,
        'required_candidate_TV_to_pass': required_by_d,
        'detectable_excess_above_floor': detectable_excess_by_d,
        'global_tolerance': global_tol,
        'old_C217_excess': {'median': old_excess_median, 'max': old_excess_max},
        'power_approx': power_rows,
        'decision': decision,
        'precision_insufficient': bool(decision == 'stop_precision_insufficient'),
        'no_tolerance_from_M1_results': True,
    }
    say('    global tol=%.3f; detectable excess d64=%s; decision=%s' % (
        global_tol, detectable_excess_by_d['64'], decision))

    say('[6/6] write floor_calib_h1b.json + schema_h1b.json ...')
    exec_seeds = {
        'h1b_data_seed_base': EXEC_SEED_BASE,
        'h1b_eval_seed_base': EXEC_SEED_BASE + 1,
        'h1b_cell_seeds': [EXEC_SEED_BASE + 10 + i for i in range(16)],
        'h1b_two_run_seeds': 'same seeds, separate processes',
        'floor_calibration_seeds': floor_seeds,
        'forbidden_old_seeds': [PARAM_SEED, TRAIN_SEED, EVAL_SEED,
                                20261310, 20261311, 20261312, 20261313, 20261314, 20261315,
                                20261401, 20261420, 20261500, 20261601, 20261701],
        'note': 'floor calibration 20261801..20261810; H1b execution data/eval 20261811/20261812, cells 20261821..20261836; disjoint',
    }
    schema = {
        'schema': 'R204-M1-S2B-H1B', 'version': 'v1',
        'top_keys': ['task', 'status', 'old_protocol_unchanged', 'floor_calibration', 'selected_measurement',
                     'tolerance_table', 'decidability', 'execution_seeds', 'H1b_grid', 'G1_G6',
                     'failure_categories', 'budget', 'run_shas', 'failure_category', 'verdict'],
        'per_cell_fields': ['d', 'N_train', 'TV_h1b', 'tolerance', 'pass', 'n_eval', 'K', 'B'],
        'forbidden_fields': ['effect_size', 'decision_utility', 'regret', 'topk', 'method_comparison',
                             'pharmacology_claim', 'real_decision_claim', 'transfer_claim', 'mechanism_claim',
                             'novelty_claim', 'real_data_result'],
        'failure_categories': ['design_invalid: projection', 'design_invalid: calibration',
                               'design_invalid: leakage', 'design_invalid: two_run_mismatch',
                               'design_invalid: chain_mismatch', 'design_invalid: compute_budget_exceeded',
                               'precision_insufficient', 'inconclusive'],
        'no_effect_results': True, 'old_C216_unchanged': True,
        'two_run_rule': 'result JSON byte-identical; telemetry separate',
    }
    write_json(schema, SCHEMA)

    out = {
        'task': 'R204-M1-S2B-H1B-PREREG',
        'status': 'floor_calibration_only_not_method_execution',
        'old_protocol_unchanged': {
            'C216_old_H1': '0/16 FAIL; design_invalid: projection unchanged',
            'C217_attribution': 'old H1 frozen tolerance below oracle finite-sample floor; unchanged',
            'old_tolerances_unchanged': True,
            'H1b_is_new_separate_protocol': True,
            'not_a_fix_or_rerun_of_old_H1': True,
        },
        'frozen_theta': {'param_seed': PARAM_SEED, 'train_seed': TRAIN_SEED, 'eval_seed': EVAL_SEED,
                         'c_scale': 0.5, 'M_scale': 0.1, 'd_scale': 0.1,
                         'sigma_formula': '0.1+0.4*sigmoid(d^T x)', 'Y_box': [-2, 2], 'K': 3,
                         'weights': [0.5, 0.3, 0.2]},
        'floor_calibration': {
            'protocol': 'new H1b measurement: hash-partition TV between oracle samples (two independent samples '
                        'of N_eval from frozen Pθ at fixed action a=0, X~N(0,I_d)), averaged over K seeds; '
                        'partition: 8-bit per Y dim -> code -> cell=code mod B',
            'grid': {'B': B_GRID, 'N_eval': N_EVAL_GRID, 'K': K_GRID, 'd_floor': D_GRID},
            'MC_reps': MC_REPS, 'p_est_n_per_d': P_EST_N,
            'table': floor_rows,
            'selected': selected,
            'selection_rule': selection_rule,
            'decision': decision,
        },
        'selected_measurement': {'B': selected['B'], 'N_eval': selected['N_eval'], 'K': selected['K'],
                                 'q95_worst': selected['q95_worst'], 'mean_worst': selected['mean_worst']},
        'tolerance_table': tol_by_d,
        'decidability': decidability,
        'H1b_grid': {'d': D_GRID, 'N_train': N_TRAIN_GRID, 'cells': [(d, n) for d in D_GRID for n in N_TRAIN_GRID]},
        'execution_seeds': exec_seeds,
        'G1_G6': {
            'G1': 'conditional kernel/Pθ measurement unchanged by target; failure calibration',
            'G2': 'support/program legality; failure support',
            'G3': 'H1b approximation/projection; failure projection',
            'G4': 'no leakage; failure leakage',
            'G5': 'two-run byte-identical; failure two_run_mismatch',
            'G6': 'schema/budget; failure compute_budget_exceeded'},
        'failure_categories': schema['failure_categories'],
        'budget': {'caps': CAPS, 'compute_only': True, 'new_wells': 0,
                   'pilot_policy': 'H1b execution must run final-implementation pilot and freeze canonical timing; '
                                   'no C-MDN is run in this prereg task',
                   'floor_calib_note': 'calibration only, not H1b execution; wall recorded in usage/report, not in result JSON'},
        'boundaries': ['old C216/C217 unchanged; H1b separate new measurement protocol; no rerun to pass old H1',
                       'no C-MDN training/effect in this task; mechanism account only; compute-only; 0 wells',
                       'no pharmacology/real decision/transfer/mechanism/novelty claims; no code promotion',
                       'no modification of old judgments/thresholds; no revival of stopped experiments',
                       'M1 not mixed with M2/M3; N1 not evidence; data readiness open C203/C205/C210/C214'],
        'no_effect_results': True,
        'no_cmdn_run': True,
    }
    write_json(out, OUTJSON)
    print('floor_calib_h1b.json sha256:', sha256_file(OUTJSON))
    print('schema_h1b.json sha256:', sha256_file(SCHEMA))
    print('floor calib wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
