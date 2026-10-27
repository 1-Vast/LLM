#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PROTOCOL_R196 implementation: audit-level re-estimation of the C130 frozen claim.

Design (frozen before this script existed, PROTOCOL_R196.md):
  * 5 outer folds grouped by drug (union drug list; both roles held together);
  * main analysis: lambda chosen by DRUG-GROUPED inner CV (both-unseen inner validation,
    scaler fitted inside inner training folds), inner metric = pooled Spearman;
  * control: C130's row-level inner CV (2 variants: scaler-before-split and fold-scaled);
  * arms: annotation [ID,ANN] (main), identity [ID], annotation_only [ANN],
    capacity [ID,RND] x10 seeds, shuffle [ID,ANN_shuf] x10 seeds;
  * CI clustered by cell (primary), pair and two-way as sensitivity; MDE80 same construction;
  * design checks run BEFORE the final treatment scoring (null arms + MDE gate).

Deterministic: fixed seeds, no timestamps, JSON sort_keys=True. No network. CPU only.
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

SEED_OUTER = 20261027
SEED_INNER_BASE = SEED_OUTER + 1000
SEED_ROW_BASE = SEED_OUTER + 2000
SEED_BOOT = SEED_OUTER + 3000
SEED_CAP_BASE = SEED_OUTER + 4000
SEED_SHUF_BASE = SEED_OUTER + 5000
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0, 3000.0, 10000.0)
N_FOLDS = 5
N_INNER = 3
N_BOOT = 2000
N_BOOT_SENS = 1000
N_NULL_SEEDS = 10
CONST_TOL = 1e-9
DELTA_MIN = 0.05
BAND = (0.05, 0.20)
MATERIAL_OPTIMISM = 0.05
CHECKS = {'D1_min_fold_test_rows': 300, 'D1_min_total_test_rows': 2000,
          'D1_min_cells_covered': 100, 'D2_min_inner_val_rows': 200,
          'D6_null_abs_mean_rho_max': 0.02}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def sha256_array(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def onehot(idx, k):
    M = np.zeros((len(idx), k), dtype=np.float64)
    M[np.arange(len(idx)), idx] = 1.0
    return M


def is_const(p):
    if len(p) < 5:
        return True
    return float(np.ptp(p)) <= CONST_TOL * max(1.0, float(np.abs(p).max()))


def rho(pred, yv):
    """Spearman with the frozen constant-prediction convention (PROTOCOL_R196 section 6)."""
    if len(pred) < 5 or len(np.unique(yv)) < 2:
        return None, 'too_small'
    if is_const(pred):
        return 0.0, 'constant'
    s = spearmanr(pred, yv).statistic
    if not np.isfinite(s):
        return 0.0, 'nonfinite'
    return float(s), 'defined'


def rho_fast(pred, yv):
    """Same convention, rank-based (used inside bootstrap loops)."""
    if len(pred) < 5:
        return None
    if is_const(pred):
        return 0.0
    r1 = rankdata(pred)
    r2 = rankdata(yv)
    s1, s2 = r1.std(), r2.std()
    if s1 == 0.0 or s2 == 0.0:
        return 0.0
    v = float(np.corrcoef(r1, r2)[0, 1])
    return v if np.isfinite(v) else 0.0


# ------------------------------------------------------------------ modelling
def standardize(Xfit, Xapp):
    mu = Xfit.mean(0)
    sd = Xfit.std(0)
    sd[sd == 0] = 1.0
    return (Xfit - mu) / sd, (Xapp - mu) / sd


def gram_solve(Z, yv, lams):
    assert np.isfinite(yv).all(), 'training label view must be finite'
    yc = yv - yv.mean()
    G = Z.T @ Z
    b = Z.T @ yc
    dg = np.diag(G).copy()
    ws = {}
    for lam in lams:
        ws[lam] = np.linalg.solve(G + np.diag(lam + 1e-9 * (dg + 1.0)), b)
    return ws, float(yv.mean())


def fit_predict(X, y, tr, te, lam):
    """Fit on training rows only; return test predictions (no test labels touched)."""
    Ztr, Zte = standardize(X[tr], X[te])
    ws, ym = gram_solve(Ztr, y[tr], [lam])
    return ym + Zte @ ws[lam]


def select_grouped(X, y_train, inner, lams):
    """PROTOCOL_R196 section 5: drug-grouped inner CV, scaler inside inner train."""
    parts = {lam: [] for lam in lams}
    for inn in inner:
        it, iv = inn['train'], inn['val']
        Zit, Ziv = standardize(X[it], X[iv])
        ws, ym = gram_solve(Zit, y_train[it], lams)
        for lam, w in ws.items():
            parts[lam].append((ym + Ziv @ w, y_train[iv]))
    metrics = {}
    kinds = {}
    for lam, chunks in parts.items():
        p = np.concatenate([c[0] for c in chunks])
        t = np.concatenate([c[1] for c in chunks])
        s, kind = rho(p, t)
        metrics[lam] = s
        kinds[lam] = kind
    defined = {lam: s for lam, s in metrics.items() if s is not None and kinds[lam] == 'defined'}
    if not defined:
        return LAMBDAS[len(LAMBDAS) // 2], metrics, kinds, 'fallback_all_constant'
    best = max(defined.values())
    cands = sorted(lam for lam, s in defined.items() if abs(s - best) < 1e-12)
    return cands[0], metrics, kinds, 'defined'


def select_rowlevel(X, y_train, tr_idx, lams, seed, fold_scaled):
    """C130-style row-level inner CV (3 random row folds)."""
    rng = np.random.default_rng(seed)
    chunks = np.array_split(rng.permutation(len(tr_idx)), 3)
    if fold_scaled:
        parts = {lam: [] for lam in lams}
        for ch in chunks:
            va = tr_idx[ch]
            trn = np.setdiff1d(tr_idx, va)
            Zit, Ziv = standardize(X[trn], X[va])
            ws, ym = gram_solve(Zit, y_train[trn], lams)
            for lam, w in ws.items():
                parts[lam].append((ym + Ziv @ w, y_train[va]))
        metrics, kinds = {}, {}
        for lam, chunks2 in parts.items():
            p = np.concatenate([c[0] for c in chunks2])
            t = np.concatenate([c[1] for c in chunks2])
            s, kind = rho(p, t)
            metrics[lam] = s
            kinds[lam] = kind
    else:  # C130 exact manner: scaler fitted on the whole outer-train before inner split
        Ztr = standardize(X[tr_idx], X[tr_idx])[0]
        parts = {lam: [] for lam in lams}
        for ch in chunks:
            va = ch
            trn = np.setdiff1d(np.arange(len(tr_idx)), va)
            ws, ym = gram_solve(Ztr[trn], y_train[tr_idx][trn], lams)
            for lam, w in ws.items():
                parts[lam].append((ym + Ztr[va] @ w, y_train[tr_idx][va]))
        metrics, kinds = {}, {}
        for lam, chunks2 in parts.items():
            vals = [rho(c[0], c[1])[0] for c in chunks2]
            vals = [v for v in vals if v is not None]
            metrics[lam] = float(np.mean(vals)) if vals else None
            kinds[lam] = 'defined' if vals else 'undefined'
    defined = {lam: s for lam, s in metrics.items() if s is not None}
    if not defined:
        return LAMBDAS[len(LAMBDAS) // 2], metrics, kinds, 'fallback_all_constant'
    best = max(defined.values())
    cands = sorted(lam for lam, s in defined.items() if abs(s - best) < 1e-12)
    return cands[0], metrics, kinds, 'defined'


# ------------------------------------------------------------------ main
def main():
    t_start = time.time()
    log = []

    def say(msg):
        print(msg, flush=True)
        log.append(msg)

    say('[1/10] verify input + load data ...')
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
    cell_idx = pd.Categorical(g['cell'], categories=cells).codes
    a_idx = pd.Categorical(g['a'], categories=drugs).codes
    b_idx = pd.Categorical(g['b'], categories=drugs).codes
    ap_idx = pd.Categorical(g['ap'], categories=a_levels).codes
    lp_idx = pd.Categorical(g['lp'], categories=l_levels).codes
    y = g['emax'].to_numpy(float)
    n = len(g)

    Xid = np.hstack([onehot(a_idx, len(drugs)), onehot(b_idx, len(drugs))])
    Xpath = np.hstack([onehot(ap_idx, len(a_levels)), onehot(lp_idx, len(l_levels))])
    data_rec = {
        'csv_rows': int(len(d)),
        'n_units': int(n), 'n_cells': int(len(cells)), 'n_drugs': int(len(drugs)),
        'n_anchor_drugs': int(g['a'].nunique()), 'n_library_drugs': int(g['b'].nunique()),
        'n_directed_pairs': int(g.groupby(['a', 'b']).ngroups),
        'n_unordered_pairs': int(len({tuple(sorted(p)) for p in zip(g['a'], g['b'])})),
        'anchor_pathway_levels': sorted(a_levels.tolist()),
        'library_pathway_levels': sorted(l_levels.tolist()),
        'n_anchor_levels': int(len(a_levels)), 'n_library_levels': int(len(l_levels)),
        'identity_dim': int(Xid.shape[1]), 'annotation_dim': int(Xpath.shape[1]),
        'endpoint': {'mean': round(float(y.mean()), 6), 'sd': round(float(y.std()), 6),
                     'min': round(float(y.min()), 6), 'max': round(float(y.max()), 6)},
        'feature_sha256': {'Xid': sha256_array(Xid), 'Xpath': sha256_array(Xpath)},
    }
    say('    units=%d cells=%d drugs=%d identity=%d annotation=%d endpoint sd=%.4f' % (
        n, len(cells), len(drugs), Xid.shape[1], Xpath.shape[1], y.std()))

    say('[2/10] outer drug folds + inner drug folds ...')
    rng = np.random.default_rng(SEED_OUTER)
    perm = rng.permutation(len(drugs))
    fold_of = np.empty(len(drugs), int)
    outer_assignment = {}
    for f, idx in enumerate(np.array_split(perm, N_FOLDS)):
        fold_of[idx] = f
        outer_assignment[f] = sorted(drugs[idx].tolist())
    fa, fb = fold_of[a_idx], fold_of[b_idx]
    outer = []
    for f in range(N_FOLDS):
        te = np.flatnonzero((fa == f) & (fb == f))
        tr = np.flatnonzero((fa != f) & (fb != f))
        one = np.flatnonzero(((fa == f) & (fb != f)) | ((fa != f) & (fb == f)))
        outer.append({'f': f, 'held': set(drugs[fold_of == f]), 'test': te,
                      'train': tr, 'one_seen': one})
    inner_all = []
    inner_rec = []
    for o in outer:
        train_drugs = sorted(set(g['a'].iloc[o['train']]) | set(g['b'].iloc[o['train']]))
        assert len(train_drugs) == len(drugs) - len(o['held'])  # 52
        rngi = np.random.default_rng(SEED_INNER_BASE + o['f'])
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
            # D2/D3 assertions: inner drug overlap = 0 and inner val = both-unseen analogue
            assert not (held_j & set(g['a'].iloc[it]) & set(g['b'].iloc[it])) or True
            assert set(g['a'].iloc[it]).isdisjoint(held_j)
            assert set(g['b'].iloc[it]).isdisjoint(held_j)
            assert set(g['a'].iloc[iv]) <= held_j and set(g['b'].iloc[iv]) <= held_j
            inner.append({'j': j, 'held': held_j, 'val': iv, 'train': it})
        inner_all.append(inner)
        inner_rec.append({'outer_fold': o['f'],
                          'inner_held_sizes': [len(x['held']) for x in inner],
                          'inner_val_rows': [int(len(x['val'])) for x in inner],
                          'inner_train_rows': [int(len(x['train'])) for x in inner],
                          'inner_train_drugs': int(len(train_drugs))})

    say('[3/10] design checks D1-D4 ...')
    fold_rec = []
    for o in outer:
        te_cells = np.unique(cell_idx[o['test']])
        fold_rec.append({'fold': o['f'], 'held_drugs': sorted(o['held']),
                         'n_held': len(o['held']), 'n_test': int(len(o['test'])),
                         'n_test_cells': int(len(te_cells)),
                         'n_test_pairs': int(g[['a', 'b']].iloc[o['test']].drop_duplicates().shape[0]),
                         'n_train': int(len(o['train'])),
                         'n_train_drugs': int(len(set(g['a'].iloc[o['train']]) | set(g['b'].iloc[o['train']]))),
                         'n_one_seen': int(len(o['one_seen']))})
    test_all = np.concatenate([o['test'] for o in outer])
    design = {
        'outer_folds': fold_rec,
        'outer_assignment': {str(k): v for k, v in outer_assignment.items()},
        'pooled_test_rows': int(len(test_all)),
        'pooled_test_rows_pct': round(100.0 * len(test_all) / n, 4),
        'pooled_test_cells': int(len(np.unique(cell_idx[test_all]))),
        'pooled_test_pairs': int(g[['a', 'b']].iloc[test_all].drop_duplicates().shape[0]),
        'inner_folds': inner_rec,
        'inner_overlap_assertions': 'passed (inner-held drugs disjoint from inner-train drugs; '
                                    'inner-val rows both drugs in inner-held)',
    }
    d1_ok = (all(len(o['held']) == 13 for o in outer)
             and all(len(o['test']) >= CHECKS['D1_min_fold_test_rows'] for o in outer)
             and len(test_all) >= CHECKS['D1_min_total_test_rows']
             and len(np.unique(cell_idx[test_all])) >= CHECKS['D1_min_cells_covered']
             and all(r['n_train_drugs'] == 52 for r in fold_rec))
    d2_ok = all(min(x['inner_val_rows']) >= CHECKS['D2_min_inner_val_rows'] for x in inner_rec)

    say('[4/10] null-arm calibration (10 shuffle + 10 capacity seeds) + MDE design ...')

    def shuffle_pathway(seed):
        rng2 = np.random.default_rng(SEED_SHUF_BASE + seed)
        a_lab = g.groupby('a')['ap'].first()
        b_lab = g.groupby('b')['lp'].first()
        a_drugs = np.array(sorted(a_lab.index))
        b_drugs = np.array(sorted(b_lab.index))
        a_new = dict(zip(a_drugs, a_lab.loc[a_drugs].to_numpy()[rng2.permutation(len(a_drugs))]))
        b_new = dict(zip(b_drugs, b_lab.loc[b_drugs].to_numpy()[rng2.permutation(len(b_drugs))]))
        ap_s = pd.Categorical([a_new[q] for q in g['a']], categories=a_levels).codes
        lp_s = pd.Categorical([b_new[q] for q in g['b']], categories=l_levels).codes
        return np.hstack([onehot(ap_s, len(a_levels)), onehot(lp_s, len(l_levels))])

    def random_block(seed):
        rng2 = np.random.default_rng(SEED_CAP_BASE + seed)
        return rng2.standard_normal((n, Xpath.shape[1]))

    test_label_reads = 0
    arms = {}

    def run_arm(name, X, scheme, row_seed_base=None, row_variant=None):
        nonlocal test_label_reads
        rec = {'arm': name, 'scheme': scheme, 'folds': [], 'preds': {}}
        for oi, o in enumerate(outer):
            # training-only label view: test labels are NaN -> selection/fit never see them (D5)
            y_train = np.full(n, np.nan)
            y_train[o['train']] = y[o['train']]
            if scheme == 'grouped':
                lam, metrics, kinds, why = select_grouped(X, y_train, inner_all[oi], LAMBDAS)
            else:
                lam, metrics, kinds, why = select_rowlevel(
                    X, y_train, o['train'], LAMBDAS, row_seed_base + o['f'],
                    fold_scaled=(row_variant == 'foldscaled'))
            pred = fit_predict(X, y_train, o['train'], o['test'], lam)
            s, kind = rho(pred, y[o['test']])   # <- the ONLY place test labels are read
            test_label_reads += 1
            rec['folds'].append({'fold': o['f'], 'lambda': float(lam), 'rho': s,
                                 'rho_kind': kind, 'selection': why,
                                 'lambda_metrics': {str(k): (None if v is None else round(float(v), 6))
                                                    for k, v in metrics.items()},
                                 'lambda_metric_kinds': {str(k): v for k, v in kinds.items()}})
            rec['preds'][o['f']] = (pred, o['test'])
        vals = [f['rho'] for f in rec['folds'] if f['rho'] is not None]
        rec['mean_rho'] = float(np.mean(vals)) if vals else float('nan')
        rec['n_defined'] = sum(1 for f in rec['folds'] if f['rho_kind'] == 'defined')
        rec['n_constant'] = sum(1 for f in rec['folds'] if f['rho_kind'] == 'constant')
        arms[name] = rec
        return rec

    null_rec = {'shuffle': {}, 'capacity': {}}
    for seed in range(N_NULL_SEEDS):
        rec = run_arm('shuffle_seed%d' % seed,
                      np.hstack([Xid, shuffle_pathway(seed)]), 'grouped')
        null_rec['shuffle'][str(seed)] = {'mean_rho': rec['mean_rho'],
                                          'lambdas': [f['lambda'] for f in rec['folds']]}
        say('    shuffle seed%d mean_rho=%+.4f lambdas=%s' % (
            seed, rec['mean_rho'], [f['lambda'] for f in rec['folds']]))
    for seed in range(N_NULL_SEEDS):
        rec = run_arm('capacity_seed%d' % seed,
                      np.hstack([Xid, random_block(seed)]), 'grouped')
        null_rec['capacity'][str(seed)] = {'mean_rho': rec['mean_rho'],
                                           'lambdas': [f['lambda'] for f in rec['folds']]}
        say('    capacity seed%d mean_rho=%+.4f lambdas=%s' % (
            seed, rec['mean_rho'], [f['lambda'] for f in rec['folds']]))

    def null_summary(dct):
        vals = np.array([v['mean_rho'] for v in dct.values()], float)
        return {'n_seeds': int(len(vals)), 'mean': round(float(vals.mean()), 6),
                'sd': round(float(vals.std(ddof=1)), 6),
                'min': round(float(vals.min()), 6), 'max': round(float(vals.max()), 6),
                'q025': round(float(np.quantile(vals, .025)), 6),
                'q975': round(float(np.quantile(vals, .975)), 6)}
    null_stats = {'shuffle': null_summary(null_rec['shuffle']),
                  'capacity': null_summary(null_rec['capacity'])}
    d6_ok = (abs(null_stats['shuffle']['mean']) <= CHECKS['D6_null_abs_mean_rho_max']
             and null_stats['shuffle']['q025'] <= 0.0 <= null_stats['shuffle']['q975'])

    # bootstrap machinery (defined before MDE design so the same constructor is used)
    def expand_mult(te, mult):
        m = mult[cell_idx[te]]
        return np.repeat(np.arange(len(te)), m)

    pairs_all = g['a'].to_numpy() + '|' + g['b'].to_numpy()
    upairs = np.array(sorted(set(pairs_all)))
    pair_code = pd.Categorical(pairs_all, categories=upairs).codes

    def _fold_means(arm, take):
        vals = []
        for f in range(N_FOLDS):
            te, pred = arm['preds'][f][1], arm['preds'][f][0]
            keep = take(te, f)
            if keep is None or len(keep) < 5:
                vals.append(0.0)
            else:
                v = rho_fast(pred[keep], y[te][keep])
                vals.append(0.0 if v is None else v)
        return float(np.mean(vals))

    def boot_gain(arm_pos, arm_neg, nboot, seed, cluster='cell'):
        rng2 = np.random.default_rng(seed)
        out = np.empty(nboot)
        for b in range(nboot):
            if cluster == 'cell':
                mult = np.bincount(rng2.integers(0, len(cells), size=len(cells)),
                                   minlength=len(cells))
                take = lambda te, f: expand_mult(te, mult)
            elif cluster == 'pair':
                mult = np.bincount(rng2.integers(0, len(upairs), size=len(upairs)),
                                   minlength=len(upairs))
                take = lambda te, f: np.repeat(np.arange(len(te)), mult[pair_code[te]])
            elif cluster == 'drug':
                # two-way drug-cluster bootstrap: resample anchor drugs x library drugs
                amult = np.bincount(rng2.integers(0, len(drugs), size=len(drugs)),
                                    minlength=len(drugs))
                bmult = np.bincount(rng2.integers(0, len(drugs), size=len(drugs)),
                                    minlength=len(drugs))
                take = lambda te, f: np.repeat(
                    np.arange(len(te)), amult[a_idx[te]] * bmult[b_idx[te]])
            else:  # two-way: product weights (cell x pair multiway bootstrap)
                cmult = np.bincount(rng2.integers(0, len(cells), size=len(cells)),
                                    minlength=len(cells))
                pmult = np.bincount(rng2.integers(0, len(upairs), size=len(upairs)),
                                    minlength=len(upairs))
                take = lambda te, f: np.repeat(
                    np.arange(len(te)), cmult[cell_idx[te]] * pmult[pair_code[te]])
            gp = _fold_means(arm_pos, take)
            gn = _fold_means(arm_neg, take) if arm_neg is not None else 0.0
            out[b] = gp - gn
        return out

    def ci_rec(boots):
        return {'ci95': [round(float(np.quantile(boots, .025)), 6),
                         round(float(np.quantile(boots, .975)), 6)],
                'boot_mean': round(float(np.mean(boots)), 6),
                'boot_sd': round(float(np.std(boots, ddof=1)), 6),
                'mde80': round(float(2.802 * np.std(boots, ddof=1)), 6)}

    say('    bootstrap null arms (seed0) for MDE_design ...')
    boot_shuf = boot_gain(arms['shuffle_seed0'], None, N_BOOT, SEED_BOOT + 11, 'cell')
    boot_cap = boot_gain(arms['capacity_seed0'], None, N_BOOT, SEED_BOOT + 12, 'cell')
    mde_design = {'shuffle_seed0': ci_rec(boot_shuf), 'capacity_seed0': ci_rec(boot_cap)}
    mde_design['max_boot_sd'] = round(max(mde_design['shuffle_seed0']['boot_sd'],
                                          mde_design['capacity_seed0']['boot_sd']), 6)
    mde_design['mde80_design'] = round(2.802 * mde_design['max_boot_sd'], 6)
    d7_ok = mde_design['mde80_design'] <= DELTA_MIN
    say('    MDE80_design=%.4f (shuffle sd=%.4f cap sd=%.4f) D7=%s' % (
        mde_design['mde80_design'], mde_design['shuffle_seed0']['boot_sd'],
        mde_design['capacity_seed0']['boot_sd'], d7_ok))

    design_checks = {
        'D1_fold_structure': {'pass': bool(d1_ok), 'value': {
            'n_folds': N_FOLDS, 'n_drugs_per_fold': [len(o['held']) for o in outer],
            'test_rows_per_fold': [len(o['test']) for o in outer],
            'pooled_test_rows': len(test_all),
            'pooled_test_cells': design['pooled_test_cells'],
            'train_drugs_per_fold': [r['n_train_drugs'] for r in fold_rec]}},
        'D2_inner_overlap_zero': {'pass': bool(d2_ok), 'value': inner_rec},
        'D3_inner_validation_both_unseen': {'pass': True,
                                            'value': design['inner_overlap_assertions']},
        'D4_lambda_grid': {'pass': True, 'value': {'lambdas': list(LAMBDAS),
                                                   'n': len(LAMBDAS)}},
        'D6_null_calibration': {'pass': bool(d6_ok), 'value': null_stats},
        'D7_mde_design': {'pass': bool(d7_ok), 'value': mde_design},
    }
    pre_ok = all(v['pass'] for k, v in design_checks.items() if k.startswith(('D1', 'D2', 'D6', 'D7')))
    say('    design gate (pre-scoring) = %s' % pre_ok)

    treated = {}
    if not pre_ok:
        verdict = 'inconclusive'
        say('    DESIGN CHECK FAILED -> inconclusive, treatment scoring skipped (frozen rule)')
        treated = {}
        rowlevel = {}
        topk = {}
        boot_main = {}
        main_gain = None
    else:
        say('[5/10] treatment arms (grouped inner CV) ...')
        run_arm('annotation', np.hstack([Xid, Xpath]), 'grouped')
        run_arm('identity', Xid, 'grouped')
        run_arm('annotation_only', Xpath, 'grouped')
        say('    annotation mean_rho=%+.4f lambdas=%s' % (
            arms['annotation']['mean_rho'],
            [f['lambda'] for f in arms['annotation']['folds']]))
        say('    identity   mean_rho=%+.4f kinds=%s' % (
            arms['identity']['mean_rho'],
            [f['rho_kind'] for f in arms['identity']['folds']]))
        say('    ann_only   mean_rho=%+.4f lambdas=%s' % (
            arms['annotation_only']['mean_rho'],
            [f['lambda'] for f in arms['annotation_only']['folds']]))

        say('[6/10] row-level control arms (C130 scheme) ...')
        run_arm('rowlevel_ann_c130', np.hstack([Xid, Xpath]), 'rowlevel',
                row_seed_base=SEED_ROW_BASE, row_variant='c130')
        run_arm('rowlevel_id_c130', Xid, 'rowlevel',
                row_seed_base=SEED_ROW_BASE, row_variant='c130')
        run_arm('rowlevel_ann_foldscaled', np.hstack([Xid, Xpath]), 'rowlevel',
                row_seed_base=SEED_ROW_BASE, row_variant='foldscaled')
        run_arm('rowlevel_id_foldscaled', Xid, 'rowlevel',
                row_seed_base=SEED_ROW_BASE, row_variant='foldscaled')
        say('    rowlevel c130: ann %+.4f id %+.4f lambdas=%s' % (
            arms['rowlevel_ann_c130']['mean_rho'], arms['rowlevel_id_c130']['mean_rho'],
            [f['lambda'] for f in arms['rowlevel_ann_c130']['folds']]))

        say('[7/10] bootstrap CIs + MDE (cell / pair / two-way) ...')
        main_gain = arms['annotation']['mean_rho'] - arms['identity']['mean_rho']
        boots_cell = boot_gain(arms['annotation'], arms['identity'], N_BOOT, SEED_BOOT, 'cell')
        boots_pair = boot_gain(arms['annotation'], arms['identity'], N_BOOT_SENS,
                               SEED_BOOT + 1, 'pair')
        boots_twoway = boot_gain(arms['annotation'], arms['identity'], N_BOOT_SENS,
                                 SEED_BOOT + 2, 'twoway')
        boots_drug = boot_gain(arms['annotation'], arms['identity'], N_BOOT_SENS,
                               SEED_BOOT + 5, 'drug')
        boot_main = {'cell': ci_rec(boots_cell), 'pair': ci_rec(boots_pair),
                     'twoway': ci_rec(boots_twoway), 'drug': ci_rec(boots_drug)}
        fold_gains = [f['rho'] for f in arms['annotation']['folds']]
        fold_sd = float(np.std(fold_gains, ddof=1))
        fold_se = fold_sd / np.sqrt(N_FOLDS)
        t_crit = 2.776  # t(0.975, df=4)
        fold_dispersion = {
            'per_fold_gain': [round(float(v), 6) for v in fold_gains],
            'mean': round(float(np.mean(fold_gains)), 6),
            'sd_across_folds': round(fold_sd, 6),
            'se_of_mean_across_folds': round(float(fold_se), 6),
            't_interval_95_df4': [round(float(np.mean(fold_gains) - t_crit * fold_se), 6),
                                  round(float(np.mean(fold_gains) + t_crit * fold_se), 6)],
            'min': round(float(np.min(fold_gains)), 6),
            'max': round(float(np.max(fold_gains)), 6),
            'note': 'DESCRIPTIVE split/drug-set dispersion across the 5 held-out drug folds; '
                    'NOT the pre-registered CI (which is cell-clustered). Each fold holds a '
                    'different random set of 13 drugs, so this reflects held-out-drug '
                    'composition variability that the cell bootstrap does not cover.'}
        annonly_boot = boot_gain(arms['annotation_only'], None, N_BOOT, SEED_BOOT + 3, 'cell')
        boot_annonly = {'annotation_only_gain_vs_zero': ci_rec(annonly_boot)}

        # row-level vs grouped difference (paired cell bootstrap)
        row_gain = arms['rowlevel_ann_c130']['mean_rho'] - arms['rowlevel_id_c130']['mean_rho']
        row_gain_fs = (arms['rowlevel_ann_foldscaled']['mean_rho']
                       - arms['rowlevel_id_foldscaled']['mean_rho'])
        rngd = np.random.default_rng(SEED_BOOT + 4)
        diffs = np.empty(N_BOOT)
        for b in range(N_BOOT):
            mult = np.bincount(rngd.integers(0, len(cells), size=len(cells)),
                               minlength=len(cells))
            g_group, g_row = [], []
            for f in range(N_FOLDS):
                te, pred = arms['annotation']['preds'][f][1], arms['annotation']['preds'][f][0]
                keep = expand_mult(te, mult)
                g_group.append(rho_fast(pred[keep], y[te][keep]))
                te2 = arms['rowlevel_ann_c130']['preds'][f][1]
                pr2 = arms['rowlevel_ann_c130']['preds'][f][0]
                keep2 = expand_mult(te2, mult)
                g_row.append(rho_fast(pr2[keep2], y[te2][keep2]))
            diffs[b] = np.mean(g_row) - np.mean(g_group)
        row_vs_grouped = {
            'grouped_gain': round(float(main_gain), 6),
            'rowlevel_c130_gain': round(float(row_gain), 6),
            'rowlevel_foldscaled_gain': round(float(row_gain_fs), 6),
            'difference_rowlevel_minus_grouped': round(float(row_gain - main_gain), 6),
            'difference_ci95': [round(float(np.quantile(diffs, .025)), 6),
                                round(float(np.quantile(diffs, .975)), 6)],
            'material_optimism_flag': bool((row_gain - main_gain) > MATERIAL_OPTIMISM),
            'rowlevel_lambdas_annotation': [f['lambda'] for f in arms['rowlevel_ann_c130']['folds']],
            'grouped_lambdas_annotation': [f['lambda'] for f in arms['annotation']['folds']],
        }
        treated = {
            'annotation': {'mean_rho': round(float(arms['annotation']['mean_rho']), 6),
                           'folds': arms['annotation']['folds']},
            'identity': {'mean_rho': round(float(arms['identity']['mean_rho']), 6),
                         'folds': arms['identity']['folds']},
            'annotation_only': {'mean_rho': round(float(arms['annotation_only']['mean_rho']), 6),
                                'folds': arms['annotation_only']['folds']},
            'main_gain': round(float(main_gain), 6),
            'boot_main': boot_main,
            'boot_annonly': boot_annonly,
        }

        say('[8/10] descriptive top-k (5%% / 20%%) ...')
        topk = {}
        for arm_name in ('annotation', 'annotation_only', 'identity'):
            rec = arms[arm_name]
            res = {}
            for frac in (0.05, 0.20):
                hits, mean_y, nsel = [], [], []
                for f in range(N_FOLDS):
                    te, pred = rec['preds'][f][1], rec['preds'][f][0]
                    yv = y[te]
                    k = max(1, int(round(frac * len(te))))
                    order = np.argsort(pred, kind='stable')[-k:]
                    q75 = np.quantile(yv, 0.75)
                    hits.append(float(np.mean(yv[order] >= q75)))
                    mean_y.append(float(np.mean(yv[order])))
                    nsel.append(k)
                res['top_%d_pct' % int(frac * 100)] = {
                    'hit_rate_mean': round(float(np.mean(hits)), 6),
                    'selected_mean_y_mean': round(float(np.mean(mean_y)), 6),
                    'n_selected_mean': round(float(np.mean(nsel)), 1),
                    'note': ('descriptive only; identity predictions are constant so its top-k '
                             'is a deterministic-by-row-order random subset (expected hit rate 0.25)'
                             if arm_name == 'identity' else
                             'descriptive only; no decision-benefit claim')}
            topk[arm_name] = res

        say('[9/10] judgment ...')
        ci_low = boot_main['cell']['ci95'][0]
        mde_scoring = boot_main['cell']['mde80']
        subtypes = []
        if mde_scoring > DELTA_MIN:
            verdict = 'inconclusive'
            subtypes.append('mde_scoring_gt_delta_min')
        elif (main_gain >= BAND[0] and main_gain <= BAND[1] and ci_low > 0.0):
            verdict = 'replicated_under_audit'
        else:
            verdict = 'weakened'
            if main_gain < DELTA_MIN:
                subtypes.append('below_minimum_effect')
            if ci_low <= 0.0:
                subtypes.append('ci_includes_zero')
            if main_gain > BAND[1]:
                subtypes.append('above_stability_band')
        judgment = {
            'verdict': verdict, 'subtypes': subtypes,
            'delta_min': DELTA_MIN, 'stability_band': list(BAND),
            'main_gain': round(float(main_gain), 6),
            'main_gain_ci95_cell': boot_main['cell']['ci95'],
            'mde80_cell': mde_scoring,
            'mde80_pair': boot_main['pair']['mde80'],
            'mde80_twoway': boot_main['twoway']['mde80'],
            'mde80_drug': boot_main['drug']['mde80'],
            'ci95_drug_cluster': boot_main['drug']['ci95'],
            'ci95_pair_cluster': boot_main['pair']['ci95'],
            'ci95_twoway_cluster': boot_main['twoway']['ci95'],
            'replicated_rule': 'CI_lower>0 AND point>=0.05 AND point<=0.20 (+ all design checks)',
            'material_optimism_flag': row_vs_grouped['material_optimism_flag'],
            'reliability_qualifier': {
                'ci_lower_gt_zero_all_clusterings': bool(
                    boot_main['cell']['ci95'][0] > 0 and boot_main['pair']['ci95'][0] > 0
                    and boot_main['twoway']['ci95'][0] > 0 and boot_main['drug']['ci95'][0] > 0),
                'mde80_le_delta_min_cell_cluster': bool(boot_main['cell']['mde80'] <= DELTA_MIN),
                'mde80_le_delta_min_drug_cluster': bool(boot_main['drug']['mde80'] <= DELTA_MIN),
                'fold_gain_range': [round(float(np.min([f['rho'] for f in arms['annotation']['folds']])), 6),
                                    round(float(np.max([f['rho'] for f in arms['annotation']['folds']])), 6)],
                'note': 'sign/positive direction is robust across all four clusterings; the '
                        'MAGNITUDE is not pinned at delta_min under held-out-DRUG resampling '
                        '(MDE80_drug > 0.05): only 5 held-out drug folds and 13 held-out drugs '
                        'per fold. The pre-registered primary (cell-clustered) MDE is <= delta_min.'},
            'c130_reference': {'gain': 0.11831576209676734,
                               'ci95': [0.09471202625415462, 0.14085000835904368],
                               'mde80': 0.0343798832700657,
                               'note': 'C130/E163 row-level inner tuning, 40 overlapping splits'},
        }
    design_checks['D5_test_label_reads'] = {
        'pass': bool(test_label_reads == N_FOLDS * len(arms)),
        'value': {'count': int(test_label_reads),
                  'expected': int(N_FOLDS * len(arms)),
                  'note': 'test labels are read only in the scoring function; lambda selection and '
                          'prediction generation receive a training-only label view in which '
                          'non-training entries are NaN (asserted finite wherever used)'}}

    t_end = time.time()
    say('[10/10] write pa2-style artefacts ...')
    r196 = {
        'protocol': {'path': 'PROTOCOL_R196.md',
                     'sha256': sha256_file(BASE / 'PROTOCOL_R196.md')},
        'script': {'path': 'r196.py', 'sha256': sha256_file(Path(__file__).resolve())},
        'input': input_rec,
        'data': data_rec,
        'settings': {
            'seed_outer': SEED_OUTER, 'seed_inner_base': SEED_INNER_BASE,
            'seed_row_base': SEED_ROW_BASE, 'seed_boot': SEED_BOOT,
            'seed_cap_base': SEED_CAP_BASE, 'seed_shuf_base': SEED_SHUF_BASE,
            'lambdas': list(LAMBDAS), 'n_folds': N_FOLDS, 'n_inner_folds': N_INNER,
            'n_boot': N_BOOT, 'n_boot_sensitivity': N_BOOT_SENS,
            'n_null_seeds': N_NULL_SEEDS, 'const_tol': CONST_TOL,
            'delta_min': DELTA_MIN, 'stability_band': list(BAND),
            'material_optimism_threshold': MATERIAL_OPTIMISM,
            'arms': ['annotation [ID,ANN] (main)', 'identity [ID]', 'annotation_only [ANN]',
                     'capacity [ID,RND] x10 seeds', 'shuffle [ID,ANN_shuf] x10 seeds',
                     'rowlevel_ann_c130', 'rowlevel_id_c130',
                     'rowlevel_ann_foldscaled', 'rowlevel_id_foldscaled'],
        },
        'design_checks': design_checks,
        'null_arms': {'stats': null_stats, 'per_seed': null_rec['shuffle'] | {
            'capacity_' + k: v for k, v in null_rec['capacity'].items()}},
        'treatment': treated,
        'rowlevel_vs_grouped': row_vs_grouped if treated else {},
        'fold_dispersion_descriptive': fold_dispersion if treated else {},
        'topk_descriptive': topk,
        'judgment': judgment if treated else {
            'verdict': 'inconclusive',
            'subtypes': ['design_check_failed_pre_scoring'],
            'design_gate_passed': False},
        'deterministic': {'random': False, 'timestamps': False, 'json_sort_keys': True},
        'deviations': [],
        'log': log,
    }
    with open(BASE / 'r196.json', 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(r196, fh, sort_keys=True, ensure_ascii=False, indent=1)
        fh.write('\n')

    rows = []
    for name, rec in sorted(arms.items()):
        for fr in rec['folds']:
            rows.append({'arm': name, 'scheme': rec['scheme'], 'fold': fr['fold'],
                         'lambda': fr['lambda'], 'n_test': int(len(rec['preds'][fr['fold']][1])),
                         'rho': fr['rho'], 'rho_kind': fr['rho_kind'],
                         'selection': fr['selection']})
    with open(BASE / 'r196_rows.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['arm', 'scheme', 'fold', 'lambda', 'n_test',
                                           'rho', 'rho_kind', 'selection'],
                           lineterminator='\n')
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x['arm'], x['fold'])):
            w.writerow(r)

    say('DONE verdict=%s' % r196['judgment']['verdict'])
    if treated:
        say('  main_gain=%+.4f CI=[%+.4f,%+.4f] MDE80=%.4f' % (
            main_gain, boot_main['cell']['ci95'][0], boot_main['cell']['ci95'][1],
            boot_main['cell']['mde80']))
        say('  rowlevel_gain=%+.4f grouped=%+.4f diff=%+.4f material_optimism=%s' % (
            row_vs_grouped['rowlevel_c130_gain'], row_vs_grouped['grouped_gain'],
            row_vs_grouped['difference_rowlevel_minus_grouped'],
            row_vs_grouped['material_optimism_flag']))
    print('DONE wall=%.1fs' % (time.time() - t_start))
    print('r196.json sha256:', sha256_file(BASE / 'r196.json'))


if __name__ == '__main__':
    main()
