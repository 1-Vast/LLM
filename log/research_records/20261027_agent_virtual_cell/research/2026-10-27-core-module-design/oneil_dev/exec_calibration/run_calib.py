#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
R199-ON2-EX: execution-time qualification calibration under PROTOCOL_ON2 v2.2.

This script performs ONLY the qualification execution allowed by the frozen
protocol (NOT an effect analysis):
  1) sigma_e calibration with fixed replicate-index split-half (no value sorting);
  2) MDE80 certification (MDE80 > delta_min=0.10 -> design_invalid: precision_insufficient);
  3) deterministic row-mean SINGLE-IMPUTATION sensitivity (NOT multiple imputation).

It does not fit models, compare updaters, estimate treatment effects, or run any
training.  It only computes well-level noise calibration and imputation sensitivity
statistics as frozen in PROTOCOL_ON2.md v2.2 section 3.2(b) / 3.3(2).

Determinism: calib.json is sorted-keys, no timestamps, allow_nan=False, fixed decimal
rounding; input and script SHA256 are recorded.  wall/CPU are recorded separately in
usage_calib.json (not in calib.json) so calib.json is reproducible.
"""
import hashlib
import json
import math
import os
import platform
import sys
import time

import numpy as np
import pandas as pd

ROOT = r'D:\MAESTRO'
OUTDIR = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev')
EXECDIR = os.path.join(OUTDIR, 'exec_calibration')
COMP = os.path.join(ROOT, 'data', 'raw', 'oneil2026_qualification',
                    '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls')
PROTOCOL = os.path.join(OUTDIR, 'PROTOCOL_ON2.md')
ERRATA = os.path.join(OUTDIR, 'ERRATA_ON2_1.md')
REPORT = os.path.join(OUTDIR, 'report_on2_1.md')
RECORD = os.path.join(OUTDIR, 'record_on2_1.md')
ON2JSON = os.path.join(OUTDIR, 'on2.json')
SCRIPT = os.path.join(EXECDIR, 'run_calib.py')
OUTJSON = os.path.join(EXECDIR, 'calib.json')
OUTUSAGE = os.path.join(EXECDIR, 'usage_calib.json')

REPS = ['viability1', 'viability2', 'viability3', 'viability4']
MDE_FACTOR = 2.801585218112968
DELTA_MIN = 0.10
N_EFF = 6
K1_EXPECTED = 78
ROUND_DIGITS = 10


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def norm(s):
    import unicodedata
    return ''.join(ch for ch in unicodedata.normalize('NFKC', str(s)).casefold()
                   if ch.isalnum())


def rq(x, nd=ROUND_DIGITS):
    if x is None:
        return None
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    v = float(x)
    if not math.isfinite(v):
        return None
    return float(round(v, nd))


def sanitize(obj):
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in sorted(obj.items())}
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
        json.dump(sanitize(obj), fh, indent=1, sort_keys=True,
                  ensure_ascii=False, allow_nan=False)
        fh.write('\n')


def build_records(sel, batch, cell, da, db, a, b, h1v, h2v, rowmean, k):
    """Build the two role-orientations of each selected row (A/B roles)."""
    n = len(sel)
    common = dict(row=sel, batch=batch[sel], cell=cell[sel], k=k[sel],
                  mh1=h1v[sel], mh2=h2v[sel], rowmean=rowmean[sel])
    rec_a = pd.DataFrame(dict(common, partner=b[sel], prole=np.full(n, 'B'),
                              member=a[sel]))
    rec_b = pd.DataFrame(dict(common, partner=a[sel], prole=np.full(n, 'A'),
                              member=b[sel]))
    return pd.concat([rec_a, rec_b], ignore_index=True)


def member_curves(recs, denom_mode):
    """Aggregate member contexts; complete = exactly 16 rows.

    denom_mode='cc':      denom_term = (1/h1 + 1/h2) per row (h1=h2=2 -> 1)
    denom_mode='av':      denom_term = (1/h1 + 1/h2) per row (varies by k)
    """
    g = recs.groupby(['batch', 'cell', 'partner', 'prole', 'member'], sort=True)
    cur = g.agg(n_rows=('row', 'size'),
                mean_h1=('mh1', 'mean'),
                mean_h2=('mh2', 'mean')).reset_index()
    if denom_mode == 'cc':
        cur['denom_term'] = 16 * 1.0  # sum over 16 rows of (1/2+1/2)
    elif denom_mode == 'av':
        # sum over rows of (1/h1 + 1/h2); use the row-level h1/h2 stored in recs
        rt = recs.groupby(['batch', 'cell', 'partner', 'prole', 'member'])['hsum'].sum()
        rt = rt.rename('denom_term').reset_index()
        cur = cur.merge(rt, on=['batch', 'cell', 'partner', 'prole', 'member'],
                        how='left')
    cur = cur[cur.n_rows == 16].copy()
    return cur




def count_legal_contexts(cur):
    g = cur.groupby(['batch', 'cell', 'partner', 'prole'], sort=True).size()
    return int((g >= 2).sum())


def pair_stats(cur, denom_per_pair_const=None):
    """For every legal member context (>=2 complete members), count member pairs and
    accumulate (delta_h1 - delta_h2)^2, denom, and delta_full."""
    units = 0
    sumsq = 0.0
    sumden = 0.0
    sumdelta = 0.0
    for key, grp in cur.groupby(['batch', 'cell', 'partner', 'prole'], sort=True):
        grp = grp.sort_values('member')
        m = len(grp)
        if m < 2:
            continue
        h1 = grp.mean_h1.to_numpy(dtype=float)
        h2 = grp.mean_h2.to_numpy(dtype=float)
        d1 = h1[:, None] - h1[None, :]
        d2 = h2[:, None] - h2[None, :]
        diff = d1 - d2
        full = 0.5 * (h1 + h2)
        dfull = full[:, None] - full[None, :]
        iu = np.triu_indices(m, 1)
        vals = diff[iu]
        units += int(vals.size)
        sumsq += float(np.sum(vals * vals))
        sumdelta += float(np.sum(dfull[iu]))
        if denom_per_pair_const is not None:
            sumden += float(vals.size) * denom_per_pair_const
        else:
            term = grp.denom_term.to_numpy(dtype=float)
            pterm = term[:, None] + term[None, :]
            sumden += float(np.sum(pterm[iu]) / 256.0)
    return {'units': int(units), 'sumsq': sumsq, 'sumden': sumden,
            'sumdelta': sumdelta,
            'sigma_e': math.sqrt(sumsq / sumden) if sumden > 0 else None}


def summarize(stat):
    sg = stat['sigma_e']
    se = sg / math.sqrt(32.0) if sg is not None else None
    mde = MDE_FACTOR * se / math.sqrt(N_EFF) if se is not None else None
    return {
        'units': stat['units'],
        'sumsq': stat['sumsq'],
        'sumden': stat['sumden'],
        'sumdelta': stat['sumdelta'],
        'delta_mean': stat['sumdelta'] / stat['units'] if stat['units'] else None,
        'sigma_e': sg,
        'se_unit': se,
        'mde80': mde,
        'mde80_le_delta_min': (mde is not None and mde <= DELTA_MIN),
    }


def main():
    t0 = time.perf_counter()
    c0 = time.process_time()
    print('[ON2-EX] hashing inputs ...', flush=True)
    inputs = {}
    for key, path in (('oneil_combination_workbook', COMP),
                      ('protocol_on2_v22', PROTOCOL),
                      ('report_on2_1', REPORT),
                      ('record_on2_1', RECORD),
                      ('errata_on2_1', ERRATA),
                      ('on2_json', ON2JSON),
                      ('script_run_calib', SCRIPT)):
        inputs[key] = {
            'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
            'bytes': os.path.getsize(path),
            'sha256': sha256_file(path),
        }
    on2 = json.load(open(ON2JSON, encoding='utf-8'))
    target_cells = sorted(on2['scope']['target_cells'])
    target_set = set(target_cells)

    print("[ON2-EX] reading O'Neil combination workbook (responses only for calibration) ...",
          flush=True)
    usecols = ['BatchID', 'cell_line', 'drugA_name', 'drugA Conc (µM)',
               'drugB_name', 'drugB Conc (µM)'] + REPS
    d = pd.read_excel(COMP, sheet_name='combination response', usecols=usecols)
    n_rows = int(len(d))
    for c in ('cell_line', 'drugA_name', 'drugB_name'):
        d[c] = d[c].astype(str).map(norm)
    batch = d.BatchID.to_numpy(dtype=int)
    cell = d.cell_line.to_numpy()
    a = d.drugA_name.to_numpy()
    b = d.drugB_name.to_numpy()
    da = pd.to_numeric(d['drugA Conc (µM)'], errors='coerce').round(9).to_numpy(dtype=float)
    db = pd.to_numeric(d['drugB Conc (µM)'], errors='coerce').round(9).to_numpy(dtype=float)
    vals = d[REPS].to_numpy(dtype=float)
    mask = ~np.isnan(vals)
    k = mask.sum(axis=1).astype(int)
    assert n_rows == 368832, n_rows
    assert int((k == 1).sum()) == K1_EXPECTED, int((k == 1).sum())

    # fixed-column-order split: first h1 non-null replicate columns vs remaining h2
    h1v = np.empty(n_rows, dtype=float)
    h2v = np.empty(n_rows, dtype=float)
    rowmean = np.empty(n_rows, dtype=float)
    hsum = np.empty(n_rows, dtype=float)
    for i in range(n_rows):
        nz = np.flatnonzero(mask[i])  # fixed column order
        kk = nz.size
        hh1 = (kk + 1) // 2
        hh2 = kk - hh1
        v = vals[i, nz]
        h1v[i] = float(np.mean(v[:hh1])) if hh1 else np.nan
        h2v[i] = float(np.mean(v[hh1:])) if hh2 else np.nan
        rowmean[i] = float(np.mean(v))
        hsum[i] = (1.0 / hh1 + 1.0 / hh2) if hh1 and hh2 else np.nan

    cc = np.flatnonzero(k == 4)
    av = np.flatnonzero(k >= 2)
    allrows = np.flatnonzero(k >= 1)
    assert len(cc) == 363090, len(cc)
    assert len(av) == 368832 - K1_EXPECTED, len(av)
    assert len(allrows) == n_rows, len(allrows)

    # ---------- primary calibration: complete-case all batches/all cells ----------
    print('[ON2-EX] complete-case calibration ...', flush=True)
    rec_cc = build_records(cc, batch, cell, da, db, a, b, h1v, h2v, rowmean, k)
    # hsum for complete-case is constant (1/2+1/2)=1 per row; denom_mode cc uses constant
    cur_cc = member_curves(rec_cc, 'cc')
    stat_cc = pair_stats(cur_cc, denom_per_pair_const=1.0 / 8.0)
    prim = summarize(stat_cc)
    prim['cohort'] = 'complete-case rows (viability1-4 all non-null); all batches/all cells'
    prim['rows_used'] = int(len(cc))
    prim['rows_excluded_k1'] = 0
    prim['units_excluded'] = 0
    prim['member_contexts_complete'] = int(len(cur_cc))
    prim['contexts_legal'] = count_legal_contexts(cur_cc)
    prim['denom_note'] = ('complete-case: every unit denom = 2 members * 16 rows * '
                          '(1/2+1/2) / 16^2 = 1/8')

    # scope variants (transparency; gate uses primary complete-case all batches)
    scope_stats = {}
    for name, selmask in (
            ('batch1_all_cells', (k == 4) & (batch == 1)),
            ('batch1_target_cells', (k == 4) & (batch == 1) & np.array([c in target_set for c in cell])),
            ('batch2_all_cells', (k == 4) & (batch == 2))):
        sel = np.flatnonzero(selmask)
        if len(sel) == 0:
            scope_stats[name] = {'rows': 0}
            continue
        r = build_records(sel, batch, cell, da, db, a, b, h1v, h2v, rowmean, k)
        cur = member_curves(r, 'cc')
        st = summarize(pair_stats(cur, denom_per_pair_const=1.0 / 8.0))
        st['rows'] = int(len(sel))
        st['member_contexts_complete'] = int(len(cur))
        st['contexts_legal'] = count_legal_contexts(cur)
        scope_stats[name] = st

    # ---------- all-available sensitivity calibration (rule A contexts) ----------
    print('[ON2-EX] all-available sensitivity calibration ...', flush=True)
    rec_av = build_records(av, batch, cell, da, db, a, b, h1v, h2v, rowmean, k)
    rec_av['hsum'] = np.concatenate([hsum[av], hsum[av]])
    cur_av = member_curves(rec_av, 'av')
    stat_av = pair_stats(cur_av, denom_per_pair_const=None)
    avs = summarize(stat_av)
    avs['cohort'] = ('all-available rows with >=2 non-null technical replicates; '
                     'member contexts with all 16 rows having k>=2 (rule A strict)')
    avs['rows_used'] = int(len(av))
    avs['rows_excluded_k1'] = int(K1_EXPECTED)
    avs['member_contexts_complete'] = int(len(cur_av))
    avs['contexts_legal'] = count_legal_contexts(cur_av)
    avs['denom_note'] = ('all-available: per-unit denom = sum over two members, 16 rows, '
                         '(1/h1 + 1/h2)/16^2 with fixed-index h1/h2')

    # all-available no-exclusion unit count: all 16-row member contexts (including k=1 rows)
    rec_all = build_records(allrows, batch, cell, da, db, a, b, h1v, h2v, rowmean, k)
    rec_all['hsum'] = np.concatenate([hsum[allrows], hsum[allrows]])
    cur_all = member_curves(rec_all, 'av')
    units_no_excl = pair_stats(cur_all, denom_per_pair_const=None)['units']
    avs['units_no_exclusion'] = int(units_no_excl)
    avs['units_excluded'] = int(units_no_excl - stat_av['units'])
    prim['units_no_exclusion_all_available'] = int(units_no_excl)
    prim['units_excluded_all_available'] = int(units_no_excl - stat_av['units'])
    avs['units_excluded_formula'] = 'all-available no-exclusion units minus rule-A units'
    prim['units_excluded_formula'] = ('complete-case calibration excludes 0 units; the '
                                       'all-available rule-A exclusion diagnostic uses '
                                       'no-exclusion units minus rule-A units')

    # ---------- deterministic row-mean single imputation sensitivity ----------
    print('[ON2-EX] deterministic single-imputation sensitivity ...', flush=True)
    # row mean over non-null reps is imputation-consistent: filling missing with the
    # non-null row mean leaves the row mean unchanged; the imputed full row mean equals
    # the observed non-null mean.
    rec_imp = build_records(allrows, batch, cell, da, db, a, b, h1v, h2v, rowmean, k)
    rec_imp['imputed_rowmean'] = np.concatenate([rowmean[allrows], rowmean[allrows]])
    cur_imp = (rec_imp.groupby(['batch', 'cell', 'partner', 'prole', 'member'], sort=True)
               .agg(n_rows=('row', 'size'), curve_mean=('imputed_rowmean', 'mean'))
               .reset_index())
    cur_imp = cur_imp[cur_imp.n_rows == 16].copy()
    imp_units = 0
    imp_sum = 0.0
    for key, grp in cur_imp.groupby(['batch', 'cell', 'partner', 'prole'], sort=True):
        grp = grp.sort_values('member')
        m = len(grp)
        if m < 2:
            continue
        cm = grp.curve_mean.to_numpy(dtype=float)
        iu = np.triu_indices(m, 1)
        imp_sum += float(np.sum((cm[:, None] - cm[None, :])[iu]))
        imp_units += int(iu[0].size)
    imp_mean = imp_sum / imp_units if imp_units else None
    imp = {
        'method': 'deterministic row-mean single imputation (NOT MI; no m/seed/Rubin)',
        'cohort': 'all rows with >=1 non-null replicate; missing replicate = mean of non-null replicates in that row',
        'rows_used': int(n_rows),
        'units': int(imp_units),
        'delta_mean': imp_mean,
        'delta_sum': imp_sum,
        'delta_min_provisional': DELTA_MIN,
        'abs_delta_mean_lt_delta_min': (abs(imp_mean) < DELTA_MIN if imp_mean is not None else None),
        'note': ('descriptive sensitivity only; mean delta is NOT an effect estimate and '
                 'is not a qualification gate; no effect/updater comparison'),
    }

    # complete-case/all-available delta means for side-by-side descriptive comparison
    # (same scopes as the unit sets)
    primary_delta_mean = prim['delta_mean']
    av_delta_mean = avs['delta_mean']
    # batch1-target single-imputation sensitivity (descriptive)
    sel_t = np.flatnonzero(np.array([c in target_set for c in cell]) & (batch == 1))
    rec_it = build_records(sel_t, batch, cell, da, db, a, b, h1v, h2v, rowmean, k)
    rec_it['imputed_rowmean'] = np.concatenate([rowmean[sel_t], rowmean[sel_t]])
    cur_it = rec_it.groupby(['batch', 'cell', 'partner', 'prole', 'member']).agg(
        n_rows=('row', 'size'), curve_mean=('imputed_rowmean', 'mean')).reset_index()
    cur_it = cur_it[cur_it.n_rows == 16]
    it_units = 0
    it_sum = 0.0
    for key, grp in cur_it.groupby(['batch', 'cell', 'partner', 'prole'], sort=True):
        grp = grp.sort_values('member')
        m = len(grp)
        if m < 2:
            continue
        cm = grp.curve_mean.to_numpy(dtype=float)
        iu = np.triu_indices(m, 1)
        it_sum += float(np.sum((cm[:, None] - cm[None, :])[iu]))
        it_units += int(iu[0].size)
    imp['batch1_target'] = {'units': int(it_units),
                            'delta_mean': (it_sum / it_units if it_units else None),
                            'delta_sum': it_sum}

    # ---------- gate / verdict ----------
    mde = prim['mde80']
    gate_pass = bool(mde is not None and mde <= DELTA_MIN)
    if gate_pass:
        status = 'calibration_passed'
        verdict = 'qualification_execution_complete_can_enter_development_descriptive_analysis'
        next_step = ('资格执行完成，可进入开发性描述分析（须另立协议+独立挑战）')
        stop_reason = None
    else:
        status = 'design_invalid: precision_insufficient'
        verdict = 'design_invalid: precision_insufficient'
        next_step = None
        stop_reason = 'measured MDE80 > delta_min_provisional=0.10; stop; no effect step'

    result = {
        'task': 'R199-ON2-EX',
        'protocol': 'PROTOCOL_ON2.md v2.2 (frozen; post-observation protocol revision)',
        'scope': 'execution-time qualification calibration only; NOT an effect analysis',
        'inputs': inputs,
        'constants': {
            'mde_factor': MDE_FACTOR,
            'delta_min_provisional': DELTA_MIN,
            'n_eff': N_EFF,
            'se_unit_denominator_sqrt': 32.0,
            'split_rule': ('fixed replicate-column index viability1..4; first h1=ceil(k/2) '
                           'non-null indices vs remaining h2=k-h1; NEVER sort by observed value'),
            'k_rules': {'4': '2+2', '3': '2+1', '2': '1+1', '1': 'excluded and counted'},
        },
        'primary': prim,
        'scope_calibrations': scope_stats,
        'all_available_sensitivity_calibration': avs,
        'single_imputation_sensitivity': imp,
        'exclusions': {
            'rows_total': n_rows,
            'rows_excluded_k1': int(K1_EXPECTED),
            'all_available_rows_used': int(len(av)),
            'all_available_units_no_exclusion': int(units_no_excl),
            'all_available_units_rule_a': int(stat_av['units']),
            'all_available_units_excluded': int(units_no_excl - stat_av['units']),
            'units_excluded': int(units_no_excl - stat_av['units']),
            'units_excluded_primary': 0,
            'units_excluded_all_available': int(units_no_excl - stat_av['units']),
            'all_available_member_contexts_complete': int(len(cur_av)),
            'all_available_member_contexts_excluded': int(len(cur_all) - len(cur_av)),
            'complete_case_units': int(stat_cc['units']),
            'complete_case_member_contexts': int(len(cur_cc)),
        },
        'certification': {
            'sigma_e': prim['sigma_e'],
            'se_unit': prim['se_unit'],
            'mde80': prim['mde80'],
            'n_eff': N_EFF,
            'delta_min_provisional': DELTA_MIN,
            'mde80_le_delta_min': bool(prim['mde80'] is not None and prim['mde80'] <= DELTA_MIN),
            'status': status,
            'verdict': verdict,
            'next_step_allowed': next_step,
            'stop_reason': stop_reason,
        },
        'attestation': {
            'effect_analysis': False,
            'training': False,
            'updater_comparison': False,
            'response_values_used_only_for_calibration_and_imputation_sensitivity': True,
            'resource_sufficient_claim': False,
            'independent_confirmation_claim': False,
            'migration_claim': False,
            'decision_benefit_claim': False,
            'mechanism_claim': False,
            'novel_algorithm_claim': False,
            'frozen_protocol_followed': True,
        },
        'determinism': {
            'json_sorted_keys': True,
            'timestamps': False,
            'allow_nan': False,
            'round_digits': ROUND_DIGITS,
        },
    }
    write_json(result, OUTJSON)

    wall = time.perf_counter() - t0
    cpu = time.process_time() - c0
    usage = {
        'task': 'R199-ON2-EX',
        'command': 'python -X utf8 research/2026-10-27-core-module-design/oneil_dev/exec_calibration/run_calib.py',
        'wall_seconds': rq(wall, 3),
        'cpu_process_seconds': rq(cpu, 3),
        'wall_seconds_python_time': rq(wall, 3),
        'cpu_seconds': rq(cpu, 3),
        'gpu_hours': None,
        'peak_rss_mb': None,
        'python': platform.python_version(),
        'numpy': np.__version__,
        'pandas': pd.__version__,
        'platform': platform.platform(),
        'inputs_bytes_total': int(sum(v['bytes'] for v in inputs.values())),
        'effect_training_updater_run': False,
        'on2_frozen_artifacts_modified': False,
        'output_calib_sha256': sha256_file(OUTJSON),
        'output_usage_sha256_note': 'usage_calib.json is written after this record; SHA recorded in record_calib.md',
    }
    write_json(usage, OUTUSAGE)

    print(json.dumps({
        'sigma_e': prim['sigma_e'], 'se_unit': prim['se_unit'],
        'mde80': prim['mde80'], 'delta_min': DELTA_MIN,
        'gate': status,
        'units_complete_case': prim['units'],
        'units_all_available_ruleA': avs['units'],
        'units_excluded': avs['units_excluded'],
        'single_imputation_units': imp['units'],
        'single_imputation_delta_mean': imp['delta_mean'],
        'wall_seconds': wall, 'cpu_seconds': cpu,
    }, indent=1, ensure_ascii=False))
    return 0 if gate_pass else 3


if __name__ == '__main__':
    sys.exit(main())
