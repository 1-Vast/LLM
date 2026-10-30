#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-A.2.2 pre-registration support: heteroscedasticity-robust sigma / null / diagnostics design.

Design/arithmetic/synthetic-calibration only:
  * restates C194 from frozen A.2-EXEC artifacts (no O'Neil responses read);
  * defines candidate robust sigma schemes R0-R5, their H0/exchangeability/implementation;
  * runs a synthetic heteroscedastic calibration (known mechanism, no O'Neil responses) comparing
    coverage of the per-context self-check, FPR/power at F_crit=2.60;
  * selects the A.2.2 primary scheme with a pre-registered rule and writes the redesigned D2/D3 gates.
No P1 execution, no O'Neil response statistics.
"""
import os
import json
import math
import hashlib
import time

import numpy as np

ROOT = r'D:\MAESTRO'
BASE = os.path.join(ROOT, 'research', '2026-10-27-agent-cell-colearning', 'mechanism_A')
OUTDIR = os.path.join(BASE, 'a22_prenull')
A2EXEC = os.path.join(BASE, 'a2_exec', 'a2_exec.json')
A2EXEC_DIAG = os.path.join(BASE, 'a2_exec', 'a2_exec_diagnostics.json')
A2_JSON = os.path.join(BASE, 'a2_prenull', 'null_design_A2_v0_2.json')
CHALLENGE = os.path.join(BASE, 'challenge_A2.md')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'sigma_robust_A22.json')

K = 4
F_CRIT = 2.60
SEED = 20261031


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


def center(v):
    return v - v.mean()


def f_from_d(d):
    dc = center(d)
    return float((dc ** 2).sum()) / (K - 1)


def quantiles(a):
    a = np.asarray(a, float)
    return {str(q): rq(float(np.percentile(a, q)), 4) for q in (0, 5, 25, 50, 75, 95, 100)}


def simulate_hetero(rng, n_cells=6, n_ctx=8, n_plans=12, sd_log=0.7):
    """Synthetic heteroscedastic H0 data at profile level.

    Each context c has true sigma_pair2(c)=h_c. For each plan: full profile estimate f_p = f + N(0, h/2);
    half-split differences d_A ~ N(0, 2h), d_B ~ N(0, 2h) independent -> d_avg=(dA+dB)/2 ~ N(0,h).
    Returns contexts list with dicts {cell, ctx, h, f_full(list), f_viol(list), dA, dB}.
    """
    contexts = []
    for cell in range(n_cells):
        for c in range(n_ctx):
            h = float(np.exp(rng.normal(0.0, sd_log)))
            h = min(max(h, 0.02), 50.0)
            f = rng.normal(size=K)
            plans = []
            for j in range(n_plans):
                eps = rng.normal(scale=math.sqrt(h / 2.0), size=K)
                f_full = f + eps
                if j == 0:
                    v = np.array([1.0, -1.0, 0.0, 0.0])
                    v = center(v)
                    v = v / np.linalg.norm(v)
                    f_viol = f_full + v * (2.0 * math.sqrt(h) * math.sqrt(K - 1))
                else:
                    f_viol = f_full
                plans.append({'f_full': f_full, 'f_viol': f_viol,
                              'dA': rng.normal(scale=math.sqrt(2.0 * h), size=K),
                              'dB': rng.normal(scale=math.sqrt(2.0 * h), size=K)})
            contexts.append({'cell': cell, 'ctx': c, 'h': h, 'plans': plans})
    return contexts


def estimate_schemes(contexts):
    """Return per-context estimates for R1 and global/robust estimates."""
    per_ctx = []
    for c in contexts:
        fselfA = np.array([f_from_d(p['dA']) for p in c['plans']])
        s2_c = 0.5 * float(fselfA.mean())          # R1 per-context sigma_pair2
        # R4: fuller-profile pair differences
        fp = [p['f_full'] for p in c['plans']]
        pairF = [f_from_d(fp[a] - fp[b]) for a in range(len(fp)) for b in range(a + 1, len(fp))]
        s2_full = float(np.mean(pairF)) if pairF else None
        per_ctx.append({'cell': c['cell'], 'ctx': c['ctx'], 'h': c['h'],
                        's2_per_ctx': s2_c, 's2_full': s2_full,
                        'fselfA': fselfA})
    s2_vals = np.array([x['s2_per_ctx'] for x in per_ctx])
    s2_full_vals = np.array([x['s2_full'] for x in per_ctx if x['s2_full'] is not None])
    glob = {
        'R0_global_mean': 0.5 * float(np.mean([f_from_d(p['dA']) for c in contexts for p in c['plans']])),
        'R1_per_context': None,
        'R2_global_median': float(np.median(s2_vals)),
        'R2_global_trimmed': float(np.mean(np.sort(s2_vals)[int(0.2 * len(s2_vals)):int(0.8 * len(s2_vals))])),
        'R4_full_profile_median': float(np.median(s2_full_vals)),
        'R4_full_profile_mean': float(np.mean(s2_full_vals)),
    }
    return per_ctx, glob, s2_vals


def fpr_power(contexts, per_ctx, sigma_mode, alpha=F_CRIT):
    """FPR/power for a sigma scheme.

    sigma_mode: 'R0' (global mean), 'R2med', 'R2trim', 'R1' (per-context), 'R4' (full-profile per-context).
    F_pair = f_from_d(f_p - f_q) / sigma2; H0 vs violation datasets.
    """
    if sigma_mode == 'R0':
        glob = 0.5 * float(np.mean([f_from_d(p['dA']) for c in contexts for p in c['plans']]))
    elif sigma_mode == 'R2med':
        glob = float(np.median([0.5 * float(np.mean([f_from_d(p['dA']) for p in c['plans']])) for c in contexts]))
    elif sigma_mode == 'R2trim':
        vals = np.array([0.5 * float(np.mean([f_from_d(p['dA']) for p in c['plans']])) for c in contexts])
        s = np.sort(vals)
        glob = float(np.mean(s[int(0.2 * len(s)):int(0.8 * len(s))]))
    else:
        glob = None
    h0_vals, viol_vals, ctx_of = [], [], []
    for c, pc in zip(contexts, per_ctx):
        if sigma_mode == 'R1':
            s2 = pc['s2_per_ctx']
        elif sigma_mode == 'R4':
            s2 = pc['s2_full']
        else:
            s2 = glob
        fp = [p['f_full'] for p in c['plans']]
        fv = [p['f_viol'] for p in c['plans']]
        for a in range(len(fp)):
            for b in range(a + 1, len(fp)):
                h0_vals.append(f_from_d(fp[a] - fp[b]) / s2)
                viol_vals.append(f_from_d(fv[a] - fv[b]) / s2)
                ctx_of.append((c['cell'], c['ctx']))
    h0_vals = np.array(h0_vals)
    viol_vals = np.array(viol_vals)
    ctx_of = np.array(ctx_of)
    q95 = float(np.percentile(h0_vals, 95))
    power = float((viol_vals > q95).mean())
    per_ctx_fpr = {}
    for key in set(map(tuple, ctx_of)):
        m = np.array([tuple(x) == key for x in ctx_of])
        per_ctx_fpr[key] = float((h0_vals[m] > alpha).mean())
    fpr_ctx = np.array(list(per_ctx_fpr.values()))
    return {
        'overall_fpr_at_F_crit': float((h0_vals > alpha).mean()),
        'fpr_q95_across_contexts': float(np.percentile(fpr_ctx, 95)),
        'fpr_worst_context': float(fpr_ctx.max()),
        'power': power,
        'q95_null': q95,
        'n_pairs': int(h0_vals.size),
    }


def fself_metrics(contexts, per_ctx, sigma_mode):
    if sigma_mode == 'R0':
        s2 = 0.5 * float(np.mean([f_from_d(p['dA']) for c in contexts for p in c['plans']]))
        scales = [s2] * len(contexts)
    elif sigma_mode == 'R2med':
        s2 = float(np.median([0.5 * float(np.mean([f_from_d(p['dA']) for p in c['plans']])) for c in contexts]))
        scales = [s2] * len(contexts)
    elif sigma_mode == 'R2trim':
        vals = np.array([0.5 * float(np.mean([f_from_d(p['dA']) for p in c['plans']])) for c in contexts])
        ss = np.sort(vals)
        s2 = float(np.mean(ss[int(0.2 * len(ss)):int(0.8 * len(ss))]))
        scales = [s2] * len(contexts)
    elif sigma_mode == 'R1':
        scales = [pc['s2_per_ctx'] for pc in per_ctx]
    else:
        scales = [pc['s2_full'] for pc in per_ctx]
    vals = []
    per_ctx_median = []
    for c, pc, s2 in zip(contexts, per_ctx, scales):
        f_self = [f_from_d((p['dA'] + p['dB']) / 2.0) / s2 for p in c['plans']]
        vals.extend(f_self)
        per_ctx_median.append(float(np.median(f_self)))
    vals = np.array(vals)
    per_ctx_median = np.array(per_ctx_median)
    coverage = float(np.mean((per_ctx_median >= 0.5) & (per_ctx_median <= 2.0)))
    return {'global_mean': float(vals.mean()),
            'global_median': float(np.median(vals)),
            'quantiles': quantiles(vals),
            'per_context_median_coverage_0p5_2': coverage,
            'per_context_median_quantiles': quantiles(per_ctx_median)}


def main():
    t0 = time.time()
    say = lambda m: print(m, flush=True)
    say('[1/6] read frozen C194 artifacts (no O\'Neil responses) ...')
    a2 = json.load(open(A2EXEC, encoding='utf-8'))
    a2d = json.load(open(A2EXEC_DIAG, encoding='utf-8'))
    c194 = {
        'verdict': a2['verdict'], 'failure_category': a2['failure_category'],
        'D2_median': a2d['F_self_check']['median'],
        'D2_mean': a2d['F_self_check']['mean'],
        'F_self_quantiles': a2d['F_self_check']['quantiles'],
        'F_self_fpr': a2d['F_self_check']['fpr_at_F_crit'],
        'sigma_pair2_A2': a2d['sigma_block']['sigma_pair2_A2'],
        'sigma_pair2_over_S1': a2d['sigma_block']['sigma_pair2_over_S1'],
        'n_legal_A2': a2d['legal_block']['n_legal_pairs'],
        'P1_executed': a2['P1'] is not None,
        'note': 'A.2-EXEC stopped at D2; P1 not executed; A.1 p0p1_negative still not interpretable',
    }
    say('    C194: D2 median=%.4f (mean %.4f); P1 executed=%s' % (
        c194['D2_median'], c194['D2_mean'], c194['P1_executed']))

    say('[2/6] synthetic heteroscedastic calibration (known mechanism; no O\'Neil responses) ...')
    rng = np.random.default_rng(SEED)
    contexts = simulate_hetero(rng)
    per_ctx, glob, s2_vals = estimate_schemes(contexts)
    trues = np.array([c['h'] for c in contexts])
    het = {'n_contexts': len(contexts), 'n_plans_per_context': 12,
           'true_sigma_pair2_quantiles': quantiles(trues),
           'estimated_per_context_quantiles': quantiles(s2_vals),
           'het_ratio_p95_p25': float(np.percentile(trues, 95) / np.percentile(trues, 25))
           if np.percentile(trues, 25) > 0 else None,
           'note': 'synthetic heterogeneity (lognormal sd=0.7); not O\'Neil'}
    say('    true sigma2 quantiles: %s' % json.dumps(het['true_sigma_pair2_quantiles']))

    say('[3/6] candidate schemes: self-check + FPR/power ...')
    schemes = {
        'R0_global_mean': {'sigma': '0.5 x mean over all plan/context ||P_perp d_A||^2/(K-1)',
                           'f_pair_scale': 'global mean',
                           'h0': 'shared f; iid noise; homogeneous sigma (invalid under heteroscedasticity)',
                           'exchangeability': 'iid noise only; not heteroscedasticity-robust'},
        'R1_per_context': {'sigma': 'per-context sigma_pair2(c) = 0.5 x mean_plans ||P_perp d_A||^2/(K-1)',
                           'f_pair_scale': 'sigma_pair2(shared context)',
                           'h0': 'shared f; noise heteroscedastic by context; F standardized per context',
                           'exchangeability': 'within-context iid; context scales estimated from plans'},
        'R2_global_median': {'sigma': 'median over contexts of per-context sigma_pair2(c)',
                             'f_pair_scale': 'global robust median',
                             'h0': 'shared f; robust global scale; heterogeneous context FPR',
                             'exchangeability': 'robust location; not per-context calibrated'},
        'R2_global_trimmed': {'sigma': '20% trimmed mean of per-context sigma_pair2(c)',
                              'f_pair_scale': 'global trimmed mean',
                              'h0': 'shared f; robust global scale',
                              'exchangeability': 'robust location; not per-context calibrated'},
        'R4_full_profile': {'sigma': 'per-context from full-profile plan-pair differences',
                            'f_pair_scale': 'sigma_pair2(c) from full profile pairs',
                            'h0': 'shared f; full-profile resampling self-check',
                            'exchangeability': 'plan pairs within context; sensitive to shared-f violations'},
    }
    rows = []
    for cid, meta in schemes.items():
        mode = {'R0_global_mean': 'R0', 'R1_per_context': 'R1', 'R2_global_median': 'R2med', 'R2_global_trimmed': 'R2trim', 'R4_full_profile': 'R4'}[cid]
        fself = fself_metrics(contexts, per_ctx, mode)
        fp = fpr_power(contexts, per_ctx, mode)
        eligible = bool(fself['per_context_median_coverage_0p5_2'] >= 0.85 and
                        0.02 <= fp['overall_fpr_at_F_crit'] <= 0.10 and
                        fp['fpr_worst_context'] <= 0.25 and
                        fp['fpr_q95_across_contexts'] <= 0.20)
        rows.append({'scheme': cid, 'h0': meta['h0'], 'exchangeability': meta['exchangeability'],
                     'sigma': meta['sigma'], 'f_pair_scale': meta['f_pair_scale'],
                     'fself': fself, 'fpr_power': fp, 'eligible': eligible})
        say('    %-24s coverage=%.3f glob_med=%.3f FPR=%.4f worstFPR=%.3f power=%.3f' % (
            cid, fself['per_context_median_coverage_0p5_2'], fself['global_median'],
            fp['overall_fpr_at_F_crit'], fp['fpr_worst_context'], fp['power']))

    priority = ['R1_per_context', 'R2_global_median', 'R2_global_trimmed', 'R4_full_profile', 'R0_global_mean']
    elig = [r for r in rows if r['eligible']]
    primary = None
    if elig:
        best = max(r['fpr_power']['power'] for r in elig)
        top = [r for r in elig if r['fpr_power']['power'] == best]
        for cid in priority:
            if any(r['scheme'] == cid for r in top):
                primary = cid
                break
        if primary is None:
            primary = top[0]['scheme']
    selection = {
        'rule': 'eligible if per-context F_self median coverage_0.5_2 >= 0.85 (48 contexts, binomial tolerance) '
                'AND overall FPR@2.60 in [0.02,0.10] AND worst-context FPR <= 0.25 AND context-FPR p95 <= 0.20; '
                'among eligible choose highest power; tie priority R1 > R2med > R2trim > R4 > R0; only synthetic '
                'calibration used (no O\'Neil observed)',
        'eligible': [r['scheme'] for r in elig], 'primary_scheme': primary,
        'coverage_threshold': 0.85, 'fpr_range': [0.02, 0.10], 'worst_context_fpr_max': 0.25,
        'context_fpr_p95_max': 0.20,
        'fallback': 'design_invalid: null_calibration if none eligible',
    }
    say('    primary scheme = %s (eligible: %s)' % (primary, selection['eligible']))

    say('[4/6] D2/D3 redesign + A.2.2 design ...')
    primary_row = next((r for r in rows if r['scheme'] == primary), None)
    design = {
        'unchanged_from_A2': ['data/population', 'U=340,088', 'A.2 legal rule (global sigma_obs_A2, threshold 0.0910607)',
                              'S-add role-stratified family', 'F_pair/T_c/pooled structure',
                              'F_crit=2.60 (conditional on D2+D3)', 'N_perm=500', 'BH q=0.05',
                              'P1 positive three conditions'],
        'changed_only': ['sigma_pair2 estimation (primary scheme from synthetic selection)',
                         'F_pair normalization (per-context or robust global)',
                         'D2/D3 gates (per-context/distributional, replace global median gate)',
                         'null model stratified/standardized by context'],
        'D2_redesign': {
            'metric': 'per-context F_self_check median coverage in [0.5,2]',
            'gate': 'coverage >= 0.85 AND global F_self median in [0.5, 1.5]',
            'fpr_related': 'F_self_check FPR@F_crit (overall) <= 0.10',
            'fail': 'design_invalid: scale_mismatch',
            'note': 'replaces A.2 global median gate; do not use observed A.2 results to tune'},
        'D3_redesign': {
            'metric': 'overall FPR@F_crit and worst-context FPR',
            'gate': 'overall <= 0.10 AND worst-context <= 0.25 AND context FPR p95 <= 0.20',
            'fail': 'design_invalid: noise_calibration'},
        'F_crit_condition': 'retain F_crit=2.60 only if D2+D3 pass; otherwise design_invalid: scale_mismatch; '
                            'no post-hoc threshold change',
        'null': 'pooled: stratified/standardized chi-square (per-context scales); per-cell: parametric bootstrap '
                'with context-specific noise; N_perm=500 seed=20261029',
        'budget': {'data_only': True, 'new_wells': 0, 'wall_cap_s': 900, 'cpu_cap_h': 2.0,
                   'memory_cap_gb': 8, 'simulations': '~2,500 (N1 500, N0 500, diagnostics 1,500)'},
        'failure_categories': ['design_invalid: scale_mismatch', 'design_invalid: noise_calibration',
                               'design_invalid: null_calibration', 'design_invalid: compute_budget_exceeded',
                               'existing A.1/A.2 categories (coverage/identifiability/leakage/family)'],
        'two_runs': True, 'json_no_telemetry': True,
        'interpretation_boundary': 'positive: developmental existence in this resource/family/design; negative: '
                                   'no_joint_contradiction only (never "contradiction absent"); no biology/mechanism/'
                                   'migration/decision/novelty; non-blind/peeked; no P2/S2/H_A2 before A.2.2',
    }
    say('    D2/D3 redesigned (per-context coverage); primary scheme recorded')

    say('[5/6] write JSON ...')
    out = {
        'protocol_a22': {'path_rel': 'research/2026-10-27-agent-cell-colearning/mechanism_A/'
                                      'a22_prenull/PROBLEM_A22.md',
                         'sha256': sha256_file(os.path.join(OUTDIR, 'PROBLEM_A22.md'))},
        'design_a22': {'path_rel': 'research/2026-10-27-agent-cell-colearning/mechanism_A/'
                                    'a22_prenull/DESIGN_A22.md',
                       'sha256': sha256_file(os.path.join(OUTDIR, 'DESIGN_A22.md'))},
        'c194_recap': c194,
        'inputs': {
            'a2_exec_json': {'path_rel': os.path.relpath(A2EXEC, ROOT).replace('\\', '/'), 'sha256': sha256_file(A2EXEC)},
            'a2_exec_diagnostics': {'path_rel': os.path.relpath(A2EXEC_DIAG, ROOT).replace('\\', '/'),
                                    'sha256': sha256_file(A2EXEC_DIAG)},
            'a2_prenull_v0_2_json': {'path_rel': os.path.relpath(A2_JSON, ROOT).replace('\\', '/'),
                                     'sha256': sha256_file(A2_JSON)},
            'challenge_a2': {'path_rel': os.path.relpath(CHALLENGE, ROOT).replace('\\', '/'),
                             'sha256': sha256_file(CHALLENGE)},
            'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                       'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        },
        'synthetic_heteroscedasticity': {'seed': SEED, 'n_cells': 6, 'n_contexts_per_cell': 8,
                                         'n_plans_per_context': 12, 'sd_log': 0.7,
                                         'true_sigma_quantiles': het['true_sigma_pair2_quantiles'],
                                         'estimated_per_context_quantiles': het['estimated_per_context_quantiles'],
                                         'note': 'synthetic only; no O\'Neil responses'},
        'candidate_schemes': rows,
        'selection': selection,
        'A22_design': design,
        'status': 'PREREGISTRATION_DRAFT (not executed; A.2.2 must not run P1 before challenge+approval)',
        'boundaries': ['A.2.2 design only; no P1 run; no O\'Neil response statistics',
                       'A.1 p0p1_negative not reinterpreted; A.2 design_invalid scale_mismatch kept as-is',
                       'data-only, 0 new wells; no P2/S2/H_A2',
                       'positive: developmental existence only; negative: no_joint_contradiction only',
                       'no biology/mechanism/migration/decision/novelty; non-blind/peeked'],
        'deviations': [],
        'log_milestones': ['C194 recap', 'synthetic heteroscedastic calibration', 'candidate selection',
                           'D2/D3 redesign', 'A.2.2 design'],
    }
    write_json(out, OUTJSON)
    print('sigma_robust_A22.json sha256:', sha256_file(OUTJSON))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
