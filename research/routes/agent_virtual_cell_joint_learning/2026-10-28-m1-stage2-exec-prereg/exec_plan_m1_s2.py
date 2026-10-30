#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M1-S2-EXEC-PREREG planning: frozen-chain verification, independent execution seeds, H1/H2/H3
diagnostic protocol arithmetic, G1-G6 inheritance, budget/schema/failure templates, skeleton unit tests.
PLANNING ONLY: no training, no effect comparison, no real data.
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
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-m1-stage2-exec-prereg')
M1S2 = os.path.join(ROOT, 'research', '2026-10-28-m1-stage2-prep')
M1S1 = os.path.join(ROOT, 'research', '2026-10-28-m1-stage1')
M1GEN = os.path.join(ROOT, 'research', '2026-10-28-m1-executable-gen-prereg')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'exec_plan_m1_s2.json')
SCHEMA = os.path.join(OUTDIR, 'schema_m1_s2_exec.json')

DELTA = 0.05
CAPS = {'wall_s': 1800, 'cpu_s': 7200, 'memory_gb': 8, 'new_wells': 0}

EXPECTED_CHAIN = {
    'research/2026-10-28-m1-stage2-prep/PROBLEM_M1_STAGE2_v0_2.md': '63C0C228CA8B9EE056E5AD2B5092BE2E125F5D55DC94E7121E5F603AFF029DE3',
    'research/2026-10-28-m1-stage2-prep/DESIGN_M1_STAGE2_v0_2.md': '642C3108DDE1A02A8D2A847E68F2251349D33952C5F50A0ECB0A6F128F605F68',
    'research/2026-10-28-m1-stage2-prep/stage2_m1_plan_v0_2.py': '482E254F4AD4AE0228D8A1823686A943027E6B78A07DCA9054055D84D03612F6',
    'research/2026-10-28-m1-stage2-prep/stage2_m1_plan_v0_2.json': '73B8C0251A42ED229D5B3BA6D48C367730FD6A284AB47E110E224D56399C1527',
    'research/2026-10-28-m1-stage2-prep/stage2_m1_schema_v0_2.json': '9C4DF02749AC400BADC8007C780FD2972C491AF3719687F2D87D0B3578CBC86E',
    'research/2026-10-28-m1-stage2-prep/timing_m1_stage2_prep_v0_2.json': '488C8EF606EB0F02D5B56821280A8D7C1DCA3530068A169B2A7C4671B694A379',
    'research/2026-10-28-m1-stage2-prep/report_m1_stage2_prep_v0_2.md': 'BCE5DE1116C3D43BEC96B1B7648C025100A2440F7235035A31718EAC5132C724',
    'research/2026-10-28-m1-stage2-prep/record_m1_stage2_prep_v0_2.md': 'CBA86C887E2D4BA236989BD534A03DEA33ECD88C108CB1F3E02C5F50ED42D272',
    'research/2026-10-28-m1-stage2-prep/DECISION_R204_M1_STAGE2_ACCEPT.md': '6EC860D23D2C467EB1E843D0A987168F64C215A5F02735242ECC185DAFFE334B',
    'research/2026-10-28-m1-stage1/m1_stage1.json': 'EF701C66BFEF12E518D40F1D897C4045EBB0B76FFAE9FE24375052B1382EEAFF',
    'research/2026-10-28-m1-stage1/report_m1_stage1.md': 'E3701DA80DF705054FFC859AA00DFC095C4635147EA417DFCD1B6465418A16C2',
    'research/2026-10-28-m1-executable-gen-prereg/DECISION_R204_M1_STAGE1.md': 'EEA8CE7675B9B6783844E1B71F3EF05790425A80F6AB98FF74423211041394CB',
}

# independent execution seeds (no reuse of C208/Stage1, M2Stage2/M2Stage3, M3 execution ranges)
EXEC_PARAM_SEED = 20261301
EXEC_TRAIN_SEED = 20261302
EXEC_EVAL_SEED = 20261303
H1_SEED_BASE = 20261310
H2_SEED_BASE = 20261326
H3_SEED_BASE = 20261331
REP_SEED_BASE = 20261340
N_REPS = 10
FORBIDDEN_SEEDS = {
    'C208_stage1_gen_eval': [20261112, 20261113],
    'M1_v0_2_param_train_eval': [20261201, 20261202, 20261203],
    'M2_stage2_prep_seed_range': list(range(20261200, 20261240)),
    'M2_stage3_seed_range': list(range(20262100, 20262140)),
    'M3_execution_reserved': list(range(20261500, 20261600)),
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


def logsumexp(a):
    a = np.asarray(a, dtype=float)
    m = np.max(a)
    return float(m + np.log(np.sum(np.exp(a - m))))


def sinkhorn_plan(cost, eps, max_iter=2000, tol=1e-8):
    """Tiny 4x4 Sinkhorn unit test (not a model fit); returns convergence diagnostics."""
    cost = np.asarray(cost, dtype=float)
    n, m = cost.shape
    a = np.ones(n) / n
    b = np.ones(m) / m
    f = np.zeros(n)
    g = np.zeros(m)
    for it in range(max_iter):
        f = eps * (np.log(a) - logsumexp(np.log(b)[None, :] - cost / eps)) + 0.0
        # vectorized update: f_i = eps*(log a_i - logsumexp_j((log b_j + g_j) - cost_ij/eps))
        M = (g[None, :] - cost) / eps
        f = eps * (np.log(a) - np.array([logsumexp(M[i]) for i in range(n)]))
        N = (f[:, None] - cost) / eps
        g = eps * (np.log(b) - np.array([logsumexp(N[:, j]) for j in range(m)]))
        P = np.exp((f[:, None] + g[None, :] - cost) / eps)
        row = P.sum(axis=1)
        col = P.sum(axis=0)
        err = max(float(np.max(np.abs(row - a))), float(np.max(np.abs(col - b))))
        if err <= tol:
            return {'converged': True, 'iterations': it + 1, 'max_marginal_error': rq(err)}
    return {'converged': False, 'iterations': max_iter, 'max_marginal_error': rq(err)}


def main():
    t0 = time.time()
    say = lambda m: print(m, flush=True)

    say('[1/7] verify frozen design chain + Lead acceptance ...')
    chain, mismatches = {}, {}
    for rel, expected in EXPECTED_CHAIN.items():
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            mismatches[rel] = 'missing'
            continue
        actual = sha256_file(path)
        chain[rel] = actual
        if actual != expected.upper():
            mismatches[rel] = {'expected': expected.upper(), 'actual': actual}
    chain_pass = len(mismatches) == 0
    stage1 = json.load(open(os.path.join(M1S1, 'm1_stage1.json'), encoding='utf-8'))
    stage1_pass = bool(stage1.get('failed_gates') == [] and stage1.get('no_effect_results') is True and
                       stage1['gates']['G1']['pass'] and stage1['gates']['G2']['pass'] and
                       stage1['gates']['G4']['pass'])
    b2 = stage1['B_spec_checks']['B2_maxent']
    step1_withdrawn = bool(b2.get('rename_maxent_detected') is True and b2.get('m1_increment_claimed') is False)
    say('    chain=%d files, mismatches=%d, pass=%s; Stage1 PASS=%s; B2 rename+withdrawn=%s' % (
        len(chain), len(mismatches), chain_pass, stage1_pass, step1_withdrawn))

    say('[2/7] independent execution seed plan ...')
    h1_cells = [(d, n) for d in (8, 16, 32, 64) for n in (512, 1024, 2048, 4096)]
    h1_seeds = [H1_SEED_BASE + i for i in range(len(h1_cells))]
    h2_seeds = [H2_SEED_BASE + i for i in range(5)]
    h3_seeds = [H3_SEED_BASE + i for i in range(2)]
    rep_seeds = [REP_SEED_BASE + i for i in range(N_REPS)]
    all_exec = [EXEC_PARAM_SEED, EXEC_TRAIN_SEED, EXEC_EVAL_SEED] + h1_seeds + h2_seeds + h3_seeds + rep_seeds
    forbidden_flat = []
    for v in FORBIDDEN_SEEDS.values():
        forbidden_flat.extend(v)
    overlap = sorted(set(all_exec) & set(forbidden_flat))
    seeds = {
        'param_seed': EXEC_PARAM_SEED, 'train_seed': EXEC_TRAIN_SEED, 'eval_seed': EXEC_EVAL_SEED,
        'H1_cell_seeds': h1_seeds, 'H2_epsilon_seeds': h2_seeds, 'H3_seeds': h3_seeds,
        'replicate_seeds': rep_seeds,
        'forbidden_seed_sets': FORBIDDEN_SEEDS,
        'overlap_with_forbidden': overlap,
        'unique': len(set(all_exec)) == len(all_exec),
        'two_runs': 'same seeds, separate processes; result JSON byte-identical; telemetry only in separate file',
        'no_generator_seed_reuse': True,
        'note': 'all execution seeds are 20261301+ and disjoint from C208/Stage1/M2/M3/generator seeds; no seed changes at execution',
    }
    say('    seeds=%d unique; overlap=%s' % (len(all_exec), overlap))

    say('[3/7] H1/H2/H3 diagnostic protocol freeze ...')
    h1 = {
        'status': 'planned_not_run',
        'dimension_grid': [8, 16, 32, 64],
        'dimension_rule': 'first d_X=8/16/32/64 features (fixed prefix) of the same frozen P_theta X~N(0,I_64)',
        'sample_grid': [512, 1024, 2048, 4096],
        'sample_rule': 'first N rows of the frozen train split (N ascending, fixed order); same train_seed',
        'eval_rule': 'fixed eval_N=2048, eval_seed=' + str(EXEC_EVAL_SEED),
        'metric': 'mean TV over 256-bin histogram (4 bins per Y dim) on eval',
        'tolerance_table_TV_max': {'d8': [0.12, 0.10, 0.08, 0.07], 'd16': [0.14, 0.11, 0.09, 0.08],
                                   'd32': [0.16, 0.13, 0.11, 0.10], 'd64': [0.18, 0.15, 0.13, 0.12]},
        'tolerance_order': 'columns correspond to N=[512,1024,2048,4096] in this exact order',
        'failure': 'any cell TV>tolerance -> design_invalid: projection',
    }
    h2 = {'status': 'planned_not_run', 'solver': 'log-domain Sinkhorn', 'epsilon_grid': [0.1, 0.25, 0.5, 1.0, 2.0],
          'max_iterations': 2000, 'marginal_tolerance': 1e-8,
          'convergence_rule': 'at least one epsilon reaches max row/col marginal error <=1e-8 within 2000 iterations',
          'constraints': 'action marginal=pi0; target outcome marginal=Q_g y-marginal; not another wrong target conditioning',
          'failure': 'no epsilon converges -> design_invalid: projection'}
    h3 = {'status': 'planned_not_run', 'small_case': {'d_X': 2, 'A': 2, 'Y_dim': 2, 'same_GMM_family': True},
          'oracle': 'exact truncated GMM target Q by tensor Gauss-Legendre 128 nodes/dim; exact target/action distribution',
          'metric': 'mean TV between candidate target-action distribution and exact oracle over 256 eval small-case x',
          'tolerance_TV_max': 0.05, 'failure': 'TV>0.05 -> design_invalid: projection',
          'note': 'small-case oracle only; NOT a high-dimensional exact oracle; high-dim error judged by H1'}
    say('    H1 4x4 grid/tolerance frozen; H2 5 eps/2000/1e-8; H3 small-case TV<=.05')

    say('[4/7] candidate/scope/G1-G6/baselines ...')
    candidate = {
        'name': 'C-MDN: conditional mixture density network + sample-based constrained planner',
        'kernel': 'K=3 logits + mean(4) + diagonal log-scale(4); truncated support; hidden 128, 2 layers ReLU',
        'training': 'NLL; Adam lr=1e-3, weight_decay=1e-5, batch=256, epochs=200; no target samples as labels',
        'planner': 'sample 4096 y per action; target-weighted action scores; legal action set; no one-step projection claim',
        'not_executed_here': True,
        'no_effect_claim': True,
    }
    generator = {
        'X_dim': 64, 'A': 4, 'Y_dim': 4, 'Y_box': [-2, 2],
        'P_theta': 'unique 3-component truncated GMM, diagonal covariance, conditional heteroscedastic; NO Student-t option',
        'weights': [0.5, 0.3, 0.2], 'param_seed': EXEC_PARAM_SEED, 'train_seed': EXEC_TRAIN_SEED,
        'eval_seed': EXEC_EVAL_SEED, 'train_N': 4096, 'eval_N': 2048,
        'param_shapes': {'c': [4, 3, 4], 'M': [4, 3, 4, 64], 'd': [4, 3, 64]},
        'mu': 'c_{a,k}+M_{a,k} x', 'sigma': '0.1+0.4*sigmoid(d_{a,k}^T x)',
        'truncation': 'Z(x,a)=sum_k w_k prod_j [Phi((2-mu_j)/sigma)-Phi((-2-mu_j)/sigma)]; Z>0 finite',
        'target_Q': 'Q_g proportional to pi0 P_theta exp(r_g/tau), tensor Gauss-Legendre 64 nodes/dim normalization; not Doob executable drug',
        'reward': {'w': [0.4, 0.3, 0.2, 0.1], 'lambda': 0.2, 'r_max': 0.375, 'r_min': -5.2,
                   'bounded_note': 'compact box + continuous reward -> bounded; no clipping; unbounded GMM not treated as bounded'},
    }
    gchecks = {
        'G1': 'conditional efficacy: target guidance does not alter P_theta; target samples not labels; executable R_pi keeps P(y|a)=P_theta',
        'G2': 'support/program legality',
        'G3': 'approximation/projection error (H1/H2/H3)',
        'G4': 'no leakage: evaluation independent of fit/policy selection; target samples not labels',
        'G5': 'two-run byte-identical result JSON; telemetry separate',
        'G6': 'schema first-written + caps 1800s/2h/8GB/0 wells',
        'failure_map': {'G1': 'calibration', 'G2': 'support', 'G3': 'projection', 'G4': 'leakage',
                        'G5': 'two_run_mismatch', 'G6': 'compute_budget_exceeded'},
    }
    baselines = {
        'executed_comparison': False,
        'spec_only': True,
        'required': ['B1 random MPC', 'B2 maximum-entropy control', 'B3 conditional density + Monte Carlo',
                     'B4 constrained Schrödinger bridge', 'B5 same-information Diffusion Forcing'],
        'common': 'same data/physical feedback/information set; target samples never labels; same compute cap 1800s/2h/8GB/0 wells; same tuning budget <=20 configs/method; same seeds',
        'equivalence_rule': 'standard control equal-budget copy/exceed or analytic equivalence -> rename_maxent/withdraw; not only wrong target-conditioning',
        'b2_status': 'rename_maxent_detected=true in Stage1; no M1 increment claim',
    }
    say('    candidate/generator/G1-G6/baselines frozen (B1-B5 spec only)')

    say('[5/7] budget/pilot reference/memory + skeleton unit tests ...')
    prep_timing = json.load(open(os.path.join(M1S2, 'timing_m1_stage2_prep_v0_2.json'), encoding='utf-8'))
    prep_plan = json.load(open(os.path.join(M1S2, 'stage2_m1_plan_v0_2.json'), encoding='utf-8'))
    budget = {
        'caps': CAPS, 'compute_only': True, 'new_wells': 0,
        'pilot_policy': 'execution must rerun final implementation pilot and freeze canonical timing BEFORE main runs; '
                        'documented canonical timing and JSON use the same snapshot; no telemetry in result JSON',
        'prep_timing_reference': {'file': 'timing_m1_stage2_prep_v0_2.json',
                                  'per_rep_seconds': prep_timing['per_rep_seconds'],
                                  'projected_seconds': prep_timing['projected_seconds'],
                                  'sha': EXPECTED_CHAIN['research/2026-10-28-m1-stage2-prep/timing_m1_stage2_prep_v0_2.json'],
                                  'note': 'planning/unit-test timing only; execution pilot must re-time final implementation'},
        'memory_planning_estimate_gb': prep_plan['planning']['memory_gb_estimate'],
        'memory_planning_within_cap': bool(prep_plan['planning']['memory_gb_estimate'] <= CAPS['memory_gb']),
        'projected_H1_cells': len(h1_cells), 'projected_H2_eps': 5, 'projected_H3_runs': 1,
    }
    # skeleton unit tests only: arithmetic/shape/Sinkhorn tiny; NO training/model fit
    rng = np.random.default_rng(EXEC_PARAM_SEED)
    c = rng.normal(scale=0.5, size=(4, 3, 4))
    M = rng.normal(scale=0.1, size=(4, 3, 4, 64))
    d = rng.normal(scale=0.1, size=(4, 3, 64))
    w = np.array([0.5, 0.3, 0.2])
    x = rng.normal(size=64)
    mu = c + np.einsum('akij,j->aki', M, x)
    sigma = 0.1 + 0.4 * (1.0 / (1.0 + np.exp(-np.einsum('akj,j->ak', d, x))))
    z_actions = []
    for a in range(4):
        comp = []
        for k in range(3):
            mass_k = 1.0
            for j in range(4):
                scale = sigma[a, k] * math.sqrt(2.0)
                mass_k *= 0.5 * (1.0 + math.erf((2.0 - mu[a, k, j]) / scale)) - \
                          0.5 * (1.0 + math.erf((-2.0 - mu[a, k, j]) / scale))
            comp.append(float(w[k]) * mass_k)
        z_actions.append(float(np.sum(comp)))
    z = float(np.min(z_actions))
    rng2 = np.random.default_rng(EXEC_PARAM_SEED)
    c2 = rng2.normal(scale=0.5, size=(4, 3, 4))
    sink = sinkhorn_plan(np.array([[1.0, 2.0, 3.0, 4.0], [2.0, 1.0, 2.0, 3.0],
                                   [3.0, 2.0, 1.0, 2.0], [4.0, 3.0, 2.0, 1.0]]), eps=0.5)
    checks = {
        'param_shapes': {'c': list(c.shape), 'M': list(M.shape), 'd': list(d.shape)},
        'shape_ok': bool(c.shape == (4, 3, 4) and M.shape == (4, 3, 4, 64) and d.shape == (4, 3, 64)),
        'weights_sum_one': bool(abs(float(w.sum()) - 1.0) < 1e-12),
        'truncation_mass_finite_positive': bool(math.isfinite(float(z)) and float(z) > 0),
        'reward_bounds': {'r_max': 0.375, 'r_min': -5.2,
                          'max_formula': '||w||^2/(4*lambda)=0.30/0.8',
                          'min_formula': 'w^T(-2)-lambda*||-2||^2=-5.2'},
        'seed_reproducible': bool(np.allclose(c, c2)),
        'sinkhorn_unit_test': sink,
        'H1_tolerance_shape': {'d8': len(h1['tolerance_table_TV_max']['d8']),
                               'd16': len(h1['tolerance_table_TV_max']['d16']),
                               'd32': len(h1['tolerance_table_TV_max']['d32']),
                               'd64': len(h1['tolerance_table_TV_max']['d64']),
                               'ok': all(len(h1['tolerance_table_TV_max'][k]) == 4 for k in ('d8', 'd16', 'd32', 'd64'))},
        'H2_grid_ok': bool(h2['epsilon_grid'] == [0.1, 0.25, 0.5, 1.0, 2.0]),
        'H3_small_case_ok': bool(h3['small_case'] == {'d_X': 2, 'A': 2, 'Y_dim': 2, 'same_GMM_family': True}),
        'no_training_executed': True,
    }
    all_pass = bool(checks['shape_ok'] and checks['weights_sum_one'] and checks['truncation_mass_finite_positive'] and
                    checks['seed_reproducible'] and checks['sinkhorn_unit_test']['converged'] and
                    checks['H1_tolerance_shape']['ok'] and checks['H2_grid_ok'] and checks['H3_small_case_ok'])
    say('    unit tests pass=%s; sinkhorn iters=%d; memory_est=%.4fGB' % (
        all_pass, checks['sinkhorn_unit_test']['iterations'], budget['memory_planning_estimate_gb']))

    say('[6/7] failure/stop/withdraw + schema ...')
    failures = {
        'categories': ['design_invalid: projection', 'design_invalid: support', 'design_invalid: calibration',
                       'design_invalid: leakage', 'design_invalid: compute_budget_exceeded',
                       'design_invalid: rename_maxent', 'design_invalid: two_run_mismatch',
                       'design_invalid: chain_mismatch', 'unreachable_gate', 'precision_insufficient',
                       'no_increment', 'inconclusive'],
        'stop_withdraw': [
            'B2 max-entropy equivalence and one-step projection are withdrawn in Stage1; no M1 increment shall be written',
            'H1 any cell TV > frozen tolerance -> design_invalid: projection; no threshold relaxation at execution',
            'H2 no epsilon converges within 2000 iters to 1e-8 -> design_invalid: projection',
            'H3 small-case TV > .05 -> design_invalid: projection; H3 is small-case only, not a high-dim oracle',
            'target guidance changes P_theta / target samples used as labels -> design_invalid: calibration',
            'unsupported action/program -> design_invalid: support',
            'leakage -> design_invalid: leakage; two-run mismatch -> design_invalid: two_run_mismatch',
            'chain mismatch -> design_invalid: chain_mismatch; budget exceed -> design_invalid: compute_budget_exceeded',
            'no old judgment/threshold/endpoint changes; no result-driven relaxation',
        ],
    }
    schema = {
        'schema': 'R204-M1-S2-EXEC',
        'version': 'v1',
        'top_keys': ['task', 'status', 'chain', 'seeds', 'generator', 'candidate', 'H1', 'H2', 'H3',
                     'G1_G6', 'baselines_spec', 'budget', 'run_shas', 'failure_category', 'verdict'],
        'H1_fields': ['dimension', 'N', 'train_seed', 'eval_seed', 'TV_256bin', 'tolerance', 'pass'],
        'H2_fields': ['epsilon', 'iterations', 'max_marginal_error', 'converged', 'pass'],
        'H3_fields': ['oracle_nodes_per_dim', 'eval_x_count', 'TV_candidate_oracle', 'tolerance', 'pass'],
        'forbidden_fields': ['decision_utility', 'regret', 'topk', 'method_comparison', 'effect_size',
                             'gain_claim', 'pharmacology_claim', 'real_decision_claim', 'transfer_claim',
                             'mechanism_claim', 'novelty_claim', 'real_data_result'],
        'no_effect_results': True,
        'no_training_in_prereg': True,
        'two_run_rule': 'result JSON byte-identical; telemetry only in separate timing file',
    }
    write_json(schema, SCHEMA)
    say('    failure/stop tree + schema written')

    say('[7/7] write exec_plan_m1_s2.json ...')
    out = {
        'task': 'R204-M1-S2-EXEC-PREREG',
        'status': 'preregistration_only_not_executed; no training/effect/real data',
        'chain': {'files': chain, 'mismatches': mismatches, 'pass': chain_pass,
                  'stage1_pass': stage1_pass, 'b2_rename_maxent_withdrawn': step1_withdrawn},
        'seeds': seeds,
        'generator': generator,
        'candidate': candidate,
        'H1': h1, 'H2': h2, 'H3': h3,
        'G1_G6': gchecks,
        'baselines_spec': baselines,
        'budget': budget,
        'unit_tests': checks, 'unit_tests_all_pass': all_pass,
        'failure_categories': failures['categories'],
        'stop_withdraw': failures['stop_withdraw'],
        'schema_file': 'schema_m1_s2_exec.json',
        'scope': {'stage2_diagnostics_only': True, 'no_effect': True, 'no_method_comparison': True,
                  'no_training_executed': True, 'no_real_data': True, 'stage3_not_executed': True,
                  'mechanism_account_only': True, 'new_wells': 0, 'compute_only': True},
        'boundaries': ['mechanism account only; synthetic compute-only; 0 wells',
                       'no Stage2 training/effect execution; no Stage3/real data/wet lab',
                       'no pharmacology/real decision/transfer/mechanism/novelty claims; no code promotion',
                       'no modification of old gates/judgments; no revival of stopped experiments',
                       'M1 not mixed with M2/M3; N1 not used as M1 Stage2 evidence; data readiness open (C203/C205/C210)',
                       'Stage2 execution requires separate pre-registration + independent challenge + Lead approval'],
        'frozen_inputs': EXPECTED_CHAIN,
        'no_effect_results': True,
        'no_training_or_comparison_executed': True,
        'log_milestones': ['chain + Lead acceptance verified', 'independent execution seeds allocated',
                           'H1/H2/H3 protocol frozen (tolerances written)',
                           'G1-G6 inherited; B1-B5 spec-only', 'budget/schema/failure templates frozen',
                           'skeleton unit tests/arithmetic only'],
    }
    write_json(out, OUTJSON)
    print('exec_plan_m1_s2.json sha256:', sha256_file(OUTJSON))
    print('schema_m1_s2_exec.json sha256:', sha256_file(SCHEMA))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
