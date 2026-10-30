"""Shared implementation for R192-R2 stage-2 preflight / effect run (v3 frozen).

Implements the frozen v3 protocol pieces:
  research/2026-10-27-drugcomb-replication/PROTOCOL_STAGE2.md (v1)
  + AMENDMENT-001.md + AMENDMENT-002.md (v3 frozen; v3 governs conflicts)

Reads ONLY identity columns (block_id/drug_row/drug_col/cell_line_name) and the
frozen primary endpoint synergy_bliss (P-B aggregation rule).  The primary CI and
the pre-flight MDE use the P-B2 Regime B **pair x cell** two-way cluster bootstrap
(AMENDMENT-002 final version).  No timestamps; deterministic seeds; sorted JSON.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import unicodedata

import numpy as np

ROOT = r'D:\MAESTRO'
OUT = os.path.join(ROOT, 'research', '2026-10-27-drugcomb-replication')
ANN = os.path.join(ROOT, 'research', '2026-10-27-drugcomb-annotation')
END = os.path.join(ROOT, 'research', '2026-10-27-drugcomb-endpoint')
QUAL = os.path.join(ROOT, 'research', '2026-10-27-drugcomb-qualification')

V14 = os.path.join(QUAL, 'downloads', 'summary_table_v1.4.csv')
MAP2 = os.path.join(ANN, 'mapping_table_v2.csv')
MAP1 = os.path.join(ANN, 'mapping_table.csv')
PROTOCOL_STAGE2 = os.path.join(OUT, 'PROTOCOL_STAGE2.md')
AMEND1 = os.path.join(OUT, 'AMENDMENT-001.md')
AMEND2 = os.path.join(OUT, 'AMENDMENT-002.md')
PB_PROTOCOL = os.path.join(END, 'PROTOCOL_PB.md')
PB_JSON = os.path.join(END, 'pb.json')
PB2_PROTOCOL = os.path.join(END, 'PROTOCOL_PB2.md')
PB2_JSON = os.path.join(END, 'pb2.json')
PREFLIGHT_JSON = os.path.join(OUT, 'preflight.json')
STAGE2_JSON = os.path.join(OUT, 'stage2.json')
SCRIPT_PREFLIGHT = os.path.join(OUT, 'preflight.py')
SCRIPT_STAGE2 = os.path.join(OUT, 'stage2.py')
SCRIPT_LIB = os.path.join(OUT, 's2lib.py')

JAAKS_ORIG = os.path.join(ROOT, 'data/external/gdsc_combinations/jaaks2022_figshare',
                          'Original screen_All tissues_fitted data.csv')
JAAKS_VAL = os.path.join(ROOT, 'data/external/gdsc_combinations/jaaks2022_figshare',
                         'Validation screen_All tissues_fitted data.csv')

# ---- frozen constants -------------------------------------------------------
DELTA_MIN = 0.0947                     # AMENDMENT-001 section 2 (R1)
Z_MDE80 = 2.801585218112968            # P-B2 / P-B frozen MDE80 multiplier
ALPHA_Z = 1.959963984540054
SEED_MASTER = 20261027                 # R2/R3 pair x cell bootstrap seed (v3 section 1)
SEED2 = 20261028                       # P-B2 design seed base
LAMBDA_GRID = [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0]
N_FOLDS = 3
N_RANDOM = 10
N_SIZE_MATCHED = 5
N_BOOT_MDE = 2000                      # F3(a) P-B2 frozen B
N_BOOT_CI = 1000                       # R2/R3 (v3)
N_POWER_REPS = 2000                    # F3(b) analytic joint power draws
RANDOM_SEEDS = [SEED_MASTER + 100 + i for i in range(N_RANDOM)]
CAPACITY_SEED = SEED_MASTER + 9001
PROXY_BINS = 20

SHA_EXPECT = {
    'v14_summary': 'E08E3D35BFA4BEA011AFE1B05B7025ACDE5C669C5E8D265866B5E12B08037A2F',
    'mapping_v2': '705A5E6476319B587C9B5E852590BAEF817CEC7B8C4D69B0A54EC7CC686ED015',
    'mapping_v1': '45EDE63521DC44FEFEC52D717765B4D2BA7D08EC3FDE4372811C4D516DE038D4',
}
NULLISH = {'', 'NA', 'NULL', 'NAN', '\\N'}


# ---------------------------------------------------------------- primitives
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest().upper()


def sha256_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest().upper()


def norm(s):
    s = unicodedata.normalize('NFKC', str(s)).casefold()
    return ''.join(ch for ch in s if ch.isalnum())


def parse_float(s):
    if s is None:
        return np.nan
    s = s.strip()
    if s == '' or s.upper() in NULLISH:
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


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
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(qd(obj), fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write('\n')


def spearman(x, y):
    from scipy.stats import rankdata
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if x.size < 3:
        return float('nan')
    rx = rankdata(x)
    ry = rankdata(y)
    rx -= rx.mean()
    ry -= ry.mean()
    den = math.sqrt(float(rx @ rx) * float(ry @ ry))
    return float('nan') if den == 0 else float(rx @ ry / den)


# ---------------------------------------------------------------- input hashes
def hash_inputs():
    files = {
        'v14_summary': V14,
        'mapping_v2': MAP2,
        'mapping_v1': MAP1,
        'protocol_stage2_v1': PROTOCOL_STAGE2,
        'amendment_001': AMEND1,
        'amendment_002': AMEND2,
        'protocol_pb': PB_PROTOCOL,
        'pb_json': PB_JSON,
        'protocol_pb2': PB2_PROTOCOL,
        'pb2_json': PB2_JSON,
        'script_lib': SCRIPT_LIB,
    }
    out = {}
    for k, p in sorted(files.items()):
        if os.path.exists(p):
            out[k] = {'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'),
                      'bytes': os.path.getsize(p), 'sha256': sha256_file(p), 'status': 'ok'}
        else:
            out[k] = {'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'), 'status': 'missing'}
    for tag, p in (('script_preflight', SCRIPT_PREFLIGHT), ('script_stage2', SCRIPT_STAGE2)):
        if os.path.exists(p):
            out[tag] = {'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'),
                        'bytes': os.path.getsize(p), 'sha256': sha256_file(p)}
    return out


# ---------------------------------------------------------------- data loading
def load_mapping(path):
    """dict drug_norm -> pathway label for source_library == 'S1' (and not unmapped)."""
    mapped, n_rows, n_s1 = {}, 0, 0
    with open(path, newline='', encoding='utf-8') as fh:
        rdr = csv.DictReader(fh)
        for row in rdr:
            n_rows += 1
            if row['source_library'] != 'S1':
                continue
            n_s1 += 1
            pw = row['pathway'].strip()
            if pw.lower() == 'unmapped':
                continue
            mapped[row['drug_normalized_name'].strip()] = pw
    return {'mapped': mapped, 'n_rows': n_rows, 'n_s1_rows': n_s1,
            'n_mapped': len(mapped), 'levels': sorted(set(mapped.values()))}


def load_v14():
    """Stream v1.4 summary once; P-B frozen aggregation: mean synergy_bliss per unit."""
    cap = 700_000
    n = 0
    rows_total = mono = 0
    blk = np.empty(cap, np.int64)
    unit_code = np.empty(cap, np.int32)
    pair_code = np.empty(cap, np.int32)
    cell_code = np.empty(cap, np.int32)
    vals = np.empty(cap, float)
    umap, pmap, cmap, dmap = {}, {}, {}, {}
    ukeys, pkeys, cnames, dnames = [], [], [], []

    def enc(s, mp, lst):
        v = mp.get(s)
        if v is None:
            v = len(lst)
            mp[s] = v
            lst.append(s)
        return v

    with open(V14, newline='', encoding='utf-8') as fh:
        rdr = csv.reader(fh)
        header = next(rdr)
        col = {c: i for i, c in enumerate(header)}
        i_b, i_dr, i_dc, i_cl, i_y = (col['block_id'], col['drug_row'], col['drug_col'],
                                      col['cell_line_name'], col['synergy_bliss'])
        for row in rdr:
            rows_total += 1
            dr, dc, cl = row[i_dr].strip(), row[i_dc].strip(), row[i_cl].strip()
            if dr.upper() in NULLISH or dc.upper() in NULLISH:
                mono += 1
                continue
            ndr, ndc, ncl = norm(dr), norm(dc), norm(cl)
            a, b = (ndr, ndc) if ndr <= ndc else (ndc, ndr)
            pk = enc(a + '\x1f' + b, pmap, pkeys)
            uk = enc(ncl + '\x1f' + a + '\x1f' + b, umap, ukeys)
            ck = enc(ncl, cmap, cnames)
            dk = enc(a, dmap, dnames)
            enc(b, dmap, dnames)
            if n >= cap:
                newcap = int(cap * 1.5)
                nb = np.empty(newcap, np.int64); nb[:n] = blk[:n]; blk = nb
                nu = np.empty(newcap, np.int32); nu[:n] = unit_code[:n]; unit_code = nu
                np2 = np.empty(newcap, np.int32); np2[:n] = pair_code[:n]; pair_code = np2
                nc = np.empty(newcap, np.int32); nc[:n] = cell_code[:n]; cell_code = nc
                nv = np.empty(newcap, float); nv[:n] = vals[:n]; vals = nv
                cap = newcap
            try:
                blk[n] = int(row[i_b])
            except (TypeError, ValueError):
                blk[n] = -1
            unit_code[n] = uk
            pair_code[n] = pk
            cell_code[n] = ck
            vals[n] = parse_float(row[i_y])
            n += 1
    n_units = len(ukeys)
    unit_pair = np.zeros(n_units, np.int64)
    unit_cell = np.zeros(n_units, np.int64)
    unit_pair[unit_code] = pair_code
    unit_cell[unit_code] = cell_code
    ok = np.isfinite(vals[:n])
    cnt = np.bincount(unit_code[:n][ok], minlength=n_units).astype(np.int64)
    sums = np.bincount(unit_code[:n][ok], weights=vals[:n][ok], minlength=n_units)
    y = np.full(n_units, np.nan)
    have = cnt > 0
    y[have] = sums[have] / cnt[have]
    pair_a = np.empty(len(pkeys), np.int32)
    pair_b = np.empty(len(pkeys), np.int32)
    for i, k in enumerate(pkeys):
        a, b = k.split('\x1f')
        pair_a[i] = dmap[a]
        pair_b[i] = dmap[b]
    # P-B design-era proxy: block_id 20-quantile bins -> unit modal bin
    edges = np.percentile(blk, np.linspace(0, 100, PROXY_BINS + 1))
    bbin = np.digitize(blk, edges[1:-1])
    counts = np.zeros((n_units, PROXY_BINS), np.int64)
    np.add.at(counts, (unit_code, bbin), 1)
    unit_bin = np.argmax(counts, axis=1).astype(np.int64)
    return {
        'header': header, 'rows_total': rows_total, 'rows_monotherapy_like': mono,
        'n_blocks_combo': n, 'n_blocks_finite': int(ok.sum()), 'n_units': n_units,
        'drug_names': dnames, 'cell_names': cnames, 'n_pairs': len(pkeys),
        'unit_pair': unit_pair, 'unit_cell': unit_cell, 'y': y, 'unit_size': cnt,
        'pair_a': pair_a, 'pair_b': pair_b, 'unit_bin': unit_bin,
        'block_bin_edges': edges, 'y_missing_units': int((~have).sum()),
    }


def drug_level_arrays(data, mapped):
    """Global drug name -> label id arrays for a mapping dict; levels sorted."""
    drugs = data['drug_names']
    vocab = sorted(set(mapped.values()))
    vidx = {l: i for i, l in enumerate(vocab)}
    lab = np.full(len(drugs), -1, np.int64)
    for i, d in enumerate(drugs):
        p = mapped.get(d)
        if p is not None:
            lab[i] = vidx[p]
    return lab, vocab


def label_dict_from_array(data, lab):
    out = {}
    for i, d in enumerate(data['drug_names']):
        if lab[i] >= 0:
            out[d] = int(lab[i])
    return out


def split_permutation(names, r, seed=SEED_MASTER):
    """v3 section 4: numpy default_rng(seed), sorted names, permutation, first k."""
    names = sorted(names)
    N = len(names)
    k = max(1, int(round(r * N)))
    rng = np.random.default_rng(seed)
    perm = rng.permutation(N)
    H = set(names[i] for i in perm[:k])
    return H, k, N, sha256_text('\n'.join(sorted(H)))


def build_pools(data, lab, H):
    drugs = data['drug_names']
    pair_a, pair_b = data['pair_a'], data['pair_b']
    a_in = np.array([drugs[d] in H for d in pair_a])
    b_in = np.array([drugs[d] in H for d in pair_b])
    a_map = lab[pair_a] >= 0
    b_map = lab[pair_b] >= 0
    test_pair = a_in & b_in
    train_pair = (~a_in) & (~b_in) & a_map & b_map
    up = data['unit_pair']
    unit_ann = a_map[up] & b_map[up]
    y_ok = np.isfinite(data['y'])
    test_units = np.where(test_pair[up] & unit_ann & y_ok)[0]
    train_units = np.where(train_pair[up] & unit_ann & y_ok)[0]
    return {'test_units': test_units, 'train_units': train_units,
            'test_pair': test_pair, 'train_pair': train_pair}


def pool_summary(data, units):
    return {'n_units': int(len(units)),
            'n_pairs': int(np.unique(data['unit_pair'][units]).size),
            'n_cells': int(np.unique(data['unit_cell'][units]).size)}


def analyzable_levels(data, lab, H, train_units):
    """F2: >=2 mapped drugs overall and level appears in BOTH train and holdout drug sets."""
    from collections import Counter
    drugs = data['drug_names']
    up = data['unit_pair']
    pa, pb = data['pair_a'], data['pair_b']
    drugs_train = {drugs[d] for u in train_units for d in (pa[up[u]], pb[up[u]])}
    lev_all = {d: int(lab[i]) for i, d in enumerate(drugs) if lab[i] >= 0}
    cnt = Counter(lev_all.values())
    train_lev = {lev_all[d] for d in drugs_train if d in lev_all}
    hold_lev = {lev_all[d] for d in H if d in lev_all}
    ok = [l for l, c in cnt.items() if c >= 2 and l in train_lev and l in hold_lev]
    return {'n_levels_total': len(cnt), 'n_levels_ge2': int(sum(1 for c in cnt.values() if c >= 2)),
            'n_analyzable': len(ok), 'analyzable_level_ids': sorted(int(x) for x in ok),
            'n_train_levels': len(train_lev), 'n_holdout_levels': len(hold_lev)}


# ---------------------------------------------------------------- ridge machinery
def _gram_binary(D, L, i, j, p, q, y, include_identity=True):
    """Gram + rhs for features [anchor_id(D), lib_id(D), anchor_ann(L), lib_ann(L)]."""
    n = len(i)
    off = (2 * D) if include_identity else 0
    K = off + 2 * L
    G = np.zeros((K, K))
    if include_identity:
        ci = np.bincount(i, minlength=D).astype(float)
        cj = np.bincount(j, minlength=D).astype(float)
        idx = np.arange(D)
        G[idx, idx] = ci
        G[D + idx, D + idx] = cj
        co = np.bincount(i * D + j, minlength=D * D).reshape(D, D).astype(float)
        G[:D, D:2 * D] = co
        G[D:2 * D, :D] = co.T
        gia = np.bincount(i * L + p, minlength=D * L).reshape(D, L).astype(float)
        gib = np.bincount(i * L + q, minlength=D * L).reshape(D, L).astype(float)
        gja = np.bincount(j * L + p, minlength=D * L).reshape(D, L).astype(float)
        gjb = np.bincount(j * L + q, minlength=D * L).reshape(D, L).astype(float)
        o = 2 * D
        G[:D, o:o + L] = gia; G[o:o + L, :D] = gia.T
        G[:D, o + L:] = gib; G[o + L:, :D] = gib.T
        G[D:2 * D, o:o + L] = gja; G[o:o + L, D:2 * D] = gja.T
        G[D:2 * D, o + L:] = gjb; G[o + L:, D:2 * D] = gjb.T
    o = off
    gpp = np.bincount(p * L + p, minlength=L * L).reshape(L, L).astype(float)
    gpq = np.bincount(p * L + q, minlength=L * L).reshape(L, L).astype(float)
    gqq = np.bincount(q * L + q, minlength=L * L).reshape(L, L).astype(float)
    G[o:o + L, o:o + L] = gpp
    G[o:o + L, o + L:] = gpq
    G[o + L:, o:o + L] = gpq.T
    G[o + L:, o + L:] = gqq
    rhs = np.concatenate([
        np.bincount(i, weights=y, minlength=D) if include_identity else np.zeros(0),
        np.bincount(j, weights=y, minlength=D) if include_identity else np.zeros(0),
        np.bincount(p, weights=y, minlength=L),
        np.bincount(q, weights=y, minlength=L)])
    return G, rhs, n, off


def _gram_extra(D, L, i, j, p, q, C, y, include_identity=True):
    G, rhs, n, off = _gram_binary(D, L, i, j, p, q, y, include_identity)
    R = C.shape[1]
    K = off + 2 * L
    Gfull = np.zeros((K + R, K + R))
    Gfull[:K, :K] = G
    Gfull[K:, K:] = C.T @ C
    if include_identity:
        Ac = np.zeros((D, R)); np.add.at(Ac, i, C)
        Bc = np.zeros((D, R)); np.add.at(Bc, j, C)
        Gfull[:D, K:] = Ac; Gfull[K:, :D] = Ac.T
        Gfull[D:2 * D, K:] = Bc; Gfull[K:, D:2 * D] = Bc.T
    o = off
    Pc = np.zeros((L, R)); np.add.at(Pc, p, C)
    Qc = np.zeros((L, R)); np.add.at(Qc, q, C)
    Gfull[o:o + L, K:] = Pc; Gfull[K:, o:o + L] = Pc.T
    Gfull[o + L:o + 2 * L, K:] = Qc; Gfull[K:, o + L:o + 2 * L] = Qc.T
    rhsfull = np.concatenate([rhs, C.T @ y])
    return Gfull, rhsfull, n, off


class BinaryRidge:
    """Ridge on binary identity+annotation features (+ optional dense extras).

    Standardization statistics are fitted ONLY on the rows passed to .fit()
    (per inner fold / outer training pool).  Test rows have all identity
    indicators zero, so ranking is driven by annotation (and extra) columns.
    """

    def __init__(self, include_identity=True):
        self.include_identity = include_identity

    def fit(self, D, L, i, j, p, q, y, lambdas=LAMBDA_GRID, extra=None):
        if extra is None:
            G, rhs, n, off = _gram_binary(D, L, i, j, p, q, y, self.include_identity)
            R = 0
        else:
            extra = np.asarray(extra, float)
            G, rhs, n, off = _gram_extra(D, L, i, j, p, q, extra, y, self.include_identity)
            R = extra.shape[1]
        nb = off + 2 * L
        counts = np.zeros(nb, float)
        if self.include_identity:
            counts[:D] = np.bincount(i, minlength=D)
            counts[D:2 * D] = np.bincount(j, minlength=D)
        counts[off:off + L] = np.bincount(p, minlength=L)
        counts[off + L:off + 2 * L] = np.bincount(q, minlength=L)
        mu = counts / n
        sd = np.sqrt(np.maximum(mu * (1 - mu), 1e-12))
        if R:
            mu_x = extra.mean(axis=0)
            sd_x = extra.std(axis=0, ddof=0)
            sd_x[sd_x <= 0] = 1.0
            mu = np.concatenate([mu, mu_x])
            sd = np.concatenate([sd, sd_x])
        Gc = G - n * np.outer(mu, mu)
        b = rhs - mu * float(y.sum())
        Gs = Gc / np.outer(sd, sd)
        ev, V = np.linalg.eigh(Gs)
        alpha = V.T @ (b / sd)
        self.ev, self.V, self.alpha, self.sd, self.mu = ev, V, alpha, sd, mu
        self.off, self.L, self.D, self.R = off, L, D, R
        self.ybar = float(y.mean())
        self.W = {lam: (V @ (alpha / (ev + lam))) for lam in lambdas}
        return self

    def scores(self, lam, p, q, extra=None):
        w = self.W[lam]
        s = np.zeros(len(p), float)
        vp = p >= 0
        s[vp] += w[self.off + p[vp]] / self.sd[self.off + p[vp]]
        vq = q >= 0
        s[vq] += w[self.off + self.L + q[vq]] / self.sd[self.off + self.L + q[vq]]
        if extra is not None and self.R:
            extra = np.asarray(extra, float)
            s += ((extra - self.mu[-self.R:]) / self.sd[-self.R:]) @ w[-self.R:]
        return s


def encode_train(train_drugs, units, data, labels):
    drugs = data['drug_names']
    name_to_pos = {nm: k for k, nm in enumerate(train_drugs)}
    dpos = np.full(len(drugs), -1, np.int64)
    for di, nm in enumerate(drugs):
        pos = name_to_pos.get(nm)
        if pos is not None:
            dpos[di] = pos
    tlevels = sorted({labels[d] for d in train_drugs if d in labels})
    lpos = {lv: k for k, lv in enumerate(tlevels)}
    up = data['unit_pair'][units]
    da = data['pair_a'][up]
    db = data['pair_b'][up]
    i = dpos[da]
    j = dpos[db]
    p = np.array([lpos.get(labels.get(drugs[d], -1), -1) for d in da], np.int64)
    q = np.array([lpos.get(labels.get(drugs[d], -1), -1) for d in db], np.int64)
    if (i < 0).any() or (p < 0).any() or (q < 0).any():
        raise AssertionError('encode_train: row outside train drug/label set')
    return {'D': len(train_drugs), 'L': len(tlevels), 'i': i, 'j': j, 'p': p, 'q': q,
            'levels': tlevels}


def encode_eval(train_drugs, levels, units, data, labels):
    drugs = data['drug_names']
    dpos = {nm: k for k, nm in enumerate(train_drugs)}
    lpos = {lv: k for k, lv in enumerate(levels)}
    up = data['unit_pair'][units]
    da = data['pair_a'][up]
    db = data['pair_b'][up]
    i = np.array([dpos.get(drugs[d], -1) for d in da], np.int64)
    j = np.array([dpos.get(drugs[d], -1) for d in db], np.int64)
    p = np.array([lpos.get(labels.get(drugs[d], -1), -1) for d in da], np.int64)
    q = np.array([lpos.get(labels.get(drugs[d], -1), -1) for d in db], np.int64)
    return i, j, p, q


def inner_folds(train_drugs, n_folds=N_FOLDS):
    return [list(train_drugs[k::n_folds]) for k in range(n_folds)]


def fit_arm(train_units, test_units, data, labels, include_identity=True,
            lambdas=LAMBDA_GRID, extra_train=None, extra_test=None):
    """Inner 3-fold by-drug lambda selection (both-unseen inner validation) + final fit."""
    drugs = data['drug_names']
    up = data['unit_pair']
    pa, pb = data['pair_a'], data['pair_b']
    train_drugs = sorted({drugs[d] for u in train_units for d in (pa[up[u]], pb[up[u]])})
    pos_train = {int(u): k for k, u in enumerate(train_units)}
    fold_scores = {}
    for fk, fold in enumerate(inner_folds(train_drugs)):
        fold_set = set(fold)
        inner_train = [d for d in train_drugs if d not in fold_set]
        inner_train_set = set(inner_train)
        itr, iva = [], []
        for u in train_units:
            a = drugs[pa[up[u]]]
            b = drugs[pb[up[u]]]
            if a in inner_train_set and b in inner_train_set:
                itr.append(int(u))
            elif a in fold_set and b in fold_set:
                iva.append(int(u))
        itr = np.array(itr, dtype=np.int64)
        iva = np.array(iva, dtype=np.int64)
        if len(itr) < 30 or len(iva) < 10:
            fold_scores[fk] = {lam: float('nan') for lam in lambdas}
            continue
        enc_tr = encode_train(inner_train, itr, data, labels)
        enc_va = encode_eval(inner_train, enc_tr['levels'], iva, data, labels)
        ex_tr = extra_train[[pos_train[u] for u in itr]] if extra_train is not None else None
        ex_va = extra_train[[pos_train[u] for u in iva]] if extra_train is not None else None
        model = BinaryRidge(include_identity).fit(
            enc_tr['D'], enc_tr['L'], enc_tr['i'], enc_tr['j'], enc_tr['p'], enc_tr['q'],
            data['y'][itr], lambdas=lambdas, extra=ex_tr)
        yv = data['y'][iva]
        fold_scores[fk] = {}
        for lam in lambdas:
            sc = model.scores(lam, enc_va[2], enc_va[3], extra=ex_va)
            fold_scores[fk][lam] = spearman(sc, yv) if np.std(sc) > 0 else float('nan')
    agg = {}
    for lam in lambdas:
        vals = [fold_scores[fk][lam] for fk in fold_scores if math.isfinite(fold_scores[fk][lam])]
        agg[lam] = float(np.mean(vals)) if vals else float('-inf')
    best_lam = max(lambdas, key=lambda l: (agg[l], -l))
    enc_full = encode_train(train_drugs, train_units, data, labels)
    ex_full = extra_train
    final = BinaryRidge(include_identity).fit(
        enc_full['D'], enc_full['L'], enc_full['i'], enc_full['j'], enc_full['p'], enc_full['q'],
        data['y'][train_units], lambdas=[best_lam], extra=ex_full)
    enc_test = encode_eval(train_drugs, enc_full['levels'], test_units, data, labels)
    pred = final.scores(best_lam, enc_test[2], enc_test[3], extra=extra_test)
    return {'pred': pred, 'lambda': float(best_lam),
            'fold_scores': {str(fk): {str(l): q(v) for l, v in sv.items()}
                            for fk, sv in fold_scores.items()},
            'fold_mean': {str(l): q(v) for l, v in agg.items()},
            'D': enc_full['D'], 'L': enc_full['L'], 'train_drugs': train_drugs,
            'train_levels': [int(x) for x in enc_full['levels']],
            'identity_unseen': bool(np.all(enc_test[0] < 0) and np.all(enc_test[1] < 0))}


# ---------------------------------------------------------------- bootstrap
def _boot_idx(rng, pair_idx, cell_idx, npairs, ncells):
    cp = np.bincount(rng.integers(0, npairs, npairs), minlength=npairs)
    cc = np.bincount(rng.integers(0, ncells, ncells), minlength=ncells)
    return np.repeat(np.arange(len(pair_idx)), cp[pair_idx] * cc[cell_idx])


def bootstrap_rho_pair_cell(y, preds, pair_idx, cell_idx, npairs, ncells,
                            B=N_BOOT_CI, seed=SEED_MASTER):
    """P-B2 Regime B: resample pairs AND cells; weights = mult_pair * mult_cell."""
    from scipy.stats import rankdata
    rng = np.random.default_rng(seed)
    ro = np.arange(len(y))
    keys = list(preds.keys())
    out = {k: np.empty(B) for k in keys}
    for b in range(B):
        idx = _boot_idx(rng, pair_idx, cell_idx, npairs, ncells)
        ry = rankdata(y[idx]); ry -= ry.mean(); ny = float(ry @ ry)
        for k in keys:
            rp = rankdata(preds[k][idx]); rp -= rp.mean()
            den = math.sqrt(float(rp @ rp) * ny)
            out[k][b] = float(rp @ ry / den) if den > 0 else float('nan')
    return out


def bootstrap_rho_pairs(y, preds, pair_idx, npairs, B=N_BOOT_CI, seed=SEED_MASTER):
    """Diagnostic: pair-clustered-only bootstrap (no cell resampling)."""
    from scipy.stats import rankdata
    rng = np.random.default_rng(seed)
    ro = np.arange(len(y))
    keys = list(preds.keys())
    out = {k: np.empty(B) for k in keys}
    for b in range(B):
        cp = np.bincount(rng.integers(0, npairs, npairs), minlength=npairs)
        idx = np.repeat(ro, cp[pair_idx])
        ry = rankdata(y[idx]); ry -= ry.mean(); ny = float(ry @ ry)
        for k in keys:
            rp = rankdata(preds[k][idx]); rp -= rp.mean()
            den = math.sqrt(float(rp @ rp) * ny)
            out[k][b] = float(rp @ ry / den) if den > 0 else float('nan')
    return out


def bootstrap_null_pair_z(y, pair_idx, cell_idx, npairs, ncells, B=N_BOOT_MDE,
                          seed=SEED_MASTER):
    """Diagnostic sanity check of the pair x cell bootstrap on an iid pair-level null
    prediction (fixed z, resampling only): used to compare with the F3(a) SE."""
    from scipy.stats import rankdata
    rng = np.random.default_rng(seed)
    z = rng.normal(size=npairs)
    pred = z[pair_idx]
    ro = np.arange(len(y))
    arr = np.empty(B)
    for b in range(B):
        idx = _boot_idx(rng, pair_idx, cell_idx, npairs, ncells)
        ry = rankdata(y[idx]); ry -= ry.mean()
        rp = rankdata(pred[idx]); rp -= rp.mean()
        den = math.sqrt(float(rp @ rp) * float(ry @ ry))
        arr[b] = float(rp @ ry / den) if den > 0 else float('nan')
    return arr


def bootstrap_rho_drugs(y, preds, a_idx, b_idx, ndrugs, B=N_BOOT_CI, seed=SEED_MASTER):
    """Sensitivity: held-out-drug two-way (anchor-drug x library-drug) cluster bootstrap."""
    from scipy.stats import rankdata
    rng = np.random.default_rng(seed)
    ro = np.arange(len(y))
    keys = list(preds.keys())
    out = {k: np.empty(B) for k in keys}
    for b in range(B):
        ca = np.bincount(rng.integers(0, ndrugs, ndrugs), minlength=ndrugs)
        cb = np.bincount(rng.integers(0, ndrugs, ndrugs), minlength=ndrugs)
        idx = np.repeat(ro, ca[a_idx] * cb[b_idx])
        ry = rankdata(y[idx]); ry -= ry.mean(); ny = float(ry @ ry)
        for k in keys:
            rp = rankdata(preds[k][idx]); rp -= rp.mean()
            den = math.sqrt(float(rp @ rp) * ny)
            out[k][b] = float(rp @ ry / den) if den > 0 else float('nan')
    return out


def boot_ci(arr):
    arr = np.asarray(arr, float)
    return {'mean': q(float(arr.mean())), 'ci_lower': q(float(np.quantile(arr, 0.025))),
            'ci_upper': q(float(np.quantile(arr, 0.975))), 'se': q(float(arr.std(ddof=1))),
            'B': int(arr.size)}


# ---------------------------------------------------------------- random arms
def random_label_assignments(data, lab, n_random=N_RANDOM, n_size_matched=N_SIZE_MATCHED):
    """10 fixed-seed drug<->annotation reassignments: 5 size-matched + 5 uniform."""
    drugs = data['drug_names']
    mapped = [(i, d) for i, d in enumerate(drugs) if lab[i] >= 0]
    names = [d for _, d in mapped]
    vals = np.array([int(lab[i]) for i, _ in mapped], np.int64)
    vocab = int(lab.max()) + 1
    out = []
    li = 0
    for k in range(n_size_matched):
        seed = RANDOM_SEEDS[li]; li += 1
        rng = np.random.default_rng(seed)
        new = vals[rng.permutation(len(vals))]
        out.append({'kind': 'size_matched', 'seed': seed,
                    'labels': {nm: int(v) for nm, v in zip(names, new)},
                    'multiset_preserved': bool(sorted(new.tolist()) == sorted(vals.tolist()))})
    for k in range(n_random - n_size_matched):
        seed = RANDOM_SEEDS[li]; li += 1
        rng = np.random.default_rng(seed)
        new = rng.integers(0, vocab, size=len(vals))
        out.append({'kind': 'uniform', 'seed': seed,
                    'labels': {nm: int(v) for nm, v in zip(names, new)},
                    'multiset_preserved': bool(sorted(new.tolist()) == sorted(vals.tolist()))})
    return out


def random_feature_matrix(unit_ids, R, seed):
    """Deterministic per-unit Gaussian features (rows in sorted unit-id order)."""
    order = np.sort(np.unique(np.asarray(unit_ids, np.int64)))
    rng = np.random.default_rng(seed)
    C = rng.normal(size=(len(order), R))
    pos = {int(u): k for k, u in enumerate(order)}
    return C, pos


# ---------------------------------------------------------------- metrics
def top_quartile_auc(pred, y):
    from scipy.stats import rankdata
    if len(y) < 4:
        return None
    thr = np.quantile(y, 0.75)
    pos = np.asarray(y) >= thr
    npos = int(pos.sum())
    nneg = int(len(y) - npos)
    if npos == 0 or nneg == 0:
        return None
    r = rankdata(pred)
    return float((float(r[pos].sum()) - npos * (npos + 1) / 2.0) / (npos * nneg))


def topk_hits(pred, y, k=100):
    if len(y) <= k:
        return None
    idx = np.argsort(-np.asarray(pred), kind='stable')[:k]
    thr = np.quantile(y, 0.75)
    return float(np.mean(np.asarray(y)[idx] >= thr))


# ---------------------------------------------------------------- self test
def selftest_binary_ridge(seed=20261027):
    """Verify the Gram/standardization/eigen path against a dense reference."""
    rng = np.random.default_rng(seed)
    n, D, L, R = 120, 7, 4, 3
    i = rng.integers(0, D, n); j = rng.integers(0, D, n)
    p = rng.integers(0, L, n); q = rng.integers(0, L, n)
    y = rng.normal(size=n) + 0.3 * p + 0.2 * q
    C = rng.normal(size=(n, R))
    for extra in (None, C):
        model = BinaryRidge(True).fit(D, L, i, j, p, q, y, lambdas=[1.0, 10.0], extra=extra)
        mu = np.concatenate([np.eye(D)[i].mean(0), np.eye(D)[j].mean(0),
                             np.eye(L)[p].mean(0), np.eye(L)[q].mean(0)])
        sd = np.sqrt(np.maximum(mu * (1 - mu), 1e-12))
        X = np.hstack([np.eye(D)[i], np.eye(D)[j], np.eye(L)[p], np.eye(L)[q]])
        if extra is not None:
            mu_x = C.mean(0); sd_x = C.std(0); sd_x[sd_x <= 0] = 1.0
            mu = np.concatenate([mu, mu_x]); sd = np.concatenate([sd, sd_x])
            X = np.hstack([X, C])
        Xc = (X - mu) / sd
        for lam in (1.0, 10.0):
            w_ref = np.linalg.solve(Xc.T @ Xc + lam * np.eye(Xc.shape[1]),
                                    Xc.T @ (y - y.mean()))
            err = float(np.max(np.abs(model.W[lam] - w_ref)))
            if err > 1e-6:
                raise AssertionError('BinaryRidge self-test failed: err=%g extra=%s' % (err, extra is not None))
    return True
