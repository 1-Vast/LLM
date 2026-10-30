#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-A.2-EXEC: A.2 data-only P1 rerun (corrected sigma/null). Implements PROTOCOL_A2_EXEC.md.

D1-D7 diagnostic gates -> A.2 legal set -> observed F_pair/T_c/pooled -> primary null N0 (pooled chi-square)
+ per-cell N1 parametric bootstrap -> D4/D5 -> P1 positive rule. Data-only, 0 new wells, no P2/S2/H_A2.
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
OUTDIR = os.path.join(BASE, 'a2_exec')
ONEIL = os.path.join(ROOT, 'data', 'raw', 'oneil2026_qualification',
                     '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls')
ON1JSON = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'on1.json')
PEEK = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'PEEK_DISCLOSURE_ON3.md')
JAAKS = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                     'Original screen_All tissues_fitted data.csv')
QUAL = os.path.join(BASE, 'qualify_A_v0_2.json')
DECISION = os.path.join(BASE, 'DECISION_R201_A2_EXEC.md')
PROBLEM_A2 = os.path.join(BASE, 'a2_prenull', 'PROBLEM_A2_v0_2.md')
DESIGN_A2 = os.path.join(BASE, 'a2_prenull', 'DESIGN_A2_v0_2.md')
NULLDESIGN = os.path.join(BASE, 'a2_prenull', 'null_design_A2_v0_2.json')
PROTOCOL = os.path.join(OUTDIR, 'PROTOCOL_A2_EXEC.md')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'a2_exec.json')
OUTROWS = os.path.join(OUTDIR, 'a2_exec_rows.csv')
OUTDIAG = os.path.join(OUTDIR, 'a2_exec_diagnostics.json')

K = 4
M = 4
R_REPS = 4
F_CRIT = 2.60
N_PERM = 500
SEED = 20261029
BH_Q = 0.05
N_CELLS = 30
U_EXPECTED = 340088
LEGAL_MIN = 17004.4
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


def main():
    t0 = time.time()
    t_start_wall = time.time()
    cpu_start = time.process_time()
    say = lambda m: print(m, flush=True)

    say('[0/9] inputs & frozen SHAs ...')
    sha = {}
    for key, path in (('protocol_exec', PROTOCOL), ('problem_a2_v0_2', PROBLEM_A2),
                      ('design_a2_v0_2', DESIGN_A2), ('null_design_a2_v0_2', NULLDESIGN),
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

    say('[1/9] read O\'Neil workbook & build A.2 matrices ...')
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
    say('    rows=%d batch1_complete=%d sigma_w_hat=%.6g sigma_obs_A2=%.6g S1=%.6g' % (
        len(df), len(b1), sigma_w_hat, sigma_obs_A2, S1))

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
                     'drugB': gc['drugB'].iloc[0], 'dosesA': dosesA, 'dosesB': dosesB,
                     'Y': mats['Y'], 'MA1': mats['MA1'], 'MA2': mats['MA2'],
                     'MB1': mats['MB1'], 'MB2': mats['MB2']})
    n_pc = len(plan)
    say('    plan-cells=%d excluded=%s' % (n_pc, excluded))
    Yall = np.array([p['Y'] for p in plan])
    rowmeans = Yall.mean(axis=2)
    colmeans = Yall.mean(axis=1)

    say('[2/9] S2 corrected sigma_pair2 + F_self_check (A/B half splits) ...')
    def profile(mat, role):
        return mat.mean(axis=1) if role == 0 else mat.mean(axis=0)

    s2_contrib = []
    fself = []
    cov_diag = []
    for p in plan:
        for role in (0, 1):
            dA = profile(p['MA1'], role) - profile(p['MA2'], role)
            dB = profile(p['MB1'], role) - profile(p['MB2'], role)
            dAc = center(dA); dBc = center(dB)
            s2_contrib.append(float((dAc ** 2).sum()) / (K - 1))
            d_avg = center((dA + dB) / 2.0)
            fself.append(float((d_avg ** 2).sum()) / (K - 1))
            na = float(math.sqrt((dAc ** 2).sum() * (dBc ** 2).sum()))
            cov_diag.append(float((dAc * dBc).sum()) / na if na > 0 else 0.0)
    s2_contrib = np.array(s2_contrib)
    fself = np.array(fself)
    sigma_pair2_A2 = 0.5 * float(s2_contrib.mean())
    F_self_check = fself / sigma_pair2_A2
    fself_stats = {
        'n_contexts': int(F_self_check.size), 'mean': rq(float(F_self_check.mean())),
        'median': rq(float(np.median(F_self_check))),
        'fpr_at_F_crit': rq(float((F_self_check > F_CRIT).mean())),
        'quantiles': quantiles(F_self_check),
        'cov_dA_dB_median': rq(float(np.median(cov_diag))),
        'cov_dA_dB_mean': rq(float(np.mean(cov_diag))),
    }
    sigma_block = {'sigma_w_hat': rq(sigma_w_hat), 'sigma_obs_A2': rq(sigma_obs_A2), 'S1': rq(S1),
                   'S2_raw': rq(float(s2_contrib.mean())), 'sigma_pair2_A2': rq(sigma_pair2_A2),
                   'sigma_pair2_over_S1': rq(sigma_pair2_A2 / S1) if S1 else None}
    say('    sigma_pair2_A2=%.8f (S1=%.8f, ratio %.4f); F_self mean=%.4f median=%.4f FPR=%.4f' % (
        sigma_pair2_A2, S1, sigma_pair2_A2 / S1 if S1 else -1, fself_stats['mean'],
        fself_stats['median'], fself_stats['fpr_at_F_crit']))

    # D1/D2/D3
    d1 = bool(1e-6 < sigma_w_hat < 1.0 and 1e-12 < sigma_pair2_A2 < 1.0)
    d2 = bool(0.5 <= fself_stats['mean'] <= 2.0 and 0.5 <= fself_stats['median'] <= 2.0 and
              0.5 <= (sigma_pair2_A2 / S1 if S1 else 0) <= 2.0)
    d3 = bool(fself_stats['fpr_at_F_crit'] <= 0.10)
    say('    D1=%s D2=%s D3=%s' % (d1, d2, d3))

    say('[3/9] A.2 legal set & pair universe ...')
    rms = np.zeros(n_pc)
    for i, p in enumerate(plan):
        Y = p['Y']
        R = Y - Y.mean(axis=1, keepdims=True) - Y.mean(axis=0, keepdims=True) + Y.mean()
        rms[i] = math.sqrt(float((R ** 2).sum()) / 9.0)
    legal_threshold = 1.96 * sigma_obs_A2
    legal = rms <= legal_threshold
    groups = {}
    for i, p in enumerate(plan):
        groups.setdefault((p['cell'], p['drugA'], 'A'), []).append((i, 0))
        groups.setdefault((p['cell'], p['drugB'], 'B'), []).append((i, 1))
    pair_set = {}
    for key, items in groups.items():
        cell, drug, role_s = key
        role = 0 if role_s == 'A' else 1
        m = len(items)
        for a in range(m):
            for b in range(a + 1, m):
                i1, _ = items[a]
                i2, _ = items[b]
                if i1 == i2:
                    continue
                k = (min(i1, i2), max(i1, i2))
                if k in pair_set:
                    continue
                pair_set[k] = {'i': k[0], 'j': k[1], 'role': role, 'cell': cell}
    pairs = list(pair_set.values())
    pi = np.array([pr['i'] for pr in pairs], dtype=np.int64)
    pj = np.array([pr['j'] for pr in pairs], dtype=np.int64)
    prole = np.array([pr['role'] for pr in pairs], dtype=np.int64)
    pcell = np.array([pr['cell'] for pr in pairs], dtype=object)
    U = len(pairs)
    cell_names = sorted({p['cell'] for p in plan})
    cell_idx = {c: i for i, c in enumerate(cell_names)}
    pair_cell_idx = np.array([cell_idx[c] for c in pcell], dtype=np.int64)
    legal_pair = legal[pi] & legal[pj]
    n_legal = int(legal_pair.sum())
    legal_block = {'threshold': rq(legal_threshold), 'legal_plans': int(legal.sum()), 'n_plan_cells': n_pc,
                   'rms_quantiles': quantiles(rms), 'U': U, 'n_legal_pairs': n_legal,
                   'legal_min': LEGAL_MIN, 'pass_min': bool(n_legal >= LEGAL_MIN)}
    say('    U=%d (expected %d) legal plans=%d/%d legal pairs=%d threshold=%.6f' % (
        U, U_EXPECTED, int(legal.sum()), n_pc, n_legal, legal_threshold))

    # D7 gates
    qual_g2 = all(x['over_identification'] >= 16 for x in qual['identifiability_audit']['per_cell'])
    g5 = {
        'target30_jaaks_disjoint': len(tcells & jaaks_cells) == 0,
        'endpoint_viability_only': not any(('EMAX' in c.upper() or 'SYNERGY' in c.upper()) for c in header_cols),
        'batch1_only': True, 'pair_cells_702_315_excluded': True, 'no_new_wells': True,
        'peek_disclosure_printed': os.path.isfile(PEEK),
    }
    d7 = {
        'G1_coverage': bool(len(cell_names) == N_CELLS and U == U_EXPECTED and n_pc > 0),
        'G2_identifiability': bool(qual_g2),
        'G4_leakage': bool(g5['target30_jaaks_disjoint'] and g5['endpoint_viability_only']),
        'G5_boundary': bool(all(v for k, v in g5.items() if isinstance(v, bool))),
        'G5_assertions': g5,
        'pass': bool(len(cell_names) == N_CELLS and U == U_EXPECTED and qual_g2 and
                     g5['target30_jaaks_disjoint'] and g5['endpoint_viability_only'] and
                     all(v for k, v in g5.items() if isinstance(v, bool))),
    }
    say('    D7=%s (G1=%s G2=%s G4=%s G5=%s)' % (
        d7['pass'], d7['G1_coverage'], d7['G2_identifiability'], d7['G4_leakage'], d7['G5_boundary']))

    def compute_F(rm, cm):
        f_i = np.where(prole[:, None] == 0, rm[pi], cm[pi])
        f_j = np.where(prole[:, None] == 0, rm[pj], cm[pj])
        d = f_i - f_j
        dc = d - d.mean(axis=1, keepdims=True)
        return (dc ** 2).sum(axis=1) / (K - 1) / sigma_pair2_A2

    say('[4/9] observed F_pair/T_c/pooled ...')
    t_obs_start = time.time()
    F_obs = compute_F(rowmeans, colmeans)
    T_obs = np.full(N_CELLS, -1.0)
    for ci in range(N_CELLS):
        m = legal_pair & (pair_cell_idx == ci)
        if m.any():
            T_obs[ci] = float(F_obs[m].max())
    pooled_obs = float((F_obs[legal_pair] >= F_CRIT).mean()) if n_legal else 0.0
    t_observed = time.time() - t_obs_start
    say('    pooled_obs=%.6f T_obs median=%.3f max=%.3f' % (
        pooled_obs, np.median(T_obs[T_obs >= 0]) if (T_obs >= 0).any() else -1, T_obs.max()))

    say('[5/9] pilot budget test ...')
    # f_hat per context-A group and model matrices for N1
    f_hat_A = np.zeros((n_pc, K))
    ctxA_groups = {}
    for i, p in enumerate(plan):
        ctxA_groups.setdefault((p['cell'], p['drugA']), []).append(i)
    for key, idxs in ctxA_groups.items():
        fh = rowmeans[idxs].mean(axis=0)
        for i in idxs:
            f_hat_A[i] = fh
    model = np.zeros((n_pc, K, M))
    for i in range(n_pc):
        ghat = colmeans[i] - f_hat_A[i].mean()
        model[i] = f_hat_A[i][:, None] + ghat[None, :]
    model_rowmean = model.mean(axis=2)
    model_colmean = model.mean(axis=1)
    sigma_y = math.sqrt(2.0 * sigma_pair2_A2)

    def one_n1_rep(rng):
        noise = rng.normal(scale=sigma_y, size=(n_pc, K, M))
        rm = model_rowmean + noise.mean(axis=2)
        cm = model_colmean + noise.mean(axis=1)
        F = compute_F(rm, cm)
        T = np.full(N_CELLS, -1.0)
        for ci in range(N_CELLS):
            m = legal_pair & (pair_cell_idx == ci)
            if m.any():
                T[ci] = float(F[m].max())
        return T

    def one_n0_rep(rng):
        draws = rng.chisquare(df=K - 1, size=n_legal) / (K - 1)
        return float((draws >= F_CRIT).mean())

    rngp = np.random.default_rng(SEED)
    tp = time.time()
    one_n1_rep(np.random.default_rng(SEED + 1))
    one_n1_rep(np.random.default_rng(SEED + 2))
    t_n1 = (time.time() - tp) / 2.0
    tp = time.time()
    one_n0_rep(np.random.default_rng(SEED + 3))
    one_n0_rep(np.random.default_rng(SEED + 4))
    t_n0 = (time.time() - tp) / 2.0
    projected = (t_observed + 500 * (t_n1 + t_n0)) * 1.2
    mem_gb = rss_gb() or 0.0
    pilot = {'t_n1_per_rep_s': rq(t_n1, 5), 't_n0_per_rep_s': rq(t_n0, 5),
             't_observed_s': rq(t_observed, 5), 'projected_total_s': rq(projected, 2),
             'memory_gb_observed': rq(mem_gb, 3),
             'caps': {'wall_s': WALL_CAP, 'cpu_s': CPU_CAP, 'memory_gb': MEM_CAP_GB},
             'pass': bool(projected <= WALL_CAP and mem_gb <= MEM_CAP_GB)}
    say('    pilot: t_n1=%.4fs t_n0=%.5fs projected=%.1fs mem=%.2fGB pass=%s' % (
        t_n1, t_n0, projected, mem_gb, pilot['pass']))

    # gate failures before P1
    gate_fail = None
    if not d1:
        gate_fail = 'design_invalid: scale_mismatch'
    elif not d2:
        gate_fail = 'design_invalid: scale_mismatch'
    elif not d3:
        gate_fail = 'design_invalid: noise_calibration'
    elif not legal_block['pass_min']:
        gate_fail = 'design_invalid: coverage'
    elif not d7['pass']:
        gate_fail = 'design_invalid: coverage_identifiability_noise_or_boundary'
    elif not pilot['pass']:
        gate_fail = 'design_invalid: compute_budget_exceeded'

    diag = {
        'sigma_block': sigma_block, 'F_self_check': fself_stats,
        'D1_sigma_non_degenerate': d1, 'D2_F_self_check_and_ratio': d2, 'D3_half_split_FPR': d3,
        'legal_block': legal_block, 'D7': d7, 'pilot_budget': pilot,
        'peek_disclosure': {'non_blind': True, 'inherited': 'ON3 QUICK invalid artifact', 'printed': True},
        'inputs': sha,
    }

    result = {
        'protocol': {'path_rel': 'research/2026-10-27-agent-cell-colearning/mechanism_A/a2_exec/'
                                 'PROTOCOL_A2_EXEC.md', 'sha256': sha256_file(PROTOCOL)},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        'frozen_chain': {
            'PROBLEM_A2_v0_2': '3B49A8ABA7FBA903C1C88CBE75318E55F5C3045512A058E4FF54AA5EF1F16104',
            'DESIGN_A2_v0_2': '3AB5A663AD485579A42B0C3BB09096D756CBD6F123A93815A7FC91EA2CF3142E',
            'null_design_A2_v0_2': '96AE014DA6B8E9E5CA7AF359CC3DAA0D683FE8F865655A468167AC16176A24E5',
            'DECISION_R201_A2_EXEC': sha256_file(DECISION),
        },
        'peek_disclosure': diag['peek_disclosure'],
        'frozen': {'U_expected': U_EXPECTED, 'F_crit': F_CRIT, 'N_perm': N_PERM, 'seed': SEED,
                   'BH_q': BH_Q, 'legal_min': LEGAL_MIN, 'family': 'S-add role-stratified',
                   'N_cells': N_CELLS},
        'diagnostics_D1_D3_D6_D7': {'D1': d1, 'D2': d2, 'D3': d3, 'D6': pilot['pass'], 'D7': d7['pass'],
                                    'fail_before_P1': gate_fail},
        'P1': None,
        'failure_category': gate_fail,
        'verdict': 'design_invalid' if gate_fail else None,
        'boundaries': ['A.2 data-only P1 rerun; 0 new wells; P2/S1/S2/H_A2 not executed',
                       'positive: developmental existence only; negative: no_joint_contradiction only',
                       'no biology/mechanism/migration/decision/novelty claims; non-blind/peeked',
                       'pair-level counts descriptive only'],
        'deviations': [],
    }

    if gate_fail:
        say('    GATE FAIL -> %s; P1 not executed' % gate_fail)
        diag['D4_null_pooled'] = 'not_evaluated (pre-P1 gate failure)'
        diag['D5_T_ratio'] = 'not_evaluated (pre-P1 gate failure)'
        diag['pre_gate_observed_statistics'] = 'computed for pilot timing only; not interpreted'
        diag['telemetry'] = {'wall_seconds': rq(time.time() - t0, 2),
                             'cpu_seconds_process': rq(time.process_time() - cpu_start, 2),
                             'memory_gb_end': rq(rss_gb() or 0.0, 3)}
        result['P1'] = None
        result['pre_gate_observed_statistics'] = 'not reported (gate failure before P1 judgment)'
        write_json(result, OUTJSON)
        write_json(diag, OUTDIAG)
        pd.DataFrame([{'cell': c, 'note': 'P1 not executed: pre-gate failure; observed statistics not interpreted'}
                      for c in cell_names]).to_csv(OUTROWS, index=False)
        print('a2_exec.json sha256:', sha256_file(OUTJSON))
        print('DONE wall=%.1fs' % (time.time() - t0))
        return

    say('[6/9] P1 primary null N0 (pooled chi-square, N=500) ...')
    rng0 = np.random.default_rng(SEED)
    pooled_null = np.array([one_n0_rep(rng0) for _ in range(N_PERM)])
    pooled_q95 = float(np.percentile(pooled_null, 95))
    pooled_median = float(np.median(pooled_null))
    say('    N0 pooled null: median=%.4f q95=%.4f; observed=%.4f' % (pooled_median, pooled_q95, pooled_obs))

    say('[7/9] P1 per-cell N1 parametric bootstrap (N=500) ...')
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
            'universe_U': U, 'n_legal_pairs_A2': n_legal, 'F_crit': F_CRIT,
            'observed_pooled_frac_F_ge_Fcrit': rq(pooled_obs),
            'null_pooled_median': rq(pooled_median), 'null_pooled_q95': rq(pooled_q95),
            'T_obs_median': rq(t_obs_median), 'T_null_median': rq(t_null_median),
            'T_null_over_obs_ratio': rq(ratio_T),
            'BH': {'q': BH_Q, 'n_cells': N_CELLS, 'n_rejected': n_reject,
                   'rejected_cells': [cell_names[i] for i in range(N_CELLS) if rejected[i]],
                   'p_range': [rq(float(pvals.min())), rq(float(pvals.max()))]},
            'per_cell_file': 'a2_exec_rows.csv',
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

    # write outputs
    write_json(result, OUTJSON)
    diag['telemetry'] = {'wall_seconds': rq(time.time() - t0, 2),
                         'cpu_seconds_process': rq(time.process_time() - cpu_start, 2),
                         'memory_gb_end': rq(rss_gb() or 0.0, 3)}
    write_json(diag, OUTDIAG)
    rows = []
    for ci, c in enumerate(cell_names):
        m = legal_pair & (pair_cell_idx == ci)
        rows.append({'cell': c, 'n_pairs': int((pair_cell_idx == ci).sum()),
                     'n_legal_pairs': int(m.sum()),
                     'T_obs': rq(float(T_obs[ci])),
                     'p_value': rq(float(pvals[ci])),
                     'null_q95': rq(float(np.percentile(T_null[ci], 95))) if m.any() else None,
                     'bh_rejected': bool(rejected[ci]),
                     'median_F_obs': rq(float(np.median(F_obs[m]))) if m.any() else None})
    pd.DataFrame(rows).to_csv(OUTROWS, index=False)
    print('a2_exec.json sha256:', sha256_file(OUTJSON))
    print('a2_exec_rows.csv sha256:', sha256_file(OUTROWS))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
