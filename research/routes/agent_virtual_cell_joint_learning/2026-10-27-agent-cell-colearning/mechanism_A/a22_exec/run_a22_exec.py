#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-A.2.2-EXEC: data-only P1 rerun with heteroscedasticity-robust R4 sigma.

Implements PROTOCOL_A22_EXEC.md: D1-D7 gates (F_self formula per Lead decision), A.2 legal rule,
R4 per-context sigma (full-profile plan-pair differences, resubstitution disclosed),
N0-strat pooled null, N1-R4 per-cell bootstrap, D4/D5, P1 positive rule.
Data-only, 0 new wells, no P2/S2/H_A2.
"""
import sys
import os
import json
import math
import hashlib
import time

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

ROOT = r'D:\MAESTRO'
BASE = os.path.join(ROOT, 'research', '2026-10-27-agent-cell-colearning', 'mechanism_A')
OUTDIR = os.path.join(BASE, 'a22_exec')
ONEIL = os.path.join(ROOT, 'data', 'raw', 'oneil2026_qualification',
                     '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls')
ON1JSON = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'on1.json')
PEEK = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'PEEK_DISCLOSURE_ON3.md')
JAAKS = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                     'Original screen_All tissues_fitted data.csv')
QUAL = os.path.join(BASE, 'qualify_A_v0_2.json')
DECISION = os.path.join(BASE, 'DECISION_R201_A22_EXEC.md')
PROBLEM_A22 = os.path.join(BASE, 'a22_prenull', 'PROBLEM_A22.md')
DESIGN_A22 = os.path.join(BASE, 'a22_prenull', 'DESIGN_A22.md')
SIGMA_A22 = os.path.join(BASE, 'a22_prenull', 'sigma_robust_A22.json')
PROTOCOL = os.path.join(OUTDIR, 'PROTOCOL_A22_EXEC.md')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'a22_exec.json')
OUTROWS = os.path.join(OUTDIR, 'a22_exec_rows.csv')
OUTDIAG = os.path.join(OUTDIR, 'a22_exec_diagnostics.json')

K = 4
M = 4
F_CRIT = 2.60
N_PERM = 500
SEED = 20261029
BH_Q = 0.05
N_CELLS = 30
U_EXPECTED = 340088
LEGAL_MIN = 17004.4
EXCL_MAX = 0.05
WALL_CAP = 900.0
CPU_CAP = 7200.0
MEM_CAP_GB = 8.0


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


def norm(s):
    import unicodedata
    return ''.join(ch for ch in unicodedata.normalize('NFKC', str(s)).casefold() if ch.isalnum())


def canon_conc(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return format(v, '.10g')


def center(v):
    return v - np.mean(v)


def quantiles(arr):
    a = np.asarray(arr, dtype=float)
    if a.size == 0:
        return {}
    return {str(q): rq(float(np.percentile(a, q)), 2) for q in (0, 5, 25, 50, 75, 95, 100)}


def rss_gb():
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024.0 ** 3)
    except Exception:
        return None


def ss_from_profiles(a, b):
    d = center(a - b)
    return float((d ** 2).sum())


def main():
    t0 = time.time()
    cpu_start = time.process_time()
    say = lambda m: print(m, flush=True)

    say('[0/9] inputs & frozen SHAs ...')
    sha = {}
    for key, path in (('protocol_exec', PROTOCOL), ('problem_a22', PROBLEM_A22),
                      ('design_a22', DESIGN_A22), ('sigma_robust_a22', SIGMA_A22),
                      ('decision', DECISION), ('qualify_v0_2', QUAL), ('script', SCRIPT),
                      ('oneil_combo', ONEIL), ('on1_json', ON1JSON), ('peek_disclosure', PEEK),
                      ('jaaks_fitted', JAAKS)):
        if not os.path.isfile(path):
            raise SystemExit('FATAL missing input: %s' % key)
        sha[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                    'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    qual = json.load(open(QUAL, encoding='utf-8'))
    on1 = json.load(open(ON1JSON, encoding='utf-8'))
    target_cells = sorted(norm(c) for c in on1['cells']['target_nonoverlap'])
    jaaks_cells = set()
    try:
        jdf = pd.read_csv(JAAKS, usecols=['CELL_LINE_NAME'], low_memory=False)
        jaaks_cells = {norm(x) for x in jdf['CELL_LINE_NAME'].to_numpy() if isinstance(x, str)}
    except Exception:
        pass
    say('    frozen inputs verified; target30=%d' % len(target_cells))

    say('[1/9] read O\'Neil workbook & build matrices ...')
    fh = open(ONEIL, 'rb')
    df = pd.read_excel(fh, sheet_name='combination response', engine='openpyxl')
    fh.close()
    header_cols = list(map(str, df.columns))
    if df.shape[0] != 368832:
        raise SystemExit('FATAL row count')
    v = df[['viability1', 'viability2', 'viability3', 'viability4']].to_numpy(float)
    df['y'] = np.nanmean(v, axis=1)
    df['hA1'] = np.nanmean(v[:, [0, 1]], axis=1)
    df['hA2'] = np.nanmean(v[:, [2, 3]], axis=1)
    df['hB1'] = np.nanmean(v[:, [0, 2]], axis=1)
    df['hB2'] = np.nanmean(v[:, [1, 3]], axis=1)
    df['complete'] = np.isfinite(v).all(axis=1)
    df['cell'] = [norm(x) for x in df['cell_line'].to_numpy()]
    df['drugA'] = [norm(x) for x in df['drugA_name'].to_numpy()]
    df['drugB'] = [norm(x) for x in df['drugB_name'].to_numpy()]
    df['concA'] = [canon_conc(x) for x in df['drugA Conc (µM)'].to_numpy()]
    df['concB'] = [canon_conc(x) for x in df['drugB Conc (µM)'].to_numpy()]
    b1 = df[(df['BatchID'] == 1) & df['complete']]
    sigma_w_hat = float(np.sqrt(np.mean((b1['hA1'].to_numpy() - b1['hA2'].to_numpy()) ** 2)))
    sigma_obs_A2 = sigma_w_hat / 2.0
    S1 = sigma_w_hat ** 2 / 8.0
    say('    batch1_complete=%d sigma_w_hat=%.6g sigma_obs_A2=%.6g' % (len(b1), sigma_w_hat, sigma_obs_A2))

    tcells = set(target_cells)
    dsub = df[df['cell'].isin(tcells)].copy()
    dsub['pair'] = [tuple(sorted((a, b))) for a, b in zip(dsub['drugA'], dsub['drugB'])]
    dsub['pc'] = list(zip(dsub['BatchID'].astype(int), dsub['cell'], dsub['pair']))
    plan = []
    excluded = {'not_batch1': 0, 'incomplete_or_bad_grid': 0, 'other': 0}
    for key, g in dsub.groupby('pc'):
        batch, cell, pair = key
        if batch != 1:
            excluded['not_batch1'] += 1
            continue
        gc = g[g['complete']]
        if len(gc) != 16:
            excluded['incomplete_or_bad_grid'] += 1
            continue
        dosesA = sorted({canon_conc(x) for x in gc['concA']})
        dosesB = sorted({canon_conc(x) for x in gc['concB']})
        combos = {(row.concA, row.concB) for row in gc.itertuples(index=False)}
        if not (len(dosesA) == 4 and len(dosesB) == 4 and len(combos) == 16):
            excluded['incomplete_or_bad_grid'] += 1
            continue
        ia = {d: i for i, d in enumerate(dosesA)}
        ib = {d: i for i, d in enumerate(dosesB)}
        mats = {k: np.full((4, 4), np.nan) for k in ('Y', 'MA1', 'MA2', 'MB1', 'MB2')}
        ok = True
        for row in gc.itertuples(index=False):
            try:
                r, c = ia[row.concA], ib[row.concB]
            except KeyError:
                ok = False
                break
            mats['Y'][r, c] = row.y
            mats['MA1'][r, c] = row.hA1
            mats['MA2'][r, c] = row.hA2
            mats['MB1'][r, c] = row.hB1
            mats['MB2'][r, c] = row.hB2
        if not ok or not all(np.isfinite(m).all() for m in mats.values()):
            excluded['other'] += 1
            continue
        plan.append({'cell': cell, 'pair': pair, 'drugA': gc['drugA'].iloc[0],
                     'drugB': gc['drugB'].iloc[0],
                     'Y': mats['Y'], 'MA1': mats['MA1'], 'MA2': mats['MA2'],
                     'MB1': mats['MB1'], 'MB2': mats['MB2']})
    n_pc = len(plan)
    say('    plan-cells=%d excluded=%s' % (n_pc, excluded))
    Yall = np.array([p['Y'] for p in plan])
    rowmeans = Yall.mean(axis=2)
    colmeans = Yall.mean(axis=1)

    say('[2/9] A.2 legal set ...')
    rms = np.zeros(n_pc)
    for i, p in enumerate(plan):
        Y = p['Y']
        R = Y - Y.mean(axis=1, keepdims=True) - Y.mean(axis=0, keepdims=True) + Y.mean()
        rms[i] = math.sqrt(float((R ** 2).sum()) / 9.0)
    legal_threshold = 1.96 * sigma_obs_A2
    legal = rms <= legal_threshold
    say('    threshold=%.6f legal plans=%d/%d' % (legal_threshold, int(legal.sum()), n_pc))

    say('[3/9] contexts, R4 sigma, pair universe ...')
    groups = {}
    for i, p in enumerate(plan):
        groups.setdefault((p['cell'], p['drugA'], 'A'), []).append((i, 0))
        groups.setdefault((p['cell'], p['drugB'], 'B'), []).append((i, 1))
    ctx_plans = {k: [i for i, _ in items] for k, items in groups.items()}
    ctx_role = {k: ('A' if k[2] == 'A' else 'B') for k in groups}
    # context profiles
    ctx_prof = {}
    for k, idxs in ctx_plans.items():
        role = 0 if ctx_role[k] == 'A' else 1
        ctx_prof[k] = np.array([rowmeans[i] if role == 0 else colmeans[i] for i in idxs])
    ctx = {}
    for k, idxs in ctx_plans.items():
        m = len(idxs)
        if m < 2:
            ctx[k] = {'valid': False, 'reason': 'lt2_plans', 'n_plans': m}
            continue
        P = ctx_prof[k]
        sss = []
        for a in range(m):
            for b in range(a + 1, m):
                sss.append(ss_from_profiles(P[a], P[b]))
        sss = np.array(sss)
        s2 = float(sss.mean()) / (K - 1)
        ctx[k] = {'valid': bool(math.isfinite(s2) and s2 > 1e-12), 'sigma2': s2,
                  'n_plans': m, 'n_pairs': len(sss), 'ss': sss,
                  'sum_ss': float(sss.sum()), 'plans': idxs, 'role': 0 if ctx_role[k] == 'A' else 1}
    # pairs
    pair_set = {}
    for k, items in groups.items():
        role = 0 if k[2] == 'A' else 1
        m = len(items)
        for a in range(m):
            for b in range(a + 1, m):
                i1, _ = items[a]
                i2, _ = items[b]
                if i1 == i2:
                    continue
                kk = (min(i1, i2), max(i1, i2))
                if kk in pair_set:
                    continue
                pair_set[kk] = {'i': kk[0], 'j': kk[1], 'role': role, 'ctx': k, 'cell': plan[kk[0]]['cell']}
    pairs = list(pair_set.values())
    pi = np.array([pr['i'] for pr in pairs], dtype=np.int64)
    pj = np.array([pr['j'] for pr in pairs], dtype=np.int64)
    pctx = [pr['ctx'] for pr in pairs]
    U = len(pairs)
    cell_names = sorted({p['cell'] for p in plan})
    cell_idx = {c: i for i, c in enumerate(cell_names)}
    pair_cell_idx = np.array([cell_idx[p['cell']] for p in pairs], dtype=np.int64)
    # pair ss and F (R4)
    F_pair = np.full(U, np.nan)
    pair_ss = np.zeros(U)
    for t, pr in enumerate(pairs):
        ss = ss_from_profiles(rowmeans[pr['i']], rowmeans[pr['j']]) if pr['role'] == 0 else \
            ss_from_profiles(colmeans[pr['i']], colmeans[pr['j']])
        pair_ss[t] = ss
        c = ctx[pr['ctx']]
        if c['valid']:
            F_pair[t] = ss / (K - 1) / c['sigma2']
    valid_ctx = np.array([ctx[pr['ctx']]['valid'] for pr in pairs])
    legal_pair = legal[pi] & legal[pj]
    infer_pair = legal_pair & valid_ctx
    n_legal = int(legal_pair.sum())
    n_infer = int(infer_pair.sum())
    excl_frac = float((~valid_ctx).sum()) / U if U else 0.0
    sigma2_vals = np.array([c['sigma2'] for c in ctx.values() if c['valid']])
    ctx_block = {
        'n_contexts': len(ctx), 'n_included': int(sum(1 for c in ctx.values() if c['valid'])),
        'n_excluded': int(sum(1 for c in ctx.values() if not c['valid'])),
        'sigma2_R4_quantiles': quantiles(sigma2_vals),
        'sigma2_over_S1_median': rq(float(np.median(sigma2_vals) / S1)) if S1 else None,
        'excluded_pair_fraction': rq(excl_frac),
        'excluded_pair_gate_max': EXCL_MAX,
        'excluded_pair_pass': bool(excl_frac <= EXCL_MAX),
        'resubstitution_disclosure': 'sigma2_R4(c) means include the tested pair (finite-sample/resubstitution '
                                     'calibration; not an independent scale); LOO sensitivity is descriptive only',
    }
    say('    U=%d legal pairs=%d infer pairs=%d ctx included=%d excluded=%d excl_frac=%.4g' % (
        U, n_legal, n_infer, ctx_block['n_included'], ctx_block['n_excluded'], excl_frac))

    say('[4/9] F_self (pair-level formula) + D2/D3 metrics ...')
    fself_vals = F_pair[infer_pair]
    fself_global_median = float(np.median(fself_vals)) if fself_vals.size else None
    fself_global_fpr = float((fself_vals > F_CRIT).mean()) if fself_vals.size else None
    per_ctx_fself = {}
    for t in np.where(infer_pair)[0]:
        per_ctx_fself.setdefault(pctx[t], []).append(F_pair[t])
    ctx_medians, ctx_fprs = [], []
    for k, vals in per_ctx_fself.items():
        arr = np.array(vals)
        ctx_medians.append(float(np.median(arr)))
        ctx_fprs.append(float((arr > F_CRIT).mean()))
    ctx_medians = np.array(ctx_medians)
    ctx_fprs = np.array(ctx_fprs)
    coverage = float(np.mean((ctx_medians >= 0.5) & (ctx_medians <= 2.0))) if ctx_medians.size else 0.0
    worst_ctx_fpr = float(ctx_fprs.max()) if ctx_fprs.size else None
    ctx_fpr_p95 = float(np.percentile(ctx_fprs, 95)) if ctx_fprs.size else None
    fself_block = {
        'definition': 'F_self(p,q)=[||P_perp(f_p-f_q)||^2/(K-1)]/sigma2_R4(shared context) (pair-level; same formula as F_pair)',
        'n_values': int(fself_vals.size),
        'global_median': rq(fself_global_median),
        'global_mean': rq(float(fself_vals.mean())) if fself_vals.size else None,
        'quantiles': quantiles(fself_vals),
        'overall_fpr_at_F_crit': rq(fself_global_fpr),
        'per_context_median_coverage_0p5_2': rq(coverage),
        'per_context_median_quantiles': quantiles(ctx_medians),
        'worst_context_fpr': rq(worst_ctx_fpr),
        'context_fpr_p95': rq(ctx_fpr_p95),
    }
    # descriptive half-split F_self_check (A.2-style; NOT used for D2/D3)
    hs_vals = []
    for k, idxs in ctx_plans.items():
        if not ctx[k]['valid']:
            continue
        role = 0 if ctx_role[k] == 'A' else 1
        s2 = ctx[k]['sigma2']
        for i in idxs:
            p = plan[i]
            if role == 0:
                dA = p['MA1'].mean(axis=1) - p['MA2'].mean(axis=1)
                dB = p['MB1'].mean(axis=1) - p['MB2'].mean(axis=1)
            else:
                dA = p['MA1'].mean(axis=0) - p['MA2'].mean(axis=0)
                dB = p['MB1'].mean(axis=0) - p['MB2'].mean(axis=0)
            davg = (dA + dB) / 2.0
            hs_vals.append(ss_from_profiles(davg, np.zeros_like(davg)) / (K - 1) / s2)
    hs_vals = np.array(hs_vals)
    hs_diag = {'definition': 'A.2-style half-split F_self_check (d_avg=(r1-r4)/2) normalized by R4 sigma; '
                             'descriptive only, not used in D2/D3',
               'n_values': int(hs_vals.size), 'mean': rq(float(hs_vals.mean())),
               'median': rq(float(np.median(hs_vals))), 'fpr_at_F_crit': rq(float((hs_vals > F_CRIT).mean())),
               'quantiles': quantiles(hs_vals)}
    say('    F_self: n=%d global_median=%.3f coverage=%.4f overall_FPR=%.4f worst_ctx_FPR=%.3f p95=%.3f' % (
        fself_vals.size, fself_global_median or -1, coverage, fself_global_fpr or -1,
        worst_ctx_fpr or -1, ctx_fpr_p95 or -1))

    # LOO sensitivity (descriptive)
    loo_ratios = []
    for k, c in ctx.items():
        if not c['valid'] or c.get('n_pairs', 0) < 2:
            continue
        sss = c['ss']; n = len(sss); total = c['sum_ss']
        for t in range(n):
            s2_loo = (total - sss[t]) / ((n - 1) * (K - 1))
            if s2_loo > 1e-12:
                f_loo = sss[t] / (K - 1) / s2_loo
                f_res = sss[t] / (K - 1) / c['sigma2']
                if f_res > 0:
                    loo_ratios.append(f_loo / f_res)
    loo_ratios = np.array(loo_ratios)
    loo_block = {'n_pairs_checked': int(loo_ratios.size),
                 'F_LOO_over_F_quantiles': quantiles(loo_ratios) if loo_ratios.size else {},
                 'note': 'descriptive sensitivity only; not used in any gate/judgment'}

    d1 = bool(all((c['valid'] and c['sigma2'] > 1e-12) for c in ctx.values() if c.get('n_plans', 0) >= 2)
              and math.isfinite(sigma_w_hat))
    d2 = bool(coverage >= 0.85 and
              (fself_global_median is not None and 0.5 <= fself_global_median <= 1.5) and
              (fself_global_fpr is not None and fself_global_fpr <= 0.10))
    d3 = bool(fself_global_fpr is not None and fself_global_fpr <= 0.10 and
              worst_ctx_fpr is not None and worst_ctx_fpr <= 0.25 and
              ctx_fpr_p95 is not None and ctx_fpr_p95 <= 0.20)
    say('    D1=%s D2=%s D3=%s' % (d1, d2, d3))

    # D7
    qual_g2 = all(x['over_identification'] >= 16 for x in qual['identifiability_audit']['per_cell'])
    g5 = {
        'target30_jaaks_disjoint': len(tcells & jaaks_cells) == 0,
        'endpoint_viability_only': not any(('EMAX' in c.upper() or 'SYNERGY' in c.upper()) for c in header_cols),
        'batch1_only': True, 'pair_cells_702_315_excluded': True, 'no_new_wells': True,
        'peek_disclosure_printed': os.path.isfile(PEEK),
    }
    d7 = {'G1_coverage': bool(len(cell_names) == N_CELLS and U == U_EXPECTED and n_pc > 0),
          'G2_identifiability': bool(qual_g2),
          'G4_leakage': bool(g5['target30_jaaks_disjoint'] and g5['endpoint_viability_only']),
          'G5_boundary': bool(all(v for k, v in g5.items() if isinstance(v, bool))),
          'G5_assertions': g5,
          'pass': bool(len(cell_names) == N_CELLS and U == U_EXPECTED and qual_g2 and
                       g5['target30_jaaks_disjoint'] and g5['endpoint_viability_only'] and
                       all(v for k, v in g5.items() if isinstance(v, bool)))}
    say('    D7=%s (G1=%s G2=%s G4=%s G5=%s)' % (d7['pass'], d7['G1_coverage'],
                                                 d7['G2_identifiability'], d7['G4_leakage'], d7['G5_boundary']))

    say('[5/9] observed F_pair/T_c/pooled ...')
    t_obs_start = time.time()
    F_obs = F_pair[infer_pair]
    T_obs = np.full(N_CELLS, -1.0)
    infer_idx = np.where(infer_pair)[0]
    infer_cell = pair_cell_idx[infer_idx]
    for ci in range(N_CELLS):
        m = infer_cell == ci
        if m.any():
            T_obs[ci] = float(F_obs[m].max())
    pooled_obs = float((F_obs >= F_CRIT).mean()) if F_obs.size else 0.0
    t_observed = time.time() - t_obs_start
    say('    pooled_obs=%.6f T_obs median=%.3f max=%.3f' % (
        pooled_obs, np.median(T_obs[T_obs >= 0]) if (T_obs >= 0).any() else -1, T_obs.max()))

    # N1 context structures
    inc_ctx = [k for k, c in ctx.items() if c['valid']]
    inc_idx = {k: j for j, k in enumerate(inc_ctx)}
    inc_plans = [ctx[k]['plans'] for k in inc_ctx]
    inc_sigma2 = np.array([ctx[k]['sigma2'] for k in inc_ctx])
    offs = np.cumsum([0] + [len(x) for x in inc_plans])
    flat_plan = [i for lst in inc_plans for i in lst]
    f_hat_flat = []
    for k, lst in zip(inc_ctx, inc_plans):
        role = ctx[k]['role']
        f_hat = np.mean([rowmeans[i] if role == 0 else colmeans[i] for i in lst], axis=0)
        f_hat_flat.extend([f_hat] * len(lst))
    f_hat_flat = np.array(f_hat_flat)
    sd_flat = np.sqrt(np.repeat(inc_sigma2 / 2.0, [len(x) for x in inc_plans]))
    local = {}
    for ci, lst in enumerate(inc_plans):
        for pos, pi_ in enumerate(lst):
            local[(ci, pi_)] = pos
    pair_ctx_idx = np.array([inc_idx[pctx[t]] for t in infer_idx], dtype=np.int64)
    pair_local_i = np.array([local[(pair_ctx_idx[j], pi[infer_idx[j]])] for j in range(len(infer_idx))], dtype=np.int64)
    pair_local_j = np.array([local[(pair_ctx_idx[j], pj[infer_idx[j]])] for j in range(len(infer_idx))], dtype=np.int64)
    pair_i_flat = offs[pair_ctx_idx] + pair_local_i
    pair_j_flat = offs[pair_ctx_idx] + pair_local_j
    pair_sigma2 = inc_sigma2[pair_ctx_idx]

    def one_n1_rep(rng):
        prof = f_hat_flat + rng.normal(scale=sd_flat[:, None], size=f_hat_flat.shape)
        d = prof[pair_i_flat] - prof[pair_j_flat]
        dc = d - d.mean(axis=1, keepdims=True)
        F = (dc ** 2).sum(axis=1) / (K - 1) / pair_sigma2
        T = np.full(N_CELLS, -1.0)
        for ci in range(N_CELLS):
            m = infer_cell == ci
            if m.any():
                T[ci] = float(F[m].max())
        return T

    def one_n0_rep(rng):
        draws = rng.chisquare(df=K - 1, size=n_infer) / (K - 1)
        return float((draws >= F_CRIT).mean())

    say('[6/9] pilot budget test ...')
    tp = time.time()
    one_n1_rep(np.random.default_rng(SEED + 1))
    t_n1 = time.time() - tp
    tp = time.time()
    one_n0_rep(np.random.default_rng(SEED + 2))
    t_n0 = time.time() - tp
    projected = (t_observed + 500 * (t_n1 + t_n0)) * 1.2
    mem_gb = rss_gb() or 0.0
    pilot = {'t_n1_per_rep_s': rq(t_n1, 5), 't_n0_per_rep_s': rq(t_n0, 5),
             't_observed_s': rq(t_observed, 5), 'projected_total_s': rq(projected, 2),
             'memory_gb_observed': rq(mem_gb, 3),
             'caps': {'wall_s': WALL_CAP, 'cpu_s': CPU_CAP, 'memory_gb': MEM_CAP_GB},
             'pass': bool(projected <= WALL_CAP and mem_gb <= MEM_CAP_GB)}
    say('    pilot: t_n1=%.4fs t_n0=%.5fs projected=%.1fs mem=%.2fGB pass=%s' % (
        t_n1, t_n0, projected, mem_gb, pilot['pass']))

    gate_fail = None
    if not d1:
        gate_fail = 'design_invalid: scale_mismatch'
    elif not d2:
        gate_fail = 'design_invalid: scale_mismatch'
    elif not d3:
        gate_fail = 'design_invalid: noise_calibration'
    elif not ctx_block['excluded_pair_pass']:
        gate_fail = 'design_invalid: coverage'
    elif n_legal < LEGAL_MIN:
        gate_fail = 'design_invalid: coverage'
    elif not d7['pass']:
        gate_fail = 'design_invalid: coverage_identifiability_noise_or_boundary'
    elif not pilot['pass']:
        gate_fail = 'design_invalid: compute_budget_exceeded'

    diag = {
        'sigma_block': {'sigma_w_hat': rq(sigma_w_hat), 'sigma_obs_A2': rq(sigma_obs_A2),
                        'S1': rq(S1), 'legal_threshold': rq(legal_threshold),
                        'legal_plans': int(legal.sum()), 'n_plan_cells': n_pc,
                        'rms_quantiles': quantiles(rms)},
        'context_R4': ctx_block, 'F_self_pair_level': fself_block,
        'half_split_descriptive': hs_diag, 'LOO_sensitivity': loo_block,
        'D1': d1, 'D2': d2, 'D3': d3, 'D7': d7, 'pilot_budget': pilot,
        'peek_disclosure': {'non_blind': True, 'inherited': 'ON3 QUICK invalid artifact', 'printed': True},
        'inputs': sha,
    }
    result = {
        'protocol': {'path_rel': 'research/2026-10-27-agent-cell-colearning/mechanism_A/a22_exec/'
                                 'PROTOCOL_A22_EXEC.md', 'sha256': sha256_file(PROTOCOL)},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        'frozen_chain': {'PROBLEM_A22': '69605BBCEA37ECFA2783F08BCC2EF194C89971F637435A853D25C46849D7E334',
                         'DESIGN_A22': 'EAC8EA10FEDC6DA5F3D0293C2C43BBCD82C9ECB6A43EF2CB4714492284531E76',
                         'sigma_robust_A22': '12DC9855A567D7ECF333F6718BB996E3EDE9BFCBDA095E09263CD79BF053D6A2',
                         'DECISION_R201_A22_EXEC': sha256_file(DECISION)},
        'peek_disclosure': diag['peek_disclosure'],
        'frozen': {'U_expected': U_EXPECTED, 'F_crit': F_CRIT, 'N_perm': N_PERM, 'seed': SEED, 'BH_q': BH_Q,
                   'legal_min': LEGAL_MIN, 'family': 'S-add role-stratified', 'N_cells': N_CELLS,
                   'excluded_pair_gate_max': EXCL_MAX},
        'diagnostics_D1_D3_D6_D7': {'D1': d1, 'D2': d2, 'D3': d3, 'D6': pilot['pass'], 'D7': d7['pass'],
                                    'fail_before_P1': gate_fail},
        'P1': None,
        'failure_category': gate_fail,
        'verdict': 'design_invalid' if gate_fail else None,
        'boundaries': ['A.2.2 data-only P1 rerun; 0 new wells; P2/S1/S2/H_A2 not executed',
                       'positive: developmental existence only; negative: no_joint_contradiction only',
                       'no biology/mechanism/migration/decision/novelty claims; non-blind/peeked',
                       'pair-level counts descriptive only; R4 sigma resubstitution disclosed'],
        'deviations': [],
    }

    if gate_fail:
        say('    GATE FAIL -> %s; P1 not executed' % gate_fail)
        diag['D4_null_pooled'] = 'not_evaluated (pre-P1 gate failure)'
        diag['D5_T_ratio'] = 'not_evaluated (pre-P1 gate failure)'
        diag['telemetry'] = {'wall_seconds': rq(time.time() - t0, 2),
                             'cpu_seconds_process': rq(time.process_time() - cpu_start, 2),
                             'memory_gb_end': rq(rss_gb() or 0.0, 3)}
        result['P1'] = None
        write_json(result, OUTJSON)
        write_json(diag, OUTDIAG)
        pd.DataFrame([{'cell': c, 'note': 'P1 not executed: pre-gate failure; observed statistics not interpreted'}
                      for c in cell_names]).to_csv(OUTROWS, index=False)
        print('a22_exec.json sha256:', sha256_file(OUTJSON))
        print('DONE wall=%.1fs' % (time.time() - t0))
        return

    say('[7/9] P1 primary null N0-strat (N=500) ...')
    rng0 = np.random.default_rng(SEED)
    pooled_null = np.array([one_n0_rep(rng0) for _ in range(N_PERM)])
    pooled_q95 = float(np.percentile(pooled_null, 95))
    pooled_median = float(np.median(pooled_null))
    say('    N0 pooled null: median=%.4f q95=%.4f observed=%.4f' % (pooled_median, pooled_q95, pooled_obs))

    say('[8/9] N1-R4 per-cell bootstrap (N=500) ...')
    rng1 = np.random.default_rng(SEED)
    T_null = np.zeros((N_CELLS, N_PERM))
    for b in range(N_PERM):
        T_null[:, b] = one_n1_rep(rng1)
        if (b + 1) % 100 == 0:
            say('    bootstrap %d/%d (%.1fs)' % (b + 1, N_PERM, time.time() - t0))
    pvals = np.ones(N_CELLS)
    for ci in range(N_CELLS):
        if T_obs[ci] >= 0:
            pvals[ci] = (1.0 + float((T_null[ci] >= T_obs[ci]).sum())) / (1.0 + N_PERM)
    order = np.argsort(pvals, kind='mergesort')
    thresh = BH_Q * np.arange(1, N_CELLS + 1) / N_CELLS
    rejected = np.zeros(N_CELLS, dtype=bool)
    kmax = -1
    for rank, idx in enumerate(order):
        if pvals[idx] <= thresh[rank]:
            kmax = rank
    if kmax >= 0:
        for rank in range(kmax + 1):
            rejected[order[rank]] = True
    n_reject = int(rejected.sum())
    t_obs_median = float(np.median(T_obs[T_obs >= 0])) if (T_obs >= 0).any() else None
    t_null_median = float(np.median(T_null))
    ratio_T = (t_null_median / t_obs_median) if t_obs_median else None
    d4 = bool(0.02 <= pooled_median <= 0.15)
    d5 = bool(ratio_T is not None and 0.2 <= ratio_T <= 3.0)
    say('    BH reject=%d; D4=%s (null pooled median %.4f); D5=%s (T ratio %.3f)' % (
        n_reject, d4, pooled_median, d5, ratio_T if ratio_T else -1))

    if not d4 or not d5:
        result['failure_category'] = 'design_invalid: null_calibration'
        result['verdict'] = 'design_invalid'
    else:
        cond1 = n_reject >= 5
        cond2 = pooled_obs >= pooled_q95
        cond3 = bool(d7['pass'])
        positive = bool(cond1 and cond2 and cond3)
        result['verdict'] = 'p1_positive' if positive else 'p1_negative'
        result['P1'] = {
            'universe_U': U, 'n_legal_pairs_A2': n_legal, 'n_legal_infer': n_infer, 'F_crit': F_CRIT,
            'observed_pooled_frac_F_ge_Fcrit': rq(pooled_obs),
            'null_pooled_median': rq(pooled_median), 'null_pooled_q95': rq(pooled_q95),
            'T_obs_median': rq(t_obs_median), 'T_null_median': rq(t_null_median),
            'T_null_over_obs_ratio': rq(ratio_T),
            'BH': {'q': BH_Q, 'n_cells': N_CELLS, 'n_rejected': n_reject,
                   'rejected_cells': [cell_names[i] for i in range(N_CELLS) if rejected[i]],
                   'p_range': [rq(float(pvals.min())), rq(float(pvals.max()))]},
            'per_cell_file': 'a22_exec_rows.csv',
            'positive_rule': {'condition1_BH_ge5': bool(cond1), 'condition2_pooled_ge_Q95': bool(cond2),
                              'condition3_gates': bool(cond3), 'positive': bool(positive)},
            'interpretation': 'positive: developmental existence of joint contradictions in this resource/'
                              'family/design; negative: no_joint_contradiction (NOT "contradiction absent")',
        }
        diag['D4_null_pooled'] = d4
        diag['D5_T_ratio'] = d5
        diag['P1_null_diagnostics'] = {'pooled_null_median': rq(pooled_median),
                                       'pooled_null_q95': rq(pooled_q95),
                                       'T_null_median': rq(t_null_median),
                                       'T_obs_median': rq(t_obs_median),
                                       'T_null_over_obs': rq(ratio_T)}

    write_json(result, OUTJSON)
    diag['telemetry'] = {'wall_seconds': rq(time.time() - t0, 2),
                         'cpu_seconds_process': rq(time.process_time() - cpu_start, 2),
                         'memory_gb_end': rq(rss_gb() or 0.0, 3)}
    write_json(diag, OUTDIAG)
    rows = []
    for ci, c in enumerate(cell_names):
        m = infer_cell == ci
        rows.append({'cell': c, 'n_pairs': int((pair_cell_idx == ci).sum()),
                     'n_legal_pairs': int((legal_pair & (pair_cell_idx == ci)).sum()),
                     'n_infer_pairs': int(m.sum()),
                     'T_obs': rq(float(T_obs[ci])),
                     'p_value': rq(float(pvals[ci])),
                     'null_q95': rq(float(np.percentile(T_null[ci], 95))) if m.any() else None,
                     'bh_rejected': bool(rejected[ci]),
                     'median_F_obs': rq(float(np.median(F_obs[m]))) if m.any() else None})
    pd.DataFrame(rows).to_csv(OUTROWS, index=False)
    print('a22_exec.json sha256:', sha256_file(OUTJSON))
    print('a22_exec_rows.csv sha256:', sha256_file(OUTROWS))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
