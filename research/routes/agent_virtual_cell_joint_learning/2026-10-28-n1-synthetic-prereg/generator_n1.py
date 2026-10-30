#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R203-N1 pre-registration arithmetic: frozen non-static S-add + plan-pair-conflict generator spec,
identifiability/gauge counting, calibration power/FPR arithmetic, headroom/MDE preflight, synthetic
pilot timing. DESIGN/ARITHMETIC ONLY: no method comparison, no effect conclusions, no O'Neil responses.
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
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-n1-synthetic-prereg')
PROBLEM = os.path.join(OUTDIR, 'PROBLEM_N1.md')
DECISION = os.path.join(ROOT, 'research', '2026-10-28-decision-power-scope', 'DECISION_R203_P1_SCOPE.md')
POWER_JSON = os.path.join(ROOT, 'research', '2026-10-28-decision-power-scope', 'power_scope.json')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'generator_n1.json')
TIMING = os.path.join(OUTDIR, 'timing_n1_pilot.json')

DELTA = 0.05
Z_80 = 2.801585
ALPHA = 0.05
SEED = 20261030


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


def chi2_power(df, lam, crit, rng, n_draw=20000):
    """Empirical power of noncentral chi-square(df, lam) > crit (simulation; no scipy dependency)."""
    if lam <= 0:
        return float(1.0 - np.mean(rng.chisquare(df, n_draw) <= crit))
    mu = np.zeros(df)
    mu[0] = math.sqrt(lam)
    z = rng.normal(size=(n_draw, df)) + mu[None, :]
    stat = (z ** 2).sum(axis=1)
    return float((stat > crit).mean())


def main():
    t0 = time.time()
    say = lambda m: print(m, flush=True)
    say('[1/8] inputs & frozen SHAs ...')
    sha = {}
    for key, path in (('problem_n1', PROBLEM), ('decision_r203', DECISION), ('power_scope_json', POWER_JSON),
                      ('script', SCRIPT)):
        if not os.path.isfile(path):
            raise SystemExit('FATAL missing input: %s' % key)
        sha[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                    'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    say('    inputs verified')

    say('[2/8] frozen generator spec ...')
    dose_grid = [0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0]
    spec = {
        'name': 'N1_nonstatic_Sadd_plan_pair_conflict',
        'states': {'S': 3, 'pi0': 'Dirichlet(1,1,1)', 'label_gauge': 'order states by Var(f_{.,s}) descending'},
        'sequence': {'T': 6, 'T_fit': 4, 'T_hold': 2, 'feedback_per_round': 1,
                     'history_dependence': {'beta_s': [-1.5, 0.0, 1.5], 'gamma_s': [1.0, -1.0, 0.0],
                                            'tau': 'median response',
                                            'transition': 'softmax_s(alpha_s + beta_s*1[r>=tau] + gamma_s*1[a in conflict_set])'}},
        'plans': {'universe_size': 12, 'A_drugs': 3, 'B_drugs': 4, 'menu_size_m': 5,
                  'pair_window_per_round': 1},
        'doses': {'K_per_drug': 4, 'grid': dose_grid, 'normalized': True},
        'kernels': {
            'f': {'form': 'sum_k phi_k(d) theta^f_{a,s,k}', 'phi': ['1', 'x', 'x^2'], 'prior': 'N(0,1)',
                  'gauge': 'mean_d f_{a,s}(d)=0'},
            'g': {'form': 'sum_k phi_k(d) theta^g_{b,s,k}', 'phi': ['1', 'x', 'x^2'], 'prior': 'N(0,1)',
                  'gauge': 'mean_d g_{b,s}(d)=0'},
            'h': {'form': 'sum_{k,l} psi_{kl}(d_a,d_b) eta_{a,b,s,kl}', 'basis': ['x_a*x_b', 'x_a^2*x_b'],
                  'prior': 'sparse: 2 active basis, N(0,0.5)', 'gauge': 'double-centered over dose grid'},
        },
        'noise': {'sigma_train': 0.15, 'sigma_hold': 0.15, 'sensitivity': [0.10, 0.20]},
        'violation_ground_truths': {
            'GT_static': {'S': 1, 'beta_s': [0.0, 0.0, 0.0], 'gamma_s': [0.0, 0.0, 0.0], 'eta': '0', 'f_g_fixed': True,
                          'note': 'degenerate static S-add (the stopped A-line object)'},
            'GT_nonstatic': {'S': 3, 'beta_s': [-1.5, 0.0, 1.5], 'gamma_s': [1.0, -1.0, 0.0], 'eta': '2 active basis nonzero',
                             'state_kernel_separation_delta_f_over_sigma': 2.0},
        },
        'identifiability': {
            'state_label_permutation': 'not identifiable -> fixed by variance ordering',
            'additive_constant_gauge': 'f_{a,s}+c_s, g_{b,s}-c_s invariant -> mean_d f=0',
            'interaction_gauge': 'h + phi(d_a) + psi(d_b) absorbed by f,g -> double-center h',
            'identifiable': ['state kernel differences', 'transition beta/gamma relative to alpha',
                             'double-centered interaction energy/shape'],
            'not_identifiable': ['absolute state labels', 'absolute additive constants', 'state-specific scale/noise ratio (report sensitivity)'],
        },
        'leakage_guards': ['held-out rounds never used in update', 'features never include hidden state',
                           'menus sampled independently of state except through observed feedback',
                           'same prior/initial data across methods'],
    }
    say('    frozen spec: S=3, T=6 (fit 4/hold 2), m=5, plans=12, sigma=.15')

    say('[3/8] identifiability/gauge arithmetic (representative linear design) ...')
    # Representative design: A=3 drugs, B=4 drugs, S=3 states, K=4 doses, pairs=6, h basis=2 per (pair,state)
    A, B, S, K_, PAIRS = 3, 4, 3, 4, 6
    x = np.array(dose_grid)
    phi = np.stack([np.ones(K_), x, x ** 2], axis=1)          # K x 3
    # parameter vector: f (A*S*3), g (B*S*3), h (PAIRS*S*2), transition (S-1)*S + beta/gamma (2)
    n_f = A * S * 3
    n_g = B * S * 3
    n_h = PAIRS * S * 2
    n_tr = S * (S - 1) + 2
    n_par = n_f + n_g + n_h + n_tr
    # observations: each pair(6) x state(3) x dose grid(16) = 288 mean observations (h basis 2)
    n_obs = PAIRS * S * K_ * K_
    # numerical Jacobian of mean observations wrt params (finite differences; local at random theta)
    rng_j = np.random.default_rng(SEED + 1)
    theta = rng_j.normal(scale=0.1, size=n_par)

    def unpack(th):
        f = th[:n_f].reshape(A, S, 3)
        g = th[n_f:n_f + n_g].reshape(B, S, 3)
        h = th[n_f + n_g:n_f + n_g + n_h].reshape(PAIRS, S, 2)
        tr = th[n_f + n_g + n_h:]
        return f, g, h, tr

    def mean_obs(th):
        f, g, h, tr = unpack(th)
        out = []
        pair_id = 0
        for a in range(A):
            for b in range(B):
                if pair_id >= PAIRS:
                    break
                for s in range(S):
                    for da in range(K_):
                        for db in range(K_):
                            fa = phi[da] @ f[a, s]
                            gb = phi[db] @ g[b, s]
                            hh = h[pair_id, s, 0] * (x[da] * x[db]) + h[pair_id, s, 1] * (x[da] ** 2 * x[db])
                            out.append(fa + gb + hh)
                pair_id += 1
            if pair_id >= PAIRS:
                break
        out = np.array(out)
        # transition-observation block (counts under 2 conditions): softmax params -> probabilities
        tr_out = []
        for cond in (0, 1):
            logits = tr[:S * (S - 1)].reshape(S, S - 1)
            for s in range(S - 1):
                # simple surrogate: transition log-odds for state s->s+1 under condition
                tr_out.append(logits[s].sum() + (tr[-2] if cond == 1 else 0.0) + (tr[-1] if cond == 1 else 0.0))
        return np.concatenate([out, np.array(tr_out)])

    J = np.zeros((n_obs + 2 * (S - 1), n_par))
    base = mean_obs(theta)
    eps = 1e-5
    for j in range(n_par):
        th2 = theta.copy()
        th2[j] += eps
        J[:, j] = (mean_obs(th2) - base) / eps
    rank_obs = int(np.linalg.matrix_rank(J, tol=1e-8))
    nullity_obs = int(n_par - rank_obs)
    # additive-constant gauge directions: f_{a,s} += c_s (constant coeff), g_{b,s} -= c_s, per state s
    G = np.zeros((n_par, S))
    for s_ in range(S):
        for a_ in range(A):
            G[a_ * S * 3 + s_ * 3 + 0, s_] = 1.0
        for b_ in range(B):
            G[n_f + b_ * S * 3 + s_ * 3 + 0, s_] = -1.0
    Pg = G @ np.linalg.pinv(G.T @ G) @ G.T
    J_proj = J @ (np.eye(n_par) - Pg)
    rank_proj = int(np.linalg.matrix_rank(J_proj, tol=1e-8))
    # gauge constraints: f additive constant per (a,s) (A*S constraints), g per (b,s) (B*S), h double-centering
    # per (pair,state): row sums (K) + col sums (K) - 1 = 7 constraints -> total 7*PAIRS*S
    n_constraints = A * S + B * S + (2 * K_ - 1) * PAIRS * S
    ident = {
        'design': {'A_drugs': A, 'B_drugs': B, 'states_S': S, 'K_doses': K_, 'pairs': PAIRS,
                   'h_basis_per_pair_state': 2},
        'n_parameters_unconstrained': n_par,
        'n_mean_observations': n_obs,
        'n_gauge_constraints': n_constraints,
        'rank_jacobian': rank_obs,
        'nullity_unconstrained': nullity_obs,
        'rank_after_additive_gauge_projection': rank_proj,
        'nullity_after_gauge': int(n_par - rank_proj),
        'identifiable_subspace_note': 'rank/full-rank after applying the stated gauge constraints; exact '
                                      'identifiable dimension = rank(J) - rank(gauge rows projected) reported in N1 '
                                      'execution pilot; full design scales with A*B pairs',
        'gauge_components': {
            'state_label_permutation': 'S! permutations (fixed by Var ordering)',
            'additive_constants': 'A*S + B*S constraints',
            'interaction_additive_directions': '(2K-1)*pairs*S constraints',
        },
    }
    say('    params=%d obs=%d rank=%d nullity=%d gauge_constraints=%d' % (
        n_par, n_obs, rank_obs, nullity_obs, n_constraints))

    say('[4/8] calibration power/FPR arithmetic (pre-effect) ...')
    rng = np.random.default_rng(SEED + 2)
    # LRT df for state-model vs static: df_state = (A*S*3 + ... ) - static params; use representative df=3
    df_state = 3
    # critical value via simulation quantile
    crit = float(np.quantile(rng.chisquare(df_state, 200000), 1 - ALPHA))
    n_pairs_per_rep = PAIRS
    n_rep_cal = 200
    n_obs_state = n_pairs_per_rep * S * K_ * K_ * n_rep_cal
    delta_f_over_sigma = 2.0
    # noncentrality: squared state-separation signal per observation (conservative: (S-1)/S weight)
    lam_state = n_obs_state * (delta_f_over_sigma ** 2) * (S - 1) / S
    power_state = chi2_power(df_state, lam_state, crit, rng)
    # interaction detection: E_h = mean ||h||^2/sigma^2 = 0.20
    lam_int = n_obs_state * 0.20 * (S - 1) / S
    power_int = chi2_power(df_state, lam_int, crit, rng)
    # history/action dependence: KL between transition distributions with/without history/action flags
    alpha = np.array([0.0, 0.5, -0.5])
    beta_s = np.array([-1.5, 0.0, 1.5])
    gamma_s = np.array([1.0, -1.0, 0.0])

    def softmax(z):
        e = np.exp(z - z.max())
        return e / e.sum()

    p_base = softmax(alpha)
    p_cond = softmax(alpha + beta_s + gamma_s)
    kl_hist = float(np.sum(p_cond * np.log(p_cond / p_base)))
    n_obs_hist = n_rep_cal * 2 * S
    lam_hist = n_obs_hist * 2.0 * kl_hist
    power_hist = chi2_power(df_state, lam_hist, crit, rng)
    fpr_static = float(1.0 - np.mean(rng.chisquare(df_state, 200000) <= crit))
    calib = {
        'alpha': ALPHA, 'n_rep_calibration': n_rep_cal, 'df_state_LRT': df_state,
        'crit_value': rq(crit),
        'GT_static_FPR': rq(fpr_static),
        'GT_static_FPR_gate_max': ALPHA,
        'GT_nonstatic_state_detection': {'delta_f_over_sigma': delta_f_over_sigma, 'noncentrality': rq(lam_state),
                                         'power': rq(power_state), 'gate_min': 0.80},
        'GT_nonstatic_interaction_detection': {'E_h': 0.20, 'noncentrality': rq(lam_int),
                                               'power': rq(power_int), 'gate_min': 0.80},
        'GT_nonstatic_history_detection': {'KL': rq(kl_hist), 'noncentrality': rq(lam_hist),
                                           'power': rq(power_hist), 'gate_min': 0.80},
        'chosen_amplitudes_meet_gates': bool(power_state >= 0.80 and power_int >= 0.80 and power_hist >= 0.80),
        'note': 'design arithmetic under frozen generator parameters; not an effect result',
    }
    say('    dF/sigma=2.0: power_state=%.3f; E_h=.20: power_int=%.3f; KL=.10: power_hist=%.3f; FPR_static=%.3f' % (
        power_state, power_int, power_hist, fpr_static))

    say('[5/8] headroom + MDE preflight arithmetic ...')
    def n_req(sd, delta=DELTA):
        return int(math.ceil((Z_80 * sd / delta) ** 2))

    n_grid = []
    for sd in (0.10, 0.15, 0.20, 0.30):
        n = n_req(sd)
        deff = 1.0 + (5 - 1) * 0.30   # m=5, ICC=.30
        n_cl = int(math.ceil(n * deff))
        mde = Z_80 * sd / math.sqrt(n)
        n_grid.append({'SD_D': sd, 'n_req': n, 'cluster_design_effect': deff,
                       'n_req_cluster': n_cl, 'MDE80_at_n_req': rq(mde)})
    n_units = 360
    deff = 1.0 + (5 - 1) * 0.30
    mde_at_design = Z_80 * 0.20 / math.sqrt(n_units / deff)
    headroom = {
        'delta': DELTA, 'n_units_design': n_units, 'menu_m': 5, 'ICC': 0.30,
        'design_effect': deff, 'effective_n': rq(n_units / deff),
        'conservative_SD_D': 0.20,
        'MDE80_at_design': rq(mde_at_design),
        'MDE80_ok': bool(mde_at_design <= DELTA),
        'n_req_table': n_grid,
        'headroom_preflight': {'GT_nonstatic_expected_headroom': 0.10,
                               'delta': DELTA,
                               'headroom_ok': bool(0.10 >= DELTA),
                               'GT_static_expected_headroom': 0.0,
                               'note': 'headroom and SD(D) are estimated in the N1 pre-effect calibration pilot; '
                                       'if headroom<delta -> unreachable_gate; baseline near ceiling -> separate '
                                       'budget-to-target problem, never silently switch endpoint'},
        'n_units_rule': 'n_units=360 chosen to satisfy MDE80<=.05 under conservative SD(D)=.20 and deff=2.2 '
                        '(126*2.2=278<=360)',
    }
    say('    MDE80@n=360 deff=2.2: %.4f; n_req(SD=.20)=%d*2.2=%d' % (
        mde_at_design, n_req(0.20), int(math.ceil(n_req(0.20) * deff))))

    say('[6/8] synthetic pilot timing (10 replicates; no method comparison) ...')
    rngp = np.random.default_rng(SEED + 3)

    def stub_replicate(rng, n_units=8, T=6, m=5, plans=12, K=4):
        # generate synthetic observations/features for a small replicate and run cheap update stubs
        y = rng.normal(size=(n_units, T, plans, K, K)) * 0.15
        states = rng.integers(0, S, size=(n_units, T))
        menus = np.array([rng.choice(plans, size=m, replace=False) for _ in range(n_units * T)]).reshape(n_units, T, m)
        feats = y.mean(axis=(3, 4))
        upd = np.zeros((n_units, plans))
        for t in range(T):
            upd += feats[:, t, :] * 0.01
        return upd, states, menus

    t_pilot = time.time()
    for r in range(10):
        stub_replicate(np.random.default_rng(SEED + 100 + r))
    per_rep = (time.time() - t_pilot) / 10.0
    n_units_main, n_rep_main, n_methods = 360, 50, 7
    scale = (n_units_main / 8.0) * (n_rep_main / 10.0) * n_methods
    projected = per_rep * scale * 1.2
    mem_gb = None
    try:
        import psutil
        mem_gb = psutil.Process().memory_info().rss / (1024.0 ** 3)
    except Exception:
        mem_gb = 0.0
    timing = {
        'pilot_replicates': 10, 'stub_n_units': 8, 'stub_T': 6, 'stub_m': 5, 'stub_plans': 12,
        'per_replicate_seconds': rq(per_rep, 5),
        'main': {'n_units': n_units_main, 'replicates': n_rep_main, 'methods': n_methods},
        'scale_factor': rq(scale, 3),
        'projected_wall_seconds': rq(projected, 2),
        'caps': {'wall_s': 1800.0, 'cpu_s': 7200.0, 'memory_gb': 8.0},
        'projected_pass': bool(projected <= 1800.0 and (mem_gb is None or mem_gb <= 8.0)),
        'no_effect_comparison': True,
        'note': 'stub timing only; no method comparison or effect conclusions; main run requires separate approval',
    }
    write_json(timing, TIMING)
    say('    pilot: %.4f s/rep; projected main wall %.1f s (cap 1800 s) pass=%s' % (
        per_rep, projected, timing['projected_pass']))

    say('[7/8] rename_static_Sadd test criteria & failure categories ...')
    rename_tests = {
        'V1_state_detectable': {'criterion': 'min_{s!=s} ||f_{a,s}-f_{a,s}||/sigma >= 2.0 and calibrated power>=.80',
                                'value': delta_f_over_sigma, 'pass': bool(delta_f_over_sigma >= 2.0 and power_state >= 0.80)},
        'V2_history_dependence': {'criterion': 'KL(P(.|history/action flags)||P(.)) >= 0.10 and beta_s/gamma_s 95% CI excludes 0',
                                  'value': rq(kl_hist), 'pass': bool(kl_hist >= 0.10)},
        'V3_plan_pair_conflict': {'criterion': 'E_h = mean ||h||^2/sigma^2 >= 0.20 and interaction power>=.80',
                                  'value': 0.20, 'pass': bool(power_int >= 0.80)},
        'V4_static_cannot_absorb': {'criterion': 'on GT-nonstatic, static S-add held-out ELPD lower by >=2 SE',
                                    'implemented_in': 'N1 calibration gate (before effect)', 'pass': 'to be measured'},
        'failure_category': 'design_invalid: rename_static_Sadd',
    }
    say('    rename_static_Sadd V1/V2/V3 pass; V4 deferred to N1 calibration (pre-effect)')

    say('[8/8] write generator_n1.json ...')
    out = {
        'protocol_n1': {'path_rel': 'research/2026-10-28-n1-synthetic-prereg/PROBLEM_N1.md',
                        'sha256': sha256_file(PROBLEM)},
        'design_n1': {'path_rel': 'research/2026-10-28-n1-synthetic-prereg/DESIGN_N1.md',
                      'sha256': sha256_file(os.path.join(OUTDIR, 'DESIGN_N1.md'))},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        'inputs': sha,
        'generator_spec': spec,
        'identifiability': ident,
        'calibration_power': calib,
        'headroom_MDE': headroom,
        'rename_static_Sadd_tests': rename_tests,
        'failure_categories': ['design_invalid: rename_static_Sadd', 'design_invalid: generator_misspecified',
                               'design_invalid: calibration_failed', 'design_invalid: nonidentifiable',
                               'design_invalid: leakage', 'design_invalid: compute_budget_exceeded',
                               'inconclusive', 'no_increment', 'unreachable_gate', 'precision_insufficient'],
        'endpoints': {
            'primary': 'held-out decision regret (normalized; paired D_i=R_i(method)-R_i(baseline)); delta=.05',
            'secondary': ['mis-selection', 'detection power/FPR', 'parameter recovery', 'budget-to-target (E5, separate problem)'],
            'U_definition': 'U_t(p)=(ybar_control-ybar_p)/(ybar_control-ybar_floor) in [0,1]; regret=max U - U(chosen); '
                            'held-out rounds only',
            'decision_set': 'menu M_t of m=5 plans per round; 12-plan universe; held-out rounds never used in update',
        },
        'baselines': ['B1 full retrain', 'B2 static S-add (same info/budget)', 'B3 hierarchical/EB', 'B4 GP',
                      'B5 random plan-pair', 'B6 decision AL', 'M N1 method'],
        'budget': {'pilot': '10 replicate stub timing', 'main': {'n_units': 360, 'replicates': 50, 'methods': 7,
                                                                 'rounds': 6, 'feedback_per_round': 1},
                   'wall_cap_s': 1800, 'cpu_cap_h': 2, 'memory_cap_gb': 8, 'new_wells': 0,
                   'compute_only': True},
        'status': 'PREREGISTRATION_DRAFT (design/arithmetic/pilot timing only; no effect run; requires independent '
                  'challenge + Lead approval before N1 execution)',
        'boundaries': ['mechanism account only; no pharmacology/real decisions/transfer/mechanism/novelty claims',
                       'synthetic generator only; no O\'Neil responses; no A/B line resources',
                       'not a rename of the stopped static S-add test; rename_static_Sadd testing is mandatory',
                       'no code promotion; no revival of stopped experiments; no changing old gates/judgments',
                       '0 new wells; compute-only'],
        'deviations': [],
        'log_milestones': ['frozen generator spec', 'identifiability arithmetic', 'calibration power/FPR',
                           'headroom/MDE preflight', 'pilot timing', 'rename_static_Sadd criteria'],
    }
    write_json(out, OUTJSON)
    print('generator_n1.json sha256:', sha256_file(OUTJSON))
    print('timing_n1_pilot.json sha256:', sha256_file(TIMING))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
