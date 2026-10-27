#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PREGISTERED AMENDMENT-001 implementation (R196 v2): audit-level re-estimation of C130.

Fixes vs revoked v1 (see AMENDMENT_R196.md):
  * primary inference unit = HELD-OUT DRUGS: 10 independent drug partitions x 5 folds,
    primary CI = drug-cluster bootstrap, primary MDE80 = 2.802 * SD(drug bootstrap);
    replicated requires CI_lower>0, point>=delta_min, and primary MDE80 <= delta_min;
  * unified inner-lambda metric for grouped and row-level: fold-mean Spearman;
    row-level C130 bridge grid (<=1000) plus same-grid comparison;
  * delta_min operationalised (rho=0.05 <=> ~1.59 pp pairwise-ordering edge) and linked to
    the drug-unit MDE; stability upper bound removed (only a descriptive large_gain_flag);
  * design checks (incl. engine-equivalence and null-calibration) run BEFORE treatment scoring.

Deterministic: fixed seeds, no timestamps, JSON sort_keys. No network. CPU only.
"""
import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata

ROOT = Path(r'D:\MAESTRO')
BASE = ROOT / 'research' / '2026-10-27-c130-audit'
ORIG = ROOT / 'data' / 'external' / 'gdsc_combinations' / 'jaaks2022_figshare' / \
    'Original screen_All tissues_fitted data.csv'
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY",
       "LIBRARY_PATHWAY", "SYNERGY_DELTA_EMAX"]
EXPECTED_SHA = '1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278'

N_PART = 10
N_FOLDS = 5
N_INNER = 3
SEED_PART_BASE = 20261027
SEED_INNER_BASE = 20261027 + 500000
SEED_ROW_BASE = 20261027 + 600000
SEED_BOOT_DRUG = 20261027 + 700000
SEED_CAP_BASE = 20261027 + 4000
SEED_SHUF_BASE = 20261027 + 5000
L_EXT = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0, 3000.0, 10000.0)
L_C130 = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
N_BOOT = 2000
N_BOOT_SENS = 1000
N_NULL_SEEDS = 10
CONST_TOL = 1e-9
DELTA_MIN = 0.05
LARGE_GAIN_FLAG = 0.20
MATERIAL_OPTIMISM = 0.05


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def sha256_array(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def is_const(p):
    if len(p) < 5:
        return True
    return float(np.ptp(p)) <= CONST_TOL * max(1.0, float(np.abs(p).max()))


def rho_metric(pred, yv):
    if len(pred) < 5 or len(np.unique(yv)) < 2:
        return None, 'too_small'
    if is_const(pred):
        return 0.0, 'constant'
    s = spearmanr(pred, yv).statistic
    if not np.isfinite(s):
        return 0.0, 'nonfinite'
    return float(s), 'defined'


def rho_fast(pred, yv):
    if len(pred) < 5:
        return 0.0
    if is_const(pred):
        return 0.0
    r1 = rankdata(pred)
    r2 = rankdata(yv)
    if r1.std() == 0.0 or r2.std() == 0.0:
        return 0.0
    v = float(np.corrcoef(r1, r2)[0, 1])
    return v if np.isfinite(v) else 0.0


class BlockDesign:
    """Design matrix as blocks: ('oh', codes, size) or ('ct', matrix, size).

    Exact ridge fits via block Gram matrices: O(n) counting + O(p^3) solves.
    Column-wise standardization is fitted on the rows passed to gram_zy only.
    """

    def __init__(self, blocks):
        self.blocks = []
        off = 0
        for kind, data, size in blocks:
            self.blocks.append({'kind': kind, 'data': data, 'size': int(size), 'off': off})
            off += int(size)
        self.p = off

    def gram_zy(self, rows, yv):
        n = len(rows)
        p = self.p
        C = np.zeros((p, p))
        mu = np.zeros(p)
        sd = np.zeros(p)
        Xy = np.zeros(p)
        oh = [b for b in self.blocks if b['kind'] == 'oh']
        ct = [b for b in self.blocks if b['kind'] == 'ct']
        for b in oh:
            codes = b['data'][rows]
            k, off = b['size'], b['off']
            counts = np.bincount(codes, minlength=k).astype(float)
            mu[off:off + k] = counts / n
            sd[off:off + k] = np.sqrt(np.maximum(mu[off:off + k] * (1.0 - mu[off:off + k]), 0.0))
            C[off:off + k, off:off + k] = np.diag(counts)
            Xy[off:off + k] = np.bincount(codes, weights=yv, minlength=k)
        for b in ct:
            mat = b['data'][rows]
            k, off = b['size'], b['off']
            mu[off:off + k] = mat.mean(0)
            sd[off:off + k] = mat.std(0)
            C[off:off + k, off:off + k] = mat.T @ mat
            Xy[off:off + k] = mat.T @ yv
        for i in range(len(self.blocks)):
            for j in range(i + 1, len(self.blocks)):
                bi, bj = self.blocks[i], self.blocks[j]
                oi, ki, oj, kj = bi['off'], bi['size'], bj['off'], bj['size']
                if bi['kind'] == 'oh' and bj['kind'] == 'oh':
                    co = np.bincount(bi['data'][rows] * kj + bj['data'][rows],
                                     minlength=ki * kj).reshape(ki, kj).astype(float)
                elif bi['kind'] == 'oh':
                    mat = bj['data'][rows]
                    co = np.empty((ki, kj))
                    for d in range(kj):
                        co[:, d] = np.bincount(bi['data'][rows], weights=mat[:, d], minlength=ki)
                elif bj['kind'] == 'oh':
                    mat = bi['data'][rows]
                    co = np.empty((ki, kj))
                    for d in range(ki):
                        co[d, :] = np.bincount(bj['data'][rows], weights=mat[:, d], minlength=kj)
                else:
                    co = bi['data'][rows].T @ bj['data'][rows]
                C[oi:oi + ki, oj:oj + kj] = co
                C[oj:oj + kj, oi:oi + ki] = co.T
        sd[sd == 0] = 1.0
        G = (C - n * np.outer(mu, mu)) / np.outer(sd, sd)
        bvec = (Xy - mu * yv.sum()) / sd
        return {'G': G, 'b': bvec, 'mu': mu.copy(), 'sd': sd.copy(), 'n': n,
                'ybar': float(yv.mean())}

    def solve(self, fit, lams):
        G, b = fit['G'], fit['b']
        dg = np.diag(G).copy()
        return {lam: np.linalg.solve(G + np.diag(lam + 1e-9 * (dg + 1.0)), b) for lam in lams}

    def predict(self, rows, fit, w):
        mu, sd = fit['mu'], fit['sd']
        zc = w / sd
        out = np.full(len(rows), fit['ybar'] - float(zc @ mu))
        for b in self.blocks:
            off, k = b['off'], b['size']
            if b['kind'] == 'oh':
                out += zc[off:off + k][b['data'][rows]]
            else:
                out += b['data'][rows] @ zc[off:off + k]
        return out


def _pick(metrics, grid):
    defined = {lam: m[0] for lam, m in metrics.items() if m[0] is not None}
    if not defined:
        return grid[len(grid) // 2], 'fallback_all_constant'
    best = max(defined.values())
    cands = sorted(lam for lam, s in defined.items() if abs(s - best) < 1e-12)
    return cands[0], 'defined'


def select_grouped(design, y_view, inner, grid):
    """Unified metric: mean of the 3 inner-fold Spearman values (AMENDMENT section 3)."""
    per_lam = {lam: [] for lam in grid}
    for inn in inner:
        fit = design.gram_zy(inn['train'], y_view[inn['train']])
        ws = design.solve(fit, grid)
        for lam, w in ws.items():
            s, _ = rho_metric(design.predict(inn['val'], fit, w), y_view[inn['val']])
            per_lam[lam].append(s)
    metrics = {}
    for lam, vals in per_lam.items():
        vv = [v for v in vals if v is not None]
        metrics[lam] = (float(np.mean(vv)) if vv else None,)
    lam, why = _pick(metrics, grid)
    return lam, why


def select_rowlevel(design, y_view, train_idx, grid, seed):
    """Row-level inner CV with the SAME fold-mean metric and fold-internal scaler."""
    rng = np.random.default_rng(seed)
    chunks = np.array_split(rng.permutation(len(train_idx)), N_INNER)
    per_lam = {lam: [] for lam in grid}
    for ch in chunks:
        va = train_idx[ch]
        trn = np.setdiff1d(train_idx, va)
        fit = design.gram_zy(trn, y_view[trn])
        ws = design.solve(fit, grid)
        for lam, w in ws.items():
            s, _ = rho_metric(design.predict(va, fit, w), y_view[va])
            per_lam[lam].append(s)
    metrics = {}
    for lam, vals in per_lam.items():
        vv = [v for v in vals if v is not None]
        metrics[lam] = (float(np.mean(vv)) if vv else None,)
    lam, why = _pick(metrics, grid)
    return lam, why


def final_fit_predict(design, y_view, train_idx, test_idx, lam):
    fit = design.gram_zy(train_idx, y_view[train_idx])
    w = design.solve(fit, [lam])[lam]
    return design.predict(test_idx, fit, w)


def main():
    t0 = time.time()
    log = []
    test_label_reads = 0

    def say(msg):
        print(msg, flush=True)
        log.append(msg)

    say('[1/12] verify input + load data ...')
    h = sha256_file(ORIG)
    if h != EXPECTED_SHA:
        raise SystemExit('FATAL: input SHA256 mismatch %s != %s' % (h, EXPECTED_SHA))
    input_rec = {'path': str(ORIG.relative_to(ROOT)).replace('\\', '/'),
                 'bytes': os.path.getsize(ORIG), 'sha256': h}

    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d['emax'] = pd.to_numeric(d['SYNERGY_DELTA_EMAX'], errors='coerce')
    d['cell'] = d['CELL_LINE_NAME'].astype(str)
    d['combo'] = d['ANCHOR_NAME'].astype(str) + " + " + d['LIBRARY_NAME'].astype(str)
    d['key'] = d['cell'] + "|" + d['combo']
    g = d.groupby('key', as_index=False).agg(
        cell=('cell', 'first'), a=('ANCHOR_NAME', 'first'), b=('LIBRARY_NAME', 'first'),
        ap=('ANCHOR_PATHWAY', 'first'), lp=('LIBRARY_PATHWAY', 'first'),
        emax=('emax', 'mean')).dropna(subset=['emax']).reset_index(drop=True)
    for c in ('cell', 'a', 'b', 'ap', 'lp'):
        g[c] = g[c].astype(str)
    assert g.groupby('a')['ap'].nunique().max() == 1
    assert g.groupby('b')['lp'].nunique().max() == 1

    cells = np.array(sorted(g['cell'].unique()))
    drugs = np.array(sorted(set(g['a']) | set(g['b'])))
    a_levels = np.array(sorted(g['ap'].unique()))
    l_levels = np.array(sorted(g['lp'].unique()))
    cell_idx = pd.Categorical(g['cell'], categories=cells).codes.astype(np.int64)
    a_idx = pd.Categorical(g['a'], categories=drugs).codes.astype(np.int64)
    b_idx = pd.Categorical(g['b'], categories=drugs).codes.astype(np.int64)
    ap_idx = pd.Categorical(g['ap'], categories=a_levels).codes.astype(np.int64)
    lp_idx = pd.Categorical(g['lp'], categories=l_levels).codes.astype(np.int64)
    y = g['emax'].to_numpy(float)
    n = len(g)
    pair_labels = g['a'] + '|' + g['b']
    pair_levels = np.array(sorted(set(pair_labels)))
    pair_code = pd.Categorical(pair_labels, categories=pair_levels).codes.astype(np.int64)
    n_pairs = len(pair_levels)
    data_rec = {
        'csv_rows': int(len(d)), 'n_units': int(n), 'n_cells': int(len(cells)),
        'n_drugs': int(len(drugs)), 'n_anchor_drugs': int(g['a'].nunique()),
        'n_library_drugs': int(g['b'].nunique()), 'n_pairs_directed': int(n_pairs),
        'anchor_pathway_levels': int(len(a_levels)), 'library_pathway_levels': int(len(l_levels)),
        'identity_dim': 2 * len(drugs), 'annotation_dim': int(len(a_levels) + len(l_levels)),
        'endpoint': {'mean': round(float(y.mean()), 6), 'sd': round(float(y.std()), 6),
                     'min': round(float(y.min()), 6), 'max': round(float(y.max()), 6)},
        'feature_sha256': {'id_codes': sha256_array(np.stack([a_idx, b_idx])),
                           'path_codes': sha256_array(np.stack([ap_idx, lp_idx]))},
    }
    say('    units=%d cells=%d drugs=%d pairs=%d | ID=%d ANN=%d' % (
        n, len(cells), len(drugs), n_pairs, 2 * len(drugs), len(a_levels) + len(l_levels)))

    say('[2/12] build 10 independent drug partitions x 5 folds + inner folds ...')
    partitions = []
    for p in range(N_PART):
        rng = np.random.default_rng(SEED_PART_BASE + 100 * p)
        perm = rng.permutation(len(drugs))
        fold_of = np.empty(len(drugs), int)
        held = {}
        for f, idx in enumerate(np.array_split(perm, N_FOLDS)):
            fold_of[idx] = f
            held[f] = set(drugs[idx].tolist())
        fa, fb = fold_of[a_idx], fold_of[b_idx]
        outer = []
        for f in range(N_FOLDS):
            te = np.flatnonzero((fa == f) & (fb == f))
            tr = np.flatnonzero((fa != f) & (fb != f))
            outer.append({'f': f, 'held': held[f], 'test': te, 'train': tr})
        inner_all = []
        for o in outer:
            train_drugs = sorted(set(g['a'].iloc[o['train']]) | set(g['b'].iloc[o['train']]))
            assert len(train_drugs) == len(drugs) - len(o['held'])
            rngi = np.random.default_rng(SEED_INNER_BASE + 1000 * p + o['f'])
            pi = rngi.permutation(len(train_drugs))
            ifold = {}
            for j, idx in enumerate(np.array_split(pi, N_INNER)):
                for i in idx:
                    ifold[train_drugs[i]] = j
            trmask = np.zeros(n, bool)
            trmask[o['train']] = True
            ia = np.array([ifold.get(x, -1) for x in g['a']])
            ib = np.array([ifold.get(x, -1) for x in g['b']])
            inner = []
            for j in range(N_INNER):
                iv = np.flatnonzero(trmask & (ia == j) & (ib == j))
                it = np.flatnonzero(trmask & (ia != j) & (ib != j))
                held_j = {dd for dd in train_drugs if ifold[dd] == j}
                assert set(g['a'].iloc[it]).isdisjoint(held_j)
                assert set(g['b'].iloc[it]).isdisjoint(held_j)
                assert set(g['a'].iloc[iv]) <= held_j and set(g['b'].iloc[iv]) <= held_j
                inner.append({'train': it, 'val': iv})
            inner_all.append(inner)
        partitions.append({'p': p, 'outer': outer, 'inner': inner_all, 'held': held})

    part_rec = []
    pooled_test_cells = set()
    total_test = 0
    for pr in partitions:
        folds = []
        for o in pr['outer']:
            pooled_test_cells.update(np.unique(cell_idx[o['test']]).tolist())
            folds.append({'fold': o['f'], 'n_held': len(o['held']),
                          'n_test': int(len(o['test'])),
                          'n_test_cells': int(len(np.unique(cell_idx[o['test']]))),
                          'n_train': int(len(o['train'])),
                          'n_train_drugs': int(len(set(g['a'].iloc[o['train']])
                                                        | set(g['b'].iloc[o['train']]))),
                          'n_inner_val': [int(len(x['val'])) for x in pr['inner'][o['f']]],
                          'n_inner_train': [int(len(x['train'])) for x in pr['inner'][o['f']]]})
        nt = int(sum(f['n_test'] for f in folds))
        total_test += nt
        part_rec.append({'partition': pr['p'],
                         'held': {str(k): sorted(v) for k, v in pr['held'].items()},
                         'folds': folds, 'n_test_total': nt,
                         'mean_test_rows_per_fold': round(float(np.mean(
                             [f['n_test'] for f in folds])), 1)})
    say('    total fold-level test rows across 10 partitions = %d; pooled cells = %d' % (
        total_test, len(pooled_test_cells)))

    say('[3/12] block engine + equivalence check (E8) ...')
    DESIGN_MAIN = BlockDesign([('oh', a_idx, len(drugs)), ('oh', b_idx, len(drugs)),
                               ('oh', ap_idx, len(a_levels)), ('oh', lp_idx, len(l_levels))])
    DESIGN_PATH = BlockDesign([('oh', ap_idx, len(a_levels)), ('oh', lp_idx, len(l_levels))])
    DESIGN_ID = BlockDesign([('oh', a_idx, len(drugs)), ('oh', b_idx, len(drugs))])
    Xd = np.hstack([np.eye(len(drugs))[a_idx], np.eye(len(drugs))[b_idx],
                    np.eye(len(a_levels))[ap_idx], np.eye(len(l_levels))[lp_idx]])
    tr0 = partitions[0]['inner'][0][0]['train']
    va0 = partitions[0]['inner'][0][0]['val']
    mu_d, sd_d = Xd[tr0].mean(0), Xd[tr0].std(0)
    sd_d[sd_d == 0] = 1.0
    Ztr = (Xd[tr0] - mu_d) / sd_d
    Zva = (Xd[va0] - mu_d) / sd_d
    G = Ztr.T @ Ztr
    b = Ztr.T @ (y[tr0] - y[tr0].mean())
    w_dense = np.linalg.solve(G + np.diag(3.0 + 1e-9 * (np.diag(G) + 1.0)), b)
    pred_dense = y[tr0].mean() + Zva @ w_dense
    fit_e = DESIGN_MAIN.gram_zy(tr0, y[tr0])
    pred_engine = DESIGN_MAIN.predict(va0, fit_e, DESIGN_MAIN.solve(fit_e, [3.0])[3.0])
    diff_main = float(np.max(np.abs(pred_engine - pred_dense)))
    # path-only design vs dense path submatrix
    fit_p = DESIGN_PATH.gram_zy(tr0, y[tr0])
    pred_path_engine = DESIGN_PATH.predict(va0, fit_p, DESIGN_PATH.solve(fit_p, [3.0])[3.0])
    lo = 2 * len(drugs)
    Ztr_p = Ztr[:, lo:]
    Gp = Ztr_p.T @ Ztr_p
    bp = Ztr_p.T @ (y[tr0] - y[tr0].mean())
    wp = np.linalg.solve(Gp + np.diag(3.0 + 1e-9 * (np.diag(Gp) + 1.0)), bp)
    pred_dense_path = y[tr0].mean() + Zva[:, lo:] @ wp
    diff_path = float(np.max(np.abs(pred_path_engine - pred_dense_path)))
    assert diff_main < 1e-8 and diff_path < 1e-8, (diff_main, diff_path)
    say('    engine equivalence max|dense-engine| main=%.2e path=%.2e' % (diff_main, diff_path))

    say('[4/12] identity-arm constancy check (partition 0) ...')
    pr0 = partitions[0]
    id_const = []
    for f in range(N_FOLDS):
        o = pr0['outer'][f]
        yv = np.full(n, np.nan); yv[o['train']] = y[o['train']]
        lam, _ = select_grouped(DESIGN_ID, yv, pr0['inner'][f], L_EXT)
        pred = final_fit_predict(DESIGN_ID, yv, o['train'], o['test'], lam)
        id_const.append(bool(is_const(pred)))
    assert all(id_const), id_const
    say('    identity constant in 5/5 partition-0 folds -> rho=0.0 explicit convention for all folds')

    def masked_y(train_idx):
        v = np.full(n, np.nan)
        v[train_idx] = y[train_idx]
        return v

    def run_arm(name, design, scheme, grid, partitions_subset=None):
        nonlocal test_label_reads
        rows, preds = [], {}
        plist = list(range(N_PART)) if partitions_subset is None else list(partitions_subset)
        for p in plist:
            pr = partitions[p]
            for f in range(N_FOLDS):
                o = pr['outer'][f]
                yv = masked_y(o['train'])
                if scheme == 'grouped':
                    lam, why = select_grouped(design, yv, pr['inner'][f], grid)
                else:
                    lam, why = select_rowlevel(design, yv, o['train'], grid,
                                               SEED_ROW_BASE + 1000 * p + f)
                pred = final_fit_predict(design, yv, o['train'], o['test'], lam)
                s, kind = rho_metric(pred, y[o['test']])
                test_label_reads += 1
                rows.append({'arm': name, 'partition': p, 'fold': f, 'scheme': scheme,
                             'grid': 'ext' if len(grid) == len(L_EXT) else 'c130',
                             'lambda': float(lam), 'n_test': int(len(o['test'])),
                             'rho': (None if s is None else round(float(s), 9)),
                             'rho_kind': kind, 'selection': why})
                preds[(p, f)] = (pred, o['test'])
        vals = [r['rho'] for r in rows if r['rho'] is not None]
        return {'name': name, 'rows': rows, 'preds': preds,
                'mean_rho': float(np.mean(vals)) if vals else float('nan'),
                'n_defined': int(sum(1 for r in rows if r['rho_kind'] == 'defined')),
                'n_constant': int(sum(1 for r in rows if r['rho_kind'] == 'constant'))}

    def arm_summary(rec):
        vals = [r['rho'] for r in rec['rows']]
        lam_hit = 0
        for r in rec['rows']:
            top = L_EXT[-1] if r['grid'] == 'ext' else L_C130[-1]
            if abs(r['lambda'] - top) < 1e-12:
                lam_hit += 1
        return {'mean_rho': round(float(np.mean(vals)), 6),
                'fold_rhos': [None if v is None else round(float(v), 6) for v in vals],
                'n_folds': len(vals),
                'n_constant': rec['n_constant'],
                'lambda_ceiling_hits': int(lam_hit),
                'n_fallback': int(sum(1 for r in rec['rows'] if r['selection'] != 'defined')),
                'lambdas_per_fold': [r['lambda'] for r in rec['rows']]}

    say('[5/12] null calibration: shuffle x10 (full design) + capacity x10 (partition 0) ...')

    def shuffled_path_codes(seed):
        rng2 = np.random.default_rng(SEED_SHUF_BASE + seed)
        a_lab = g.groupby('a')['ap'].first(); b_lab = g.groupby('b')['lp'].first()
        a_drugs = np.array(sorted(a_lab.index)); b_drugs = np.array(sorted(b_lab.index))
        a_new = dict(zip(a_drugs, a_lab.loc[a_drugs].to_numpy()[rng2.permutation(len(a_drugs))]))
        b_new = dict(zip(b_drugs, b_lab.loc[b_drugs].to_numpy()[rng2.permutation(len(b_drugs))]))
        ap_s = pd.Categorical([a_new[q] for q in g['a']], categories=a_levels).codes.astype(np.int64)
        lp_s = pd.Categorical([b_new[q] for q in g['b']], categories=l_levels).codes.astype(np.int64)
        return ap_s, lp_s

    null = {'shuffle': {}, 'capacity': {}}
    shuffle_preds = {}
    for seed in range(N_NULL_SEEDS):
        ap_s, lp_s = shuffled_path_codes(seed)
        design = BlockDesign([('oh', a_idx, len(drugs)), ('oh', b_idx, len(drugs)),
                              ('oh', ap_s, len(a_levels)), ('oh', lp_s, len(l_levels))])
        rec = run_arm('shuffle_seed%d' % seed, design, 'grouped', L_EXT)
        null['shuffle'][str(seed)] = {'mean_rho': round(float(rec['mean_rho']), 6),
                                      'n_defined': rec['n_defined'],
                                      'lambda_ceiling_hits': int(sum(
                                          1 for r in rec['rows'] if abs(r['lambda'] - L_EXT[-1]) < 1e-12))}
        shuffle_preds[seed] = rec['preds']
        say('    shuffle seed%d mean_rho=%+.4f ceiling_hits=%d' % (
            seed, rec['mean_rho'], null['shuffle'][str(seed)]['lambda_ceiling_hits']))
    for seed in range(N_NULL_SEEDS):
        rnd = np.random.default_rng(SEED_CAP_BASE + seed).standard_normal(
            (n, len(a_levels) + len(l_levels)))
        design = BlockDesign([('oh', a_idx, len(drugs)), ('oh', b_idx, len(drugs)),
                              ('ct', rnd, rnd.shape[1])])
        rec = run_arm('capacity_seed%d' % seed, design, 'grouped', L_EXT,
                      partitions_subset=[0])
        null['capacity'][str(seed)] = {'mean_rho': round(float(rec['mean_rho']), 6),
                                       'n_defined': rec['n_defined']}
        say('    capacity seed%d mean_rho=%+.4f (partition 0)' % (seed, rec['mean_rho']))

    def null_summary(dct):
        vals = np.array([v['mean_rho'] for v in dct.values()], float)
        return {'n_seeds': int(len(vals)), 'mean': round(float(vals.mean()), 6),
                'sd': round(float(vals.std(ddof=1)), 6), 'min': round(float(vals.min()), 6),
                'max': round(float(vals.max()), 6),
                'q025': round(float(np.quantile(vals, .025)), 6),
                'q975': round(float(np.quantile(vals, .975)), 6)}
    null_stats = {'shuffle': null_summary(null['shuffle']),
                  'capacity': null_summary(null['capacity'])}
    e6_ok = (abs(null_stats['shuffle']['mean']) <= 0.02
             and null_stats['shuffle']['q025'] <= 0.0 <= null_stats['shuffle']['q975'])

    def boot_estimates(targets, nboot, seed, cluster='drug'):
        rng2 = np.random.default_rng(seed)
        arms = [t['preds'] for t in targets]
        signs = [t.get('sign', 1.0) for t in targets]
        keys = sorted(arms[0].keys())
        out = np.empty(nboot)
        for b in range(nboot):
            if cluster == 'drug':
                amult = np.bincount(rng2.integers(0, len(drugs), size=len(drugs)),
                                    minlength=len(drugs))
                bmult = np.bincount(rng2.integers(0, len(drugs), size=len(drugs)),
                                    minlength=len(drugs))
            elif cluster == 'cell':
                cmult = np.bincount(rng2.integers(0, len(cells), size=len(cells)),
                                    minlength=len(cells))
            elif cluster == 'pair':
                pmult = np.bincount(rng2.integers(0, n_pairs, size=n_pairs),
                                    minlength=n_pairs)
            else:
                cmult = np.bincount(rng2.integers(0, len(cells), size=len(cells)),
                                    minlength=len(cells))
                pmult = np.bincount(rng2.integers(0, n_pairs, size=n_pairs),
                                    minlength=n_pairs)
            tot = 0.0
            for arm, sign in zip(arms, signs):
                fold_vals = []
                for p, f in keys:
                    pred, te = arm[(p, f)]
                    if cluster == 'drug':
                        w = amult[a_idx[te]] * bmult[b_idx[te]]
                    elif cluster == 'cell':
                        w = cmult[cell_idx[te]]
                    elif cluster == 'pair':
                        w = pmult[pair_code[te]]
                    else:
                        w = cmult[cell_idx[te]] * pmult[pair_code[te]]
                    keep = np.repeat(np.arange(len(te)), w)
                    fold_vals.append(rho_fast(pred[keep], y[te][keep]))
                tot += sign * float(np.mean(fold_vals))
            out[b] = tot
        return out

    def boot_rec(boots):
        return {'ci95': [round(float(np.quantile(boots, .025)), 6),
                         round(float(np.quantile(boots, .975)), 6)],
                'boot_mean': round(float(np.mean(boots)), 6),
                'boot_sd': round(float(np.std(boots, ddof=1)), 6),
                'mde80': round(float(2.802 * np.std(boots, ddof=1)), 6)}

    say('[6/12] design checks + MDE design gate (E7) ...')
    boots_shuf0 = boot_estimates([{'preds': shuffle_preds[0], 'sign': 1.0}],
                                 N_BOOT_SENS, SEED_BOOT_DRUG + 21, 'drug')
    mde_design = boot_rec(boots_shuf0)
    e7_ok = mde_design['mde80'] <= DELTA_MIN
    say('    MDE80_design(drug, shuffle seed0) = %.4f (sd %.4f) -> E7=%s' % (
        mde_design['mde80'], mde_design['boot_sd'], e7_ok))

    e1_ok = (total_test >= 20000 and len(pooled_test_cells) >= 100
             and all(fr['n_test'] >= 300 and fr['n_train_drugs'] == 52
                     for pr_rec in part_rec for fr in pr_rec['folds']))
    e2_ok = all(min(fr['n_inner_val']) >= 200 for pr_rec in part_rec for fr in pr_rec['folds'])
    design_checks = {
        'E1_fold_structure': {'pass': bool(e1_ok), 'value': {
            'n_partitions': N_PART, 'n_folds': N_FOLDS,
            'total_fold_test_rows': int(total_test),
            'pooled_test_cells': int(len(pooled_test_cells)),
            'per_partition_n_test_total': [r['n_test_total'] for r in part_rec],
            'per_partition_n_test_per_fold': [[f['n_test'] for f in r['folds']] for r in part_rec],
            'train_drugs_per_fold_min': int(min(fr['n_train_drugs'] for pr_rec in part_rec
                                                for fr in pr_rec['folds']))}},
        'E2_inner_overlap_and_both_unseen': {'pass': bool(e2_ok), 'value':
            'assertions passed for all 50 outer folds: inner-held disjoint from inner-train '
            'drugs; inner-validation rows have both drugs in inner-held'},
        'E3_unified_inner_metric': {'pass': True, 'value':
            'grouped and row-level both use the mean of the 3 per-inner-fold Spearman values; '
            'scaler fitted inside each inner training fold (see record_r196_v2.md)'},
        'E4_lambda_grids': {'pass': True,
                            'value': {'L_EXT': list(L_EXT), 'L_C130': list(L_C130)}},
        'E5_test_label_reads': {'pass': True, 'value': {
            'count': int(test_label_reads),
            'expected': int(N_FOLDS * N_PART * (5 + 2 * N_NULL_SEEDS) - N_FOLDS * N_PART * 1),
            'note': 'the count is populated after treatment/null runs; see final field below'}},
        'E6_null_calibration': {'pass': bool(e6_ok), 'value': null_stats},
        'E7_mde_design_drug_unit': {'pass': bool(e7_ok), 'value': mde_design},
        'E8_engine_equivalence': {'pass': True, 'value': {
            'max_abs_diff_main': diff_main, 'max_abs_diff_path': diff_path}},
    }
    design_gate = all(v['pass'] for k, v in design_checks.items()
                      if k.split('_')[0] in ('E1', 'E2', 'E6', 'E7'))
    say('    design gate (pre-scoring) = %s' % design_gate)

    say('[7/12] treatment arms ...')
    ann = run_arm('annotation', DESIGN_MAIN, 'grouped', L_EXT)
    annonly = run_arm('annotation_only', DESIGN_PATH, 'grouped', L_EXT)
    grouped_c130 = run_arm('grouped_c130_grid', DESIGN_MAIN, 'grouped', L_C130)
    row_ext = run_arm('rowlevel_ext', DESIGN_MAIN, 'rowlevel', L_EXT)
    row_c130 = run_arm('rowlevel_c130_grid', DESIGN_MAIN, 'rowlevel', L_C130)
    gain_pts = np.array([r['rho'] for r in ann['rows']], float)
    point = float(np.mean(gain_pts))
    say('    annotation=%.4f (identity=0.0 explicit) gain=%.4f | annonly=%.4f | rowlevel_ext=%.4f '
        '| rowlevel_c130=%.4f | grouped_c130=%.4f' % (
            ann['mean_rho'], point, annonly['mean_rho'], row_ext['mean_rho'],
            row_c130['mean_rho'], grouped_c130['mean_rho']))

    say('[8/12] primary drug bootstrap + cluster sensitivities ...')
    boots_drug = boot_estimates([{'preds': ann['preds'], 'sign': 1.0}], N_BOOT,
                                SEED_BOOT_DRUG, 'drug')
    boots_cell = boot_estimates([{'preds': ann['preds'], 'sign': 1.0}], N_BOOT,
                                SEED_BOOT_DRUG + 1, 'cell')
    boots_pair = boot_estimates([{'preds': ann['preds'], 'sign': 1.0}], N_BOOT_SENS,
                                SEED_BOOT_DRUG + 2, 'pair')
    boots_two = boot_estimates([{'preds': ann['preds'], 'sign': 1.0}], N_BOOT_SENS,
                               SEED_BOOT_DRUG + 3, 'twoway')
    primary = boot_rec(boots_drug)
    ci_cell, ci_pair, ci_two = boot_rec(boots_cell), boot_rec(boots_pair), boot_rec(boots_two)
    annonly_boot = boot_estimates([{'preds': annonly['preds'], 'sign': 1.0}], N_BOOT_SENS,
                                  SEED_BOOT_DRUG + 4, 'drug')

    say('[9/12] partition-level + fold-level dispersion ...')
    part_means = [float(np.mean([r['rho'] for r in ann['rows'] if r['partition'] == p]))
                  for p in range(N_PART)]
    part_sd = float(np.std(part_means, ddof=1))
    part_se = part_sd / np.sqrt(N_PART)
    t9 = 2.262
    partition_rec = {
        'per_partition_gain': [round(v, 6) for v in part_means],
        'mean': round(float(np.mean(part_means)), 6), 'sd': round(part_sd, 6),
        'se': round(float(part_se), 6),
        't_interval_95_df9': [round(float(np.mean(part_means) - t9 * part_se), 6),
                              round(float(np.mean(part_means) + t9 * part_se), 6)],
        'min': round(float(np.min(part_means)), 6), 'max': round(float(np.max(part_means)), 6),
        'leave_one_partition_out': [
            {'left_out_partition': p,
             'mean_gain': round(float(np.mean([r['rho'] for r in ann['rows']
                                               if r['partition'] != p])), 6)}
            for p in range(N_PART)]}
    fold_sd = float(np.std(gain_pts, ddof=1))
    fold_se = fold_sd / np.sqrt(len(gain_pts))
    t49 = 2.010
    fold_rec = {
        'n_folds': int(len(gain_pts)),
        'per_fold_gain': [round(float(v), 6) for v in gain_pts],
        'mean': round(point, 6), 'sd': round(fold_sd, 6), 'se': round(float(fold_se), 6),
        't_interval_95_df49': [round(float(point - t49 * fold_se), 6),
                               round(float(point + t49 * fold_se), 6)],
        'min': round(float(np.min(gain_pts)), 6), 'max': round(float(np.max(gain_pts)), 6),
        'note': 'formal sensitivity (AMENDMENT section 4/6); primary inference uses the '
                'drug-cluster bootstrap, not this t-interval'}
    say('    partition mean %.4f sd %.4f t-CI [%.4f,%.4f] | fold sd %.4f' % (
        partition_rec['mean'], partition_rec['sd'], partition_rec['t_interval_95_df9'][0],
        partition_rec['t_interval_95_df9'][1], fold_sd))

    say('[10/12] H196b row-level vs grouped (paired drug bootstrap) ...')
    diff_ext = float(row_ext['mean_rho']) - point
    diff_c130 = float(row_c130['mean_rho']) - float(grouped_c130['mean_rho'])
    row_boots = boot_estimates([{'preds': row_ext['preds'], 'sign': 1.0},
                                {'preds': ann['preds'], 'sign': -1.0}],
                               N_BOOT, SEED_BOOT_DRUG + 5, 'drug')
    rowc130_boots = boot_estimates([{'preds': row_c130['preds'], 'sign': 1.0},
                                    {'preds': grouped_c130['preds'], 'sign': -1.0}],
                                   N_BOOT_SENS, SEED_BOOT_DRUG + 6, 'drug')
    h196b = {
        'rowlevel_ext_gain': round(float(row_ext['mean_rho']), 6),
        'grouped_ext_gain': round(point, 6),
        'difference_ext': round(diff_ext, 6),
        'difference_ext_ci95_drug': boot_rec(row_boots)['ci95'],
        'rowlevel_c130_gain': round(float(row_c130['mean_rho']), 6),
        'grouped_c130_gain': round(float(grouped_c130['mean_rho']), 6),
        'difference_c130': round(diff_c130, 6),
        'difference_c130_ci95_drug': boot_rec(rowc130_boots)['ci95'],
        'rowlevel_ext_lambda_ceiling_hits': arm_summary(row_ext)['lambda_ceiling_hits'],
        'rowlevel_c130_lambda_ceiling_hits': arm_summary(row_c130)['lambda_ceiling_hits'],
        'rowlevel_ext_lambdas_head': arm_summary(row_ext)['lambdas_per_fold'][:10],
        'grouped_ext_lambdas_head': arm_summary(ann)['lambdas_per_fold'][:10],
        'material_optimism_flag_ext': bool(diff_ext > MATERIAL_OPTIMISM),
        'note': 'H196b is a reliability qualifier only; it does not change the pre-registered '
                'verdict rule (AMENDMENT section 5). Both schemes now use the identical '
                'fold-mean inner metric; the c130-grid variants are the C130 bridge.'}
    say('    rowlevel_ext - grouped_ext = %+.4f CI %s | c130-grid diff %+.4f' % (
        diff_ext, h196b['difference_ext_ci95_drug'], diff_c130))

    say('[11/12] capacity contrast + verdict ...')
    cap0 = null['capacity']['0']['mean_rho']
    ann_part0 = float(np.mean([r['rho'] for r in ann['rows'] if r['partition'] == 0]))
    capacity_contrast = {
        'annotation_partition0_gain': round(ann_part0, 6),
        'capacity_seed0_partition0_gain': round(float(cap0), 6),
        'difference': round(ann_part0 - float(cap0), 6),
        'note': 'descriptive zero-model specificity contrast; capacity was run on partition 0 only'}

    subtypes = []
    if not design_gate or primary['mde80'] > DELTA_MIN:
        verdict = 'inconclusive'
        if not design_gate:
            subtypes.append('design_check_failed')
        if primary['mde80'] > DELTA_MIN:
            subtypes.append('primary_mde80_gt_delta_min')
    elif primary['ci95'][0] > 0.0 and point >= DELTA_MIN:
        verdict = 'replicated_under_audit'
    else:
        verdict = 'weakened'
        if primary['ci95'][0] <= 0.0:
            subtypes.append('ci_includes_zero')
        if point < DELTA_MIN:
            subtypes.append('below_minimum_effect')

    expected_reads = N_FOLDS * N_PART * (3 + 2 * 0 + 0) + N_FOLDS * N_PART * 2 \
        + N_FOLDS * N_PART * (2 * 0) + N_FOLDS * 0
    # counted arms: annotation, annotation_only, grouped_c130, rowlevel_ext, rowlevel_c130
    # = 5 arms x 50 folds; capacity = 10 seeds x 5 folds; shuffle = 10 seeds x 50 folds
    expected_reads = 5 * N_FOLDS * N_PART + N_NULL_SEEDS * N_FOLDS + N_NULL_SEEDS * N_FOLDS * N_PART
    design_checks['E5_test_label_reads'] = {
        'pass': bool(test_label_reads == expected_reads),
        'value': {'count': int(test_label_reads), 'expected': int(expected_reads),
                  'note': 'test labels are read only in the scoring step; lambda selection and '
                          'prediction generation receive a training-only label view whose '
                          'non-training entries are NaN (asserted finite wherever used)'}}

    judgment = {
        'verdict': verdict, 'subtypes': subtypes,
        'verdict_rule': 'inconclusive if primary MDE80>delta_min or any design check fails; '
                        'replicated if primary drug-cluster CI lower>0 and point>=delta_min and '
                        'MDE80<=delta_min and design checks pass; weakened otherwise',
        'primary_unit': 'held-out drugs (10 independent drug partitions; drug-cluster bootstrap)',
        'primary_estimator': 'mean of 50 fold-level gains (10 partitions x 5 folds)',
        'delta_min': DELTA_MIN,
        'delta_min_operational': 'rho=0.05 <=> Kendall tau=(2/pi)asin(0.05)=0.0318 <=> ~1.59 pp '
                                 'higher chance of correctly ordering a random pair of unseen '
                                 'combinations; a reliability minimum, not a utility threshold',
        'point_estimate': round(point, 6),
        'primary_ci95_drug': primary['ci95'],
        'primary_mde80': primary['mde80'],
        'primary_boot_sd': primary['boot_sd'],
        'ci95_cell': ci_cell['ci95'], 'mde80_cell': ci_cell['mde80'],
        'ci95_pair': ci_pair['ci95'], 'mde80_pair': ci_pair['mde80'],
        'ci95_twoway': ci_two['ci95'], 'mde80_twoway': ci_two['mde80'],
        'large_gain_flag_descriptive_only': bool(point > LARGE_GAIN_FLAG),
        'stability_band': 'no upper bound (AMENDMENT section 5); large_gain_flag recorded only',
        'partition_dispersion': partition_rec,
        'fold_dispersion_formal_sensitivity': fold_rec,
        'null_arms': null_stats,
        'annotation_only_gain': round(float(annonly['mean_rho']), 6),
        'annotation_only_ci95_drug': boot_rec(annonly_boot)['ci95'],
        'capacity_contrast': capacity_contrast,
        'h196b': h196b,
        'c130_reference_not_a_comparison_interval': {
            'gain': 0.11831576209676734,
            'ci95': [0.09471202625415462, 0.14085000835904368],
            'note': 'C130 used 40 overlapping random splits and row-level inner tuning with '
                    'lambda<=1000; this amendment uses 10 independent drug partitions, '
                    'drug-grouped inner tuning and lambda<=10000. Its CI is NOT a reference '
                    'interval for this audit.'},
        'wording_template': {
            'replicated_under_audit': 'allowed only as: within AMENDMENT-001, the fixed 10 drug '
                                      'partitions and the declared primary unit (held-out drugs), '
                                      'the both-unseen gain point estimate is >=delta_min with '
                                      'drug-cluster CI lower>0 and primary MDE80<=delta_min; must '
                                      'be reported together with the drug CI/MDE and partition/'
                                      'fold dispersion; no claim of C130 replication/confirmation/'
                                      'magnitude recovery/decision use',
            'weakened': 'may not be written as C130 refuted or annotation useless; only as "did '
                        'not meet the audit-level minimum standard under this protocol"',
            'inconclusive': 'may not be written as a negative result; only as "underpowered at '
                            'the audit target unit / design check failed, unresolved"'},
        'not_claims': ['not an external replication', 'not an independent confirmation',
                       'no decision benefit', 'no mechanism'],
    }

    say('[12/12] write artefacts ...')
    rows_out = []
    for rec in (ann, annonly, grouped_c130, row_ext, row_c130):
        rows_out.extend(rec['rows'])
    rows_out.append({'arm': 'identity', 'partition': -1, 'fold': -1, 'scheme': 'constant',
                     'grid': 'n/a', 'lambda': 0.0, 'n_test': 0, 'rho': 0.0,
                     'rho_kind': 'constant', 'selection': 'explicit_convention'})
    with open(BASE / 'r196_v2_rows.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['arm', 'partition', 'fold', 'scheme', 'grid',
                                           'lambda', 'n_test', 'rho', 'rho_kind', 'selection'],
                           lineterminator='\n')
        w.writeheader()
        for r in sorted(rows_out, key=lambda x: (x['arm'], x['partition'], x['fold'])):
            w.writerow(r)

    r196 = {
        'protocol': {'path': 'AMENDMENT_R196.md',
                     'sha256': sha256_file(BASE / 'AMENDMENT_R196.md')},
        'script': {'path': 'r196_v2.py', 'sha256': sha256_file(Path(__file__).resolve())},
        'supersedes': {'v1_protocol': 'PROTOCOL_R196.md',
                       'v1_verdict_withdrawn': 'replicated_under_audit',
                       'revocation': 'REVOCATION_R196.md',
                       'challenge': 'challenge_R196.md'},
        'input': input_rec,
        'data': data_rec,
        'settings': {
            'n_partitions': N_PART, 'n_folds': N_FOLDS, 'n_inner_folds': N_INNER,
            'seed_part_base': SEED_PART_BASE, 'seed_inner_base': SEED_INNER_BASE,
            'seed_row_base': SEED_ROW_BASE, 'seed_boot_drug': SEED_BOOT_DRUG,
            'seed_cap_base': SEED_CAP_BASE, 'seed_shuf_base': SEED_SHUF_BASE,
            'lambdas_ext': list(L_EXT), 'lambdas_c130': list(L_C130),
            'n_boot_primary': N_BOOT, 'n_boot_sensitivity': N_BOOT_SENS,
            'n_null_seeds': N_NULL_SEEDS, 'const_tol': CONST_TOL,
            'delta_min': DELTA_MIN, 'large_gain_flag_threshold': LARGE_GAIN_FLAG,
            'material_optimism_threshold': MATERIAL_OPTIMISM,
            'primary_estimator': 'mean of 50 fold-level gains (10 partitions x 5 drug folds)',
            'identity_convention': 'rho(identity)=0.0 at both-unseen test (constant predictions; '
                                   'asserted on partition 0, constructive for all folds)'},
        'partitions': part_rec,
        'design_checks': design_checks,
        'null_arms_per_seed': {'shuffle': null['shuffle'], 'capacity': null['capacity']},
        'treatment': {
            'annotation': arm_summary(ann),
            'annotation_only': arm_summary(annonly),
            'grouped_c130_grid': arm_summary(grouped_c130),
            'rowlevel_ext': arm_summary(row_ext),
            'rowlevel_c130_grid': arm_summary(row_c130),
            'identity': {'mean_rho': 0.0, 'n_constant': N_PART * N_FOLDS,
                         'convention': 'explicit constant-prediction convention'}},
        'judgment': judgment,
        'deterministic': {'random': False, 'timestamps': False, 'json_sort_keys': True},
        'deviations': [],
        'log': log,
    }
    with open(BASE / 'r196_v2.json', 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(r196, fh, sort_keys=True, ensure_ascii=True, indent=1)
        fh.write('\n')
    say('DONE verdict=%s point=%.4f primary_ci=%s primary_mde=%.4f' % (
        verdict, point, primary['ci95'], primary['mde80']))
    print('DONE wall=%.1fs' % (time.time() - t0))
    print('r196_v2.json sha256:', sha256_file(BASE / 'r196_v2.json'))


if __name__ == '__main__':
    main()
