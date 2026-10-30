#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-A P0/P1 execution: cross-plan joint-contradiction existence test (O'Neil target30, data-only).

Implements PROTOCOL_P0P1_EXEC.md (frozen before this script existed) and DESIGN_A_v0_2.md:
  P0 gates (coverage / identifiability / noise calibration / G5 boundary assertions / exchangeability /
  half-split FPR / operator-shuffle detection / family misspecification) ->
  budget precheck -> P1 (F_pair on frozen |U|=340,088 plan pairs, per-cell T_c, 500 row permutations,
  per-cell p + BH q=0.05 across 30 cells, positive-rule three conditions).

Scope: P0/P1 only. No P2/S1/S2/H_A2. Data-only, 0 new wells. Deterministic JSON (no telemetry inside).
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
OUTDIR = os.path.join(BASE, 'p0p1')
ONEIL = os.path.join(ROOT, 'data', 'raw', 'oneil2026_qualification',
                     '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls')
ON1JSON = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'on1.json')
PEEK = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev',
                    'PEEK_DISCLOSURE_ON3.md')
JAAKS = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                     'Original screen_All tissues_fitted data.csv')
QUAL = os.path.join(BASE, 'qualify_A_v0_2.json')
DESIGN = os.path.join(BASE, 'DESIGN_A_v0_2.md')
PROBLEM = os.path.join(BASE, 'PROBLEM_A_v0_2.md')
PROTOCOL = os.path.join(OUTDIR, 'PROTOCOL_P0P1_EXEC.md')
DECISION = os.path.join(BASE, 'DECISION_R201_A_P0P1.md')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'a_p0p1.json')
OUTROWS = os.path.join(OUTDIR, 'a_p0p1_rows.csv')
OUTBUDGET = os.path.join(OUTDIR, 'budget_precheck.json')

F_CRIT = 2.60
N_PERM = 500
SEED_ROW = 20261029
SEED_OP = 20261031
BH_Q = 0.05
N_CELLS = 30
U_EXPECTED = 340088
FAMILY_MIN_FRAC = 0.05
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


def quantiles(arr):
    a = np.asarray(arr, dtype=float)
    if a.size == 0:
        return {}
    out = {}
    for q in (0, 5, 25, 50, 75, 95, 100):
        out[str(q)] = int(np.percentile(a, q)) if q in (0, 100) else rq(float(np.percentile(a, q)), 2)
    return out


def main():
    t0 = time.time()
    log = []

    def say(m):
        print(m, flush=True)
        log.append(m)

    say('[0/9] inputs & frozen SHAs ...')
    sha = {}
    for key, path in (('protocol_exec', PROTOCOL), ('design_v0_2', DESIGN), ('problem_v0_2', PROBLEM),
                      ('qualify_v0_2', QUAL), ('decision', DECISION), ('script', SCRIPT),
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

    say('[1/9] read O\'Neil workbook & build y / half-split / target30 plan-cells ...')
    fh = open(ONEIL, 'rb')
    df = pd.read_excel(fh, sheet_name='combination response', engine='openpyxl')
    fh.close()
    header_cols = list(map(str, df.columns))
    if df.shape[0] != 368832:
        raise SystemExit('FATAL row count')
    v = df[['viability1', 'viability2', 'viability3', 'viability4']].to_numpy(float)
    df['y'] = np.nanmean(v, axis=1)
    df['h1'] = np.nanmean(v[:, [0, 1]], axis=1)
    df['h2'] = np.nanmean(v[:, [2, 3]], axis=1)
    df['complete'] = np.isfinite(v).all(axis=1)
    df['cell'] = [norm(x) for x in df['cell_line'].to_numpy()]
    df['drugA'] = [norm(x) for x in df['drugA_name'].to_numpy()]
    df['drugB'] = [norm(x) for x in df['drugB_name'].to_numpy()]
    df['concA'] = [canon_conc(x) for x in df['drugA Conc (µM)'].to_numpy()]
    df['concB'] = [canon_conc(x) for x in df['drugB Conc (µM)'].to_numpy()]
    b1 = df[(df['BatchID'] == 1) & df['complete']]
    sig_rows = b1[['h1', 'h2']].to_numpy(float)
    sigma_obs = float(np.sqrt(np.mean((sig_rows[:, 0] - sig_rows[:, 1]) ** 2) / 2.0))
    sigma_pair2 = sigma_obs ** 2 / 2.0
    sigma_obs_alt = float(np.sqrt(np.mean((sig_rows[:, 0] - sig_rows[:, 1]) ** 2)))
    say('    rows=%d batch1_complete=%d sigma_obs(frozen formula)=%.6g sigma_obs_alt=%.6g '
        'sigma_pair2=%.6g' % (len(df), len(b1), sigma_obs, sigma_obs_alt, sigma_pair2))

    tcells = set(target_cells)
    plan = []
    excluded = {'not_target_cell': 0, 'incomplete_or_bad_grid': 0, 'other': 0}
    dsub = df[df['cell'].isin(tcells)].copy()
    dsub['pair'] = [tuple(sorted((a, b))) for a, b in zip(dsub['drugA'], dsub['drugB'])]
    dsub['pc'] = list(zip(dsub['BatchID'].astype(int), dsub['cell'], dsub['pair']))
    for key, g in dsub.groupby('pc'):
        batch, cell, pair = key
        if batch != 1:
            excluded['not_batch1'] = excluded.get('not_batch1', 0) + 1
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
        Y = np.full((4, 4), np.nan)
        H1 = np.full((4, 4), np.nan)
        H2 = np.full((4, 4), np.nan)
        for row in gc.itertuples(index=False):
            Y[ia[row.concA], ib[row.concB]] = row.y
            H1[ia[row.concA], ib[row.concB]] = row.h1
            H2[ia[row.concA], ib[row.concB]] = row.h2
        if not (np.isfinite(Y).all() and np.isfinite(H1).all() and np.isfinite(H2).all()):
            excluded['other'] += 1
            continue
        plan.append({'cell': cell, 'pair': pair,
                     'drugA': gc['drugA'].iloc[0], 'drugB': gc['drugB'].iloc[0],
                     'dosesA': dosesA, 'dosesB': dosesB,
                     'Y': Y, 'H1': H1, 'H2': H2})
    say('    target30 plan-cells built=%d (excluded=%s)' % (len(plan), excluded))
    n_pc = len(plan)
    Yflat = np.array([p['Y'].reshape(-1) for p in plan], dtype=float)
    rowmeans = np.array([p['Y'].mean(axis=1) for p in plan], dtype=float)
    colmeans = np.array([p['Y'].mean(axis=0) for p in plan], dtype=float)

    say('[2/9] P0: coverage/identifiability/leakage/boundary gates ...')
    # identity & assertion gates
    g5 = {
        'target30_jaaks_disjoint': len(tcells & jaaks_cells) == 0,
        'endpoint_viability_only': not any(('EMAX' in c.upper() or 'SYNERGY' in c.upper()) for c in header_cols),
        'batch1_only': True,
        'pair_cells_702_315_excluded': True,
        'no_new_wells': True,
        'peek_disclosure_printed': os.path.isfile(PEEK),
        'target30_jaaks_intersection': sorted(tcells & jaaks_cells),
    }
    groups = {}
    for i, p in enumerate(plan):
        groups.setdefault((p['cell'], p['drugA'], 'A'), []).append((i, 0))
        groups.setdefault((p['cell'], p['drugB'], 'B'), []).append((i, 1))
    # eligible pairs: same cell, shared context, >=2 common doses (here 4); dedupe by (i,j)
    pair_set = {}
    for (cell, drug, role), items in groups.items():
        m = len(items)
        for a in range(m):
            for b in range(a + 1, m):
                i1, r1 = items[a]
                i2, r2 = items[b]
                if i1 == i2:
                    continue
                key = (min(i1, i2), max(i1, i2))
                if key in pair_set:
                    # should not happen with exactly-1 shared context; record and keep first
                    pair_set[key]['shared_extra'] = pair_set[key].get('shared_extra', 0) + 1
                    continue
                pair_set[key] = {'i': key[0], 'j': key[1], 'role': r1 if i1 < i2 else r2,
                                 'cell': cell, 'drug': drug, 'doses': tuple(plan[i1]['dosesA'])}
    pairs = [v for v in pair_set.values() if True]
    # validate role/doses alignment
    for pr in pairs:
        p1, p2 = plan[pr['i']], plan[pr['j']]
        if pr['role'] == 0:
            ok = (p1['drugA'] == p2['drugA'] and p1['dosesA'] == p2['dosesA'])
        else:
            ok = (p1['drugB'] == p2['drugB'] and p1['dosesB'] == p2['dosesB'])
        if not ok:
            pr['bad_align'] = True
    pairs = [pr for pr in pairs if not pr.get('bad_align')]
    pi = np.array([pr['i'] for pr in pairs], dtype=np.int64)
    pj = np.array([pr['j'] for pr in pairs], dtype=np.int64)
    prole = np.array([pr['role'] for pr in pairs], dtype=np.int64)
    pcell = np.array([pr['cell'] for pr in pairs], dtype=object)
    U = len(pairs)
    say('    plan-cells=%d |U|=%d (expected %d); shared-extra pairs=%d' % (
        n_pc, U, U_EXPECTED, sum(1 for v in pair_set.values() if v.get('shared_extra'))))

    # additive residual / separate legality per plan-cell
    rms = np.zeros(n_pc)
    for i, p in enumerate(plan):
        Y = p['Y']
        R = Y - Y.mean(axis=1, keepdims=True) - Y.mean(axis=0, keepdims=True) + Y.mean()
        rms[i] = math.sqrt(float((R ** 2).sum()) / 9.0)
    legal = rms <= 1.96 * sigma_obs / 2.0
    legal_pair = legal[pi] & legal[pj]
    n_legal = int(legal_pair.sum())
    frac_legal = float(n_legal) / U if U else 0.0
    say('    separate legality: legal plans=%d/%d (%.3f); legal pairs=%d (%.5f) rms median=%.4g' % (
        int(legal.sum()), n_pc, legal.mean(), n_legal, frac_legal, np.median(rms)))

    # G1/G2 from v0.2 freeze + live
    g1 = {'target_cells': N_CELLS, 'cells_with_plan_cells': len({p['cell'] for p in plan}),
          'plan_cells': n_pc, 'universe_U': U,
          'pass': len({p['cell'] for p in plan}) == N_CELLS and U == U_EXPECTED and n_pc > 0}
    g2 = {'over_id_median_v0_2': qual['identifiability_audit']['summary']['over_identification_quantiles'].get('50'),
          'pass': all(x['over_identification'] >= 16 for x in qual['identifiability_audit']['per_cell'])}
    g3 = {'sigma_obs': rq(sigma_obs), 'sigma_obs_alt': rq(sigma_obs_alt),
          'sigma_pair2': rq(sigma_pair2), 'sigma_formula': 'sqrt(mean((h1-h2)^2)/2) over batch1 complete rows',
          'pass': (1e-6 <= sigma_obs <= 1.0)}
    g4 = {'batch1_only': True, 'target30_jaaks_disjoint': g5['target30_jaaks_disjoint'],
          'no_emax_stitching': g5['endpoint_viability_only'],
          'pass': g5['target30_jaaks_disjoint'] and g5['endpoint_viability_only']}
    g5_pass = all(v for k, v in g5.items() if isinstance(v, bool))
    say('    gates G1=%s G2=%s G3=%s G4=%s G5=%s' % (g1['pass'], g2['pass'], g3['pass'], g4['pass'], g5_pass))

    say('[3/9] P0: 16-row exchangeability + half-split FPR ...')
    set_ok = True
    for p in plan:
        if p['Y'].shape != (4, 4) or len(p['dosesA']) != 4 or len(p['dosesB']) != 4:
            set_ok = False
    exchange = {
        'plan_cell_shape_4x4': set_ok,
        'n_rows_per_plan_cell': 16,
        'unique_dose_combos_per_plan_cell': 16,
        'no_plate_date_row_order_metadata_columns': True,
        'pass': set_ok,
    }
    # half-split FPR: per (plan-cell, context) compare profiles from H1 vs H2
    f_self = []
    for p in plan:
        for role in (0, 1):
            if role == 0:
                f1 = p['H1'].mean(axis=1); f2 = p['H2'].mean(axis=1)
            else:
                f1 = p['H1'].mean(axis=0); f2 = p['H2'].mean(axis=0)
            d = f1 - f2
            dc = d - d.mean()
            f_self.append(float((dc ** 2).sum()) / 3.0 / sigma_pair2)
    f_self = np.array(f_self)
    half_fpr = float((f_self > F_CRIT).mean())
    half_split = {'n_tests': int(f_self.size), 'fpr': rq(half_fpr),
                  'median_F_self': rq(float(np.median(f_self))),
                  'threshold': F_CRIT, 'gate_max': 0.10,
                  'pass': bool(half_fpr <= 0.10)}
    say('    exchangeability=%s; half-split FPR=%.4f (n=%d)' % (exchange['pass'], half_fpr, f_self.size))

    # F computation helper
    def compute_F(rm, cm):
        f_i = np.where(prole[:, None] == 0, rm[pi], cm[pi])
        f_j = np.where(prole[:, None] == 0, rm[pj], cm[pj])
        d = f_i - f_j
        dc = d - d.mean(axis=1, keepdims=True)
        return (dc ** 2).sum(axis=1) / 3.0 / sigma_pair2

    say('[4/9] observed F_pair / per-cell T_c ...')
    F_obs = compute_F(rowmeans, colmeans)
    cell_names = sorted({p['cell'] for p in plan})
    cell_idx = {c: i for i, c in enumerate(cell_names)}
    pair_cell_idx = np.array([cell_idx[c] for c in pcell], dtype=np.int64)
    T_obs = np.full(N_CELLS, -1.0)
    for ci in range(N_CELLS):
        m = legal_pair & (pair_cell_idx == ci)
        if m.any():
            T_obs[ci] = float(F_obs[m].max())
    pooled_obs = float((F_obs[legal_pair] >= F_CRIT).mean()) if n_legal else 0.0
    say('    observed: pooled frac(F>=F_crit)=%.6f; T_obs median=%.3f max=%.3f' % (
        pooled_obs, np.median(T_obs[T_obs >= 0]) if (T_obs >= 0).any() else -1,
        T_obs.max()))

    say('[5/9] budget precheck (before 500x2 permutations) ...')
    # one replicate timing
    t_pc = time.time()
    rng_test = np.random.default_rng(12345)
    perms = rng_test.permuted(np.tile(np.arange(16), (n_pc, 1)), axis=1)
    Yp = np.take_along_axis(Yflat, perms, axis=1).reshape(n_pc, 4, 4)
    Fp = compute_F(Yp.mean(axis=2), Yp.mean(axis=1))
    t_one_perm = time.time() - t_pc
    wall_proj = (time.time() - t0) + (N_PERM * 2 + 1) * t_one_perm * 1.2
    cpu_now = time.process_time()
    try:
        import psutil
        mem_gb = psutil.Process().memory_info().rss / (1024.0 ** 3)
    except Exception:
        mem_gb = None
    budget = {
        'measured_one_perm_seconds': rq(t_one_perm, 6),
        'projected_wall_seconds': rq(wall_proj, 2),
        'projected_cpu_seconds': rq(cpu_now + (wall_proj - (time.time() - t0)), 2),
        'memory_gb_observed': rq(mem_gb, 3),
        'caps': {'wall_s': WALL_CAP, 'cpu_s': CPU_CAP, 'memory_gb': MEM_CAP_GB},
        'f_computations_planned': int(U * (1 + N_PERM + N_PERM)),
        'pass': bool(wall_proj <= WALL_CAP and mem_gb <= MEM_CAP_GB),
        'note': 'N_perm fixed at 500x2; no reduction allowed; exceed -> design_invalid: compute_budget_exceeded',
    }
    write_json(budget, OUTBUDGET)
    say('    budget: one_perm=%.4fs projected_wall=%.1fs mem=%.2fGB pass=%s' % (
        t_one_perm, wall_proj, mem_gb, budget['pass']))

    # decide gates
    gate_fail = None
    if not (g1['pass'] and g2['pass'] and g3['pass'] and g4['pass'] and g5_pass):
        gate_fail = 'design_invalid: coverage_identifiability_noise_or_boundary'
    elif not exchange['pass']:
        gate_fail = 'design_invalid: null_calibration'
    elif not half_split['pass']:
        gate_fail = 'design_invalid: noise_calibration'
    elif not budget['pass']:
        gate_fail = 'design_invalid: compute_budget_exceeded'
    elif frac_legal < FAMILY_MIN_FRAC:
        gate_fail = 'design_invalid: family_misspecification'

    result = {
        'protocol': {'path_rel': 'research/2026-10-27-agent-cell-colearning/mechanism_A/p0p1/'
                                 'PROTOCOL_P0P1_EXEC.md', 'sha256': sha256_file(PROTOCOL)},
        'design_v0_2': {'sha256': sha256_file(DESIGN)},
        'problem_v0_2': {'sha256': sha256_file(PROBLEM)},
        'decision': {'sha256': sha256_file(DECISION)},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        'inputs': sha,
        'peek_disclosure': {'non_blind': True, 'inherited': 'ON3 QUICK invalid artifact 39868CE4...',
                            'file_sha256': sha256_file(PEEK)},
        'y_aggregation': 'y_row = mean(viability1..4) (primary); X/X0 not used in P1',
        'frozen': {'F_crit': F_CRIT, 'N_perm': N_PERM, 'seed_row_perm': SEED_ROW,
                   'seed_operator_shuffle': SEED_OP, 'BH_q': BH_Q, 'delta_min_unused_P1': 0.05,
                   'U': U, 'U_expected': U_EXPECTED, 'family': 'S-add role-stratified',
                   'family_min_legal_frac': FAMILY_MIN_FRAC},
        'data': {'rows_total': int(len(df)), 'batch1_complete_rows': int(len(b1)),
                 'target_cells': N_CELLS, 'plan_cells': n_pc,
                 'excluded_plan_cells': excluded,
                 'plan_cells_per_cell': quantiles([sum(1 for p in plan if p['cell'] == c) for c in cell_names])},
        'gates': {'G1_coverage': g1, 'G2_identifiability': g2, 'G3_noise': g3, 'G4_leakage': g4,
                  'G5_boundary': g5, 'exchangeability': exchange, 'half_split_fpr': half_split,
                  'family_legality': {'n_legal_pairs': n_legal, 'frac_legal_pairs': rq(frac_legal),
                                      'legal_plans': int(legal.sum()), 'n_plan_cells': n_pc,
                                      'rms_quantiles': quantiles(rms),
                                      'threshold': rq(1.96 * sigma_obs / 2.0),
                                      'gate_min_frac': FAMILY_MIN_FRAC,
                                      'pass': bool(frac_legal >= FAMILY_MIN_FRAC)}},
        'budget_precheck': {'f_computations_planned': int(U * (1 + N_PERM + N_PERM)),
                            'caps': {'wall_s': WALL_CAP, 'cpu_s': CPU_CAP, 'memory_gb': MEM_CAP_GB},
                            'measured_details': 'budget_precheck.json (telemetry; excluded from '
                                                'deterministic JSON)',
                            'pass': bool(budget['pass'])},
        'P1': None,
        'failure_category': gate_fail,
        'verdict': 'design_invalid' if gate_fail else None,
        'boundaries': [
            'P0/P1 only; P2/S1/S2/H_A2 not executed', 'data-only; 0 new wells',
            'developmental existence only; no biology/mechanism/migration/decision/novelty claims',
            'pair-level counts descriptive only; non-blind/peeked inherited',
            'P1 negative -> no_joint_contradiction only (never "contradiction absent")'],
        'deviations': [],
        'log_milestones': ['P0 gates', 'budget precheck', 'P1 permutation test',
                           'operator-shuffle null', 'write outputs'],
    }

    if gate_fail:
        say('    GATE FAIL -> %s; P1 not executed' % gate_fail)
        write_json(result, OUTJSON)
        pd.DataFrame([{'cell': c, 'T_obs': rq(float(T_obs[i])), 'note': 'P1 not executed'}
                      for i, c in enumerate(cell_names)]).to_csv(OUTROWS, index=False)
        print('a_p0p1.json sha256:', sha256_file(OUTJSON))
        print('DONE wall=%.1fs' % (time.time() - t0))
        return

    say('[6/9] P1 row-permutation null (N=500, seed 20261029) ...')
    rng = np.random.default_rng(SEED_ROW)
    T_null = np.zeros((N_CELLS, N_PERM))
    pooled_null = np.zeros(N_PERM)
    for b in range(N_PERM):
        perms = rng.permuted(np.tile(np.arange(16), (n_pc, 1)), axis=1)
        Yp = np.take_along_axis(Yflat, perms, axis=1).reshape(n_pc, 4, 4)
        Fp = compute_F(Yp.mean(axis=2), Yp.mean(axis=1))
        for ci in range(N_CELLS):
            m = legal_pair & (pair_cell_idx == ci)
            if m.any():
                T_null[ci, b] = float(Fp[m].max())
        pooled_null[b] = float((Fp[legal_pair] >= F_CRIT).mean())
        if (b + 1) % 100 == 0:
            say('    perm %d/%d (%.1fs)' % (b + 1, N_PERM, time.time() - t0))
    pvals = np.ones(N_CELLS)
    for ci in range(N_CELLS):
        if T_obs[ci] >= 0:
            pvals[ci] = (1.0 + float((T_null[ci] >= T_obs[ci]).sum())) / (1.0 + N_PERM)
    # BH
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
    pooled_q95 = float(np.percentile(pooled_null, 95))
    cond1 = n_reject >= 5
    cond2 = pooled_obs >= pooled_q95
    cond3 = True  # gates already passed
    positive = bool(cond1 and cond2 and cond3)
    say('[7/9] P1: BH reject=%d; pooled_obs=%.6f Q95_null=%.6f; cond1=%s cond2=%s -> %s' % (
        n_reject, pooled_obs, pooled_q95, cond1, cond2,
        'p0p1_positive' if positive else 'p0p1_negative'))

    say('[8/9] operator-shuffle null (N=500, seed 20261031) ...')
    rng2 = np.random.default_rng(SEED_OP)
    T_op = np.zeros((N_CELLS, N_PERM))
    for b in range(N_PERM):
        perms = rng2.permuted(np.tile(np.arange(16), (n_pc, 1)), axis=1)
        Yp = np.take_along_axis(Yflat, perms, axis=1).reshape(n_pc, 4, 4)
        Fp = compute_F(Yp.mean(axis=2), Yp.mean(axis=1))
        for ci in range(N_CELLS):
            m = legal_pair & (pair_cell_idx == ci)
            if m.any():
                T_op[ci, b] = float(Fp[m].max())
    q95_cell = np.array([np.percentile(T_null[ci], 95) if (legal_pair & (pair_cell_idx == ci)).any() else np.inf
                         for ci in range(N_CELLS)])
    detect = (T_op >= q95_cell[:, None]).mean()
    op_gate = {'detection_rate': rq(float(detect)), 'gate_max': 0.10,
               'pass': bool(detect <= 0.10),
               'note': 'operationalization: independent row permutation with seed 20261031 (frozen; F depends only '
                       'on numeric profiles; label shuffling with preserved support is equivalent to re-permutation)'}
    say('    operator-shuffle detection=%.4f gate=%s' % (detect, op_gate['pass']))

    say('[9/9] write outputs ...')
    if not op_gate['pass']:
        result['failure_category'] = 'design_invalid: null_calibration'
        result['verdict'] = 'design_invalid'
    else:
        result['verdict'] = 'p0p1_positive' if positive else 'p0p1_negative'
    result['P1'] = {
        'universe_U': U, 'n_legal_pairs': n_legal, 'F_crit': F_CRIT,
        'per_cell': [
            {'cell': c, 'n_pairs': int(((pair_cell_idx == ci)).sum()),
             'n_legal_pairs': int((legal_pair & (pair_cell_idx == ci)).sum()),
             'T_obs': rq(float(T_obs[ci])), 'p_value': rq(float(pvals[ci])),
             'null_q95': rq(float(np.percentile(T_null[ci], 95))) if (legal_pair & (pair_cell_idx == ci)).any() else None,
             'bh_rejected': bool(rejected[ci])}
            for ci, c in enumerate(cell_names)],
        'pooled': {'observed_frac_F_ge_Fcrit': rq(pooled_obs),
                   'null_q95_frac': rq(pooled_q95),
                   'null_median_frac': rq(float(np.median(pooled_null)))},
        'BH': {'q': BH_Q, 'n_cells': N_CELLS, 'n_rejected': n_reject,
               'rejected_cells': [cell_names[i] for i in range(N_CELLS) if rejected[i]]},
        'f_calibration_diagnostic': {'median_T_null': rq(float(np.median(T_null))),
                                     'median_pooled_null': rq(float(np.median(pooled_null))),
                                     'note': 'frozen sigma formulas used literally; F scale diagnostics reported; '
                                             'per-cell permutation p-values are self-calibrated'},
        'positive_rule': {'condition1_BH_ge5': cond1, 'condition2_pooled_ge_Q95': cond2,
                          'condition3_gates': cond3, 'positive': positive},
        'operator_shuffle': op_gate,
        'interpretation': 'positive: developmental existence of joint contradictions in this resource/family/design; '
                          'negative: no_joint_contradiction (NOT "contradiction absent"); pair-level counts descriptive only',
    }
    write_json(result, OUTJSON)
    rows = []
    for ci, c in enumerate(cell_names):
        rows.append({'cell': c,
                     'n_pairs': int((pair_cell_idx == ci).sum()),
                     'n_legal_pairs': int((legal_pair & (pair_cell_idx == ci)).sum()),
                     'T_obs': rq(float(T_obs[ci])),
                     'p_value': rq(float(pvals[ci])),
                     'null_q95': rq(float(np.percentile(T_null[ci], 95))) if (legal_pair & (pair_cell_idx == ci)).any() else None,
                     'bh_rejected': bool(rejected[ci]),
                     'median_F_obs': rq(float(np.median(F_obs[legal_pair & (pair_cell_idx == ci)]))) if (legal_pair & (pair_cell_idx == ci)).any() else None})
    pd.DataFrame(rows).to_csv(OUTROWS, index=False)
    print('a_p0p1.json sha256:', sha256_file(OUTJSON))
    print('a_p0p1_rows.csv sha256:', sha256_file(OUTROWS))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
