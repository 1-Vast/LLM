#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M2-P1 formalism/identifiability arithmetic: group-moment operator model, assignment estimators,
identifiability examples, non-closure counterexample, randomization contract, synthetic truth-testbed
spec + pilot timing. DESIGN/ARITHMETIC ONLY: no effect comparison, no gain claims, no O'Neil responses.
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
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-m2-operator-prereg')
R204 = os.path.join(ROOT, 'research', '2026-10-28-deep-coupling-redesign')
A_LINE = os.path.join(ROOT, 'research', '2026-10-27-agent-cell-colearning')
R203 = os.path.join(ROOT, 'research', '2026-10-28-decision-power-scope')
N1 = os.path.join(ROOT, 'research', '2026-10-28-n1-synthetic-prereg')
AZX2 = os.path.join(ROOT, 'research', '2026-10-28-az-export-coverage', 'report_x2.md')
AZX3 = os.path.join(ROOT, 'research', '2026-10-28-az-q1-reeval', 'report_x3.md')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'formalism_M2.json')
TIMING = os.path.join(OUTDIR, 'timing_M2_pilot.json')

DELTA = 0.05
Z_80 = 2.801585
ALPHA = 0.05
SEED = 20261080


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


def main():
    t0 = time.time()
    say = lambda m: print(m, flush=True)

    say('[1/8] read-only inputs & SHA registry ...')
    inputs = {}
    for key, path in (('r204_report', os.path.join(R204, 'report.md')),
                      ('r204_brief', os.path.join(R204, 'BRIEF_R204.md')),
                      ('r204_evidence', os.path.join(R204, 'evidence_notes.md')),
                      ('errata', os.path.join(A_LINE, 'ERRATA_R201_R202.md')),
                      ('problem_decision', os.path.join(R203, 'PROBLEM_DECISION.md')),
                      ('power_scope', os.path.join(R203, 'power_scope.json')),
                      ('decision_r203_scope', os.path.join(R203, 'DECISION_R203_P1_SCOPE.md')),
                      ('n1_problem_v0_4', os.path.join(N1, 'PROBLEM_N1_v0_4.md')),
                      ('n1_design_v0_4', os.path.join(N1, 'DESIGN_N1_v0_4.md')),
                      ('az_report_x2', AZX2), ('az_report_x3', AZX3)):
        if not os.path.isfile(path):
            raise SystemExit('FATAL missing input %s: %s' % (key, path))
        inputs[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                       'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    say('    inputs registered: %d' % len(inputs))

    say('[2/8] formalization (model + assignment estimators) ...')
    formal = {
        'state_X': 'culture/cohort state including necessary history and absolute counts (not only normalized RNA '
                   'distribution; proliferation/death counts retained)',
        'phi': 'small observable function family phi(X) in R^p estimable from actual measurements (independent '
               'functional readouts + counts + pre-registered history terms); basis fixed before fitting',
        'closure_claim': 'E[phi(X_Delta) | X_0=x, a] = K_a phi(x) with action-specific K_a in R^{p x p}; this is '
                         'a declared modelling assumption to be tested on real new moments, not an identity',
        'cohort_moments_fixed_pi': 'i = independent cohort/culture; known fixed randomization pi_i(a) with equal '
                                   'starting distribution across action groups: '
                                   'V_i = sum_a pi_i(a) K_a U_i with U_i=E[phi(X_0)|i], V_i=E[phi(X_Delta)|i]',
        'cohort_moments_recorded_state_assignment': 'if assignment depends on recorded X_0, the correct estimator is '
                                                   'V_i = sum_a K_a E[1{A=a} phi(X_0) | i]; the shortcut '
                                                   'sum_a pi(a) E[phi(X_0)] is biased and forbidden',
        'action_labels': 'full action labels must be used (no aggregation/dropping to manufacture a new problem)',
        'pi_semantics': 'pi is assignment probability between cohorts/cultures, NOT within-culture cell-level free '
                        'dosing, NOT drug combination',
        'task_driven_loop': 'from measured independent function f_g fit its legal-action conditional successor; Agent '
                            'chooses starting conditions/dosing/timepoints to identify task-relevant action '
                            'directions; refit on real new moments and test closure; closed -> multi-step programs '
                            'by K products / recombination within measured functions; failure -> report which '
                            'action/timescale is not reusable; function selection/augmentation/finite-sample error '
                            'control remain open algorithm problems',
        'identifiability_scope': 'full K_a requires varying U_i/assignment support; group moments at fixed U identify '
                                 'only K_a U (or mixtures); no claim to identify all K or that mixtures beat pure '
                                 'drug groups',
        'gauge_symmetries': ['phi basis change M: K_a -> M K_a M^{-1}', 'state label/sign symmetries of chosen basis',
                             'unassigned action support -> K_a unidentifiable'],
    }
    say('    formalization frozen (X/phi/closure/V_i estimator/pi semantics)')

    say('[3/8] identifiability arithmetic ...')
    rng = np.random.default_rng(SEED + 1)
    # (a) same U: V_i = sum_a Pi_ia w_a with w_a = K_a U
    A, p = 3, 4
    U = rng.normal(size=p)
    Pi_full = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [0.5, 0.5, 0.0],
                        [0.2, 0.3, 0.5], [0.34, 0.33, 0.33]])
    Pi_mix = np.array([[0.5, 0.5, 0.0], [0.2, 0.3, 0.5], [0.34, 0.33, 0.33]])
    rank_pi_full = int(np.linalg.matrix_rank(Pi_full))
    rank_pi_mix = int(np.linalg.matrix_rank(Pi_mix))
    same_u = {'p': p, 'A': A, 'U': [rq(float(v)) for v in U],
              'design_pure_plus_mixes': {'n_groups': len(Pi_full), 'rank': rank_pi_full,
                                         'identifiable_targets': 'K_a U for each a (rank(design)=A)',
                                         'identified': rank_pi_full == A},
              'design_mixtures_only': {'n_groups': len(Pi_mix), 'rank': rank_pi_mix,
                                       'identifiable_targets': 'only rank(design) linear combos of K_a U',
                                       'identified_all_K_a_U': rank_pi_mix == A}}
    # (b) full K_a: pure action groups with U_i spanning R^p
    Gp = 24
    U_pure = rng.normal(size=(Gp, p))
    blocks = []
    for a in range(A):
        idx = [i for i in range(Gp) if i % A == a]
        for i in idx:
            # row for each output coord: (U_i^T kron I_p) vec(K_a)
            blocks.append((a, i))
    # build design on theta = vec(K_0),...,vec(K_{A-1}) of size A*p*p
    rows = []
    for a, i in blocks:
        for c in range(p):
            row = np.zeros(A * p * p)
            row[a * p * p + c * p:a * p * p + c * p + p] = U_pure[i]
            rows.append(row)
    Jp = np.array(rows)
    rank_full = int(np.linalg.matrix_rank(Jp))
    full_k = {'p': p, 'A': A, 'n_groups_with_pure_assignments': Gp,
              'parameter_dim_A_p2': A * p * p, 'rank_pure_design': rank_full,
              'identifiable_dim': rank_full,
              'condition': 'each action has >=p groups with pure assignment and U_i spanning R^p (rank(U_a)=p)',
              'pass': rank_full == A * p * p}
    # (c) mixed assignments only with same varying U: bilinear design rank
    G = 10
    U_mix = rng.normal(size=(G, p))
    Pi_mix2 = rng.dirichlet(np.ones(A), size=G)
    rows2 = []
    for i in range(G):
        for c in range(p):
            row = np.zeros(A * p * p)
            for a in range(A):
                row[a * p * p + c * p:a * p * p + c * p + p] += Pi_mix2[i, a] * U_mix[i]
            rows2.append(row)
    J2 = np.array(rows2)
    rank_mix = int(np.linalg.matrix_rank(J2))
    mixed = {'p': p, 'A': A, 'n_groups': G, 'parameter_dim_A_p2': A * p * p,
             'rank_mixed_design': rank_mix, 'nullity': A * p * p - rank_mix,
             'note': 'mixed assignments with varying U are bilinear; they can identify some directions but not '
                     'all K_a in general; needs designed support/varying U or pure-action blocks',
             'identifiable_dim': rank_mix}
    # (d) unassigned action
    unassigned = {'A': 3, 'assigned_actions': [0, 1], 'K_2_identified': False,
                  'reason': 'positivity violation: no support for action 2; K_2 unidentifiable'}
    ident = {'same_U_moment_identifiability': same_u, 'full_K_pure_randomization': full_k,
             'mixed_assignment_rank': mixed, 'unassigned_action': unassigned,
             'orthogonal_design_example': {
                 'example': 'same U: groups with pi=(1,0) and pi=(0,1) isolate K_1 U and K_2 U; a group with '
                            'pi=(.5,.5) only gives the average; two different mixes can separate K_1 U and K_2 U '
                            'but cannot identify all K, and do not guarantee mixtures beat pure groups',
                 'claim': 'separation of K_a U only; no identification of all K; no mixture-superiority claim'}}
    say('    same-U rank=%d/%d; pure fullK rank=%d/%d; mixed rank=%d/%d' % (
        rank_pi_full, A, rank_full, A * p * p, rank_mix, A * p * p))

    say('[4/8] correct vs naive assignment estimator bias ...')
    # cohort: x ~ N(0,1); assignment P(A=1|x)=sigmoid(1.5x); phi=(1,x,x^2); pi=E[sigmoid(1.5x)]
    n = 400000
    xg = rng.normal(size=n)
    logits = 1.5 * xg
    pa = 1.0 / (1.0 + np.exp(-logits))
    ag = (rng.random(n) < pa).astype(int)
    phi = np.column_stack([np.ones(n), xg, xg ** 2])
    pi_bar = float(pa.mean())
    E_group = (ag[:, None] * phi).mean(axis=0)
    naive = pi_bar * phi.mean(axis=0)
    bias = E_group - naive
    estimator = {'n_mc': n, 'assignment': 'P(A=1|x)=sigmoid(1.5x), x~N(0,1)', 'pi_bar': rq(pi_bar),
                 'E[1{A=1}phi(X0)]': [rq(float(v)) for v in E_group],
                 'pi_bar*E[phi(X0)]': [rq(float(v)) for v in naive],
                 'bias_naive_minus_correct': [rq(float(v)) for v in bias],
                 'bias_norm': rq(float(np.linalg.norm(bias))),
                 'conclusion': 'recorded-state assignment requires sum_a K_a E[1{A=a}phi(X0)]; the marginal '
                               'pi*mean shortcut is biased and forbidden'}
    say('    naive-estimator bias norm=%.4f (non-zero)' % np.linalg.norm(bias))

    say('[5/8] closure / non-closure counterexamples ...')
    # closed linear system phi=(1,x), x' = a*x + b + eps -> K_a rows: [1,0], [b,a]
    xgrid = np.linspace(-1.5, 1.5, 13)
    a_coef, b_coef = 0.7, 0.2
    phi_closed = np.column_stack([np.ones_like(xgrid), xgrid])
    target_closed = np.column_stack([np.ones_like(xgrid), a_coef * xgrid + b_coef])
    K_lin, *_ = np.linalg.lstsq(phi_closed, target_closed, rcond=None)
    resid_closed = np.linalg.norm(phi_closed @ K_lin - target_closed, ord='fro')
    # non-closed: x' = x + a + c x^2 + eps; phi=(1,x,x^2); E[x'^2] has x^3,x^4 terms
    c_non = 0.8
    sigma = 0.15
    phi_nc = np.column_stack([np.ones_like(xgrid), xgrid, xgrid ** 2])
    target_nc = np.column_stack([
        np.ones_like(xgrid),
        xgrid + a_coef + c_non * xgrid ** 2,
        (xgrid + a_coef + c_non * xgrid ** 2) ** 2 + sigma ** 2
    ])
    K_nc, *_ = np.linalg.lstsq(phi_nc, target_nc, rcond=None)
    resid_nc = float(np.linalg.norm(phi_nc @ K_nc - target_nc, ord='fro'))
    nonclosure = {
        'closed_linear_example': {'phi': '(1, x)', 'dynamics': "x' = 0.7 x + 0.2 + eps",
                                  'K_fit': [[rq(float(v)) for v in row] for row in K_lin],
                                  'closure_residual_fro': rq(resid_closed),
                                  'closed': bool(resid_closed < 1e-10)},
        'nonclosed_example': {'phi': '(1, x, x^2)', 'dynamics': "x' = x + 0.7 + 0.8 x^2 + eps",
                              'why_not_closed': 'E[x\'^2] contains x^3 and x^4 terms absent from phi',
                              'K_fit_on_grid': [[rq(float(v)) for v in row] for row in K_nc],
                              'closure_residual_fro': rq(resid_nc),
                              'closed': bool(resid_nc < 1e-8),
                              'note': 'residual non-zero on grid; a 3-function phi cannot close this nonlinearity'},
        'randomization_note': 'the closure test must be run on real new moments under recorded assignment; '
                              'the synthetic examples are arithmetic, not evidence about real biology',
    }
    say('    closed residual=%.2g; nonclosed residual=%.4f' % (resid_closed, resid_nc))

    say('[6/8] randomization/exchangeability contract ...')
    contract = {
        'requirements': [
            'pi_i(a) known, recorded before outcomes, independent of hidden cohort state given recorded history',
            'action groups have equal starting distribution after conditioning on recorded state (exchangeability)',
            'if assignment depends on recorded X0, use V_i=sum_a K_a E[1{A=a}phi(X0)|i] (no marginal shortcut)',
            'no within-culture cell-level free dosing; pi is between-cohort assignment',
            'action labels retained in full; no aggregation',
            'sister preparations exchangeable in source/handling/batch; no pseudo-pairing of same-cell trajectories',
            'counts (proliferation/death) retained; normalized RNA alone cannot distinguish count changes',
        ],
        'checks': ['recorded assignment balance table', 'exchangeability diagnostics on recorded covariates',
                   'positivity/support check per action', 'sensitivity to assignment mechanism'],
        'failure': 'design_invalid: randomization (if any contract fails, stop; no gain claim)',
    }
    say('    randomization/exchangeability contract frozen')

    say('[7/8] synthetic truth-testbed spec + timing pilot ...')
    testbed = {
        'name': 'M2_controlled_cohort_operator_testbed',
        'hidden_state': 'd=4 continuous hidden state with history term; nonlinear transition for non-closure cases',
        'actions_A': 3, 'phi_dim_p': 5, 'n_cohorts': 200, 'timepoints': 3,
        'cases': ['linear closed K_a known truth (positive control)',
                  'nonlinear non-closed example (negative control; closure must fail)',
                  'partial-support action (identifiability negative control)'],
        'identifiability_checks': ['rank of assignment design', 'pure-action blocks with U_i spanning',
                                   'recover K_a U vs full K_a conditions', 'gauge basis change'],
        'orthogonal_design_example': 'same U with pure vs soft mixes separates K_a U; not all K; no mixed-superiority',
        'randomization_check': 'recorded assignment balance and exchangeability',
        'known_K_a': 'synthetic truth K_a generated from fixed seed; never passed to methods',
        'no_effect_run': True,
    }
    rngp = np.random.default_rng(SEED + 2)

    def pilot_once(rng):
        # planning arithmetic only: build a group design and solve a small moment regression (no method effects)
        A_, p_ = 3, 5
        G_ = 60
        Pi_ = rng.dirichlet(np.ones(A_), size=G_)
        U_ = rng.normal(size=(G_, p_))
        K_truth = rng.normal(size=(A_, p_, p_))
        V_ = np.einsum('ga,aij,gj->gi', Pi_, K_truth, U_)
        # solve stack: for each group and output coord equation V_gi = sum_a Pi_ga (U_g^T kron I) vec(K_a)
        rows, rhs = [], []
        for g in range(G_):
            for c in range(p_):
                row = np.zeros(A_ * p_ * p_)
                for a in range(A_):
                    row[a * p_ * p_ + c * p_:a * p_ * p_ + c * p_ + p_] = Pi_[g, a] * U_[g]
                rows.append(row)
                rhs.append(V_[g, c])
        theta, *_ = np.linalg.lstsq(np.array(rows), np.array(rhs), rcond=None)
        return float(np.linalg.norm(theta))

    t_pilot = time.time()
    norms = []
    for r in range(10):
        norms.append(pilot_once(np.random.default_rng(SEED + 100 + r)))
    per_rep = (time.time() - t_pilot) / 10.0
    stage1_proj = per_rep * 20 * 1.2
    stage2_proj = stage1_proj * 5
    stage3_proj = stage1_proj * 20
    timing = {
        'pilot_replicates': 10, 'per_replicate_seconds': rq(per_rep, 5),
        'stage1_synthetic_projected_seconds': rq(stage1_proj, 2),
        'stage2_projected_seconds': rq(stage2_proj, 2),
        'stage3_projected_seconds': rq(stage3_proj, 2),
        'caps': {'stage1_wall_s': 600, 'stage2_wall_s': 1800, 'stage3_wall_s': 1800,
                 'cpu_s': 7200, 'memory_gb': 8},
        'compute_only': True, 'new_wells': 0,
        'note': 'planning arithmetic only: builds moment design and solves small regression to time the arithmetic; '
                'no method comparison or effect metric computed',
    }
    write_json(timing, TIMING)
    say('    pilot per-rep=%.5fs; stage1 proj=%.1fs stage2=%.1fs stage3=%.1fs' % (
        per_rep, stage1_proj, stage2_proj, stage3_proj))

    say('[8/8] analysis/endpoint planning arithmetic & stop tree ...')
    planning = {
        'primary_endpoint': 'independent functional decision utility / regret (per endpoint separate planning); '
                            'RNA/prediction/operator error are secondary only and cannot replace it',
        'delta': DELTA, 'delta_units': 'normalized independent functional utility',
        'sample_size_rule': 'paired independent functional units; n=ceil((2.801585*SD(D)/delta)^2); cluster by '
                            'independent culture/background/task [no 6,282 generic gate]',
        'ceiling_precheck': 'baseline U0/U_max: if headroom=U_max-U0 < delta -> unreachable_gate; near-ceiling -> '
                            'separate budget-to-target problem; never silently switch endpoint',
        'precision_rule': 'MDE80=2.801585*SD(D)/sqrt(n_ind); if MDE80>delta or n_available<n_req -> '
                          'precision_insufficient (not algorithm failure)',
        'secondary': ['prediction calibration', 'operator/K_a error', 'RNA error (secondary only)'],
        'stages': {
            'stage1_controlled_truth': 'synthetic known-K_a system: identifiability/closure/randomization checks; '
                                       'no gain claim; synthetic compute-only 0 wells',
            'stage2_fixed_feedback_learning': 'qualified multi-time functional data: candidate vs strong '
                                              'predictors/full-history retrain/hierarchical-GP/KoopCell/DisKO '
                                              'adaptation/TD-JEPA successor-feature adaptation/state-space-PKPD; '
                                              'same fixed feedback, same info/budget/tuning',
            'stage3_fixed_updater_acquisition': 'candidate active intervention selection vs random/GP/optimal input '
                                                'design/BATCHIE adaptation; same fixed updater and budget',
            'full_loop': 'complete closed loop: cohorts/plates/controls/failures/replicates/calibration/compute/'
                         'tuning counted; hold out program then background',
        },
        'baselines_equal_budget': ['controlled weak EDMD / system identification + optimal input design '
                                   '(equivalent strong baseline)', 'KoopCell/DisKO adaptation',
                                   'TD-JEPA/successor-feature adaptation', 'state-space/PKPD', 'hierarchical GP',
                                   'full-history retrain'],
        'stop_rules': ['standard method replicates at equal budget -> withdraw main algorithm claim (no_increment)',
                       'closure/randomization/measurement contract fails -> stop design_invalid',
                       'benefit only in RNA without independent functional decision -> withdraw',
                       'feedback/experiment cost above frozen cap -> stop',
                       'CI cannot exclude no utility -> inconclusive', 'cross-task failure -> limit to current task'],
        'data_requirements_real': [
            'multi-time functional / cohort snapshots from the same culture/background/batch with exchangeable '
            'starting distribution; dose/time/function readouts',
            'independent cultures/plate replicates; technical replicates are not independent units',
            'orthogonal functional readouts (apoptosis/caspase/target engagement/regrowth) where claimed',
            'recorded assignment pi and action labels; counts (proliferation/death) alongside RNA',
            'AZ export data dictionary/functional numeric not yet available (C203): real stage currently '
            'data_unavailable until obtained',
        ],
        'failure_tree': ['design_invalid: identifiability', 'design_invalid: randomization',
                         'design_invalid: closure', 'design_invalid: leakage',
                         'design_invalid: compute_budget_exceeded', 'design_invalid: rename_edmd',
                         'data_unavailable', 'unreachable_gate', 'precision_insufficient',
                         'no_increment', 'inconclusive'],
    }
    say('    endpoint/baseline/stop tree frozen')

    out = {
        'task': 'R204-M2-P1',
        'status': 'preregistration_design_only_no_effect_results',
        'inputs': inputs,
        'formalization': formal,
        'identifiability': ident,
        'assignment_estimator_bias': estimator,
        'closure_nonclosure': nonclosure,
        'randomization_contract': contract,
        'synthetic_testbed': testbed,
        'planning_endpoints': planning,
        'baselines': planning['baselines_equal_budget'],
        'failure_categories': planning['failure_tree'],
        'budget': {'stage1_compute_only': True, 'stage1_new_wells': 0,
                   'stage1_wall_s': 600, 'stage2_wall_s': 1800, 'stage3_wall_s': 1800,
                   'cpu_cap_s': 7200, 'memory_cap_gb': 8,
                   'timing_file': 'timing_M2_pilot.json',
                   'real_stage_data': 'required multi-time functional resource; currently data_unavailable'},
        'boundaries': ['mechanism account only; synthetic compute-only in stage 1; no effect comparison/gain claim',
                       'fixed-phi linear closure is directly covered by controlled weak EDMD/system identification + '
                       'optimal input design; if equal-budget replication -> withdraw main algorithm claim',
                       'KoopCell/DisKO/TD-JEPA/BATCHIE cover parts; no novelty claim',
                       'no biology/mechanism/transfer/real decision benefit/novelty claims; no code promotion',
                       'no modification of old gates/judgments; no revival of stopped experiments; 0 wells'],
        'no_effect_results': True,
        'log_milestones': ['formalism frozen', 'identifiability/estimator arithmetic', 'closure counterexamples',
                           'randomization contract', 'testbed spec + pilot timing', 'endpoint/baseline/stop tree'],
    }
    write_json(out, OUTJSON)
    print('formalism_M2.json sha256:', sha256_file(OUTJSON))
    print('timing_M2_pilot.json sha256:', sha256_file(TIMING))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
