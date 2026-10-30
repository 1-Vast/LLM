"""R192-PB2: MDE80 / power on the ANNOTATED analysis universe; stage-2 reopenability.

Implements PROTOCOL_PB2.md (frozen before the first run). Zero-model / power only:
NO identity/annotation model is fitted and NO effect is estimated. The response column
used is ONLY the frozen P-B primary endpoint (synergy_bliss, block mean per cell x pair).

Run:  & D:\\anaconda\\envs\\maestro\\python.exe research\\2026-10-27-drugcomb-endpoint\\pb2.py
Out:  pb2.json (next to this script). P-B artifacts are hashed before/after and must be unchanged.
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import math
import os
import platform
import re
import sys
import time
import unicodedata

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
QUAL = os.path.join(ROOT, 'research', '2026-10-27-drugcomb-qualification')
PA = os.path.join(ROOT, 'research', '2026-10-27-drugcomb-annotation')
V14 = os.path.join(QUAL, 'downloads', 'summary_table_v1.4.csv')
MAPPING = os.path.join(PA, 'mapping_table.csv')
PROTOCOL = os.path.join(BASE, 'PROTOCOL_PB2.md')
SCRIPT = os.path.abspath(__file__)
OUT_JSON = os.path.join(BASE, 'pb2.json')
PB_ARTIFACTS = ['PROTOCOL_PB.md', 'pb.py', 'pb.json', 'endpoint_audit.csv',
                'report.md', 'record.md', 'usage.json']

SEED2 = 20261028
Z_MDE80 = 2.801585218112968
ALPHA_Z = 1.959963984540054
B_MDE = 2000
N_POWER = 1000
TARGET_RHOS = (0.1183, 0.10, 0.05)
DELTA_MIN_TIER_B = 0.1183     # frozen headline point estimate
DELTA_MIN_TIER_A = 0.0947     # frozen effect 95% CI lower bound
TRAINING_MIN_UNITS = 5000     # P-A G4 threshold reused as design constraint
SUPPLEMENTARY_R = (0.45, 0.50, 0.55)   # post-freeze exploration of the extrapolated requirement
PRIMARY = 'synergy_bliss'
NULLISH = {'', 'NA', 'NULL', '\\N'}

EXPECTED = {
    'n_combo_blocks': 466033,
    'n_cell_x_pair_units': 380418,
    'n_drugs_normalized': 4088,
    'n_mapped_drugs_S1': 1418,
    'n_annotated_units': 88118,
    'pa_both_unseen_r020': 2682,
    'e1_both_unseen_r020': 3739,
    'frozen_effect': 0.1183,
    'frozen_ci': [0.0947, 0.1409],
}


# ------------------------------------------------------------------ helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest().upper()


def norm(s):
    s = unicodedata.normalize('NFKC', str(s)).casefold()
    return ''.join(ch for ch in s if ch.isalnum())


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


def spearman_fast(x, y):
    from scipy.stats import rankdata
    if len(x) < 3:
        return float('nan')
    rx = rankdata(x, method='average')
    ry = rankdata(y, method='average')
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    den = math.sqrt(float(np.dot(rx, rx)) * float(np.dot(ry, ry)))
    return float('nan') if den == 0 else float(np.dot(rx, ry) / den)


def mde80(se):
    return Z_MDE80 * se if (se is not None and math.isfinite(se)) else None


# ------------------------------------------------------------------ inputs
def hash_inputs():
    files = {
        'mapping_table': MAPPING,
        'v14_summary': V14,
        'protocol_pb2': PROTOCOL,
        'pa_json': os.path.join(PA, 'pa.json'),
        'pa_report': os.path.join(PA, 'report.md'),
        'pa_protocol': os.path.join(PA, 'PROTOCOL_PA.md'),
    }
    out = {}
    for k, p in files.items():
        if not os.path.exists(p):
            out[k] = {'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'), 'status': 'missing'}
            continue
        out[k] = {'path_rel': os.path.relpath(p, ROOT).replace('\\', '/'),
                  'bytes': os.path.getsize(p), 'sha256': sha256_file(p), 'status': 'ok'}
    out['script_pb2'] = {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                         'bytes': os.path.getsize(SCRIPT), 'sha256': sha256_file(SCRIPT)}
    return out


def hash_pb_artifacts():
    out = {}
    for f in PB_ARTIFACTS:
        p = os.path.join(BASE, f)
        out[f] = {'bytes': os.path.getsize(p), 'sha256': sha256_file(p)} if os.path.exists(p) else {'status': 'missing'}
    return out


# ------------------------------------------------------------ v1.4 read (minimal)
def read_v14():
    """Stream v1.4 once: identity + the frozen primary endpoint (synergy_bliss)."""
    cap = 600_000
    n = 0
    rows_total = 0
    mono = 0
    blk = np.empty(cap, dtype=np.int64)
    unit_code = np.empty(cap, dtype=np.int32)
    pair_code = np.empty(cap, dtype=np.int32)
    cell_code = np.empty(cap, dtype=np.int32)
    drug_code = np.empty(cap, dtype=np.int32)
    vals = np.empty(cap, dtype=float)
    unit_map, pair_map, cell_map, drug_map = {}, {}, {}, {}
    unit_keys, pair_keys, cell_names, drug_names = [], [], [], []

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
        if PRIMARY not in col:
            raise SystemExit('primary endpoint column missing from v1.4 summary')
        i_b, i_dr, i_dc, i_cl, i_y = (col['block_id'], col['drug_row'], col['drug_col'],
                                      col['cell_line_name'], col[PRIMARY])
        for row in rdr:
            rows_total += 1
            dr, dc, cl = row[i_dr].strip(), row[i_dc].strip(), row[i_cl].strip()
            if dr.upper() in NULLISH or dc.upper() in NULLISH:
                mono += 1
                continue
            ndr, ndc, ncl = norm(dr), norm(dc), norm(cl)
            a, b = (ndr, ndc) if ndr <= ndc else (ndc, ndr)
            pk = enc(a + '\x1f' + b, pair_map, pair_keys)
            uk = enc(ncl + '\x1f' + a + '\x1f' + b, unit_map, unit_keys)
            ck = enc(ncl, cell_map, cell_names)
            dk = enc(a, drug_map, drug_names)
            enc(b, drug_map, drug_names)
            if n >= cap:
                newcap = int(cap * 1.5)
                new_blk = np.empty(newcap, dtype=np.int64); new_blk[:n] = blk[:n]; blk = new_blk
                new_u = np.empty(newcap, dtype=np.int32); new_u[:n] = unit_code[:n]; unit_code = new_u
                new_p = np.empty(newcap, dtype=np.int32); new_p[:n] = pair_code[:n]; pair_code = new_p
                new_c = np.empty(newcap, dtype=np.int32); new_c[:n] = cell_code[:n]; cell_code = new_c
                new_d = np.empty(newcap, dtype=np.int32); new_d[:n] = drug_code[:n]; drug_code = new_d
                new_v = np.empty(newcap, dtype=float); new_v[:n] = vals[:n]; vals = new_v
                cap = newcap
            try:
                blk[n] = int(row[i_b])
            except (TypeError, ValueError):
                blk[n] = -1
            unit_code[n] = uk
            pair_code[n] = pk
            cell_code[n] = ck
            drug_code[n] = dk
            vals[n] = parse_float(row[i_y])
            n += 1
    n_units = len(unit_keys)
    n_blocks = n
    unit_pair = np.zeros(n_units, dtype=np.int64)
    unit_cell = np.zeros(n_units, dtype=np.int64)
    unit_pair[unit_code] = pair_code
    unit_cell[unit_code] = cell_code
    ok = np.isfinite(vals)
    cnt = np.bincount(unit_code[ok], minlength=n_units).astype(np.int64)
    sums = np.bincount(unit_code[ok], weights=vals[ok], minlength=n_units)
    y = np.full(n_units, np.nan)
    have = cnt > 0
    y[have] = sums[have] / cnt[have]
    pair_a = np.empty(len(pair_keys), dtype=np.int32)
    pair_b = np.empty(len(pair_keys), dtype=np.int32)
    for i, k in enumerate(pair_keys):
        a, b = k.split('\x1f')
        pair_a[i] = drug_map[a]
        pair_b[i] = drug_map[b]
    return {
        'header': header, 'rows_total': rows_total, 'rows_monotherapy_like': mono,
        'n_blocks_combo': n_blocks, 'n_units': n_units,
        'drug_names': drug_names, 'cell_names': cell_names,
        'n_pairs': len(pair_keys),
        'unit_pair': unit_pair, 'unit_cell': unit_cell, 'y': y,
        'unit_size': cnt,
        'pair_drug': (pair_a, pair_b),
    }


def read_mapped_drugs():
    mapped = set()
    n_rows = 0
    with open(MAPPING, newline='', encoding='utf-8') as fh:
        rdr = csv.DictReader(fh)
        for row in rdr:
            n_rows += 1
            if row['source_library'] != 'S1':
                continue
            if row['pathway'].strip().lower() == 'unmapped':
                continue
            mapped.add(row['drug_normalized_name'].strip())
    return mapped, n_rows


# ------------------------------------------------------------ MDE + power
def bootstrap_mde(y, pair_idx, cell_idx, npairs, ncells, B, seed):
    rng = np.random.default_rng(seed)
    nunits = y.size
    ro = np.arange(nunits)
    ra = np.empty(B)
    rb = np.empty(B)
    for b in range(B):
        cp = np.bincount(rng.integers(0, npairs, npairs), minlength=npairs)
        idx = np.repeat(ro, cp[pair_idx])
        z = rng.normal(size=npairs)
        ra[b] = spearman_fast(z[pair_idx][idx], y[idx])
        cp2 = np.bincount(rng.integers(0, npairs, npairs), minlength=npairs)
        cc = np.bincount(rng.integers(0, ncells, ncells), minlength=ncells)
        idx2 = np.repeat(ro, cp2[pair_idx] * cc[cell_idx])
        z2 = rng.normal(size=npairs)
        rb[b] = spearman_fast(z2[pair_idx][idx2], y[idx2])
    out = {'B': B, 'seed': seed}
    for tag, arr in (('A_pair_clustered', ra), ('B_two_way_clustered', rb)):
        sd = float(arr.std(ddof=1))
        out[tag] = {'se': sd, 'mde80': mde80(sd), 'mean_null_rho': float(arr.mean())}
    n = nunits
    out['iid_analytic_reference'] = {'se': 1.0 / math.sqrt(n - 1) if n > 2 else None,
                                     'mde80': mde80(1.0 / math.sqrt(n - 1)) if n > 2 else None}
    return out


def power_check(y, pair_idx, npairs, se_ref, targets, reps, seed):
    cntp = np.bincount(pair_idx, minlength=npairs).astype(float)
    sums = np.bincount(pair_idx, weights=y, minlength=npairs)
    pair_mean = sums / np.maximum(cntp, 1)
    pm_unit = pair_mean[pair_idx]
    rho_pm = spearman_fast(pm_unit, y)
    sd = float(pm_unit.std())
    base = (pair_mean - pair_mean.mean()) / sd if sd > 0 else np.zeros(npairs)
    vals = {}
    for delta in targets:
        c = min(1.0, float(delta) / rho_pm) if (rho_pm and rho_pm > 0) else 0.0
        resid = math.sqrt(max(0.0, 1.0 - c * c))
        rng = np.random.default_rng((seed + int(round(float(delta) * 1000003))) & 0x7FFFFFFF)
        rej = 0
        for _ in range(reps):
            z = c * base + resid * rng.normal(size=npairs)
            rho = spearman_fast(z[pair_idx], y)
            if rho > ALPHA_Z * se_ref:
                rej += 1
        vals['%.6f' % delta] = {'realized_pair_weight': c, 'reject_rate': rej / reps}
    return {'rho_pair_mean_replication': rho_pm, 'reps': reps,
            'threshold': ALPHA_Z * se_ref, 'targets': vals}


# ------------------------------------------------------------ design selection
def holdout(names_sorted, r):
    n = len(names_sorted)
    k = max(1, round(r * n))
    step = max(1, n // k)
    return set(names_sorted[0::step][:k]), k, step


def design_mask(unit_pair, pair_drug, mem_hold, mem_mapped, annotated_only=True):
    pa, pb_ = pair_drug
    a = pa[unit_pair]
    b = pb_[unit_pair]
    hold = (mem_hold[a] == 1) & (mem_hold[b] == 1)
    if annotated_only:
        mapped = (mem_mapped[a] == 1) & (mem_mapped[b] == 1)
        return hold & mapped, mapped
    return hold, None


def main():
    t0 = time.time()
    print('[1/7] hash inputs + P-B artifacts (before) ...', flush=True)
    inputs = hash_inputs()
    pb_before = hash_pb_artifacts()
    assert inputs['mapping_table']['status'] == 'ok'
    assert inputs['mapping_table']['sha256'] == \
        '45EDE63521DC44FEFEC52D717765B4D2BA7D08EC3FDE4372811C4D516DE038D4', 'mapping table hash mismatch'
    assert inputs['v14_summary']['sha256'] == \
        'E08E3D35BFA4BEA011AFE1B05B7025ACDE5C669C5E8D265866B5E12B08037A2F', 'v1.4 hash mismatch'
    protocol_sha = sha256_file(PROTOCOL)

    print('[2/7] read v1.4 (identity + frozen primary endpoint) ...', flush=True)
    v14 = read_v14()
    print('    blocks %d / units %d / pairs %d / drugs %d / cells %d (%.1fs)'
          % (v14['n_blocks_combo'], v14['n_units'], v14['n_pairs'],
             len(v14['drug_names']), len(v14['cell_names']), time.time() - t0), flush=True)

    print('[3/7] read P-A frozen mapping table (S1-A main strategy) ...', flush=True)
    mapped, mapping_rows = read_mapped_drugs()
    drug_names = v14['drug_names']
    drug_index = {n: i for i, n in enumerate(drug_names)}
    mapped_in_v14 = {n for n in mapped if n in drug_index}
    unmapped_in_mapping = {n for n in drug_names if n not in mapped}
    mem_mapped = np.zeros(len(drug_names), dtype=np.int8)
    for n in mapped_in_v14:
        mem_mapped[drug_index[n]] = 1

    # annotated universe
    pair_a, pair_b = v14['pair_drug']
    unit_pair = v14['unit_pair']
    unit_cell = v14['unit_cell']
    y_all = v14['y']
    a_all = pair_a[unit_pair]
    b_all = pair_b[unit_pair]
    annotated = (mem_mapped[a_all] == 1) & (mem_mapped[b_all] == 1)
    n_units_total = v14['n_units']
    universe = {
        'n_combo_blocks': int(v14['n_blocks_combo']),
        'n_cell_x_pair_units_total': int(n_units_total),
        'n_drugs_normalized_total': int(len(drug_names)),
        'mapping_table_S1_rows': int(mapping_rows),
        'n_mapped_drugs': int(len(mapped_in_v14)),
        'mapped_drugs_frac_of_total': len(mapped_in_v14) / len(drug_names),
        'n_annotated_units': int(annotated.sum()),
        'annotated_units_frac_of_total': float(annotated.sum()) / n_units_total,
        'n_annotated_pairs': int(np.unique(unit_pair[annotated]).size),
        'n_annotated_cells': int(np.unique(unit_cell[annotated]).size),
        'annotated_units_endpoint_missing': int((~np.isfinite(y_all[annotated])).sum()),
    }

    print('[4/7] construct PA / E1 splits x r designs ...', flush=True)
    ordered_total = sorted(drug_names)
    ordered_mapped = sorted(mapped_in_v14)
    r_values = (0.20, 0.30, 0.40)
    designs = {}
    design_order = []
    for split in ('PA', 'E1'):
        names = ordered_mapped if split == 'PA' else ordered_total
        for r in r_values:
            hold, k, step = holdout(names, r)
            mem_hold = np.zeros(len(drug_names), dtype=np.int8)
            for n in hold:
                if n in drug_index:
                    mem_hold[drug_index[n]] = 1
            mask, _ = design_mask(unit_pair, v14['pair_drug'], mem_hold, mem_mapped,
                                  annotated_only=True)
            train_mask = (mem_mapped[a_all] == 1) & (mem_mapped[b_all] == 1) & \
                         (mem_hold[a_all] == 0) & (mem_hold[b_all] == 0)
            did = '%s_r%02d' % (split, int(round(r * 100)))
            design_order.append(did)
            designs[did] = {
                'id': did, 'split': split, 'r': r, 'n_names_in_split_universe': len(names),
                'k_holdout': k, 'step': step,
                'n_units': int(mask.sum()),
                'n_pairs': int(np.unique(unit_pair[mask]).size),
                'n_cells': int(np.unique(unit_cell[mask]).size),
                'n_training_annotated_units': int(train_mask.sum()),
                'mask': mask, 'train_mask': train_mask,
                'pair_cluster_ids': None,
            }
            print('    %s: holdout %d, both-unseen units %d, pairs %d, cells %d, training %d'
                  % (did, k, designs[did]['n_units'], designs[did]['n_pairs'],
                     designs[did]['n_cells'], designs[did]['n_training_annotated_units']), flush=True)

    print('[5/7] MDE80 (two-way + pair-clustered) and power per design ...', flush=True)
    results = {}

    def run_design(did, split, r):
        names = ordered_mapped if split == 'PA' else ordered_total
        hold, k, step = holdout(names, r)
        mem_hold = np.zeros(len(drug_names), dtype=np.int8)
        for n in hold:
            if n in drug_index:
                mem_hold[drug_index[n]] = 1
        mask, _ = design_mask(unit_pair, v14['pair_drug'], mem_hold, mem_mapped,
                              annotated_only=True)
        train_mask = (mem_mapped[a_all] == 1) & (mem_mapped[b_all] == 1) & \
                     (mem_hold[a_all] == 0) & (mem_hold[b_all] == 0)
        mask = mask & np.isfinite(y_all)
        y = y_all[mask]
        pr = unit_pair[mask]
        ce = unit_cell[mask]
        upairs, pr2 = np.unique(pr, return_inverse=True)
        ucells, ce2 = np.unique(ce, return_inverse=True)
        npairs = int(upairs.size)
        ncells = int(ucells.size)
        seed = SEED2 + 1000 + 100 * int(round(r * 100)) + (0 if split == 'PA' else 1)
        mde = bootstrap_mde(y, pr2.astype(np.int64), ce2.astype(np.int64),
                            npairs, ncells, B_MDE, seed)
        se_b = mde['B_two_way_clustered']['se']
        pw = power_check(y, pr2.astype(np.int64), npairs, se_b, TARGET_RHOS, N_POWER, seed + 7)
        rec = {
            'id': did, 'split': split, 'r': r, 'k_holdout': k, 'step': step,
            'n_units': int(y.size), 'n_pairs': npairs, 'n_cells': ncells,
            'n_training_annotated_units': int(train_mask.sum()),
            'mean_units_per_pair': float(y.size / npairs) if npairs else None,
            'mde': mde, 'power': pw,
        }
        results[did] = rec
        print('    %s: MDE80 two-way %.4f / pair %.4f ; power@0.1183 %.3f'
              % (did, mde['B_two_way_clustered']['mde80'], mde['A_pair_clustered']['mde80'],
                 pw['targets']['0.118300']['reject_rate']), flush=True)
        return rec

    for di, did in enumerate(design_order):
        d = designs[did]
        run_design(did, d['split'], d['r'])

    # supplementary (post-freeze exploration of the extrapolated requirement; the
    # pre-registered decision above is unaffected and reported separately)
    print('    supplementary design exploration (post-freeze extension, disclosed):', flush=True)
    supp_order = []
    for split in ('PA', 'E1'):
        for r in SUPPLEMENTARY_R:
            did = '%s_r%02d' % (split, int(round(r * 100)))
            supp_order.append(did)
            run_design(did, split, r)

    # ---------------------------------------------------------------- decision
    print('[6/7] decision rule (PROTOCOL_PB2 section 7) ...', flush=True)

    def evaluate(tier_name, delta_min):
        passing = []
        for did in design_order:
            rec = results[did]
            mde_b = rec['mde']['B_two_way_clustered']['mde80']
            pw = rec['power']['targets']['0.118300']['reject_rate']
            ok_mde = bool(mde_b is not None and mde_b <= delta_min)
            ok_pw = bool(pw >= 0.80)
            ok_train = bool(rec['n_training_annotated_units'] >= TRAINING_MIN_UNITS)
            ok = bool(ok_mde and ok_pw and ok_train)
            rec.setdefault('gates', {})[tier_name] = {
                'delta_min': delta_min,
                'mde80_two_way': mde_b,
                'mde_ok': ok_mde,
                'power_at_0.1183': pw,
                'power_ok': ok_pw,
                'training_units': rec['n_training_annotated_units'],
                'training_ok': ok_train,
                'design_pass': ok,
            }
            if ok:
                passing.append(did)
        if passing:
            best = min(passing, key=lambda x: results[x]['mde']['B_two_way_clustered']['mde80'])
            return {'tier': tier_name, 'delta_min': delta_min,
                    'passing_designs': passing,
                    'recommended_design': best,
                    'recommended_design_mde80_two_way': results[best]['mde']['B_two_way_clustered']['mde80'],
                    'recommended_design_power_at_0.1183': results[best]['power']['targets']['0.118300']['reject_rate'],
                    'reopenable': True}
        return {'tier': tier_name, 'delta_min': delta_min, 'passing_designs': [],
                'recommended_design': None, 'reopenable': False}

    tier_b = evaluate('B_frozen_headline', DELTA_MIN_TIER_B)
    tier_a = evaluate('A_frozen_CI_lower', DELTA_MIN_TIER_A)

    # supplementary gate evaluation (post-freeze; disclosed, not part of the pre-registered decision)
    supp_eval = {}
    for did in supp_order:
        rec = results[did]
        mde_b = rec['mde']['B_two_way_clustered']['mde80']
        pw = rec['power']['targets']['0.118300']['reject_rate']
        supp_eval[did] = {
            'r': rec['r'], 'split': rec['split'],
            'n_units': rec['n_units'], 'n_pairs': rec['n_pairs'],
            'n_training_annotated_units': rec['n_training_annotated_units'],
            'mde80_two_way': mde_b,
            'power_at_0.1183': pw,
            'tier_B_ok': bool(mde_b is not None and mde_b <= DELTA_MIN_TIER_B
                              and pw >= 0.80 and rec['n_training_annotated_units'] >= TRAINING_MIN_UNITS),
            'tier_A_ok': bool(mde_b is not None and mde_b <= DELTA_MIN_TIER_A
                              and pw >= 0.80 and rec['n_training_annotated_units'] >= TRAINING_MIN_UNITS),
        }
    supp_pass_b = [d for d in supp_order if supp_eval[d]['tier_B_ok']]
    supp_pass_a = [d for d in supp_order if supp_eval[d]['tier_A_ok']]

    # ---------------------------------------------------------- extrapolation
    print('[7/7] extrapolation of the minimum required annotated universe ...', flush=True)
    n_u = np.array([results[d]['n_units'] for d in design_order], dtype=float)
    n_p = np.array([results[d]['n_pairs'] for d in design_order], dtype=float)
    se = np.array([results[d]['mde']['B_two_way_clustered']['se'] for d in design_order], dtype=float)
    rho = n_u / n_p

    def ols_alpha(x, yv):
        lx = np.log(x)
        ly = np.log(yv)
        A = np.column_stack([np.ones_like(lx), lx])
        coef, *_ = np.linalg.lstsq(A, ly, rcond=None)
        return float(coef[1]), float(coef[0])

    alpha_units, _ = ols_alpha(n_u, se)
    alpha_pairs, _ = ols_alpha(n_p, se)
    c_units = float(np.median(se * np.sqrt(n_u)))
    c_pairs = float(np.median(se * np.sqrt(n_p)))
    ratio_med = float(np.median(rho))
    extrap = {
        'fit_relation': 'SE ~ c * n^(-1/2) (exponent fixed by pre-registration section 8)',
        'loglog_exponent_units': alpha_units,
        'loglog_exponent_pairs': alpha_pairs,
        'c_units_median_SE_times_sqrt_n_units': c_units,
        'c_pairs_median_SE_times_sqrt_n_pairs': c_pairs,
        'median_units_per_pair': ratio_med,
        'design_points': {d: {'n_units': int(results[d]['n_units']),
                              'n_pairs': int(results[d]['n_pairs']),
                              'se_two_way': results[d]['mde']['B_two_way_clustered']['se']}
                          for d in design_order},
        'caveats': [
            'only 6 design points; the n^(-1/2) exponent is fixed by pre-registration, log-log fits are reported as diagnostics',
            'the cell count is roughly fixed (about 100-110) and the pair-size distribution does not scale with n',
            'if the required unit count exceeds the annotated universe, the correct remedy is a larger annotation coverage (P-A extension), not a larger r',
        ],
    }
    for tag, delta in (('tier_B_frozen_headline', DELTA_MIN_TIER_B),
                       ('tier_A_frozen_CI_lower', DELTA_MIN_TIER_A)):
        se_target = delta / Z_MDE80
        need_u_from_units = (c_units / se_target) ** 2
        need_p_from_pairs = (c_pairs / se_target) ** 2
        need_u_from_pairs = need_p_from_pairs * ratio_med
        need_u = max(need_u_from_units, need_u_from_pairs)
        extrap[tag] = {
            'delta_min': delta,
            'se_target': se_target,
            'required_pairs': need_p_from_pairs,
            'required_units_from_units_fit': need_u_from_units,
            'required_units_from_pairs_fit': need_u_from_pairs,
            'required_annotated_both_unseen_units': need_u,
            'factor_vs_largest_design': need_u / n_u.max(),
            'factor_vs_annotated_universe_units': need_u / max(1.0, float(annotated.sum())),
            'exceeds_annotated_universe': bool(need_u > float(annotated.sum())),
        }

    # verify the pre-registered extrapolation against the post-freeze supplementary designs
    supp_verification = {}
    for did in supp_order:
        rec = results[did]
        pred_u = c_units / math.sqrt(rec['n_units']) if rec['n_units'] else None
        pred_p = c_pairs / math.sqrt(rec['n_pairs']) if rec['n_pairs'] else None
        supp_verification[did] = {
            'n_units': rec['n_units'], 'n_pairs': rec['n_pairs'],
            'predicted_se_from_units_fit': pred_u,
            'predicted_mde80_from_units_fit': mde80(pred_u),
            'predicted_mde80_from_pairs_fit': mde80(pred_p),
            'observed_se_two_way': rec['mde']['B_two_way_clustered']['se'],
            'observed_mde80_two_way': rec['mde']['B_two_way_clustered']['mde80'],
            'observed_power_at_0.1183': rec['power']['targets']['0.118300']['reject_rate'],
            'observed_training_annotated_units': rec['n_training_annotated_units'],
        }
    extrap['supplementary_verification_post_freeze'] = supp_verification

    # ------------------------------------------------------------- judgment
    if tier_b['reopenable']:
        status = 'reopenable'
        recommendation = {
            'status': status,
            'justification_target': 'Tier B: delta_min = frozen headline 0.1183',
            'design': tier_b['recommended_design'],
            'delta_min': DELTA_MIN_TIER_B,
            'tier_A_also_reopenable': tier_a['reopenable'],
            'note': ('stage 2 may be reopened only with the pre-registered design/delta_min above; '
                     'this is a power/design decision and does not assert any effect'),
        }
    elif tier_a['reopenable']:
        status = 'reopenable_tier_A_only'
        recommendation = {
            'status': status,
            'justification_target': 'none at Tier B; Tier A (delta_min = 0.0947) is met',
            'design': tier_a['recommended_design'],
            'delta_min': DELTA_MIN_TIER_A,
            'note': 'lenient-only reopening; requires explicit Lead acceptance of the smaller target effect',
        }
    elif supp_pass_b:
        # smallest-r passing supplementary design (least deviation from the R191 grid); prefer PA split
        best = min(supp_pass_b, key=lambda x: (results[x]['r'],
                                               0 if results[x]['split'] == 'PA' else 1))
        status = 'not_reopenable_on_preregistered_grid_but_reopenable_with_new_design'
        recommendation = {
            'status': status,
            'conclusion': ('no pre-registered design (r in {0.20,0.30,0.40}, PA/E1) reaches MDE80 <= '
                           'the frozen target effect with power >= 0.80 at 0.1183; the annotated universe '
                           'CAN support a defensible design only at a larger holdout fraction OUTSIDE the '
                           'R191 grid, which requires a NEW frozen stage-2 design'),
            'pre_registered_grid_best': {
                'max_power_at_0.1183': max(results[d]['power']['targets']['0.118300']['reject_rate']
                                           for d in design_order),
                'min_mde80_two_way': min(results[d]['mde']['B_two_way_clustered']['mde80']
                                         for d in design_order),
                'passing_designs_tier_B': tier_b['passing_designs'],
            },
            'recommended_new_design': {
                'design': best,
                'split': results[best]['split'],
                'r': results[best]['r'],
                'k_holdout': results[best]['k_holdout'],
                'n_both_unseen_annotated_units': results[best]['n_units'],
                'n_pairs': results[best]['n_pairs'],
                'n_cells': results[best]['n_cells'],
                'n_training_annotated_units': results[best]['n_training_annotated_units'],
                'delta_min': DELTA_MIN_TIER_B,
                'mde80_two_way': results[best]['mde']['B_two_way_clustered']['mde80'],
                'mde80_pair_clustered': results[best]['mde']['A_pair_clustered']['mde80'],
                'power_at_0.1183': results[best]['power']['targets']['0.118300']['reject_rate'],
                'power_at_0.10': results[best]['power']['targets']['0.100000']['reject_rate'],
                'power_at_0.05': results[best]['power']['targets']['0.050000']['reject_rate'],
                'training_units_ok': bool(results[best]['n_training_annotated_units'] >= TRAINING_MIN_UNITS),
            },
            'supplementary_designs_passing_tier_B': supp_pass_b,
            'supplementary_designs_passing_tier_A': supp_pass_a,
            'supplementary_table': supp_eval,
            'minimum_required_annotated_both_unseen_units': {
                'tier_B_frozen_headline_0.1183': extrap['tier_B_frozen_headline']['required_annotated_both_unseen_units'],
                'tier_A_frozen_CI_lower_0.0947': extrap['tier_A_frozen_CI_lower']['required_annotated_both_unseen_units'],
            },
            'unfreeze_conditions': [
                'the Lead freezes a NEW stage-2 design at the recommended r/split (outside the R191 '
                'r in {0.20,0.30,0.40} grid) with delta_min = 0.1183 explicitly justified as the '
                'replication target effect; this audit computes power but does not choose the design',
                'the stage-2 protocol must disclose that a larger holdout fraction changes the training '
                'set size and may change the expected annotation gain (the frozen effect was measured at '
                'r=0.20; equality of effect size across holdout fractions is NOT assumed)',
                'if the Lead requires Tier A (delta_min = 0.0947), a still larger design is needed '
                '(see supplementary_designs_passing_tier_A)',
            ],
        }
    else:
        status = 'not_reopenable'
        recommendation = {
            'status': status,
            'conclusion': ('the annotated universe is too small: no design reaches MDE80 <= frozen '
                           'target effect with power >= 0.80 at 0.1183, even at the largest explored '
                           'holdout fraction; stage 2 cannot be legitimately reopened on this resource '
                           'with the frozen endpoint'),
            'minimum_required_annotated_both_unseen_units': {
                'tier_B_frozen_headline_0.1183': extrap['tier_B_frozen_headline']['required_annotated_both_unseen_units'],
                'tier_A_frozen_CI_lower_0.0947': extrap['tier_A_frozen_CI_lower']['required_annotated_both_unseen_units'],
            },
            'unfreeze_conditions': [
                'a larger ANNOTATION coverage (P-A extension) that increases the annotated both-unseen '
                'unit count to the extrapolated minimum, or',
                'a defensible protocol amendment lowering the replication target effect below the frozen '
                'headline (must be explicitly justified by the Lead and is NOT recommended by this audit), or',
                'a different resource / design with more independent drug pairs',
            ],
        }

    pb_after = hash_pb_artifacts()
    unchanged = (pb_before == pb_after)
    out = {
        'protocol': {'path_rel': os.path.relpath(PROTOCOL, ROOT).replace('\\', '/'),
                     'bytes': os.path.getsize(PROTOCOL), 'sha256': protocol_sha},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'bytes': os.path.getsize(SCRIPT), 'sha256': sha256_file(SCRIPT)},
        'environment': {'python': sys.version.split()[0], 'numpy': np.__version__,
                        'platform': platform.platform()},
        'inputs': inputs,
        'rules_reference': {
            'z_mde80': Z_MDE80, 'alpha_z': ALPHA_Z, 'B_bootstrap': B_MDE,
            'power_reps': N_POWER, 'target_rhos': list(TARGET_RHOS),
            'delta_min_tier_B_frozen_headline': DELTA_MIN_TIER_B,
            'delta_min_tier_A_frozen_CI_lower': DELTA_MIN_TIER_A,
            'training_min_units': TRAINING_MIN_UNITS,
            'primary_endpoint': PRIMARY,
            'aggregation': 'arithmetic mean of block-level synergy_bliss within cell x unordered pair (P-B frozen)',
            'seeds': {'master': SEED2, 'design_seed_rule': 'SEED2+1000+100*round(r*100)+(0 PA,1 E1)'},
        },
        'cross_checks': {
            'expected': EXPECTED,
            'measured': {
                'n_combo_blocks': int(v14['n_blocks_combo']),
                'n_cell_x_pair_units': int(n_units_total),
                'n_drugs_normalized': int(len(drug_names)),
                'n_mapped_drugs_S1': int(len(mapped_in_v14)),
                'n_annotated_units': int(annotated.sum()),
                'pa_both_unseen_r020': int(designs['PA_r20']['n_units']),
                'e1_both_unseen_r020': int(designs['E1_r20']['n_units']),
            },
        },
        'universe': universe,
        'design_table': {did: {k: v for k, v in results[did].items() if k != 'mask'}
                         for did in design_order},
        'design_order': design_order,
        'supplementary_design_exploration_post_freeze': {
            'status': 'post-freeze extension (disclosed in record_pb2.md); the pre-registered decision above is unchanged',
            'purpose': ('check whether the extrapolated required annotated both-unseen unit count is reachable '
                        'on the existing annotated universe at larger holdout fractions'),
            'r_values': list(SUPPLEMENTARY_R),
            'designs_order': supp_order,
            'designs': supp_eval,
            'passing_tier_B': supp_pass_b,
            'passing_tier_A': supp_pass_a,
        },
        'decision': {
            'tier_B_frozen_headline': tier_b,
            'tier_A_frozen_CI_lower': tier_a,
            'design_recommendation': recommendation,
        },
        'extrapolation': extrap,
        'pb_artifacts_unchanged': {'unchanged': bool(unchanged),
                                   'before': pb_before, 'after': pb_after},
        'response_use_attestation': {
            'identity_or_annotation_model_fitted': False,
            'effect_estimated': False,
            'training_or_feature_selection_on_responses': False,
            'response_columns_used': [PRIMARY],
            'response_used_only_for': ['frozen endpoint aggregation (P-B rule)',
                                       'MDE variance estimation', 'power simulation'],
        },
        'boundaries': {
            'endpoint_switch': 'not performed; primary endpoint fixed to synergy_bliss by P-B',
            'effect_claims': 'none: no arm contrast, no pathway-minus-identity gain, no mechanism/clinical claim',
            'frozen_claim_status': 'unchanged (not unfrozen) by this audit',
        },
    }
    out = qd(out)
    write_json(out, OUT_JSON)
    print('    STATUS: %s' % status, flush=True)
    if 'recommended_new_design' in recommendation:
        nd = recommendation['recommended_new_design']
        print('    recommended NEW design: %s (r=%.2f, delta_min %.4f, MDE80 %.4f, power@0.1183 %.3f, '
              'training units %d)'
              % (nd['design'], nd['r'], nd['delta_min'], nd['mde80_two_way'],
                 nd['power_at_0.1183'], nd['n_training_annotated_units']), flush=True)
        print('    minimum required annotated both-unseen units: tierB %.0f / tierA %.0f'
              % (extrap['tier_B_frozen_headline']['required_annotated_both_unseen_units'],
                 extrap['tier_A_frozen_CI_lower']['required_annotated_both_unseen_units']), flush=True)
    elif recommendation.get('design'):
        print('    recommended design: %s (delta_min %.4f)'
              % (recommendation['design'], recommendation['delta_min']), flush=True)
    else:
        print('    required annotated both-unseen units: tierB %.0f / tierA %.0f (available %d)'
              % (extrap['tier_B_frozen_headline']['required_annotated_both_unseen_units'],
                 extrap['tier_A_frozen_CI_lower']['required_annotated_both_unseen_units'],
                 int(annotated.sum())), flush=True)
    print('    done in %.1fs' % (time.time() - t0), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
