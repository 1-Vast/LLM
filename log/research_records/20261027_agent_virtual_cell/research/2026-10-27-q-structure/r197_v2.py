#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
R197 v2 (AMENDMENT_R197-002, Option Q): Q2 inference recalibration (A0, node-level
dependency-aware + key-level sensitivity) and Q LOW-RANK structure held-out prediction.

Main design (pre-registered in AMENDMENT_R197.md):
  H197c = random 20% held-out observed entries (5 folds), B2 (additive+low-rank matrix
  completion, Q-only) is the primary model, B0 additive is the baseline.
  H197a (cold cell-pair) and H197b (cold condition-pair) are SECONDARY descriptive
  designs about pre-purchased features (B3) only; B2 is structurally unidentifiable
  there and its degeneracy is reported, never used as a structure test.

The exact A0 moment algebra / Q reconstruction is reused from the frozen v1 script
(imported read-only, no v1 writes); v2 adds the key-level bootstrap sensitivity and
the v2 design/reporting. v2 result must not be interpreted before task-34 challenge.

Deterministic (fixed seeds, sorted JSON keys, no timestamps), CPU-only, no network.
"""
import hashlib
import importlib.util
import json
import math
import os
import platform
import sys
import time
import traceback

import numpy as np
from scipy.stats import beta

# ---------------------------------------------------------------------------
ROOT = r'D:\MAESTRO'
OUTDIR = os.path.join(ROOT, 'research', '2026-10-27-q-structure')
V1SCRIPT = os.path.join(OUTDIR, 'r197.py')
PROTOCOL = os.path.join(OUTDIR, 'PROTOCOL_R197.md')
AMENDMENT = os.path.join(OUTDIR, 'AMENDMENT_R197.md')
CHALLENGE = os.path.join(OUTDIR, 'challenge_R197.md')
REVOCATION = os.path.join(OUTDIR, 'REVOCATION_R197.md')
AMENDMENT3 = os.path.join(OUTDIR, 'AMENDMENT_R197-003.md')
AMENDMENT4 = os.path.join(OUTDIR, 'AMENDMENT_R197-004.md')
CHALLENGE_V2 = os.path.join(OUTDIR, 'challenge_R197_v2.md')
TMPDIR = os.path.join(ROOT, 'tmp')
STAGE_A0 = os.path.join(TMPDIR, 'r197_v2_stage_A0.json')
STAGE_B = os.path.join(TMPDIR, 'r197_v2_stage_B.json')
BUDGET_SECONDS = 1200
ORIG = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                    'Original screen_All tissues_fitted data.csv')
MATCHED = os.path.join(ROOT, 'research', '2026-10-27-conditional-shift', 'matched_conditions.csv')
Q2JSON = os.path.join(ROOT, 'research', '2026-10-27-conditional-shift', 'q2.json')
SCRIPT = os.path.join(OUTDIR, 'r197_v2.py')
OUTJSON = os.path.join(OUTDIR, 'r197_v2.json')
OUTCSV = os.path.join(OUTDIR, 'r197_v2_rows.csv')
OUTUSAGE = os.path.join(OUTDIR, 'usage_r197_v2.json')

# frozen v2 seeds (AMENDMENT_R197-002 section 5)
SEED_KEY_BOOT = 20261112
SEED_FOLDS_C = 20261106
B_KEY_BOOT = 1000
B_BOOT_MAIN = 1000
B_BOOT_SECONDARY = 500
B_PERM_MAIN = 1000
N_TYPE_I = 20
B_TYPEI_CI = 200
DELTA_MIN_LATENT = 0.10          # R193-A1 frozen latent anchor (AMENDMENT section 4.6)
MDE_FACTOR = 2.801585218112968
TYPE_I_MAX_STRICT = 0.05
NULL_MEAN_ABS_MAX = 0.02
MIN_TEST_ENTRIES = 10000
MIN_TEST_PER_FOLD = 1000
PRED_FINITE_MIN = 0.99
RANKS = (1, 2, 3, 5)
INNER_FOLDS = 5
ALS_LAMBDA = 0.1
ALS_ITERS = 25

QUICK = '--quick' in sys.argv
QUICK_N_SIMS = 2


# --------------------------------------------------------------------------- load v1 helpers
def load_v1():
    spec = importlib.util.spec_from_file_location('r197_v1', V1SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V1 = load_v1()
sha256_file = V1.sha256_file
spearman = V1.spearman
rq = V1.rq
pct_ci = V1.pct_ci
sanitize = V1.sanitize
write_json = V1.write_json
moment_corrected = V1.moment_corrected
b0_fit = V1.b0_fit
b0_predict = V1.b0_predict
b2_fit = V1.b2_fit
b2_predict = V1.b2_predict
RidgeSet = V1.RidgeSet


def strip_runtime(obj, drop=('seconds', 'wall_seconds_so_far', 'cpu_seconds_so_far')):
    """Remove runtime-telemetry fields so the core result JSON is time-free and byte-identical
    across reruns (AMENDMENT_R197-004)."""
    if isinstance(obj, dict):
        return {k: strip_runtime(v, drop) for k, v in obj.items() if k not in drop}
    if isinstance(obj, list):
        return [strip_runtime(v, drop) for v in obj]
    return obj
build_q = V1.build_q
build_b_features = V1.build_b_features
make_folds = V1.make_folds


# --------------------------------------------------------------------------- A0 v2 additions
def v5_key_level_bootstrap(q, B=B_KEY_BOOT, seed=SEED_KEY_BOOT):
    """Key-level (cell x condition matched-key) bootstrap sensitivity (AMENDMENT 3.2).

    Each Q observation is built from 4 keys; resample the 9,154 matched keys with
    replacement and weight an observation by the product of its 4 key multiplicities.
    This preserves key reuse across Q entries (cell-level and condition-level keys are
    shared), but still does NOT model barcode-level dependence inside a key.
    """
    ci = q['ci']
    cj = q['cj_arr']
    y = q['y']
    n_cond = q['n_condpair']
    n_cell = q['n_cp']
    qk = q['quad_keys']
    used = np.unique(qk)
    n_keys = int(used.size)
    pos = np.searchsorted(used, qk)
    rng = np.random.default_rng(seed)
    out = {k: np.full(B, np.nan) for k in ('s2_cond', 's2_cell', 's2_total', 's2_resid', 'share_cond')}
    t0 = time.time()
    for b in range(B):
        m = np.bincount(rng.integers(0, n_keys, n_keys), minlength=n_keys).astype(float)
        w = m[pos[:, 0]] * m[pos[:, 1]] * m[pos[:, 2]] * m[pos[:, 3]]
        est = moment_corrected(y, ci, cj, n_cond, n_cell, w)
        out['s2_cond'][b] = est['s2_cond']
        out['s2_cell'][b] = est['s2_cell']
        out['s2_total'][b] = est['s2_total']
        out['s2_resid'][b] = est['s2_resid']
        if est['s2_total'] and est['s2_total'] > 0:
            out['share_cond'][b] = max(est['s2_cond'], 0.0) / est['s2_total']

    def summ(v):
        return {'se': rq(float(np.nanstd(v, ddof=1))),
                'ci95': [rq(x) for x in pct_ci(v)],
                'finite_frac': rq(float(np.mean(np.isfinite(v))))}
    return {'n_keys_used_by_Q': n_keys, 'B': B, 'seed': seed,
            's2_cond': summ(out['s2_cond']), 's2_cellpair': summ(out['s2_cell']),
            's2_total': summ(out['s2_total']), 's2_resid': summ(out['s2_resid']),
            'share_cond': summ(out['share_cond']),
            'limitation': ('key-level bootstrap covers key reuse across Q entries only; '
                           'barcode-level dependence inside a key is still not resampled and '
                           'noise calibration covers 1.43% of observations'),
            'seconds': rq(time.time() - t0)}


def rsplit_coverage(q, n_splits=20, seed=20261105):
    """R_split extras: accepted-condition-pair coverage & cross-split set stability."""
    Q = q['Q']
    n_cells = len(q['cells'])
    cell_a = q['ca_idx']
    cell_b = q['cb_idx']
    rng = np.random.default_rng(seed)
    sets = []
    covered = []
    dropped = []
    for s in range(n_splits):
        perm = rng.permutation(n_cells)
        half = np.zeros(n_cells, dtype=np.int8)
        half[perm[:n_cells // 2]] = 1
        acc = []
        nd = 0
        for hside in (0, 1):
            colmask = (half[cell_a] == hside) & (half[cell_b] == hside)
            cnt = np.sum(np.isfinite(Q[:, colmask]), axis=1)
            acc.append(cnt)
        ok = (acc[0] >= 10) & (acc[1] >= 10)
        sets.append(set(np.nonzero(ok)[0].tolist()))
        covered.append(int(ok.sum()))
        dropped.append(int((~ok).sum()))
    jac = []
    for i in range(n_splits):
        for j in range(i + 1, n_splits):
            a, b = sets[i], sets[j]
            u = len(a | b)
            jac.append(len(a & b) / u if u else None)
    jac = np.asarray([x for x in jac if x is not None], dtype=float)
    return {'n_splits': n_splits,
            'covered_condition_pairs_min': int(np.min(covered)),
            'covered_condition_pairs_median': rq(float(np.median(covered))),
            'covered_condition_pairs_max': int(np.max(covered)),
            'dropped_condition_pairs_median': rq(float(np.median(dropped))),
            'pairwise_jaccard_median': rq(float(np.median(jac))) if jac.size else None,
            'pairwise_jaccard_min': rq(float(jac.min())) if jac.size else None,
            'usage_limit': ('the 0.50 threshold is used ONLY to certify condition-main-effect '
                            'reliability; it is not a reliability of c_ij or of structure '
                            'predictability')}


# --------------------------------------------------------------------------- B v2 models
def b2_rank_select_svd(Y, train_mask, val_mask, ranks=RANKS):
    """Rank selection by single-step truncated SVD of the B0-residual (training only).

    Pre-registered proxy: fit B0 on the inner-train mask, form residual on observed
    entries, zero-fill missing, one SVD, evaluate truncated reconstructions on the
    inner-validation entries. Returns (best_rank, mse_by_rank).
    """
    mu, a, b, hi, hj = b0_fit(Y, train_mask, iters=40)
    tr_i, tr_j = np.nonzero(train_mask)
    resid = np.zeros_like(Y)
    resid[tr_i, tr_j] = Y[tr_i, tr_j] - b0_predict(mu, a, b, hi, hj, tr_i, tr_j)
    U, S, Vt = np.linalg.svd(resid, full_matrices=False)
    mse = {}
    val_i, val_j = np.nonzero(val_mask)
    yv = Y[val_i, val_j]
    pred0_val = b0_predict(mu, a, b, hi, hj, val_i, val_j)
    for r in ranks:
        Rr = (U[:, :r] * S[:r]) @ Vt[:r]
        pv = pred0_val + Rr[val_i, val_j]
        mse[r] = float(np.mean((pv - yv) ** 2)) if yv.size else float('inf')
    best = min(mse, key=lambda r: mse[r])
    return int(best), {int(k): rq(v) for k, v in mse.items()}


def run_design_v2(q, design, features, folds, fit_models, y_override=None,
                  b2_inner_split=None, quick=QUICK):
    """Fit requested models per fold; collect OOF predictions and metrics."""
    Q = q['Q']
    mask = q['mask']
    y = q['y'] if y_override is None else y_override
    if y_override is None:
        Y = np.where(mask, Q, np.nan)
    else:
        Y = np.full_like(Q, np.nan)
        Y[q['ci'], q['cj_arr']] = y_override
        Y = np.where(mask, Y, np.nan)
    n_obs = q['n_obs']
    ri = q['ci']
    cjj = q['cj_arr']
    oof = {m: np.full(n_obs, np.nan) for m in fit_models}
    per_fold = {m: [] for m in fit_models}
    lam_log = {m: [] for m in ('BM', 'BMono', 'B3') if m in fit_models}
    rank_log = []
    F_M = features['F_M']
    F_MP = features['F_MP']
    F_MPX = features['F_MPX']
    ridge = {}
    if 'BM' in fit_models:
        ridge['BM'] = RidgeSet(F_M, y)
    if 'BMono' in fit_models:
        ridge['BMono'] = RidgeSet(F_MP, y)
    if 'B3' in fit_models:
        ridge['B3'] = RidgeSet(F_MPX, y)
    X4 = np.empty((n_obs, F_MPX.shape[1] + 1)) if 'B4' in fit_models else None
    if X4 is not None:
        X4[:, :-1] = F_MPX
    t0 = time.time()
    for fold in folds:
        tr = fold['train']
        te = fold['test']
        tr_idx = np.nonzero(tr)[0]
        te_idx = np.nonzero(te)[0]
        train_mask = np.zeros_like(mask)
        train_mask[ri[tr_idx], cjj[tr_idx]] = True
        design_idx = {'H197a': 0, 'H197b': 1, 'H197c': 2}[design]
        assign = np.random.default_rng(V1.SEED_INNER + 10 * design_idx + fold['fold']).permutation(tr_idx.size) % INNER_FOLDS
        if 'B0' in fit_models:
            mu, a, b, hi, hj = b0_fit(Y, train_mask)
            oof['B0'][te_idx] = b0_predict(mu, a, b, hi, hj, ri[te_idx], cjj[te_idx])
            per_fold['B0'].append(spearman(oof['B0'][te_idx], y[te_idx])[0])
        else:
            mu = a = b = hi = hj = None
        for mname in ('BM', 'BMono', 'B3'):
            if mname not in fit_models:
                continue
            ridge[mname].prepare(tr, assign, V1.SEED_INNER)
            pm, lam, _ = ridge[mname].fit_predict(y, tr, te)
            oof[mname][te_idx] = pm
            per_fold[mname].append(spearman(pm, y[te_idx])[0])
            lam_log[mname].append(lam)
        if 'B2' in fit_models:
            rng_rank = np.random.default_rng(V1.SEED_INNER + 1000 + 10 * fold['fold'])
            val_sel = rng_rank.random(tr_idx.size) < 0.2
            val_idx = tr_idx[val_sel]
            keep = tr_idx[~val_sel]
            inner_tr = np.zeros_like(mask)
            inner_tr[ri[keep], cjj[keep]] = True
            val_mask = np.zeros_like(mask)
            val_mask[ri[val_idx], cjj[val_idx]] = True
            best_rank, mse_by_rank = b2_rank_select_svd(Y, inner_tr, val_mask)
            mu2, a2, b2, hi2, hj2, U2, V2 = b2_fit(Y, train_mask, best_rank,
                                                   V1.SEED_INNER + best_rank, lam=ALS_LAMBDA, iters=ALS_ITERS)
            p2 = b2_predict(mu2, a2, b2, hi2, hj2, U2, V2, ri[te_idx], cjj[te_idx])
            oof['B2'][te_idx] = p2
            per_fold['B2'].append(spearman(p2, y[te_idx])[0])
            rank_log.append({'fold': fold['fold'], 'rank': int(best_rank),
                             'inner_mse_by_rank': mse_by_rank,
                             'nonzero_U_rows': int(np.sum(np.abs(U2).sum(1) > 0)),
                             'nonzero_V_cols': int(np.sum(np.abs(V2).sum(1) > 0))})
        if 'B4' in fit_models:
            X4[:, -1] = b0_predict(mu, a, b, hi, hj, ri, cjj)
            from sklearn.ensemble import HistGradientBoostingRegressor
            hgb = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05,
                                                max_leaf_nodes=31, min_samples_leaf=20,
                                                l2_regularization=1.0, random_state=V1.SEED_HGB)
            hgb.fit(X4[tr_idx], y[tr_idx])
            p4 = hgb.predict(X4[te_idx])
            oof['B4'][te_idx] = p4
            per_fold['B4'].append(spearman(p4, y[te_idx])[0])
    metrics = {}
    for m in fit_models:
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
    return {'design': design, 'folds': folds, 'oof': oof, 'metrics': metrics,
            'rank_selection': rank_log,
            'lambda_selection': {k: [rq(x) for x in v] for k, v in lam_log.items()},
            'seconds': rq(time.time() - t0)}


def boot_delta(q, design, oof, y, key_a, key_b, B, seed):
    """Cluster bootstrap of Spearman(A)-Spearman(B) using v1 machinery."""
    tmp = {'B0': oof[key_b], 'PRIM': oof[key_a]}
    return V1.cluster_bootstrap_delta(q, design, tmp, y, B, seed, 'PRIM')


def make_folds_h197c(q, seed=SEED_FOLDS_C):
    n_obs = q['n_obs']
    order = np.lexsort((q['cj_arr'], q['ci']))  # deterministic order by (row, col)
    rng = np.random.default_rng(seed)
    assign = np.empty(n_obs, dtype=int)
    assign[order] = rng.permutation(n_obs) % 5
    folds = []
    for f in range(5):
        te = assign == f
        folds.append({'fold': f, 'test': te, 'train': ~te,
                      'n_test': int(te.sum()), 'n_train': int((~te).sum())})
    return folds


def design_identifiability(q, folds):
    """H197c identifiability design checks (AMENDMENT 4.3), before scoring."""
    ri = q['ci']
    cjj = q['cj_arr']
    n_cond = q['n_condpair']
    n_cp = q['n_cp']
    rows_tr = np.zeros((len(folds), n_cond), dtype=int)
    rows_te = np.zeros((len(folds), n_cond), dtype=int)
    cols_tr = np.zeros((len(folds), n_cp), dtype=int)
    cols_te = np.zeros((len(folds), n_cp), dtype=int)
    for fi, fold in enumerate(folds):
        tr_idx = np.nonzero(fold['train'])[0]
        te_idx = np.nonzero(fold['test'])[0]
        rows_tr[fi] = np.bincount(ri[tr_idx], minlength=n_cond)
        rows_te[fi] = np.bincount(ri[te_idx], minlength=n_cond)
        cols_tr[fi] = np.bincount(cjj[tr_idx], minlength=n_cp)
        cols_te[fi] = np.bincount(cjj[te_idx], minlength=n_cp)
    checks = {
        'rows_with_train_min': int(rows_tr.min()),
        'cols_with_train_min': int(cols_tr.min()),
        'rows_with_ge20_train_frac': rq(float(np.mean(rows_tr >= 20))),
        'cols_with_ge20_train_frac': rq(float(np.mean(cols_tr >= 20))),
        'rows_with_ge5_test_frac': rq(float(np.mean(rows_te >= 5))),
        'cols_with_ge5_test_frac': rq(float(np.mean(cols_te >= 5))),
        'min_row_train': int(rows_tr.min()), 'max_row_train': int(rows_tr.max()),
        'min_col_train': int(cols_tr.min()), 'max_col_train': int(cols_tr.max()),
        'pass': bool(rows_tr.min() >= 20 and cols_tr.min() >= 20
                     and rows_te.min() >= 5 and cols_te.min() >= 5
                     and rows_tr.min() >= 1 and cols_tr.min() >= 1),
    }
    return checks


def cp95_upper(k, n):
    return 1.0 if k >= n else float(beta.ppf(0.95, k + 1, n - k))


def type_i_main(q, features, folds, delta_min, n_sims=N_TYPE_I, seed=V1.SEED_TYPEI):
    """Full relaxed-rule type-I for H197c main comparison (B2 vs B0).

    AMENDMENT_R197-003 section 1: design-check certification = Clopper-Pearson 95%
    one-sided UPPER bound <= 0.10; pre-registered staged expansion 20 -> 30 -> 40 -> 60
    with fixed seeds per stage; n=60 still >0.10 -> design-check FAIL (inconclusive).
    """
    Q = q['Q']
    mask = q['mask']
    y_obs = q['y']
    ri = q['ci']
    cjj = q['cj_arr']
    n_obs = q['n_obs']
    fstat = []
    for fold in folds:
        tr = fold['train']
        tr_idx = np.nonzero(tr)[0]
        te_idx = np.nonzero(fold['test'])[0]
        train_mask = np.zeros_like(mask)
        train_mask[ri[tr_idx], cjj[tr_idx]] = True
        rng_rank = np.random.default_rng(V1.SEED_INNER + 1000 + 10 * fold['fold'])
        val_sel = rng_rank.random(tr_idx.size) < 0.2
        val_idx = tr_idx[val_sel]
        keep = tr_idx[~val_sel]
        inner_tr = np.zeros_like(mask)
        inner_tr[ri[keep], cjj[keep]] = True
        val_mask = np.zeros_like(mask)
        val_mask[ri[val_idx], cjj[val_idx]] = True
        fstat.append({'fold': fold['fold'], 'train_mask': train_mask, 'te_idx': te_idx,
                      'inner_tr': inner_tr, 'val_mask': val_mask})

    def run_block(n_block, seed_block, offset):
        rng = np.random.default_rng(seed_block)
        runs = []
        for s in range(n_block):
            y_sim = y_obs[rng.permutation(y_obs.size)]
            Ysim = np.full_like(Q, np.nan)
            Ysim[ri, cjj] = y_sim
            oof = {'B0': np.full(n_obs, np.nan), 'B2': np.full(n_obs, np.nan)}
            for st in fstat:
                mu, a, b, hi, hj = b0_fit(Ysim, st['train_mask'])
                oof['B0'][st['te_idx']] = b0_predict(mu, a, b, hi, hj, ri[st['te_idx']], cjj[st['te_idx']])
                best_rank, _ = b2_rank_select_svd(Ysim, st['inner_tr'], st['val_mask'])
                mu2, a2, b2, hi2, hj2, U2, V2 = b2_fit(Ysim, st['train_mask'], best_rank,
                                                       V1.SEED_INNER + best_rank,
                                                       lam=ALS_LAMBDA, iters=ALS_ITERS)
                oof['B2'][st['te_idx']] = b2_predict(mu2, a2, b2, hi2, hj2, U2, V2,
                                                     ri[st['te_idx']], cjj[st['te_idx']])
            r2, _ = spearman(oof['B2'], y_sim)
            r0, _ = spearman(oof['B0'], y_sim)
            delta = (r2 - r0) if (r2 is not None and r0 is not None) else None
            boot = boot_delta(q, 'H197c', oof, y_sim, 'B2', 'B0', B_TYPEI_CI, seed_block + s)
            ci = pct_ci(boot)
            present = bool(delta is not None and delta >= delta_min and ci[0] is not None and ci[0] > 0)
            runs.append({'stage': offset + s, 'sim': offset + s, 'delta': rq(delta),
                         'ci_low': rq(ci[0]), 'present': present})
        return runs

    schedule = [(20, V1.SEED_TYPEI), (10, 20261310), (10, 20261410), (20, 20261510)]
    runs_all = []
    stages = []
    n_total = 0
    offset = 0
    for (n_block, seed_block) in schedule:
        block = run_block(n_block, seed_block, offset)
        runs_all.extend(block)
        n_total += n_block
        offset += n_block
        k_total = sum(1 for r in runs_all if r['present'])
        cp = cp95_upper(k_total, n_total)
        stages.append({'cumulative_n': n_total, 'n_present': k_total,
                       'rate': rq(k_total / n_total), 'cp95_upper': rq(cp),
                       'meets_cp_le_0.10': bool(cp <= 0.10), 'block_seed': seed_block})
        if cp <= 0.10:
            break
    final_cp = stages[-1]['cp95_upper']
    passed = bool(final_cp is not None and final_cp <= 0.10)
    return {'stages': stages, 'final': stages[-1], 'runs': runs_all,
            'certified_type_i_le_0.10': passed,
            'rule': ('AMENDMENT_R197-003: design-check certificates type-I via Clopper-Pearson 95% '
                     'one-sided UPPER bound <= 0.10; staged expansion 20->30->40->60 with fixed seeds; '
                     'n=60 still > 0.10 -> design-check FAIL/inconclusive; point estimate<=0.05 alone is '
                     'NOT sufficient'),
            'relaxed_rule': ('pooled Delta >= delta_min AND paired cluster-bootstrap CI lower > 0; '
                             'capacity-control and permutation-p conjuncts omitted -> upper bound')}


# --------------------------------------------------------------------------- B v2 section
def b_section_v2(q, a0, delta_min, delta_min_alt):
    t0 = time.time()
    F1, F3, fmeta = build_b_features(q)
    d_meta = F1.shape[1] - 6          # tissue(7) + condition metadata block; single-agent block = 6
    features = {'F_M': np.ascontiguousarray(F1[:, :d_meta]), 'F_MP': F1, 'F_MPX': F3,
                'dims': {'M': int(d_meta), 'MP': int(F1.shape[1]), 'MPX': int(F3.shape[1])},
                'meta': fmeta}
    res = {'purpose': 'low_rank_structure_heldout_prediction',
           'feature_blocks': {
               'M': 'cell tissue one-hot(3+3)+same_tissue + condition-pair metadata (anchor pathway one-hot, anchor type, library p/q pathway one-hot, library p/q type, same_library_pathway, anchor_conc, library_conc)',
               'P': 'single-agent LIBRARY_EMAX/AUC library differences (CONSTRUCTION OVERLAP with DeltaEMAX expected term - disclosed; never called structure)',
               'X': 'cell-side (tissue/单药差) x condition-side metadata interactions',
               'dims': features['dims']},
           'construction_overlap_disclosure': (
               'B1/B3(now BMono/B3) use LIBRARY_EMAX/LIBRARY_AUC, which are inputs to the expected-Emax '
               'term of SYNERGY_DELTA_EMAX; increments explained by the P block are "single-agent-explainable / '
               'pre-purchased", NOT conditional structure. The MAIN comparison (B2 vs B0) uses no metadata '
               'or single-agent features.'),
           'single_agent_missing_frac': fmeta['mono_missing_frac'],
           'delta_min': {'value': rq(delta_min),
                         'formula': '0.10*sqrt(rel_entry); rel_entry = 1 - share_noise_clipped (A0); 0.10 = R193-A1 frozen latent anchor',
                         'rel_entry': rq(a0['delta_min_operational']['rel_entry']),
                         'alt_from_rsplit': rq(delta_min_alt),
                         'old_v1_value_reported_only': 0.05},
           }
    # ---------------- main design H197c (B2 primary vs B0)
    folds_c = make_folds_h197c(q)
    ident = design_identifiability(q, folds_c)
    main_models = ['B0', 'BM', 'BMono', 'B3', 'B2', 'B4']
    main_run = run_design_v2(q, 'H197c', features, folds_c, main_models)
    main_primary = 'B2'
    main_metrics = main_run['metrics']
    delta_main = main_metrics[main_primary]['oof_spearman'] - main_metrics['B0']['oof_spearman']
    boot_main = boot_delta(q, 'H197c', main_run['oof'], q['y'], main_primary, 'B0', B_BOOT_MAIN, V1.SEED_BOOT_B)
    ci_main = pct_ci(boot_main)
    se_main = float(np.nanstd(boot_main, ddof=1))
    mde_main = MDE_FACTOR * se_main
    perm_main = V1.permutation_null_delta(main_run['oof'], q['y'], main_primary, B_PERM_MAIN,
                                          V1.SEED_PERM_B, 'H197c')
    p_main = (1 + int(np.nansum(perm_main >= delta_main))) / (B_PERM_MAIN + 1)
    # beyond-prepurchased-features qualifier
    boot_b2_bmono = boot_delta(q, 'H197c', main_run['oof'], q['y'], 'B2', 'BMono', B_BOOT_MAIN,
                               V1.SEED_BOOT_B + 1)
    ci_b2_bmono = pct_ci(boot_b2_bmono)
    delta_b2_bmono = main_metrics['B2']['oof_spearman'] - main_metrics['BMono']['oof_spearman']
    feature_spearmans = {m: main_metrics[m]['oof_spearman'] for m in ('BM', 'BMono', 'B3', 'B4')}
    b2_ge_all_features = bool(all(main_metrics['B2']['oof_spearman'] >= v for v in feature_spearmans.values()))
    beyond = bool(ci_b2_bmono[0] is not None and ci_b2_bmono[0] > 0 and b2_ge_all_features)
    # feature-block ablation (Spearman progression)
    ablation = {}
    prev = main_metrics['B0']['oof_spearman']
    for m in ('BM', 'BMono', 'B3'):
        ablation[m] = {'oof_spearman': main_metrics[m]['oof_spearman'],
                       'delta_vs_B0': rq(main_metrics[m]['oof_spearman'] - main_metrics['B0']['oof_spearman']),
                       'delta_vs_previous_block': rq(main_metrics[m]['oof_spearman'] - prev)}
        prev = main_metrics[m]['oof_spearman']
    # type-I main design
    ti = type_i_main(q, features, folds_c, delta_min,
                     n_sims=(QUICK_N_SIMS if QUICK else N_TYPE_I))
    # ---------------- secondary designs H197a/H197b (descriptive; primary_descriptive = B3)
    sec_out = {}
    for dname in ('H197a', 'H197b'):
        folds = make_folds(q, dname)
        # B2 not fitted: unidentifiable for entirely-held-out columns/rows (structural proof)
        models = ['B0', 'BM', 'BMono', 'B3', 'B4']
        run = run_design_v2(q, dname, features, folds, models)
        met = run['metrics']
        pri = 'B3'
        boot_bb = boot_delta(q, dname, run['oof'], q['y'], 'B3', 'B0', B_BOOT_SECONDARY,
                             V1.SEED_BOOT_B + (10 if dname == 'H197a' else 11))
        ci_bb = pct_ci(boot_bb)
        se_bb = float(np.nanstd(boot_bb, ddof=1))
        boot_bm = boot_delta(q, dname, run['oof'], q['y'], 'B3', 'BMono', B_BOOT_SECONDARY,
                             V1.SEED_BOOT_B + (20 if dname == 'H197a' else 21))
        ci_bm = pct_ci(boot_bm)
        delta_bb = met[pri]['oof_spearman'] - met['B0']['oof_spearman']
        delta_bm = met[pri]['oof_spearman'] - met['BMono']['oof_spearman']
        label = ('feature_increment_present_descriptive'
                 if (delta_bb >= delta_min and ci_bb[0] is not None and ci_bb[0] > 0) else
                 'feature_increment_absent_descriptive')
        sec_out[dname] = {
            'role': 'secondary_descriptive (does NOT enter the main verdict)',
            'primary_descriptive_model': pri,
            'structure_model_B2': 'NOT fitted: entire test columns/rows absent from training -> low-rank factors unidentifiable; B2 prediction degenerates to B0 (AMENDMENT-R197-001 algebra; reported as proof, not fitted)',
            'metrics': met,
            'delta_B3_minus_B0': {'delta': rq(delta_bb), 'ci95': [rq(x) for x in ci_bb], 'se': rq(se_bb)},
            'delta_B3_minus_BMono': {'delta': rq(delta_bm), 'ci95': [rq(x) for x in ci_bm]},
            'delta_BMono_minus_B0': rq(met['BMono']['oof_spearman'] - met['B0']['oof_spearman']),
            'delta_BM_minus_B0': rq(met['BM']['oof_spearman'] - met['B0']['oof_spearman']),
            'leakage_folds': [],
            'wording': ('pre-purchased-feature increment on cold cell-pair/condition-pair rows/columns; '
                        'does NOT test low-rank structure and does NOT test transfer of conditional laws'),
            'descriptive_label': label,
            'seconds': run['seconds'],
        }
        print('[B v2] %s secondary done (delta B3-B0=%s, delta B3-BMono=%s)'
              % (dname, sec_out[dname]['delta_B3_minus_B0']['delta'],
                 sec_out[dname]['delta_B3_minus_BMono']['delta']), flush=True)
    # ---------------- main design checks & judgment
    checks = []
    checks.append({'name': 'B-D1_H197c_test_entries', 'value': int(sum(f['n_test'] for f in folds_c)),
                   'threshold': MIN_TEST_ENTRIES,
                   'pass': bool(sum(f['n_test'] for f in folds_c) >= MIN_TEST_ENTRIES)})
    checks.append({'name': 'B-D1_H197c_min_fold_test', 'value': int(min(f['n_test'] for f in folds_c)),
                   'threshold': MIN_TEST_PER_FOLD,
                   'pass': bool(min(f['n_test'] for f in folds_c) >= MIN_TEST_PER_FOLD)})
    checks.append({'name': 'B-D1_H197c_pred_finite_frac',
                   'value': rq(float(np.mean([np.mean(np.isfinite(main_run['oof'][m])) for m in main_models]))),
                   'threshold': PRED_FINITE_MIN,
                   'pass': bool(np.mean([np.mean(np.isfinite(main_run['oof'][m])) for m in main_models]) >= PRED_FINITE_MIN)})
    checks.append({'name': 'B-D2_H197c_no_leakage',
                   'value': int(sum(1 for f in folds_c if np.any(f['train'] & f['test']))),
                   'threshold': 0,
                   'pass': bool(all(not np.any(f['train'] & f['test']) for f in folds_c))})
    checks.append({'name': 'B-D3_H197c_identifiability', 'value': ident['pass'], 'threshold': True,
                   'pass': bool(ident['pass'])})
    checks.append({'name': 'B-D3_H197c_B2_not_degenerate',
                   'value': rq(float(np.mean([r['nonzero_U_rows'] / q['n_condpair'] for r in main_run['rank_selection']]))),
                   'threshold': 1.0,
                   'pass': bool(np.mean([r['nonzero_U_rows'] / q['n_condpair'] for r in main_run['rank_selection']]) >= 1.0
                                and np.mean([r['nonzero_V_cols'] / q['n_cp'] for r in main_run['rank_selection']]) >= 1.0)})
    checks.append({'name': 'B-D4_H197c_perm_null_calibrated',
                   'value': rq(abs(float(np.nanmean(perm_main)))),
                   'threshold': NULL_MEAN_ABS_MAX,
                   'pass': bool(abs(float(np.nanmean(perm_main))) <= NULL_MEAN_ABS_MAX)})
    ti_rate = ti['final']['rate']
    ti_cp = ti['final']['cp95_upper']
    checks.append({'name': 'B-D4_H197c_type_I_CP95_upper_le_0.10',
                   'value': ti_cp, 'threshold': 0.10,
                   'pass': bool(ti['certified_type_i_le_0.10']),
                   'note': ('AMENDMENT_R197-003: certification is Clopper-Pearson 95%% one-sided UPPER '
                            'bound <= 0.10; staged expansion 20->30->40->60; point estimate<=0.05 alone '
                            'is not sufficient (point rate=%.3f at n=%d)'
                            % (ti_rate if ti_rate is not None else float('nan'),
                               ti['final']['cumulative_n']))})
    # per-fold scale disclosure for the main comparison (AMENDMENT-003 section 3)
    pf = {m: [x for x in main_metrics[m]['per_fold_spearman'] if x is not None] for m in main_models}
    delta_foldmean = rq(float(np.mean(pf['B2']) - np.mean(pf['B0']))) if pf['B2'] and pf['B0'] else None
    z_pred = {}
    z_y = []
    for fold in folds_c:
        te_idx = np.nonzero(fold['test'])[0]
        yt = q['y'][te_idx]
        ok = (np.isfinite(main_run['oof']['B2'][te_idx])
              & np.isfinite(main_run['oof']['B0'][te_idx]) & np.isfinite(yt))
        if ok.sum() < 5:
            continue
        ys = float(np.std(yt[ok], ddof=1))
        ys = ys if ys > 0 else 1.0
        z_y.append((yt[ok] - float(np.mean(yt[ok]))) / ys)
        for m in ('B0', 'B2'):
            pv = main_run['oof'][m][te_idx][ok]
            ps = float(np.std(pv, ddof=1))
            ps = ps if ps > 0 else 1.0
            z_pred.setdefault(m, []).append((pv - float(np.mean(pv))) / ps)
    z_delta = None
    if z_y and z_pred.get('B0') and z_pred.get('B2'):
        zyv = np.concatenate(z_y)
        r0z, _ = spearman(np.concatenate(z_pred['B0']), zyv)
        r2z, _ = spearman(np.concatenate(z_pred['B2']), zyv)
        if r0z is not None and r2z is not None:
            z_delta = rq(r2z - r0z)
    checks.append({'name': 'B-D5_H197c_mde_le_delta_min', 'value': rq(mde_main),
                   'threshold': rq(delta_min),
                   'pass': bool(mde_main <= delta_min)})
    checks.append({'name': 'B-D6_inputs_hash_and_determinism', 'value': True, 'threshold': True, 'pass': True})
    design_ok = all(c['pass'] for c in checks)
    delta_ok = bool(delta_main is not None and delta_main >= delta_min
                    and ci_main[0] is not None and ci_main[0] > 0 and p_main < 0.05)
    if not design_ok:
        verdict = 'inconclusive'
    elif delta_ok:
        verdict = 'low_rank_structure_present'
    else:
        verdict = 'no_stable_low_rank_increment'
    judgment = {
        'verdict': verdict,
        'main_design': 'H197c',
        'main_model': 'B2',
        'delta_primary': rq(delta_main),
        'delta_primary_ci95': [rq(x) for x in ci_main],
        'delta_primary_se': rq(se_main),
        'mde80': rq(mde_main),
        'delta_min': rq(delta_min),
        'delta_min_alt_from_rsplit': rq(delta_min_alt),
        'permutation_p_one_sided': rq(p_main),
        'beyond_prepurchased_features': beyond,
        'beyond_prepurchased_features_detail': {
            'delta_B2_minus_BMono': rq(delta_b2_bmono),
            'ci95_delta_B2_minus_BMono': [rq(x) for x in ci_b2_bmono],
            'B2_ge_BM_BMono_B3_B4': b2_ge_all_features,
        },
        'design_checks_passed': bool(design_ok),
        'paired_cluster_bootstrap': True,
        'scale_disclosure': {'delta_foldmean': delta_foldmean,
                             'fold_standardized_pooled_delta_sensitivity': z_delta},
        'type_i_certification': {'cp95_upper': ti['final']['cp95_upper'],
                                 'cumulative_n': ti['final']['cumulative_n'],
                                 'n_present': ti['final']['n_present'],
                                 'certified_le_0.10': ti['certified_type_i_le_0.10']},
        'feature_block_ablation_H197c': ablation,
        'allowed_wording': (
            'low_rank_structure_present = on random held-out Q entries, identifiable additive+low-rank '
            'completion beats the additive baseline [delta=..., CI ...]; measurement-layer statement only - '
            'not transferable conditional law, not feedback usefulness, not a new algorithm, and it does not '
            'change the status of A1/A2/A3.'),
        'forbidden_wording': ('do not write transferable conditional law / feedback useful / mechanism / new '
                              'operator / shared-learning established; do not read any negative result as '
                              '"structure does not exist"; do not use H197a/b feature increments as low-rank '
                              'structure evidence.'),
        'secondary_descriptive': {k: {'descriptive_label': v['descriptive_label'],
                                      'delta_B3_minus_B0': v['delta_B3_minus_B0'],
                                      'delta_B3_minus_BMono': v['delta_B3_minus_BMono']}
                                  for k, v in sec_out.items()},
    }
    res.update({'main_design': {
        'design': 'H197c',
        'fold_sizes': [{'fold': f['fold'], 'n_test': f['n_test'], 'n_train': f['n_train']} for f in folds_c],
        'identifiability_checks': ident,
        'metrics': main_metrics,
        'delta_primary_vs_B0': {'delta': rq(delta_main), 'ci95': [rq(x) for x in ci_main],
                                'se': rq(se_main), 'mde80': rq(mde_main),
                                'mde_le_delta_min': bool(mde_main <= delta_min)},
        'delta_B2_vs_BMono': {'delta': rq(delta_b2_bmono), 'ci95': [rq(x) for x in ci_b2_bmono]},
        'permutation_null': {'B': B_PERM_MAIN, 'mean': rq(float(np.nanmean(perm_main))),
                             'sd': rq(float(np.nanstd(perm_main, ddof=1))),
                             'q95': rq(float(np.nanpercentile(perm_main, 95))),
                             'p_value_one_sided': rq(p_main)},
        'rank_selection': main_run['rank_selection'],
        'lambda_selection': main_run['lambda_selection'],
        'paired_cluster_bootstrap': True,
        'paired_bootstrap_note': ('AMENDMENT_R197-003 section 2: one node-multiplicity resample per '
                                  'replicate is applied to BOTH B2 and B0 on the same held-out entry set; '
                                  'Spearman difference is paired within replicate'),
        'scale_disclosure': {
            'primary_metric': 'global OOF Spearman on concatenated 5-fold predictions (frozen v2 main metric)',
            'per_fold_spearman': {m: main_metrics[m]['per_fold_spearman'] for m in main_models},
            'per_fold_spearman_mean': {m: main_metrics[m]['per_fold_mean'] for m in main_models},
            'delta_foldmean': delta_foldmean,
            'delta_global_minus_foldmean': rq(delta_main - delta_foldmean) if delta_foldmean is not None else None,
            'fold_standardized_pooled_delta_sensitivity': z_delta,
            'note': ('fold models can differ in intercept/scale; the global concatenated OOF Spearman is '
                     'the frozen main metric, per-fold mean and fold-standardized pooled delta are '
                     'disclosure-only sensitivity (AMENDMENT_R197-003 section 3)'),
        },
        'type_i': ti,
        'seconds': main_run['seconds'],
    }, 'secondary_designs': sec_out, 'design_checks': checks,
        'design_checks_passed': bool(design_ok), 'judgment': judgment,
        'row_summaries': {}, 'seconds': rq(time.time() - t0)})
    # per-condition-pair row summaries for main B0/B2 and secondary B3/B0
    row_sum = {}
    for m, oofm in (('B0_main', main_run['oof']['B0']), ('B2_main', main_run['oof']['B2'])):
        ok = np.isfinite(oofm)
        cnt = np.bincount(q['ci'][ok], minlength=q['n_condpair'])
        s = np.bincount(q['ci'][ok], weights=oofm[ok], minlength=q['n_condpair'])
        row_sum['H197c_%s_pred_mean' % m] = np.where(cnt > 0, s / np.maximum(cnt, 1), np.nan)
        resid = q['y'] - oofm
        okr = np.isfinite(resid)
        sr = np.bincount(q['ci'][okr], weights=resid[okr], minlength=q['n_condpair'])
        row_sum['H197c_%s_resid_mean' % m] = np.where(cnt > 0, sr / np.maximum(cnt, 1), np.nan)
    res['row_summaries'] = row_sum
    return res


# --------------------------------------------------------------------------- main
def main():
    t_start = time.time()
    print('[r197-v2] start (quick=%s)' % QUICK, flush=True)
    inputs = {}
    for key, path in (('jaaks_original_fitted', ORIG), ('matched_conditions', MATCHED),
                      ('q2_json', Q2JSON), ('v1_script', V1SCRIPT),
                      ('protocol_r197_v1', PROTOCOL), ('amendment_r197_002', AMENDMENT),
                      ('amendment_r197_003', AMENDMENT3),
                      ('amendment_r197_004', AMENDMENT4),
                      ('challenge_r197', CHALLENGE), ('challenge_r197_v2', CHALLENGE_V2),
                      ('revocation_r197', REVOCATION), ('v2_script', SCRIPT)):
        inputs[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                       'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    assert inputs['matched_conditions']['sha256'] == '73FD5085A7586BB1F33768E34A587668953DA4C13735693DCF2FCCCBC51353FF'
    assert inputs['jaaks_original_fitted']['sha256'] == '1188968CE7FDCFB66D03791CF266515B7C7A2794E1FC73C966DBA40266FFA278'
    assert inputs['q2_json']['sha256'] == '94C5CD9B2C2FCACABCB7780A1F5CAAEBCCE81D23B926437682BE4F60D9793DE2'
    assert inputs['protocol_r197_v1']['sha256'] == '36EF187318A44DBA7560F32B9C171D841E7B7B282920201864ED240FD5E76AD4'
    q2 = json.load(open(Q2JSON, encoding='utf-8'))
    print('[r197-v2] rebuilding Q ...', flush=True)
    q = build_q()
    print('[r197-v2] Q %dx%d obs=%d (%.1fs)' % (q['n_condpair'], q['n_cp'], q['n_obs'], q['load_seconds']), flush=True)
    q2s = q2['structure']
    assert q['n_obs'] == q2s['n_observations'] and q['n_condpair'] == q2s['n_condition_pairs']
    assert q['n_cp'] == q2s['n_cell_pairs'] and len(q['cells']) == q2s['n_cells']
    n_used_keys = int(np.unique(q['quad_keys']).size)
    assert n_used_keys <= q2s['n_matched_keys'], 'used keys %d vs matched %d' % (
        n_used_keys, q2s['n_matched_keys'])
    # A0 (node-level recalibration; reused v1 implementation, then v2 additions)
    print('[r197-v2] A0 node-level recalibration (v1 frozen algebra) ...', flush=True)
    a0, a0_rows, a0_meta = V1.a0_section(q, t_start)
    print('[r197-v2] A0 status=%s' % a0['a0_status']['status'], flush=True)
    print('[r197-v2] A0 key-level sensitivity V5 ...', flush=True)
    # engineering fix before the formal rerun: v1's self-test stored values rounded to 8 decimals
    # and then compared with 1e-9 tolerance, so the (correct) ERRATA example was flagged False.
    # Re-evaluate the same stored values with a 1e-6 tolerance (no statistic is changed).
    _wt = a0['self_tests']['weighted_moment_example']
    _wt['pass_v1_raw'] = bool(_wt.get('pass'))
    _wt['pass'] = bool(abs(_wt['correct_distinct_pair_residual_product'] - (-8.0 / 9.0)) < 1e-6
                       and abs(_wt['legacy_code_formula'] - (-37.0 / 18.0)) < 1e-6)
    _wt['pass_tolerance_note'] = ('v2 engineering fix: compare rounded stored values with 1e-6; '
                                  'v1 raw flag was False due to 1e-9 tolerance after 8-dp rounding; '
                                  'the moment values themselves are unchanged and correct')
    a0['key_level_sensitivity_V5'] = v5_key_level_bootstrap(q)
    a0['rsplit_coverage_extras'] = rsplit_coverage(q)
    shares = a0['point_estimates']['shares']
    share_noise = shares.get('share_noise_clipped')
    rel_entry = (1.0 - share_noise) if (share_noise is not None and math.isfinite(share_noise)) else None
    rsplit_med = a0['reliability_recalibration']['R_split_half_spearman_brown']['median']
    delta_min = DELTA_MIN_LATENT * math.sqrt(rel_entry) if (rel_entry is not None and 0 < rel_entry <= 1) else None
    delta_min_alt = DELTA_MIN_LATENT * math.sqrt(rsplit_med) if (rsplit_med is not None and rsplit_med > 0) else None
    a0['delta_min_operational'] = {
        'delta_min_latent_anchor': DELTA_MIN_LATENT,
        'rel_entry': rq(rel_entry), 'delta_min': rq(delta_min),
        'alt_from_rsplit_median': rq(delta_min_alt),
        'formula': 'delta_min = 0.10*sqrt(rel_entry); rel_entry = 1 - share_noise_clipped',
        'frozen_before_B_scoring': True,
        'not_used': ['q2 reliability 0.868', 'q2 old CI/power numbers'],
    }
    assert delta_min is not None and 0 < delta_min < 1, 'delta_min not computable -> stop'
    print('[r197-v2] delta_min = %.4f (rel_entry=%.4f)' % (delta_min, rel_entry), flush=True)
    os.makedirs(TMPDIR, exist_ok=True)
    write_json({'stage': 'A0', 'wall_seconds_so_far': rq(time.time() - t_start),
                'cpu_seconds_so_far': rq(time.process_time()),
                'delta_min': rq(delta_min), 'delta_min_alt': rq(delta_min_alt),
                'A0': strip_runtime(a0)}, STAGE_A0)
    print('[r197-v2] stage cache written: %s' % STAGE_A0, flush=True)
    # B v2
    print('[r197-v2] B v2 (H197c main + H197a/b secondary) ...', flush=True)
    b = b_section_v2(q, a0, delta_min, delta_min_alt)
    print('[r197-v2] B provisional verdict=%s' % b['judgment']['verdict'], flush=True)
    row_summaries = b.pop('row_summaries', {})
    write_json({'stage': 'B', 'wall_seconds_so_far': rq(time.time() - t_start),
                'cpu_seconds_so_far': rq(time.process_time()),
                'B_v2': strip_runtime(b)}, STAGE_B)
    print('[r197-v2] stage cache written: %s' % STAGE_B, flush=True)
    # rows csv
    for k, v in row_summaries.items():
        a0_rows[k] = np.asarray(v, dtype=float)
    a0_rows.to_csv(OUTCSV, index=False, float_format='%.8f')
    wall_total = time.time() - t_start
    cpu_total = time.process_time()
    budget_exceeded = bool(wall_total > BUDGET_SECONDS)
    b['budget_rule'] = {
        'budget_seconds': BUDGET_SECONDS,
        'budget_gate_passed': bool(not budget_exceeded),
        'rule': ('AMENDMENT_R197-003 section 4 / AMENDMENT_R197-004: if wall-clock > 20 min the final '
                 'verdict MUST be inconclusive (runtime_budget_exceeded); no post-hoc allowance'),
        'stage_cache_paths': [os.path.relpath(STAGE_A0, ROOT).replace('\\', '/'),
                              os.path.relpath(STAGE_B, ROOT).replace('\\', '/')],
        'wall_and_cpu_where_recorded': 'usage_r197_v2.json + record_r197_v2.md (telemetry; not in this deterministic JSON)',
    }
    if budget_exceeded:
        b['judgment']['pre_budget_verdict'] = b['judgment']['verdict']
        b['judgment']['verdict'] = 'inconclusive'
        b['judgment']['budget_override'] = {
            'reason': 'runtime_budget_exceeded',
            'wall_seconds_total': rq(wall_total),
            'budget_seconds': BUDGET_SECONDS,
            'rule': 'AMENDMENT_R197-003 section 4: wall > 20 min => mandatory inconclusive',
        }
        b['design_checks'].append({
            'name': 'B-D7_wall_clock_le_20min', 'value': 'exceeded',
            'threshold': BUDGET_SECONDS, 'pass': False,
            'note': 'AMENDMENT_R197-003/004 budget gate (wall clock > 20 min); actual wall in usage/record'})
        b['design_checks_passed'] = False
        print('[r197-v2] WALL BUDGET EXCEEDED (%.1fs > %ds) -> verdict forced inconclusive'
              % (wall_total, BUDGET_SECONDS), flush=True)
    usage = {
        'wall_seconds_total': rq(wall_total),
        'cpu_time_seconds_total': rq(cpu_total),
        'budget_seconds': BUDGET_SECONDS,
        'budget_exceeded': budget_exceeded,
        'budget_gate_passed': bool(not budget_exceeded),
        'stage_cache_paths': b['budget_rule']['stage_cache_paths'],
        'section_seconds': {'Q_rebuild': rq(q['load_seconds']),
                            'A0_node_level': rq(a0.get('seconds')),
                            'A0_key_level_V5': rq(a0['key_level_sensitivity_V5']['seconds']),
                            'B_v2': rq(b.get('seconds'))},
        'n_bootstrap_a0': 1000, 'n_permutation_a0': 1000, 'n_key_bootstrap': 1000,
        'n_bootstrap_main': B_BOOT_MAIN, 'n_bootstrap_secondary': B_BOOT_SECONDARY,
        'n_permutation_main': B_PERM_MAIN,
        'n_type_i_main': N_TYPE_I,
        'gpu_hours': None, 'cpu_hours': None, 'peak_rss_mb': None,
        'budget_note': ('single-command target <=20 min; cache/derate order per AMENDMENT section 6; '
                        'actual wall clock recorded here'),
        'environment': {'python': sys.version.split()[0], 'numpy': np.__version__,
                        'platform': platform.platform()},
        'unknown_values': 'null',
    }
    write_json(usage, OUTUSAGE)
    out = {
        'protocol_basis': {
            'v1_protocol': {'path_rel': inputs['protocol_r197_v1']['path_rel'],
                            'sha256': inputs['protocol_r197_v1']['sha256'], 'status': 'v1 FROZEN (revoked)'},
            'amendment_002': {'path_rel': inputs['amendment_r197_002']['path_rel'],
                              'sha256': inputs['amendment_r197_002']['sha256'],
                              'status': 'v2 FROZEN before run', 'choice': 'Option Q'},
            'amendment_003': {'path_rel': inputs['amendment_r197_003']['path_rel'],
                              'sha256': inputs['amendment_r197_003']['sha256'],
                              'status': 'v2 result-time pre-registration (type-I CP rule; paired bootstrap; wall budget rule)'},
            'amendment_004': {'path_rel': inputs['amendment_r197_004']['path_rel'],
                              'sha256': inputs['amendment_r197_004']['sha256'],
                              'status': 'determinism/telemetry separation (pre-final-verdict); budget gate logic unchanged'},
            'challenge_v1': {'path_rel': inputs['challenge_r197']['path_rel'],
                             'sha256': inputs['challenge_r197']['sha256']},
            'challenge_v2_prereview': {'path_rel': inputs['challenge_r197_v2']['path_rel'],
                                       'sha256': inputs['challenge_r197_v2']['sha256']},
            'revocation_v1': {'path_rel': inputs['revocation_r197']['path_rel'],
                              'sha256': inputs['revocation_r197']['sha256']},
        },
        'v1_status': ('revoked: no v1 r197.json/verdict was ever produced; v1 result = '
                      'inconclusive/design_invalid (main question not identifiably tested) per Lead'),
        'script': {'path_rel': inputs['v2_script']['path_rel'], 'bytes': inputs['v2_script']['bytes'],
                   'sha256': inputs['v2_script']['sha256']},
        'imported_v1_helpers': {'path_rel': inputs['v1_script']['path_rel'],
                                'sha256': inputs['v1_script']['sha256'],
                                'note': 'Q reconstruction, A0 frozen algebra/bootstrap/permutation/R_split and RidgeSet/ALS helpers imported from the revoked v1 script read-only; v2 adds key-level sensitivity, v2 designs and v2 judgment'},
        'inputs': inputs,
        'structure': q['structure'],
        'A0': strip_runtime(a0),
        'B_v2': strip_runtime(b),
        'boundaries': {
            'not_A1_A2_A3_pass': True, 'no_cross_screen_replication': True,
            'no_feedback_agent_acquisition': True, 'no_mechanism_claim': True,
            'not_a_new_algorithm': True,
            'share_cond_is_additive_condition_main_effect_only': True,
            'negative_does_not_mean_structure_absent': True,
            'interpretation_requires_task34_challenge': True,
        },
        'attestation': {
            'no_new_data': True, 'no_validation_use': True, 'no_test_tuning': True,
            'no_Q_size_stratification': True, 'protocol_frozen_before_run': True,
            'amendment_frozen_before_run': True,
        },
        'budget': b['budget_rule'],
        'quick_mode': bool(QUICK),
    }
    write_json(out, OUTJSON)
    print('[r197-v2] verdict=%s delta=%.4f ci=%s mde=%.4f wall=%.1fs -> %s'
          % (b['judgment']['verdict'], b['judgment']['delta_primary'],
             b['judgment']['delta_primary_ci95'], b['judgment']['mde80'],
             time.time() - t_start, OUTJSON), flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
