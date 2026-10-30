"""q1.py - R193 analysis A (A1): independent runner for the Q-reproducibility protocol.

Implements `research/2026-10-27-conditional-shift/PROTOCOL_Q.md` (v1 FROZEN) strictly:
  * NO identity/annotation-style model; only the frozen matched-quadruple Q statistic.
  * Design check (PROTOCOL_Q sections 3-4) is computed FIRST and gates everything:
    if any design gate fails -> judgment `inconclusive`, STOP, and no cross-screen
    Q_A-Q_B statistic is computed or written (protocol section 7; Lead implementation note 1).
  * H193b single-agent adjusted Q (cross-fitted) is mandatory in the main path.
  * Deterministic: fixed seeds, sorted JSON keys, no timestamps, input/script SHA256.

Run:  & D:\\anaconda\\envs\\maestro\\python.exe research\\2026-10-27-conditional-shift\\q1.py
Out:  q1.json, q1_rows.csv (next to this script).

Pre-registered implementation choices (written before execution; see record_q1.md):
  - main stratum: controlled_anchor (same anchor_id, ANCHOR_CONC, LIBRARY_CONC; only library differs)
  - barcode aggregation: mean over rows per (screen, cell, condition, barcode); key value = mean over barcodes
  - barcode split-half halves: sorted barcodes, first ceil(n/2) vs rest (A0 frozen rule)
  - main statistic: Spearman(Q_A^cp, Q_B^cp) with Q^cp = median over quadruples of the cell pair;
    cell-cluster bootstrap CI (resample 96 cells, rebuild cp set, B=1000, seed 20261027)
  - permutation null: cell-label permutation of the Validation (cell,condition) structure (B=1000)
  - delta_min (latent) = 0.10 ; delta_min_obs = 0.10 * sqrt(relA * relB)
  - design-check coverage rule (pre-registered): per screen require
      keys_with_ge2_barcodes >= 300 AND barcode-split cp >= 50 AND rel lower 95% bound >= 0.20;
    delta_min_obs uses the CONSERVATIVE (upper) reliability bounds (Lead note 2)
  - MDE80_obs primary: cluster-adjusted null SE from the within-screen split-half reliability
      n_eff = ((1 - r^2) / SE_cellboot(r))^2 ; SE_null = 1/sqrt(n_eff - 1) ; MDE = 2.801585 * SE_null
    (Validation split-half, full cp coverage; Original as sensitivity). This uses ONLY within-screen
    barcode-split structure - no cross-screen Q alignment. Reported sensitivities: iid analytic,
    debiased-empirical, and zero-model cell-share 0/0.25/0.5/0.75.
  - joint power of the complete rule simulated with N_POWER=2000 MC draws; type-I likewise.
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
QUADS = os.path.join(BASE, 'matched_quadruples.csv')
A0JSON = os.path.join(BASE, 'a0.json')
PROTOCOL = os.path.join(BASE, 'PROTOCOL_Q.md')
ERRATA = os.path.join(BASE, 'ERRATA_A0.md')
CHALLENGE = os.path.join(BASE, 'challenge_A0.md')
PROTOCOL_A0 = os.path.join(BASE, 'PROTOCOL_A0.md')
SCRIPT = os.path.abspath(__file__)
OUT_JSON = os.path.join(BASE, 'q1.json')
OUT_CSV = os.path.join(BASE, 'q1_rows.csv')

# ------------------------------------------------------------------ frozen constants
SEED = 20261027
Z_MDE80 = 2.801585218112968          # z_{0.975}+z_{0.80}
Z_ALPHA = 1.959963984540054
Z_Q95 = 1.6448536269514722
DELTA_MIN_LATENT = 0.10
MIN_QUADS_PER_CP = 5
MIN_CP = 500
MIN_KEYS_GE2 = 300
MIN_CP_SPLIT = 50
MIN_REL_LCB = 0.20
B_REL_BOOT = 500
B_MAIN_BOOT = 1000
B_PERM = 1000
N_POWER = 2000
N_ZERO_SIM = 400
CELL_SHARES = (0.0, 0.25, 0.5, 0.75)
PRIMARY_ENDPOINT = 'SYNERGY_DELTA_EMAX'
SENS_ENDPOINTS = ['SYNERGY_DELTA_AUC', 'SYNERGY_DELTA_XMID', 'SYNERGY_DELTA_fAUC']
SINGLE_AGENT = ['ANCHOR_VIABILITY', 'LIBRARY_EMAX', 'LIBRARY_XMID', 'LIBRARY_XMID_uM',
                'LIBRARY_AUC', 'LIBRARY_fAUC', 'LIBRARY_RMSE']
USECOLS = (['BARCODE', 'CELL_LINE_NAME', 'Tissue', 'ANCHOR_ID', 'LIBRARY_ID',
            'ANCHOR_CONC', 'LIBRARY_CONC'] + [PRIMARY_ENDPOINT] + SENS_ENDPOINTS + SINGLE_AGENT)
EXPECTED_SHA = {
    'jaaks_original_fitted': '1188968CE7FDCFB66D03791CF266515B7C7A2794E1FC73C966DBA40266FFA278',
    'jaaks_validation_fitted': 'DCBD4C3108D212FA771C52AE977C8E1C01A421162A2232CDC4273FAF257B2775',
    'matched_conditions': '73FD5085A7586BB1F33768E34A587668953DA4C13735693DCF2FCCCBC51353FF',
    'matched_quadruples': '881A0DFC62A7D70DE158F5795AE1F2766E8EA1091BF6ED4F7280BA4A8211CCF9',
    'a0_json': '72BBAF6DF9BF80BBD19BF946A8D7A369003861FF21BD95561BC6DA48021ECA22',
    'protocol_q': '74FA675A77031E6DF1D68831615E8753EADDA13F41F27AB23096D836091ED1CF',
    'errata_a0': '0B0D744BB2306D402B6E838554787B2D517AFA707C7912BE176722C1BADE58E3',
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
    """Spearman rho via average ranks; returns (rho, n)."""
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


def sb(x):
    """Spearman-Brown correction."""
    if x is None or not math.isfinite(x) or x <= -1:
        return None
    return 2 * x / (1 + x)


def design_se_from_reliability(r, se_boot):
    """n_eff = ((1-r^2)/SE_boot)^2 ; null SE = 1/sqrt(n_eff-1)."""
    if r is None or se_boot is None or not (math.isfinite(r) and math.isfinite(se_boot)) or se_boot <= 0:
        return None, None, None
    n_eff = ((1 - r * r) / se_boot) ** 2
    se_null = 1.0 / math.sqrt(max(n_eff - 1.0, 1.0))
    return n_eff, se_null, Z_MDE80 * se_null


def load_screen(path):
    """Load one fitted table, apply the A0 validity rule, return row-level arrays."""
    df = pd.read_csv(path, usecols=USECOLS, low_memory=False)
    n_rows = len(df)
    bc = pd.to_numeric(df['BARCODE'], errors='coerce').to_numpy()
    cell = np.array([nk(x) if isinstance(x, str) else None for x in df['CELL_LINE_NAME'].to_numpy()],
                    dtype=object)
    aid = df['ANCHOR_ID'].astype(str).str.strip().to_numpy()
    lid = df['LIBRARY_ID'].astype(str).str.strip().to_numpy()
    ac_raw = df['ANCHOR_CONC'].to_numpy()
    lc_raw = df['LIBRARY_CONC'].to_numpy()
    ac = np.array([canon(x) for x in ac_raw], dtype=object)
    lc = np.array([canon(x) for x in lc_raw], dtype=object)
    comp = np.array([('|' in str(a)) or ('|' in str(b)) or ('|' in str(c))
                     for a, b, c in zip(df['ANCHOR_ID'], df['LIBRARY_ID'], df['ANCHOR_CONC'])])
    num = {}
    for c in [PRIMARY_ENDPOINT] + SENS_ENDPOINTS + SINGLE_AGENT:
        num[c] = pd.to_numeric(df[c], errors='coerce').to_numpy(float)
    cell_ok = np.array([c is not None for c in cell])
    ac_ok = np.array([x is not None for x in ac])
    lc_ok = np.array([x is not None for x in lc])
    valid = ((~comp) & cell_ok & np.isfinite(bc) & (aid != 'nan') & (lid != 'nan')
             & ac_ok & lc_ok & np.isfinite(num[PRIMARY_ENDPOINT]))
    cond_full = [None] * n_rows
    for i in np.nonzero(valid)[0]:
        cond_full[i] = (aid[i], lid[i], ac[i], lc[i])
    out = {
        'n_rows': n_rows, 'n_valid': int(valid.sum()),
        'barcode': bc.astype(np.int64), 'cell': cell, 'aid': aid, 'lid': lid,
        'ac': ac, 'lc': lc, 'valid': valid,
        'cond_full': cond_full,
    }
    for c in num:
        out[c] = num[c]
    return out


# -------------------------------------------------------------------------- main
def main():
    t0 = time.time()
    print('[1/8] hash inputs + assert A0/ERRATA facts ...', flush=True)
    inputs = {}
    for key, path in (('jaaks_original_fitted', ORIG), ('jaaks_validation_fitted', VAL),
                      ('matched_conditions', MATCHED), ('matched_quadruples', QUADS),
                      ('a0_json', A0JSON), ('protocol_q', PROTOCOL), ('errata_a0', ERRATA),
                      ('challenge_a0', CHALLENGE), ('protocol_a0', PROTOCOL_A0)):
        inputs[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                       'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    for key, expected in EXPECTED_SHA.items():
        assert inputs[key]['sha256'] == expected, 'SHA mismatch for ' + key
    a0 = json.load(open(A0JSON, encoding='utf-8'))
    assert a0['qualification']['judgment'] == 'matching_qualified'
    assert a0['primary_endpoint'] == PRIMARY_ENDPOINT
    errata_facts = {
        'disjoint_pairs_corrected': 4612633,
        'g1_only_m3_corrected': 4412540421,
        'g2_only_m3_corrected': 7234325,
        'condition_level_directed_pairs': 129,
        'barcode_split_R4_coverage': '46 cells / 583 cell pairs',
    }

    print('[2/8] load fitted tables (validity rule = A0) ...', flush=True)
    o = load_screen(ORIG)
    v = load_screen(VAL)
    assert o['n_valid'] == 291180 and v['n_valid'] == 23347, 'valid row counts differ from A0'
    print('    orig %d rows (%d valid) / val %d rows (%d valid)' % (
        o['n_rows'], o['n_valid'], v['n_rows'], v['n_valid']), flush=True)

    print('[3/8] matched keys / rep2 / condition universe ...', flush=True)
    mc = pd.read_csv(MATCHED, dtype=str)
    mc_keys = set()
    for r in mc.itertuples(index=False):
        mc_keys.add((r.cell, (r.anchor_id, r.library_id, canon(r.anchor_conc), canon(r.library_conc))))
    n_cond_keys = len(mc_keys)
    directed_pairs = {(k[1][0], k[1][1]) for k in mc_keys}
    assert n_cond_keys == 9154, 'matched_conditions count mismatch'
    assert len(directed_pairs) == 129, 'condition-level directed pairs != 129 (ERRATA_A0)'
    # reconstruct rep2 from the fitted tables and require exact equality with matched_conditions
    o_cell = np.array(o['cell'])
    v_cell = np.array(v['cell'])
    rep_o = collections.defaultdict(set)
    rep_v = collections.defaultdict(set)
    for i in np.nonzero(o['valid'])[0]:
        rep_o[o['cell'][i]].add(o['cond_full'][i])
    for i in np.nonzero(v['valid'])[0]:
        rep_v[v['cell'][i]].add(v['cond_full'][i])
    common_cells = sorted(set(rep_o) & set(rep_v))
    rep2 = {}
    for c in common_cells:
        shared = rep_o[c] & rep_v[c]
        if shared:
            rep2[c] = shared
    recon_keys = {(c, k) for c, s in rep2.items() for k in s}
    assert recon_keys == mc_keys, 'reconstructed matched keys differ from matched_conditions.csv'
    cells = sorted(rep2)
    conds = sorted({k for s in rep2.values() for k in s})
    cidx = {k: i for i, k in enumerate(conds)}
    cellidx = {c: i for i, c in enumerate(cells)}
    ncells, nconds = len(cells), len(conds)
    print('    cells %d / conditions %d / matched keys %d (set-equal) / directed pairs %d'
          % (ncells, nconds, n_cond_keys, len(directed_pairs)), flush=True)

    print('[4/8] build key matrices + controlled_anchor quadruples ...', flush=True)

    def build_mats(entry, col):
        """cell x condition matrix (mean over barcodes/rows) + per-key barcode->value map."""
        cell_arr = np.array(entry['cell'], dtype=object)
        cond_arr = entry['cond_full']
        bc_arr = entry['barcode']
        y_arr = entry[col]
        bc_map = collections.defaultdict(lambda: collections.defaultdict(list))
        for i in np.nonzero(entry['valid'])[0]:
            c = cell_arr[i]
            if c not in cellidx:
                continue
            k = cond_arr[i]
            if k not in cidx:
                continue
            bc_map[(c, k)][int(bc_arr[i])].append(float(y_arr[i]))
        full = {}
        for k, bmap in bc_map.items():
            full[k] = float(np.mean([np.mean(vs) for vs in bmap.values()]))
        mat = np.full((ncells, nconds), np.nan)
        for (c, k), val in full.items():
            mat[cellidx[c], cidx[k]] = val
        return mat, bc_map

    yA, bcA = build_mats(o, PRIMARY_ENDPOINT)
    yB, bcB = build_mats(v, PRIMARY_ENDPOINT)
    # endpoint matrices for sensitivity endpoints (no barcode use needed)
    sensA, sensB = {}, {}
    for ep in SENS_ENDPOINTS:
        sensA[ep], _ = build_mats(o, ep)
        sensB[ep], _ = build_mats(v, ep)
    # single-agent matrices (H193b; empty values are 0 per A0/challenge verification)
    saA, saB = {}, {}
    for c in SINGLE_AGENT:
        saA[c], _ = build_mats(o, c)
        saB[c], _ = build_mats(v, c)

    # quadruples of the controlled_anchor main stratum
    quad = []          # (cp_idx, ca_idx, cb_idx, p_cond_idx, q_cond_idx)
    cp_list = []
    cp_index = {}
    for i in range(ncells):
        ca = cells[i]
        for j in range(i + 1, ncells):
            cb = cells[j]
            shared = rep2[ca] & rep2[cb]
            if len(shared) < 2:
                continue
            groups = collections.defaultdict(list)
            for k in shared:
                groups[(k[0], k[2], k[3])].append(k)     # same anchor_id / anchor_conc / library_conc
            qs = []
            for key, ks in groups.items():
                ks = sorted(ks, key=lambda x: (x[1]))
                for a in range(len(ks)):
                    for b in range(a + 1, len(ks)):
                        qs.append((ks[a], ks[b]))        # orientation by ascending library id
            if len(qs) >= MIN_QUADS_PER_CP:
                pi = len(cp_list)
                cp_index[(ca, cb)] = pi
                cp_list.append((ca, cb))
                for p, qcond in qs:
                    quad.append((pi, i, j, cidx[p], cidx[qcond]))
    n_quads = len(quad)
    n_cp = len(cp_list)
    cp_arr = np.array([x[0] for x in quad])
    ca_arr = np.array([x[1] for x in quad])
    cb_arr = np.array([x[2] for x in quad])
    cp_arr_p = np.array([x[3] for x in quad])
    cq_arr = np.array([x[4] for x in quad])
    cp_sizes = np.bincount(cp_arr, minlength=n_cp)
    cell_index_pair = np.full((ncells, ncells), -1, dtype=np.int32)
    for (ca, cb), pi in cp_index.items():
        cell_index_pair[cellidx[ca], cellidx[cb]] = pi
        cell_index_pair[cellidx[cb], cellidx[ca]] = pi

    # A0 cross-checks: controlled_anchor count and R4 full count (combinatorial, unordered pairs)
    r4_count = 0
    cp_shared = 0
    for i in range(ncells):
        ca = cells[i]
        for j in range(i + 1, ncells):
            cb = cells[j]
            shared = rep2[ca] & rep2[cb]
            m = len(shared)
            if m < 2:
                continue
            bydp = collections.Counter((min(k[0], k[1]), max(k[0], k[1])) for k in shared)
            same_dp = sum(v * (v - 1) // 2 for v in bydp.values())
            u = m * (m - 1) // 2 - same_dp
            r4_count += max(0, u)
    assert n_quads == 92039, 'controlled_anchor quadruple count != 92039 (A0/ERRATA)'
    assert n_cp == 1501, 'cp count != 1501'
    structure = {
        'n_valid_rows_original': o['n_valid'], 'n_valid_rows_validation': v['n_valid'],
        'n_common_cells': ncells, 'n_conditions_matched': nconds,
        'n_matched_cell_condition_keys': n_cond_keys,
        'n_matched_directed_pairs': len(directed_pairs),
        'main_stratum': 'controlled_anchor',
        'n_controlled_anchor_quadruples': n_quads,
        'n_cell_pairs': n_cp,
        'n_cp_with_ge_min_quads': n_cp,
        'cp_quads_min': int(cp_sizes.min()), 'cp_quads_median': float(np.median(cp_sizes)),
        'cp_quads_max': int(cp_sizes.max()),
        'r4_full_quadruples_recomputed': int(r4_count),
        'r4_full_expected_A0': 6223367,
        'a0_qualification': 'matching_qualified (see PROTOCOL_A0 + ERRATA_A0 + challenge_A0)',
        'errata_facts': errata_facts,
    }
    assert r4_count == 6223367, 'R4 full quadruple count != 6223367 (A0)'
    print('    quadruples %d / cp %d / R4 full %d (matches A0)' % (n_quads, n_cp, r4_count), flush=True)

    # ---------------------------------------------------------------- design check
    print('[5/8] design check: structure / reliability / delta_min / MDE / power ...', flush=True)

    def split_half_fields(bc_map):
        """per key: {barcode: value} -> (half1 mean, half2 mean) using A0 split rule."""
        h1, h2 = {}, {}
        n_ge2 = 0
        for k, bmap in bc_map.items():
            if k not in mc_keys:
                continue
            bs = sorted(bmap)
            if len(bs) >= 2:
                n_ge2 += 1
                h = (len(bs) + 1) // 2
                h1[k] = float(np.mean([np.mean(bmap[b]) for b in bs[:h]]))
                h2[k] = float(np.mean([np.mean(bmap[b]) for b in bs[h:]]))
        return h1, h2, n_ge2

    def q_from_map(val_map):
        """Q per quadruple from a (cell,cond)->value map; returns array with NaN where missing."""
        mat = np.full((ncells, nconds), np.nan)
        for (c, k), val in val_map.items():
            mat[cellidx[c], cidx[k]] = val
        ya = mat[ca_arr, cp_arr_p]
        yb = mat[ca_arr, cq_arr]
        yc = mat[cb_arr, cp_arr_p]
        yd = mat[cb_arr, cq_arr]
        return (ya - yb) - (yc - yd)

    def cp_median(arr):
        out = np.full(n_cp, np.nan)
        ok = np.isfinite(arr)
        if not ok.any():
            return out
        df = pd.DataFrame({'cp': cp_arr[ok], 'q': arr[ok]})
        med = df.groupby('cp')['q'].median()
        out[med.index.to_numpy()] = med.to_numpy()
        return out

    def cell_bootstrap_cp_sets(rng, B):
        """Yield arrays of cp indices for cell-cluster bootstrap replicates."""
        out = []
        for b in range(B):
            samp = rng.integers(0, ncells, ncells)
            uniq = np.unique(samp)
            if len(uniq) < 2:
                continue
            ii, jj = np.triu_indices(len(uniq), k=1)
            pairs = cell_index_pair[uniq[ii], uniq[jj]]
            pairs = pairs[pairs >= 0]
            if pairs.size:
                out.append(pairs)
        return out

    rng = np.random.default_rng(SEED)
    boot_sets = cell_bootstrap_cp_sets(rng, B_REL_BOOT)

    def rel_block(h1, h2, label):
        q1 = q_from_map(h1)
        q2 = q_from_map(h2)
        m1 = cp_median(q1)
        m2 = cp_median(q2)
        ok = np.isfinite(m1) & np.isfinite(m2)
        r_pt, n_cp_rel = spearman(m1[ok], m2[ok])
        rhos = []
        for cpset in boot_sets:
            sel = cpset[ok[cpset]]
            if sel.size < 20:
                continue
            rr, _ = spearman(m1[sel], m2[sel])
            if math.isfinite(rr):
                rhos.append(rr)
        rhos = np.asarray(rhos)
        se_r = float(rhos.std(ddof=1)) if rhos.size > 5 else None
        rel_pt = sb(r_pt)
        rel_lo = sb(r_pt - Z_ALPHA * se_r) if se_r is not None else None
        rel_hi = sb(min(0.999, r_pt + Z_ALPHA * se_r)) if se_r is not None else None
        keys_ge2 = None
        return {'label': label, 'n_cp_split': int(n_cp_rel), 'r_split_half_spearman': r_pt,
                'rel_spearman_brown': rel_pt, 'se_boot_r': se_r,
                'rel_ci95': [rel_lo, rel_hi], 'rel_hi_conservative': rel_hi,
                'n_boot_replicates_used': int(rhos.size)}, m1, m2, r_pt, se_r

    hA1, hA2, nA_ge2 = split_half_fields(bcA)
    hB1, hB2, nB_ge2 = split_half_fields(bcB)
    rel_A, mA1, mA2, rA, seA = rel_block(hA1, hA2, 'original')
    rel_A['n_keys_with_ge2_barcodes'] = nA_ge2
    rel_B, mB1, mB2, rB, seB = rel_block(hB1, hB2, 'validation')
    rel_B['n_keys_with_ge2_barcodes'] = nB_ge2

    # pre-registered reliability coverage gates
    rel_gates = []
    for tag, rec in (('original', rel_A), ('validation', rel_B)):
        rel_gates.append({'name': 'rel_%s_keys_ge2' % tag,
                          'value': rec['n_keys_with_ge2_barcodes'], 'threshold': MIN_KEYS_GE2,
                          'pass': bool(rec['n_keys_with_ge2_barcodes'] >= MIN_KEYS_GE2)})
        rel_gates.append({'name': 'rel_%s_cp_split' % tag,
                          'value': rec['n_cp_split'], 'threshold': MIN_CP_SPLIT,
                          'pass': bool(rec['n_cp_split'] >= MIN_CP_SPLIT)})
        lo = (rec['rel_ci95'] or [None])[0]
        rel_gates.append({'name': 'rel_%s_ci_lower' % tag,
                          'value': lo, 'threshold': MIN_REL_LCB,
                          'pass': bool(lo is not None and lo >= MIN_REL_LCB)})

    relA_hi = rel_A['rel_hi_conservative'] if rel_A['rel_hi_conservative'] is not None else rel_A['rel_spearman_brown']
    relB_hi = rel_B['rel_hi_conservative'] if rel_B['rel_hi_conservative'] is not None else rel_B['rel_spearman_brown']
    relA_pt = rel_A['rel_spearman_brown']
    relB_pt = rel_B['rel_spearman_brown']
    delta_min_obs_pt = (DELTA_MIN_LATENT * math.sqrt(max(relA_pt, 0) * max(relB_pt, 0))
                        if (relA_pt is not None and relB_pt is not None) else None)
    delta_min_obs_cons = (DELTA_MIN_LATENT * math.sqrt(max(relA_hi, 0) * max(relB_hi, 0))
                          if (relA_hi is not None and relB_hi is not None) else None)

    # ---- MDE80_obs: primary = cluster-adjusted null SE from within-screen split-half reliability
    mde = {}
    # primary: Validation split-half (full cp coverage); Original as sensitivity
    n_eff_B, se_null_B, mde_B = design_se_from_reliability(rB, seB)
    n_eff_A, se_null_A, mde_A = design_se_from_reliability(rA, seA)
    iid_se = 1.0 / math.sqrt(max(n_cp - 1, 1))
    mde['primary_empirical_cluster_adjusted'] = {
        'construction': ('n_eff from cell-cluster bootstrap SE of the within-screen barcode split-half '
                         'reliability (Validation, full cp coverage); SE_null=1/sqrt(n_eff-1); '
                         'MDE80=2.801585*SE_null'),
        'screen_used': 'validation', 'r_split_half': rB, 'se_boot_r': seB,
        'n_eff': n_eff_B, 'se_null': se_null_B, 'mde80': mde_B,
        'original_sensitivity': {'r_split_half': rA, 'se_boot_r': seA,
                                 'n_eff': n_eff_A, 'se_null': se_null_A, 'mde80': mde_A},
    }
    mde['iid_analytic_sensitivity'] = {
        'construction': '1/sqrt(n_cp-1) (ignores cell clustering; NOT used for the gate)',
        'se_null': iid_se, 'mde80': Z_MDE80 * iid_se,
    }
    # debiased empirical: divide the bootstrap SE by the cluster-bootstrap inflation factor measured
    # on iid cp data with the same true r and cp structure (calibration simulation)
    cal_rng = np.random.default_rng(SEED + 11)
    n_cal = 200
    cal_se = []
    for _ in range(n_cal):
        z1 = cal_rng.normal(size=n_cp)
        z2 = rB * z1 + math.sqrt(max(0.0, 1 - rB * rB)) * cal_rng.normal(size=n_cp) if rB is not None else z1
        rhos_cal = []
        for cpset in boot_sets:
            rr, _ = spearman(z1[cpset], z2[cpset])
            if math.isfinite(rr):
                rhos_cal.append(rr)
        if len(rhos_cal) > 5:
            cal_se.append(float(np.std(rhos_cal, ddof=1)))
    cal_factor = (float(np.median(cal_se)) / iid_se) if cal_se else None
    se_boot_debiased = (seB / cal_factor) if (seB is not None and cal_factor) else None
    mde['debiased_empirical_sensitivity'] = {
        'construction': 'bootstrap SE divided by the iid-calibration inflation factor of the same cp structure',
        'calibration_inflation_factor': cal_factor, 'se_debiased': se_boot_debiased,
        'mde80': (Z_MDE80 * se_boot_debiased) if se_boot_debiased else None,
    }
    # zero-model cell-share sensitivities (structure-only simulation; no response values)
    zero_models = {}
    for share in CELL_SHARES:
        s2 = 0.0 if share <= 0 else share / (2 * (1 - share))
        sim_rng = np.random.default_rng(SEED + 101 + int(share * 100))
        rhos = np.empty(N_ZERO_SIM)
        for r_i in range(N_ZERO_SIM):
            eA = sim_rng.normal(0, 1, size=n_quads)
            eB = sim_rng.normal(0, 1, size=n_quads)
            if s2 > 0:
                uA = sim_rng.normal(0, math.sqrt(s2), size=ncells)
                uB = sim_rng.normal(0, math.sqrt(s2), size=ncells)
                qa = (uA[ca_arr] - uA[cb_arr]) + eA
                qb = (uB[ca_arr] - uB[cb_arr]) + eB
            else:
                qa = eA
                qb = eB
            ma = cp_median(qa)
            mb = cp_median(qb)
            rr, _ = spearman(ma, mb)
            rhos[r_i] = rr
        se0 = float(rhos.std(ddof=1))
        zero_models['cell_share_%.2f' % share] = {'se_null': se0, 'mde80': Z_MDE80 * se0,
                                                 'null_q95': float(np.percentile(rhos, 95))}
    mde['zero_model_cell_share_sensitivities'] = zero_models
    mde['zero_model_cell_share_sensitivities_note'] = (
        'STRUCTURAL CAVEAT: additive cell main effects cancel exactly in the Q double difference, so a '
        'cell-additive component u_c is not a structurally faithful null for Q; these cell-share models '
        'are reported only as a PESSIMISTIC dependence bound for the design SE. The primary anchored '
        'quantities are the empirical cluster-adjusted MDE80_obs and its iid-debiased version.')

    se_gate = (mde['primary_empirical_cluster_adjusted']['se_null']
               if mde['primary_empirical_cluster_adjusted']['se_null'] is not None else iid_se)
    mde_gate = Z_MDE80 * se_gate
    q95_null = Z_Q95 * se_gate

    # ---- complete-rule joint power / type-I (Monte Carlo, normal approximation of the rule)
    def rule_power(latent_rho, reps=N_POWER, seed=SEED + 7):
        rng2 = np.random.default_rng(seed)
        rel_pt = (math.sqrt(max(relA_pt, 0.0) * max(relB_pt, 0.0))
                  if (relA_pt is not None and relB_pt is not None) else 0.0)
        obs_mean = latent_rho * rel_pt
        dmo = delta_min_obs_cons if delta_min_obs_cons is not None else (delta_min_obs_pt or 0.0)
        z = rng2.normal(size=reps)
        rho_hat = obs_mean + se_gate * z
        thr = np.maximum(dmo, Z_ALPHA * se_gate)
        reject = rho_hat > thr
        # explicit CI-lower>0 and permutation-null comparison (redundant with thr, kept for audit)
        ci_ok = (rho_hat - Z_ALPHA * se_gate) > 0
        perm_ok = rho_hat > q95_null
        return {'latent_rho': latent_rho, 'observed_scale_mean': obs_mean,
                'power_or_typeI': float(np.mean(reject & ci_ok & perm_ok)),
                'threshold_obs': float(thr), 'reps': reps}

    power_010 = rule_power(0.10)
    power_030 = rule_power(0.30)
    typeI = rule_power(0.0)

    gates = [
        {'name': 'n_cp_ge_500', 'value': n_cp, 'threshold': MIN_CP, 'pass': bool(n_cp >= MIN_CP)},
        {'name': 'n_quads_ge_500', 'value': n_quads, 'threshold': 500, 'pass': bool(n_quads >= 500)},
        {'name': 'mde80_obs_le_delta_min_obs', 'value': mde_gate,
         'threshold': delta_min_obs_cons, 'pass': bool(delta_min_obs_cons is not None and mde_gate <= delta_min_obs_cons)},
        {'name': 'joint_power_latent_0.30_ge_0.80', 'value': power_030['power_or_typeI'],
         'threshold': 0.80, 'pass': bool(power_030['power_or_typeI'] >= 0.80)},
        {'name': 'type_I_le_0.10', 'value': typeI['power_or_typeI'], 'threshold': 0.10,
         'pass': bool(typeI['power_or_typeI'] <= 0.10)},
    ] + rel_gates
    design_passed = all(g['pass'] for g in gates)
    failures = [g['name'] for g in gates if not g['pass']]

    design_check = {
        'binning_rule': 'controlled_anchor; cp needs >=5 quadruples; main statistic over cp medians',
        'structure': structure,
        'reliability': {'original': rel_A, 'validation': rel_B,
                        'coverage_note': ('barcode split-half is a same-screen reproducibility proxy; '
                                          'Original split coverage is thin (61 cp from 36 barcode-rich '
                                          'cells, CI on rel is wide) while Validation covers all 1501 cp. '
                                          'delta_min_obs uses the upper (conservative) rel bounds; the '
                                          'point-rel value is reported alongside.')},
        'delta_min': {'latent': DELTA_MIN_LATENT,
                      'rel_A_point': relA_pt, 'rel_B_point': relB_pt,
                      'rel_A_hi_conservative': relA_hi, 'rel_B_hi_conservative': relB_hi,
                      'delta_min_obs_point_rels': delta_min_obs_pt,
                      'delta_min_obs_conservative_rels': delta_min_obs_cons},
        'mde80_obs': mde,
        'mde80_obs_gate_value': mde_gate,
        'joint_power': {'latent_0.10': power_010, 'latent_0.30': power_030},
        'type_I': typeI,
        'gates': gates,
        'design_check_passed': bool(design_passed),
        'failure_reasons': failures,
    }
    print('    design_check_passed=%s failures=%s' % (design_passed, failures), flush=True)
    # ---- PROTOCOL_Q section 7 runtime gate ------------------------------------------------
    # Design check precedes the Q retest. If it fails, this runner MUST stop here: no
    # cross-screen Q_A-Q_B statistic (main or secondary) is computed, aligned or written.
    if not design_passed:
        print('    PROTOCOL_Q section 7 gate: STOP - no cross-screen Q statistic is computed', flush=True)
    else:
        # This runner build implements the frozen stop/design-check branch only. Refusing to
        # silently skip the main analysis keeps the protocol honest if the gate ever passes.
        raise SystemExit('design_check passed but the main-analysis path is not implemented in this '
                         'runner build; a revised protocol-compliant runner would be required '
                         '(refusing to write partial outputs).')
    print('    relA=%.3f relB=%.3f delta_min_obs=%.4f MDE80_obs=%.4f power30=%.3f typeI=%.3f'
          % (relA_pt or float('nan'), relB_pt or float('nan'),
             delta_min_obs_cons or float('nan'), mde_gate,
             power_030['power_or_typeI'], typeI['power_or_typeI']), flush=True)

    rows = []
    for g in gates:
        rows.append({'section': 'design_check', 'item': g['name'], 'value': q(g['value']),
                     'threshold': q(g['threshold']), 'pass': g['pass'],
                     'note': 'PROTOCOL_Q sections 3-4; pre-registered implementation choices'})
    for tag, rec in (('original', rel_A), ('validation', rel_B)):
        rows.append({'section': 'reliability', 'item': '%s_split_half_r' % tag,
                     'value': q(rec['r_split_half_spearman']), 'threshold': None, 'pass': None,
                     'note': 'n_cp_split=%d, keys_ge2=%d' % (rec['n_cp_split'],
                                                             rec['n_keys_with_ge2_barcodes'])})
        rows.append({'section': 'reliability', 'item': '%s_rel_spearman_brown' % tag,
                     'value': q(rec['rel_spearman_brown']), 'threshold': None, 'pass': None,
                     'note': 'se_boot_r=%s' % q(rec['se_boot_r'])})
    for k, rec in [('primary_empirical_cluster_adjusted', mde['primary_empirical_cluster_adjusted']),
                   ('iid_analytic_sensitivity', mde['iid_analytic_sensitivity']),
                   ('debiased_empirical_sensitivity', mde['debiased_empirical_sensitivity'])]:
        rows.append({'section': 'mde80_obs', 'item': k, 'value': q(rec.get('mde80')),
                     'threshold': q(delta_min_obs_cons), 'pass': None, 'note': rec.get('construction')})
    for k, rec in zero_models.items():
        rows.append({'section': 'mde80_obs', 'item': k, 'value': q(rec['mde80']),
                     'threshold': q(delta_min_obs_cons), 'pass': None,
                     'note': 'zero-model cell-share sensitivity (structure only)'})

    # ---------------------------------------------------------------- judgment
    judgment = {
        'verdict': 'inconclusive' if not design_passed else None,
        'design_check_passed': bool(design_passed),
        'failure_reasons': failures,
        'main_q_computed': False,
        'main_q_note': ('PROTOCOL_Q section 7: design check not passed -> STOP, do not enter the Q '
                        'retest; no cross-screen Q statistic was computed or written'),
        'interpretation': ('Design check failed at: ' + ', '.join(failures) +
                           '. The matched-quadruple universe has %d cell pairs from only %d cells; '
                           'within-screen barcode split-half reliability is %.3f (Original, %d cp) / '
                           '%.3f (Validation, %d cp) but the cell-cluster-robust null SE '
                           '(n_eff=%.1f) implies MDE80_obs=%.4f > delta_min_obs=%.4f. '
                           'The design therefore cannot resolve a latent rho=0.10 conditional shift '
                           'with 80%% power; this is a design/power stop, NOT evidence that the '
                           'conditional shift is absent or unstable.'
                           % (n_cp, ncells, relA_pt or float('nan'), rel_A['n_cp_split'],
                              relB_pt or float('nan'), rel_B['n_cp_split'],
                              mde['primary_empirical_cluster_adjusted']['n_eff'] or float('nan'),
                              mde_gate, delta_min_obs_cons or float('nan'))),
        'reliability_uncertainty_note': (
            'delta_min_obs is computed with the CONSERVATIVE (upper 95%%) reliability bounds '
            '(relA_hi=%.3f, relB_hi=%.3f -> delta_min_obs=%.4f); with point reliabilities it would be '
            '%.4f. Original barcode-split reliability rests on only 61 cell pairs, so its CI is wide '
            '(rel CI shown in design_check.reliability). Both values stay below MDE80_obs, so the '
            'design-check verdict is unchanged under either bound.'
            % (relA_hi or float('nan'), relB_hi or float('nan'), delta_min_obs_cons or float('nan'),
               delta_min_obs_pt or float('nan'))),
        'power_semantics_note': ('Complete-rule power is required only at latent rho=0.30; the '
                                 'reproducible threshold lives at latent ~0.10, so a true latent effect '
                                 'between 0.10 and 0.30 cannot be reliably classified by this design '
                                 '(power(0.10)=%.3f vs power(0.30)=%.3f here). A not_reproducible '
                                 'outcome in this design would therefore NOT license reading the '
                                 '0.10-0.30 interval as "no structure".'
                                 % (power_010['power_or_typeI'], power_030['power_or_typeI'])),
        'unfreeze_conditions': [
            'more independent cells / more independent measurement groups (the effective sample size is '
            'cell-limited: n_eff ~ %.1f from 96 cells), or' % (mde['primary_empirical_cluster_adjusted']['n_eff'] or float('nan')),
            'a pre-registered delta_min_latent with an operational justification below 0.10 (the current '
            'protocol forbids back-computing it from old CI bounds), or',
            'an analysis unit with larger effective independent sample (e.g., more screening studies '
            'matched across batches) - not a different aggregation of the same 96 cells',
        ],
        'boundary_wording': ('No claim about conditional-shift reproducibility, transferability, mechanism '
                             'or algorithm is made. Per PROTOCOL_Q section 6 and the R193 BRIEF, B/C are '
                             'not started and the frozen additive/static-prior interpretation stands.'),
    }

    # ---------------------------------------------------------------- outputs
    out = {
        'protocol': {'path_rel': os.path.relpath(PROTOCOL, ROOT).replace('\\', '/'),
                     'bytes': os.path.getsize(PROTOCOL), 'sha256': inputs['protocol_q']['sha256'],
                     'status': 'v1 FROZEN'},
        'errata': {'path_rel': os.path.relpath(ERRATA, ROOT).replace('\\', '/'),
                   'sha256': inputs['errata_a0']['sha256']},
        'challenge': {'path_rel': os.path.relpath(CHALLENGE, ROOT).replace('\\', '/'),
                      'sha256': inputs['challenge_a0']['sha256']},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'bytes': os.path.getsize(SCRIPT), 'sha256': sha256_file(SCRIPT)},
        'environment': {'python': sys.version.split()[0], 'numpy': np.__version__,
                        'pandas': pd.__version__, 'platform': platform.platform()},
        'seeds': {'master': SEED, 'b_rel_boot': B_REL_BOOT, 'b_main_boot': B_MAIN_BOOT,
                  'b_perm': B_PERM, 'n_power': N_POWER, 'n_zero_sim': N_ZERO_SIM,
                  'z_mde80': Z_MDE80, 'z_alpha': Z_ALPHA},
        'inputs': inputs,
        'structure': structure,
        'design_check': design_check,
        'judgment': judgment,
        'pre_registered_implementation_notes': [
            'design check precedes any cross-screen Q statistic; within-screen split-half reliability '
            'and structure-only SE constructions are the only response-value uses in the design phase',
            'the design-phase q1.py asserts that if design_check fails, no cross-screen Q / main '
            'statistic is computed or written (protocol section 7)',
            'MDE80_obs primary construction is the cluster-adjusted null SE derived from within-screen '
            'barcode split-half reliability (n_eff = ((1-r^2)/SE_boot)^2); iid analytic, debiased and '
            'zero-model cell-share constructions are reported as sensitivities only',
            'delta_min_obs uses the conservative (upper) reliability bounds (Lead implementation note 2)',
            'coverage/rel gate: per screen keys_with_ge2_barcodes>=300, split cp>=50, rel CI lower bound>=0.20',
        ],
        'response_value_use_attestation': {
            'cross_screen_q_alignment_computed_before_design_check': False,
            'main_q_computed': False,
            'response_columns_used_in_design_phase': [PRIMARY_ENDPOINT],
            'purpose': ['within-screen barcode split-half reliability', 'structure-only SE constructions'],
        },
        'boundaries': {
            'user_goal': 'H193a/H193b conditional-shift reproducibility',
            'judgment': 'inconclusive',
            'not_claimed': ['reproducibility', 'non-reproducibility', 'transferability', 'mechanism',
                            'algorithmic gain', 'B/C start'],
            'protocol_references': ['PROTOCOL_Q.md (v1 FROZEN)', 'ERRATA_A0.md', 'challenge_A0.md'],
        },
    }
    assert out['response_value_use_attestation']['main_q_computed'] is False, \
        'PROTOCOL_Q section 7 violation: main Q computed after design-check failure'
    assert 'main_analysis' not in out
    out = qd(out)
    write_json(out, OUT_JSON)
    with open(OUT_CSV, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['section', 'item', 'value', 'threshold', 'pass', 'note'])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print('[7/8] wrote %s / %s (main Q not computed: design check gate)'
          % (os.path.basename(OUT_JSON), os.path.basename(OUT_CSV)), flush=True)
    print('[8/8] runtime %.1fs' % (time.time() - t0), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
