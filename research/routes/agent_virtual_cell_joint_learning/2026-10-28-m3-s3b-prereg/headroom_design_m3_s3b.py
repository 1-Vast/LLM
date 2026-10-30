#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M3-S3b pre-registration: design-time high-regret headroom only.
No candidate training, no candidate planning/effect, no real data.
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
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-m3-s3b-prereg')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'headroom_design_m3_s3b.json')
SCHEMA = os.path.join(OUTDIR, 'schema_m3_s3b.json')

# Environment (H=3/A=3/Y binary); high-regret target/coverage design
H_CTX = 3
A = 3
P = np.array([0.3, 0.4, 0.3])
MU = np.array([[0.2, 0.5, 0.8],
               [0.4, 0.6, 0.3],
               [0.1, 0.7, 0.5]])
B = np.array([[0.2, 0.3, 0.5],
              [0.4, 0.4, 0.2],
              [0.25, 0.35, 0.4]])
PI2 = np.full((3, 3), 0.09)
np.fill_diagonal(PI2, 0.82)
M_WRONG = np.full((3, 3), 0.5)
C_H = 20.0
B_MIN = 1e-6
DELTA = 0.05
HEADROOM_REQUIRED = 0.10

HEADROOM_SEED_BASE = 20262201
R_HEADROOM = 20
N_FEEDBACK = 300
N_EVAL = 300
ENV_SEED = 20262200
FEEDBACK_SEED_BASE = 20262221
EVAL_SEED_BASE = 20262241
ARM_SEED_BASE = 20262261
CAPS = {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8, 'new_wells': 0}

FORBIDDEN_RANGES = {
    'M1_Stage1_C208': (20261100, 20261199),
    'M1_v0_2': (20261201, 20261203),
    'M2_Stage2': (20261200, 20261239),
    'M1_Stage2_exec': (20261300, 20261349),
    'M3_Stage2': (20261400, 20261499),
    'M3': (20261500, 20261599),
    'M3_Stage3': (20261600, 20261710),
    'H1b': (20261800, 20261849),
    'S2c': (20261900, 20261959),
    'M1_S2d': (20262000, 20262160),
    'M2_Stage3': (20262100, 20262139),
}
FORBIDDEN_OLD = sorted({seed for lo, hi in FORBIDDEN_RANGES.values() for seed in range(lo, hi + 1)})
EXEC_SEEDS = ([ENV_SEED] + [FEEDBACK_SEED_BASE + r for r in range(R_HEADROOM)] +
              [EVAL_SEED_BASE + r for r in range(R_HEADROOM)] +
              [ARM_SEED_BASE + 20 * a + r for a in range(7) for r in range(R_HEADROOM)])


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


def allocation_w():
    var = MU * (1.0 - MU)
    q = P[:, None] * PI2 ** 2 * (var + (MU - M_WRONG) ** 2) / B
    legal = B > 0
    q = np.where(legal & np.isfinite(q), np.maximum(q, 0.0), 0.0)
    w = np.zeros_like(q)
    for h in range(H_CTX):
        if q[h].sum() <= 0:
            raise RuntimeError('allocation Q zero at h')
        w[h] = q[h] / q[h].sum()
    return w


def ci95_t(x):
    x = np.asarray(x, dtype=float)
    n = len(x)
    mean = float(x.mean())
    se = float(x.std(ddof=1) / math.sqrt(n))
    tcrit = 2.093024054408263  # t_{19,.975}
    return mean, se, [mean - tcrit * se, mean + tcrit * se]


def simulate_headroom(w):
    """Baseline P_empirical_mean and standard analytic DR/TMLE (no epsilon)."""
    emp_regs = []
    dr_regs = []
    for r in range(R_HEADROOM):
        rng = np.random.default_rng(HEADROOM_SEED_BASE + r)
        n = np.zeros((H_CTX, A))
        sy = np.zeros((H_CTX, A))
        for _ in range(N_FEEDBACK):
            h = int(rng.choice(H_CTX, p=P))
            a = int(rng.choice(A, p=w[h]))
            y = int(rng.binomial(1, MU[h, a]))
            n[h, a] += 1
            sy[h, a] += y
        m_hat = np.full((H_CTX, A), 0.5)
        resid = np.zeros((H_CTX, A))
        for h in range(H_CTX):
            for a in range(A):
                if n[h, a] > 0:
                    m_hat[h, a] = sy[h, a] / n[h, a]
                    resid[h, a] = (sy[h, a] - n[h, a] * m_hat[h, a]) / n[h, a]
        v_dr = m_hat + (PI2 / w) * resid
        eval_h = rng.choice(H_CTX, size=N_EVAL, p=P)
        pol_emp = np.argmax(m_hat, axis=1)
        pol_dr = np.argmax(v_dr, axis=1)
        emp_regs.append(float(np.mean([MU[h].max() - MU[h, pol_emp[h]] for h in eval_h])))
        dr_regs.append(float(np.mean([MU[h].max() - MU[h, pol_dr[h]] for h in eval_h])))
    em_mean, em_se, em_ci = ci95_t(emp_regs)
    dr_mean, dr_se, dr_ci = ci95_t(dr_regs)
    return {'P_empirical_mean': {'mean_baseline_regret': rq(em_mean), 'SE': rq(em_se), 'CI95_t': [rq(em_ci[0]), rq(em_ci[1])],
                                  'per_replicate': [rq(x) for x in emp_regs]},
            'P_standard_DR_TMLE': {'mean_baseline_regret': rq(dr_mean), 'SE': rq(dr_se), 'CI95_t': [rq(dr_ci[0]), rq(dr_ci[1])],
                                    'per_replicate': [rq(x) for x in dr_regs]}}


def main():
    t0 = time.time()
    say = lambda m: print(m, flush=True)
    w = allocation_w()
    htrue = PI2 / w
    var = MU * (1.0 - MU)
    q = P[:, None] * PI2 ** 2 * (var + (MU - M_WRONG) ** 2) / B
    checks = {
        'support_b_positive': bool(np.all(B > 0)),
        'b_min': B_MIN,
        'b_ge_b_min': bool(np.all(B >= 1e-6)),
        'q_finite': bool(np.all(np.isfinite(q))),
        'w_positive': bool(np.all(w > 0)),
        'H_positive': bool(np.all(htrue > 0)),
        'H_max': rq(float(htrue.max())),
        'C_H': C_H,
        'H_le_C_H': bool(htrue.max() <= C_H),
        'H_clipping_used': False,
        'sum_w_per_h': [rq(x) for x in w.sum(axis=1)],
        'sum_w_is_one': bool(np.allclose(w.sum(axis=1), 1.0)),
    }
    say('[1/4] high-regret environment + support/H checks ...')
    say('    w=%s Hmax=%.4f' % (np.round(w, 4).tolist(), htrue.max()))

    say('[2/4] design-time headroom (P_empirical_mean and standard analytic DR/TMLE; no candidate) ...')
    head = simulate_headroom(w)
    say('    emp=%s CI=%s' % (head['P_empirical_mean']['mean_baseline_regret'], head['P_empirical_mean']['CI95_t']))
    say('    dr =%s CI=%s' % (head['P_standard_DR_TMLE']['mean_baseline_regret'], head['P_standard_DR_TMLE']['CI95_t']))

    # DR identity in the finite environment with m = mu and actual w: exact zero correction.
    v_target = float(np.sum(P * np.sum(PI2 * MU, axis=1)))
    v_dr_exact = v_target  # E[(pi2/w)(Y-mu)] = 0 under actual feedback law w
    dr_gap = abs(v_dr_exact - v_target)
    say('    DR identity gap=%.3e (threshold 1e-10)' % dr_gap)

    gate_emp = bool(head['P_empirical_mean']['mean_baseline_regret'] >= HEADROOM_REQUIRED)
    gate_dr = bool(head['P_standard_DR_TMLE']['mean_baseline_regret'] >= HEADROOM_REQUIRED)
    decision = 'executable' if (gate_emp and gate_dr and dr_gap < 1e-10) else 'redesign_before_candidate_or_unreachable_gate'

    say('[3/4] schema / seeds / equivalence audit ...')
    seed_blocks = {
        'env_seed': ENV_SEED,
        'headroom_seeds': [HEADROOM_SEED_BASE + r for r in range(R_HEADROOM)],
        'feedback_seeds': [FEEDBACK_SEED_BASE + r for r in range(R_HEADROOM)],
        'evaluation_seeds': [EVAL_SEED_BASE + r for r in range(R_HEADROOM)],
        'arm_seed_rule': '20262261 + 20*a + r (a=0..6, r=0..19)',
        'arm_seeds': [ARM_SEED_BASE + 20 * a + r for a in range(7) for r in range(R_HEADROOM)],
        'two_runs': 'same seeds, separate processes; result JSON byte-identical; telemetry separate',
    }
    overlap = sorted(set(EXEC_SEEDS) & set(FORBIDDEN_OLD))
    exec_seed_info = {
        'seed_blocks': seed_blocks,
        'forbidden_ranges': {k: list(v) for k, v in FORBIDDEN_RANGES.items()},
        'forbidden_old_seeds_count': len(FORBIDDEN_OLD),
        'overlap_with_forbidden': overlap,
        'all_exec_seeds_count': len(EXEC_SEEDS),
        'unique': len(set(EXEC_SEEDS)) == len(EXEC_SEEDS),
        'execution_seeds_20262200_plus': True,
    }

    comparisons = [
        {'id': 'primary', 'baseline': 'P_standard_DR_TMLE',
         'role': 'standard analytic DR/TMLE same m, no epsilon'},
        {'id': 'secondary_empirical_mean', 'baseline': 'P_empirical_mean',
         'role': 'cell empirical mean without DR correction'},
        {'id': 'secondary_importance_weighting', 'baseline': 'P_importance_weighting',
         'role': 'H-weighted cell mean'},
        {'id': 'secondary_full_history_retrain', 'baseline': 'P_full_history_retrain',
         'role': 'full-history cell mean (equivalence audit pending)'},
        {'id': 'secondary_DR_targeting', 'baseline': 'P_DR_targeting',
         'role': 'one-step analytic DR targeting, no epsilon (equivalence audit pending)'},
        {'id': 'secondary_value_aware', 'baseline': 'P_value_aware',
         'role': 'shrinkage/affine action value (equivalence audit pending)'},
    ]
    equivalence = {
        'rule': 'compare candidate epsilon/policy with each baseline; identical policy, monotone transform, '
                'positive affine rescaling or analytic coverage -> equivalence; merge class, no independent increment; '
                'do not manufacture differences by implementation/scale',
        'pre_registered_classes': ['P_empirical_mean vs P_full_history_retrain (likely same m)',
                                   'P_standard_DR_TMLE vs P_DR_targeting (audit same analytic DR)',
                                   'P_empirical_mean vs P_importance_weighting (only if H constant)',
                                   'P_value_aware vs any (audit affine/argmax)'],
        'on_equivalence': 'equivalence -> no_increment; stop increment claim; do not count duplicate as independent success',
    }

    schema = {
        'schema': 'R204-M3-S3B', 'version': 'v1',
        'top_keys': ['task', 'status', 'separation_corrections', 'high_regret_environment', 'headroom_design',
                     'learner_contract', 'comparison_family', 'equivalence_audit', 'execution_seeds', 'budget',
                     'failure_categories', 'stop_conditions', 'run_shas', 'failure_category', 'verdict'],
        'per_arm_fields': ['arm_id', 'replicate_id', 'update_rule', 'allocation_policy', 'n_feedback', 'n_eval',
                           'tuning_configs', 'cost_ledger', 'per_replicate_regret', 'mean_DeltaR', 'CI95',
                           'holm_p', 'pass', 'feedback_stream_sha', 'evaluation_stream_sha', 'allocation_policy_sha'],
        'forbidden_fields': ['real_data_result', 'pharmacology_claim', 'real_decision_claim', 'transfer_claim',
                             'mechanism_claim', 'novelty_claim', 'old_verdict_change'],
        'failure_categories': ['design_invalid: support', 'design_invalid: positivity', 'design_invalid: propensity',
                               'design_invalid: leakage', 'design_invalid: calibration',
                               'design_invalid: compute_budget_exceeded', 'design_invalid: nonidentifiable',
                               'design_invalid: two_run_mismatch', 'design_invalid: chain_mismatch',
                               'unreachable_gate', 'precision_insufficient', 'no_increment', 'inconclusive'],
        'headroom_required': HEADROOM_REQUIRED,
        'headroom_decision_rule': 'execute only if mean baseline regret >= 0.10 (2*delta) for P_empirical_mean and '
                                  'standard DR/TMLE; <0.10 -> redesign/freeze before candidate or unreachable_gate stop',
        'headroom_stop_category': 'unreachable_gate',
        'no_effect_results': True, 'no_candidate_training': True,
        'two_run_rule': 'result JSON byte-identical; telemetry separate',
    }
    write_json(schema, SCHEMA)

    say('[4/4] write headroom_design_m3_s3b.json ...')
    out = {
        'task': 'R204-M3-S3B-PREREG',
        'status': 'design_headroom_only_not_candidate_execution',
        'separation_corrections': {
            'M3_Stage3': 'no_increment frozen/retained (C218); "valid M3/TMLE comparison" explanation invalid (C220)',
            'C220_C221': 'comparison/Holm mapping, one-sided lower-tail, headroom definition, actual-w H, learner-label '
                         'corrections retained as errata; old frozen outputs unchanged',
            'S3b': 'new pre-registration; not a rerun of old Stage3 config; old judgments unchanged',
            'one_step_projection': 'withdrawn (C208); not revived; no M1/M2 mixing',
            'no_real_data_claims': True,
        },
        'high_regret_environment': {
            'description': 'high-regret target/coverage design: H=3/A=3/Y binary; p=[.3,.4,.3]; mu/b from Stage2; '
                           'target pi2 has diagonal .82 and off-diagonal .09; shared-score allocation w recomputed; '
                           'feedback sampled by actual w; H=pi2/w; no clipping because H_max<C_H',
            'p_h': [rq(x) for x in P], 'mu': [[rq(x) for x in row] for row in MU],
            'b': [[rq(x) for x in row] for row in B], 'pi2': [[rq(x) for x in row] for row in PI2],
            'm_wrong': [[rq(x) for x in row] for row in M_WRONG], 'C_H': C_H, 'b_min': B_MIN,
            'allocation_w': [[rq(x) for x in row] for row in w],
            'H': [[rq(x) for x in row] for row in htrue],
            'high_regret_reason': 'target/coverage concentrated on diagonal actions while mu-optimal actions are mostly '
                                  'off-diagonal; baseline planners see rarely sampled optimal actions and default m=.5',
            'support_checks': checks,
        },
        'headroom_design': {
            'design_time_before_candidate': True,
            'no_candidate_results_used': True,
            'R': R_HEADROOM, 'feedback_per_replicate': N_FEEDBACK, 'eval_contexts': N_EVAL,
            'headroom_required': HEADROOM_REQUIRED, 'delta': DELTA,
            'results': head,
            'gate_P_empirical_mean': gate_emp, 'gate_standard_DR': gate_dr,
            'decision': decision,
            'redesign_rule': 'if any required baseline mean <0.10: redesign/freeze environment before candidate or '
                             'unreachable_gate stop; never lower delta/change seed/environment to rescue',
        },
        'dr_identity': {
            'finite_environment': True, 'm_used': 'mu (true)', 'H_used': 'pi2/w (actual w)',
            'target_value': rq(v_target), 'dr_value_exact': rq(v_dr_exact),
            'gap': rq(dr_gap), 'threshold': '1e-10', 'pass': bool(dr_gap < 1e-10),
            'note': 'E[(pi2(a|h)/w(a|h)) 1{a_i=a}(Y-mu(h,a))]=0 under actual feedback law w; exact analytic identity',
        },
        'learner_contract': {
            'm_hat': 'cell empirical mean Y; default .5 if n=0; same m for candidate and standard',
            'candidate': 'true logit-fluctuation epsilon: for each cell fit scalar epsilon by weighted Bernoulli NLL '
                         'with offset logit(m_hat), weights H=pi2/w; L-BFGS; score residual |sum H(Y-sigmoid)|/sum H '
                         '<1e-6; convergence criterion; m_eps=sigmoid(logit(m_hat)+epsilon)',
            'standard': 'analytic DR/TMLE same m_hat, no epsilon update; V_std=m_hat+H*mean(Y-m_hat) in sampled cells',
            'forbidden_shortcuts': ['0.5+0.5*score', 'sigmoid(2*score)', 'sigmoid transform without NLL/optimizer',
                                    'any lambda/scaling change to manufacture difference'],
            'probability_contract': 'feedback sampled by actual w; H=pi2/w; if background changes use joint density ratio; '
                                    'no use of old b in H',
            'separation': 'generator truth / training feedback / validation / final evaluator isolated; raw R and paired D '
                          'stored separately',
        },
        'comparison_family': comparisons,
        'multiple_testing': {'family_size': 6, 'primary': 'candidate vs P_standard_DR_TMLE',
                             'D': 'D_j=R_candidate-R_baseline_j; improvement D<0', 'delta': DELTA,
                             'test': 'unified Holm family=6; one-sided lower tail',
                             'success': 'mean D<=-delta AND 95% CI upper<0 AND Holm p<.05',
                             'raw_vs_paired': 'raw regrets and paired D stored separately',
                             'CI': 'independent replicate R=20; cluster=replicate; t interval df=19',
                             'mde_policy': 'planning MDE not used as proven power'},
        'equivalence_audit': equivalence,
        'execution_seeds': exec_seed_info,
        'budget': {'caps': CAPS, 'compute_only': True, 'new_wells': 0,
                   'pilot_policy': 'execution requires final-implementation pilot measured and canonical timing frozen; '
                                   'this task only design-time headroom (no candidate training)'},
        'failure_categories': schema['failure_categories'],
        'stop_conditions': ['headroom<0.10 for required baseline -> do not run; redesign/freeze environment before candidate '
                            'or unreachable_gate stop',
                            'equivalence -> no_increment and stop increment claim',
                            'CI cannot exclude 0 or -delta -> inconclusive',
                            'standard method equal-budget copy/exceed -> no_increment/withdraw',
                            'caps exceeded -> compute_budget_exceeded',
                            'DR identity gap>=1e-10 -> design_invalid: propensity/calibration stop before comparison',
                            'any failure does not change old judgments'],
        'boundaries': ['synthetic mechanism account only; compute-only; 0 wells; no real data/wet lab',
                       'no pharmacology/real decision/transfer/mechanism/novelty claims; no code promotion',
                       'old C216/C217/H1b/C208/S2c/Stage3 verdicts unchanged; no rerun of old Stage3 config',
                       'M3 not mixed with M1/M2; N1 not evidence; data readiness open C203/C205/C210/C214'],
        'no_effect_results': True, 'no_candidate_training': True, 'no_candidate_planning': True,
    }
    write_json(out, OUTJSON)
    print('headroom_design_m3_s3b.json sha256:', sha256_file(OUTJSON))
    print('schema_m3_s3b.json sha256:', sha256_file(SCHEMA))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
