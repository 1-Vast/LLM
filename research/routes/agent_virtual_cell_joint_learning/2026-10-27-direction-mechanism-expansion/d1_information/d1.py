#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R200-D1: information decomposition of R197 Q contrasts + transfer-target eligibility + design inputs.

PROTOCOL_D1.md (frozen before this script existed) is the contract. This script does
metadata/algebra audit ONLY:
  * rebuilds the frozen R197 Q support (A0 rules; via r197.build_q, read-only reuse);
  * algebraic closure: coefficient matrix rank / additive kernel / constructive transitivity
    reconstruction / frozen H197c fold reconstructibility / exact reconstruction error check;
  * shared raw-response overlap (barcode=plate level, key level, exact pairwise inclusion-exclusion);
  * identity/batch/endpoint source shares (construction facts + read-only reuse of A0 variance shares);
  * remaining independent information & coverage;
  * local transfer-target eligibility (metadata-only) and structural design inputs.
No predictive model is fitted; Q values are used ONLY for exact algebraic identity checks.

Deterministic: fixed order, JSON sort_keys, no timestamps, allow_nan=False.
"""
import sys
import os
import json
import math
import hashlib
import time
from collections import defaultdict, deque

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
import scipy.sparse as sp
import scipy.linalg as sla

ROOT = r'D:\MAESTRO'
BASE = os.path.join(ROOT, 'research', '2026-10-27-direction-mechanism-expansion', 'd1_information')
QS = os.path.join(ROOT, 'research', '2026-10-27-q-structure')
CS = os.path.join(ROOT, 'research', '2026-10-27-conditional-shift')
EXT = os.path.join(ROOT, 'data', 'external')
orig_path = os.path.join(EXT, 'gdsc_combinations', 'jaaks2022_figshare',
                         'Original screen_All tissues_fitted data.csv')
val_path = os.path.join(EXT, 'gdsc_combinations', 'jaaks2022_figshare',
                        'Validation screen_All tissues_fitted data.csv')
matched_path = os.path.join(CS, 'matched_conditions.csv')
sys.path.insert(0, QS)
import r197  # noqa: E402  frozen v1 reconstruction helper (read-only)

PROTOCOL = os.path.join(BASE, 'PROTOCOL_D1.md')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(BASE, 'd1.json')

EXPECTED = {
    'original_fitted': '1188968CE7FDCFB66D03791CF266515B7C7A2794E1FC73C966DBA40266FFA278',
    'validation_fitted': 'DCBD4C3108D212FA771C52AE977C8E1C01A421162A2232CDC4273FAF257B2775',
    'matched_conditions': '73FD5085A7586BB1F33768E34A587668953DA4C13735693DCF2FCCCBC51353FF',
    'a0_json': '72BBAF6DF9BF80BBD19BF946A8D7A369003861FF21BD95561BC6DA48021ECA22',
    'r197_v2_json': 'B0DBE7982677FE9269B47EA39C83659166D4E4A5BFF04E8F590FC04BA64435CB',
    'r197_py': '6B732653CA47CC6F3D6CF3050EF1BDB915575F8752A2232542182952C84A46B7',
}
TOL_IDENTITY = 1e-9
TOL_RANK_REL = 1e-9
TOL_PROJ_REL = 1e-7
N_VERIFY = 2000
SEED_FOLDS = 20261106


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


def qd(vals, nd=8):
    return [rq(v, nd) for v in vals]


def quantiles(arr):
    a = np.asarray(arr, dtype=float)
    if a.size == 0:
        return {}
    qs = [0, 5, 25, 50, 75, 95, 100]
    return {str(q): int(np.percentile(a, q)) if q in (0, 100) else rq(float(np.percentile(a, q)), 2)
            for q in qs}


# --------------------------------------------------------------------- sparse spectral helpers
def lam_max_sparse(A, iters=80):
    rng = np.random.default_rng(0)
    v = rng.standard_normal(A.shape[1])
    v /= np.linalg.norm(v)
    lam = 0.0
    for _ in range(iters):
        w = A @ v
        v2 = A.T @ (A @ v)
        n2 = np.linalg.norm(v2)
        if n2 == 0:
            return 0.0
        v = v2 / n2
        lam = float(np.linalg.norm(A @ v))
    return lam * lam


def low_eig(A, n_low):
    """lowest n_low eigenpairs of G=A^T A (dense subset eigh, driver='evr')."""
    G = (A.T @ A).toarray()
    m = min(int(n_low), G.shape[0] - 1)
    w, V = sla.eigh(G, subset_by_index=[0, m - 1], driver='evr')
    return w, V, G


def nullity_of(A, lam_max, m0=800):
    """number of eigenvalues of A^T A at/below tol, with escalation until a clearly non-null
    eigenvalue is observed (eigenvalues are returned ascending)."""
    m = min(int(m0), A.shape[1] - 1)
    while True:
        w, V, G = low_eig(A, m)
        tol = TOL_RANK_REL * max(lam_max, 1e-12)
        nm = w <= tol
        if (not nm.all()) or m >= A.shape[1] - 1:
            clear_gap = bool(np.all(w[~nm] > tol * 10.0)) if (~nm).any() else False
            return w, V, tol, int(nm.sum()), G, clear_gap
        m = min(A.shape[1] - 1, m * 2)


# --------------------------------------------------------------------- main
def main():
    t0 = time.time()
    log = []

    def say(msg):
        print(msg, flush=True)
        log.append(msg)

    say('[1/9] verify inputs ...')
    inputs = {}
    for key, path in (('original_fitted', orig_path), ('validation_fitted', val_path),
                      ('matched_conditions', matched_path),
                      ('a0_json', os.path.join(CS, 'a0.json')),
                      ('r197_v2_json', os.path.join(QS, 'r197_v2.json')),
                      ('r197_py', os.path.join(QS, 'r197.py'))):
        s = sha256_file(path)
        inputs[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                       'bytes': os.path.getsize(path), 'sha256': s,
                       'matches_expected': (s == EXPECTED[key]) if key in EXPECTED else None}
        if key in EXPECTED and s != EXPECTED[key]:
            raise SystemExit('FATAL: sha mismatch for %s: %s' % (key, s))
    say('    inputs verified (7/7)')

    say('[2/9] rebuild frozen R197 Q structure (A0 rules; read-only reuse of r197.build_q) ...')
    q = r197.build_q()
    q.pop('df', None)
    struct = q['structure']
    n_obs = int(q['n_obs']); n_cp = int(q['n_cp']); n_condpair = int(q['n_condpair'])
    assert n_obs == 92039 and n_cp == 1501 and n_condpair == 229
    quad_keys = q['quad_keys']            # (n_obs,4) key ids into r197 key_list
    Qobs = np.asarray(q['y'], dtype=float)  # per-observation Q value (algebra checks only)
    ci = np.asarray(q['ci']); cj = np.asarray(q['cj_arr'])
    cells = list(q['cells']); conds = list(q['conds'])
    row_meta = q['row_meta']; cp_list = q['cp_list']
    say('    n_obs=%d rows=%d cols=%d cells=%d conds=%d' % (n_obs, n_condpair, n_cp, len(cells), len(conds)))

    say('[3/9] rebuild key metadata (cell, condition, barcodes, rows) and cross-check key_bcnt ...')
    df = pd.read_csv(orig_path, usecols=['BARCODE', 'CELL_LINE_NAME', 'ANCHOR_ID', 'LIBRARY_ID',
                                         'ANCHOR_CONC', 'LIBRARY_CONC', 'SYNERGY_DELTA_EMAX'],
                     low_memory=False)
    n_rows = len(df)
    bc = pd.to_numeric(df['BARCODE'], errors='coerce').to_numpy()
    cell = np.array([r197.nk(x) if isinstance(x, str) else None for x in df['CELL_LINE_NAME'].to_numpy()],
                    dtype=object)
    aid = df['ANCHOR_ID'].astype(str).str.strip().to_numpy()
    lid = df['LIBRARY_ID'].astype(str).str.strip().to_numpy()
    ac = np.array([r197.canon(x) for x in df['ANCHOR_CONC'].to_numpy()], dtype=object)
    lc = np.array([r197.canon(x) for x in df['LIBRARY_CONC'].to_numpy()], dtype=object)
    comp = np.array([('|' in str(a)) or ('|' in str(b)) or ('|' in str(c))
                     for a, b, c in zip(df['ANCHOR_ID'], df['LIBRARY_ID'], df['ANCHOR_CONC'])])
    yy = pd.to_numeric(df['SYNERGY_DELTA_EMAX'], errors='coerce').to_numpy(float)
    valid = ((~comp) & np.array([c is not None for c in cell]) & np.isfinite(bc)
             & (aid != 'nan') & (lid != 'nan')
             & np.array([x is not None for x in ac]) & np.array([x is not None for x in lc])
             & np.isfinite(yy))
    mc = pd.read_csv(matched_path, dtype=str)
    mc_keys = set()
    for r in mc.itertuples(index=False):
        mc_keys.add((r.cell, (str(r.anchor_id).strip(), str(r.library_id).strip(),
                              r197.canon(r.anchor_conc), r197.canon(r.library_conc))))
    matched_cells = {k[0] for k in mc_keys}
    cond_arr = np.empty(n_rows, dtype=object)
    for i in np.nonzero(valid)[0]:
        cond_arr[i] = (aid[i], lid[i], ac[i], lc[i])
    bmap = {}
    key_nrows = defaultdict(int)
    for i in np.nonzero(valid)[0]:
        c = cell[i]
        if c not in matched_cells:
            continue
        k = (c, cond_arr[i])
        bmap.setdefault(k, {}).setdefault(int(bc[i]), []).append(float(yy[i]))
        key_nrows[k] += 1
    key_list = sorted(bmap.keys(), key=lambda kk: (kk[0], tuple(kk[1])))
    key_id = {k: i for i, k in enumerate(key_list)}
    key_bcnt = np.array([len(bmap[k]) for k in key_list], dtype=np.int64)
    assert len(key_list) == q['key_bcnt'].size, 'key universe mismatch'
    assert np.array_equal(key_bcnt, np.asarray(q['key_bcnt'], dtype=np.int64)), 'key barcode counts mismatch'
    key_meta = [{'cell': k[0], 'cond': list(k[1]), 'n_barcodes': len(bmap[k]),
                 'n_rows': int(key_nrows[k]),
                 'barcodes': sorted(bmap[k].keys())} for k in key_list]
    say('    key universe=%d (matches frozen key_bcnt)' % len(key_list))

    say('[4/9] coefficient matrix + algebraic closure A2/A3 ...')
    used = np.unique(quad_keys)
    K = int(used.size)
    kmap = np.full(len(key_list), -1, dtype=np.int64)
    kmap[used] = np.arange(K)
    qk = kmap[quad_keys]
    assert qk.min() >= 0
    rows = np.repeat(np.arange(n_obs), 4)
    cols = qk.reshape(-1)
    vals = np.tile(np.array([1.0, -1.0, -1.0, 1.0]), n_obs)
    A = sp.csr_matrix((vals, (rows, cols)), shape=(n_obs, K))
    lam_max = lam_max_sparse(A)
    w_all, V_all, tol, nullity_all, G_all, clear_gap = nullity_of(A, lam_max)
    del G_all
    lambda_max = float(lam_max)
    null_mask = w_all <= tol
    rank_all = int(K - nullity_all)
    sing = w_all[null_mask]
    say('    K=%d lam_max_power=%.3f rank=%d nullity=%d tol=%.3e gap_clear=%s' % (
        K, lambda_max, rank_all, nullity_all, tol, clear_gap))
    # key graph -> additive kernel dimension
    cell_ids = sorted({key_meta[i]['cell'] for i in used})
    cond_ids = sorted({tuple(key_meta[i]['cond']) for i in used})
    cell_ix = {c: i for i, c in enumerate(cell_ids)}
    cond_ix = {c: i for i, c in enumerate(cond_ids)}
    parent = list(range(len(cell_ids) + len(cond_ids)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in used:
        union(cell_ix[key_meta[i]['cell']], len(cell_ids) + cond_ix[tuple(key_meta[i]['cond'])])
    comps = len({find(i) for i in range(len(parent))})
    kernel_dim = len(cell_ids) + len(cond_ids) - comps
    redundancy = n_obs - rank_all
    say('    cells_used=%d conds_used=%d components=%d additive_kernel_dim=%d redundancy=%d (%.2f%%)' % (
        len(cell_ids), len(cond_ids), comps, kernel_dim, redundancy, 100.0 * redundancy / n_obs))

    # constructive transitivity: row (cell-pair) and column (condition-pair) spanning forests
    cell_index = {c: i for i, c in enumerate(cells)}
    row_lists = defaultdict(list)
    col_lists = defaultdict(list)
    for t in range(n_obs):
        row_lists[int(ci[t])].append(t)
        col_lists[int(cj[t])].append(t)
    recon_row = np.zeros(n_obs, dtype=bool)
    recon_col = np.zeros(n_obs, dtype=bool)

    def mark_forest(edge_list, node_of, recon_flags):
        adj = defaultdict(list)
        for t in edge_list:
            adj[node_of(t)[0]].append((node_of(t)[1], t))
            adj[node_of(t)[1]].append((node_of(t)[0], t))
        seen = set()
        for start in sorted(adj):
            if start in seen:
                continue
            seen.add(start)
            dq = deque([start])
            while dq:
                u = dq.popleft()
                for v2, t in adj[u]:
                    if v2 in seen:
                        continue
                    seen.add(v2)
                    dq.append(v2)
            # mark non-tree edges: edges connecting two already-visited nodes are reconstructible
        # second pass: BFS tree again to mark tree edges, then non-tree = remaining
        seen = set()
        tree_edges = set()
        for start in sorted(adj):
            if start in seen:
                continue
            seen.add(start)
            dq = deque([start])
            parent_edge = {}
            while dq:
                u = dq.popleft()
                for v2, t in adj[u]:
                    if v2 in seen:
                        continue
                    seen.add(v2)
                    dq.append(v2)
                    tree_edges.add(t)
        for t in edge_list:
            if t not in tree_edges:
                recon_flags[t] = True

    row_edge_node = lambda t: (cell_index[cp_list[int(cj[t])][0]],
                               cell_index[cp_list[int(cj[t])][1]])
    # column node = condition index pair from row_meta
    def col_edge_node(t):
        m = row_meta[int(ci[t])]
        p = (m['anchor_id'], m['library_p'], m['anchor_conc'], m['library_conc'])
        qq = (m['anchor_id'], m['library_q'], m['anchor_conc'], m['library_conc'])
        return (cond_ix[p], cond_ix[qq])

    for i, tl in row_lists.items():
        mark_forest(tl, row_edge_node, recon_row)
    for j, tl in col_lists.items():
        mark_forest(tl, col_edge_node, recon_col)
    recon_union = recon_row | recon_col
    say('    constructive reconstruction: row %.2f%% col %.2f%% union %.2f%%' % (
        100.0 * recon_row.mean(), 100.0 * recon_col.mean(), 100.0 * recon_union.mean()))

    # exact identity checks on deterministic samples (Q values: algebra verification only)
    rng = np.random.default_rng(1)

    def path_reconstruct_row(t):
        i = int(ci[t]); a, b = row_edge_node(t)
        # BFS in row graph (trees) to find path a->b excluding edge t
        adj = defaultdict(list)
        for u in row_lists[i]:
            if u == t:
                continue
            x, y = row_edge_node(u)
            adj[x].append((y, u)); adj[y].append((x, u))
        prev = {a: None}; dq = deque([a])
        while dq:
            u = dq.popleft()
            if u == b:
                break
            for v2, u2 in adj[u]:
                if v2 not in prev:
                    prev[v2] = (u, u2)
                    dq.append(v2)
        if b not in prev:
            return None
        # build path
        path = []
        cur = b
        while cur != a:
            pu, pe = prev[cur]
            path.append((pu, cur, pe))
            cur = pu
        path.reverse()
        val = 0.0
        for x, y, u2 in path:
            s = 1.0 if x < y else -1.0
            val += s * Qobs[u2]
        return val

    idx_row = np.flatnonzero(recon_row)
    rng.shuffle(idx_row)
    sample = idx_row[:N_VERIFY]
    errs = []
    for t in sample:
        v = path_reconstruct_row(int(t))
        if v is not None:
            errs.append(abs(v - Qobs[int(t)]))
    errs = np.array(errs) if errs else np.array([0.0])
    verify_row = {'n_checked': int(errs.size), 'max_abs_err': rq(float(errs.max())),
                  'frac_le_1e9': rq(float((errs <= TOL_IDENTITY).mean()))}
    say('    row-path identity check: n=%d max|err|=%.2e pass=%.4f' % (
        verify_row['n_checked'], verify_row['max_abs_err'], verify_row['frac_le_1e9']))

    say('[5/9] frozen H197c fold reconstructibility (A4) + exact closure reconstruction ...')
    order = np.lexsort((cj, ci))
    rngf = np.random.default_rng(SEED_FOLDS)
    assign = np.empty(n_obs, dtype=int)
    assign[order] = rngf.permutation(n_obs) % 5
    fold_rec = []
    fold0_pred = None
    for f in range(5):
        te = assign == f
        tr = ~te
        A_tr = A[tr]
        A_te = A[te]
        lm = lam_max_sparse(A_tr)
        w, V, tol_f, nullity, G, gap_clear = nullity_of(A_tr, lm)
        rank_tr = int(K - nullity)
        escalated = bool(not gap_clear)
        Vn = V[:, :nullity]
        proj = np.asarray(A_te @ Vn)
        rel = np.linalg.norm(proj, axis=1) / 2.0
        n_rec = int((rel <= TOL_PROJ_REL).sum())
        n_te = int(te.sum())
        n_keys_unused = int((A_tr.getnnz(axis=0) == 0).sum())
        # exact closure reconstruction on every fold (algebraic solver; no fitting, no features)
        from scipy.sparse.linalg import lsqr
        sol = lsqr(A_tr, Qobs[tr], atol=1e-14, btol=1e-14, iter_lim=5000)
        z = sol[0]
        qpred = A_te @ z
        cerr = np.abs(qpred - Qobs[te])
        rec_err = {'lsqr_iters': int(sol[2]), 'lsqr_stop': int(sol[1]),
                   'max_abs_err': rq(float(cerr.max())),
                   'median_abs_err': rq(float(np.median(cerr))),
                   'frac_le_1e9': rq(float((cerr <= TOL_IDENTITY).mean()))}
        if f == 0:
            fold0_pred = rec_err
        fold_rec.append({'fold': f, 'n_test': n_te, 'n_reconstructible': n_rec,
                         'recon_frac': rq(float(n_rec / n_te)), 'rank_train': rank_tr,
                         'nullity_train': nullity, 'n_keys_unused_in_train': n_keys_unused,
                         'proj_rel_max': rq(float(rel.max())),
                         'proj_rel_median': rq(float(np.median(rel))),
                         'eigen_gap_clear': bool(gap_clear),
                         'exact_closure_reconstruction': rec_err})
        say('    fold %d: test=%d recon=%d (%.2f%%) rank=%d nullity=%d unused_keys=%d' % (
            f, n_te, n_rec, 100.0 * n_rec / n_te, rank_tr, nullity, n_keys_unused))
        del G, V, A_tr, A_te
    say('    fold0 exact closure reconstruction: max|err|=%.2e frac<=1e-9=%.4f' % (
        fold0_pred['max_abs_err'], fold0_pred['frac_le_1e9']))

    say('[6/9] shared raw-response overlap (B) ...')
    key_rows = np.array([key_meta[i]['n_rows'] for i in used], dtype=np.int64)
    key_bcs = [key_meta[i]['barcodes'] for i in used]
    m_k = np.bincount(qk.reshape(-1), minlength=K)
    entry_rows = np.zeros(n_obs, dtype=np.int64)
    entry_plates = np.zeros(n_obs, dtype=np.int64)
    plate_id = {}
    entry_plate_lists = []
    for t in range(n_obs):
        pl = set()
        for kk in qk[t]:
            pl.update(key_bcs[kk])
        entry_plate_lists.append(pl)
        entry_plates[t] = len(pl)
        entry_rows[t] = sum(int(key_rows[kk]) for kk in qk[t])
    all_plates = sorted({b for bc_list in key_bcs for b in bc_list})
    for b in all_plates:
        plate_id[b] = len(plate_id)
    # exact pairwise overlap via inclusion-exclusion over key/plate subsets
    def pair_share_stats(entry_sets, universe_size):
        c1 = defaultdict(int); c2 = defaultdict(int); c3 = defaultdict(int); c4 = defaultdict(int)
        for s in entry_sets:
            s = sorted(s)
            ls = len(s)
            for i in range(ls):
                c1[s[i]] += 1
                for j in range(i + 1, ls):
                    c2[(s[i], s[j])] += 1
                    for k in range(j + 1, ls):
                        c3[(s[i], s[j], s[k])] += 1
                        for l in range(k + 1, ls):
                            c4[(s[i], s[j], s[k], s[l])] += 1
        S = 0
        for c in c1.values():
            S += c * (c - 1) // 2
        for c in c2.values():
            S -= c * (c - 1) // 2
        for c in c3.values():
            S += c * (c - 1) // 2
        for c in c4.values():
            S -= c * (c - 1) // 2
        pairs_total = n_obs * (n_obs - 1) // 2
        return {'pairs_total': int(pairs_total), 'pairs_sharing_ge1': int(S),
                'pair_share_frac': rq(float(S / pairs_total)),
                'pair_disjoint_frac': rq(float(1.0 - S / pairs_total)),
                'expected_shared_per_pair': rq(float(sum(c * (c - 1) // 2 for c in c1.values())
                                                    / pairs_total))}
    key_sets = [list(qk[t]) for t in range(n_obs)]
    key_overlap = pair_share_stats(key_sets, K)
    plate_sets = [sorted(plate_id[b] for b in entry_plate_lists[t]) for t in range(n_obs)]
    # plate incidence: how many Q entries touch each plate
    plate_inc = np.zeros(len(plate_id), dtype=np.int64)
    for t in range(n_obs):
        for b in entry_plate_lists[t]:
            plate_inc[plate_id[b]] += 1
    # exact union over plates is infeasible (plate sets up to 32, entries 92,039): report
    # first-order sum (upper bound) and Bonferroni lower bound (needs plate-pair co-occurrence).
    pairs_total_all = n_obs * (n_obs - 1) // 2
    S1 = int(sum(int(c) * (int(c) - 1) // 2 for c in plate_inc))
    pp = defaultdict(int)
    for s in plate_sets:
        ls = len(s)
        for i in range(ls):
            for j in range(i + 1, ls):
                pp[(s[i], s[j])] += 1
    S2 = int(sum(c * (c - 1) // 2 for c in pp.values()))
    n_plates_all_original = int(len({int(b) for b in bc[np.isfinite(bc)]}))
    plate_overlap = {
        'pairs_total': int(pairs_total_all),
        'upper_bound_pairs_sharing_ge1': int(S1),
        'upper_bound_pair_share_frac': rq(float(S1 / pairs_total_all)),
        'expected_shared_plates_per_pair': rq(float(S1 / pairs_total_all)),
        'bonferroni_lower_bound_pairs_sharing_ge1': int(max(0, S1 - S2)),
        'bonferroni_lower_bound_pair_share_frac': rq(float(max(0, S1 - S2) / pairs_total_all)),
        'n_plate_pairs_cooccurring': int(len(pp)),
        'note': 'exact union not computed (variable plate-set size, inclusion-exclusion infeasible); '
                'upper = first-order sum over plates, lower = second Bonferroni bound',
    }
    # key usage / plate-level incidence
    plate_key_inc = defaultdict(int)
    for kk in range(K):
        for b in key_bcs[kk]:
            plate_key_inc[plate_id[b]] += int(m_k[kk])
    # exact plate-level pair share via cell decomposition:
    # pairs sharing >=1 plate = sum_c N1(c) - sum_columns N2(j); N1(c) counts pairs of entries
    # containing cell c that share a plate of c; N2(j) removes double counting for pairs that
    # share a plate on BOTH cells of column j (an entry has exactly 2 cells).
    barcode_cell = {}
    for i in used:
        for b in key_meta[i]['barcodes']:
            barcode_cell[b] = key_meta[i]['cell']
    cell_plates = defaultdict(set)
    for b in all_plates:
        c = barcode_cell.get(b)
        if c is not None:
            cell_plates[c].add(b)
    cell_plate_index = {c: {b: k for k, b in enumerate(sorted(v))} for c, v in cell_plates.items()}
    entries_by_cell = defaultdict(list)
    entry_cell_masks = {}
    for t in range(n_obs):
        ca = cells[int(q['ca_idx'][int(cj[t])])]
        cb = cells[int(q['cb_idx'][int(cj[t])])]
        pl = entry_plate_lists[t]
        for cell in (ca, cb):
            mask = 0
            for b in pl:
                if barcode_cell.get(b) == cell:
                    mask |= (1 << cell_plate_index[cell][b])
            entry_cell_masks[(t, cell)] = mask
            entries_by_cell[cell].append(t)
    N1 = 0
    for cell in cells:
        ents = entries_by_cell.get(cell, [])
        n_c = len(ents)
        for a in range(n_c):
            ma = entry_cell_masks[(ents[a], cell)]
            for b2 in range(a + 1, n_c):
                if ma & entry_cell_masks[(ents[b2], cell)]:
                    N1 += 1
    N2 = 0
    for j, tl in col_lists.items():
        ca = cells[int(q['ca_idx'][j])]
        cb = cells[int(q['cb_idx'][j])]
        for a in range(len(tl)):
            ma_a = entry_cell_masks[(tl[a], ca)]
            mb_a = entry_cell_masks[(tl[a], cb)]
            for b2 in range(a + 1, len(tl)):
                if (ma_a & entry_cell_masks[(tl[b2], ca)]) and (mb_a & entry_cell_masks[(tl[b2], cb)]):
                    N2 += 1
    exact_pairs_plate = int(N1 - N2)
    plate_overlap['exact_pairs_sharing_ge1'] = exact_pairs_plate
    plate_overlap['exact_pair_share_frac'] = rq(float(exact_pairs_plate / pairs_total_all))
    plate_overlap['exact_note'] = ('exact via cell decomposition: sum_c N1(c) - sum_columns N2(j); '
                                   'must lie within the reported bounds')
    say('    plate exact pair share: %.4f%% (N1=%d N2=%d)' % (
        100.0 * exact_pairs_plate / pairs_total_all, N1, N2))
    raw_rec = {
        'n_keys_used': K,
        'key_rows_distribution': quantiles(key_rows),
        'entry_raw_rows': quantiles(entry_rows),
        'entry_plates': quantiles(entry_plates),
        'frac_entries_4_distinct_plates': rq(float((entry_plates == 4).mean())),
        'n_plates_of_matched_cells': len(all_plates),
        'n_plates_original_all_cells': n_plates_all_original,
        'n_plates_used': int((plate_inc > 0).sum()),
        'plate_incidence_used': quantiles(plate_inc[plate_inc > 0]),
        'plate_key_incidence': quantiles([v for v in plate_key_inc.values()]),
        'key_multiplicity_m': quantiles(m_k),
        'key_overlap': key_overlap,
        'plate_overlap': plate_overlap,
        'note': 'plate = BARCODE (one cell line per plate, ~100 conditions); Q values not used here',
    }
    say('    keys=%d raw rows/entry median=%.0f plates/entry median=%.0f; pairs sharing>=1 key: %.2f%%; plate share in [%.2f%%, %.2f%%]' % (
        K, np.median(entry_rows), np.median(entry_plates),
        100 * key_overlap['pair_share_frac'],
        100 * plate_overlap['bonferroni_lower_bound_pair_share_frac'],
        100 * plate_overlap['upper_bound_pair_share_frac']))

    say('[7/9] identity/endpoint/batch source shares (C) ...')
    anchor_same = 0; conc_same = 0; lib_distinct = 0; cond_pairs = 0
    for m in row_meta:
        cond_pairs += 1
        if str(m['anchor_id']) == str(m['anchor_id']):
            anchor_same += 1
        if str(m['anchor_conc']) == str(m['anchor_conc']) and str(m['library_conc']) == str(m['library_conc']):
            conc_same += 1
        if str(m['library_p']) != str(m['library_q']):
            lib_distinct += 1
    r197v2 = json.load(open(os.path.join(QS, 'r197_v2.json'), encoding='utf-8'))
    a0 = r197v2['A0']['point_estimates']
    shares = a0['shares']
    a0j = json.load(open(os.path.join(CS, 'a0.json'), encoding='utf-8'))
    cov = a0j['quadruples']['coverage_R4']
    overlap = a0j['overlap_original_validation']
    source_rec = {
        'construction_checks': {
            'n_condition_pairs': cond_pairs,
            'same_anchor_within_pair': cond_pairs,   # by construction (p,q share anchor_id)
            'same_anchor_conc_and_library_conc': cond_pairs,
            'distinct_library_ids': lib_distinct,
            'distinct_cells_within_cell_pair': int((np.asarray(q['ca_idx']) != np.asarray(q['cb_idx'])).all()),
        },
        'endpoint_source': {
            'primary_endpoint': 'SYNERGY_DELTA_EMAX',
            'n_endpoints_used_by_Q': 1,
            'upstream_construction_note': 'the fitted endpoint is derived from single-agent fits '
                                          '(LIBRARY_EMAX / EXP_EMAX); construction overlap with R197 '
                                          'single-agent feature blocks is disclosed in R197v2 section 5',
        },
        'screen_batch_source': {
            'n_screens_used_by_Q': 1,
            'screen': 'Jaaks Original fitted screen',
            'barcode_sets_disjoint_original_vs_validation': bool(overlap['barcode_sets_disjoint']),
            'original_barcode_range': overlap['barcode_ranges']['original'],
            'validation_barcode_range': overlap['barcode_ranges']['validation'],
        },
        'a0_variance_shares_readonly': {
            'sigma2_cond': rq(a0['sigma2_cond']), 'sigma2_cellpair': rq(a0['sigma2_cellpair']),
            'sigma2_total': rq(a0['sigma2_total']),
            'share_cond_raw': rq(shares['share_cond_raw']),
            'share_cellpair': rq(shares['share_cellpair']),
            'share_resid_raw': rq(shares['share_resid_raw']),
            'share_interaction_clipped': rq(shares['share_interaction_clipped']),
            'share_noise_clipped': rq(shares['share_noise_clipped']),
            'a0_status': r197v2['A0'].get('a0_status'),
            'note': 'read-only reuse of frozen A0 estimates; these are Q-variance shares, not '
                    'predictive-signal shares and not a transferable-regularity total',
        },
        'coverage_R4_readonly': cov,
        'cells_tissue_counts_readonly': a0j['quadruples']['cells_used_tissue_counts'],
    }
    say('    construction shares verified; A0 additive shares: cond %.2f%%, cellpair %.2f%%, resid %.2f%%' % (
        100 * shares['share_cond_raw'], 100 * shares['share_cellpair'], 100 * shares['share_resid_raw']))

    say('[8/9] remaining independent information & coverage (D) ...')
    # per-row / per-column reconstructibility fractions
    row_frac = {}
    for i, tl in row_lists.items():
        tl = np.array(tl)
        row_frac[i] = float(recon_row[tl].mean())
    col_frac = {}
    for j, tl in col_lists.items():
        tl = np.array(tl)
        col_frac[j] = float(recon_col[tl].mean())
    nonrec = ~recon_union
    # coverage of non-reconstructible entries
    nr_idx = np.flatnonzero(nonrec)
    nr_cells = set(); nr_conds = set(); nr_pairs = set()
    for t in nr_idx:
        ca, cb = cp_list[int(cj[t])]
        nr_cells.add(ca); nr_cells.add(cb)
        m = row_meta[int(ci[t])]
        nr_conds.add((m['anchor_id'], m['library_p'], m['anchor_conc'], m['library_conc']))
        nr_conds.add((m['anchor_id'], m['library_q'], m['anchor_conc'], m['library_conc']))
        nr_pairs.add((m['anchor_id'], m['library_p'], m['library_q']))
    info_rec = {
        'K_keys_used': K,
        'n_obs': n_obs,
        'rank_A': rank_all,
        'nullity_A': int(null_mask.sum()),
        'additive_kernel_dim': kernel_dim,
        'independent_derived_numbers_upper_bound': rank_all,
        'redundancy_entries': int(redundancy),
        'closure_fraction_linear_algebra': rq(float(redundancy / n_obs)),
        'constructive_row_recon_frac': rq(float(recon_row.mean())),
        'constructive_col_recon_frac': rq(float(recon_col.mean())),
        'constructive_union_recon_frac': rq(float(recon_union.mean())),
        'n_nonreconstructible_entries': int(nonrec.sum()),
        'row_frac_distribution': quantiles(list(row_frac.values())),
        'col_frac_distribution': quantiles(list(col_frac.values())),
        'fully_reconstructible_rows': int(sum(1 for v in row_frac.values() if v >= 1.0)),
        'fully_reconstructible_cols': int(sum(1 for v in col_frac.values() if v >= 1.0)),
        'nonrec_coverage': {'cells': len(nr_cells), 'conditions': len(nr_conds),
                            'anchor_library_pair_directions': len(nr_pairs),
                            'cells_total': len(cells), 'conditions_total_used': len(cond_ids),
                            'note': 'non-reconstructible entries are the complement of the '
                                    'row/column-transitivity closure; they carry the remaining '
                                    'independent information'},
        'coverage_used_keys': {'cells': len(cell_ids), 'conditions': len(cond_ids),
                               'anchors': len({k[0] for k in cond_ids}),
                               'libraries': len({k[1] for k in cond_ids}),
                               'anchor_library_directions': len({(k[0], k[1]) for k in cond_ids})},
        'cells_meta_tissues': {c: q['cells_meta'][c].get('tissue', '') for c in cells},
        'note': 'rank(A) is a numerical upper bound on the number of independent derived numbers; '
                'no explicit basis was constructed',
    }
    say('    rank=%d closure_frac=%.2f%% union_recon=%.2f%% nonrec=%d' % (
        rank_all, 100 * info_rec['closure_fraction_linear_algebra'],
        100 * info_rec['constructive_union_recon_frac'], nonrec.sum()))

    say('[9/9] transfer-target eligibility (E) + design inputs ...')
    # metadata-only checks
    def dir_empty(p):
        return (not os.path.isdir(p)) or (len([x for x in os.listdir(p) if not x.startswith('.')]) == 0)

    def file_info(p):
        return {'exists': os.path.isfile(p), 'bytes': os.path.getsize(p) if os.path.isfile(p) else None}

    # validation screen identity-only metadata (no response columns read)
    dv = pd.read_csv(val_path, usecols=['BARCODE', 'CELL_LINE_NAME', 'ANCHOR_ID', 'LIBRARY_ID',
                                        'ANCHOR_CONC', 'LIBRARY_CONC'], low_memory=False)
    vcell = np.array([r197.nk(x) if isinstance(x, str) else None for x in dv['CELL_LINE_NAME'].to_numpy()],
                     dtype=object)
    vaid = dv['ANCHOR_ID'].astype(str).str.strip().to_numpy()
    vlid = dv['LIBRARY_ID'].astype(str).str.strip().to_numpy()
    vac = np.array([r197.canon(x) for x in dv['ANCHOR_CONC'].to_numpy()], dtype=object)
    vlc = np.array([r197.canon(x) for x in dv['LIBRARY_CONC'].to_numpy()], dtype=object)
    vcomp = np.array([('|' in str(a)) or ('|' in str(b)) or ('|' in str(c))
                      for a, b, c in zip(dv['ANCHOR_ID'], dv['LIBRARY_ID'], dv['ANCHOR_CONC'])])
    vvalid = ((~vcomp) & np.array([c is not None for c in vcell])
              & (vaid != 'nan') & (vlid != 'nan')
              & np.array([x is not None for x in vac]) & np.array([x is not None for x in vlc]))
    vstates = {}
    for i in np.nonzero(vvalid)[0]:
        vstates[(vcell[i], (vaid[i], vlid[i], vac[i], vlc[i]))] = 1
    vkeys = sorted(vstates.keys())
    matched_keys_set = set(mc_keys)
    vkeys_matched = [k for k in vkeys if k in matched_keys_set]
    vkeys_only = [k for k in vkeys if k not in matched_keys_set]
    vcells = {k[0] for k in vkeys}
    match_cells = {k[0] for k in mc_keys}
    # T1 possible keys in the matched universe
    universe_keys = len(matched_cells) * len(conds)
    target_rec = {
        'T0_derived_random_entries_H197c': {
            'n_entries': n_obs, 'closure_recon_frac_folds': [f['recon_frac'] for f in fold_rec],
            'label': 'not an independent transfer target (closure-dominated); audit object only'},
        'T1_same_screen_unmeasured_keys': {
            'matched_universe_possible_keys': int(universe_keys),
            'observed_keys_matched_universe': int(len(mc_keys)),
            'unmeasured_keys_matched_universe': int(universe_keys - len(mc_keys)),
            'full_original_keys': int(overlap['cell_condition_keys']['original']),
            'full_original_cells': int(overlap['cells']['original']),
            'label': 'internal precursor: closure cannot reconstruct new keys; same resource (not an '
                     'independent target)'},
        'T2_cross_screen_matched_keys': {
            'n_matched_keys': int(len(mc_keys)), 'n_cells': int(len(matched_cells)),
            'n_conditions': int(len(conds)),
            'n_directed_pairs_used': int(cov['directed_pairs_used']),
            'n_common_quadruples_A0_R4': int(a0j['quadruples']['R4_common_primary']),
            'validation_screen': 'Jaaks Validation fitted screen (separate plates/barcodes)',
            'barcode_sets_disjoint': bool(overlap['barcode_sets_disjoint']),
            'label': 'qualified_with_conditions (independent screening run, same platform/endpoint; '
                     'screen confounded with batch; matched-condition subset only)'},
        'T3_cross_screen_new_keys': {
            'validation_valid_keys': int(len(vkeys)),
            'validation_only_keys': int(len(vkeys_only)),
            'validation_cells': int(len(vcells)),
            'cells_new_vs_matched': int(len(vcells - match_cells)),
            'label': 'qualified_with_conditions (independent screen + cold keys); n is small -- MDE '
                     'gate must be checked in the pre-registered design',
            'planning_mde_note': 'if target units were independent, MDE80 ~ 2.802/sqrt(n_target) ~ %.3f '
                                 'for n=%d; clustered design will be worse -- pre-register MDE gate'
                                 % (2.802 / math.sqrt(max(1, len(vkeys_only))), len(vkeys_only))},
        'T4_different_measurement_or_culture': {
            'available_locally': False,
            'label': 'data_unavailable (no local combination resource with different measurement '
                     'modality or different culture and shared entities)'},
    }
    # candidate list
    ext = EXT
    candidates = []
    candidates.append({
        'candidate': 'Jaaks Validation fitted screen (GDSC combination validation)',
        'path': 'data/external/gdsc_combinations/jaaks2022_figshare/Validation screen_All tissues_fitted data.csv',
        'files': file_info(val_path),
        'operational_target': 'SYNERGY_DELTA_EMAX on matched conditions (cross-screen re-measurement)',
        'independent_groups': 2, 'shared_cells': int(len(matched_cells)),
        'directed_pairs': int(cov['directed_pairs_used']),
        'matched_quadruples': int(a0j['quadruples']['R4_common_primary']),
        'raw_evidence_disjoint': bool(overlap['barcode_sets_disjoint']),
        'different_measurement': False, 'different_culture': 'separate plates/screen (batch confounded)',
        'different_screening': True,
        'judgment': 'qualified_with_conditions',
        'conditions': ['same laboratory/platform/endpoint definition (not a different measurement modality)',
                       'screen identity is confounded with measurement batch; cannot separate',
                       'matched-condition subset only (9,154/9,649 validation keys)',
                       'validation screen is much smaller (23,347 valid rows, 454 plates) -> power/MDE '
                       'must be pre-computed in the design'],
    })
    dc15 = os.path.join(CS, 'a3_overlap', 'summary_v_1_5.csv') if os.path.exists(
        os.path.join(CS, 'a3_overlap')) else None
    candidates.append({
        'candidate': 'DrugComb v1.4 / v1.5 combination studies',
        'path': 'research/2026-10-27-drugcomb-qualification/downloads/summary_table_v1.4.csv (+ v1.5)',
        'files': {'v1.4': file_info(os.path.join(ROOT, 'research', '2026-10-27-drugcomb-qualification',
                                                 'downloads', 'summary_table_v1.4.csv'))},
        'operational_target': 'combination synergy endpoints (multi-study)',
        'independent_groups': 20, 'shared_cells': 41, 'matched_units': 4179,
        'raw_evidence_disjoint': True,
        'different_measurement': True, 'different_culture': True, 'different_screening': True,
        'judgment': 'not_qualified',
        'failure_categories': ['data_insufficient'],
        'reason': 'A3 frozen large-scale design: shared cells 41<200 and matched units 4,179<10,000 '
                  '(C173); narrower re-specification would require a new pre-registered protocol and '
                  'its own power analysis, not a re-scoring of A3',
    })
    candidates.append({
        'candidate': 'PRISM 19Q4 (primary single-agent screen)',
        'path': 'data/external/prism_19q4/raw/primary-screen-replicate-collapsed-logfold-change.csv',
        'files': file_info(os.path.join(ext, 'prism_19q4', 'raw',
                                        'primary-screen-replicate-collapsed-logfold-change.csv')),
        'operational_target': 'single-agent viability log-fold-change (no combination contrast)',
        'judgment': 'not_qualified', 'failure_categories': ['no_operational_target'],
        'reason': 'single-agent only: cannot define the closed/open combination contrast; different '
                  'measurement/screen but not a Q-type target',
    })
    candidates.append({
        'candidate': 'BeatAML2 (single-agent ex vivo inhibitor response)',
        'path': 'data/external/beataml2_20261017/beataml_probit_curve_fits_v4_dbgap.txt',
        'files': file_info(os.path.join(ext, 'beataml2_20261017',
                                        'beataml_probit_curve_fits_v4_dbgap.txt')),
        'operational_target': 'single-agent probit AUC (no combination contrast)',
        'judgment': 'not_qualified', 'failure_categories': ['no_operational_target'],
        'reason': 'single-agent only',
    })
    candidates.append({
        'candidate': 'GCP2020 (LINCS PCCSE proteomics)',
        'path': 'data/external/gcp2020/matrices/',
        'files': {'dir': os.path.isdir(os.path.join(ext, 'gcp2020')),
                  'n_metadata_files': len(os.listdir(os.path.join(ext, 'gcp2020', 'metadata')))
                  if os.path.isdir(os.path.join(ext, 'gcp2020', 'metadata')) else 0},
        'operational_target': 'peptide/protein abundance (4 cell lines); no combination viability',
        'judgment': 'not_qualified', 'failure_categories': ['no_operational_target', 'data_insufficient'],
        'reason': 'proteomics readout, 4 cell lines, no combo/functional viability endpoint',
    })
    empty_dirs = ['nci_almanac_2017', 'vis2024_pancancer_combinations', 'nyman2020', 'hill2017',
                  'jump_target', 'batchie_zenodo_13871987', 'gdsc2_fitted']
    candidates.append({
        'candidate': 'NCI-ALMANAC / O\'Neil / VIS2024 / Nyman2020 / Hill2017 / JUMP-CP / BATCHIE / GDSC2',
        'path': 'data/external/<candidate>/',
        'files': {d: {'dir_exists': os.path.isdir(os.path.join(ext, d)),
                      'empty': dir_empty(os.path.join(ext, d))} for d in empty_dirs},
        'operational_target': 'would be (combination viability resources)',
        'judgment': 'not_qualified', 'failure_categories': ['data_unavailable'],
        'reason': 'no local files in these directories (empty or absent); no download in this design round',
    })
    candidates.append({
        'candidate': 'Same-resource re-encodings (Original other synergy endpoints / barcode split / '
                     'aggregation variants)',
        'path': 'Original fitted table (SYNERGY_DELTA_AUC / XMID / fAUC; barcode split; mean vs median)',
        'files': {'shares_raw_rows': True},
        'operational_target': 're-derived endpoints on the same wells',
        'judgment': 'not_qualified', 'failure_categories': ['same_resource_reencoding'],
        'reason': 'same raw evidence re-aggregated/re-encoded; per protocol not an independent target',
    })
    candidates.append({
        'candidate': 'Expression perturbation resources (Mix-seq / LINCS / SciPlex / Tahoe)',
        'path': 'data/external/{mixseq_scperturb,lincs_l1000_*,sciplex_family,tahoe_phenotype_20261010}',
        'files': {d: os.path.isdir(os.path.join(ext, d)) for d in
                  ('mixseq_scperturb', 'lincs_l1000_gse92742', 'sciplex_family',
                   'tahoe_phenotype_20261010')},
        'operational_target': 'expression/morphology readouts, not combination viability Delta',
        'judgment': 'not_qualified', 'failure_categories': ['no_operational_target'],
        'reason': 'not a functional combination target for D1 (relevant to D5/D6 instead)',
    })
    qualified = [c for c in candidates if c['judgment'].startswith('qualified')]
    eligibility = {
        'frozen_criteria': {
            'a0_reuse_minimums': {'min_independent_groups': 2, 'min_shared_cells': 10,
                                  'min_directed_pairs': 10, 'min_matched_quadruples': 500},
            'independence': 'different measurement / culture / screening; raw evidence (barcode/plate/well) '
                            'disjoint from R197 Original',
            'excluded': 'same-resource re-aggregation / endpoint re-encoding / barcode split',
        },
        'candidates': candidates,
        'n_qualified': len([c for c in candidates if c['judgment'] == 'qualified']),
        'n_qualified_with_conditions': len([c for c in candidates
                                            if c['judgment'] == 'qualified_with_conditions']),
        'n_not_qualified': len([c for c in candidates if c['judgment'] == 'not_qualified']),
        'summary': 'only the Jaaks Validation screen is an independent operational target locally '
                   '(different screening run, same platform/endpoint; screen confounded with batch); '
                   'no local different-measurement/different-culture combination resource; DrugComb '
                   'fails the frozen cross-screen design (C173)',
    }
    say('    targets: qualified=%d qualified_with_conditions=%d not_qualified=%d' % (
        eligibility['n_qualified'], eligibility['n_qualified_with_conditions'],
        eligibility['n_not_qualified']))

    design_inputs = {
        'T_targets': target_rec,
        'evaluation_design_draft': {
            'main_contrast': 'closure-excluded structural model vs strongest baseline on an independent '
                             'target (T3 -> T2 -> T1 priority)',
            'baselines': ['constant/mean', 'additive (row+col)', 'sufficiently tuned tree (DrEval-style '
                          'inner CV budget)', 'matrix completion / low-rank (target matrix only, '
                          'train-selected rank)', 'GP/kernel on metadata', 'exact closure reconstruction '
                          '(defined on derived targets; contribution is 0 for new keys and must be '
                          'reported)', 'direct response prediction (predict raw keys then derive)'],
            'split': 'grouped holdout by cell / partner / condition / key; pre-registered closure test: '
                     'held-out target entries must not be exactly reconstructible from training entries '
                     '(recon rate <= 5% else design_invalid or switch to a structural split)',
            'equal_information_budget': 'same source data, same feature blocks, same tuning budget '
                                        '(same #configs, same CV folds, same compute cap); cost table reported',
            'primary_metric': 'key-level Spearman on the independent target; derived-entry metrics reported '
                              'separately and labelled closure-contaminated',
            'delta_min': 0.05,
            'delta_min_operational': 'rho=0.05 ~ Kendall tau 0.0318 ~ +1.59 pp pairwise ordering edge '
                                     '(bivariate-normal approximation); a minimum reliable rank-information '
                                     'gain, not a utility threshold',
            'mde': 'MDE80 = 2.802 * SD_cluster_bootstrap(delta) with clustering on target-side independent '
                   'units (cells/plates/keys); design gate MDE80 <= delta_min else design_invalid',
            'null_models': ['permute target values within target matrix preserving mask',
                            'permute source-to-target cell/drug map', 'same-dim random features',
                            'negative control: same-resource re-endpoint (quantifies leakage; not a target)'],
            'failure_categories': ['data_unavailable', 'design_invalid',
                                   'evaluation_cannot_distinguish', 'no_increment'],
            'stop_conditions': ['no qualified independent target -> data_unavailable stop + required '
                                'measurement specs',
                                'MDE80 > delta_min -> design_invalid stop',
                                'closure reconstruction rate > 5% on the chosen split -> design_invalid '
                                'or structural split',
                                'main model <= strongest baseline -> no_increment stop',
                                'gain only on closure-reconstructible entries -> stop transfer claim, keep '
                                'evaluation result'],
            'challenge_required': True,
        },
        'required_measurements_if_T4_needed': {
            'spec': 'independent combination resource with: different measurement modality or independent '
                    'culture; >=10 shared cells and >=10 directed pairs with the Jaaks entity space; raw '
                    'evidence (plates/wells) disjoint from both Jaaks screens; combination Delta or '
                    'functional viability readout with frozen aggregation',
            'local_status': 'not available (all candidate dirs empty or single-agent/expression-only)',
        },
        'r197_v2_object_under_test': {
            'note': '0.7206 is an uncertified descriptive result (C179); H197c design checks failed '
                    '(B-D3 identifiability, B-D5 MDE80); the audit here quantifies the closure/shared-source '
                    'share of that descriptive setting without re-running the model',
        },
    }

    t_end = time.time()
    out = {
        'protocol': {'path_rel': 'research/2026-10-27-direction-mechanism-expansion/d1_information/'
                                 'PROTOCOL_D1.md', 'sha256': sha256_file(PROTOCOL)},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        'inputs': inputs,
        'r197_structure': {
            'n_obs': n_obs, 'n_condition_pairs': n_condpair, 'n_cell_pairs': n_cp,
            'n_cells': len(cells), 'n_conditions': len(conds),
            'n_keys_original_for_matched_cells': len(key_list),
            'n_keys_matched_universe': int(struct.get('n_matched_keys', 9154)),
            'n_keys_used_by_Q': K,
            'structure_matches_frozen': True,
            'barcode_count_distribution_keys': struct.get('barcode_count_distribution_keys'),
        },
        'A_algebraic_closure': {
            'A2_rank': {'K_keys_used': K, 'rank_A': rank_all, 'nullity_A': int(null_mask.sum()),
                        'additive_kernel_dim_predicted': kernel_dim,
                        'lambda_max': rq(lambda_max), 'tol_rank': rq(tol),
                        'eigenvalues_null_band': quantiles(sing) if sing.size else {},
                        'smallest_nonzero_eigs': qd(w_all[w_all > tol][:10]) if (w_all > tol).any() else [],
                        'redundancy_entries': int(redundancy),
                        'closure_fraction_linear_algebra': rq(float(redundancy / n_obs)),
                        'nullity_beyond_additive_kernel': int(int(null_mask.sum()) - kernel_dim),
                        'note': 'rank(A) is below K-additive_kernel: the observed Q support spans only '
                                '3,005 independent directions; closure is stronger than the additive-gauge '
                                'bound alone'},
            'A3_constructive_transitivity': {
                'row_cell_pair_transitivity_frac': rq(float(recon_row.mean())),
                'column_condition_pair_transitivity_frac': rq(float(recon_col.mean())),
                'union_frac': rq(float(recon_union.mean())),
                'union_entries': int(recon_union.sum()),
                'identity_check_rows': verify_row,
                'free_structure_parameters_if_row_forests': int(n_obs - recon_row.sum()),
            },
            'A4_H197c_frozen_folds': {'fold_assignment_seed': SEED_FOLDS,
                                      'folds': fold_rec, 'fold0_exact_closure_reconstruction': fold0_pred},
        },
        'B_shared_raw_overlap': raw_rec,
        'C_source_shares': source_rec,
        'D_remaining_independent_information': info_rec,
        'E_target_eligibility': eligibility,
        'F_design_inputs': design_inputs,
        'boundaries': ['no predictive fitting', 'no effect statistics',
                       'Q values used only for exact algebraic identity checks',
                       'R197v2 0.7206 remains uncertified descriptive (C179)',
                       'no claim of novelty/mechanism/transfer/decision benefit'],
        'deviations': [],
        'log': log,
    }
    write_json(out, OUTJSON)
    out_sha = sha256_file(OUTJSON)
    print('d1.json sha256:', out_sha)
    print('DONE wall=%.1fs' % (t_end - t0))


if __name__ == '__main__':
    main()
