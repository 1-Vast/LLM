#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M1-S2d misspecification/background-drift planning-value pre-registration:
design-time headroom only. No candidate C-MDN training, no candidate planning, no effect/real data.
"""
import sys
import os
import json
import math
import hashlib
import time

sys.dont_write_bytecode = True
import numpy as np
from scipy.special import ndtr, log_ndtr

ROOT = r'D:\MAESTRO'
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-m1-s2d-misspec-prereg')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'headroom_design_m1_s2d_v0_2.json')
SCHEMA = os.path.join(OUTDIR, 'schema_m1_s2d_v0_2.json')

PARAM_SEED = 20261301
TRAIN_SEED = 20261302
EVAL_SEED = 20261303
TARGET_PARAM_SEEDS = {'T1_scale_drift': 20262001, 'T2_slope_drift': 20262002,
                      'T3_background_drift': None}
HEADROOM_REP_BASE = 20262011
R_REPS = 20
N_TRAIN = 4096
N_EVAL = 4096
A = 4
D_MAIN = 64
RW = np.array([0.4, 0.3, 0.2, 0.1])
LAM = 0.2
DELTA = 0.05
CAPS = {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8, 'new_wells': 0}
EXEC_SEED_BASE = 20262031
FORBIDDEN_OLD = [20261301, 20261302, 20261303, 20261310, 20261401, 20261500, 20261601,
                 20261701, 20261801, 20261811, 20261812, 20261821, 20261901, 20261921,
                 20261922, 20261931]

TARGETS = {
    'T1_scale_drift': {'c_scale': 1.0, 'M_scale': None, 'x_scale': 1.0,
                       'description': "c'~N(0,1.0^2); M,d same as source; X~N(0,I)"},
    'T2_slope_drift': {'c_scale': None, 'M_scale': 0.2, 'x_scale': 1.0,
                       'description': "M'~N(0,.2^2); c,d same as source; X~N(0,I)"},
    'T3_background_drift': {'c_scale': None, 'M_scale': None, 'x_scale': 1.5,
                            'description': "theta same as source; X'~N(0,1.5^2 I)"},
}


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


def make_source_theta():
    rng = np.random.default_rng(PARAM_SEED)
    c = rng.normal(scale=0.5, size=(A, 3, 4))
    M = rng.normal(scale=0.1, size=(A, 3, 4, 64))
    d = rng.normal(scale=0.1, size=(A, 3, 64))
    return c, M, d, np.array([0.5, 0.3, 0.2])


def make_target_theta(name, source):
    c0, M0, d0, w = source
    spec = TARGETS[name]
    if name == 'T1_scale_drift':
        rng = np.random.default_rng(TARGET_PARAM_SEEDS[name])
        return rng.normal(scale=spec['c_scale'], size=(A, 3, 4)), M0, d0, w
    if name == 'T2_slope_drift':
        rng = np.random.default_rng(TARGET_PARAM_SEEDS[name])
        return c0, rng.normal(scale=spec['M_scale'], size=(A, 3, 4, 64)), d0, w
    return c0, M0, d0, w


def _phi(z):
    return np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def true_expected_reward(x, a, dim, theta):
    c, M, d, w = theta
    x = np.asarray(x, dtype=float)
    n = x.shape[0]
    log2pi = math.log(2.0 * math.pi)
    zsum = np.zeros(n)
    ey = np.zeros((n, 4))
    ey2 = np.zeros((n, 4))
    for k in range(3):
        mu = c[a, k][None, :] + x[:, :dim] @ M[a, k, :, :dim].T
        sig = 0.1 + 0.4 / (1.0 + np.exp(-(x[:, :dim] @ d[a, k, :dim])))
        zlo = (-2.0 - mu) / sig[:, None]
        zhi = (2.0 - mu) / sig[:, None]
        log_ph = log_ndtr(zhi)
        log_pl = log_ndtr(zlo)
        with np.errstate(divide='ignore', invalid='ignore'):
            log_prob = log_ph + np.log1p(-np.exp(log_pl - log_ph))
        valid = np.isfinite(log_prob) & (log_prob > -700.0)
        logp_safe = np.where(valid, log_prob, 0.0)
        log_phi_lo = -0.5 * zlo * zlo - 0.5 * log2pi
        log_phi_hi = -0.5 * zhi * zhi - 0.5 * log2pi
        val = (np.exp(np.where(valid, log_phi_lo - logp_safe, -np.inf)) -
               np.exp(np.where(valid, log_phi_hi - logp_safe, -np.inf)))
        term = (np.exp(np.where(valid, log_phi_lo + np.log(np.maximum(zlo, 1e-300)) - logp_safe, -np.inf)) -
                np.exp(np.where(valid, log_phi_hi + np.log(np.maximum(zhi, 1e-300)) - logp_safe, -np.inf)))
        mean = mu + sig[:, None] * val
        var = sig[:, None] ** 2 * (1.0 + term - val * val)
        joint_log = np.sum(log_prob, axis=1)
        comp_valid = np.isfinite(joint_log) & (joint_log > -700.0)
        ww = np.where(comp_valid, w[k] * np.exp(joint_log), 0.0)
        zsum += ww
        ey += ww[:, None] * np.where(comp_valid[:, None], mean, 0.0)
        ey2 += ww[:, None] * np.where(comp_valid[:, None], var + mean * mean, 0.0)
    ok = zsum > 0.0
    out = np.full(n, np.nan)
    ey = ey[ok] / zsum[ok, None]
    ey2 = ey2[ok] / zsum[ok, None]
    out[ok] = RW @ ey.T - LAM * np.sum(ey2, axis=1)
    return out


def sample_reward(x, a, rng, theta, dim):
    c, M, d, w = theta
    x = np.asarray(x, dtype=float)
    n = x.shape[0]
    out = []
    got = 0
    while got < n:
        m = min(100000, n - got)
        xx = x[got:got + m]
        k = rng.choice(3, size=m, p=w)
        mu = c[a, k].copy()
        for j in range(4):
            mu[:, j] += np.sum(xx[:, :dim] * M[a, k, j, :dim], axis=1)
        sig = 0.1 + 0.4 / (1.0 + np.exp(-np.sum(xx[:, :dim] * d[a, k, :dim], axis=1)))
        eps = rng.normal(size=(m, 4))
        y = mu + sig[:, None] * eps
        ok = np.all((y >= -2.0) & (y <= 2.0), axis=1)
        yy = y[ok]
        out.append(yy @ RW - LAM * np.sum(yy * yy, axis=1))
        got += int(ok.sum())
    return np.concatenate(out, axis=0)[:n]


def main():
    t0 = time.time()
    say = lambda m: print(m, flush=True)
    source = make_source_theta()

    say('[1/5] source/target environment registration ...')
    targets = {}
    for name in TARGETS:
        targets[name] = make_target_theta(name, source)
    say('    targets: %s' % list(TARGETS))

    say('[2/5] design-time headroom on target Pθ\': P_empirical_mean_source baseline regret ...')
    results = {}
    for name in TARGETS:
        tgt = targets[name]
        x_scale = TARGETS[name]['x_scale']
        regs = []
        chosen = []
        valid_counts = []
        for r in range(R_REPS):
            rng = np.random.default_rng(HEADROOM_REP_BASE + r)
            # source-trained empirical-mean planner: N_train=4096 per action, action-level mean
            means = np.zeros(A)
            for a in range(A):
                x_train = rng.normal(size=(N_TRAIN, D_MAIN))
                rr = sample_reward(x_train, a, rng, source, D_MAIN)
                means[a] = float(rr.mean())
            best = int(np.argmax(means))
            chosen.append(best)
            # target eval X (background drift) and target Pθ' true reward
            x_eval = rng.normal(scale=x_scale, size=(N_EVAL, D_MAIN))
            true = np.column_stack([true_expected_reward(x_eval, a, D_MAIN, tgt) for a in range(A)])
            valid = np.all(np.isfinite(true), axis=1)
            valid_counts.append(int(valid.sum()))
            true = true[valid]
            best_true = np.max(true, axis=1)
            regret = best_true - true[:, best]
            regs.append(float(regret.mean()))
        regs = np.asarray(regs)
        mean = float(regs.mean())
        se = float(regs.std(ddof=1) / math.sqrt(R_REPS))
        ci = [mean - 2.093024054408263 * se, mean + 2.093024054408263 * se]
        results[name] = {'description': TARGETS[name]['description'], 'mean_baseline_regret': rq(mean),
                         'SE': rq(se), 'CI95_t': [rq(ci[0]), rq(ci[1])], 'chosen_actions': chosen,
                         'valid_eval_rows_min': min(valid_counts), 'n_eval': N_EVAL,
                         'x_scale': x_scale, 'headroom_ok': bool(mean >= 0.10)}
        say('    %s: mean=%.5f CI=[%.5f,%.5f] chosen=%s' % (name, mean, ci[0], ci[1], sorted(set(chosen))))

    say('[3/5] headroom gate (each target >= 2*delta = 0.10) ...')
    all_ok = all(v['headroom_ok'] for v in results.values())
    main_target = 'T1_scale_drift'
    decision = 'executable' if all_ok else 'redesign_before_candidate_or_unreachable_gate'
    say('    all targets headroom ok=%s decision=%s' % (all_ok, decision))

    say('[4/5] frozen comparison family / seeds / schema ...')
    comparisons = [
        {'id': 'primary', 'comparison': 'candidate (source-trained) vs P_empirical_mean_source',
         'role': 'standard source-trained empirical-mean planner'},
        {'id': 'secondary_target_adapted_empirical_mean',
         'comparison': 'candidate vs P_empirical_mean_target_adapted',
         'role': 'same-budget target calibration/reweighting: 3584 source + 512 target samples per action'},
        {'id': 'secondary_max_entropy', 'comparison': 'candidate vs P_max_entropy', 'role': 'max-entropy control'},
        {'id': 'secondary_conditional_density_MC', 'comparison': 'candidate vs P_conditional_density_MC',
         'role': 'same C-MDN; expected D=0, not independent'},
        {'id': 'secondary_random', 'comparison': 'candidate vs P_random', 'role': 'random legal planner'},
        {'id': 'secondary_softmax_expected_reward', 'comparison': 'candidate vs P_softmax_expected_reward',
         'role': 'softmax expected reward'},
    ]
    cell_blocks = {
        'T1_scale_drift': [20262041 + i for i in range(20)],
        'T2_slope_drift': [20262061 + i for i in range(20)],
        'T3_background_drift': [20262081 + i for i in range(20)],
    }
    all_cells = [s for block in cell_blocks.values() for s in block]
    exec_seeds = {
        'headroom_reps': '20262011..20262030',
        'execution_data_seed': EXEC_SEED_BASE,
        'execution_target_eval_seed': EXEC_SEED_BASE + 1,
        'execution_cell_seed_blocks': cell_blocks,
        'execution_cell_seeds': all_cells,
        'R_execution_per_target': 20,
        'n_targets': 3,
        'n_cells': len(all_cells),
        'cluster': 'replicate',
        'CI_method': '95% t interval across independent replicates (df=R-1); cluster=replicate',
        'two_runs': 'same seeds, separate processes; result JSON byte-identical; telemetry separate',
        'forbidden_old_seeds': FORBIDDEN_OLD,
        'overlap_with_forbidden': sorted(set([EXEC_SEED_BASE, EXEC_SEED_BASE + 1] + all_cells) & set(FORBIDDEN_OLD)),
        'cell_blocks_disjoint': True,
        'unique': True,
    }
    schema = {
        'schema': 'R204-M1-S2D', 'version': 'v1',
        'top_keys': ['task', 'status', 'separation', 'source_environment', 'target_environments',
                     'headroom_design', 'execution_seeds', 'comparison_family', 'multiple_testing',
                     'equivalence_audit', 'budget', 'failure_categories', 'run_shas', 'failure_category', 'verdict'],
        'per_cell_fields': ['target_env', 'replicate', 'planner', 'raw_regret', 'D_vs_baseline', 'pass'],
        'forbidden_fields': ['real_decision', 'pharmacology_claim', 'transfer_claim', 'mechanism_claim',
                             'novelty_claim', 'old_H1_verdict_change', 'real_data_result', 'target_training'],
        'headroom_required': 0.10,
        'headroom_decision_rule': 'execute only if mean baseline regret >= 0.10 (2*delta) on every target Pθ\'; '
                                  '<0.10 -> before candidate results redesign/freeze target or design_invalid: '
                                  'unreachable_gate stop',
        'headroom_stop_category': 'design_invalid: unreachable_gate',
        'failure_categories': ['design_invalid: projection', 'design_invalid: calibration',
                               'design_invalid: leakage', 'design_invalid: unreachable_gate',
                               'design_invalid: equivalence', 'design_invalid: precision_insufficient',
                               'design_invalid: two_run_mismatch', 'design_invalid: chain_mismatch',
                               'design_invalid: compute_budget_exceeded', 'no_increment', 'inconclusive'],
        'R_execution_per_target': 20,
        'n_targets': 3,
        'n_cells': len(all_cells),
        'cluster': 'replicate',
        'CI_method': '95% t interval across independent replicates (df=R-1); cluster=replicate',
        'valid_eval_rows_frozen': {'T1_scale_drift': 4096, 'T2_slope_drift': 4093, 'T3_background_drift': 4096},
        'T2_valid_eval_rows_note': 'T2 target eval valid rows=4093 (3 extreme analytic-underflow rows dropped); '
                                   'frozen; not reported as 4096',
        'no_effect_results': True, 'no_target_training': True,
        'two_run_rule': 'result JSON byte-identical; telemetry separate',
    }
    write_json(schema, SCHEMA)

    say('[5/5] write headroom_design_m1_s2d.json ...')
    out = {
        'task': 'R204-M1-S2D.1',
        'status': 'design_headroom_only_not_candidate_execution_v0_2',
        'separation': {
            'S2c_positive_result': 'synthetic known-truth planning comparison only; not real data/pharmacology/'
                                   'real decision/transfer/mechanism/novelty',
            'old_statuses': 'C216 old H1 0/16/design_invalid: projection; C217 attribution; H1b 16/16 density-only; '
                            'one-step projection withdrawn (C208): all unchanged',
            'S2d_new_prereg': 'does not modify S2c; new pre-registration for misspecification/background drift',
        },
        'source_environment': {
            'P_theta': 'c~N(0,.5²), M~N(0,.1²), d~N(0,.1²), sigma=.1+.4*sigmoid(d^T x), Y in [-2,2]^4, K=3/[.5,.3,.2]',
            'param_seed': PARAM_SEED, 'train_seed': TRAIN_SEED, 'eval_seed': EVAL_SEED,
            'X': 'N(0,I_64)', 'A': A, 'reward': {'w': [0.4, 0.3, 0.2, 0.1], 'lambda': 0.2, 'tau': 1.0},
        },
        'target_environments': {name: {'spec': TARGETS[name], 'param_seed': TARGET_PARAM_SEEDS[name],
                                       'pi0_target': 'full 4 actions uniform',
                                       'known_truth': 'analytic truncated-normal moments under target Pθ\''}
                                for name in TARGETS},
        'headroom_design': {
            'baseline': 'P_empirical_mean_source: N_train=4096 source samples per action; action-level mean; '
                        'x-independent; evaluated on target Pθ\' with independent target eval X',
            'N_train': N_TRAIN, 'N_eval': N_EVAL, 'R_reps': R_REPS, 'reps': '20262011..20262030',
            'delta': DELTA, 'headroom_required': 0.10,
            'results': results, 'all_targets_headroom_ok': all_ok,
            'main_target': main_target, 'decision': decision,
            'headroom_measured_design_time_before_candidate': True,
            'no_candidate_results_used_for_headroom': True,
            'redesign_rule': 'if any target <0.10: before candidate results redesign/freeze that target or '
                             'design_invalid: unreachable_gate stop; never lower delta/change seed/environment to rescue',
        },
        'comparison_family': comparisons,
        'multiple_testing': {'family_size': 6, 'primary': 'candidate vs P_empirical_mean_source',
                             'secondary': ['P_empirical_mean_target_adapted', 'P_max_entropy',
                                           'P_conditional_density_MC', 'P_random', 'P_softmax_expected_reward'],
                             'D': 'D_j=regret_candidate−regret_baseline_j; improvement D<0',
                             'test': 'Holm alpha=.05; one-sided lower tail', 'delta': DELTA,
                             'raw_vs_paired': 'raw regret and paired D stored separately',
                             'CI': 'per target independent replicates R=20 (60 cells total, 20 per target); '
                                   'cluster=replicate; 95% t interval (df=R-1); not planning-MDE power',
                             'R_execution_per_target': 20, 'n_targets': 3, 'n_cells': len(all_cells),
                             'cluster': 'replicate',
                             'CI_method': '95% t interval across independent replicates (df=R-1); cluster=replicate',
                             'per_target': 'six comparisons evaluated per target; primary target T1; T2/T3 secondary/'
                                           'generalization; Holm within each target; no pooled target claim'},
        'equivalence_audit': {
            'rule': 'candidate (source-trained) equal to P_empirical_mean_source/P_max_entropy/'
                    'P_conditional_density_MC by actions or analytic coverage -> equivalence/no increment',
            'no_target_training_or_tuning': True,
        },
        'execution_seeds': exec_seeds,
        'budget': {'caps': CAPS, 'compute_only': True, 'new_wells': 0,
                   'pilot_policy': 'execution requires final-implementation pilot measured and canonical timing '
                                   'frozen; this task only design-time headroom (no candidate training)'},
        'failure_categories': schema['failure_categories'],
        'stop_conditions': ['headroom<2*delta (=0.10) on any target -> before seeing candidate results: redesign/'
                            'freeze target, or design_invalid: unreachable_gate stop; do not execute',
                            'equivalence -> no increment',
                            'CI cannot exclude 0 or -delta -> inconclusive',
                            'standard method equal-budget copy/exceed -> no_increment/withdraw',
                            'caps exceeded -> compute_budget_exceeded',
                            'any failure does not change old judgments'],
        'execution_design': {
            'R_execution_per_target': 20, 'n_targets': 3, 'n_cells': len(all_cells),
            'cluster': 'replicate',
            'CI_method': '95% t interval across independent replicates (df=R-1); cluster=replicate',
            'cell_seed_blocks': cell_blocks,
            'valid_eval_rows': {k: v['valid_eval_rows_min'] for k, v in results.items()},
            'valid_eval_rows_note': 'target eval nominal rows=4096; T2=4093 valid rows frozen (3 extreme '
                                    'analytic-underflow rows dropped); not reported as 4096',
        },
        'boundaries': ['S2c positive result only synthetic known-truth; no pharmacology/real decision/transfer/'
                       'mechanism/novelty claims',
                       'candidate only source-trained; target data forbidden for training/tuning',
                       'no candidate training/planning in this task; mechanism account only; compute-only; 0 wells',
                       'no modification of old gates/judgments; no revival of stopped experiments',
                       'M1 not mixed with M2/M3; N1 not evidence; data readiness open (C203/C205/C210/C214)'],
        'no_effect_results': True, 'no_candidate_training': True, 'no_candidate_planning': True,
    }
    write_json(out, OUTJSON)
    print('headroom_design_m1_s2d_v0_2.json sha256:', sha256_file(OUTJSON))
    print('schema_m1_s2d_v0_2.json sha256:', sha256_file(SCHEMA))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
