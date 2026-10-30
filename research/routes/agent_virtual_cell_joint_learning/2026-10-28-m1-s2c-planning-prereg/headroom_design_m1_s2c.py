#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M1-S2C planning-value pre-registration: design-time headroom only.
Computes baseline planning regret of the empirical-mean planner under frozen Pθ.
NO candidate C-MDN training, NO candidate planning, NO effect/real data.
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
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-m1-s2c-planning-prereg')
H1B = os.path.join(ROOT, 'research', '2026-10-28-m1-stage2b-h1b-prereg')
H1BRUN = os.path.join(ROOT, 'research', '2026-10-28-m1-stage2b-h1b-run')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'headroom_design_m1_s2c.json')
SCHEMA = os.path.join(OUTDIR, 'schema_m1_s2c.json')

PARAM_SEED = 20261301
TRAIN_SEED = 20261302
EVAL_SEED = 20261303
HEADROOM_REP_SEED = 20261901
R_REPS = 20
N_TRAIN = 4096
N_EVAL = 4096
A = 4
D_MAIN = 64
D_SECOND = 16
RW = np.array([0.4, 0.3, 0.2, 0.1])
LAM = 0.2
DELTA = 0.05
CAPS = {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8, 'new_wells': 0}
EXEC_SEED_BASE = 20261921
FORBIDDEN_OLD = [20261301, 20261302, 20261303, 20261310, 20261401, 20261500, 20261601,
                 20261701, 20261801, 20261811, 20261812, 20261821]


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


def make_theta(seed=PARAM_SEED):
    rng = np.random.default_rng(seed)
    c = rng.normal(scale=0.5, size=(A, 3, 4))
    M = rng.normal(scale=0.1, size=(A, 3, 4, 64))
    d = rng.normal(scale=0.1, size=(A, 3, 64))
    w = np.array([0.5, 0.3, 0.2])
    return c, M, d, w


def _phi(z):
    return np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def _Phi(z):
    return 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))


def true_expected_reward(x, a, dim, theta):
    """Exact (high precision) E[r(y)|x,a] for truncated diagonal GMM; log-space stable moments."""
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
    """Sample r(y) with y~truncated Pθ(.|x,a)."""
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
    theta = make_theta()

    say('[1/5] read-only H1b/C222 chain (no modification) ...')
    chain = {}
    for rel in ('research/2026-10-28-m1-stage2b-h1b-run/h1b_result.json',
                'research/2026-10-28-m1-stage2b-h1b-run/report_h1b_run.md',
                'research/2026-10-28-m1-stage2b-h1b-prereg/floor_calib_h1b.json',
                'research/2026-10-28-m1-stage2-rerun/m1_stage2_rerun.json',
                'research/2026-10-28-m1-stage2-fail-diag/diag_m1_s2.json'):
        p = os.path.join(ROOT, rel)
        chain[rel] = sha256_file(p) if os.path.isfile(p) else None
    say('    chain files=%d' % len(chain))

    say('[2/5] design-time baseline headroom (frozen truth; N_train=4096 per action; independent eval X) ...')
    protocols = {
        'full': {'legal': [0, 1, 2, 3], 'pi0': [0.25, 0.25, 0.25, 0.25]},
        'constrained': {'legal': [0, 1], 'pi0': [0.5, 0.5, 0.0, 0.0]},
    }
    results = {}
    for pname, pinfo in protocols.items():
        legal = pinfo['legal']
        regs = []
        chosen = []
        for r in range(R_REPS):
            rng = np.random.default_rng(HEADROOM_REP_SEED + r)
            # baseline empirical-mean planner: N_train samples per action, action-level mean reward
            means = np.zeros(A)
            for a in legal:
                x_train = rng.normal(size=(N_TRAIN, D_MAIN))
                rr = sample_reward(x_train, a, rng, theta, D_MAIN)
                means[a] = float(rr.mean())
            best = max(legal, key=lambda a: means[a])
            chosen.append(int(best))
            # independent eval X; true expected reward analytic
            x_eval = rng.normal(size=(N_EVAL, D_MAIN))
            true = np.column_stack([true_expected_reward(x_eval, a, D_MAIN, theta) for a in range(A)])
            valid_rows = np.all(np.isfinite(true), axis=1)
            true = true[valid_rows]
            best_true = np.max(true[:, legal], axis=1)
            regret = best_true - true[:, best]
            regs.append(float(regret.mean()))
        regs = np.asarray(regs)
        mean = float(regs.mean())
        se = float(regs.std(ddof=1) / math.sqrt(R_REPS))
        ci = [mean - 2.093024054408263 * se, mean + 2.093024054408263 * se]  # t_{19,.975}
        results[pname] = {'mean_baseline_regret': rq(mean), 'SE': rq(se), 'CI95_t': [rq(ci[0]), rq(ci[1])],
                          'chosen_actions': chosen, 'n_eval': N_EVAL, 'n_train_per_action': N_TRAIN,
                          'legal_actions': legal, 'pi0': pinfo['pi0'],
                          'baseline_planner': 'P_empirical_mean (action-level empirical mean reward from N_train samples; x-independent)'}
        say('    %s: mean=%.5f CI=[%.5f,%.5f] chosen=%s' % (pname, mean, ci[0], ci[1], sorted(set(chosen))))

    say('[3/5] headroom gate (>= 2*delta = 0.10) ...')
    main_protocol = 'full' if results['full']['mean_baseline_regret'] >= 0.10 else 'constrained'
    headroom_ok = bool(results[main_protocol]['mean_baseline_regret'] >= 0.10)
    alternate_ok = bool(results['full' if main_protocol == 'constrained' else 'constrained']['mean_baseline_regret'] >= 0.10)
    if not headroom_ok:
        decision = 'redesign_before_candidate_or_unreachable_gate'
    else:
        decision = 'executable'
    say('    main=%s headroom_ok=%s decision=%s' % (main_protocol, headroom_ok, decision))

    say('[4/5] frozen comparison family / seeds / schema ...')
    comparisons = [
        {'id': 'primary', 'baseline': 'P_empirical_mean', 'role': 'standard empirical-mean planner'},
        {'id': 'secondary_max_entropy', 'baseline': 'P_max_entropy', 'role': 'max-entropy control'},
        {'id': 'secondary_conditional_density_MC', 'baseline': 'P_conditional_density_MC', 'role': 'conditional density + MC'},
        {'id': 'secondary_constrained_SB', 'baseline': 'P_constrained_SB', 'role': 'constrained Schrodinger bridge'},
        {'id': 'secondary_random', 'baseline': 'P_random', 'role': 'random planner'},
        {'id': 'secondary_softmax_expected_reward', 'baseline': 'P_softmax_expected_reward', 'role': 'softmax expected reward'},
    ]
    exec_seeds = {
        'headroom_reps': '20261901..20261920',
        'execution_data_seed': EXEC_SEED_BASE,
        'execution_eval_seed': EXEC_SEED_BASE + 1,
        'execution_cell_seeds': [EXEC_SEED_BASE + 10 + i for i in range(24)],
        'two_runs': 'same seeds, separate processes; result JSON byte-identical; telemetry separate',
        'forbidden_old_seeds': FORBIDDEN_OLD,
        'overlap_with_forbidden': sorted(set([EXEC_SEED_BASE, EXEC_SEED_BASE + 1] +
                                             [EXEC_SEED_BASE + 10 + i for i in range(24)]) & set(FORBIDDEN_OLD)),
        'unique': True,
    }
    schema = {
        'schema': 'R204-M1-S2C', 'version': 'v1',
        'top_keys': ['task', 'status', 'old_protocol_unchanged', 'frozen_environment', 'headroom_design',
                     'execution_seeds', 'comparison_family', 'multiple_testing', 'equivalence_audit',
                     'budget', 'failure_categories', 'run_shas', 'failure_category', 'verdict'],
        'per_cell_fields': ['replicate', 'planner', 'raw_regret', 'D_vs_baseline', 'pass'],
        'forbidden_fields': ['effect_size', 'real_decision', 'pharmacology_claim', 'transfer_claim',
                             'mechanism_claim', 'novelty_claim', 'old_H1_verdict_change', 'real_data_result'],
        'failure_categories': ['design_invalid: projection', 'design_invalid: calibration',
                               'design_invalid: leakage', 'design_invalid: unreachable_gate',
                               'design_invalid: equivalence', 'design_invalid: precision_insufficient',
                               'design_invalid: two_run_mismatch', 'design_invalid: chain_mismatch',
                               'design_invalid: compute_budget_exceeded', 'no_increment', 'inconclusive'],
        'old_C216_unchanged': True, 'old_C217_unchanged': True,
        'h1b_density_only': True, 'one_step_projection_still_withdrawn': True,
        'no_effect_results': True,
        'two_run_rule': 'result JSON byte-identical; telemetry separate',
    }
    write_json(schema, SCHEMA)

    say('[5/5] write headroom_design_m1_s2c.json ...')
    out = {
        'task': 'R204-M1-S2C-PREREG',
        'status': 'design_headroom_only_not_candidate_execution',
        'old_protocol_unchanged': {
            'C216_old_H1': '0/16 FAIL; design_invalid: projection unchanged',
            'C217_attribution': 'oracle finite-sample floor attribution unchanged',
            'H1b_only_density': '16/16 PASS only density-approximation measurability; not old H1 pass',
            'one_step_projection': 'still withdrawn (C208); no M1 increment claim here',
            'old_tolerances_unchanged': True,
        },
        'frozen_environment': {
            'P_theta': '3-component truncated GMM; c~N(0,.5²), M~N(0,.1²), d~N(0,.1²); '
                       'sigma=.1+.4*sigmoid(d^T x); Y in [-2,2]^4; K=3/[.5,.3,.2]',
            'param_seed': PARAM_SEED, 'train_seed': TRAIN_SEED, 'eval_seed': EVAL_SEED,
            'X': 'N(0,I_d)', 'd_main': D_MAIN, 'd_secondary': D_SECOND, 'A': A,
            'reward': {'w': [0.4, 0.3, 0.2, 0.1], 'lambda': 0.2, 'tau': 1.0,
                       'r_max': 0.375, 'r_min': -5.2},
            'pi0': {'full': '4 actions uniform', 'constrained': 'only actions {0,1}; actions 2/3 unsupported'},
            'planning_MC': 4096, 'known_truth': 'analytic truncated-normal moments (high precision); no train/validation reuse',
        },
        'headroom_design': {
            'baseline_planner': 'P_empirical_mean: action-level empirical mean reward from N_train=4096 samples per legal '
                                'action (x-independent); independent eval X',
            'N_train': N_TRAIN, 'N_eval': N_EVAL, 'R_reps': R_REPS,
            'reps': '20261901..20261920', 'delta': DELTA,
            'requirement': 'mean baseline regret >= 2*delta = 0.10',
            'results': results,
            'main_protocol': main_protocol,
            'alternate_protocol': 'full' if main_protocol == 'constrained' else 'constrained',
            'main_headroom_ok': headroom_ok,
            'alternate_headroom_ok': alternate_ok,
            'decision': decision,
            'redesign_rule': 'if <0.10: redesign/freeze environment BEFORE seeing candidate results (log choices) or '
                             'unreachable_gate stop; never lower delta/change seed to rescue',
        },
        'comparison_family': comparisons,
        'multiple_testing': {'family_size': 6, 'primary': 'candidate vs P_empirical_mean',
                             'secondary': ['P_max_entropy', 'P_conditional_density_MC', 'P_constrained_SB',
                                           'P_random', 'P_softmax_expected_reward'],
                             'D': 'D_j = regret_candidate - regret_baseline_j; improvement D<0',
                             'test': 'one-sided lower-tail; unified Holm alpha=.05',
                             'raw_vs_paired': 'raw regret and paired D stored separately',
                             'CI': 'by independent replicate R>=20; cluster=replicate; not planning-MDE power',
                             'delta': DELTA},
        'equivalence_audit': {
            'rule': 'if candidate policy/actions equal P_empirical_mean or P_max_entropy (or analytic coverage) -> '
                    'register equivalence/no_increment; do not claim increment from implementation differences',
            'comparators': ['P_empirical_mean', 'P_max_entropy'],
        },
        'execution_seeds': exec_seeds,
        'budget': {'caps': CAPS, 'compute_only': True, 'new_wells': 0,
                   'pilot_policy': 'execution requires final-implementation pilot measured and canonical timing frozen '
                                   'before main; this task only design-time headroom (no candidate training)'},
        'failure_categories': schema['failure_categories'],
        'stop_conditions': ['headroom<delta -> do not run',
                            'equivalence -> no increment',
                            'CI cannot exclude 0 or -delta -> inconclusive',
                            'standard method equal-budget copy/exceed -> no_increment/withdraw',
                            'caps exceeded -> compute_budget_exceeded',
                            'any failure does not change old judgments'],
        'boundaries': ['old C216/C217 unchanged; H1b density-only; one-step projection still withdrawn',
                       'no candidate C-MDN training/planning/effect in this task',
                       'no pharmacology/real decision/transfer/mechanism/novelty claims; no code promotion',
                       'no modification of old gates/judgments; no revival of stopped experiments',
                       'M1 not mixed with M2/M3; N1 not evidence; data readiness open (C203/C205/C210/C214)'],
        'no_effect_results': True, 'no_candidate_training': True, 'no_candidate_planning': True,
    }
    write_json(out, OUTJSON)
    print('headroom_design_m1_s2c.json sha256:', sha256_file(OUTJSON))
    print('schema_m1_s2c.json sha256:', sha256_file(SCHEMA))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
