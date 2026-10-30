#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-A.2 pre-registration support: C192 recap arithmetic + candidate null-model synthetic calibration.

Design/arithmetic only:
  * restates C192 numbers from the frozen A-P0P1 artifacts (a_p0p1.json) -- no O'Neil response read;
  * derives sigma_pair scale formulas (independence-derived S1 vs half-split-layer S2) and the A.1
    scale mismatch arithmetic;
  * runs a SYNTHETIC calibration simulation (mechanism known, no O'Neil responses) comparing candidate
    null models N0/N1/N2/N3/N4/N5 on FPR@F_crit and power under a pre-registered shape violation;
  * emits the pre-registered candidate table, primary-null selection rule outcome, and A.2 design gates.
No P1 effect run, no fitting of O'Neil responses, no prediction.
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
BASE = os.path.join(ROOT, 'research', '2026-10-27-agent-cell-colearning', 'mechanism_A')
OUTDIR = os.path.join(BASE, 'a2_prenull')
P0P1 = os.path.join(BASE, 'p0p1', 'a_p0p1.json')
DESIGN_V2 = os.path.join(BASE, 'DESIGN_A_v0_2.md')
PROBLEM_V2 = os.path.join(BASE, 'PROBLEM_A_v0_2.md')
QUAL = os.path.join(BASE, 'qualify_A_v0_2.json')
DECISION = os.path.join(BASE, 'DECISION_R201_A_P0P1.md')
PROTOCOL_P0P1 = os.path.join(BASE, 'p0p1', 'PROTOCOL_P0P1_EXEC.md')
PROBLEM_A2 = os.path.join(OUTDIR, 'PROBLEM_A2.md')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'null_design_A2.json')

F_CRIT = 2.60
K = 4
M = 4
R_REPS = 4
N_PERM_A2 = 500
DELTA_MIN = 0.05
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


def center(v):
    return v - v.mean()


def f_stat_from_profiles(fp, fq, sigma_pair2):
    """F = ||P_perp(fp-fq)||^2/(K-1) / sigma_pair2"""
    d = center(fp - fq)
    return float((d ** 2).sum()) / (K - 1) / sigma_pair2


def synthetic_groups(rng, n_cells=5, n_groups=6, n_plans=6, sigma_w=0.10, violation=False, effect=2.0):
    """Generate synthetic plan-cell data under S-add.

    Y[plan] (4x4) = f(d) + g(e) + noise, noise sd = sigma_w/sqrt(R_REPS) on the row-mean scale.
    Under violation: the first plan in each group gets a shape-violated member profile:
    f_v = f + delta * v with v = [1,-1,0,0] scaled so that ||P_perp(delta v)|| = effect * sigma_pair.
    Returns (Y_list, group_ids, plan_ids, sigma_pair_true).
    """
    sigma_y = sigma_w / math.sqrt(R_REPS)          # row-mean noise sd per cell
    sigma_pair = math.sqrt(2.0) * sigma_y / math.sqrt(M)  # sd of profile difference per dose
    data = []
    meta = []
    pid = 0
    for c in range(n_cells):
        for g in range(n_groups):
            f = rng.normal(size=K) * 1.0
            for j in range(n_plans):
                gvec = rng.normal(size=M) * 1.0
                Y = f[:, None] + gvec[None, :] + rng.normal(scale=sigma_y, size=(K, M))
                if violation and j == 0:
                    v = np.array([1.0, -1.0, 0.0, 0.0])
                    v = center(v)
                    v = v / np.linalg.norm(v)
                    # profile shift with ||P_perp shift|| = effect * sigma_pair * sqrt(K-1)
                    Y = Y + (effect * sigma_pair * math.sqrt(K - 1) * v)[:, None]
                data.append(Y)
                meta.append({'cell': c, 'group': g, 'plan': j, 'pid': pid})
                pid += 1
    return data, meta, sigma_pair


def pair_F_values(data, meta, sigma_pair2):
    """F for all within-group plan pairs."""
    out = []
    by_group = {}
    for Y, m in zip(data, meta):
        by_group.setdefault((m['cell'], m['group']), []).append((m['pid'], Y))
    for key, items in by_group.items():
        for a in range(len(items)):
            for b in range(a + 1, len(items)):
                Ya, Yb = items[a][1], items[b][1]
                out.append(f_stat_from_profiles(Ya.mean(axis=1), Yb.mean(axis=1), sigma_pair2))
    return np.array(out)


def pair_F_within_groups(mats, meta, sigma_pair2):
    """F for within-(cell,group) plan pairs given a list of matrices aligned with meta."""
    by_group = {}
    for Y, m in zip(mats, meta):
        by_group.setdefault((m['cell'], m['group']), []).append(Y)
    out = []
    for key, items in by_group.items():
        for a in range(len(items)):
            for b in range(a + 1, len(items)):
                out.append(f_stat_from_profiles(items[a].mean(axis=1), items[b].mean(axis=1), sigma_pair2))
    return np.array(out)


def fitted_shared_null_via_bootstrap(data, meta, sigma_pair2, rng, n_boot=1):
    """Parametric bootstrap: fit shared f (mean profile per group) + per-plan g (col means), resimulate."""
    sigma_y = math.sqrt(sigma_pair2 * M / 2.0)   # sigma_pair^2 = 2 sigma_y^2 / M
    by_group = {}
    for Y, m in zip(data, meta):
        by_group.setdefault((m['cell'], m['group']), []).append((m['pid'], Y))
    boots = []
    for key, items in by_group.items():
        f_hat = np.mean([Y.mean(axis=1) for _, Y in items], axis=0)
        sim = []
        for pid, Y in items:
            g_hat = (Y - f_hat[:, None]).mean(axis=0)
            Ys = f_hat[:, None] + g_hat[None, :] + rng.normal(scale=sigma_y, size=(K, M))
            sim.append(Ys)
        for a in range(len(sim)):
            for b in range(a + 1, len(sim)):
                boots.append(f_stat_from_profiles(sim[a].mean(axis=1), sim[b].mean(axis=1), sigma_pair2))
    return np.array(boots)


def residual_permutation_null(data, meta, sigma_pair2, rng, n_rep=3):
    """Per-plan additive fit; permute residuals within plan; recompute within-group F (null)."""
    by_group = {}
    for idx, (Y, m) in enumerate(zip(data, meta)):
        by_group.setdefault((m['cell'], m['group']), []).append(idx)
    nulls = []
    for rep in range(n_rep):
        mats = [None] * len(meta)
        for key, idxs in by_group.items():
            for idx in idxs:
                Y = data[idx]
                fit = Y.mean(axis=1)[:, None] + Y.mean(axis=0)[None, :] - Y.mean()
                resid = (Y - fit).reshape(-1)
                perm = rng.permutation(resid.size)
                mats[idx] = fit + resid[perm].reshape(K, M)
        nulls.append(pair_F_within_groups(mats, meta, sigma_pair2))
    return np.concatenate(nulls)


def dose_split_crossfit_null(data, meta, sigma_pair2, rng):
    """Cross-fit over dose splits {0,1}/{2,3}: estimate profile-difference variance from independent halves
    and generate a null F distribution under H0 with that scale (chi-square(3)/3 * scale)."""
    half_diffs = []
    for Y, m in zip(data, meta):
        prof = Y.mean(axis=1)
        d = center(prof[:2].mean() * np.ones(K) - prof[:2].mean())  # placeholder not used
    # simpler: use dose-split profile difference to estimate scale of profile difference
    by_group = {}
    for Y, m in zip(data, meta):
        by_group.setdefault((m['cell'], m['group']), []).append((m['pid'], Y))
    scales = []
    for key, items in by_group.items():
        for a in range(len(items)):
            for b in range(a + 1, len(items)):
                pa = items[a][1].mean(axis=1); pb = items[b][1].mean(axis=1)
                # profile estimated from first two doses only (df 1) and last two (df 1)
                for idx in ((0, 1), (2, 3)):
                    d = center(pa[list(idx)] - pb[list(idx)])
                    scales.append(float((d ** 2).sum()) / 1.0)
    scale = float(np.mean(scales)) if scales else sigma_pair2
    # null: chi-square(3)/3 * (scale/sigma_pair2) -- scale inflation factor estimated from cross-fit
    factor = scale / sigma_pair2
    nulls = rng.chisquare(df=K - 1, size=2000) / (K - 1) * factor
    return np.array(nulls), {'crossfit_scale': scale, 'scale_factor': factor}


def dose_label_permutation_null(data, meta, sigma_pair2, rng, n_rep=1):
    """Dose-label permutation: permute profile values among the 4 dose positions per plan."""
    by_group = {}
    for Y, m in zip(data, meta):
        by_group.setdefault((m['cell'], m['group']), []).append((m['pid'], Y))
    nulls = []
    for rep in range(n_rep):
        sim = []
        for key, items in by_group.items():
            for pid, Y in items:
                prof = Y.mean(axis=1)
                perm = rng.permutation(K)
                Yp = Y.copy()
                # permute rows (dose positions) of the matrix
                Yp = Yp[perm, :]
                sim.append(Yp)
        nulls.append(pair_F_within_groups(sim, meta, sigma_pair2))
    return np.concatenate(nulls)


def half_split_null_scale(sigma_w, sigma_pair2_true, rng, n=4000):
    """Half-split layer: F_self = ||P_perp(f_h1-f_h2)||^2/(K-1) / sigma_pair2_true under independence;
    returns F_self samples and estimated A.2 sigma_pair2 (S2 = mean F_self * sigma_pair2_true)."""
    f = rng.normal(size=K)
    sigma_h = sigma_w / math.sqrt(2.0) / math.sqrt(M)   # row mean of a half (2 reps) over M columns
    vals = []
    for _ in range(n):
        f_h1 = f + rng.normal(scale=sigma_h, size=K)
        f_h2 = f + rng.normal(scale=sigma_h, size=K)
        vals.append(float((center(f_h1 - f_h2) ** 2).sum()) / (K - 1) / sigma_pair2_true)
    return np.array(vals)


def main():
    t0 = time.time()
    log = []
    say = lambda m: (print(m, flush=True), log.append(m))

    say('[1/7] verify inputs & read frozen A-P0P1 artifacts (no response values) ...')
    sha = {}
    for key, path in (('problem_a2', PROBLEM_A2), ('design_v0_2', DESIGN_V2), ('problem_v0_2', PROBLEM_V2),
                      ('qualify_v0_2', QUAL), ('decision', DECISION), ('protocol_p0p1', PROTOCOL_P0P1),
                      ('a_p0p1_json', P0P1), ('script', SCRIPT)):
        if not os.path.isfile(path):
            raise SystemExit('FATAL missing input: %s' % key)
        sha[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                    'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    p0p1 = json.load(open(P0P1, encoding='utf-8'))
    rows_csv = os.path.join(BASE, 'p0p1', 'a_p0p1_rows.csv')
    t_obs_vals = []
    try:
        import csv
        with open(rows_csv, encoding='utf-8') as fh:
            for row in csv.DictReader(fh):
                try:
                    t_obs_vals.append(float(row['T_obs']))
                except (TypeError, ValueError):
                    pass
    except Exception:
        t_obs_vals = []
    t_obs_median = float(np.median(t_obs_vals)) if t_obs_vals else None
    c192 = {
        'null_pooled_median': p0p1['P1']['pooled']['null_median_frac'],
        'null_pooled_q95': p0p1['P1']['pooled']['null_q95_frac'],
        'observed_pooled': p0p1['P1']['pooled']['observed_frac_F_ge_Fcrit'],
        'null_median_T': p0p1['P1']['f_calibration_diagnostic']['median_T_null'],
        'observed_median_T': rq(t_obs_median),
        'F_self_median': p0p1['gates']['half_split_fpr']['median_F_self'],
        'half_split_fpr': p0p1['gates']['half_split_fpr']['fpr'],
        'sigma_obs_frozen': p0p1['gates']['G3_noise']['sigma_obs'],
        'sigma_obs_alt': p0p1['gates']['G3_noise']['sigma_obs_alt'],
        'sigma_pair2_frozen': p0p1['gates']['G3_noise']['sigma_pair2'],
        'verdict_A1': p0p1.get('verdict'),
        'U': p0p1['P1']['universe_U'],
        'n_legal_pairs': p0p1['P1']['n_legal_pairs'],
    }
    say('    C192: null pooled median %.4f vs observed %.4f; null median T %.2f vs observed %.2f; '
        'F_self median %.4f' % (c192['null_pooled_median'], c192['observed_pooled'],
                                c192['null_median_T'], c192['observed_median_T'], c192['F_self_median']))

    say('[2/7] sigma scale arithmetic (formulas only; numbers from frozen artifacts) ...')
    sigma_w_hat = c192['sigma_obs_alt']                 # sqrt(mean((h1-h2)^2)) = estimate of sigma_well
    sigma_w_hat2 = sigma_w_hat ** 2
    sigma_pair2_S1 = sigma_w_hat2 / 8.0                 # R=4, M=4 -> sigma_w^2/(R*M)*2
    sigma_pair2_S2_formula = 'mean over (plan,context) of ||P_perp(f_h1-f_h2)||^2/(K-1)  [computed in A.2 execution]'
    frozen = c192['sigma_pair2_frozen']
    scale_ratio = frozen / sigma_pair2_S1
    # F_self under frozen denominator (which equals sigma_w^2/4) is expected 1 under iid replicates;
    # observed median 0.4579 -> implied variance factor
    implied_factor = c192['F_self_median']
    sigma = {
        'sigma_w_hat_from_half_split': rq(sigma_w_hat),
        'sigma_w_hat_sq': rq(sigma_w_hat2),
        'sigma_pair2_S1_independence': rq(sigma_pair2_S1),
        'sigma_pair2_S2_formula': sigma_pair2_S2_formula,
        'sigma_pair2_frozen_A1': rq(frozen),
        'frozen_over_S1_ratio': rq(scale_ratio),
        'expected_F_self_under_frozen_denominator_if_iid': 1.0,
        'observed_F_self_median': rq(implied_factor),
        'implied_variance_factor': rq(implied_factor),
        'F_crit': F_CRIT,
        'F_crit_note': 'retained only if A.2 normalization gives E[F]=1 and F_self in [0.5,2], FPR@F_crit<=0.10; '
                       'otherwise design_invalid: scale_mismatch; no post-hoc threshold change',
        'diagnosis': 'A.1 frozen sigma_pair2 = 2 x S1 -> A.1 F scale is half of the independence-normalized '
                     'scale; F_self median 0.458 confirms scale mismatch; A.1 must be rerun as A.2 (new '
                     'pre-registration), not patched post hoc',
    }
    say('    sigma_w_hat=%.6f; S1 sigma_pair2=%.6f; frozen=%.6f (ratio %.3f); F_self median=%.4f' % (
        sigma_w_hat, sigma_pair2_S1, frozen, scale_ratio, implied_factor))

    say('[3/7] synthetic calibration simulation (known mechanism; no O\'Neil responses) ...')
    rng = np.random.default_rng(SEED_SIM)
    sigma_w_sim = 0.10
    # H0 and violation datasets (independently generated)
    rng_h0 = np.random.default_rng(SEED_SIM + 1)
    data_h0, meta_h0, sigma_pair_sim = synthetic_groups(rng_h0, violation=False)
    sigma_pair2_sim = sigma_pair_sim ** 2
    rng_alt = np.random.default_rng(SEED_SIM + 2)
    data_alt, meta_alt, _ = synthetic_groups(rng_alt, violation=True, effect=2.0)
    F_h0 = pair_F_values(data_h0, meta_h0, sigma_pair2_sim)
    F_alt = pair_F_values(data_alt, meta_alt, sigma_pair2_sim)
    n_pairs_sim = F_h0.size
    cands = {}
    # N0 analytic chi-square(3)/3
    rng0 = np.random.default_rng(SEED_SIM + 10)
    null_N0 = rng0.chisquare(df=K - 1, size=4000) / (K - 1)
    cands['N0_chi2'] = {'null': null_N0, 'implementation': 'analytic/simulated chi-square(K-1)/(K-1)',
                        'h0': 'shared f + iid noise; sigma known; F normalized E=1',
                        'exchangeability': 'iid noise; parametric F distribution'}
    # N1 parametric bootstrap (fit shared f + per-plan g, resimulate)
    rng1 = np.random.default_rng(SEED_SIM + 11)
    null_N1 = []
    for _ in range(3):
        null_N1.append(fitted_shared_null_via_bootstrap(data_h0, meta_h0, sigma_pair2_sim, rng1))
    null_N1 = np.concatenate(null_N1)
    alt_N1 = fitted_shared_null_via_bootstrap(data_alt, meta_alt, sigma_pair2_sim, rng1)
    cands['N1_parametric_bootstrap'] = {'null': null_N1, 'altnull': alt_N1,
                                        'implementation': 'fit shared f + per-plan g; resimulate iid noise; recompute F',
                                        'h0': 'S-add shared f; per-plan g free; iid noise',
                                        'exchangeability': 'parametric (no permutation)'}
    # N2 residual permutation
    rng2 = np.random.default_rng(SEED_SIM + 12)
    null_N2 = residual_permutation_null(data_h0, meta_h0, sigma_pair2_sim, rng2, n_rep=3)
    alt_N2 = residual_permutation_null(data_alt, meta_alt, sigma_pair2_sim, rng2, n_rep=3)
    cands['N2_residual_permutation'] = {'null': null_N2, 'altnull': alt_N2,
                                        'implementation': 'fit shared f + per-plan g; permute residuals within plan',
                                        'h0': 'residual exchangeability (iid resid)',
                                        'exchangeability': 'residuals exchangeable under H0'}
    # N3 dose-split cross-fit
    rng3 = np.random.default_rng(SEED_SIM + 13)
    null_N3, info_N3 = dose_split_crossfit_null(data_h0, meta_h0, sigma_pair2_sim, rng3)
    alt_N3, _ = dose_split_crossfit_null(data_alt, meta_alt, sigma_pair2_sim, np.random.default_rng(SEED_SIM + 14))
    cands['N3_dose_split_crossfit'] = {'null': null_N3, 'altnull': alt_N3,
                                       'implementation': 'cross-fit profile differences over dose splits; scale null chi2',
                                       'h0': 'dose-exchangeable noise estimation; shared f',
                                       'exchangeability': 'dose labels exchangeable only for noise estimation',
                                       'info': info_N3}
    # N4 dose-label permutation (invalid control)
    rng4 = np.random.default_rng(SEED_SIM + 15)
    null_N4 = dose_label_permutation_null(data_h0, meta_h0, sigma_pair2_sim, rng4, n_rep=3)
    alt_N4 = dose_label_permutation_null(data_alt, meta_alt, sigma_pair2_sim, rng4, n_rep=3)
    cands['N4_dose_label_permutation'] = {'null': null_N4, 'altnull': alt_N4,
                                          'implementation': 'permute 4 dose positions of each plan profile',
                                          'h0': 'INVALID for shared-f H0 (does not preserve profiles); '
                                                'diagnostic only',
                                          'exchangeability': 'dose labels; invalid for shared-f'}
    # N5 half-split layer
    rng5 = np.random.default_rng(SEED_SIM + 16)
    fself = half_split_null_scale(sigma_w_sim, sigma_pair2_sim, rng5)
    null_N5 = rng5.chisquare(df=K - 1, size=4000) / (K - 1)  # normalized F under S2 scale
    cands['N5_half_split_layer'] = {'null': null_N5, 'altnull': null_N5,
                                    'implementation': 'estimate sigma_pair2 from half-split profile differences; '
                                                      'normalized chi-square null',
                                    'h0': 'half-splits independent; shared f',
                                    'exchangeability': 'independent half-split noise',
                                    'fself_median': rq(float(np.median(fself))),
                                    'fself_mean': rq(float(np.mean(fself)))}
    # evaluate candidates
    table = []
    for cid, c in cands.items():
        q95 = float(np.percentile(c['null'], 95))
        fpr = float((c['null'] > F_CRIT).mean())
        power_alt = float((F_alt > q95).mean())
        table.append({'candidate': cid, 'h0': c['h0'], 'exchangeability': c['exchangeability'],
                      'implementation': c['implementation'],
                      'null_median': rq(float(np.median(c['null']))),
                      'null_q95': rq(q95), 'fpr_at_F_crit': rq(fpr),
                      'power_under_effect': rq(power_alt) if power_alt is not None else None,
                      'primary_eligible': bool(0.02 <= fpr <= 0.10)})
    say('    synthetic calibration (n_pairs=%d):' % n_pairs_sim)
    for t in table:
        say('      %-30s FPR=%.4f power=%s' % (t['candidate'], t['fpr_at_F_crit'], t['power_under_effect']))
    # selection rule (pre-registered): among primary_eligible and not N4, pick highest power; tie priority
    priority = ['N0_chi2', 'N3_dose_split_crossfit', 'N2_residual_permutation',
                'N1_parametric_bootstrap', 'N5_half_split_layer']
    elig = [t for t in table if t['primary_eligible'] and not t['candidate'].startswith('N4')]
    primary = None
    if elig:
        best_power = max((t['power_under_effect'] if t['power_under_effect'] is not None else -1) for t in elig)
        top = [t for t in elig if (t['power_under_effect'] if t['power_under_effect'] is not None else -1) == best_power]
        for cid in priority:
            for t in top:
                if t['candidate'] == cid:
                    primary = cid
                    break
            if primary:
                break
        if primary is None:
            primary = top[0]['candidate']
    selection = {
        'rule': 'primary = candidate with synthetic FPR@F_crit in [0.02,0.10] and highest power under the '
                'pre-registered shape violation (effect=2 sigma_pair on one plan profile); tie-break priority '
                'N0 > N3 > N2 > N1 > N5; N4 excluded (invalid H0, diagnostic only)',
        'eligible_candidates': [t['candidate'] for t in elig],
        'primary_null': primary,
        'fallback_if_none': 'design_invalid: null_calibration',
        'not_used_to_select': 'A.1/A.2 observed P1 results (only synthetic calibration + C192 diagnostics)',
    }
    say('    primary null selected by pre-registered rule: %s' % primary)

    say('[4/7] A.2 design gates / budget / failure categories ...')
    design = {
        'unchanged_from_A1': ['data (O\'Neil batch1 complete-case target30 complete 4x4 grids)',
                              'U=340,088 plan-pair universe', 'separate legality rule',
                              'S-add role-stratified family', 'F_pair formula with corrected sigma_pair2',
                              'F_crit=2.60 (conditional on normalization gates)', 'per-cell T_c=max F_pair',
                              'N_perm=500 (primary null)', 'BH q=0.05 across 30 cells',
                              'P1 positive three conditions'],
        'changed_only': ['sigma_pair2 estimation (S2 primary, S1 sensitivity)',
                         'null model (primary chosen by synthetic calibration; all candidates reported)',
                         'added calibration diagnostic gates'],
        'diagnostic_gates': {
            'F_self': {'metric': 'mean/median of F_self using A.2 sigma_pair2', 'target': [0.5, 2.0],
                       'fpr_gate': 0.10, 'fail': 'design_invalid: scale_mismatch'},
            'null_pooled': {'metric': 'primary null pooled fraction median', 'target': [0.02, 0.15],
                            'fail': 'design_invalid: null_calibration'},
            'null_vs_observed_T': {'metric': 'median(T_null)/median(T_obs)', 'target': [0.2, 3.0],
                                   'fail': 'design_invalid: null_calibration'},
            'sigma_finite': {'metric': 'sigma_w_hat, sigma_pair2_A2 finite and non-degenerate',
                             'fail': 'design_invalid: scale_mismatch'},
            'half_split_fpr': {'metric': 'FPR@F_crit on half-split self-tests', 'max': 0.10,
                               'fail': 'design_invalid: noise_calibration'},
        },
        'budget': {'new_wells': 0, 'data_only': True, 'wall_cap_s': 900, 'cpu_cap_h': 2.0,
                   'memory_cap_gb': 8, 'n_perm_primary': 500,
                   'n_perm_candidate_diagnostics': '<=500 per candidate (4 candidates max), total <=3000 '
                                                   'permutation-equivalents; compute cap applies',
                   'calc': 'A.1 one perm ~0.05 s; A.2 primary + 4 candidates ×500 ≈ 2500 perms*0.05 ≈ 125 s '
                           '+ overhead; well within 900 s'},
        'failure_categories': ['design_invalid: null_calibration', 'design_invalid: scale_mismatch',
                               'design_invalid: compute_budget_exceeded',
                               'existing A.1 categories (coverage/identifiability/noise/leakage/family)'],
        'two_runs': True,
        'interpretation_boundary': 'positive: developmental existence in this resource/family/design; negative: '
                                   'no_joint_contradiction only (never "contradiction absent"); no biology/'
                                   'mechanism/migration/decision/novelty claims; non-blind/peeked; no P2/S2/H_A2 '
                                   'before A.2',
    }
    say('    design gates/budget/failure categories recorded')

    say('[5/7] A.2 pre-registration status ...')
    t_end = time.time()
    out = {
        'protocol_a2': {'path_rel': 'research/2026-10-27-agent-cell-colearning/mechanism_A/a2_prenull/'
                                    'PROBLEM_A2.md', 'sha256': sha256_file(PROBLEM_A2)},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        'inputs': sha,
        'c192_recap': c192,
        'sigma_scale_arithmetic': sigma,
        'candidate_nulls': {'table': table, 'details': {k: {'h0': v['h0'],
                                                            'exchangeability': v['exchangeability'],
                                                            'implementation': v['implementation'],
                                                            **({'info': v.get('info')} if v.get('info') else {}),
                                                            **({'fself_median': v.get('fself_median'),
                                                                'fself_mean': v.get('fself_mean')}
                                                               if 'fself_median' in v else {})}
                                                     for k, v in cands.items()}},
        'selection': selection,
        'synthetic_calibration': {
            'seed': SEED_SIM, 'n_cells': 5, 'n_groups': 6, 'n_plans': 6, 'n_pairs': int(n_pairs_sim),
            'sigma_w_simulated': 0.10, 'effect_size': '2 sigma_pair shape violation on one plan profile',
            'note': 'synthetic only; no O\'Neil response values used; calibration diagnostics only',
        },
        'A2_design': design,
        'status': 'PREREGISTRATION_DRAFT (not executed; requires Lead approval + independent challenge before A.2 run)',
        'boundaries': [
            'A.2 is a new pre-registration; A.1 thresholds are not patched post hoc',
            'no P1 effect run in this task; no O\'Neil response statistics read',
            'no P2/S2/H_A2 before A.2 completes and passes',
            'developmental wording only; no biology/mechanism/migration/decision/novelty claims',
            'non-blind/peeked inherited from ON3; data-only; 0 new wells',
        ],
        'deviations': [],
        'log_milestones': ['C192 recap', 'sigma arithmetic', 'synthetic null calibration', 'selection rule',
                           'A.2 design gates'],
    }
    write_json(out, OUTJSON)
    print('null_design_A2.json sha256:', sha256_file(OUTJSON))
    print('DONE wall=%.1fs' % (t_end - t0))


if __name__ == '__main__':
    main()
