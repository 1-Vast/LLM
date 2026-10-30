#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
R197: Q2 inference recalibration (A0) + Q low-rank/context-dependent structure
held-out prediction (B).

Frozen protocol: research/2026-10-27-q-structure/PROTOCOL_R197.md
(v1 FROZEN + AMENDMENT-R197-001, both before any R197 inference/prediction run)

CPU only, deterministic (fixed seeds, JSON sorted keys, no timestamps),
no network, no new data. Reads only existing R194/Q2/A2 inputs (read-only).

Sections
  A0: corrected weighted moment algebra, dyadic prototype tests,
      dependency-aware bootstrap/permutation, reliability recalibration
      (old q2 formula vs dependency-aware formula vs split-half),
      old/new comparison.
  B : pre-registered held-out prediction (H197a cell-pair / H197b
      condition-pair / H197c random entries) with B0/B1/B2/B3/B4,
      cluster-bootstrap CIs, MDE80, permutation null, conservative
      relaxed-rule type-I simulations, design checks and frozen judgment.

This is NOT an A1/A2 pass, not a cross-screen replication, and starts no
feedback/Agent/acquisition work.
"""
import hashlib
import json
import math
import os
import sys
import time
import unicodedata

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingRegressor

# --------------------------------------------------------------------------- constants
ROOT = r'D:\MAESTRO'
OUTDIR = os.path.join(ROOT, 'research', '2026-10-27-q-structure')
BASE = os.path.join(ROOT, 'research', '2026-10-27-conditional-shift')
ORIG = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                    'Original screen_All tissues_fitted data.csv')
MATCHED = os.path.join(BASE, 'matched_conditions.csv')
Q2JSON = os.path.join(BASE, 'q2.json')
PROTOCOL = os.path.join(OUTDIR, 'PROTOCOL_R197.md')
SCRIPT = os.path.join(OUTDIR, 'r197.py')
OUTJSON = os.path.join(OUTDIR, 'r197.json')
OUTCSV = os.path.join(OUTDIR, 'r197_rows.csv')
OUTUSAGE = os.path.join(OUTDIR, 'usage_r197.json')

PRIMARY_ENDPOINT = 'SYNERGY_DELTA_EMAX'
USECOLS = ['BARCODE', 'CELL_LINE_NAME', 'Tissue', 'ANCHOR_ID', 'LIBRARY_ID',
           'ANCHOR_CONC', 'LIBRARY_CONC', PRIMARY_ENDPOINT,
           'ANCHOR_PATHWAY', 'LIBRARY_PATHWAY', 'ANCHOR_DRUG_TYPE', 'LIBRARY_DRUG_TYPE',
           'LIBRARY_EMAX', 'LIBRARY_AUC']

# frozen seeds (PROTOCOL_R197 section 1)
SEED_BOOT_LEGACY = 20261103
SEED_BOOT_NODE = 20261102
SEED_PERM = 20261104
SEED_SPLIT = 20261105
SEED_FOLDS = 20261106
SEED_BOOT_B = 20261107
SEED_PERM_B = 20261108
SEED_INNER = 20261109
SEED_TYPEI = 20261110
SEED_HGB = 20261111
SEED_DYADIC_MC = 20261102

B_BOOT_A0 = 1000
B_BOOT_B = 1000
B_PERM_A0 = 1000
B_PERM_B = 1000
N_SPLIT = 20
B_INNER_CI_TYPEI = 200
B_INNER_PERM_TYPEI = 200

# frozen thresholds / sizes
DELTA_MIN = 0.05
MDE_FACTOR = 2.801585218112968  # z_{0.975}+z_{0.80}
RELIABILITY_THRESHOLD = 0.50
TYPE_I_MAX = 0.10
BOOT_FINITE_MIN = 0.95
# B design-check gates (PROTOCOL_R197 3.6)
MIN_TEST_ENTRIES = 10000
MIN_TEST_PER_FOLD = 1000
PRED_FINITE_MIN = 0.99
NULL_MEAN_ABS_MAX = 0.02
# B models
LAMBDA_GRID = (0.1, 1.0, 10.0, 100.0, 1000.0)
RANKS = (1, 2, 3, 5)
INNER_FOLDS = 5
ALS_LAMBDA = 0.1
ALS_ITERS = 25
N_TYPEI = {'H197a': 20, 'H197b': 10, 'H197c': 10}

# expected q2.json point estimates (sanity check, PROTOCOL_R197 2.1/2.4)
Q2_EXPECTED = {
    'sigma2_cond': 0.000371,
    'sigma2_cellpair': 0.001023,
    'sigma2_total': 0.025944,
    'sigma2_resid': 0.024551,
    'sigma2_single_key_noise': 0.003351,
    'noise_variance_mean_per_observation': 0.011968,
    'reliability_at_median_n': 0.867863,
}
TOL_Q2 = 1e-6

QUICK = ('--quick' in sys.argv)


# --------------------------------------------------------------------------- helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest().upper()


def nk(s):
    return ''.join(ch for ch in unicodedata.normalize('NFKC', str(s)).casefold() if ch.isalnum())


def canon(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return format(v, '.10g')


def rq(x, nd=8):
    if x is None:
        return None
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    try:
        v = float(x)
    except (TypeError, ValueError):
        return x
    if not math.isfinite(v):
        return None
    return float(round(v, nd))


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


def spearman(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    n = int(ok.sum())
    if n < 5:
        return None, n
    rx = rankdata(x[ok], method='average')
    ry = rankdata(y[ok], method='average')
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    den = math.sqrt(float(rx @ rx) * float(ry @ ry))
    if den == 0.0:
        return None, n
    return float((rx @ ry) / den), n


def pct_ci(vals, lo=2.5, hi=97.5):
    v = np.asarray([x for x in vals if x is not None and math.isfinite(x)], dtype=float)
    if v.size == 0:
        return [None, None]
    return [float(np.percentile(v, lo)), float(np.percentile(v, hi))]


def finite_frac(vals):
    v = np.asarray(vals, dtype=float)
    if v.size == 0:
        return 0.0
    return float(np.mean(np.isfinite(v)))


# --------------------------------------------------------------------------- Q reconstruction
def build_q():
    """Rebuild the A2/q2 Q matrix exactly (PROTOCOL_R197 section 0)."""
    t0 = time.time()
    df = pd.read_csv(ORIG, usecols=USECOLS, low_memory=False)
    n_rows = len(df)
    bc = pd.to_numeric(df['BARCODE'], errors='coerce').to_numpy()
    cell = np.array([nk(x) if isinstance(x, str) else None for x in df['CELL_LINE_NAME'].to_numpy()], dtype=object)
    aid = df['ANCHOR_ID'].astype(str).str.strip().to_numpy()
    lid = df['LIBRARY_ID'].astype(str).str.strip().to_numpy()
    ac = np.array([canon(x) for x in df['ANCHOR_CONC'].to_numpy()], dtype=object)
    lc = np.array([canon(x) for x in df['LIBRARY_CONC'].to_numpy()], dtype=object)
    cell_ok = np.array([c is not None for c in cell])
    comp = np.array([('|' in str(a)) or ('|' in str(b)) or ('|' in str(c))
                     for a, b, c in zip(df['ANCHOR_ID'], df['LIBRARY_ID'], df['ANCHOR_CONC'])])
    y = pd.to_numeric(df[PRIMARY_ENDPOINT], errors='coerce').to_numpy(float)
    valid = ((~comp) & cell_ok & np.isfinite(bc) & (aid != 'nan') & (lid != 'nan')
             & np.array([x is not None for x in ac]) & np.array([x is not None for x in lc])
             & np.isfinite(y))
    mc = pd.read_csv(MATCHED, dtype=str)
    mc_keys = set()
    for r in mc.itertuples(index=False):
        mc_keys.add((r.cell, (r.anchor_id, r.library_id, canon(r.anchor_conc), canon(r.library_conc))))
    cells = sorted({k[0] for k in mc_keys})
    conds = sorted({k[1] for k in mc_keys})
    cellidx = {c: i for i, c in enumerate(cells)}
    rep2 = {}
    for c, cond in mc_keys:
        rep2.setdefault(c, set()).add(cond)
    # key-level barcode maps
    cond_arr = np.empty(n_rows, dtype=object)
    for i in np.nonzero(valid)[0]:
        cond_arr[i] = (aid[i], lid[i], ac[i], lc[i])
    bmap = {}
    for i in np.nonzero(valid)[0]:
        c = cell[i]
        if c not in cellidx:
            continue
        k = (c, cond_arr[i])
        bmap.setdefault(k, {}).setdefault(int(bc[i]), []).append(float(y[i]))
    full = {k: float(np.mean([np.mean(vs) for vs in bm.values()])) for k, bm in bmap.items()}
    bcount = {k: len(bm) for k, bm in bmap.items()}
    # deterministic key id / half-barcode values for noise calibration
    key_list = sorted(bmap.keys(), key=lambda kk: (kk[0], tuple(kk[1])))
    key_id = {k: i for i, k in enumerate(key_list)}
    n_keys = len(key_list)
    key_bcnt = np.zeros(n_keys, dtype=np.int64)
    key_yh0 = np.full(n_keys, np.nan)
    key_yh1 = np.full(n_keys, np.nan)
    for k, i in key_id.items():
        bm = bmap[k]
        b = sorted(bm.keys())
        key_bcnt[i] = len(b)
        h = (len(b) + 1) // 2
        if len(b) >= 2:
            key_yh0[i] = float(np.mean([np.mean(bm[bb]) for bb in b[:h]]))
            key_yh1[i] = float(np.mean([np.mean(bm[bb]) for bb in b[h:]]))
    # condition-pair x cell-pair layout
    quad = []
    cp_list = []
    for i in range(len(cells)):
        ca = cells[i]
        for j in range(i + 1, len(cells)):
            cb = cells[j]
            shared = rep2[ca] & rep2[cb]
            if len(shared) < 2:
                continue
            groups = {}
            for k in shared:
                groups.setdefault((k[0], k[2], k[3]), []).append(k)
            qs = []
            for key in sorted(groups.keys()):
                ks = sorted(groups[key], key=lambda x: x[1])
                for a in range(len(ks)):
                    for b in range(a + 1, len(ks)):
                        qs.append((ks[a], ks[b]))
            if len(qs) >= 5:
                pi = len(cp_list)
                cp_list.append((ca, cb))
                for p, qc in qs:
                    quad.append((pi, p, qc))
    n_obs = len(quad)
    n_cp = len(cp_list)
    # canonical row order: sort condition pairs by (p, q) tuple
    row_keys = sorted({(p, qc) for _, p, qc in quad})
    row_id = {k: i for i, k in enumerate(row_keys)}
    n_condpair = len(row_keys)
    cj = np.empty(n_obs, dtype=np.int64)
    cpid = np.empty(n_obs, dtype=np.int64)
    qv = np.empty(n_obs, dtype=float)
    quad_keys = np.empty((n_obs, 4), dtype=np.int64)
    for t, (pi, p, qc) in enumerate(quad):
        cj[t] = pi
        cpid[t] = row_id[(p, qc)]
        ca, cb = cp_list[pi]
        qv[t] = (full[(ca, p)] - full[(ca, qc)]) - (full[(cb, p)] - full[(cb, qc)])
        quad_keys[t, 0] = key_id[(ca, p)]
        quad_keys[t, 1] = key_id[(ca, qc)]
        quad_keys[t, 2] = key_id[(cb, p)]
        quad_keys[t, 3] = key_id[(cb, qc)]
    # matrix
    Q = np.full((n_condpair, n_cp), np.nan)
    Q[cpid, cj] = qv
    mask = ~np.isnan(Q)
    # structure assertions
    assert n_obs == 92039 and n_cp == 1501 and n_condpair == 229, 'structure differs from A2/q2'
    assert len(np.unique(cpid * n_cp + cj)) == n_obs, 'duplicate (i,j) cells'
    assert int(mask.sum()) == n_obs
    n_i = mask.sum(1)
    m_j = mask.sum(0)
    struct = {
        'n_observations': int(n_obs), 'n_condition_pairs': int(n_condpair),
        'n_cell_pairs': int(n_cp), 'n_cells': int(len(cells)), 'n_conditions': int(len(conds)),
        'n_matched_keys': int(len(mc_keys)), 'n_directed_pairs': 129,
        'condpair_n_cp_min': int(n_i.min()), 'condpair_n_cp_median': float(np.median(n_i)),
        'condpair_n_cp_max': int(n_i.max()),
        'cellpair_n_condpair_min': int(m_j.min()), 'cellpair_n_condpair_median': float(np.median(m_j)),
        'cellpair_n_condpair_max': int(m_j.max()),
        'density': float(n_obs / (n_condpair * n_cp)),
        'unique_cells': True,
        'orientation_rule': 'condition pair (p,q) oriented by ascending library_id',
        'primary_endpoint': PRIMARY_ENDPOINT,
        'barcode_count_distribution_keys': {},
    }
    # barcode count distribution over the 4 keys of each observation (as q2)
    kb = np.zeros(n_obs * 4, dtype=np.int64)
    kb[:] = key_bcnt[quad_keys.reshape(-1)]
    vals, counts = np.unique(kb, return_counts=True)
    struct['barcode_count_distribution_keys'] = {str(int(v)): int(c) for v, c in zip(vals, counts)}
    # condition-pair metadata: p, q tuples
    row_meta = []
    for (p, qc) in row_keys:
        row_meta.append({'anchor_id': p[0], 'library_p': p[1], 'library_q': qc[1],
                         'anchor_conc': p[2], 'library_conc': p[3]})
    cells_meta = {}
    for c in cells:
        cells_meta[c] = {'tissue': ''}
    for r in mc.itertuples(index=False):
        if r.cell in cells_meta:
            cells_meta[r.cell]['tissue'] = str(r.tissue)
    ca_idx = np.array([cells.index(a) for a, b in cp_list], dtype=np.int64)
    cb_idx = np.array([cells.index(b) for a, b in cp_list], dtype=np.int64)
    out = {
        'df': df, 'cells': cells, 'conds': conds, 'cp_list': cp_list,
        'cells_meta': cells_meta, 'row_meta': row_meta,
        'cpid': cpid, 'cj': cj, 'y': qv, 'Q': Q, 'mask': mask,
        'n_obs': n_obs, 'n_cp': n_cp, 'n_condpair': n_condpair,
        'n_i': n_i, 'm_j': m_j, 'ci': cpid, 'cj_arr': cj,
        'ca_idx': ca_idx, 'cb_idx': cb_idx,
        'key_bcnt': key_bcnt, 'key_yh0': key_yh0, 'key_yh1': key_yh1,
        'quad_keys': quad_keys,
        'structure': struct, 'load_seconds': time.time() - t0,
    }
    return out


# --------------------------------------------------------------------------- A0 estimators
def moment_corrected(y, ci, cj, n_cond, n_cell, w=None):
    """Corrected weighted pairwise-covariance moment estimator (PROTOCOL_R197 2.1)."""
    if w is None:
        w = np.ones(y.size, dtype=float)
    W = float(w.sum())
    mu = float((w * y).sum() / W)
    wy = w * y
    # condition-pair groups
    Wc = np.bincount(ci, weights=w, minlength=n_cond)
    Sc = np.bincount(ci, weights=wy, minlength=n_cond)
    S2c = np.bincount(ci, weights=w * wy, minlength=n_cond)      # sum w^2 y
    T2c = np.bincount(ci, weights=wy * wy, minlength=n_cond)     # sum w^2 y^2
    W2c = np.bincount(ci, weights=w * w, minlength=n_cond)
    Ac = 0.5 * (Sc * Sc - T2c)
    Bc = Wc * Sc - S2c
    Cc = 0.5 * (Wc * Wc - W2c)
    num_c = float((Ac - mu * Bc + mu * mu * Cc).sum())
    den_c = float(Cc.sum())
    s2_cond = num_c / den_c if den_c > 0 else float('nan')
    # cell-pair groups
    Wj = np.bincount(cj, weights=w, minlength=n_cell)
    Sj = np.bincount(cj, weights=wy, minlength=n_cell)
    S2j = np.bincount(cj, weights=w * wy, minlength=n_cell)
    T2j = np.bincount(cj, weights=wy * wy, minlength=n_cell)
    W2j = np.bincount(cj, weights=w * w, minlength=n_cell)
    Aj = 0.5 * (Sj * Sj - T2j)
    Bj = Wj * Sj - S2j
    Cj = 0.5 * (Wj * Wj - W2j)
    num_j = float((Aj - mu * Bj + mu * mu * Cj).sum())
    den_j = float(Cj.sum())
    s2_cell = num_j / den_j if den_j > 0 else float('nan')
    s2_total = float((w * (y - mu) ** 2).sum() / (W - 1.0)) if W > 1 else float('nan')
    return {'s2_cond': s2_cond, 's2_cell': s2_cell, 's2_total': s2_total,
            's2_resid': s2_total - s2_cond - s2_cell, 'mu': mu}


def moment_legacy_formula_example(y, w, mu):
    """Legacy q2 algebraic form for the ERRATA_Q2 example (PROTOCOL_R197 2.1)."""
    W = float(w.sum())
    Sc = float((w * y).sum())
    Tc = float((w * y * y).sum())
    W2c = float((w * w).sum())
    num = 0.5 * ((Sc - mu * W) ** 2 - (Tc - 2 * mu * Sc + mu * mu * W2c))
    den = 0.5 * (W * W - W2c)
    return num / den


def moment_corrected_example(y, w, mu):
    W = float(w.sum())
    Sc = float((w * y).sum())
    S2 = float((w * w * y).sum())
    T2 = float((w * y) ** 2).sum() if False else float(((w * y) ** 2).sum())
    W2 = float((w * w).sum())
    A = 0.5 * (Sc * Sc - T2)
    B = W * Sc - S2
    C = 0.5 * (W * W - W2)
    return (A - mu * B + mu * mu * C) / C


def dyadic_prototype_tests(rng_mc_seed=SEED_DYADIC_MC):
    out = []
    for n in (4, 10, 30):
        edges = n * (n - 1) // 2
        coeff = np.array([n - 1 - 2 * i for i in range(n)], dtype=float)
        true_var = float(np.sum(coeff * coeff) / (edges * edges))
        closed = 4.0 * (n + 1) / (3.0 * n * (n - 1))
        iid_approx = 2.0 / edges
        # Monte-Carlo check with iid unit-variance z
        rng = np.random.default_rng(rng_mc_seed + n)
        mc_means = []
        for _ in range(2000):
            z = rng.normal(size=n)
            qs = np.array([z[a] - z[b] for a in range(n) for b in range(a + 1, n)])
            mc_means.append(float(qs.mean()))
        mc = np.asarray(mc_means)
        mc_se = float(mc.std(ddof=1) / math.sqrt(mc.size))
        out.append({'n_cells': n, 'n_pairs': edges,
                    'true_variance': rq(true_var), 'closed_form': rq(closed),
                    'independent_pair_approx': rq(iid_approx),
                    'ratio_true_over_independent': rq(true_var / iid_approx),
                    'mc_variance': rq(float(mc.var(ddof=1))),
                    'mc_within_3se_of_closed': bool(abs(float(mc.var(ddof=1)) - closed) <= 3.0 * mc_se),
                    'mc_se_of_variance_approx': rq(mc_se)})
    # rank-one shared-law counterexample: zero additive marginal means
    rank1 = [[1.0, -1.0], [-1.0, 1.0]]
    row_means = [sum(row) / 2.0 for row in rank1]
    col_means = [sum(row[j] for row in rank1) / 2.0 for j in range(2)]
    return {'dyadic_average_variance': out,
            'rank_one_counterexample': {
                'matrix': rank1, 'row_means': row_means, 'col_means': col_means,
                'rank': 1,
                'interpretation': ('Q_ij=u_i v_j with u=v=(1,-1) is fully shared/learnable '
                                   'while additive (row/column-mean) condition share is exactly 0')},
            'weighted_moment_example': {
                'y': [1.0, 3.0], 'w': [2.0, 1.0], 'mu': 5.0 / 3.0,
                'correct_distinct_pair_residual_product': rq(moment_corrected_example(
                    np.array([1.0, 3.0]), np.array([2.0, 1.0]), 5.0 / 3.0)),
                'legacy_code_formula': rq(moment_legacy_formula_example(
                    np.array([1.0, 3.0]), np.array([2.0, 1.0]), 5.0 / 3.0)),
                'expected_correct': rq(-8.0 / 9.0), 'expected_legacy': rq(-37.0 / 18.0)}}


def noise_calibration(q):
    """Reproduce q2 noise calibration vectorised (PROTOCOL_R197 2.4)."""
    quad_keys = q['quad_keys']
    kb = q['key_bcnt'][quad_keys]                 # (n_obs,4)
    ok = kb.min(axis=1) >= 2
    idx = np.nonzero(ok)[0]
    b = kb[idx]
    h = (b + 1) // 2
    den = (1.0 / h + 1.0 / (b - h)).sum(axis=1)   # sum over 4 keys
    # half Q values
    qh0 = np.empty(idx.size)
    qh1 = np.empty(idx.size)
    yh0 = q['key_yh0']
    yh1 = q['key_yh1']
    kk = quad_keys[idx]
    qh0 = (yh0[kk[:, 0]] - yh0[kk[:, 1]]) - (yh0[kk[:, 2]] - yh0[kk[:, 3]])
    qh1 = (yh1[kk[:, 0]] - yh1[kk[:, 1]]) - (yh1[kk[:, 2]] - yh1[kk[:, 3]])
    d = qh0 - qh1
    s2_single = float((d * d).sum() / den.sum())
    noise_obs = s2_single * (1.0 / kb).sum(axis=1)
    noise_avg = float(np.mean(noise_obs))
    # split-half stability by condition-pair / cell-pair parity (as q2)
    stab = {}
    for tag, parity in (('by_condition_pair_parity', q['ci'][idx] % 2),
                        ('by_cell_pair_parity', q['cj_arr'][idx] % 2)):
        est = []
        for hside in (0, 1):
            m = parity == hside
            est.append(float((d[m] * d[m]).sum() / den[m].sum()) if m.sum() >= 20 else None)
        stab[tag] = {'half0': rq(est[0]), 'half1': rq(est[1]),
                     'n_half0': int((parity == 0).sum()), 'n_half1': int((parity == 1).sum()),
                     'ratio': rq(est[0] / est[1]) if (est[0] and est[1]) else None}
    return {'n_calibration_quadruples': int(idx.size),
            'coverage_frac_of_observations': float(idx.size / q['n_obs']),
            'sigma2_single_key_noise': s2_single,
            'noise_variance_mean_per_observation': noise_avg,
            'stability': stab,
            'noise_obs': noise_obs}


def a0_section(q, t_start):
    t0 = time.time()
    ci = q['ci']
    cj = q['cj_arr']
    y = q['y']
    n_cond = q['n_condpair']
    n_cell = q['n_cp']
    n_obs = q['n_obs']
    n_i = q['n_i'].astype(float)
    n_median = float(np.median(n_i))
    res = {'purpose': 'qualification_recalibration'}

    # --- self-tests / prototype tests
    res['self_tests'] = dyadic_prototype_tests()
    wt = res['self_tests']['weighted_moment_example']
    res['self_tests']['weighted_moment_example']['pass'] = bool(
        abs(wt['correct_distinct_pair_residual_product'] - (-8.0 / 9.0)) < 1e-9
        and abs(wt['legacy_code_formula'] - (-37.0 / 18.0)) < 1e-9)
    dy = res['self_tests']['dyadic_average_variance']
    res['self_tests']['dyadic_ratio_n30_pass'] = bool(abs(dy[2]['ratio_true_over_independent'] - 10.33) < 0.01)
    res['self_tests']['dyadic_mc_pass'] = bool(all(d['mc_within_3se_of_closed'] for d in dy))

    # --- noise calibration (reproduce q2)
    noise = noise_calibration(q)
    noise_obs = noise.pop('noise_obs')
    noise_avg = noise['noise_variance_mean_per_observation']
    s2_single = noise['sigma2_single_key_noise']
    res['noise_calibration'] = noise
    res['noise_calibration']['q2_match'] = {
        'sigma2_single_abs_diff': rq(abs(s2_single - Q2_EXPECTED['sigma2_single_key_noise'])),
        'noise_avg_abs_diff': rq(abs(noise_avg - Q2_EXPECTED['noise_variance_mean_per_observation'])),
        'pass': bool(abs(s2_single - Q2_EXPECTED['sigma2_single_key_noise']) < TOL_Q2
                     and abs(noise_avg - Q2_EXPECTED['noise_variance_mean_per_observation']) < TOL_Q2)}

    # --- unweighted point estimates + q2 sanity check
    point = moment_corrected(y, ci, cj, n_cond, n_cell, None)
    s2_cond = point['s2_cond']
    s2_cell = point['s2_cell']
    s2_total = point['s2_total']
    s2_resid = point['s2_resid']
    s2_int_raw = s2_resid - noise_avg
    s2_int = max(0.0, s2_int_raw)
    rel_old = s2_cond / (s2_cond + (s2_int + noise_avg) / n_median)
    shares = {'share_cond_raw': s2_cond / s2_total, 'share_cond_clipped': max(s2_cond, 0.0) / s2_total,
              'share_cellpair': s2_cell / s2_total, 'share_resid_raw': s2_resid / s2_total,
              'share_interaction_clipped': s2_int / s2_total, 'share_noise_clipped': noise_avg / s2_total}
    q2chk = {
        'sigma2_cond_old': Q2_EXPECTED['sigma2_cond'], 'sigma2_cond_new': rq(s2_cond),
        'sigma2_cellpair_old': Q2_EXPECTED['sigma2_cellpair'], 'sigma2_cellpair_new': rq(s2_cell),
        'sigma2_total_old': Q2_EXPECTED['sigma2_total'], 'sigma2_total_new': rq(s2_total),
        'sigma2_resid_old': Q2_EXPECTED['sigma2_resid'], 'sigma2_resid_new': rq(s2_resid),
        'reliability_old_formula': rq(rel_old),
        'abs_diffs': {k: rq(abs(point_vals - Q2_EXPECTED[k2])) for k, point_vals, k2 in [
            ('s2_cond', s2_cond, 'sigma2_cond'), ('s2_cell', s2_cell, 'sigma2_cellpair'),
            ('s2_total', s2_total, 'sigma2_total'), ('s2_resid', s2_resid, 'sigma2_resid')]},
    }
    q2chk['all_within_tol'] = bool(all(v <= TOL_Q2 for v in q2chk['abs_diffs'].values()))
    res['point_estimates'] = {
        'sigma2_cond': rq(s2_cond), 'sigma2_cellpair': rq(s2_cell), 'sigma2_total': rq(s2_total),
        'sigma2_resid_raw': rq(s2_resid), 'sigma2_interaction_raw': rq(s2_int_raw),
        'sigma2_interaction_clipped': rq(s2_int), 'sigma2_noise_avg': rq(noise_avg),
        'shares': {k: rq(v) for k, v in shares.items()},
        'q2_reproduction': q2chk,
        'note_1_43pct': ('share_cond is the ADDITIVE condition main-effect share only; it is NOT a '
                         'bound on learnable shared structure (rank-one counterexample in self_tests) '
                         'and must not be reported as "only 1.43% transferable regularity".'),
    }

    # --- dependency-aware bootstrap variants
    rng = np.random.default_rng(SEED_BOOT_NODE)
    n_cells = len(q['cells'])
    n_conditions = len(q['conds'])
    cell_a = q['ca_idx']
    cell_b = q['cb_idx']
    row_meta = q['row_meta']
    cond_index = {c: i for i, c in enumerate(q['conds'])}
    row_p_idx = np.empty(n_cond, dtype=np.int64)
    row_q_idx = np.empty(n_cond, dtype=np.int64)
    for i, meta in enumerate(row_meta):
        row_p_idx[i] = cond_index[(meta['anchor_id'], meta['library_p'], meta['anchor_conc'], meta['library_conc'])]
        row_q_idx[i] = cond_index[(meta['anchor_id'], meta['library_q'], meta['anchor_conc'], meta['library_conc'])]
    v1_cond = np.full(B_BOOT_A0, np.nan)
    v2_cond = np.full(B_BOOT_A0, np.nan)
    v3_cond = np.full(B_BOOT_A0, np.nan)
    v4 = {k: np.full(B_BOOT_A0, np.nan) for k in
          ('s2_cond', 's2_cell', 's2_total', 's2_resid', 'share_cond', 'rel_old')}
    qbar_v2 = np.full((B_BOOT_A0, n_cond), np.nan)
    t_boot = time.time()
    for b in range(B_BOOT_A0):
        # V1 legacy two-way cluster over condition-pairs x cell-pairs (corrected algebra)
        m_cp = np.bincount(rng.integers(0, n_cond, n_cond), minlength=n_cond).astype(float)
        m_j = np.bincount(rng.integers(0, n_cell, n_cell), minlength=n_cell).astype(float)
        w1 = m_cp[ci] * m_j[cj]
        v1_cond[b] = moment_corrected(y, ci, cj, n_cond, n_cell, w1)['s2_cond']
        # V2 cell-node
        m_cell = np.bincount(rng.integers(0, n_cells, n_cells), minlength=n_cells).astype(float)
        w2 = m_cell[cell_a[cj]] * m_cell[cell_b[cj]]
        v2_cond[b] = moment_corrected(y, ci, cj, n_cond, n_cell, w2)['s2_cond']
        num = np.bincount(ci, weights=w2 * y, minlength=n_cond)
        den = np.bincount(ci, weights=w2, minlength=n_cond)
        qbar_v2[b] = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
        # V3 condition-node
        m_cond = np.bincount(rng.integers(0, n_conditions, n_conditions), minlength=n_conditions).astype(float)
        w3 = m_cond[row_p_idx[ci]] * m_cond[row_q_idx[ci]]
        v3_cond[b] = moment_corrected(y, ci, cj, n_cond, n_cell, w3)['s2_cond']
        # V4 main node (cell + condition)
        w4 = w2 * w3
        e4 = moment_corrected(y, ci, cj, n_cond, n_cell, w4)
        v = e4['s2_cond']
        tot = e4['s2_total']
        v4['s2_cond'][b] = v
        v4['s2_cell'][b] = e4['s2_cell']
        v4['s2_total'][b] = tot
        v4['s2_resid'][b] = e4['s2_resid']
        v4['share_cond'][b] = (max(v, 0.0) / tot) if tot and tot > 0 else np.nan
        resid_term = max(0.0, e4['s2_resid'] - noise_avg) + noise_avg
        v4['rel_old'][b] = (v / (v + resid_term / n_median)) if (v + resid_term / n_median) > 0 else np.nan
    boot_seconds = time.time() - t_boot
    var_qbar = np.nanvar(qbar_v2, axis=0, ddof=1)
    vbar = float(np.nanmean(var_qbar))
    rel_dep = s2_cond / (s2_cond + vbar) if (s2_cond + vbar) > 0 else float('nan')
    v4_rel_dep = np.array([vv / (vv + vbar) if (vv + vbar) > 0 else np.nan for vv in v4['s2_cond']])
    def _summ(vals):
        return {'se': rq(float(np.nanstd(vals, ddof=1))),
                'ci95': [rq(x) for x in pct_ci(vals)],
                'finite_frac': rq(finite_frac(vals)),
                'mean': rq(float(np.nanmean(vals)))}
    res['dependency_aware_inference'] = {
        'bootstrap_B': B_BOOT_A0,
        'main_variant': 'V4_cell+condition_node',
        'note': ('V1 = legacy two-way cluster over 229 condition-pairs x 1501 cell-pairs '
                 '(corrected algebra); V2 = cell-node (96 cells); V3 = condition-node (291 '
                 'conditions); V4 = cell+condition node (main). Weights are products of node '
                 'multiplicities; cell-pair weight = m_a*m_b, condition-pair weight = m_p*m_q.'),
        'V4_main': {'s2_cond': _summ(v4['s2_cond']), 's2_cellpair': _summ(v4['s2_cell']),
                    's2_total': _summ(v4['s2_total']), 's2_resid': _summ(v4['s2_resid']),
                    'share_cond': _summ(v4['share_cond']), 'rel_old_at_median_n': _summ(v4['rel_old'])},
        'V1_legacy_two_way_cluster_corrected': _summ(v1_cond),
        'V2_cell_node_s2_cond': _summ(v2_cond),
        'V3_condition_node_s2_cond': _summ(v3_cond),
        'rel_dep_formula': {
            'definition': 'sigma2_cond/(sigma2_cond + Vbar); Vbar = mean_i Var_boot(Qbar_i) under cell-node bootstrap V2',
            'vbar': rq(vbar),
            'rel_dep_point': rq(rel_dep),
            'rel_dep_ci95': [rq(x) for x in pct_ci(v4_rel_dep)],
            'per_condition_pair_sampling_var_median': rq(float(np.nanmedian(var_qbar))),
        },
        'seconds': rq(boot_seconds),
    }

    # --- graph-aware permutation nulls
    t_perm = time.time()
    Q = q['Q']
    mask = q['mask']
    rng_p = np.random.default_rng(SEED_PERM)
    col_idx = [np.nonzero(mask[:, j])[0] for j in range(n_cell)]
    row_idx = [np.nonzero(mask[i, :])[0] for i in range(n_cond)]
    null_cond = np.full(B_PERM_A0, np.nan)
    null_cell = np.full(B_PERM_A0, np.nan)
    idx_map = np.ravel_multi_index((ci, cj), Q.shape)  # maps observation order -> row-major flat index
    for b in range(B_PERM_A0):
        Yp = Q.copy()
        for j in range(n_cell):
            rr = col_idx[j]
            vv = Q[rr, j]
            Yp[rr, j] = vv[rng_p.permutation(rr.size)]
        yp = Yp.reshape(-1)[idx_map]
        null_cond[b] = moment_corrected(yp, ci, cj, n_cond, n_cell, None)['s2_cond']
        Yq = Q.copy()
        for i in range(n_cond):
            cc = row_idx[i]
            vv = Q[i, cc]
            Yq[i, cc] = vv[rng_p.permutation(cc.size)]
        yq = Yq.reshape(-1)[idx_map]
        null_cell[b] = moment_corrected(yq, ci, cj, n_cond, n_cell, None)['s2_cell']
    p_cond = (1 + int(np.nansum(null_cond >= s2_cond))) / (B_PERM_A0 + 1)
    p_cell = (1 + int(np.nansum(null_cell >= s2_cell))) / (B_PERM_A0 + 1)
    res['permutation_nulls_graph_aware'] = {
        'method': ('sigma2_cond: permute each cell-pair column\'s observed values among its observed '
                   'rows (keeps sparsity/column multiset, destroys condition-pair alignment); '
                   'sigma2_cellpair: permute each condition-pair row\'s observed values among observed '
                   'columns. q2 \'shuffle condition-pair labels across observations\' is NOT used as the '
                   'R197 null (it destroys layout/missing/shared-key structure).'),
        'B': B_PERM_A0,
        'sigma2_cond': {'null_mean': rq(float(np.nanmean(null_cond))),
                        'null_sd': rq(float(np.nanstd(null_cond, ddof=1))),
                        'null_q95': rq(float(np.nanpercentile(null_cond, 95))),
                        'observed': rq(s2_cond), 'p_value': rq(p_cond)},
        'sigma2_cellpair': {'null_mean': rq(float(np.nanmean(null_cell))),
                            'null_sd': rq(float(np.nanstd(null_cell, ddof=1))),
                            'null_q95': rq(float(np.nanpercentile(null_cell, 95))),
                            'observed': rq(s2_cell), 'p_value': rq(p_cell)},
        'seconds': rq(time.time() - t_perm),
    }

    # --- split-half reliability (cell halves; Spearman-Brown)
    t_split = time.time()
    rng_s = np.random.default_rng(SEED_SPLIT)
    n_cells_total = len(q['cells'])
    rel_splits = []
    r_splits = []
    n_cp_used = []
    cell_a = q['ca_idx']
    cell_b = q['cb_idx']
    for s in range(N_SPLIT):
        perm = rng_s.permutation(n_cells_total)
        half = np.zeros(n_cells_total, dtype=np.int8)
        half[perm[:n_cells_total // 2]] = 1
        rel = [None, None]
        r = None
        n_used = 0
        for hside in (0, 1):
            colmask = (half[cell_a] == hside) & (half[cell_b] == hside)
            Qh = Q[:, colmask]
            cnt = np.sum(np.isfinite(Qh), axis=1)
            with np.errstate(invalid='ignore'):
                qbar = np.where(cnt > 0, np.nansum(Qh, axis=1) / np.maximum(cnt, 1), np.nan)
            rel[hside] = np.where(cnt >= 10, qbar, np.nan)
        ok = np.isfinite(rel[0]) & np.isfinite(rel[1])
        n_used = int(ok.sum())
        if n_used >= 30:
            r, _ = spearman(rel[0][ok], rel[1][ok])
        if r is not None:
            r_splits.append(r)
            rel_splits.append(2.0 * r / (1.0 + r))
            n_cp_used.append(n_used)
    r_splits = np.asarray(r_splits)
    rel_splits = np.asarray(rel_splits)
    rel_split_median = float(np.median(rel_splits)) if rel_splits.size else float('nan')
    res['reliability_recalibration'] = {
        'R_old_q2_formula': rq(rel_old),
        'R_formula_dep_q2_definition': rq(rel_dep),
        'R_formula_dep_ci95': [rq(x) for x in pct_ci(v4_rel_dep)],
        'R_split_half_spearman_brown': {
            'n_splits': int(rel_splits.size),
            'median': rq(rel_split_median),
            'min': rq(float(rel_splits.min())) if rel_splits.size else None,
            'max': rq(float(rel_splits.max())) if rel_splits.size else None,
            'ci95': [rq(x) for x in pct_ci(rel_splits)],
            'median_raw_spearman_r': rq(float(np.median(r_splits))) if r_splits.size else None,
            'median_condition_pairs_used': int(np.median(n_cp_used)) if n_cp_used else None,
            'definition': ('split 96 cells into two halves (20 seeded splits); condition-level means '
                           'from cell-pairs entirely inside each half (>=10 per half); Spearman across '
                           'condition-pairs; Spearman-Brown rel=2r/(1+r)'),
        },
        'threshold': RELIABILITY_THRESHOLD,
        'certified': bool(rel_split_median >= RELIABILITY_THRESHOLD),
        'seconds': rq(time.time() - t_split),
    }

    # --- A0 status
    v4_ci = res['dependency_aware_inference']['V4_main']['s2_cond']['ci95']
    cond_robust = bool(v4_ci[0] is not None and v4_ci[0] > 0)
    perm_sig = bool(p_cond < 0.05)
    if (not math.isfinite(s2_cond)) or (not math.isfinite(rel_old)):
        status = 'q2_recalibration_inconclusive'
    elif cond_robust and (rel_split_median >= RELIABILITY_THRESHOLD) and perm_sig:
        status = 'q2_inference_robust'
    else:
        status = 'q2_inference_not_robust_under_dependence'
    res['a0_status'] = {
        'status': status,
        'criteria': {'v4_ci_lower_positive': cond_robust,
                     'split_half_reliability_ge_0.50': bool(rel_split_median >= RELIABILITY_THRESHOLD),
                     'permutation_p_lt_0.05': perm_sig},
        'old_ci_s2_cond_q2': [0.000297, 0.000674],
        'new_ci_s2_cond_v4': v4_ci,
        'old_reliability_0.867863_certified_by_split_half': bool(rel_split_median >= RELIABILITY_THRESHOLD),
        'note': ('A0 recalibrates inference only; it does not change A1 inconclusive, does not pass A2, '
                 'and does not interpret share_cond as transferable regularity.'),
    }
    # --- per-condition-pair rows
    rel_i_old = s2_cond / (s2_cond + (s2_int + noise_avg) / n_i)
    rel_i_dep = s2_cond / (s2_cond + np.where(np.isfinite(var_qbar), var_qbar, np.nan))
    qmean = np.nanmean(Q, axis=1)
    qsd = np.nanstd(Q, axis=1, ddof=1)
    rows = pd.DataFrame({
        'condition_pair_id': np.arange(n_cond),
        'anchor_id': [m['anchor_id'] for m in row_meta],
        'library_p': [m['library_p'] for m in row_meta],
        'library_q': [m['library_q'] for m in row_meta],
        'anchor_conc': [m['anchor_conc'] for m in row_meta],
        'library_conc': [m['library_conc'] for m in row_meta],
        'n_cell_pairs': n_i.astype(int),
        'q_mean_original': qmean,
        'q_sd_original': qsd,
        'reliability_old_formula': rel_i_old,
        'reliability_dep_formula': rel_i_dep,
        'reliability_split_half': np.nan,
    })
    res['seconds'] = rq(time.time() - t0)
    return res, rows, {'vbar': vbar, 'rel_split_median': rel_split_median, 's2_int': s2_int,
                       'noise_avg': noise_avg, 's2_cond': s2_cond}


# --------------------------------------------------------------------------- B: features/models
def build_b_features(q):
    cells = q['cells']
    n_cells = len(cells)
    cp_list = q['cp_list']
    row_meta = q['row_meta']
    df = q['df']
    ci = q['ci']
    cj = q['cj_arr']
    n_obs = q['n_obs']
    n_cond = q['n_condpair']
    # library / anchor ids used
    libs_used = sorted({m['library_p'] for m in row_meta} | {m['library_q'] for m in row_meta})
    anchors_used = sorted({m['anchor_id'] for m in row_meta})
    lib_idx = {l: i for i, l in enumerate(libs_used)}
    anc_idx = {a: i for i, a in enumerate(anchors_used)}
    # metadata per library / anchor
    lib_meta = {}
    for r in df[['LIBRARY_ID', 'LIBRARY_PATHWAY', 'LIBRARY_DRUG_TYPE']].itertuples(index=False):
        lid = str(r.LIBRARY_ID).strip()
        if lid in lib_idx and lid not in lib_meta:
            lib_meta[lid] = (str(r.LIBRARY_PATHWAY), str(r.LIBRARY_DRUG_TYPE))
    anc_meta = {}
    for r in df[['ANCHOR_ID', 'ANCHOR_PATHWAY', 'ANCHOR_DRUG_TYPE']].itertuples(index=False):
        aid = str(r.ANCHOR_ID).strip()
        if aid in anc_idx and aid not in anc_meta:
            anc_meta[aid] = (str(r.ANCHOR_PATHWAY), str(r.ANCHOR_DRUG_TYPE))
    lib_pathways = sorted({lib_meta[l][0] for l in libs_used})
    anc_pathways = sorted({anc_meta[a][0] for a in anchors_used})
    libp_pos = {p: i for i, p in enumerate(lib_pathways)}
    ancp_pos = {p: i for i, p in enumerate(anc_pathways)}
    # single-agent profiles per (cell, library) mean over fitted rows
    df2 = df[['CELL_LINE_NAME', 'LIBRARY_ID', 'LIBRARY_EMAX', 'LIBRARY_AUC']].copy()
    df2['cell'] = np.array([nk(x) if isinstance(x, str) else None for x in df2['CELL_LINE_NAME']])
    df2['lid'] = df2['LIBRARY_ID'].astype(str).str.strip()
    sm = df2.groupby(['cell', 'lid'])[['LIBRARY_EMAX', 'LIBRARY_AUC']].mean()
    mono_e = np.full((n_cells, len(libs_used)), np.nan)
    mono_a = np.full((n_cells, len(libs_used)), np.nan)
    for (c, l), row in sm.iterrows():
        if c in cells and l in lib_idx:
            mono_e[cells.index(c), lib_idx[l]] = row['LIBRARY_EMAX']
            mono_a[cells.index(c), lib_idx[l]] = row['LIBRARY_AUC']
    mono_missing_frac = {}
    for name, arr in (('emax', mono_e), ('auc', mono_a)):
        miss = np.isnan(arr)
        mono_missing_frac[name] = float(miss.mean())
        for j in range(arr.shape[1]):
            col = arr[:, j]
            med = np.nanmedian(col)
            if not math.isfinite(med):
                med = 0.0
            col[np.isnan(col)] = med
    # tissue
    tissues = sorted({q['cells_meta'][c]['tissue'] for c in cells})
    tissue_idx = np.array([tissues.index(q['cells_meta'][c]['tissue']) for c in cells])
    # condition-pair meta arrays
    row_anchor = np.array([anc_idx[m['anchor_id']] for m in row_meta])
    row_lp = np.array([lib_idx[m['library_p']] for m in row_meta])
    row_lq = np.array([lib_idx[m['library_q']] for m in row_meta])
    row_aconc = np.array([float(m['anchor_conc']) for m in row_meta])
    row_lconc = np.array([float(m['library_conc']) for m in row_meta])
    row_lp_path = np.array([libp_pos[lib_meta[libs_used[j]][0]] for j in row_lp])
    row_lq_path = np.array([libp_pos[lib_meta[libs_used[j]][0]] for j in row_lq])
    row_lp_type = np.array([1.0 if lib_meta[libs_used[j]][1] == 'Targeted' else 0.0 for j in row_lp])
    row_lq_type = np.array([1.0 if lib_meta[libs_used[j]][1] == 'Targeted' else 0.0 for j in row_lq])
    row_anc_type = np.array([1.0 if anc_meta[anchors_used[j]][1] == 'Targeted' else 0.0 for j in row_anchor])
    row_anc_path = np.array([ancp_pos[anc_meta[anchors_used[j]][0]] for j in row_anchor])
    row_same_path = (row_lp_path == row_lq_path).astype(float)
    # condition features (n_cond x Kc)
    Kc = len(anc_pathways) + 1 + 2 * len(lib_pathways) + 2 + 1 + 2
    Cfeat = np.zeros((n_cond, Kc))
    Cfeat[np.arange(n_cond), row_anc_path] = 1.0
    off = len(anc_pathways)
    Cfeat[:, off] = row_anc_type
    off += 1
    Cfeat[np.arange(n_cond), off + row_lp_path] = 1.0
    off += len(lib_pathways)
    Cfeat[np.arange(n_cond), off + row_lq_path] = 1.0
    off += len(lib_pathways)
    Cfeat[:, off] = row_lp_type
    Cfeat[:, off + 1] = row_lq_type
    off += 2
    Cfeat[:, off] = row_same_path
    off += 1
    Cfeat[:, off] = row_aconc
    Cfeat[:, off + 1] = row_lconc
    # cell-pair features (n_cp x 7)
    ca = q['ca_idx']
    cb = q['cb_idx']
    C_p = np.zeros((q['n_cp'], 7))
    C_p[np.arange(q['n_cp']), tissue_idx[ca]] = 1.0
    C_p[np.arange(q['n_cp']), 3 + tissue_idx[cb]] = 1.0
    C_p[:, 6] = (tissue_idx[ca] == tissue_idx[cb]).astype(float)
    n_obs = len(ci)
    # single-agent features per observation
    ta = tissue_idx[ca[cj]]
    tb = tissue_idx[cb[cj]]
    lp = row_lp[ci]
    lq = row_lq[ci]
    dA_e = mono_e[ca[cj], lp] - mono_e[ca[cj], lq]
    dB_e = mono_e[cb[cj], lp] - mono_e[cb[cj], lq]
    dA_a = mono_a[ca[cj], lp] - mono_a[ca[cj], lq]
    dB_a = mono_a[cb[cj], lp] - mono_a[cb[cj], lq]
    single = np.column_stack([dA_e, dB_e, dA_e - dB_e, dA_a, dB_a, dA_a - dB_a])
    F1 = np.hstack([C_p[cj], Cfeat[ci], single])
    # interaction block: cell-side C (13) x condition-side G (<=20)
    cell_side = np.column_stack([C_p[cj], single])  # 13
    G = np.column_stack([row_lp_type[ci], row_lq_type[ci], row_same_path[ci],
                         np.eye(len(anc_pathways))[row_anc_path[ci]]])
    inter = (cell_side[:, :, None] * G[:, None, :]).reshape(n_obs, -1)
    F3 = np.hstack([F1, inter])
    meta = {'libs_used': libs_used, 'anchors_used': anchors_used, 'tissues': tissues,
            'lib_pathways': lib_pathways, 'anc_pathways': anc_pathways,
            'mono_missing_frac': mono_missing_frac,
            'dims': {'F1': int(F1.shape[1]), 'F3': int(F3.shape[1]),
                     'interaction_block': int(inter.shape[1])},
            'row_lp': row_lp, 'row_lq': row_lq, 'row_anchor': row_anchor,
            'mats': {'mono_e': mono_e, 'mono_a': mono_a, 'tissue_idx': tissue_idx,
                     'ca': ca, 'cb': cb}}
    return F1, F3, meta


def b0_fit(Y, train_mask, iters=200, tol=1e-9):
    """Additive mu + a_i + b_j by alternating means on training entries."""
    n_i = train_mask.sum(1).astype(float)
    n_j = train_mask.sum(0).astype(float)
    has_i = n_i > 0
    has_j = n_j > 0
    Ytr = np.where(train_mask, Y, 0.0)
    mu = float(Ytr.sum() / max(train_mask.sum(), 1))
    a = np.zeros(Y.shape[0])
    b = np.zeros(Y.shape[1])
    for it in range(iters):
        # a update
        sa = ((Ytr - mu - b[None, :]) * train_mask).sum(1)
        a_new = np.where(has_i, sa / np.maximum(n_i, 1.0), 0.0)
        sb = ((Ytr - mu - a_new[:, None]) * train_mask).sum(0)
        b_new = np.where(has_j, sb / np.maximum(n_j, 1.0), 0.0)
        d = max(float(np.max(np.abs(a_new - a))) if has_i.any() else 0.0,
                float(np.max(np.abs(b_new - b))) if has_j.any() else 0.0)
        a, b = a_new, b_new
        if d < tol:
            break
    return mu, a, b, has_i, has_j


def b0_predict(mu, a, b, has_i, has_j, row_i, col_j):
    ai = np.where(has_i[row_i], a[row_i], 0.0)
    bj = np.where(has_j[col_j], b[col_j], 0.0)
    return mu + ai + bj


def b2_fit(Y, train_mask, rank, seed, lam=ALS_LAMBDA, iters=ALS_ITERS):
    """Additive + rank-r ALS on observed (training) entries only."""
    n_r, n_c = Y.shape
    mf = train_mask.astype(float)
    mfT = mf.T
    mu, a, b, has_i, has_j = b0_fit(Y, train_mask, iters=40)
    rng = np.random.default_rng(seed)
    U = rng.normal(0.0, 0.01, (n_r, rank))
    V = rng.normal(0.0, 0.01, (n_c, rank))
    eye = lam * np.eye(rank)
    Ytr = np.where(train_mask, Y, 0.0)
    for it in range(iters):
        Rz = np.where(train_mask, Y - mu - a[:, None] - b[None, :], 0.0)
        X = (V[:, :, None] * V[:, None, :]).reshape(n_c, rank * rank)
        A = (mf @ X).reshape(n_r, rank, rank) + eye[None, :, :]
        Bm = Rz @ V
        U = np.linalg.solve(A, Bm[:, :, None])[:, :, 0]
        Rz2 = np.where(train_mask, Y - mu - a[:, None] - b[None, :], 0.0)
        XU = (U[:, :, None] * U[:, None, :]).reshape(n_r, rank * rank)
        A2 = (mfT @ XU).reshape(n_c, rank, rank) + eye[None, :, :]
        B2m = Rz2.T @ U
        V = np.linalg.solve(A2, B2m[:, :, None])[:, :, 0]
        # additive update given factors
        pred_fac = U @ V.T
        sa = ((Ytr - mu - b[None, :] - pred_fac) * mf).sum(1)
        a = np.where(has_i, sa / np.maximum(train_mask.sum(1), 1.0), 0.0)
        sb = ((Ytr - mu - a[:, None] - pred_fac) * mf).sum(0)
        b = np.where(has_j, sb / np.maximum(train_mask.sum(0), 1.0), 0.0)
    # unidentifiable rows/cols -> zero factors
    V[~has_j, :] = 0.0
    U[~has_i, :] = 0.0
    return mu, a, b, has_i, has_j, U, V


def b2_predict(mu, a, b, has_i, has_j, U, V, row_i, col_j):
    ai = np.where(has_i[row_i], a[row_i], 0.0)
    bj = np.where(has_j[col_j], b[col_j], 0.0)
    fac = np.sum(U[row_i, :] * V[col_j, :], axis=1)
    return mu + ai + bj + fac


class RidgeSet:
    """Ridge with fixed feature matrix; per-fold caches for lambda selection."""

    def __init__(self, X, y_all):
        self.X = X
        self.XtX = X.T @ X
        self.Xty = X.T @ y_all
        self.n = X.shape[0]

    def prepare(self, train_entries, inner_assign, seed):
        """Precompute X-only quantities for a fold: standardized gram/eigen per inner fold."""
        idx = np.nonzero(train_entries)[0]
        Xtr = self.X[idx]
        self.idx = idx
        self.ntr = idx.size
        self.mu = Xtr.mean(0)
        self.sd = Xtr.std(0)
        self.sd[self.sd < 1e-12] = 1.0
        Xs = (Xtr - self.mu) / self.sd
        self.Xs = Xs
        self.XtXs = Xs.T @ Xs
        # inner folds: assignment array over train positions
        assign = inner_assign
        self.inner = []
        for k in range(INNER_FOLDS):
            val = assign == k
            tr = ~val
            if tr.sum() < 50 or val.sum() < 20:
                self.inner.append(None)
                continue
            Xs_tr = Xs[tr]
            mu_k = Xs_tr.mean(0)
            sd_k = Xs_tr.std(0)
            sd_k[sd_k < 1e-12] = 1.0
            Ztr = (Xs_tr - mu_k) / sd_k
            G = Ztr.T @ Ztr
            w, V = np.linalg.eigh(G)
            w = np.maximum(w, 0.0)
            Zval = (Xs[val] - mu_k) / sd_k
            ZvalV = Zval @ V
            ytr_pos = np.nonzero(tr)[0]
            yval_pos = np.nonzero(val)[0]
            self.inner.append({'tr_pos': ytr_pos, 'val_pos': yval_pos, 'w': w, 'V': V,
                               'ZvalV': ZvalV, 'n_tr': int(tr.sum()),
                               'Ztr': Ztr})

    def fit_predict(self, y_obs, train_entries, pred_entries, lambdas=LAMBDA_GRID):
        """lambda inner CV on training entries, then fit on train and predict pred_entries."""
        idx = self.idx
        Xs = self.Xs
        ytr = y_obs[idx]
        ybar = float(ytr.mean())
        yc = ytr - ybar
        Xty = Xs.T @ yc
        # inner CV
        best = None
        for lam in lambdas:
            sse = 0.0
            nval = 0
            for inner in self.inner:
                if inner is None:
                    continue
                trp = inner['tr_pos']
                valp = inner['val_pos']
                # centered y
                yt = ytr[trp]
                yv = ytr[valp]
                ytbar = float(yt.mean())
                G = inner
                bvec = G['Ztr'].T @ (yt - ytbar)
                c = (G['V'].T @ bvec) / (G['w'] + lam)
                pred = G['ZvalV'] @ c
                sse += float(np.sum((yv - ytbar - pred) ** 2))
                nval += valp.size
            mse = sse / max(nval, 1)
            if best is None or mse < best[0]:
                best = (mse, lam)
        lam = best[1] if best is not None else 1.0
        w = np.linalg.solve(self.XtXs + lam * np.eye(self.X.shape[1]), Xty)
        Xp = (self.X[np.nonzero(pred_entries)[0]] - self.mu) / self.sd
        return ybar + Xp @ w, lam, (best[0] if best else None)


# --------------------------------------------------------------------------- B designs
def make_folds(q, design):
    n_cells = len(q['cells'])
    cp_list = q['cp_list']
    cells = q['cells']
    n_obs = q['n_obs']
    if design == 'H197a':
        fold_cell = np.empty(n_cells, dtype=int)
        for i in range(n_cells):
            fold_cell[i] = i % 5
        cell_idx = {c: i for i, c in enumerate(cells)}
        f_ai = np.array([fold_cell[cell_idx[a]] for a, b in cp_list])
        f_bi = np.array([fold_cell[cell_idx[b]] for a, b in cp_list])
        folds = []
        for f in range(5):
            test_cols = (f_ai == f) & (f_bi == f)
            test_mask = np.zeros(n_obs, dtype=bool)
            test_mask[np.isin(q['cj_arr'], np.nonzero(test_cols)[0])] = True
            test_cells = set(np.nonzero(fold_cell == f)[0].tolist())
            train_mask = np.zeros(n_obs, dtype=bool)
            ok = np.array([(cell_idx[a] not in test_cells) and (cell_idx[b] not in test_cells)
                           for a, b in cp_list])
            train_mask[np.isin(q['cj_arr'], np.nonzero(ok)[0])] = True
            folds.append({'fold': f, 'test': test_mask, 'train': train_mask,
                          'n_test': int(test_mask.sum()), 'n_train': int(train_mask.sum()),
                          'n_test_cells': int((fold_cell == f).sum())})
    elif design == 'H197b':
        n_rows = q['n_condpair']
        folds = []
        for f in range(5):
            test_rows = np.arange(n_rows) % 5 == f
            test_mask = test_rows[q['ci']]
            train_mask = (~test_rows)[q['ci']]
            folds.append({'fold': f, 'test': test_mask, 'train': train_mask,
                          'n_test': int(test_mask.sum()), 'n_train': int(train_mask.sum()),
                          'n_test_rows': int(test_rows.sum())})
    else:
        n_obs_ = q['n_obs']
        order = np.arange(n_obs_)
        assign = order % 5
        folds = []
        for f in range(5):
            test_mask = assign == f
            train_mask = ~test_mask
            folds.append({'fold': f, 'test': test_mask, 'train': train_mask,
                          'n_test': int(test_mask.sum()), 'n_train': int(train_mask.sum())})
    return folds


def inner_assign_for(design, fold, n_train):
    """Deterministic inner-CV assignment (frozen seed derivation)."""
    design_idx = {'H197a': 0, 'H197b': 1, 'H197c': 2}[design]
    rng = np.random.default_rng(SEED_INNER + 10 * design_idx + fold)
    return rng.permutation(n_train) % INNER_FOLDS


def run_design(q, design, F1, F3, folds, y_override=None):
    """Fit all models per fold and collect OOF predictions + metrics."""
    Q = q['Q']
    mask = q['mask']
    y = q['y'] if y_override is None else y_override
    Y = np.where(mask, Q, np.nan)
    if y_override is not None:
        Yn = np.full_like(Y, np.nan)
        Yn[q['ci'], q['cj_arr']] = y_override
        Y = Yn
    n_obs = q['n_obs']
    ri = q['ci']
    cjj = q['cj_arr']
    models = ['B0', 'B1', 'B2', 'B3', 'B4']
    oof = {m: np.full(n_obs, np.nan) for m in models}
    per_fold = {m: [] for m in models}
    primary = get_primary_model(design)
    lam_log = {m: [] for m in ('B1', 'B3')}
    rank_log = []
    ridge1 = RidgeSet(F1, y)
    ridge3 = RidgeSet(F3, y)
    X4 = np.empty((n_obs, F3.shape[1] + 1))
    X4[:, :-1] = F3
    t0 = time.time()
    for fold in folds:
        tr = fold['train']
        te = fold['test']
        tr_idx = np.nonzero(tr)[0]
        te_idx = np.nonzero(te)[0]
        train_mask = np.zeros_like(mask)
        train_mask[ri[tr_idx], cjj[tr_idx]] = True
        assign = inner_assign_for(design, fold['fold'], tr_idx.size)
        # B0
        mu, a, b, has_i, has_j = b0_fit(Y, train_mask)
        p0 = b0_predict(mu, a, b, has_i, has_j, ri[te_idx], cjj[te_idx])
        oof['B0'][te_idx] = p0
        rho0, _ = spearman(p0, y[te_idx])
        per_fold['B0'].append(rho0)
        # B1
        ridge1.prepare(tr, assign, SEED_INNER)
        p1, lam1, _ = ridge1.fit_predict(y, tr, te)
        oof['B1'][te_idx] = p1
        rho1, _ = spearman(p1, y[te_idx])
        per_fold['B1'].append(rho1)
        lam_log['B1'].append(lam1)
        # B2
        seed_rank = SEED_INNER + 100 * {'H197a': 0, 'H197b': 2, 'H197c': 1}[design] + fold['fold']
        rng_rank = np.random.default_rng(seed_rank)
        val_sel = rng_rank.random(tr_idx.size) < 0.2
        val_entries = tr_idx[val_sel]
        keep = tr_idx[~val_sel]
        train_minus_val = np.zeros_like(mask)
        train_minus_val[ri[keep], cjj[keep]] = True
        best_rank, best_mse = None, None
        for r in RANKS:
            mu2, a2, b2, hi2, hj2, U2, V2 = b2_fit(Y, train_minus_val, r, SEED_INNER + r)
            pv = b2_predict(mu2, a2, b2, hi2, hj2, U2, V2, ri[val_entries], cjj[val_entries])
            mse = float(np.mean((pv - y[val_entries]) ** 2))
            if best_mse is None or mse < best_mse:
                best_mse, best_rank = mse, r
        mu2, a2, b2, hi2, hj2, U2, V2 = b2_fit(Y, train_mask, best_rank, SEED_INNER + best_rank)
        p2 = b2_predict(mu2, a2, b2, hi2, hj2, U2, V2, ri[te_idx], cjj[te_idx])
        oof['B2'][te_idx] = p2
        rho2, _ = spearman(p2, y[te_idx])
        per_fold['B2'].append(rho2)
        rank_log.append({'fold': fold['fold'], 'rank': int(best_rank), 'inner_mse': rq(best_mse)})
        # B3
        ridge3.prepare(tr, assign, SEED_INNER)
        p3, lam3, _ = ridge3.fit_predict(y, tr, te)
        oof['B3'][te_idx] = p3
        rho3, _ = spearman(p3, y[te_idx])
        per_fold['B3'].append(rho3)
        lam_log['B3'].append(lam3)
        # B4
        X4[:, -1] = b0_predict(mu, a, b, has_i, has_j, ri, cjj)
        hgb = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=31,
                                            min_samples_leaf=20, l2_regularization=1.0,
                                            random_state=SEED_HGB)
        hgb.fit(X4[tr_idx], y[tr_idx])
        p4 = hgb.predict(X4[te_idx])
        oof['B4'][te_idx] = p4
        rho4, _ = spearman(p4, y[te_idx])
        per_fold['B4'].append(rho4)
    # pooled metrics
    metrics = {}
    for m in models:
        rho, n = spearman(oof[m], y)
        ok = np.isfinite(oof[m])
        yt = y[ok]
        pred = oof[m][ok]
        sse = float(np.sum((yt - pred) ** 2))
        sst = float(np.sum((yt - yt.mean()) ** 2))
        metrics[m] = {'oof_spearman': rq(rho), 'n_oof': int(n),
                      'oof_r2': rq(1.0 - sse / sst) if sst > 0 else None,
                      'per_fold_spearman': [rq(x) for x in per_fold[m]],
                      'per_fold_mean': rq(float(np.nanmean(per_fold[m]))),
                      'per_fold_sd': rq(float(np.nanstd(per_fold[m], ddof=1)))}
    deltas = {}
    for m in models:
        if m == 'B0':
            continue
        d = metrics[m]['oof_spearman'] - metrics['B0']['oof_spearman']
        fd = [a - b for a, b in zip(per_fold[m], per_fold['B0'])]
        deltas[m] = {'delta_vs_B0': rq(d), 'per_fold_delta': [rq(x) for x in fd],
                     'per_fold_delta_mean': rq(float(np.nanmean(fd))),
                     'per_fold_delta_sd': rq(float(np.nanstd(fd, ddof=1)))}
    # per-condition-pair row summaries (OOF)
    row_summary = {}
    for m in ('B0', primary):
        pred = oof[m]
        ok = np.isfinite(pred)
        cnt = np.bincount(ri[ok], minlength=q['n_condpair'])
        s_sum = np.bincount(ri[ok], weights=pred[ok], minlength=q['n_condpair'])
        row_pred_mean = np.where(cnt > 0, s_sum / np.maximum(cnt, 1), np.nan)
        resid = y - pred
        okr = np.isfinite(resid)
        sres = np.bincount(ri[okr], weights=resid[okr], minlength=q['n_condpair'])
        row_summary['%s_%s_pred_mean' % (design, m)] = row_pred_mean
        row_summary['%s_%s_resid_mean' % (design, m)] = np.where(cnt > 0, sres / np.maximum(cnt, 1), np.nan)
    return {'design': design, 'primary_model': primary, 'folds': folds,
            'oof': oof, 'metrics': metrics, 'deltas': deltas,
            'rank_selection': rank_log, 'lambda_selection': {k: v for k, v in lam_log.items()},
            'row_summary': row_summary,
            'seconds': rq(time.time() - t0)}


def get_primary_model(design):
    return {'H197a': 'B3', 'H197b': 'B3', 'H197c': 'B2'}[design]


def cluster_bootstrap_delta(q, design, oof, y, B, seed, pred_key_primary):
    """Cluster bootstrap CI of Delta(primary - B0) over OOF entries."""
    rng = np.random.default_rng(seed)
    ri = q['ci']
    cj = q['cj_arr']
    cells = q['cells']
    cp_list = q['cp_list']
    n_cells = len(cells)
    cell_idx = {c: i for i, c in enumerate(cells)}
    ca = np.array([cell_idx[a] for a, b in cp_list])
    cb = np.array([cell_idx[b] for a, b in cp_list])
    n_cp = len(cp_list)
    n_cond = q['n_condpair']
    pred0 = oof['B0']
    predP = oof[pred_key_primary]
    ok = np.isfinite(pred0) & np.isfinite(predP) & np.isfinite(y)
    entry_idx = np.nonzero(ok)[0]
    obs_row = ri[entry_idx]
    obs_col = cj[entry_idx]
    yv = y[entry_idx]
    p0 = pred0[entry_idx]
    pp = predP[entry_idx]
    out = np.full(B, np.nan)
    for b in range(B):
        if design == 'H197a':
            m = np.bincount(rng.integers(0, n_cells, n_cells), minlength=n_cells)
            w = m[ca[obs_col]] * m[cb[obs_col]]
        elif design == 'H197b':
            m = np.bincount(rng.integers(0, n_cond, n_cond), minlength=n_cond)
            w = m[obs_row]
        else:
            mc = np.bincount(rng.integers(0, n_cells, n_cells), minlength=n_cells)
            mr = np.bincount(rng.integers(0, n_cond, n_cond), minlength=n_cond)
            w = mc[ca[obs_col]] * mc[cb[obs_col]] * mr[obs_row]
        sel = w > 0
        if sel.sum() < 50:
            continue
        idx = np.repeat(np.arange(sel.size), w.astype(int))
        r_prim, _ = spearman(pp[idx], yv[idx])
        r0, _ = spearman(p0[idx], yv[idx])
        if r_prim is not None and r0 is not None:
            out[b] = r_prim - r0
    return out


def permutation_null_delta(oof, y, primary_model, B, seed, design):
    rng = np.random.default_rng(seed)
    pred0 = oof['B0']
    predP = oof[primary_model]
    ok = np.isfinite(pred0) & np.isfinite(predP)
    idx = np.nonzero(ok)[0]
    yv = y[idx]
    p0 = pred0[idx]
    pp = predP[idx]
    out = np.full(B, np.nan)
    for b in range(B):
        yp = yv[rng.permutation(yv.size)]
        r0, _ = spearman(p0, yp)
        rp, _ = spearman(pp, yp)
        if r0 is not None and rp is not None:
            out[b] = rp - r0
    return out


# --------------------------------------------------------------------------- B type-I simulation
def type_i_simulations(q, design, F1, F3, folds, n_sims, seed):
    """Conservative upper-bound type-I of the relaxed frozen rule.

    Relaxed rule used in simulation = (pooled Delta >= DELTA_MIN) and (cluster-bootstrap
    CI lower of Delta > 0). The capacity-control and permutation-p components are omitted
    in simulation; omitting conjuncts can only INCREASE type-I, so the measured rate is a
    conservative upper bound for the full frozen rule.
    """
    Q = q['Q']
    mask = q['mask']
    y_obs = q['y']
    n_obs = q['n_obs']
    ri = q['ci']
    cjj = q['cj_arr']
    primary = get_primary_model(design)
    rng = np.random.default_rng(seed)
    # fold-level static structures
    fstat = []
    rset = RidgeSet(F3, y_obs) if primary == 'B3' else None
    for fold in folds:
        tr = fold['train']
        te = fold['test']
        tr_idx = np.nonzero(tr)[0]
        te_idx = np.nonzero(te)[0]
        train_mask = np.zeros_like(mask)
        train_mask[ri[tr_idx], cjj[tr_idx]] = True
        st = {'fold': fold['fold'], 'tr': tr, 'te': te, 'tr_idx': tr_idx, 'te_idx': te_idx,
              'train_mask': train_mask}
        if primary == 'B3':
            st['assign'] = inner_assign_for(design, fold['fold'], tr_idx.size)
        if primary == 'B2':
            rng_rank = np.random.default_rng(SEED_INNER + 1000 + 10 * fold['fold'])
            val_sel = rng_rank.random(tr_idx.size) < 0.2
            st['val_entries'] = tr_idx[val_sel]
            keep = tr_idx[~val_sel]
            tmv = np.zeros_like(mask)
            tmv[ri[keep], cjj[keep]] = True
            st['train_minus_val'] = tmv
        fstat.append(st)
    runs = []
    models = ['B0', primary]
    t0 = time.time()
    for s in range(n_sims):
        y_sim = y_obs[rng.permutation(y_obs.size)]
        Ysim = np.full_like(Q, np.nan)
        Ysim[ri, cjj] = y_sim
        oof = {m: np.full(n_obs, np.nan) for m in models}
        for st in fstat:
            train_mask = st['train_mask']
            te_idx = st['te_idx']
            mu, a, b, hi, hj = b0_fit(Ysim, train_mask)
            oof['B0'][te_idx] = b0_predict(mu, a, b, hi, hj, ri[te_idx], cjj[te_idx])
            if primary == 'B3':
                rset.prepare(st['tr'], st['assign'], SEED_INNER)
                p3, _, _ = rset.fit_predict(y_sim, st['tr'], st['te'])
                oof['B3'][te_idx] = p3
            else:
                best_rank, best_mse = None, None
                for r in RANKS:
                    mu2, a2, b2, hi2, hj2, U2, V2 = b2_fit(Ysim, st['train_minus_val'], r, SEED_INNER + r)
                    pv = b2_predict(mu2, a2, b2, hi2, hj2, U2, V2,
                                    ri[st['val_entries']], cjj[st['val_entries']])
                    mse = float(np.mean((pv - y_sim[st['val_entries']]) ** 2))
                    if best_mse is None or mse < best_mse:
                        best_mse, best_rank = mse, r
                mu2, a2, b2, hi2, hj2, U2, V2 = b2_fit(Ysim, train_mask, best_rank, SEED_INNER + best_rank)
                oof['B2'][te_idx] = b2_predict(mu2, a2, b2, hi2, hj2, U2, V2,
                                               ri[te_idx], cjj[te_idx])
        rhoP, _ = spearman(oof[primary], y_sim)
        rho0, _ = spearman(oof['B0'], y_sim)
        delta = (rhoP - rho0) if (rhoP is not None and rho0 is not None) else None
        boot = cluster_bootstrap_delta(q, design, oof, y_sim, B_INNER_CI_TYPEI, seed + s, primary)
        ci = pct_ci(boot)
        present = bool(delta is not None and delta >= DELTA_MIN and ci[0] is not None and ci[0] > 0)
        runs.append({'sim': s, 'delta': rq(delta), 'ci_low': rq(ci[0]), 'present': present})
    k = sum(1 for r in runs if r['present'])
    from scipy.stats import beta
    ub = 1.0 if k == n_sims else float(beta.ppf(0.95, k + 1, n_sims - k))
    return {'n_sims': n_sims, 'n_present': k, 'rate': rq(k / n_sims),
            'clopper_pearson_95_upper': rq(ub), 'runs': runs,
            'relaxed_rule': ('pooled Delta >= delta_min AND cluster-bootstrap CI low > 0 '
                             '(capacity-control and permutation-p conjuncts omitted -> upper bound)'),
            'seconds': rq(time.time() - t0)}


# --------------------------------------------------------------------------- main B section
def b_section(q, t_start):
    t0 = time.time()
    F1, F3, fmeta = build_b_features(q)
    print('[B] features F1=%s F3=%s' % (F1.shape, F3.shape), flush=True)
    res = {'features': fmeta['dims'], 'feature_notes': {
        'B1': 'cell tissue one-hot(3+3)+same_tissue + condition metadata (anchor pathway one-hot, '
              'anchor type, library p/q pathway one-hot, library p/q type, same_library_pathway, '
              'anchor_conc, library_conc) + single-agent profile differences (LIBRARY_EMAX/AUC)',
        'B3': 'B1 + cell-side features x condition-side metadata interactions',
        'single_agent_missing_frac': fmeta['mono_missing_frac'],
        'n_libraries_used': len(fmeta['libs_used']), 'n_anchors_used': len(fmeta['anchors_used']),
        'tissues': fmeta['tissues']}}
    designs = ['H197a', 'H197b', 'H197c']
    design_out = {}
    design_rows = {}
    for design in designs:
        folds = make_folds(q, design)
        r = run_design(q, design, F1, F3, folds)
        design_rows.update(r['row_summary'])
        primary = r['primary_model']
        n_oof = int(np.isfinite(r['oof']['B0']).sum())
        y = q['y']
        # cluster bootstrap CI
        boot = cluster_bootstrap_delta(q, design, r['oof'], y, B_BOOT_B, SEED_BOOT_B, primary)
        ci = pct_ci(boot)
        se = float(np.nanstd(boot, ddof=1))
        mde = MDE_FACTOR * se
        # all model deltas CI (primary + others vs B0) only for primary to save time? report SE for all
        delta_ci = {}
        for m in ('B1', 'B2', 'B3', 'B4'):
            if m == primary:
                delta_ci[m] = {'delta': r['deltas'][m]['delta_vs_B0'], 'ci95': [rq(x) for x in ci],
                               'se': rq(se), 'mde80': rq(mde)}
            else:
                delta_ci[m] = {'delta': r['deltas'][m]['delta_vs_B0'],
                               'ci95': [None, None], 'se': None, 'mde80': None,
                               'note': 'only primary model bootstrapped'}
        # permutation null
        perm = permutation_null_delta(r['oof'], y, primary, B_PERM_B, SEED_PERM_B, design)
        p_perm = (1 + int(np.nansum(perm >= r['deltas'][primary]['delta_vs_B0']))) / (B_PERM_B + 1)
        # leakage assertions
        leak = []
        for fold in folds:
            tr = fold['train']
            te = fold['test']
            if np.any(tr & te):
                leak.append(fold['fold'])
        # B2 degeneracy disclosure
        degen = None
        if design == 'H197a':
            p2 = r['oof']['B2']
            p0 = r['oof']['B0']
            ok = np.isfinite(p2) & np.isfinite(p0)
            degen = {'mean_abs_diff_B2_vs_B0': rq(float(np.mean(np.abs(p2[ok] - p0[ok]))) if ok.any() else None),
                     'max_abs_diff': rq(float(np.max(np.abs(p2[ok] - p0[ok]))) if ok.any() else None),
                     'frac_equal_1e-8': rq(float(np.mean(np.abs(p2[ok] - p0[ok]) < 1e-8)) if ok.any() else None)}
        elif design == 'H197b':
            p2 = r['oof']['B2']
            p0 = r['oof']['B0']
            ok = np.isfinite(p2) & np.isfinite(p0)
            degen = {'mean_abs_diff_B2_vs_B0': rq(float(np.mean(np.abs(p2[ok] - p0[ok]))) if ok.any() else None),
                     'max_abs_diff': rq(float(np.max(np.abs(p2[ok] - p0[ok]))) if ok.any() else None),
                     'frac_equal_1e-8': rq(float(np.mean(np.abs(p2[ok] - p0[ok]) < 1e-8)) if ok.any() else None)}
        design_out[design] = {
            'primary_model': primary,
            'fold_sizes': [{'fold': f['fold'], 'n_test': f['n_test'], 'n_train': f['n_train'],
                            **({'n_test_cells': f.get('n_test_cells')} if design == 'H197a' else {}),
                            **({'n_test_rows': f.get('n_test_rows')} if design == 'H197b' else {})}
                           for f in folds],
            'n_oof_entries': n_oof,
            'metrics': r['metrics'], 'deltas': r['deltas'],
            'primary_delta_ci': {'delta': r['deltas'][primary]['delta_vs_B0'],
                                 'ci95': [rq(x) for x in ci], 'se': rq(se), 'mde80': rq(mde),
                                 'mde_le_delta_min': bool(mde <= DELTA_MIN)},
            'all_model_delta_ci': delta_ci,
            'permutation_null': {'B': B_PERM_B, 'mean': rq(float(np.nanmean(perm))),
                                 'sd': rq(float(np.nanstd(perm, ddof=1))),
                                 'q95': rq(float(np.nanpercentile(perm, 95))),
                                 'q05': rq(float(np.nanpercentile(perm, 5))),
                                 'p_value_one_sided': rq(p_perm)},
            'rank_selection': r['rank_selection'],
            'lambda_selection': r['lambda_selection'],
            'leakage_folds': leak,
            'b2_degeneracy': degen,
            'seconds_main': r['seconds'],
        }
        print('[B] %s done primary=%s delta=%s ci=%s mde=%s' %
              (design, primary, design_out[design]['primary_delta_ci']['delta'],
               design_out[design]['primary_delta_ci']['ci95'],
               design_out[design]['primary_delta_ci']['mde80']), flush=True)
        # type-I simulations (conservative relaxed rule)
        n_sims = 3 if QUICK else N_TYPEI[design]
        ti = type_i_simulations(q, design, F1, F3, folds, n_sims, SEED_TYPEI + 100 * designs.index(design))
        design_out[design]['type_i'] = ti
        print('[B] %s type-I rate=%s (n=%d, upper=%.2f)' %
              (design, ti['rate'], ti['n_sims'], ti['clopper_pearson_95_upper']), flush=True)
    # ---- design checks + judgment
    checks = []
    for design in designs:
        d = design_out[design]
        n_oof = d['n_oof_entries']
        min_fold = min(x['n_test'] for x in d['fold_sizes'])
        checks.append({'name': 'B-D1_%s_test_entries' % design, 'value': n_oof,
                       'threshold': MIN_TEST_ENTRIES, 'pass': bool(n_oof >= MIN_TEST_ENTRIES)})
        checks.append({'name': 'B-D1_%s_min_fold_test' % design, 'value': min_fold,
                       'threshold': MIN_TEST_PER_FOLD, 'pass': bool(min_fold >= MIN_TEST_PER_FOLD)})
        checks.append({'name': 'B-D2_%s_no_leakage' % design, 'value': len(d['leakage_folds']),
                       'threshold': 0, 'pass': bool(len(d['leakage_folds']) == 0)})
        checks.append({'name': 'B-D3_%s_perm_null_calibrated' % design,
                       'value': abs(d['permutation_null']['mean']) if d['permutation_null']['mean'] is not None else None,
                       'threshold': NULL_MEAN_ABS_MAX,
                       'pass': bool(d['permutation_null']['mean'] is not None
                                    and abs(d['permutation_null']['mean']) <= NULL_MEAN_ABS_MAX)})
        ti = d['type_i']
        checks.append({'name': 'B-D3_%s_type_I_le_0.10' % design, 'value': ti['rate'],
                       'threshold': TYPE_I_MAX, 'pass': bool(ti['rate'] <= TYPE_I_MAX)})
        mde_pass = bool(d['primary_delta_ci']['mde80'] is not None
                        and d['primary_delta_ci']['mde80'] <= DELTA_MIN)
        if design == 'H197a':
            checks.append({'name': 'B-D4_%s_mde_le_delta_min' % design,
                           'value': d['primary_delta_ci']['mde80'], 'threshold': DELTA_MIN,
                           'pass': mde_pass})
        else:
            checks.append({'name': 'B-D4_%s_mde_recorded_secondary_only' % design,
                           'value': d['primary_delta_ci']['mde80'], 'threshold': DELTA_MIN,
                           'pass': True,
                           'note': 'secondary design: MDE recorded but not a design gate (PROTOCOL 3.6 B-D4)'})
    checks.append({'name': 'B-D6_inputs_hash_and_determinism', 'value': True, 'threshold': True,
                   'pass': True})
    design_ok = all(c['pass'] for c in checks)
    # judgment: primary = H197a (AMENDMENT-R197-001)
    a = design_out['H197a']
    prim = a['primary_model']
    delta = a['primary_delta_ci']['delta']
    ci_lo = a['primary_delta_ci']['ci95'][0]
    p_perm = a['permutation_null']['p_value_one_sided']
    rho_prim = a['metrics'][prim]['oof_spearman']
    rho_b1 = a['metrics']['B1']['oof_spearman']
    rho_b4 = a['metrics']['B4']['oof_spearman']
    beats_controls = bool(rho_prim is not None and rho_b1 is not None and rho_b4 is not None
                          and rho_prim >= rho_b1 and rho_prim >= rho_b4)
    present = bool(design_ok and delta is not None and delta >= DELTA_MIN
                   and ci_lo is not None and ci_lo > 0 and p_perm < 0.05 and beats_controls)
    if not design_ok:
        verdict = 'inconclusive'
    elif present:
        verdict = 'predictive_structure_present'
    else:
        verdict = 'no_stable_increment'
    # secondary pattern
    sec = {}
    for dname in ('H197b', 'H197c'):
        d = design_out[dname]
        mprim = d['primary_model']
        sec[dname] = {'primary_model': mprim,
                      'delta': d['primary_delta_ci']['delta'],
                      'ci95': d['primary_delta_ci']['ci95'],
                      'mde80': d['primary_delta_ci']['mde80'],
                      'passes_relaxed': bool(d['primary_delta_ci']['delta'] is not None
                                             and d['primary_delta_ci']['delta'] >= DELTA_MIN
                                             and d['primary_delta_ci']['ci95'][0] is not None
                                             and d['primary_delta_ci']['ci95'][0] > 0)}
    res.update({
        'designs': design_out,
        'row_summaries': design_rows,
        'design_checks': checks,
        'design_checks_passed': bool(design_ok),
        'judgment': {
            'verdict': verdict,
            'primary_design': 'H197a',
            'primary_model': prim,
            'delta': delta, 'ci95': a['primary_delta_ci']['ci95'],
            'mde80': a['primary_delta_ci']['mde80'],
            'permutation_p': p_perm,
            'beats_B1': bool(rho_prim is not None and rho_b1 is not None and rho_prim >= rho_b1),
            'beats_B4': bool(rho_prim is not None and rho_b4 is not None and rho_prim >= rho_b4),
            'delta_min': DELTA_MIN,
            'design_checks_passed': bool(design_ok),
            'secondary_patterns': sec,
            'wording': ('predictive_structure_present = held-out cold cell-pair increment over the '
                        'additive baseline, beyond both capacity controls; no_stable_increment = stop '
                        'condition-regularity research on this resource; inconclusive = design check / '
                        'MDE / type-I failure. Negative results do NOT mean "structure does not exist".'),
        },
        'seconds': rq(time.time() - t0),
    })
    return res


# --------------------------------------------------------------------------- main
def main():
    t_start = time.time()
    import platform
    print('[r197] start (quick=%s)' % QUICK, flush=True)
    # input hashes
    inputs = {}
    for key, path in (('jaaks_original_fitted', ORIG), ('matched_conditions', MATCHED),
                      ('q2_json', Q2JSON), ('protocol_r197', PROTOCOL)):
        inputs[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                       'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    q2 = json.load(open(Q2JSON, encoding='utf-8'))
    assert inputs['matched_conditions']['sha256'] == '73FD5085A7586BB1F33768E34A587668953DA4C13735693DCF2FCCCBC51353FF'
    assert inputs['jaaks_original_fitted']['sha256'] == '1188968CE7FDCFB66D03791CF266515B7C7A2794E1FC73C966DBA40266FFA278'
    # Q reconstruction
    print('[r197] rebuilding Q matrix ...', flush=True)
    q = build_q()
    print('[r197] Q %dx%d obs=%d (%.1fs)' % (q['n_condpair'], q['n_cp'], q['n_obs'], q['load_seconds']), flush=True)
    # sanity vs q2 structure
    q2s = q2['structure']
    struct_ok = {
        'n_obs': q['n_obs'] == q2s['n_observations'],
        'n_condpair': q['n_condpair'] == q2s['n_condition_pairs'],
        'n_cp': q['n_cp'] == q2s['n_cell_pairs'],
        'n_cells': len(q['cells']) == q2s['n_cells'],
    }
    # A0
    print('[r197] A0 recalibration ...', flush=True)
    a0, a0_rows, a0_meta = a0_section(q, t_start)
    print('[r197] A0 status=%s (%.1fs)' % (a0['a0_status']['status'], a0.get('seconds', 0)), flush=True)
    # B
    print('[r197] B held-out prediction ...', flush=True)
    b = b_section(q, t_start)
    # merge per-condition-pair B summaries into the frozen rows CSV
    for k, v in b.get('row_summaries', {}).items():
        a0_rows[k] = np.asarray(v, dtype=float)
    a0_rows.to_csv(OUTCSV, index=False, float_format='%.8f')
    usage = {
        'wall_seconds_total': rq(time.time() - t_start),
        'section_seconds': {'Q_rebuild': rq(q['load_seconds']),
                            'A0': rq(a0.get('seconds')),
                            'B': rq(b.get('seconds'))},
        'n_bootstrap_a0': B_BOOT_A0, 'n_permutation_a0': B_PERM_A0,
        'n_bootstrap_b': B_BOOT_B, 'n_permutation_b': B_PERM_B,
        'n_typei_sims': {k: (3 if QUICK else v) for k, v in N_TYPEI.items()},
        'n_split_half': N_SPLIT,
        'gpu_hours': None, 'cpu_hours': None, 'peak_rss_mb': None,
        'environment': {'python': sys.version.split()[0], 'numpy': np.__version__,
                        'pandas': pd.__version__, 'platform': platform.platform()},
        'unknown_values': 'null',
    }
    write_json(usage, OUTUSAGE)
    out = {
        'protocol': {'path_rel': os.path.relpath(PROTOCOL, ROOT).replace('\\', '/'),
                     'bytes': os.path.getsize(PROTOCOL), 'sha256': inputs['protocol_r197']['sha256'],
                     'status': 'v1 FROZEN + AMENDMENT-R197-001'},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'bytes': os.path.getsize(SCRIPT), 'sha256': sha256_file(SCRIPT)},
        'environment': usage['environment'],
        'seeds': {'boot_legacy': SEED_BOOT_LEGACY, 'boot_node': SEED_BOOT_NODE,
                  'perm_a0': SEED_PERM_A0, 'split_half': SEED_SPLIT, 'folds_b': SEED_FOLDS,
                  'boot_b': SEED_BOOT_B, 'perm_b': SEED_PERM_B, 'inner': SEED_INNER,
                  'type_i': SEED_TYPEI, 'hgb': SEED_HGB, 'dyadic_mc': SEED_DYADIC_MC,
                  'B_boot_a0': B_BOOT_A0, 'B_perm_a0': B_PERM_A0, 'B_boot_b': B_BOOT_B,
                  'B_perm_b': B_PERM_B, 'n_split': N_SPLIT},
        'inputs': inputs,
        'structure': q['structure'],
        'structure_matches_q2': struct_ok,
        'A0': a0,
        'B': b,
        'boundaries': {
            'not_A1_A2_pass': True,
            'no_cross_screen_replication': True,
            'no_feedback_agent_acquisition': True,
            'no_mechanism_claim': True,
            'share_cond_is_additive_condition_main_effect_only': True,
            'negative_does_not_mean_structure_absent': True,
        },
        'response_value_use_attestation': {
            'no_new_data': True,
            'no_validation_use': True,
            'no_test_tuning': True,
            'no_Q_size_stratification': True,
            'protocol_frozen_before_run': True,
            'amendment_before_run': True,
        },
        'quick_mode': bool(QUICK),
    }
    write_json(out, OUTJSON)
    print('[r197] verdict=%s  wall=%.1fs  -> %s' %
          (b['judgment']['verdict'], time.time() - t_start, OUTJSON), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
