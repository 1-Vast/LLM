"""q2.py - R194 analysis A2: is there an estimable CONDITION-PAIR-level structure in Q?

Implements `research/2026-10-27-conditional-shift/PROTOCOL_Q2.md` (v1 FROZEN) strictly.

Model (frozen): Q_ij = mu + a_i(condition-pair) + b_j(cell-pair) + c_ij(interaction) + eps_ij(noise)
on the controlled_anchor quadruple universe. Variance components are estimated by the frozen
pairwise-covariance moment estimator; measurement noise is calibrated from within-screen barcode
split-halves; the condition-level Q reliability is sigma2_cond / (sigma2_cond + sigma2_est).

Order (frozen): load+assert SHA -> structure -> design check D1-D4 -> only if D passes:
variance components / shares / reliability / shuffle nulls -> exploratory Validation cross-check
-> judgment. No cross-screen Q replication is performed (that was A1; A2 is a different question).

Deterministic: fixed seeds, sorted JSON keys, no timestamps, input/script SHA256.

Run:  & D:\\anaconda\\envs\\maestro\\python.exe research\\2026-10-27-conditional-shift\\q2.py
Out:  q2.json, q2_rows.csv (next to this script).
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import math
import os
import platform
import sys
import time
import unicodedata

import numpy as np
import pandas as pd
from scipy.stats import rankdata

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
D = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare')
ORIG = os.path.join(D, 'Original screen_All tissues_fitted data.csv')
VAL = os.path.join(D, 'Validation screen_All tissues_fitted data.csv')
MATCHED = os.path.join(BASE, 'matched_conditions.csv')
A0JSON = os.path.join(BASE, 'a0.json')
PROTOCOL_A0 = os.path.join(BASE, 'PROTOCOL_A0.md')
PROTOCOL_Q = os.path.join(BASE, 'PROTOCOL_Q.md')
PROTOCOL_Q2 = os.path.join(BASE, 'PROTOCOL_Q2.md')
ERRATA = os.path.join(BASE, 'ERRATA_A0.md')
CHALLENGE = os.path.join(BASE, 'challenge_A0.md')
Q1JSON = os.path.join(BASE, 'q1.json')
BRIEF = os.path.join(ROOT, 'research', '2026-10-27-innovation-round-r194', 'BRIEF.md')
SCRIPT = os.path.abspath(__file__)
OUT_JSON = os.path.join(BASE, 'q2.json')
OUT_CSV = os.path.join(BASE, 'q2_rows.csv')

# ------------------------------------------------------------------ frozen constants
SEED = 20261028            # master (bootstrap)
SEED_PERM_COND = 20261029
SEED_PERM_CELL = 20261030
SEED_POWER = 20261031
B_MAIN = 1000
B_PILOT = 200
B_POWER = 100
N_POWER = 200
N_POWER_SENS = 100
B_PERM = 1000
Z_ONE_SIDED = 1.6448536269514722
RELIABILITY_THRESHOLD = 0.50
SHARE_NEGLIGIBLE = 0.10
POWER_THRESHOLD = 0.80
TYPE_I_MAX = 0.10
ALT_S = (0.2, 0.4)
ALT_RHO_CELLPAIR = 0.4
MIN_OBS = 10000
MIN_CELLPAIRS = 200
MIN_CONDPAIRS = 50
MIN_CP_PER_CONDPAIR = 10
MIN_CONDPAIRS_PER_CP = 5
MIN_NOISE_QUADS = 300
MIN_NOISE_HALF = 100
NOISE_RATIO_LO, NOISE_RATIO_HI = 0.5, 2.0
MIN_PILOT_SE_FINITE = 0.95
MAX_COMPONENTS = 5
PRIMARY_ENDPOINT = 'SYNERGY_DELTA_EMAX'
USECOLS = ['BARCODE', 'CELL_LINE_NAME', 'Tissue', 'ANCHOR_ID', 'LIBRARY_ID',
           'ANCHOR_CONC', 'LIBRARY_CONC', PRIMARY_ENDPOINT]
EXPECTED_SHA = {
    'jaaks_original_fitted': '1188968CE7FDCFB66D03791CF266515B7C7A2794E1FC73C966DBA40266FFA278',
    'jaaks_validation_fitted': 'DCBD4C3108D212FA771C52AE977C8E1C01A421162A2232CDC4273FAF257B2775',
    'matched_conditions': '73FD5085A7586BB1F33768E34A587668953DA4C13735693DCF2FCCCBC51353FF',
    'a0_json': '72BBAF6DF9BF80BBD19BF946A8D7A369003861FF21BD95561BC6DA48021ECA22',
    'protocol_a0': 'D77316ED9983D803D0671EF0C7D51F58BCDD439CFCCF253110BEA9B19539AA93',
    'protocol_q': '74FA675A77031E6DF1D68831615E8753EADDA13F41F27AB23096D836091ED1CF',
    'errata_a0': '0B0D744BB2306D402B6E838554787B2D517AFA707C7912BE176722C1BADE58E3',
    'challenge_a0': '6B14BCA1BC97158E3A5B53BCA6988E92532D2B34337F99A79E70B6DC0D050A3D',
    'q1_json': '064AD3C3A7AEF6D9BF67C139B144503A3EA2BACBDAF39F240F40113140903534',
    'protocol_q2': '0F8D19463ECEA5481C3258293108420ADA59674E9778B95B545B96B575E286CE',
}


# ------------------------------------------------------------------------ helpers
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


def q(x, nd=6):
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
    return round(v, nd)


def qd(d):
    if isinstance(d, dict):
        return {k: qd(v) for k, v in d.items()}
    if isinstance(d, (list, tuple)):
        return [qd(v) for v in d]
    if isinstance(d, (np.floating, np.integer, np.bool_)):
        return q(d.item())
    if isinstance(d, float):
        return q(d)
    return d


def write_json(obj, path):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write('\n')


def spearman(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    n = int(ok.sum())
    if n < 5:
        return float('nan'), n
    rx = rankdata(x[ok], method='average')
    ry = rankdata(y[ok], method='average')
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    den = math.sqrt(float(np.dot(rx, rx)) * float(np.dot(ry, ry)))
    if den == 0:
        return float('nan'), n
    return float(np.dot(rx, ry) / den), n


def load_screen(path):
    df = pd.read_csv(path, usecols=USECOLS, low_memory=False)
    n_rows = len(df)
    bc = pd.to_numeric(df['BARCODE'], errors='coerce').to_numpy()
    cell = np.array([nk(x) if isinstance(x, str) else None for x in df['CELL_LINE_NAME'].to_numpy()],
                    dtype=object)
    aid = df['ANCHOR_ID'].astype(str).str.strip().to_numpy()
    lid = df['LIBRARY_ID'].astype(str).str.strip().to_numpy()
    ac = np.array([canon(x) for x in df['ANCHOR_CONC'].to_numpy()], dtype=object)
    lc = np.array([canon(x) for x in df['LIBRARY_CONC'].to_numpy()], dtype=object)
    comp = np.array([('|' in str(a)) or ('|' in str(b)) or ('|' in str(c))
                     for a, b, c in zip(df['ANCHOR_ID'], df['LIBRARY_ID'], df['ANCHOR_CONC'])])
    y = pd.to_numeric(df[PRIMARY_ENDPOINT], errors='coerce').to_numpy(float)
    cell_ok = np.array([c is not None for c in cell])
    ac_ok = np.array([x is not None for x in ac])
    lc_ok = np.array([x is not None for x in lc])
    valid = ((~comp) & cell_ok & np.isfinite(bc) & (aid != 'nan') & (lid != 'nan')
             & ac_ok & lc_ok & np.isfinite(y))
    cond = [None] * n_rows
    for i in np.nonzero(valid)[0]:
        cond[i] = (aid[i], lid[i], ac[i], lc[i])
    out = {'n_rows': n_rows, 'n_valid': int(valid.sum()), 'barcode': bc.astype(np.int64),
           'cell': cell, 'cond': cond, 'y': y, 'valid': valid}
    return out


# ---------------------------------------------------------------------- estimator
def moment_estimator(y, ci, cj, n_cond, n_cell, w=None):
    """Frozen pairwise-covariance moment estimator (PROTOCOL_Q2 section 2).

    sigma2_cond  = weighted covariance of observations sharing a condition-pair
    sigma2_cell  = weighted covariance of observations sharing a cell-pair
    sigma2_total = weighted unbiased sample variance
    """
    if w is None:
        w = np.ones(y.size, dtype=float)
    W = float(w.sum())
    mu = float((w * y).sum() / W)
    # condition-pair aggregates
    Wc = np.bincount(ci, weights=w, minlength=n_cond)
    Sc = np.bincount(ci, weights=w * y, minlength=n_cond)
    Tc = np.bincount(ci, weights=w * y * y, minlength=n_cond)
    W2c = np.bincount(ci, weights=w * w, minlength=n_cond)
    num_c = 0.5 * (((Sc - mu * Wc) ** 2) - (Tc - 2 * mu * Sc + mu * mu * W2c)).sum()
    den_c = 0.5 * ((Wc ** 2 - W2c).sum())
    s2_cond = float(num_c / den_c) if den_c > 0 else float('nan')
    # cell-pair aggregates
    Wj = np.bincount(cj, weights=w, minlength=n_cell)
    Sj = np.bincount(cj, weights=w * y, minlength=n_cell)
    Tj = np.bincount(cj, weights=w * y * y, minlength=n_cell)
    W2j = np.bincount(cj, weights=w * w, minlength=n_cell)
    num_j = 0.5 * (((Sj - mu * Wj) ** 2) - (Tj - 2 * mu * Sj + mu * mu * W2j)).sum()
    den_j = 0.5 * ((Wj ** 2 - W2j).sum())
    s2_cell = float(num_j / den_j) if den_j > 0 else float('nan')
    s2_tot = float((w * (y - mu) ** 2).sum() / (W - 1.0)) if W > 1 else float('nan')
    return {'s2_cond': s2_cond, 's2_cell': s2_cell, 's2_total': s2_tot,
            's2_resid': s2_tot - s2_cond - s2_cell, 'n_obs_weight': W}


def two_way_bootstrap(qvals, ci, cj, n_cond, n_cell, B, seed, stats=('s2_cond', 's2_cell')):
    rng = np.random.default_rng(seed)
    out = {k: np.empty(B) for k in stats}
    for b in range(B):
        mc = np.bincount(rng.integers(0, n_cond, n_cond), minlength=n_cond).astype(float)
        mj = np.bincount(rng.integers(0, n_cell, n_cell), minlength=n_cell).astype(float)
        w = mc[ci] * mj[cj]
        est = moment_estimator(qvals, ci, cj, n_cond, n_cell, w)
        for k in stats:
            out[k][b] = est[k]
    return out


# -------------------------------------------------------------------------- main
def main():
    t0 = time.time()
    print('[1/9] hash inputs + protocol assertions ...', flush=True)
    inputs = {}
    for key, path in (('jaaks_original_fitted', ORIG), ('jaaks_validation_fitted', VAL),
                      ('matched_conditions', MATCHED), ('a0_json', A0JSON),
                      ('protocol_a0', PROTOCOL_A0), ('protocol_q', PROTOCOL_Q),
                      ('protocol_q2', PROTOCOL_Q2), ('errata_a0', ERRATA),
                      ('challenge_a0', CHALLENGE), ('q1_json', Q1JSON), ('r194_brief', BRIEF)):
        inputs[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                       'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    for key, expected in EXPECTED_SHA.items():
        assert inputs[key]['sha256'] == expected, 'SHA mismatch: ' + key
    a0 = json.load(open(A0JSON, encoding='utf-8'))
    assert a0['qualification']['judgment'] == 'matching_qualified'

    print('[2/9] load fitted tables (A0 validity rule) ...', flush=True)
    o = load_screen(ORIG)
    v = load_screen(VAL)
    assert o['n_valid'] == 291180 and v['n_valid'] == 23347

    print('[3/9] matched keys / condition universe ...', flush=True)
    mc = pd.read_csv(MATCHED, dtype=str)
    mc_keys = set()
    for r in mc.itertuples(index=False):
        mc_keys.add((r.cell, (r.anchor_id, r.library_id, canon(r.anchor_conc), canon(r.library_conc))))
    assert len(mc_keys) == 9154
    assert len({(k[1][0], k[1][1]) for k in mc_keys}) == 129
    cells = sorted({k[0] for k in mc_keys})
    conds = sorted({k[1] for k in mc_keys})
    cidx = {k: i for i, k in enumerate(conds)}
    cellidx = {c: i for i, c in enumerate(cells)}
    rep2 = collections.defaultdict(set)
    for cell, cond in mc_keys:
        rep2[cell].add(cond)
    n_cells, n_conds = len(cells), len(conds)

    print('[4/9] key matrices + barcode structure ...', flush=True)

    def key_series(entry):
        """(cell,cond) -> dict(barcode -> mean y); returns also full-key means."""
        cells_arr = entry['cell']
        conds_arr = entry['cond']
        bc_arr = entry['barcode']
        y_arr = entry['y']
        bmap = collections.defaultdict(lambda: collections.defaultdict(list))
        for i in np.nonzero(entry['valid'])[0]:
            c = cells_arr[i]
            if c not in cellidx:
                continue
            k = conds_arr[i]
            bmap[(c, k)][int(bc_arr[i])].append(float(y_arr[i]))
        full = {}
        for k, bm in bmap.items():
            full[k] = float(np.mean([np.mean(vs) for vs in bm.values()]))
        return full, bmap

    fullA, bcA = key_series(o)
    fullB, bcB = key_series(v)
    bcountA = {k: len(bm) for k, bm in bcA.items()}

    print('[5/9] condition-pair x cell-pair layout + Q values ...', flush=True)
    quad = []
    cp_list = []
    cp_index = {}
    for i in range(n_cells):
        ca = cells[i]
        for j in range(i + 1, n_cells):
            cb = cells[j]
            shared = rep2[ca] & rep2[cb]
            if len(shared) < 2:
                continue
            groups = collections.defaultdict(list)
            for k in shared:
                groups[(k[0], k[2], k[3])].append(k)
            qs = []
            for key, ks in groups.items():
                ks = sorted(ks, key=lambda x: (x[1]))      # canonical orientation by library id
                for a in range(len(ks)):
                    for b in range(a + 1, len(ks)):
                        qs.append((ks[a], ks[b]))
            if len(qs) >= 5:
                pi = len(cp_list)
                cp_index[(ca, cb)] = pi
                cp_list.append((ca, cb))
                for p, qc in qs:
                    quad.append((pi, i, j, p, qc))
    n_obs = len(quad)
    n_cp = len(cp_list)
    cpid_map = {}
    cpid = np.empty(n_obs, dtype=np.int64)
    cj = np.empty(n_obs, dtype=np.int64)
    q_orig = np.empty(n_obs)
    q_val = np.empty(n_obs)
    key_bcounts = np.empty((n_obs, 4), dtype=np.int64)
    for t, (pi, i, j, p, qc) in enumerate(quad):
        cj[t] = pi
        key = (p, qc)
        if key not in cpid_map:
            cpid_map[key] = len(cpid_map)
        cpid[t] = cpid_map[key]
        ca, cb = cells[i], cells[j]
        ycp_a = fullA[(ca, p)]
        ycq_a = fullA[(ca, qc)]
        ydp_a = fullA[(cb, p)]
        ydq_a = fullA[(cb, qc)]
        q_orig[t] = (ycp_a - ycq_a) - (ydp_a - ydq_a)
        ycp_b = fullB[(ca, p)]
        ycq_b = fullB[(ca, qc)]
        ydp_b = fullB[(cb, p)]
        ydq_b = fullB[(cb, qc)]
        q_val[t] = (ycp_b - ycq_b) - (ydp_b - ydq_b)
        key_bcounts[t, 0] = bcountA.get((ca, p), 0)
        key_bcounts[t, 1] = bcountA.get((ca, qc), 0)
        key_bcounts[t, 2] = bcountA.get((cb, p), 0)
        key_bcounts[t, 3] = bcountA.get((cb, qc), 0)
    n_condpair = len(cpid_map)
    condpair_meta = {}
    for (p, qc), i in cpid_map.items():
        condpair_meta[i] = {'p': p, 'q': qc}
    n_i = np.bincount(cpid, minlength=n_condpair)
    m_j = np.bincount(cj, minlength=n_cp)
    assert n_obs == 92039 and n_cp == 1501 and n_condpair == 229, 'structure differs from A2 probe'
    assert len(np.unique(cpid * n_cp + cj)) == n_obs, 'duplicate (condition-pair, cell-pair) cells'
    import scipy.sparse as sp
    A = sp.coo_matrix((np.ones(n_obs), (cpid, cj)), shape=(n_condpair, n_cp)).tocsr()
    big = sp.bmat([[None, A], [A.T, None]], format='csr')
    n_comp, labels = sp.csgraph.connected_components(big, directed=False)
    comp_sizes = np.bincount(labels[:n_condpair])
    structure = {
        'n_observations': n_obs, 'n_condition_pairs': n_condpair, 'n_cell_pairs': n_cp,
        'n_cells': n_cells, 'n_conditions': n_conds, 'n_matched_keys': len(mc_keys),
        'n_directed_pairs': 129,
        'condpair_n_cp_min': int(n_i.min()), 'condpair_n_cp_median': float(np.median(n_i)),
        'condpair_n_cp_max': int(n_i.max()), 'condpair_n_cp_mean': float(n_i.mean()),
        'cellpair_n_condpair_min': int(m_j.min()), 'cellpair_n_condpair_median': float(np.median(m_j)),
        'cellpair_n_condpair_max': int(m_j.max()),
        'unique_cells': True, 'bipartite_components': int(n_comp),
        'component_condition_pair_sizes': sorted(comp_sizes.tolist(), reverse=True),
        'density': float(n_obs / (n_condpair * n_cp)),
        'orientation_rule': 'condition pair (p,q) oriented by ascending library_id',
        'primary_endpoint': PRIMARY_ENDPOINT,
        'a0_references': 'PROTOCOL_A0.md + ERRATA_A0.md + challenge_A0.md',
    }

    print('[6/9] noise calibration (Original barcode split-half) ...', flush=True)
    # quadruples with all 4 keys having >=2 Original barcodes
    cal_idx = []
    diff2 = []
    denom = []
    for t in range(n_obs):
        bs = key_bcounts[t]
        if bs.min() >= 2:
            pi = int(cj[t])
            ca, cb = cp_list[pi]
            pi_, i, j, p, qc = quad[t]
            bm_cp = bcA[(ca, p)]
            bm_cq = bcA[(ca, qc)]
            bm_dp = bcA[(cb, p)]
            bm_dq = bcA[(cb, qc)]
            sets = [sorted(bm_cp), sorted(bm_cq), sorted(bm_dp), sorted(bm_dq)]
            if min(len(s) for s in sets) < 2:
                continue
            vals = []
            for half in (0, 1):
                ys = []
                for s, bm in zip(sets, (bm_cp, bm_cq, bm_dp, bm_dq)):
                    h = (len(s) + 1) // 2
                    chosen = s[:h] if half == 0 else s[h:]
                    ys.append(float(np.mean([np.mean(bm[b]) for b in chosen])))
                vals.append((ys[0] - ys[1]) - (ys[2] - ys[3]))
            d = vals[0] - vals[1]
            # denominator: sum over keys of 1/b_h1 + 1/b_h2
            den = 0.0
            for s in sets:
                h = (len(s) + 1) // 2
                den += 1.0 / h + 1.0 / (len(s) - h)
            cal_idx.append(t)
            diff2.append(d * d)
            denom.append(den)
    cal_idx = np.array(cal_idx, dtype=np.int64)
    diff2 = np.array(diff2)
    denom = np.array(denom)
    n_cal = int(cal_idx.size)
    s2_single = float(diff2.sum() / denom.sum()) if n_cal else float('nan')

    def single_est(mask):
        if mask.sum() < 20:
            return None
        return float(diff2[mask].sum() / denom[mask].sum())

    # split-half stability of the noise estimate
    cal_cond = cpid[cal_idx]
    cal_cell = cj[cal_idx]
    stab = {}
    for tag, parity in (('by_condition_pair_parity', cal_cond % 2),
                        ('by_cell_pair_parity', cal_cell % 2)):
        a = single_est(parity == 0)
        b = single_est(parity == 1)
        stab[tag] = {'half0': a, 'half1': b,
                     'n_half0': int((parity == 0).sum()), 'n_half1': int((parity == 1).sum()),
                     'ratio': (a / b) if (a and b and b > 0) else None}
    # per-observation noise variance from barcode counts
    noise_obs = s2_single * (1.0 / key_bcounts).sum(axis=1)
    noise_avg = float(np.mean(noise_obs)) if n_cal else float('nan')
    noise_block = {
        'n_calibration_quadruples': n_cal,
        'coverage_frac_of_observations': n_cal / n_obs,
        'sigma2_single_key_noise': s2_single,
        'noise_variance_mean_per_observation': noise_avg,
        'barcode_count_distribution_keys': {str(k): int((key_bcounts == k).sum())
                                            for k in sorted(np.unique(key_bcounts).tolist())},
        'stability': stab,
        'note': ('sigma2_single is the single-barcode error variance of one key value; per-observation '
                 'Q noise variance = sigma2_single * sum(1/b_k) over the four keys. Calibration uses only '
                 'Original quadruples whose four keys all have >=2 barcodes; the stationarity assumption '
                 'is a design-check item (D2).'),
    }

    # ---------------------------------------------------------------- design check
    print('[7/9] design check D1-D4 ...', flush=True)
    gates = []
    # D1 structure
    gates += [
        {'name': 'D1_n_obs_ge_min', 'value': n_obs, 'threshold': MIN_OBS, 'pass': bool(n_obs >= MIN_OBS)},
        {'name': 'D1_n_cellpairs_ge_min', 'value': n_cp, 'threshold': MIN_CELLPAIRS,
         'pass': bool(n_cp >= MIN_CELLPAIRS)},
        {'name': 'D1_n_condpairs_ge_min', 'value': n_condpair, 'threshold': MIN_CONDPAIRS,
         'pass': bool(n_condpair >= MIN_CONDPAIRS)},
        {'name': 'D1_min_cp_per_condpair', 'value': int(n_i.min()), 'threshold': MIN_CP_PER_CONDPAIR,
         'pass': bool(n_i.min() >= MIN_CP_PER_CONDPAIR)},
        {'name': 'D1_min_condpairs_per_cp', 'value': int(m_j.min()), 'threshold': MIN_CONDPAIRS_PER_CP,
         'pass': bool(m_j.min() >= MIN_CONDPAIRS_PER_CP)},
        {'name': 'D1_unique_cells', 'value': True, 'threshold': True, 'pass': True},
        {'name': 'D1_components_le_max', 'value': int(n_comp), 'threshold': MAX_COMPONENTS,
         'pass': bool(n_comp <= MAX_COMPONENTS)},
    ]
    # D2 noise
    stab_ok = True
    for tag, rec in stab.items():
        r = rec['ratio']
        if rec['n_half0'] < MIN_NOISE_HALF or rec['n_half1'] < MIN_NOISE_HALF:
            stab_ok = False
        if r is None or not (NOISE_RATIO_LO <= r <= NOISE_RATIO_HI):
            stab_ok = False
    gates += [
        {'name': 'D2_n_noise_quads', 'value': n_cal, 'threshold': MIN_NOISE_QUADS,
         'pass': bool(n_cal >= MIN_NOISE_QUADS)},
        {'name': 'D2_sigma2_single_positive', 'value': s2_single, 'threshold': 0.0,
         'pass': bool(math.isfinite(s2_single) and s2_single > 0)},
        {'name': 'D2_noise_stability_ratio', 'value': stab_ok, 'threshold': '[0.5, 2]',
         'pass': bool(stab_ok)},
        {'name': 'D2_noise_finite', 'value': noise_avg, 'threshold': '< inf',
         'pass': bool(math.isfinite(noise_avg))},
    ]
    # D3 estimability: point estimates + pilot bootstrap SE finite ratio
    point = moment_estimator(q_orig, cpid, cj, n_condpair, n_cp, None)
    pilot = two_way_bootstrap(q_orig, cpid, cj, n_condpair, n_cp, B_PILOT, SEED)
    se_pilot = {k: float(np.std(v, ddof=1)) for k, v in pilot.items()}
    finite_frac = float(np.mean([math.isfinite(se_pilot['s2_cond']), math.isfinite(se_pilot['s2_cell'])]))
    gates += [
        {'name': 'D3_point_estimates_finite',
         'value': bool(math.isfinite(point['s2_cond']) and math.isfinite(point['s2_cell'])),
         'threshold': True, 'pass': bool(math.isfinite(point['s2_cond']) and math.isfinite(point['s2_cell']))},
        {'name': 'D3_pilot_se_finite_frac', 'value': finite_frac, 'threshold': MIN_PILOT_SE_FINITE,
         'pass': bool(finite_frac >= MIN_PILOT_SE_FINITE)},
    ]

    # D4 power / type-I simulation on the observed cell pattern (frozen protocol section 5)
    def simulate_alternative(s, rho_cellpair, seed):
        rng = np.random.default_rng(seed)
        s2c = s * s
        rem = max(0.0, 1.0 - s2c)
        s2b = rho_cellpair * rem
        s2e = (1.0 - rho_cellpair) * rem
        a = rng.normal(0.0, math.sqrt(s2c), size=n_condpair)
        bb = rng.normal(0.0, math.sqrt(s2b), size=n_cp)
        return a[cpid] + bb[cj] + rng.normal(0.0, math.sqrt(s2e), size=n_obs)

    def power_sim(s, rho_cellpair, n_sim, seed):
        rng = np.random.default_rng(seed)
        rej = 0
        ests = []
        for k in range(n_sim):
            ysim = simulate_alternative(s, rho_cellpair, seed * 1000 + k)
            est = moment_estimator(ysim, cpid, cj, n_condpair, n_cp, None)
            se = float(np.std(two_way_bootstrap(ysim, cpid, cj, n_condpair, n_cp, B_POWER,
                                                SEED + k)['s2_cond'], ddof=1))
            ests.append(est['s2_cond'])
            if se > 0 and est['s2_cond'] / se > Z_ONE_SIDED:
                rej += 1
        return {'s': s, 'rho_cellpair': rho_cellpair, 'n_sim': n_sim,
                'mean_s2_cond': float(np.mean(ests)), 'reject_rate': rej / n_sim}

    t_power = time.time()
    power_020 = power_sim(ALT_S[0], ALT_RHO_CELLPAIR, N_POWER, SEED_POWER)
    power_040 = power_sim(ALT_S[1], ALT_RHO_CELLPAIR, N_POWER, SEED_POWER + 1)
    type_i = power_sim(0.0, ALT_RHO_CELLPAIR, N_POWER, SEED_POWER + 2)
    sens_split = {('%.1f' % rho): power_sim(ALT_S[1], rho, N_POWER_SENS, SEED_POWER + 10 + int(rho * 10))
                  for rho in (0.2, 0.6)}
    power_block = {'power_s0.2': power_020, 'power_s0.4': power_040, 'type_I_s0': type_i,
                   'split_sensitivity_rho_cellpair': sens_split,
                   'seed': SEED_POWER, 'b_power': B_POWER, 'n_sim': N_POWER,
                   'test': 'two-way bootstrap z = s2_cond / SE; reject if z > 1.645'}
    gates += [
        {'name': 'D4_power_s0.4_ge_0.80', 'value': power_040['reject_rate'], 'threshold': POWER_THRESHOLD,
         'pass': bool(power_040['reject_rate'] >= POWER_THRESHOLD)},
        {'name': 'D4_type_I_le_0.10', 'value': type_i['reject_rate'], 'threshold': TYPE_I_MAX,
         'pass': bool(type_i['reject_rate'] <= TYPE_I_MAX)},
    ]
    design_passed = all(g['pass'] for g in gates)
    failures = [g['name'] for g in gates if not g['pass']]
    print('    design_check_passed=%s failures=%s (power s0.4=%.2f typeI=%.2f noise_quads=%d)'
          % (design_passed, failures, power_040['reject_rate'], type_i['reject_rate'], n_cal), flush=True)
    design_check = {
        'structure': structure,
        'noise': noise_block,
        'point_estimates_design_phase': point,
        'pilot_bootstrap_se': se_pilot,
        'power': power_block,
        'gates': gates,
        'design_check_passed': bool(design_passed),
        'failure_reasons': failures,
    }

    # ---------------------------------------------------------------- main analysis
    judgment = {'verdict': 'inconclusive' if not design_passed else None,
                'design_check_passed': bool(design_passed),
                'failure_reasons': failures}
    main = {'computed': False}
    if design_passed:
        print('[8/9] main estimation: variance components / reliability / null distributions ...', flush=True)
        # point estimates with noise-based decomposition
        s2_cond = point['s2_cond']
        s2_cell = point['s2_cell']
        s2_total = point['s2_total']
        s2_resid = point['s2_resid']
        s2_int = max(0.0, s2_resid - noise_avg)
        n_median = float(np.median(n_i))
        rel_primary = (s2_cond / (s2_cond + (s2_int + noise_avg) / n_median)
                       if (s2_cond + (s2_int + noise_avg) / n_median) > 0 else float('nan'))
        rel_noise_only = (s2_cond / (s2_cond + noise_avg / n_median)
                          if (s2_cond + noise_avg / n_median) > 0 else float('nan'))
        rel_with_cell = (s2_cond / (s2_cond + (s2_cell + s2_int + noise_avg) / n_median)
                         if (s2_cond + (s2_cell + s2_int + noise_avg) / n_median) > 0 else float('nan'))
        shares = {
            'share_cond_clipped': max(s2_cond, 0.0) / s2_total if s2_total > 0 else float('nan'),
            'share_cellpair_clipped': max(s2_cell, 0.0) / s2_total if s2_total > 0 else float('nan'),
            'share_interaction_clipped': s2_int / s2_total if s2_total > 0 else float('nan'),
            'share_noise_clipped': noise_avg / s2_total if s2_total > 0 else float('nan'),
            'share_cond_raw': s2_cond / s2_total if s2_total > 0 else float('nan'),
            'share_cellpair_raw': s2_cell / s2_total if s2_total > 0 else float('nan'),
            'share_resid_raw': s2_resid / s2_total if s2_total > 0 else float('nan'),
            'sigma2_total': s2_total,
        }
        # per-condition-pair Q means and reliabilities
        n_cp_arr = n_i.astype(float)
        rel_i = s2_cond / (s2_cond + (s2_int + noise_avg) / n_cp_arr)
        qmean = np.bincount(cpid, weights=q_orig, minlength=n_condpair) / n_cp_arr
        qsd = np.sqrt(np.maximum(
            np.bincount(cpid, weights=(q_orig - qmean[cpid]) ** 2, minlength=n_condpair) / np.maximum(n_cp_arr - 1, 1),
            0.0))
        # main bootstrap (two-way)
        boot = two_way_bootstrap(q_orig, cpid, cj, n_condpair, n_cp, B_MAIN, SEED)
        boot_cond = boot['s2_cond']
        boot_cell = boot['s2_cell']
        ci_cond = [float(np.percentile(boot_cond, 2.5)), float(np.percentile(boot_cond, 97.5))]
        ci_cell = [float(np.percentile(boot_cell, 2.5)), float(np.percentile(boot_cell, 97.5))]
        se_cond = float(np.std(boot_cond, ddof=1))
        # shuffle nulls
        rng_cond = np.random.default_rng(SEED_PERM_COND)
        null_cond = np.empty(B_PERM)
        for b in range(B_PERM):
            perm = rng_cond.permutation(n_obs)
            est = moment_estimator(q_orig, cpid[perm], cj, n_condpair, n_cp, None)
            null_cond[b] = est['s2_cond']
        rng_cell = np.random.default_rng(SEED_PERM_CELL)
        null_cell = np.empty(B_PERM)
        for b in range(B_PERM):
            perm = rng_cell.permutation(n_obs)
            est = moment_estimator(q_orig, cpid, cj[perm], n_condpair, n_cp, None)
            null_cell[b] = est['s2_cell']
        p_cond = (1 + int((null_cond >= s2_cond).sum())) / (B_PERM + 1)
        p_cell = (1 + int((null_cell >= s2_cell).sum())) / (B_PERM + 1)
        q95_cond = float(np.percentile(null_cond, 95))
        # exploratory Validation cross-check (condition-level means only)
        v_n = np.bincount(cpid, minlength=n_condpair).astype(float)
        qmean_val = np.bincount(cpid, weights=q_val, minlength=n_condpair) / v_n
        rho_cond_levels, n_pairs_val = spearman(qmean, qmean_val)
        # bootstrap CI over condition-pairs for the exploratory correlation
        rng_v = np.random.default_rng(SEED + 5)
        vboot = []
        for b in range(B_MAIN):
            idx = rng_v.integers(0, n_condpair, n_condpair)
            rr, _ = spearman(qmean[idx], qmean_val[idx])
            if math.isfinite(rr):
                vboot.append(rr)
        v_ci = [float(np.percentile(vboot, 2.5)), float(np.percentile(vboot, 97.5))] if vboot else None
        point_val = moment_estimator(q_val, cpid, cj, n_condpair, n_cp, None)
        share_val = point_val['s2_cond'] / point_val['s2_total'] if point_val['s2_total'] > 0 else float('nan')
        present = bool(s2_cond > 0 and ci_cond[0] > 0 and s2_cond > q95_cond
                       and rel_primary >= RELIABILITY_THRESHOLD)
        verdict = 'condition_structure_present' if present else 'condition_structure_absent'
        h194b = ('negligible (<10% of Q variance)' if (shares['share_cond_clipped'] < SHARE_NEGLIGIBLE)
                 else 'non-negligible (>=10% of Q variance)')
        main = {
            'computed': True,
            'variance_components': {
                'sigma2_cond': s2_cond, 'sigma2_cellpair': s2_cell,
                'sigma2_total': s2_total, 'sigma2_resid_raw': s2_resid,
                'sigma2_interaction_clipped': s2_int, 'sigma2_noise_avg': noise_avg,
                'sigma2_interaction_raw': s2_resid - noise_avg,
            },
            'shares': shares,
            'reliability': {
                'primary_formula': 'sigma2_cond / (sigma2_cond + (sigma2_int + sigma2_noise_avg)/n_i)',
                'n_median': n_median,
                'rel_primary_at_median_n': rel_primary,
                'rel_noise_only_at_median_n': rel_noise_only,
                'rel_with_cellpair_sampling_at_median_n': rel_with_cell,
                'rel_i_median': float(np.median(rel_i)),
                'rel_i_p25': float(np.percentile(rel_i, 25)),
                'rel_i_p75': float(np.percentile(rel_i, 75)),
                'threshold': RELIABILITY_THRESHOLD,
            },
            'inference': {
                'bootstrap_B': B_MAIN, 'seed': SEED,
                'se_s2_cond': se_cond, 'ci95_s2_cond': ci_cond,
                'ci95_s2_cellpair': ci_cell,
                'permutation_condition_pairs': {'B': B_PERM, 'seed': SEED_PERM_COND,
                                                'null_q95_s2_cond': q95_cond,
                                                'p_value': p_cond,
                                                'null_mean': float(null_cond.mean()),
                                                'null_sd': float(null_cond.std(ddof=1))},
                'permutation_cell_pairs': {'B': B_PERM, 'seed': SEED_PERM_CELL,
                                           'p_value': p_cell,
                                           'null_q95_s2_cell': float(np.percentile(null_cell, 95))},
            },
            'H194a': {'sigma2_cond_positive': bool(s2_cond > 0),
                      'ci_lower_positive': bool(ci_cond[0] > 0),
                      'above_permutation_q95': bool(s2_cond > q95_cond),
                      'reliability_ge_threshold': bool(rel_primary >= RELIABILITY_THRESHOLD),
                      'pass': present},
            'H194b': {'share_cond': shares['share_cond_clipped'], 'share_cellpair': shares['share_cellpair_clipped'],
                      'classification': h194b},
            'validation_exploratory': {
                'condition_level_spearman': rho_cond_levels, 'n_condition_pairs': n_pairs_val,
                'bootstrap_ci95': v_ci,
                'sigma2_cond_validation': point_val['s2_cond'],
                'share_cond_validation': share_val,
                'note': ('exploratory out-of-sample condition-level consistency ONLY; not part of the '
                         'H194a/H194b judgment and NOT a cross-screen Q replication'),
            },
            'per_condition_pair': {'qmean': qmean, 'rel_i': rel_i, 'n_cp': n_i,
                                   'qsd': qsd, 'qmean_validation': qmean_val},
        }
        judgment.update({
            'verdict': verdict,
            'H194a_pass': present,
            'reliability_at_median_n': rel_primary,
            'sigma2_cond': s2_cond,
            'share_cond': shares['share_cond_clipped'],
        })
        print('    verdict=%s sigma2_cond=%.4f share=%.3f rel=%.3f (95%% CI cond [%.4f, %.4f], p_perm=%.4f)'
              % (verdict, s2_cond, shares['share_cond_clipped'], rel_primary,
                 ci_cond[0], ci_cond[1], p_cond), flush=True)
    else:
        judgment.update({
            'verdict': 'inconclusive',
            'main_effects_computed': False,
            'stop_reason': ('PROTOCOL_Q2 section 5: design check failed -> stop before H194a/H194b '
                            'judgment; no variance-component judgment is made'),
            'unfreeze_conditions': [
                'increase the barcode-repeat coverage of the Original screen so the noise calibration is '
                'stable (current calibration uses %d quadruples = %.2f%% of observations)' % (n_cal, 100.0 * n_cal / n_obs),
                'a design with more estimable condition-pair variance (e.g. more measurement groups) - '
                'not a different aggregation of the same 96 cells',
                're-examine the frozen design gates only with a new protocol revision',
            ],
        })

    # ---------------------------------------------------------------- outputs
    print('[9/9] write outputs ...', flush=True)
    rows = []
    for i in range(n_condpair):
        p, qc = condpair_meta[i]['p'], condpair_meta[i]['q']
        rows.append({
            'condition_pair_id': i,
            'anchor_id': p[0], 'library_p': p[1], 'library_q': qc[1],
            'anchor_conc': p[2], 'library_conc': p[3],
            'n_cell_pairs': int(n_i[i]),
            'q_mean_original': q(main['per_condition_pair']['qmean'][i]) if main['computed'] else None,
            'q_sd_original': q(main['per_condition_pair']['qsd'][i]) if main['computed'] else None,
            'q_mean_validation_exploratory': q(main['per_condition_pair']['qmean_validation'][i]) if main['computed'] else None,
            'reliability_primary': q(main['per_condition_pair']['rel_i'][i]) if main['computed'] else None,
        })
    with open(OUT_CSV, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    # assemble output (strip per-condition-pair arrays from JSON; they are in the CSV)
    if main['computed']:
        main_json = {k: v for k, v in main.items() if k != 'per_condition_pair'}
    else:
        main_json = {'computed': False}
    out = {
        'protocol': {'path_rel': os.path.relpath(PROTOCOL_Q2, ROOT).replace('\\', '/'),
                     'bytes': os.path.getsize(PROTOCOL_Q2), 'sha256': inputs['protocol_q2']['sha256'],
                     'status': 'v1 FROZEN'},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'bytes': os.path.getsize(SCRIPT), 'sha256': sha256_file(SCRIPT)},
        'environment': {'python': sys.version.split()[0], 'numpy': np.__version__,
                        'pandas': pd.__version__, 'platform': platform.platform()},
        'seeds': {'master': SEED, 'b_main': B_MAIN, 'b_pilot': B_PILOT, 'b_power': B_POWER,
                  'n_power': N_POWER, 'b_perm': B_PERM,
                  'perm_condition_pairs': SEED_PERM_COND, 'perm_cell_pairs': SEED_PERM_CELL,
                  'power': SEED_POWER},
        'inputs': inputs,
        'structure': structure,
        'design_check': design_check,
        'main_analysis': main_json,
        'judgment': judgment,
        'a0_citation': 'PROTOCOL_A0.md (SHA %s) + ERRATA_A0.md (SHA %s) + challenge_A0.md (SHA %s)'
                       % (inputs['protocol_a0']['sha256'], inputs['errata_a0']['sha256'],
                          inputs['challenge_a0']['sha256']),
        'relationship_to_A1': {
            'A1_verdict': 'inconclusive (C171)',
            'A2_is_not': ['an A1 pass', 'a cross-screen Q replication', 'a different aggregation of the same 96 cells used to rescue A1'],
            'A2_question': 'is there an estimable condition-pair-level variance component in Q?',
            'validation_role': 'exploratory out-of-sample condition-level consistency only; not in judgment',
        },
        'boundaries': {
            'no_B_C_acquisition': True,
            'no_endpoint_or_stratum_or_delta_change': True,
            'no_Q_size_stratification': True,
            'absent_wording': ('condition_structure_absent = "not estimable / negligible in this resource, '
                               'stratum and calibration precision" - NOT "condition-level structure does '
                               'not exist" and NOT an A1 pass/fail'),
            'conditional_shift_not_mechanism': True,
        },
        'response_value_use_attestation': {
            'model_selection_from_Q_results': False,
            'cross_screen_Q_replication_performed': False,
            'main_effects_computed': bool(main['computed']),
        },
    }
    assert out['response_value_use_attestation']['model_selection_from_Q_results'] is False
    out = qd(out)
    write_json(out, OUT_JSON)
    print('    wrote %s / %s' % (os.path.basename(OUT_JSON), os.path.basename(OUT_CSV)), flush=True)
    print('    runtime %.1fs' % (time.time() - t0), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
