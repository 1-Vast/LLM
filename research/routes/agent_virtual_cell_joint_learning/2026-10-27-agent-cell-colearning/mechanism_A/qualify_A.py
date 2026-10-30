#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-A qualification: O'Neil complete-case 4x4 grid as a cross-plan shared-operator resource.

Metadata/structure/operator-consistency audit ONLY (no response-value effect statistics, no fitting):
  * reads the O'Neil combination workbook identity/dose columns + viability NULLNESS (complete-case mask);
  * counts pair-cells / cells / drugs / dose grids / missingness / batch loss;
  * builds the shared-operator design (additive member dose response + partner functions) and reports
    per-cell rank / gauge / over-identification (constraints available for joint-contradiction testing);
  * counts cross-plan support (same (cell, drug, role, dose) in >=2 pair-cell contexts; plan pairs);
  * Jaaks fitted table: identity/dose-column metadata only -> judged not a CL1 target;
  * pre-registered planning MDE for decision endpoints at cluster=cell (30 target cells).
PROBLEM_A.md is the frozen formalization contract (written before this script).
"""
import sys
import os
import json
import math
import hashlib
import time
from collections import defaultdict

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

ROOT = r'D:\MAESTRO'
BASE = os.path.join(ROOT, 'research', '2026-10-27-agent-cell-colearning', 'mechanism_A')
ONEIL = os.path.join(ROOT, 'data', 'raw', 'oneil2026_qualification',
                     '15357163mct150843-sup-156849_1_supp_1_w2lrww.xls')
ON1JSON = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev', 'on1.json')
PEEK = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev',
                    'PEEK_DISCLOSURE_ON3.md')
ON3EXEC = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev',
                       'on3_exec.json')
JAAKS = os.path.join(ROOT, 'data', 'external', 'gdsc_combinations', 'jaaks2022_figshare',
                     'Original screen_All tissues_fitted data.csv')
PROBLEM = os.path.join(BASE, 'PROBLEM_A.md')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(BASE, 'qualify_A.json')

DELTA_MIN = 0.05
MDE_FACTOR = 2.801585218112968
N_TARGET_CELLS = 30
ON2_EXPECTED = {'complete_rows': 363090, 'batch1_complete_rows': 357876,
                'batch2_complete_rows': 5214, 'batch3_complete_rows': 0,
                'pair_cells_16': 22035, 'pair_cells_15': 702, 'pair_cells_0': 315,
                'pair_cells_total': 23052}


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


def norm(s):
    import unicodedata
    return ''.join(ch for ch in unicodedata.normalize('NFKC', str(s)).casefold() if ch.isalnum())


def canon_conc(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return format(v, '.10g')


def quantiles(arr):
    a = np.asarray(arr, dtype=float)
    if a.size == 0:
        return {}
    out = {}
    for q in (0, 5, 25, 50, 75, 95, 100):
        out[str(q)] = int(np.percentile(a, q)) if q in (0, 100) else rq(float(np.percentile(a, q)), 2)
    return out


def main():
    t0 = time.time()
    log = []

    def say(m):
        print(m, flush=True)
        log.append(m)

    say('[1/10] verify inputs ...')
    sha = {}
    for key, path in (('problem_a', PROBLEM), ('script', SCRIPT), ('oneil_combo', ONEIL),
                      ('on1_json', ON1JSON), ('peek_disclosure', PEEK), ('on3_exec', ON3EXEC),
                      ('jaaks_fitted', JAAKS)):
        if not os.path.isfile(path):
            raise SystemExit('FATAL missing input: %s' % key)
        sha[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                    'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    on1 = json.load(open(ON1JSON, encoding='utf-8'))
    target_cells = sorted(norm(c) for c in on1['cells']['target_nonoverlap'])
    overlap_cells = sorted(norm(c) for c in on1['cells']['jaaks_overlap'])
    say('    inputs verified; target cells=%d, Jaaks-overlap cells=%d' %
        (len(target_cells), len(overlap_cells)))

    say('[2/10] read O\'Neil workbook (identity/dose columns + viability NULLNESS only) ...')
    fh = open(ONEIL, 'rb')
    df = pd.read_excel(fh, sheet_name='combination response', engine='openpyxl')
    fh.close()
    if df.shape[0] != 368832:
        raise SystemExit('FATAL unexpected row count: %d' % df.shape[0])
    df['cell'] = [norm(x) for x in df['cell_line'].to_numpy()]
    df['drugA'] = [norm(x) for x in df['drugA_name'].to_numpy()]
    df['drugB'] = [norm(x) for x in df['drugB_name'].to_numpy()]
    df['concA'] = [canon_conc(x) for x in df['drugA Conc (µM)'].to_numpy()]
    df['concB'] = [canon_conc(x) for x in df['drugB Conc (µM)'].to_numpy()]
    vcols = ['viability1', 'viability2', 'viability3', 'viability4']
    nan = df[vcols].isna()
    df['k'] = 4 - nan.sum(axis=1).astype(int)
    df['complete'] = df['k'] == 4
    df['pair'] = [tuple(sorted((a, b))) for a, b in zip(df['drugA'], df['drugB'])]
    df['pc'] = list(zip(df['BatchID'].astype(int), df['cell'], df['pair']))
    say('    rows=%d cells=%d drugs=%d pairs=%d' % (
        len(df), df['cell'].nunique(),
        len({d for d in df['drugA']} | {d for d in df['drugB']}), df['pair'].nunique()))

    say('[3/10] pair-cell / batch / missingness structure ...')
    batches = {}
    for b, g in df.groupby('BatchID'):
        batches[str(int(b))] = {'rows': int(len(g)), 'cells': int(g['cell'].nunique()),
                                'pair_cells': int(g['pc'].nunique()),
                                'complete_rows': int(g['complete'].sum())}
    pcg = df.groupby('pc').agg(n_rows=('complete', 'size'), n_complete=('complete', 'sum'))
    buckets = {str(int(k)): int(v) for k, v in pcg['n_complete'].value_counts().sort_index().items()}
    row_buckets = {str(int(k)): int(v) for k, v in pcg['n_rows'].value_counts().sort_index().items()}
    k_counts = {str(int(k)): int(v) for k, v in df['k'].value_counts().sort_index().items()}
    missing = {
        'rows_total': int(len(df)),
        'k_counts': k_counts,
        'complete_case_rows': int(df['complete'].sum()),
        'complete_case_share': rq(float(df['complete'].mean())),
        'pair_cell_complete_row_buckets': buckets,
        'pair_cell_rows_buckets': row_buckets,
        'batches': batches,
        'on2_expected': ON2_EXPECTED,
        'matches_on2_expected': {
            'complete_rows': int(df['complete'].sum()) == ON2_EXPECTED['complete_rows'],
            'pair_cells_16': buckets.get('16') == ON2_EXPECTED['pair_cells_16'],
            'pair_cells_15': buckets.get('15') == ON2_EXPECTED['pair_cells_15'],
            'pair_cells_0': buckets.get('0') == ON2_EXPECTED['pair_cells_0'],
            'batch1': batches.get('1', {}).get('complete_rows') == ON2_EXPECTED['batch1_complete_rows'],
            'batch2': batches.get('2', {}).get('complete_rows') == ON2_EXPECTED['batch2_complete_rows'],
            'batch3': batches.get('3', {}).get('complete_rows') == ON2_EXPECTED['batch3_complete_rows'],
        },
        'note': 'ON2 v2.1 metadata-only complete-case convention: complete iff viability1-4 all non-null; '
                'only the NULLNESS mask is used, no response values enter any statistic',
    }
    say('    complete rows=%d (%.2f%%); buckets=%s; matches_on2=%s' % (
        missing['complete_case_rows'], 100 * missing['complete_case_share'],
        buckets, all(missing['matches_on2_expected'].values())))

    say('[4/10] 4x4 dose-grid + cross-plan (member replacement) support ...')
    grid_rows = []
    for key, g in df[df['complete']].groupby('pc'):
        nA = int(g['concA'].nunique())
        nB = int(g['concB'].nunique())
        ncombo = int(g[['concA', 'concB']].drop_duplicates().shape[0])
        grid_rows.append({'pc': key, 'n_complete': int(len(g)), 'nA': nA, 'nB': nB, 'n_combo': ncombo})
    grid_df = pd.DataFrame(grid_rows)
    grid_ok = grid_df[(grid_df['n_complete'] == 16) & (grid_df['nA'] == 4) &
                      (grid_df['nB'] == 4) & (grid_df['n_combo'] == 16)]
    grid_ok_keys = set(grid_ok['pc'])
    n_grid_b1 = int(sum(1 for (b, c, p) in grid_ok_keys if b == 1))
    say('    complete-case pair-cells=%d; complete 4x4 grids (all batches)=%d (batch1=%d)' % (
        int(pcg.shape[0]), int(len(grid_ok)), n_grid_b1))

    pc_meta = {}
    for key, g in df[(df['BatchID'] == 1) & df['complete']].groupby('pc'):
        if key not in grid_ok_keys:
            continue
        meta = {}
        for row in g.itertuples(index=False):
            meta.setdefault(row.drugA + '|A', set()).add(row.concA)
            meta.setdefault(row.drugB + '|B', set()).add(row.concB)
        pc_meta[key] = {kk: tuple(sorted(v)) for kk, v in meta.items()}
    cell_pcs = defaultdict(list)
    for (b, c, p), meta in pc_meta.items():
        cell_pcs[c].append(meta)
    ctx_meta = defaultdict(list)
    for (b, c, p), meta in pc_meta.items():
        for role_key, doses in meta.items():
            drug, role = role_key.split('|')
            ctx_meta[(c, drug, role)].append(tuple(doses))
    n_ctx = len(ctx_meta)
    ctx_ge2 = sum(1 for v in ctx_meta.values() if len(v) >= 2)
    ctx_aligned = sum(1 for v in ctx_meta.values()
                      if len(v) >= 2 and len({tuple(sorted(x)) for x in v}) == 1)
    dose_ctx = defaultdict(int)
    for (c, d, role), v in ctx_meta.items():
        for doses in v:
            for dose in doses:
                dose_ctx[(c, d, role, dose)] += 1
    dose_ge2 = sum(1 for v in dose_ctx.values() if v >= 2)
    plan_pairs = defaultdict(int)
    for c, mlist in cell_pcs.items():
        for i in range(len(mlist)):
            for j in range(i + 1, len(mlist)):
                mi, mj = mlist[i], mlist[j]
                shared = 0
                for role_key in set(mi) & set(mj):
                    if len(set(mi[role_key]) & set(mj[role_key])) >= 2:
                        shared += 1
                if shared >= 1:
                    plan_pairs[c] += 1
    n_plan_pairs = int(sum(plan_pairs.values()))
    pairs_per_cell = {c: len(v) for c, v in cell_pcs.items()}
    say('    cells with complete-grid pairs=%d; pair-cells/cell median=%s; contexts=%d (>=2=%d, '
        'aligned=%d); dose-level shared=%d; plan pairs=%d' % (
            len(cell_pcs), np.median(list(pairs_per_cell.values())) if pairs_per_cell else 0,
            n_ctx, ctx_ge2, ctx_aligned, dose_ge2, n_plan_pairs))

    say('[5/10] shared-operator identifiability audit (additive member dose response + partner) ...')
    ident = []
    for c, mlist in cell_pcs.items():
        pc_keys = [k for k, meta in pc_meta.items() if k[1] == c]
        g_cell = df[(df['BatchID'] == 1) & (df['cell'] == c) & df['complete']]
        obs = []
        for (b, cc, pair) in pc_keys:
            g = g_cell[g_cell['pair'] == pair]
            for row in g.itertuples(index=False):
                obs.append((row.drugA + '|A', row.concA, row.drugB + '|B', row.concB))
        cols = sorted({(a, ca) for a, ca, b, cb in obs} | {(b, cb) for a, ca, b, cb in obs})
        col = {x: i for i, x in enumerate(cols)}
        D = np.zeros((len(obs), len(cols)), dtype=np.int8)
        parent = list(range(len(cols)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[ry] = rx

        for i, (a, ca, b, cb) in enumerate(obs):
            ia, ib = col[(a, ca)], col[(b, cb)]
            D[i, ia] = 1
            D[i, ib] = 1
            union(ia, ib)
        comps = len({find(i) for i in range(len(cols))}) if cols else 0
        rank = int(np.linalg.matrix_rank(D.astype(float))) if len(obs) else 0
        ident.append({'cell': c, 'n_pair_cells': len(pc_keys), 'n_obs': int(len(obs)),
                      'n_context_dose_cols': len(cols), 'rank': rank,
                      'gauge_nullity': int(len(cols) - rank), 'components': int(comps),
                      'over_identification': int(len(obs) - rank)})
    over_pos = [x for x in ident if x['over_identification'] >= 1]
    over_ge16 = [x for x in ident if x['over_identification'] >= 16]
    target_ident = [x for x in ident if x['cell'] in target_cells]
    over_pos_target = sum(1 for x in target_ident if x['over_identification'] >= 1)
    say('    cells audited=%d; over-id>=1=%d; over-id>=16=%d; target30 audited=%d (>=1: %d); '
        'median over-id=%s' % (len(ident), len(over_pos), len(over_ge16), len(target_ident),
                               over_pos_target,
                               np.median([x['over_identification'] for x in ident]) if ident else None))

    say('[6/10] missingness / reference audit ...')
    ref_rows = int(((df['drugA'] == '') | (df['drugB'] == '') |
                    df['drugA'].str.contains('dmso|vehicle', regex=True) |
                    df['drugB'].str.contains('dmso|vehicle', regex=True)).sum())
    refs = {
        'combo_workbook_rows_with_missing_or_vehicle_drug_names': ref_rows,
        'combo_workbook_reference_note': 'combination workbook contains two-drug rows only (n=368,832); no '
                                         'single-agent / vehicle reference rows are present, so the shared '
                                         'operator cannot be anchored on absolute single-agent curves from '
                                         'this workbook',
        'single_agent_workbook': 'exists separately (1.68 MB, metadata only, not read; 16,752 rows / 39 '
                                 'cells / 38 drugs per ON1/PROTOCOL_ON1); any use as single-agent reference '
                                 'requires a separate pre-registration and qualification',
    }

    say('[7/10] Jaaks fitted table audit (identity/dose columns only) ...')
    jdf = pd.read_csv(JAAKS, usecols=['CELL_LINE_NAME', 'ANCHOR_ID', 'LIBRARY_ID',
                                      'ANCHOR_CONC', 'LIBRARY_CONC'], low_memory=False)
    jdf['cell'] = [norm(x) if isinstance(x, str) else None for x in jdf['CELL_LINE_NAME'].to_numpy()]
    jdf['pair'] = [tuple(sorted((norm(a), norm(b)))) for a, b in zip(jdf['ANCHOR_ID'], jdf['LIBRARY_ID'])]
    jdf['dose'] = [(canon_conc(a), canon_conc(b)) for a, b in zip(jdf['ANCHOR_CONC'], jdf['LIBRARY_CONC'])]
    jdoses = jdf.groupby(['cell', 'pair'])['dose'].nunique()
    jaaks_audit = {
        'rows': int(len(jdf)), 'cells': int(jdf['cell'].nunique()),
        'unordered_pairs': int(jdf['pair'].nunique()), 'cell_pair_keys': int(len(jdoses)),
        'dose_pairs_per_key': quantiles(jdoses.to_numpy()),
        'judgment': 'not_qualified',
        'failure_categories': ['no_operational_target', 'data_insufficient'],
        'reason': 'different endpoint family (SYNERGY_DELTA_EMAX vs viability); the fitted table is not a '
                  '4x4 dose-grid plan resource (sparse published dose pairs per combination); D1 already '
                  'concluded no independent target meeting the reuse thresholds; no stitching',
    }
    say('    Jaaks rows=%d cells=%d pairs=%d keys=%d dose-pairs/key max=%s' % (
        jaaks_audit['rows'], jaaks_audit['cells'], jaaks_audit['unordered_pairs'],
        jaaks_audit['cell_pair_keys'], jaaks_audit['dose_pairs_per_key'].get('100')))

    say('[8/10] planning MDE for decision endpoints (cluster = cell) ...')
    rank_mde = MDE_FACTOR * math.sqrt(2.0 / (N_TARGET_CELLS - 3.0))
    n_required = {'0.05': rq(2.0 * (MDE_FACTOR / 0.05) ** 2 + 3.0),
                  '0.10': rq(2.0 * (MDE_FACTOR / 0.10) ** 2 + 3.0)}
    topk = {('k%d' % k): rq(MDE_FACTOR * math.sqrt(2.0 * p * (1.0 - p) / N_TARGET_CELLS))
            for k, p in ((1, 0.3), (3, 0.4), (5, 0.5))}
    regret = {('sd_%s' % sd): rq(MDE_FACTOR * sd / math.sqrt(N_TARGET_CELLS)) for sd in (0.5, 0.3, 0.2)}
    mde = {
        'delta_min': DELTA_MIN, 'n_target_cells': N_TARGET_CELLS,
        'rank_delta_rho_mde80': rq(rank_mde),
        'required_independent_cells_for_rank_gate': n_required,
        'topk_precision_planning_mde80': topk,
        'normalized_regret_planning_mde80': regret,
        'judgment': 'evaluation_cannot_distinguish',
        'reason': 'with only 30 independent target cells every planning MDE is far above delta_min=0.05; '
                  'decision-benefit claims cannot be certified on this resource (rank MDE=0.7625; needs '
                  '~6,283 independent cells for delta=0.05 / ~1,573 for delta=0.10)',
        'allowed_role': 'development-only formal/existence diagnostics; decision endpoints descriptive only, '
                        'never reported as decision benefit',
    }
    say('    rank MDE80=%.4f; required cells (delta0.05)=%s, (delta0.10)=%s' % (
        rank_mde, n_required['0.05'], n_required['0.10']))

    say('[9/10] qualification judgment ...')
    conditions = [
        "development-only O'Neil resource (viability; technical replicates are NOT independent cultures)",
        'batch1 complete-case main population; batch2 disclosure only; batch3 lost entirely (0 complete rows)',
        '702 15-row pair-cells excluded from complete grids; no interpolation/extrapolation',
        'no single-agent/double-drug reference in the combination workbook; single-agent workbook is '
        'metadata-only and would need its own qualification',
        'non-blind/peeked inherited from ON3 QUICK artifact (PEEK_DISCLOSURE_ON3); no blind/independent claim',
        'joint-contradiction testing is possible only where over-identification >= 1 and member/dose '
        'overlap exists; cells/pairs below that are not testable',
        'decision-benefit endpoint is evaluation_cannot_distinguish at delta_min=0.05 with 30 cells; only '
        'formal/existence and internal consistency claims are allowed',
        'no stitching with Jaaks ΔEMAX; no migration/cross-culture/mechanism/novelty claims',
    ]
    judgement = {
        'resource': "O'Neil complete-case batch1 4x4 combination viability grid",
        'support': {
            'n_pair_cells_total': int(pcg.shape[0]),
            'n_pair_cells_complete_grid_batch1': n_grid_b1,
            'n_cells_with_complete_grid_pairs': int(len(cell_pcs)),
            'n_target30_cells_with_complete_grid_pairs': int(sum(1 for c in cell_pcs if c in target_cells)),
            'n_drug_role_contexts': int(n_ctx),
            'n_drug_role_contexts_ge2': int(ctx_ge2),
            'n_drug_role_contexts_identical_dose_sets': int(ctx_aligned),
            'n_dose_levels_shared_across_contexts': int(dose_ge2),
            'n_plan_pairs_sharing_member_and_ge2_doses': int(n_plan_pairs),
            'pairs_per_cell': quantiles(list(pairs_per_cell.values())),
            'per_cell_plan_pairs': quantiles(list(plan_pairs.values())),
            'n_cells_identifiability_audited': int(len(ident)),
            'n_cells_over_identification_ge1': int(len(over_pos)),
            'n_cells_over_identification_ge16': int(len(over_ge16)),
            'n_target30_cells_audited': int(len(target_ident)),
            'n_target30_cells_over_id_ge1': int(over_pos_target),
            'over_identification_quantiles': quantiles([x['over_identification'] for x in ident]),
        },
        'judgment': 'qualified_with_conditions',
        'conditions': conditions,
        'decision_benefit_on_this_resource': 'evaluation_cannot_distinguish',
        'required_measurements_for_decision_claim': {
            'independent_cells': n_required['0.05'],
            'note': 'independent biological units (cell lines / patient-derived cultures), not wells or '
                    'replicate plans; external to the O\'Neil target30; needs a separate pre-registration',
        },
    }
    say('    judgment=%s (decision benefit: evaluation_cannot_distinguish)' % judgement['judgment'])

    t_end = time.time()
    out = {
        'protocol': {'path_rel': 'research/2026-10-27-agent-cell-colearning/mechanism_A/PROBLEM_A.md',
                     'sha256': sha256_file(PROBLEM)},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        'inputs': sha,
        'oneil_structure': {
            'n_rows': int(len(df)), 'n_batches': int(df['BatchID'].nunique()),
            'batches': batches, 'n_pair_cells': int(pcg.shape[0]),
            'n_cells': int(df['cell'].nunique()),
            'n_drugs': int(len({d for d in df['drugA']} | {d for d in df['drugB']})),
            'n_grid_4x4_pair_cells_all_batches': int(len(grid_ok)),
            'n_grid_4x4_pair_cells_batch1': n_grid_b1,
        },
        'cross_plan_support': {
            'cells_with_complete_grid_pairs': int(len(cell_pcs)),
            'pairs_per_cell': quantiles(list(pairs_per_cell.values())),
            'drug_role_contexts': int(n_ctx),
            'drug_role_contexts_ge2': int(ctx_ge2),
            'drug_role_contexts_identical_dose_sets': int(ctx_aligned),
            'dose_level_shared_contexts': int(dose_ge2),
            'plan_pairs_sharing_member_and_ge2_doses': int(n_plan_pairs),
            'per_cell_plan_pairs': quantiles(list(plan_pairs.values())),
        },
        'identifiability_audit': {
            'operator_family': 'additive: y(pair(a,b); d_a,d_b) = f_{a,roleA}(d_a) + g_{b,roleB}(d_b)',
            'per_cell': ident,
            'summary': {
                'n_cells': int(len(ident)),
                'over_identification_quantiles': quantiles([x['over_identification'] for x in ident]),
                'rank_quantiles': quantiles([x['rank'] for x in ident]),
                'n_over_id_ge1': int(len(over_pos)),
                'n_over_id_ge16': int(len(over_ge16)),
                'target30_n': int(len(target_ident)),
                'target30_over_id_ge1': int(over_pos_target),
            },
        },
        'missingness': missing,
        'reference_audit': refs,
        'jaaks_audit': jaaks_audit,
        'mde_planning': mde,
        'qualification': judgement,
        'boundaries': [
            'development-only; no effect/decision/migration/mechanism/novelty claims',
            'no response values used for statistics: only the viability1-4 NULLNESS mask was read (ON2 '
            'v2.1 metadata-only convention); no means/effects were computed',
            "O'Neil plan family in this audit = rows of the 4x4 dose grid (P-dose) and member replacement "
            '(P-replace); P-program (time course/sequence) is not supported by this resource',
            'shared-operator identifiability audit uses design-matrix rank only (no fitting)',
            'non-blind/peeked inherited from ON3 (QUICK invalid artifact seen); no blind/independent claim',
        ],
        'deviations': [],
        'log': log,
    }
    write_json(out, OUTJSON)
    print('qualify_A.json sha256:', sha256_file(OUTJSON))
    print('DONE wall=%.1fs' % (t_end - t0))


if __name__ == '__main__':
    main()
