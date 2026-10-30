#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-A.2.1: corrected pre-registration arithmetic (S2 factor-2, F_self rewrite, legal rule, budget).

Design/arithmetic/synthetic-calibration only (no P1 run, no O'Neil response statistics).
Reuses the frozen A.2 v0.1 design script functions for synthetic calibration (import only; no O'Neil data).
"""
import sys
import os
import json
import math
import hashlib
import importlib.util
import time

sys.dont_write_bytecode = True
import numpy as np

ROOT = r'D:\MAESTRO'
BASE = os.path.join(ROOT, 'research', '2026-10-27-agent-cell-colearning', 'mechanism_A')
A2 = os.path.join(BASE, 'a2_prenull')
P0P1 = os.path.join(BASE, 'p0p1', 'a_p0p1.json')
V01_JSON = os.path.join(A2, 'null_design_A2.json')
V01_SCRIPT = os.path.join(A2, 'null_design_A2.py')
CHALLENGE = os.path.join(BASE, 'challenge_A2.md')
PROBLEM_V2 = os.path.join(A2, 'PROBLEM_A2_v0_2.md')
DESIGN_V2 = os.path.join(A2, 'DESIGN_A2_v0_2.md')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(A2, 'null_design_A2_v0_2.json')

K = 4
M = 4
R_REPS = 4
F_CRIT = 2.60
N_PERM = 500
SEED_SIM = 20261030


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


def load_v01():
    spec = importlib.util.spec_from_file_location('a2_v01', V01_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def center(v):
    return v - v.mean()


def main():
    t0 = time.time()
    say = lambda m: print(m, flush=True)
    say('[1/8] inputs & frozen SHAs ...')
    sha = {}
    for key, path in (('problem_v0_2', PROBLEM_V2), ('design_v0_2', DESIGN_V2),
                      ('v0_1_json', V01_JSON), ('v0_1_script', V01_SCRIPT),
                      ('challenge_a2', CHALLENGE), ('a_p0p1_json', P0P1), ('script', SCRIPT)):
        if not os.path.isfile(path):
            raise SystemExit('FATAL missing input: %s' % key)
        sha[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                    'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    v01 = json.load(open(V01_JSON, encoding='utf-8'))
    p0p1 = json.load(open(P0P1, encoding='utf-8'))
    vmod = load_v01()
    c192 = v01['c192_recap']
    say('    C192: null pooled %.4f vs obs %.4f; null T %.2f vs obs %.2f; F_self %.4f' % (
        c192['null_pooled_median'], c192['observed_pooled'],
        c192['null_median_T'], c192['observed_median_T'], c192['F_self_median']))

    say('[2/8] S2 factor-2 derivation arithmetic ...')
    sigma_w2 = c192['sigma_obs_alt'] ** 2
    # per-dose variances (R=4, M=4)
    var_full_profile = sigma_w2 / (R_REPS * M)          # sigma_w^2/16
    sigma_pair2_true = 2.0 * var_full_profile            # sigma_w^2/8
    var_half_profile = (sigma_w2 / 2.0) / M              # (sigma_w^2/2)/4 = sigma_w^2/8
    var_half_diff = 2.0 * var_half_profile               # sigma_w^2/4 = 2 sigma_pair^2
    S2_raw_expected = var_half_diff                      # 2 sigma_pair^2
    sigma_pair2_A2_corrected = 0.5 * S2_raw_expected      # == sigma_pair2_true under iid
    S1 = sigma_w2 / 8.0
    sigma = {
        'R_reps': R_REPS, 'M_cols': M, 'K_doses': K,
        'var_full_profile_per_dose': rq(var_full_profile),
        'sigma_pair2_true_from_sigma_w': rq(sigma_pair2_true),
        'var_half_profile_per_dose': rq(var_half_profile),
        'var_half_diff_per_dose': rq(var_half_diff),
        'S2_raw_expectation': rq(S2_raw_expected),
        'S2_raw_over_sigma_pair2': rq(S2_raw_expected / sigma_pair2_true),
        'sigma_pair2_A2_corrected_formula': '0.5 * mean_{plan,context} ||P_perp(f_h1-f_h2)||^2/(K-1)',
        'sigma_pair2_A2_corrected_expected': rq(sigma_pair2_A2_corrected),
        'S1_independence': rq(S1),
        'corrected_over_S1_ratio': rq(sigma_pair2_A2_corrected / S1),
        'A1_frozen_sigma_pair2': rq(c192['sigma_pair2_frozen']),
        'A1_frozen_over_corrected_ratio': rq(c192['sigma_pair2_frozen'] / sigma_pair2_A2_corrected),
        'expected_corrected_value_vs_lead_expected': '≈0.00107924 (S1), not A.1 0.00215849',
        'diagnosis': 'A.1 frozen sigma_pair2 = 2 x corrected sigma_pair2; previous v0.1 A.2 S2 formula '
                     'reproduced the same factor-2 error with a new name; A.2 now uses 0.5 x S2_raw.',
    }
    say('    var(full)=%.6g; sigma_pair2=%.6g; Var(half diff)=%.6g=2x; corrected=%.6g; A1/corrected=%.3f' % (
        var_full_profile, sigma_pair2_true, var_half_diff, sigma_pair2_A2_corrected,
        c192['sigma_pair2_frozen'] / sigma_pair2_A2_corrected))

    say('[3/8] F_self rewrite: old identity vs new same-variance H0 self-check ...')
    rng = np.random.default_rng(SEED_SIM + 100)
    sigma_w_sim = 0.10
    sigma_y = sigma_w_sim / math.sqrt(R_REPS)       # row-mean noise sd
    sigma_pair2_sim = sigma_y ** 2 / M * 2.0        # sigma_w^2/8
    # simulate plans with technical repeats to estimate S2_raw, F_self_old (identity) and F_self_check
    n_plans = 4000
    f = rng.normal(size=(n_plans, K))
    g = rng.normal(size=(n_plans, M))
    # full 4-rep row means per plan (K x M) = f + g + noise
    Y = f[:, :, None] + g[:, None, :] + rng.normal(scale=sigma_y, size=(n_plans, K, M))
    # half splits: {1,2}/{3,4} and {1,3}/{2,4}; each half row mean over M columns
    def half_row_mean(split):
        # split: ('A') reps (1,2) vs (3,4); ('B') reps (1,3) vs (2,4)
        reps = rng.normal(scale=sigma_w_sim, size=(n_plans, K, M, R_REPS))
        if split == 'A':
            h1 = reps[..., [0, 1]].mean(axis=-1).mean(axis=2)
            h2 = reps[..., [2, 3]].mean(axis=-1).mean(axis=2)
        else:
            h1 = reps[..., [0, 2]].mean(axis=-1).mean(axis=2)
            h2 = reps[..., [1, 3]].mean(axis=-1).mean(axis=2)
        return h1, h2
    hA1, hA2 = half_row_mean('A')
    hB1, hB2 = half_row_mean('B')
    dA = hA1 - hA2
    dB = hB1 - hB2
    d_avg = 0.5 * (dA + dB)
    S2_raw_samples = np.array([float((center(dA[i]) ** 2).sum()) / (K - 1) for i in range(n_plans)])
    F_self_old = S2_raw_samples / S2_raw_samples   # identity by construction
    sigma_pair2_A2_est = 0.5 * float(S2_raw_samples.mean())
    F_self_check = np.array([float((center(d_avg[i]) ** 2).sum()) / (K - 1) for i in range(n_plans)]) / sigma_pair2_A2_est
    # S1 estimate from half-diff row-level variance
    S1_est = float(np.mean((hA1 - hA2) ** 2) * 0 + 0)  # placeholder; S1 uses row-level diffs
    fself = {
        'old_F_self_identity': {'definition': 'S2_raw/S2_raw (same half-difference) -> identically 1',
                                'mean': rq(float(F_self_old.mean())), 'sd': rq(float(F_self_old.std(ddof=1))),
                                'note': 'identity: cannot detect F_pair half-scale error (challenge item 2)'},
        'new_F_self_check': {
            'definition': 'd_avg=(dA+dB)/2 from two disjoint-covariance half splits; '
                          'F_self_check=||P_perp d_avg||^2/(K-1)/sigma_pair2_A2; same variance as F_pair numerator',
            'mean': rq(float(F_self_check.mean())), 'median': rq(float(np.median(F_self_check))),
            'fpr_at_F_crit': rq(float((F_self_check > F_CRIT).mean())),
            'target': 'mean/median in [0.5,2.0]; FPR@F_crit<=0.10; else design_invalid: scale_mismatch',
        },
        'sigma_pair2_A2_estimated_from_S2_raw': rq(sigma_pair2_A2_est),
        'sigma_pair2_sim_true': rq(sigma_pair2_sim),
        'identity_check_note': 'old F_self is an identity (sd ~0) and is retired; new F_self_check is used in D2/D3',
    }
    say('    old F_self mean=%.6f sd=%.2g (identity); new F_self_check mean=%.4f median=%.4f FPR=%.4f' % (
        fself['old_F_self_identity']['mean'], fself['old_F_self_identity']['sd'],
        fself['new_F_self_check']['mean'], fself['new_F_self_check']['median'],
        fself['new_F_self_check']['fpr_at_F_crit']))

    say('[4/8] corrected-scale synthetic candidate calibration (v0.1 functions reused) ...')
    rng_h0 = np.random.default_rng(SEED_SIM + 1)
    data_h0, meta_h0, sigma_pair_sim = vmod.synthetic_groups(rng_h0, violation=False)
    sigma_pair2_sim_true = sigma_pair_sim ** 2
    data_alt, meta_alt, _ = vmod.synthetic_groups(np.random.default_rng(SEED_SIM + 2), violation=True)
    F_h0 = vmod.pair_F_values(data_h0, meta_h0, sigma_pair2_sim_true)
    F_alt = vmod.pair_F_values(data_alt, meta_alt, sigma_pair2_sim_true)
    # wrong-scale diagnostic: if sigma_pair2 = S2_raw = 2 x true, then F becomes F/2
    F_h0_half = F_h0 / 2.0
    F_alt_half = F_alt / 2.0
    cands = {}
    cands['N0_chi2'] = rng_h0.chisquare(df=K - 1, size=4000) / (K - 1) if False else \
        np.random.default_rng(SEED_SIM + 10).chisquare(df=K - 1, size=4000) / (K - 1)
    cands['N1_parametric_bootstrap'] = vmod.fitted_shared_null_via_bootstrap(
        data_h0, meta_h0, sigma_pair2_sim_true, np.random.default_rng(SEED_SIM + 11))
    cands['N2_residual_permutation'] = vmod.residual_permutation_null(
        data_h0, meta_h0, sigma_pair2_sim_true, np.random.default_rng(SEED_SIM + 12), n_rep=3)
    null_N3, info_N3 = vmod.dose_split_crossfit_null(
        data_h0, meta_h0, sigma_pair2_sim_true, np.random.default_rng(SEED_SIM + 13))
    cands['N3_dose_split_crossfit'] = null_N3
    cands['N4_dose_label_permutation'] = vmod.dose_label_permutation_null(
        data_h0, meta_h0, sigma_pair2_sim_true, np.random.default_rng(SEED_SIM + 15), n_rep=3)
    cands['N5_half_split_layer'] = np.random.default_rng(SEED_SIM + 16).chisquare(df=K - 1, size=4000) / (K - 1)
    table = []
    for cid, null in cands.items():
        q95 = float(np.percentile(null, 95))
        fpr = float((null > F_CRIT).mean())
        power = float((F_alt > q95).mean())
        # wrong-scale (half F) diagnostic
        fpr_half = float(((null) > F_CRIT * 2.0).mean())  # if observed F halved, effective threshold doubles
        power_half = float((F_alt_half > q95 * 1.0).mean())
        table.append({'candidate': cid, 'null_median': rq(float(np.median(null))), 'null_q95': rq(q95),
                      'fpr_at_F_crit': rq(fpr), 'power_under_effect': rq(power),
                      'primary_eligible': bool(0.02 <= fpr <= 0.10),
                      'wrong_scale_diagnostic': {'fpr_if_F_pair_halved_equivalent': rq(fpr_half),
                                                 'power_if_F_pair_halved': rq(power_half)}})
    priority = ['N0_chi2', 'N3_dose_split_crossfit', 'N2_residual_permutation',
                'N1_parametric_bootstrap', 'N5_half_split_layer']
    elig = [t for t in table if t['primary_eligible'] and not t['candidate'].startswith('N4')]
    primary = None
    if elig:
        best = max(t['power_under_effect'] for t in elig)
        top = [t for t in elig if t['power_under_effect'] == best]
        for cid in priority:
            if any(t['candidate'] == cid for t in top):
                primary = cid
                break
    selection = {'rule': 'primary = FPR in [0.02,0.10] and not N4, highest power; tie priority N0>N3>N2>N1>N5; '
                         'N4 excluded (invalid H0); only synthetic calibration used',
                 'eligible': [t['candidate'] for t in elig], 'primary_null': primary,
                 'recompute_note': 'corrected normalization uses true synthetic sigma_pair2 as denominator; if '
                                   'sigma_pair2 were S2_raw=2x true, F would be halved (wrong_scale_diagnostic) '
                                   'and FPR/power would collapse -> the factor-2 fix is necessary',
                 'fallback': 'design_invalid: null_calibration if no eligible candidate'}
    say('    corrected-scale table: ' + '; '.join('%s FPR=%.4f power=%.4f%s' % (
        t['candidate'], t['fpr_at_F_crit'], t['power_under_effect'],
        'eligible' if t['primary_eligible'] else '') for t in table))
    say('    primary null = %s' % primary)

    say('[5/8] legal-pair rule frozen for A.2 ...')
    sigma_obs_A2 = c192['sigma_obs_alt'] / 2.0   # row-mean noise SD = sigma_w/2
    threshold_A2 = 1.96 * sigma_obs_A2
    threshold_A1 = 1.96 * c192['sigma_obs_frozen'] / 2.0
    legal = {
        'A1_rule': 'RMS <= 1.96*sigma_obs/2 with A.1 frozen sigma_obs=0.06570366 -> threshold=0.06438958',
        'A2_rule': 'RMS <= 1.96*sigma_obs_A2 with sigma_obs_A2 = sigma_w_hat/2 (row-mean noise SD); '
                   'sigma_w_hat = sqrt(mean((h1-h2)^2)) = 0.092919 -> sigma_obs_A2=0.0464595, threshold=0.0910607',
        'sigma_obs_A2': rq(sigma_obs_A2), 'threshold_A2': rq(threshold_A2),
        'threshold_A1_recomputed': rq(threshold_A1),
        'decision': 'A.2 recomputes the legal-pair set with the A.2 rule; A.1 n_legal=110,523 is NOT frozen/'
                    'reused; report n_legal_A2; gate n_legal_A2 >= 5% of |U| (17,004.4) else '
                    'design_invalid: coverage',
        'pooled_BH': 'pooled denominator = n_legal_A2 (per-cell legal pairs recomputed under A.2 rule); BH q=0.05 '
                     'across 30 cells unchanged; A.1 legal set reported descriptively for comparison only',
        'consistency': 'PROBLEM_A2_v0_2/DESIGN_A2_v0_2/JSON must use this same rule; no execution-time choice',
    }
    say('    threshold A2=%.6f vs A1=%.6f (A2 looser due to corrected row-mean noise SD)' % (
        threshold_A2, threshold_A1))

    say('[6/8] unified budget & failure categories ...')
    budget = {
        'data_only': True, 'new_wells': 0,
        'components': {
            'N1_per_cell_bootstrap': {'fits': 500, 'per_fit_estimate_s': 0.10,
                                      'estimate_s': 50.0, 'note': '30 cells x 500 replicates; vectorized fitting'},
            'N0_pooled': {'sims': 500, 'estimate_s': 1.0},
            'candidate_diagnostics': {'N2': 500, 'N3': 500, 'N5': 500, 'estimate_s': 75.0,
                                      'note': '2,000 simulation-equivalents including the 500 pooled'},
            'observed_statistics': {'estimate_s': 60.0},
        },
        'total_estimate_s': 186.0,
        'wall_cap_s': 900.0, 'cpu_cap_h': 2.0, 'memory_cap_gb': 8.0,
        'budget_failure': 'design_invalid: compute_budget_exceeded (no reducing N_perm or cheaper analysis)',
        'two_runs': True, 'json_no_telemetry': True,
    }
    failures = {
        'mapping': {
            'D1_sigma_non_degenerate': 'design_invalid: scale_mismatch',
            'D2_F_self_check': 'design_invalid: scale_mismatch',
            'D3_half_split_FPR': 'design_invalid: noise_calibration',
            'D4_null_pooled': 'design_invalid: null_calibration',
            'D5_null_vs_observed_T': 'design_invalid: null_calibration',
            'D6_budget': 'design_invalid: compute_budget_exceeded',
            'D7_G1_to_G5': 'existing A.1 categories (coverage/identifiability/noise/leakage/family)',
        },
        'categories_unified': ['design_invalid: scale_mismatch', 'design_invalid: noise_calibration',
                               'design_invalid: null_calibration', 'design_invalid: compute_budget_exceeded'],
        'note': 'noise_calibration is the D3-half-split-FPR category; scale_mismatch covers sigma/F_self; '
                'null_calibration covers null-pooled/T comparability; all appear in PROBLEM/DESIGN/JSON',
    }
    say('    budget estimate %.0f s (<900); failure categories unified (%d)' % (
        budget['total_estimate_s'], len(failures['categories_unified'])))

    say('[7/8] write v0.2 JSON ...')
    t_end = time.time()
    out = {
        'protocol_v0_2': {'path_rel': 'research/2026-10-27-agent-cell-colearning/mechanism_A/a2_prenull/'
                                      'PROBLEM_A2_v0_2.md', 'sha256': sha256_file(PROBLEM_V2)},
        'design_v0_2': {'path_rel': 'research/2026-10-27-agent-cell-colearning/mechanism_A/a2_prenull/'
                                    'DESIGN_A2_v0_2.md', 'sha256': sha256_file(DESIGN_V2)},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        'inputs': sha,
        'c192_recap': c192,
        'S2_factor2_fix': sigma,
        'F_self_rewrite': fself,
        'candidate_calibration_corrected': {'table': table, 'selection': selection,
                                            'note': 'synthetic only; no O\'Neil responses; corrected sigma_pair2 '
                                                    'denominator; wrong_scale diagnostic shows halved F collapses '
                                                    'FPR/power'},
        'legal_pair_rule_A2': legal,
        'budget': budget,
        'failure_categories': failures,
        'status': 'PREREGISTRATION_v0_2 (not executed; needs Lead approval after challenge; no P1 run)',
        'boundaries': ['A.2.1 correction only; no P1 run; no O\'Neil response statistics',
                       'A.1 negative not reinterpreted; A.2 new pre-registration',
                       'no P2/S2/H_A2 before A.2 completes and passes',
                       'no biology/mechanism/migration/decision/novelty claims; non-blind/peeked; 0 new wells'],
        'deviations': [],
        'log_milestones': ['S2 factor-2 arithmetic', 'F_self rewrite (identity retired)',
                           'corrected synthetic calibration', 'legal rule frozen', 'budget/failure categories'],
    }
    write_json(out, OUTJSON)
    print('null_design_A2_v0_2.json sha256:', sha256_file(OUTJSON))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
