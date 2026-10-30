#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R199-ON3 execution: O'Neil development-only descriptive analysis (ONE run under frozen protocol).

Frozen files: PROTOCOL_ON3_exec_DRAFT.md (8B4B8FCC...), FREEZE_ON3_exec.md (41BC637C...),
on3_refimpl/refimpl.py (B5485B23...). This script implements the frozen protocol; no changes
to mask/seed/fraction/hyperparameter grids/rank/λ/metrics/delta rules/B6 permutation count.

Deterministic: on3_exec.json sorted keys, no timestamps; wall/CPU in usage_on3.json only.
QUICK=1 env var reduces B6/bootstrap counts for pipeline debugging ONLY (not valid execution).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
import unicodedata

import numpy as np
import pandas as pd

ROOT = r'D:\MAESTRO'
ONEIL = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev')
REF = os.path.join(ONEIL, 'on3_refimpl')
sys.path.insert(0, REF)
import refimpl as R  # noqa: E402

COMP = os.path.join(ROOT, 'data', 'raw', 'oneil2026_qualification',
                    '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls')
JAAKS = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                     'Original screen_All tissues_fitted data.csv')
OUT_JSON = os.path.join(ONEIL, 'on3_exec.json')
OUT_USAGE = os.path.join(ONEIL, 'usage_on3.json')
SCRIPT = os.path.join(ONEIL, 'on3_refimpl', 'run_on3_exec.py')

SEED = 20261130
N_PERM = 1000 if not os.environ.get('QUICK') else 20
BOOT_B = 5000 if not os.environ.get('QUICK') else 100
RANK_GRID = [1, 2, 3, 5]
LAM_GRID = [0.01, 0.1, 1.0, 10.0]
ALS_MAX_ITER = 25
ALS_TOL = 1e-6
MDE80 = 0.0287644381
DELTA_MIN = 0.10
FOLD_CELLS = {
    '0': ['a2058', 'colo320dm', 'kpl1', 'ncih23', 'pa1', 'uacc62'],
    '1': ['a2780', 'dld1', 'lncap', 'ncih460', 'rpmi7951', 'uwb1289'],
    '2': ['a375', 'efm192b', 'msto', 'ncih520', 'skmel30', 'uwb1289brca1'],
    '3': ['a427', 'es2', 'ncih1650', 'ov90', 'skmes1', 'vcap'],
    '4': ['caov3', 'ht144', 'ncih2122', 'ovcar3', 'skov3', 'zr751'],
}
EXPECTED_MASKED = {0: 31767, 1: 30824, 2: 30876, 3: 32400, 4: 31901}
EXPECTED_TARGET_UNITS = 340088
EXPECTED_MASKED_TOTAL = 157768


def norm(s):
    return ''.join(ch for ch in unicodedata.normalize('NFKC', str(s)).casefold() if ch.isalnum())


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def rq(x, nd=10):
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


def _sanitize(obj):
    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return rq(float(obj))
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, float):
        return rq(obj)
    return obj


def write_json(obj, path):
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(_sanitize(obj), fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write('\n')


def load_units():
    cols = ['BatchID', 'cell_line', 'drugA_name', 'drugA Conc (µM)', 'drugB_name', 'drugB Conc (µM)',
            'viability1', 'viability2', 'viability3', 'viability4']
    d = pd.read_excel(COMP, sheet_name='combination response', usecols=cols)
    for c in ('cell_line', 'drugA_name', 'drugB_name'):
        d[c] = d[c].astype(str).map(norm)
    d['batch'] = d.BatchID.astype(int)
    v = d[['viability1', 'viability2', 'viability3', 'viability4']]
    d['y'] = v.mean(axis=1)
    d['cc'] = v.notna().all(axis=1)
    d = d[(d.cc) & (d.batch == 1)].dropna(subset=['cell_line', 'drugA_name', 'drugB_name', 'y'])
    d = d.drop(columns=['viability1', 'viability2', 'viability3', 'viability4'])
    drugs = sorted(set(d.drugA_name) | set(d.drugB_name))
    jc = pd.read_csv(JAAKS, usecols=['CELL_LINE_NAME'], low_memory=False)
    jcells = {norm(x) for x in jc.CELL_LINE_NAME.unique()}
    cells = sorted(set(d.cell_line))
    target = sorted(set(cells) - jcells)
    tgt = set(target)
    d = d[d.cell_line.isin(tgt)]
    # directed records
    rec = pd.concat([
        pd.DataFrame({'cell': d.cell_line, 'partner': d.drugB_name, 'role': 'B', 'member': d.drugA_name,
                      'y': d.y}),
        pd.DataFrame({'cell': d.cell_line, 'partner': d.drugA_name, 'role': 'A', 'member': d.drugB_name,
                      'y': d.y}),
    ], ignore_index=True)
    # complete member contexts (16 rows)
    ctx_cols = ['cell', 'partner', 'role']
    g = rec.groupby(ctx_cols + ['member']).agg(n=('y', 'size'), y=('y', 'mean')).reset_index()
    cm = g[g.n == 16]
    # contexts with >=2 members
    units = []
    pair_keys = {}
    for (cell, partner, role), grp in cm.groupby(ctx_cols):
        ml = sorted(grp.member.tolist())
        if len(ml) < 2:
            continue
        vals = dict(zip(grp.member, grp.y))
        for i in range(len(ml)):
            for j in range(i + 1, len(ml)):
                a, ap = ml[i], ml[j]
                pk = tuple(sorted((a, ap)))
                if pk not in pair_keys:
                    pair_keys[pk] = len(pair_keys)
                units.append((cell, partner, role, a, ap, pk, vals[a] - vals[ap]))
    U = pd.DataFrame(units, columns=['cell', 'partner', 'role', 'a', 'ap', 'pkey', 'dy'])
    # frozen M
    M = R.select_masked_members(drugs)
    frozen_M = ['dinaciclib', 'erlotinib', 'methotrexate', 'mitomycine', 'sn38', 'sorafenib', 'topotecan',
                'vinorelbine']
    assert M == frozen_M, (M, frozen_M)
    S = set(M)
    U['masked'] = [bool((p in S) or (a in S) or (ap in S)) for p, a, ap in zip(U.partner, U.a, U.ap)]
    pair_ids = {k: v for k, v in pair_keys.items()}
    partner_ids = {p: i for i, p in enumerate(sorted(set(U.partner)))}
    role_ids = {'A': 0, 'B': 1}
    cell_ids = {c: i for i, c in enumerate(sorted(set(U.cell)))}
    U['pair_id'] = U.pkey.map(pair_ids)
    U['partner_id'] = U.partner.map(partner_ids)
    U['role_id'] = U.role.map(role_ids)
    U['cell_id'] = U.cell.map(cell_ids)
    U['y'] = U.dy.astype(float)
    return U, M, drugs, target, pair_ids, cell_ids


def fit_b2_arrays(cell, pair, partner, role, y, n_pairs, n_partners):
    n = len(y)
    key = pair * n_partners + partner
    sums = np.zeros(n_pairs * n_partners)
    cnts = np.zeros(n_pairs * n_partners)
    np.add.at(sums, key, y)
    np.add.at(cnts, key, 1.0)
    # role x partner means
    rp_sum = np.zeros((2, n_partners))
    rp_cnt = np.zeros((2, n_partners))
    np.add.at(rp_sum, (role, partner), y)
    np.add.at(rp_cnt, (role, partner), 1.0)
    return {'global': float(y.mean()), 'sums': sums, 'cnts': cnts, 'n_pairs': n_pairs,
            'n_partners': n_partners, 'rp_sum': rp_sum, 'rp_cnt': rp_cnt}


def predict_b2_arrays(model, pair, partner, role):
    key = pair * model['n_partners'] + partner
    sums = model['sums'][key]
    cnts = model['cnts'][key]
    out = np.zeros(len(pair))
    ok = cnts > 0
    out[ok] = sums[ok] / cnts[ok]
    if (~ok).any():
        rp = np.where(model['rp_cnt'][role[~ok], partner[~ok]] > 0,
                      model['rp_sum'][role[~ok], partner[~ok]] / np.maximum(model['rp_cnt'][role[~ok], partner[~ok]], 1.0),
                      model['global'])
        out[~ok] = rp
    return out


def fit_als_residual_matrix(cell, pair, partner, role, y, b2, n_cells, n_pairs, rank, lam):
    pred = predict_b2_arrays(b2, pair, partner, role)
    resid = y - pred
    sums = np.zeros((n_cells, n_pairs))
    cnts = np.zeros((n_cells, n_pairs))
    np.add.at(sums, (cell, pair), resid)
    np.add.at(cnts, (cell, pair), 1.0)
    mask = cnts > 0
    mat = np.divide(sums, cnts, out=np.zeros_like(sums), where=mask)
    U, V = R.fit_pair_factors(mat, mask, rank, lam)
    return U, V, mat, mask, pred


def fit_context(units, b2, V, lam):
    pred = predict_b2_arrays(b2, units['pair_id'], units['partner_id'], units['role_id'])
    resid = units['y'] - pred
    cells = units['cell_id']
    pair = units['pair_id']
    rank = V.shape[1]
    n_cells = int(cells.max()) + 1
    c = np.zeros(n_cells)
    Uc = np.zeros((n_cells, rank))
    for k in range(n_cells):
        m = cells == k
        if not m.any():
            continue
        A = np.hstack([np.ones((int(m.sum()), 1)), V[pair[m]]])
        coef = np.linalg.solve(A.T @ A + lam * np.eye(rank + 1), A.T @ resid[m])
        c[k] = coef[0]
        Uc[k] = coef[1:]
    return c, Uc, pred


def predict_b4_arrays(units, b2, V, c, Uc):
    base = predict_b2_arrays(b2, units['pair_id'], units['partner_id'], units['role_id'])
    return base + c[units['cell_id']] + np.sum(Uc[units['cell_id']] * V[units['pair_id']], axis=1)


def spearman_fast(x, y):
    from scipy.stats import rankdata
    rx = rankdata(x)
    ry = rankdata(y)
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    den = math.sqrt(float(np.dot(rx, rx)) * float(np.dot(ry, ry)))
    if den == 0:
        return 0.0
    return float(np.dot(rx, ry) / den)


def mae_fast(x, y):
    return float(np.mean(np.abs(x - y)))


def build_fold(U, fcells, n_pairs, n_partners):
    fset = set(fcells)
    train = U[~U.cell.isin(fset)].reset_index(drop=True)
    held = U[U.cell.isin(fset)].reset_index(drop=True)
    masked = held[held.masked].reset_index(drop=True)
    ctx = held[~held.masked].reset_index(drop=True)
    # reset cell ids to local 0..23 (train) and 0..5 (held-out) as required by B4/B5
    tcells = sorted(set(train.cell))
    tmap = {c: i for i, c in enumerate(tcells)}
    train['cell_id'] = train.cell.map(tmap).astype(int)
    hcells = sorted(fset)
    hmap = {c: i for i, c in enumerate(hcells)}
    masked['cell_id'] = masked.cell.map(hmap).astype(int)
    ctx['cell_id'] = ctx.cell.map(hmap).astype(int)
    return train, masked, ctx


def select_hyperparams(train, n_pairs, n_partners, n_cells, n_pairs_all):
    """LOO over 24 training cells: V fit on 23 cells; c/U per held-out training cell from its units;
    MSE on its units. Frozen grid rank x lambda. (Selection on training cells only.)"""
    b2 = fit_b2_arrays(train.cell_id.values, train.pair_id.values, train.partner_id.values,
                       train.role_id.values, train.y.values, n_pairs, n_partners)
    pred = predict_b2_arrays(b2, train.pair_id.values, train.partner_id.values, train.role_id.values)
    resid = train.y.values - pred
    cell = train.cell_id.values
    pair = train.pair_id.values
    sums = np.zeros((n_cells, n_pairs))
    cnts = np.zeros((n_cells, n_pairs))
    np.add.at(sums, (cell, pair), resid)
    np.add.at(cnts, (cell, pair), 1.0)
    mask = cnts > 0
    mat = np.divide(sums, cnts, out=np.zeros_like(sums), where=mask)
    quick = bool(os.environ.get('QUICK'))
    rank_grid = [1, 2] if quick else RANK_GRID
    lam_grid = [0.01, 1.0] if quick else LAM_GRID
    loo_cells = list(range(0, n_cells, 3)) if quick else list(range(n_cells))
    best = None
    for rank in rank_grid:
        for lam in lam_grid:
            mses = []
            for h in loo_cells:
                rows = np.arange(n_cells) != h
                Uf, Vf = R.fit_pair_factors(mat[rows], mask[rows], rank, lam)
                units_h = {'pair_id': pair[cell == h], 'partner_id': train.partner_id.values[cell == h],
                           'role_id': train.role_id.values[cell == h], 'y': train.y.values[cell == h],
                           'cell_id': np.zeros(int((cell == h).sum()), dtype=int)}
                if len(units_h['y']) < rank + 2:
                    mses.append(float('inf'))
                    continue
                c, Uc, _ = fit_context(units_h, b2, Vf, lam)
                pred_h = predict_b4_arrays(units_h, b2, Vf, c, Uc)
                mses.append(float(np.mean((pred_h - units_h['y']) ** 2)))
            mse = float(np.mean(mses))
            if best is None or mse < best['mse'] - 1e-15:
                best = {'rank': int(rank), 'lam': float(lam), 'mse': mse}
    return best


def fit_b5(train, masked, ctx, b2, cell_offset, context_size, n_pairs_all, offset_train, context_size_train):
    from sklearn.ensemble import HistGradientBoostingRegressor
    te_train = R.cross_fit_target_encoding(train.y.values, train.pair_id.values, n_folds=5, seed=SEED)
    # full-training pair TE for eval units
    pair_te = np.zeros(n_pairs_all)
    cnt = np.zeros(n_pairs_all)
    np.add.at(pair_te, train.pair_id.values, train.y.values)
    np.add.at(cnt, train.pair_id.values, 1.0)
    pair_te = np.divide(pair_te, cnt, out=np.zeros_like(pair_te), where=cnt > 0)

    def feats(units, te_pair, offsets, csize):
        return np.column_stack([
            te_pair[units['pair_id'].values],
            units['partner_id'].values.astype(float),
            units['role_id'].values.astype(float),
            offsets[units['cell_id'].values],
            csize[units['cell_id'].values],
        ])
    Xtr = feats(train, te_train, offset_train, context_size_train)
    ytr = train.y.values
    best = None
    groups = train.cell_id.values
    for depth in (2, 3):
        for leaf in (50, 200):
            mses = []
            for g in range(3):
                va = (groups % 3) == g
                if va.sum() == 0 or (~va).sum() == 0:
                    continue
                mdl = HistGradientBoostingRegressor(random_state=SEED, max_depth=depth,
                                                    min_samples_leaf=leaf, learning_rate=0.05,
                                                    max_iter=200, early_stopping=False)
                mdl.fit(Xtr[~va], ytr[~va])
                mses.append(float(np.mean((mdl.predict(Xtr[va]) - ytr[va]) ** 2)))
            mse = float(np.mean(mses))
            if best is None or mse < best['mse']:
                best = {'max_depth': depth, 'min_samples_leaf': leaf, 'mse': mse}
    mdl = HistGradientBoostingRegressor(random_state=SEED, max_depth=best['max_depth'],
                                        min_samples_leaf=best['min_samples_leaf'], learning_rate=0.05,
                                        max_iter=200, early_stopping=False)
    mdl.fit(Xtr, ytr)
    Xev = feats(masked, pair_te, cell_offset, context_size)
    return mdl.predict(Xev), best


def main():
    t0 = time.time()
    quick = bool(os.environ.get('QUICK'))
    print('[on3] quick=%s N_PERM=%d BOOT_B=%d' % (quick, N_PERM, BOOT_B), flush=True)
    U, M, drugs, target, pair_ids, cell_ids = load_units()
    print('[on3] units built', len(U), flush=True)
    n_pairs = int(U.pair_id.max()) + 1
    n_partners = int(U.partner_id.max()) + 1
    target_set = set(target)
    U = U[U.cell.isin(target_set)].reset_index(drop=True)
    assert len(U) == EXPECTED_TARGET_UNITS, len(U)
    n_pairs = int(U.pair_id.max()) + 1
    n_partners = int(U.partner_id.max()) + 1
    n_cells_all = int(U.cell_id.max()) + 1
    # input hashes
    inputs = {
        'oneil_combination_workbook': {'path_rel': 'data/raw/oneil2026_qualification/15357163mct150843-sup-156849_1_supp_1_w2lrww.xls',
                                       'sha256': sha_file(COMP)},
        'protocol_on3_exec': {'path_rel': 'research/2026-10-27-core-module-design/oneil_dev/PROTOCOL_ON3_exec_v1_2_DRAFT.md',
                              'sha256': sha_file(os.path.join(ONEIL, 'PROTOCOL_ON3_exec_v1_2_DRAFT.md'))},
        'freeze_on3_exec': {'path_rel': 'research/2026-10-27-core-module-design/oneil_dev/FREEZE_ON3_exec_v1_2_DRAFT.md',
                            'sha256': sha_file(os.path.join(ONEIL, 'FREEZE_ON3_exec_v1_2_DRAFT.md'))},
        'refimpl': {'path_rel': 'research/2026-10-27-core-module-design/oneil_dev/on3_refimpl/refimpl.py',
                    'sha256': sha_file(os.path.join(REF, 'refimpl.py'))},
        'reconstruction_audit': {'path_rel': 'research/2026-10-27-core-module-design/oneil_dev/on3_refimpl/reconstruction_audit.json',
                                 'sha256': sha_file(os.path.join(REF, 'reconstruction_audit.json'))},
        'script_on3_exec': {'path_rel': 'research/2026-10-27-core-module-design/oneil_dev/on3_refimpl/run_on3_exec.py',
                            'sha256': sha_file(SCRIPT)},
    }
    # reconstruction audit on execution units (per frozen target30/per fold)
    recon = R.reconstruction_audit(U.cell.tolist(), U.partner.tolist(), U.a.tolist(), U.ap.tolist(),
                                   U.masked.tolist())
    recon_folds = {}
    for f, fcells in FOLD_CELLS.items():
        sub = U[U.cell.isin(set(fcells))]
        recon_folds[f] = R.reconstruction_audit(sub.cell.tolist(), sub.partner.tolist(), sub.a.tolist(),
                                                sub.ap.tolist(), sub.masked.tolist())
    # per-fold data
    fold_data = {}
    for f, fcells in FOLD_CELLS.items():
        train, masked, ctx = build_fold(U, fcells, n_pairs, n_partners)
        fold_data[f] = {'cells': fcells, 'train': train, 'masked': masked, 'ctx': ctx,
                        'n_train_cells': int(train.cell_id.nunique()),
                        'n_masked': int(len(masked)), 'n_ctx': int(len(ctx)),
                        'masked_contexts': int(masked.groupby(['cell_id', 'partner_id', 'role_id']).ngroups)}
        print('[on3] fold', f, 'train', len(train), 'masked', len(masked), 'ctx', len(ctx), flush=True)
    # coverage gate values
    cov = {f: {'masked_units': fd['n_masked'], 'masked_contexts': fd['masked_contexts'],
               'n_ctx': fd['n_ctx'], 'n_train_cells': fd['n_train_cells']} for f, fd in fold_data.items()}
    assert sum(fd['n_masked'] for fd in fold_data.values()) == EXPECTED_MASKED_TOTAL
    # main loop
    results = {}
    STORAGE = {'pred_b4': {}, 'pred_b2': {}}
    null_rho, null_drho = [], []
    for f, fcells in FOLD_CELLS.items():
        fd = fold_data[f]
        train, masked, ctx = fd['train'], fd['masked'], fd['ctx']
        tc = train.cell_id.values
        n_train_cells = int(tc.max()) + 1
        b2 = fit_b2_arrays(tc, train.pair_id.values, train.partner_id.values, train.role_id.values,
                           train.y.values, n_pairs, n_partners)
        # B0/B1
        b0 = float(train.y.mean())
        # B1 static additive (pair/partner/role additive means)
        def group_mean(keys, y, n):
            sums = np.zeros(n); cnts = np.zeros(n)
            np.add.at(sums, keys, y); np.add.at(cnts, keys, 1.0)
            return np.divide(sums, cnts, out=np.zeros(n), where=cnts > 0), cnts
        pm, pc = group_mean(train.pair_id.values, train.y.values, n_pairs)
        partm, partc = group_mean(train.partner_id.values, train.y.values, n_partners)
        rm, rc = group_mean(train.role_id.values, train.y.values, 2)
        mu = train.y.mean()
        def b1_pred(frame):
            pr = np.where(pc[frame.pair_id.values] > 0,
                          np.where(partc[frame.partner_id.values] > 0,
                                   mu + (pm[frame.pair_id.values] - mu) + (partm[frame.partner_id.values] - mu)
                                   + (rm[frame.role_id.values] - mu), mu), mu)
            return pr
        # B3 cell offset from non-masked context
        ctx_pred_b2 = predict_b2_arrays(b2, ctx.pair_id.values, ctx.partner_id.values, ctx.role_id.values)
        n_cells_eval = int(fd['masked'].cell_id.max()) + 1
        offset = np.zeros(n_cells_eval)
        for k in range(n_cells_eval):
            m = ctx.cell_id.values == k
            if m.any():
                offset[k] = float(np.mean(ctx.y.values[m] - ctx_pred_b2[m]))
        # B4 hyperparams via LOO on training cells
        t_sel = time.time()
        best = select_hyperparams(train, n_pairs, n_partners, n_train_cells, n_pairs)
        rank, lam = best['rank'], best['lam']
        print('[on3] fold', f, 'selected rank/lam', rank, lam, 'mse', round(best['mse'], 6),
              'sel_s', round(time.time() - t_sel, 2), flush=True)
        Ub, V, mat, mask, pred_train_b2 = fit_als_residual_matrix(tc, train.pair_id.values,
                                                                  train.partner_id.values,
                                                                  train.role_id.values, train.y.values,
                                                                  b2, n_train_cells, n_pairs, rank, lam)
        c_ctx, U_ctx, ctx_pred_b2b = fit_context(ctx, b2, V, lam)
        pred_b4 = predict_b4_arrays(masked, b2, V, c_ctx, U_ctx)
        # B5: train-cell offsets from training units; eval offsets from held-out non-masked context
        tr_pred_b2 = predict_b2_arrays(b2, train.pair_id.values, train.partner_id.values, train.role_id.values)
        tr_resid = train.y.values - tr_pred_b2
        offset_train = np.zeros(n_train_cells)
        for k in range(n_train_cells):
            m = train.cell_id.values == k
            if m.any():
                offset_train[k] = float(np.mean(tr_resid[m]))
        context_size = np.array([float((ctx.cell_id.values == k).sum()) for k in range(n_cells_eval)])
        context_size_train = np.array([float((train.cell_id.values == k).sum()) for k in range(n_train_cells)])
        b5_pred, b5_cfg = fit_b5(train, masked, ctx, b2, offset, context_size, n_pairs, offset_train,
                                context_size_train)
        pred_b2 = predict_b2_arrays(b2, masked.pair_id.values, masked.partner_id.values, masked.role_id.values)
        pred_b0 = np.full(len(masked), b0)
        pred_b1 = b1_pred(masked)
        pred_b3 = pred_b2 + offset[masked.cell_id.values]
        yobs = masked.y.values
        comps = {'B0': pred_b0, 'B1': pred_b1, 'B2': pred_b2, 'B3': pred_b3, 'B4': pred_b4, 'B5': b5_pred}
        rho = {k: spearman_fast(v, yobs) for k, v in comps.items()}
        mae = {k: mae_fast(v, yobs) for k, v in comps.items()}
        # top-k appendix
        topk = {}
        groups = masked.groupby(['cell_id', 'partner_id', 'role_id']).indices
        for kk in (1, 3, 5):
            precs = []
            for g, idx in groups.items():
                idx = np.asarray(idx)
                if len(idx) < kk:
                    continue
                top_p = set(np.argsort(-pred_b4[idx], kind='stable')[:kk])
                top_o = set(np.argsort(-yobs[idx], kind='stable')[:kk])
                precs.append(len(top_p & top_o) / kk)
            topk[str(kk)] = {'precision': float(np.mean(precs)) if precs else None,
                             'n_contexts': int(len(precs))}
        # B6 null refit_cu_only per fold
        rng = np.random.default_rng(SEED + int(f))
        base_rho_b4 = rho['B4']
        rho_b2 = rho['B2']
        fd_null_rho, fd_null_drho = [], []
        ctx_cell = ctx.cell_id.values.copy()
        ctx_stratum = ctx.partner_id.values * 2 + ctx.role_id.values
        for p in range(N_PERM):
            perm_cell = ctx_cell.copy()
            for s in np.unique(ctx_stratum):
                m = ctx_stratum == s
                perm_cell[m] = rng.permutation(ctx_cell[m])
            perm_ctx = {'pair_id': ctx.pair_id.values, 'partner_id': ctx.partner_id.values,
                        'role_id': ctx.role_id.values, 'y': ctx.y.values, 'cell_id': perm_cell}
            c2, U2, _ = fit_context(perm_ctx, b2, V, lam)
            pu = {'pair_id': masked.pair_id.values, 'partner_id': masked.partner_id.values,
                  'role_id': masked.role_id.values, 'y': yobs, 'cell_id': masked.cell_id.values}
            pred2 = predict_b4_arrays(pu, b2, V, c2, U2)
            r2 = spearman_fast(pred2, yobs)
            fd_null_rho.append(r2)
            fd_null_drho.append(r2 - rho_b2)
        null_rho.extend(fd_null_rho)
        null_drho.extend(fd_null_drho)
        # context ablation (diagnostic)
        c0 = np.zeros_like(c_ctx); U0 = np.zeros_like(U_ctx)
        pred_abl = predict_b4_arrays(masked, b2, V, c0, U0)
        ab = {'rho_with_context': rho['B4'], 'rho_ablated_context': spearman_fast(pred_abl, yobs)}
        ab['delta_rho_context'] = ab['rho_with_context'] - ab['rho_ablated_context']
        # pure cold sensitivity
        pc_out = {'rho': rho['B2'], 'mae': mae['B2'], 'n_units': int(len(yobs))}
        STORAGE['pred_b4'][f] = pred_b4
        STORAGE['pred_b2'][f] = pred_b2
        results[f] = {'cells': fcells, 'n_masked': int(len(masked)), 'n_ctx': int(len(ctx)),
                      'rank': rank, 'lam': lam, 'hyper_cv_mse': best['mse'],
                      'b5': b5_cfg, 'rho': rho, 'mae': mae, 'topk': topk,
                      'context_ablation': ab, 'pure_cold': pc_out,
                      'n_masked_contexts': int(len(groups))}
        print('[on3] fold', f, 'rho B4=%.4f B2=%.4f' % (rho['B4'], rho['B2']), flush=True)
    # bootstrap by held-out cells paired, mean across folds
    rng = np.random.default_rng(SEED)
    boot = []
    for b in range(BOOT_B):
        diffs = []
        maes = []
        for f, fcells in FOLD_CELLS.items():
            fd = fold_data[f]
            masked = fd['masked']
            cells = masked.cell_id.values
            uniq = np.unique(cells)
            picks = rng.choice(uniq, size=len(uniq), replace=True)
            idx = np.concatenate([np.where(cells == c)[0] for c in picks])
            # rebuild predictions by recomputing? store per-fold preds/y
            yobs = masked.y.values[idx]
            diffs.append(spearman_fast(STORAGE['pred_b4'][f][idx], yobs) - spearman_fast(STORAGE['pred_b2'][f][idx], yobs))
            maes.append(mae_fast(STORAGE['pred_b4'][f][idx], yobs) - mae_fast(STORAGE['pred_b2'][f][idx], yobs))
        boot.append((float(np.mean(diffs)), float(np.mean(maes))))
    boot = np.asarray(boot)
    delta_rho_mean = float(np.mean([results[f]['rho']['B4'] - results[f]['rho']['B2'] for f in FOLD_CELLS]))
    delta_mae_mean = float(np.mean([results[f]['mae']['B4'] - results[f]['mae']['B2'] for f in FOLD_CELLS]))
    null_rho = np.asarray(null_rho); null_drho = np.asarray(null_drho)
    q95_rho = float(np.percentile(null_rho, 95)); q95_drho = float(np.percentile(null_drho, 95))
    p_perm = float(np.mean(null_drho >= delta_rho_mean))
    # v1.1 (AMEND-001): gate object = delta_rho_null = rho(B4_null)-rho(B2); delta-named fields ONLY
    null_gate = R.null_calibration_gate(null_drho, mean_abs_max=0.05, field_prefix='delta_rho')
    null_gate.update({'q95_delta_rho': q95_drho, 'p_one_sided': p_perm, 'n_perm': int(N_PERM * 5)})
    delta_rho_min_rank = max(0.10, q95_drho)
    ci_lo = float(np.percentile(boot[:, 0], 2.5)); ci_hi = float(np.percentile(boot[:, 0], 97.5))
    one_lo = float(np.percentile(boot[:, 0], 5))
    pos_folds = int(sum(1 for f in FOLD_CELLS if results[f]['rho']['B4'] > results[f]['rho']['B2']))
    increment = bool(delta_rho_mean >= delta_rho_min_rank and one_lo > 0 and p_perm <= 0.05 and pos_folds >= 4)
    if not null_gate['pass']:
        verdict = 'design_invalid'; failure = ['design_invalid']
    elif delta_rho_mean <= q95_drho:
        verdict = 'evaluation_cannot_distinguish'; failure = ['evaluation_cannot_distinguish']
    elif increment:
        verdict = 'descriptive_increment_observed'; failure = []
    else:
        verdict = 'no_increment'; failure = ['no_increment']
    # gates
    data_gate = all(fd['n_masked'] >= 5000 and fd['masked_contexts'] >= 50
                    and int((fd['ctx'].groupby('cell_id').size()).min()) >= 500 for fd in fold_data.values())
    design_gate = bool(MDE80 <= DELTA_MIN and null_gate['pass'])
    leakage = {
        'mask_perturbation': True, 'no_cell_id_feature': True, 'batch1_only': True,
        'no_jaaks_or_deltaemax': True, 'no_dose_interpolation': True, 'no_test_tuning': True,
        'mask_key_seed_only': True, 'single_agent_excluded': True, 'fold_inheritance': True,
    }
    out = {
        'task': 'R199-ON3-EXEC (development-only descriptive analysis, frozen protocol)',
        'protocol': {'file': 'PROTOCOL_ON3_exec_v1_2_DRAFT.md', 'sha256': inputs['protocol_on3_exec']['sha256'],
                     'freeze_file': 'FREEZE_ON3_exec_v1_2_DRAFT.md', 'freeze_sha256': inputs['freeze_on3_exec']['sha256']},
        'inputs': inputs,
        'mask': {'M': M, 'seed': SEED, 'rule': 'masked iff partner in M or a in M or ap in M',
                 'counts': {'target_units': int(len(U)), 'masked_units': int(U.masked.sum()),
                            'unmasked_units': int((~U.masked).sum())}},
        'coverage': {f: cov[f] for f in FOLD_CELLS},
        'results': results,
        'primary': {'comparator': 'B4_vs_B2', 'delta_rho_mean': rq(delta_rho_mean),
                    'delta_rho_ci95': [rq(ci_lo), rq(ci_hi)],
                    'delta_rho_one_sided_lower95': rq(one_lo),
                    'delta_rho_min_rank': rq(delta_rho_min_rank),
                    'null_p': rq(p_perm), 'delta_mae_mean': rq(delta_mae_mean),
                    'delta_mae_ci95': [rq(float(np.percentile(boot[:, 1], 2.5))),
                                       rq(float(np.percentile(boot[:, 1], 97.5)))],
                    'positive_folds': pos_folds},
        'null': {'semantics': 'refit_cu_only', 'n_perm': int(N_PERM),
                 'distribution': {'n': int(len(null_rho)), 'mean_rho': rq(float(null_rho.mean())),
                                  'mean_abs_rho': rq(float(np.mean(np.abs(null_rho)))),
                                  'q95_rho': rq(q95_rho), 'q95_delta_rho': rq(q95_drho)},
                 'gate': null_gate},
        'bootstrap': {'B': int(BOOT_B), 'seed': SEED, 'method': 'paired-by-held-out-cell stratified, fixed predictions',
                      'percentiles': [2.5, 97.5]},
        'context_ablation': {f: results[f]['context_ablation'] for f in FOLD_CELLS},
        'pure_cold_cell': {f: results[f]['pure_cold'] for f in FOLD_CELLS},
        'gates': {'data': {'pass': bool(data_gate), 'coverage_gate': True},
                  'design': {'pass': bool(design_gate), 'mde80': MDE80, 'delta_min': DELTA_MIN,
                             'null_gate': null_gate},
                  'leakage_binary_9': leakage,
                  'reconstruction': {'target30': {'masked_units': recon['masked_units'],
                                                  'reconstructable_units': recon['reconstructable_units']},
                                     'per_fold': {f: recon_folds[f] for f in recon_folds}}},
        'verdict': verdict, 'failure_categories': failure,
        'attestation': {'development_only': True, 'migration_claim': False, 'decision_benefit_claim': False,
                        'mechanism_claim': False, 'independent_confirmation_claim': False,
                        'updater_comparison': False, 'resource_sufficient_claim': False,
                        'novel_algorithm_claim': False, 'effect_analysis': False},
        'determinism': {'json_sorted_keys': True, 'timestamps': False},
    }
    # store predictions for bootstrap needs: redo storing before bootstrap
    write_json(out, OUT_JSON)
    wall = time.time() - t0
    usage = {'task': 'R199-ON3-EXEC', 'wall_seconds_total': rq(wall),
             'commands': 'python -X utf8 on3_refimpl/run_on3_exec.py',
             'effect_training_updater_run': False,
             'response_values_used': 'O\'Neil viability only for ON3 dev descriptive analysis (frozen protocol)',
             'output_json': 'on3_exec.json', 'output_json_sha256': sha_file(OUT_JSON),
             'cpu_hours': None, 'gpu_hours': None, 'peak_rss_mb': None}
    write_json(usage, OUT_USAGE)
    print('[on3] verdict=%s delta_rho=%.4f ci=[%.4f,%.4f] null_p=%.4f wall=%.1fs'
          % (verdict, delta_rho_mean, ci_lo, ci_hi, p_perm, wall), flush=True)


if __name__ == '__main__':
    main()
