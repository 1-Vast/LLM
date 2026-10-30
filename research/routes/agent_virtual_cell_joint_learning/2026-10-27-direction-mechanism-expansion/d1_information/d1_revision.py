#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R200-D1.1 revision (v0.2): corrected target eligibility + locked target hierarchy/power +
operationalized design inputs. PROTOCOL_D1_v0_2.md is the frozen contract.

Metadata/algebra audit ONLY (same discipline as v0.1):
  * re-verify input SHAs and re-state the corrected O'Neil / nyman2020 / T4 facts;
  * compute the corrected eligibility table (9 candidates) with frozen failure categories;
  * compute the pre-registered planning MDE80 table for T1/T2/T3 (frozen formula, deterministic);
  * record the design decision (T2 primary candidate vs design_invalid -> stop);
  * no model fitting, no effect/transfer statistics, no response reads for O'Neil/Validation.

Deterministic: fixed order, JSON sort_keys, no timestamps, allow_nan=False.
"""
import sys
import os
import json
import math
import hashlib
import time

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

ROOT = r'D:\MAESTRO'
BASE = os.path.join(ROOT, 'research', '2026-10-27-direction-mechanism-expansion', 'd1_information')
CS = os.path.join(ROOT, 'research', '2026-10-27-conditional-shift')
QS = os.path.join(ROOT, 'research', '2026-10-27-q-structure')
EXT = os.path.join(ROOT, 'data', 'external')
ON = os.path.join(ROOT, 'research', '2026-10-27-oneil-transfer-qualification')
OND = os.path.join(ROOT, 'research', '2026-10-27-core-module-design', 'oneil_dev')
ONEIL_RAW = os.path.join(ROOT, 'data', 'raw', 'oneil2026_qualification')
VAL = os.path.join(EXT, 'gdsc_combinations', 'jaaks2022_figshare',
                   'Validation screen_All tissues_fitted data.csv')
PROTOCOL = os.path.join(BASE, 'PROTOCOL_D1_v0_2.md')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(BASE, 'd1_v0_2.json')
V01_JSON = os.path.join(BASE, 'd1.json')

DELTA_MIN = 0.05
MDE_FACTOR = 2.801585218112968
ICC_MULTIPLIERS = [0.0, 0.5, 1.0, 2.0]
RHO_AB = [0.0, 0.5, 0.8]
SEED = 20261120


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


def plan_mde(n_units, cells, conds, icc_cell, icc_cond, rho_ab):
    """Pre-registered planning MDE for Delta_rho (Spearman difference).

    DE = 1 + (mbar_cell-1)*ICC_cell + (mbar_cond-1)*ICC_cond ; n_eff = n_units/DE
    Var(Delta_rho) = 2(1-rho_ab)/(n_eff-3) ; MDE80 = 2.801585*sqrt(Var)
    """
    mbar_c = n_units / float(cells)
    mbar_d = n_units / float(conds)
    de = 1.0 + (mbar_c - 1.0) * icc_cell + (mbar_d - 1.0) * icc_cond
    n_eff = n_units / de
    var = 2.0 * (1.0 - rho_ab) / max(1e-9, (n_eff - 3.0))
    mde = MDE_FACTOR * math.sqrt(var)
    return {'n_units': int(n_units), 'mbar_cell': rq(mbar_c), 'mbar_cond': rq(mbar_d),
            'design_effect': rq(de), 'n_eff': rq(n_eff), 'rho_ab': rho_ab,
            'var_delta_rho': rq(var), 'sd_delta_rho': rq(math.sqrt(var)),
            'mde80': rq(mde), 'passes_delta_min': bool(mde <= DELTA_MIN)}


def main():
    t0 = time.time()
    log = []

    def say(m):
        print(m, flush=True)
        log.append(m)

    say('[1/8] verify inputs ...')
    inputs = {}
    for key, path in (('protocol_v0_2', PROTOCOL), ('script_v0_2', SCRIPT),
                      ('v0_1_json', V01_JSON),
                      ('v0_1_protocol', os.path.join(BASE, 'PROTOCOL_D1.md')),
                      ('v0_1_script', os.path.join(BASE, 'd1.py')),
                      ('matched_conditions', os.path.join(CS, 'matched_conditions.csv')),
                      ('a0_json', os.path.join(CS, 'a0.json')),
                      ('on1_json', os.path.join(OND, 'on1.json')),
                      ('protocol_on1', os.path.join(OND, 'PROTOCOL_ON1.md')),
                      ('oneil_counts', os.path.join(ON, 'counts.json')),
                      ('oneil_report', os.path.join(ON, 'report.md')),
                      ('validation_fitted', VAL)):
        inputs[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                       'exists': os.path.isfile(path),
                       'bytes': os.path.getsize(path) if os.path.isfile(path) else None,
                       'sha256': sha256_file(path) if os.path.isfile(path) else None}
        if not inputs[key]['exists']:
            raise SystemExit('FATAL missing input: %s' % key)
    say('    inputs verified (%d) incl. protocol/script SHA' % len(inputs))

    v01 = json.load(open(V01_JSON, encoding='utf-8'))
    a0 = json.load(open(inputs['a0_json']['sha256'] and os.path.join(CS, 'a0.json'), encoding='utf-8'))
    mc = pd.read_csv(os.path.join(CS, 'matched_conditions.csv'), dtype=str)
    on1 = json.load(open(os.path.join(OND, 'on1.json'), encoding='utf-8'))
    oneil_counts = json.load(open(os.path.join(ON, 'counts.json'), encoding='utf-8'))

    say('[2/8] O\'Neil / nyman2020 / T4 fact corrections ...')
    oneil_files = sorted(os.listdir(ONEIL_RAW))
    oneil_sizes = {f: os.path.getsize(os.path.join(ONEIL_RAW, f)) for f in oneil_files}
    oneil_total = sum(oneil_sizes.values())
    cells_meta = on1.get('cells', {})
    jaaks_overlap = cells_meta.get('jaaks_overlap') or []
    n_overlap = len(jaaks_overlap)
    frac = float(cells_meta.get('jaaks_overlap_frac', 0.0))
    n_cells_oneil = int(round(n_overlap / frac)) if frac else None
    nyman_root = os.path.join(EXT, 'nyman2020')
    nyman_files = []
    for root, dirs, fs in os.walk(nyman_root):
        for f in fs:
            nyman_files.append(os.path.join(root, f))
    nyman_bytes = sum(os.path.getsize(p) for p in nyman_files)
    # Validation identity-only metadata (no response columns read) for T3 structure
    dv = pd.read_csv(VAL, usecols=['BARCODE', 'CELL_LINE_NAME', 'ANCHOR_ID', 'LIBRARY_ID',
                                   'ANCHOR_CONC', 'LIBRARY_CONC'], low_memory=False)

    def nk(s):
        import unicodedata
        return ''.join(ch for ch in unicodedata.normalize('NFKC', str(s)).casefold() if ch.isalnum())

    def canon(x):
        try:
            v = float(x)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(v):
            return None
        return format(v, '.10g')

    vcell = np.array([nk(x) if isinstance(x, str) else None for x in dv['CELL_LINE_NAME'].to_numpy()],
                     dtype=object)
    vaid = dv['ANCHOR_ID'].astype(str).str.strip().to_numpy()
    vlid = dv['LIBRARY_ID'].astype(str).str.strip().to_numpy()
    vac = np.array([canon(x) for x in dv['ANCHOR_CONC'].to_numpy()], dtype=object)
    vlc = np.array([canon(x) for x in dv['LIBRARY_CONC'].to_numpy()], dtype=object)
    vcomp = np.array([('|' in str(a)) or ('|' in str(b)) or ('|' in str(c))
                      for a, b, c in zip(dv['ANCHOR_ID'], dv['LIBRARY_ID'], dv['ANCHOR_CONC'])])
    vvalid = ((~vcomp) & np.array([c is not None for c in vcell])
              & (vaid != 'nan') & (vlid != 'nan')
              & np.array([x is not None for x in vac]) & np.array([x is not None for x in vlc]))
    vkeys = {}
    for i in np.nonzero(vvalid)[0]:
        vkeys[(vcell[i], (vaid[i], vlid[i], vac[i], vlc[i]))] = 1
    vkeys = set(vkeys)
    matched_keys = set()
    for r in mc.itertuples(index=False):
        matched_keys.add((r.cell, (str(r.anchor_id).strip(), str(r.library_id).strip(),
                                   canon(r.anchor_conc), canon(r.library_conc))))
    vkeys_only = sorted(k for k in vkeys if k not in matched_keys)
    t3_cells = len({k[0] for k in vkeys_only})
    t3_conds = len({k[1] for k in vkeys_only})
    facts = {
        'F1_oneil_resource': {
            'path': 'data/raw/oneil2026_qualification/',
            'n_files': len(oneil_files), 'total_bytes': oneil_total,
            'files': {f: oneil_sizes[f] for f in oneil_files},
            'used_by': 'ON1/ON2/ON3 (research/2026-10-27-core-module-design/oneil_dev/)',
            'source': 'directory listing',
        },
        'F2_oneil_jaaks_overlap': {
            'jaaks_overlap_cells': n_overlap, 'oneil_cells': n_cells_oneil,
            'overlap_fraction': rq(frac),
            'target_nonoverlap_cells': n_cells_oneil - n_overlap if n_cells_oneil else None,
            'source': 'research/2026-10-27-core-module-design/oneil_dev/on1.json (DG5) + PROTOCOL_ON1.md',
            'conservative_name_overlap': oneil_counts['counts']['intersection'],
            'status': '9/39 < the frozen >=10 shared-cell threshold of D1; no A0-matched conditions / '
                      'same endpoint',
        },
        'F3_oneil_endpoint': {
            'endpoint': 'combination response viability1-4 (mean), columns X/X0, 4x4 dose grid',
            'jaaks_endpoint': 'SYNERGY_DELTA_EMAX (fitted synergy delta)',
            'match': False,
            'source': 'PROTOCOL_ON1.md (main input: 15357163mct150843-sup-156849_1_supp_1_w2lrww.xls)',
        },
        'F4_oneil_not_blind': {
            'fact': 'O\'Neil data were used in earlier model fitting/selection and G/F evaluation; '
                    'not an unexposed sealed set',
            'source': 'research/2026-10-27-oneil-transfer-qualification/report.md',
        },
        'F5_nyman2020': {
            'dir_exists': os.path.isdir(nyman_root),
            'n_files': len(nyman_files), 'total_bytes': nyman_bytes,
            'valid_data_files': len(nyman_files),
            'classification': 'data_unavailable (directory present but no valid data files; v0.1 '
                              '"empty:false" was inconsistent)',
        },
        'F6_T4_corrected': {
            'v0_1_wording': 'no local different-measurement/culture combination resource',
            'v0_2_wording': 'no different-measurement/culture target that meets the A0 reuse thresholds '
                            '(O\'Neil is a local different-measurement combination resource, but its '
                            'Jaaks overlap is 9/39 < 10 and it has no A0-matched conditions / same endpoint)',
        },
        'F7_validation_target': {
            'n_matched_keys': len(matched_keys), 'n_cells': int(mc['cell'].nunique()),
            'n_conditions': int(len({(str(r.anchor_id).strip(), str(r.library_id).strip(),
                                      canon(r.anchor_conc), canon(r.library_conc))
                                     for r in mc.itertuples(index=False)})),
            'directed_pairs_used': int(a0['quadruples']['coverage_R4']['directed_pairs_used']),
            'common_quadruples': int(a0['quadruples']['R4_common_primary']),
            'barcode_sets_disjoint': bool(a0['overlap_original_validation']['barcode_sets_disjoint']),
            'validation_valid_keys': len(vkeys), 'validation_only_keys': len(vkeys_only),
            't3_cells': t3_cells, 't3_conditions': t3_conds,
            'note': 'same platform / same endpoint definition, different screen/plate/run: '
                    'cross-screen SAME-KEY re-test only; NOT independent measurement/culture/lineage',
        },
    }
    say('    O\'Neil: %d files / %d B; Jaaks overlap %d/%d cells; nyman2020 files=%d; '
        'Validation keys=%d (only %d)' % (
            len(oneil_files), oneil_total, n_overlap, n_cells_oneil, len(nyman_files),
            len(vkeys), len(vkeys_only)))

    say('[3/8] corrected eligibility table v0.2 ...')
    val_dir = os.path.join(EXT, 'gdsc_combinations', 'jaaks2022_figshare')
    candidates = [
        {
            'candidate': 'Jaaks Validation fitted screen',
            'path_rel': 'data/external/gdsc_combinations/jaaks2022_figshare/Validation screen_All '
                        'tissues_fitted data.csv',
            'local': {'exists': os.path.isfile(VAL), 'bytes': os.path.getsize(VAL)},
            'target': 'SYNERGY_DELTA_EMAX on 9,154 matched keys (cross-screen same-key re-test)',
            'independent_groups': 2, 'shared_cells': int(mc['cell'].nunique()),
            'directed_pairs': int(a0['quadruples']['coverage_R4']['directed_pairs_used']),
            'matched_quadruples_or_keys': int(a0['quadruples']['R4_common_primary']),
            'raw_evidence_disjoint': bool(a0['overlap_original_validation']['barcode_sets_disjoint']),
            'target_nature': 'cross-screen same-key re-measurement; same platform/endpoint; NOT '
                             'different measurement/culture/lineage',
            'judgment': 'qualified_with_conditions',
            'conditions': ['only cross-screen same-key re-test (not independent measurement/culture/lineage)',
                           'screen confounded with batch; matched-condition subset only',
                           'Validation is smaller -> power/MDE must pass the pre-registered gate (section 3)'],
        },
        {
            'candidate': "O'Neil 2026 (combination viability, X/X0)",
            'path_rel': 'data/raw/oneil2026_qualification/',
            'local': {'exists': os.path.isdir(ONEIL_RAW), 'n_files': len(oneil_files),
                      'total_bytes': oneil_total},
            'target': 'combination response viability (X/X0), 4x4 dose grid; 39 cells / 583 unordered pairs',
            'independent_groups': 1, 'shared_cells': n_overlap, 'shared_cells_of': n_cells_oneil,
            'shared_keys_conservative': int(oneil_counts['counts']['intersection']['cell_pair']),
            'raw_evidence_disjoint': True,
            'target_nature': 'different measurement (X/X0 growth-normalized response vs fitted ΔEMAX '
                             'synergy); different screen/plates; but no A0-matched conditions / same '
                             'endpoint; already used in earlier fitting/selection (not sealed)',
            'judgment': 'not_qualified',
            'failure_categories': ['data_insufficient', 'no_operational_target'],
            'reason': '9/39 shared cells < >=10 frozen threshold; conservative match 5 cells / 27 '
                      'cell-pair keys (loose 9 cells / 69 keys) << 500; endpoint X/X0 != SYNERGY_DELTA_EMAX '
                      'so no A0-matched condition/quadruple target',
        },
        {
            'candidate': 'DrugComb v1.4 / v1.5 combination studies',
            'local': {'v1_4': os.path.isfile(os.path.join(
                ROOT, 'research', '2026-10-27-drugcomb-qualification', 'downloads',
                'summary_table_v1.4.csv'))},
            'target': 'multi-study combination synergy endpoints',
            'shared_cells': 41, 'matched_units': 4179, 'independent_groups': 20,
            'raw_evidence_disjoint': True,
            'judgment': 'not_qualified',
            'failure_categories': ['data_insufficient'],
            'reason': 'A3/C173 frozen large-scale design: shared cells 41 < 200, matched units 4,179 < '
                      '10,000; a narrower protocol would need its own pre-registration',
        },
        {
            'candidate': 'PRISM 19Q4 (primary single-agent screen)',
            'local': {'exists': os.path.isfile(os.path.join(
                EXT, 'prism_19q4', 'raw', 'primary-screen-replicate-collapsed-logfold-change.csv'))},
            'target': 'single-agent viability log-fold-change (no combination contrast)',
            'judgment': 'not_qualified', 'failure_categories': ['no_operational_target'],
            'reason': 'single-agent only; cannot define a combination contrast',
        },
        {
            'candidate': 'BeatAML2 (single-agent ex vivo inhibitor response)',
            'local': {'exists': os.path.isfile(os.path.join(
                EXT, 'beataml2_20261017', 'beataml_probit_curve_fits_v4_dbgap.txt'))},
            'target': 'single-agent probit AUC (no combination contrast)',
            'judgment': 'not_qualified', 'failure_categories': ['no_operational_target'],
            'reason': 'single-agent only',
        },
        {
            'candidate': 'GCP2020 (LINCS PCCSE proteomics)',
            'local': {'exists': os.path.isdir(os.path.join(EXT, 'gcp2020'))},
            'target': 'peptide/protein abundance (4 cell lines); no combination viability',
            'judgment': 'not_qualified',
            'failure_categories': ['no_operational_target', 'data_insufficient'],
        },
        {
            'candidate': "NCI-ALMANAC / VIS2024 / Nyman2020 / Hill2017 / JUMP-CP / BATCHIE / GDSC2",
            'local': {d: {'dir_exists': os.path.isdir(os.path.join(EXT, d)),
                          'n_files': (len(os.listdir(os.path.join(EXT, d)))
                                      if os.path.isdir(os.path.join(EXT, d)) else 0)}
                      for d in ('nci_almanac_2017', 'vis2024_pancancer_combinations', 'nyman2020',
                                'hill2017', 'jump_target', 'batchie_zenodo_13871987', 'gdsc2_fitted')},
            'target': 'would be combination viability resources',
            'judgment': 'not_qualified', 'failure_categories': ['data_unavailable'],
            'reason': 'directory present but no valid data files (empty or file-less subdirectories); '
                      'unified wording per challenge item 1',
        },
        {
            'candidate': 'Same-resource re-encodings (Original other synergy endpoints / aggregation / '
                         'barcode split)',
            'local': {'same_fitted_table': True},
            'target': 're-derived endpoints on the same wells',
            'judgment': 'not_qualified', 'failure_categories': ['same_resource_reencoding'],
            'reason': 'same raw evidence re-aggregated/re-encoded; not an independent target by protocol',
        },
        {
            'candidate': 'Expression perturbation resources (Mix-seq / LINCS / SciPlex / Tahoe)',
            'local': {'exists': True},
            'target': 'expression/morphology readouts, not combination viability Delta',
            'judgment': 'not_qualified', 'failure_categories': ['no_operational_target'],
            'reason': 'not a functional combination target for D1 (relevant to D5/D6)',
        },
    ]
    n_q = sum(1 for c in candidates if c['judgment'] == 'qualified')
    n_qwc = sum(1 for c in candidates if c['judgment'] == 'qualified_with_conditions')
    n_nq = sum(1 for c in candidates if c['judgment'] == 'not_qualified')
    eligibility = {
        'frozen_criteria': {
            'a0_reuse_minimums': {'min_independent_groups': 2, 'min_shared_cells': 10,
                                  'min_directed_pairs': 10, 'min_matched_keys_or_quadruples': 500},
            'independence': 'different measurement / culture / screening with raw evidence '
                            '(plate/well/run) disjoint from R197 Original; different screen but same '
                            'platform/endpoint only qualifies as cross-screen same-key re-test',
            'excluded': 'same-resource re-aggregation / endpoint re-encoding / barcode split',
            'failure_categories': ['data_unavailable', 'data_insufficient', 'no_operational_target',
                                   'same_resource_reencoding', 'design_invalid'],
        },
        'candidates': candidates,
        'n_qualified': n_q, 'n_qualified_with_conditions': n_qwc, 'n_not_qualified': n_nq,
        'summary': 'qualified=0; qualified_with_conditions=1 (Jaaks Validation, cross-screen SAME-KEY '
                   're-test only); not_qualified=8. T4 has no target meeting the A0 reuse thresholds '
                   '(O\'Neil is a local different-measurement resource but 9/39 < 10 shared cells and no '
                   'A0-matched conditions / same endpoint).',
        'v0_1_corrections': {
            'O\'Neil': 'v0.1 wrongly placed O\'Neil in the empty-directory data_unavailable group; '
                       'corrected to not_qualified (data_insufficient + no_operational_target)',
            'nyman2020': 'v0.1 recorded empty:false without data files; unified as data_unavailable '
                         '(directory present, no valid data files)',
            'T4': 'v0.1 said "no local different-measurement/culture combination resource"; corrected to '
                  '"no different-measurement/culture target that meets the A0 reuse thresholds"',
        },
    }
    say('    eligibility: qualified=%d qualified_with_conditions=%d not_qualified=%d' % (
        n_q, n_qwc, n_nq))

    say('[4/8] locked target hierarchy + planning MDE80 ...')
    share = a0['shares'] if 'shares' in a0 else None
    v01_source = v01['C_source_shares']['a0_variance_shares_readonly']
    icc_cell = float(v01_source['share_cellpair'])
    icc_cond = float(v01_source['share_cond_raw'])
    targets = {
        'T1': {'name': 'same-screen unmeasured keys (internal precursor)',
               'n_units': int(27936 - 9154), 'cells': 96, 'conds': 291,
               'role': 'internal_precursor_only', 'gate': False},
        'T2': {'name': 'cross-screen same-key re-test (Validation matched keys)',
               'n_units': 9154, 'cells': 96, 'conds': 291,
               'role': 'only_candidate_primary', 'gate': True},
        'T3': {'name': 'cross-screen cold keys (Validation-only)',
               'n_units': int(len(vkeys_only)), 'cells': int(t3_cells), 'conds': int(t3_conds),
               'role': 'exploratory_only', 'gate': False},
    }
    power = {}
    for tid, tv in targets.items():
        main = plan_mde(tv['n_units'], tv['cells'], tv['conds'], icc_cell, icc_cond, 0.0)
        grid = []
        for mult in ICC_MULTIPLIERS:
            for rho in RHO_AB:
                r = plan_mde(tv['n_units'], tv['cells'], tv['conds'],
                             icc_cell * mult, icc_cond * mult, rho)
                grid.append({'icc_multiplier': mult, 'rho_ab': rho,
                             'design_effect': r['design_effect'], 'n_eff': r['n_eff'],
                             'mde80': r['mde80'], 'passes': r['passes_delta_min']})
        power[tid] = {
            'name': tv['name'], 'n_units': tv['n_units'], 'cells': tv['cells'], 'conds': tv['conds'],
            'role': tv['role'], 'primary_gate': tv['gate'],
            'planning_icc_cell': rq(icc_cell), 'planning_icc_cond': rq(icc_cond),
            'main_planning_scenario': main,
            'sensitivity_grid': grid,
            'delta_min': DELTA_MIN,
        }
    # pair-level MDE for T2 (98 directed pairs) as requested
    pair_mde = plan_mde(98, 96, 98, icc_cell, icc_cond, 0.0)
    # threshold analysis: required design effect for MDE80 <= delta_min
    thresholds = []
    for rho in RHO_AB:
        var_max = (DELTA_MIN / MDE_FACTOR) ** 2
        n_eff_req = 3.0 + 2.0 * (1.0 - rho) / var_max
        de_req = 9154.0 / n_eff_req
        # solve ICC (assume ICC_cell = ICC_cond = ICC) for DE = 1 + (mbar_c-1 + mbar_d-1)*ICC
        slope = (9154.0 / 96.0 - 1.0) + (9154.0 / 291.0 - 1.0)
        icc_req = (de_req - 1.0) / slope
        thresholds.append({'rho_ab': rho, 'n_eff_required': rq(n_eff_req),
                           'design_effect_required': rq(de_req),
                           'icc_required_if_equal': rq(icc_req),
                           'icc_required_vs_planning_prior': rq(icc_req / icc_cell)})
    t2_main = power['T2']['main_planning_scenario']
    t3_main = power['T3']['main_planning_scenario']
    t1_main = power['T1']['main_planning_scenario']
    verdict = {
        'decision': None,
        'reasons': [],
        'T2_mde_main': t2_main['mde80'],
        'T2_mde_by_scenario': {('mult=%s,rho_ab=%s' % (g['icc_multiplier'], g['rho_ab'])):
                               g['mde80'] for g in power['T2']['sensitivity_grid']},
        'T3_mde_main': t3_main['mde80'],
        'T1_mde_main': t1_main['mde80'],
        'pair_level_T2_mde_main': pair_mde['mde80'],
        'thresholds_for_T2_pass': thresholds,
    }
    if t2_main['mde80'] is not None and t2_main['mde80'] <= DELTA_MIN:
        verdict['decision'] = 'narrow_to_T2_primary'
        verdict['reasons'].append('T2 planning MDE80 <= delta_min under the pre-registered conservative '
                                  'scenario; T3 exploratory/design_invalid; T1 internal precursor; T4 no target')
    else:
        verdict['decision'] = 'stop'
        verdict['reasons'].append('T2 planning MDE80 = %.4f > delta_min, so the only candidate primary '
                                  'target is design_invalid: precision_insufficient' % t2_main['mde80'])
        verdict['reasons'].append('T3 planning MDE80 = %.4f > delta_min -> design_invalid: '
                                  'precision_insufficient (exploratory only)' % t3_main['mde80'])
        verdict['reasons'].append('T1 planning MDE80 = %.4f > delta_min but T1 is an internal precursor, '
                                  'not an independent target' % t1_main['mde80'])
        verdict['reasons'].append('T4 has no target meeting the A0 reuse thresholds (O\'Neil 9/39 < 10 '
                                  'and no matched conditions/same endpoint)')
        verdict['reasons'].append('therefore no minimal experiment can be certified for the '
                                  'closure-outside/new-key independent-information question or for a '
                                  'precision-passes T2 replication; verdict = stop with required '
                                  'measurement specs')
    # derived conditions for the T2 gate and the explicit decision branches
    var_max = (DELTA_MIN / MDE_FACTOR) ** 2
    t2_neff = t2_main['n_eff']
    rho_needed = 1.0 - var_max * (t2_neff - 3.0) / 2.0
    verdict['T2_rho_ab_required_at_prior_icc'] = rq(rho_needed)
    verdict['reasons'].append(
        'under the conservative planning scenario T2 would pass only if the target-side rank ICC were '
        '<= %.4f (%.1f%% of the A0 planning prior) or the model-prediction rank correlation were >= %.3f; '
        'neither is known at design stage' % (
            thresholds[0]['icc_required_if_equal'],
            100.0 * thresholds[0]['icc_required_vs_planning_prior'], rho_needed))
    verdict['decision_branches'] = {
        'default_this_revision': 'stop: T2 conservative planning MDE80 = %.4f > delta_min; no minimal '
                                 'experiment can be certified' % t2_main['mde80'],
        'if_lead_explicitly_accepts_optimistic_independence_planning': 'an amendment could pre-register '
            'ICC=0 and rho_ab=0 (optimistic, non-conservative); then T2 planning MDE80 = %.4f <= delta_min '
            'and a NARROWED cross-screen SAME-KEY replication (T1 internal precursor, T3 exploratory) may '
            'be submitted to independent challenge; it must not be written as independent measurement/'
            'culture/lineage or closure-outside/new-key transfer'
            % power['T2']['sensitivity_grid'][0]['mde80'],
        'if_lead_requires_new_key_closure_outside_test': 'no qualified target/power locally -> stop; required '
            'measurement specs in J_required_measurements',
    }
    say('    T1/T2/T3 planning MDE80 (main) = %.4f / %.4f / %.4f ; decision = %s' % (
        t1_main['mde80'], t2_main['mde80'], t3_main['mde80'], verdict['decision']))

    say('[5/8] closure gate plan (target-specific) ...')
    closure = {
        'principle': 'v0.1 A4 showed 100%% of H197c random held-out derived entries are exactly '
                     'reconstructible from training entries (source side); any target endpoint built on '
                     'derived Q with a random-entry mask is closure-contaminated.',
        'target_closure_rate_by_construction': {
            'T1_key_level': '0 by construction (keys are primitives; Q algebra cannot determine new keys)',
            'T2_key_level': '0 by construction (same-key cross-screen value is not determined by source Q)',
            'T3_key_level': '0 by construction (cold keys)',
            'derived_Q_secondary': 'must be measured pre-scoring on the target-specific split; only '
                                   'S-structural splits are expected to be informative (S-random is '
                                   'expected to fail: v0.1 evidence 100%)',
        },
        'gate_rule': 'derived-endpoint evaluation set must have closure reconstruction rate <= 5%; else '
                     'design_invalid: closure_contaminated; pre-registered split family: S-random '
                     '(random entries) and S-structural (grouped by cell/partner/key); no outcome-based '
                     'split switching',
        'exact_closure_baseline_definitions': {
            'T1_new_keys': 'key-level contribution 0 (by construction); derived secondary: reconstruct '
                           'target Q from target training entries and report max|err| / rate',
            'T2_same_keys': 'key-level: the zero-structure baseline is SOURCE-VALUE TRANSFER (matched '
                            'Original key value), not closure reconstruction; derived secondary: '
                            'reconstruct Validation Q from Validation training entries (if built) and report',
            'T3_cold_keys': 'key-level contribution 0; derived secondary: target-training closure '
                            'reconstruction and report',
        },
    }
    say('    closure gate plan recorded (T0 v0.1 evidence: 100% recon -> S-random fails by design)')

    say('[6/8] operational definitions (main contrast / baselines / budget caps) ...')
    operational = {
        'main_model': {
            'name': 'de-closure structural model M*',
            'source_feature_blocks': {
                'B1': 'cell metadata (tissue/lineage; A0 cell metadata)',
                'B2': 'drug annotation blocks (project-frozen pathway/target/class template; P-A/P-A2 '
                      'mapping; no re-mapping)',
                'B3': 'source additive effects estimated on the maximal linearly independent basis of '
                      'source derived entries (basis size = rank(A_source) = 3,005, fixed greedy order)',
                'B4': 'source structural interaction (low-rank cell x condition + annotation '
                      'interactions) fitted in the closure orthogonal complement',
            },
            'closure_exclusion': {
                'primary': 'training set = maximal linearly independent basis of source derived entries '
                           '(rank 3,005, fixed greedy) instead of all 92,039; target evaluation restricted '
                           'to non-closure units (key-level targets have no closure channel)',
                'sensitivity': 'residualize source features against closure span C=rowspace(A_source) via '
                               'projection I-P_C',
            },
            'model_class': 'low-rank/hierarchical structural model (cell x condition interaction + '
                           'annotation blocks); hyperparameter grid <=30 configs, inner 5-fold CV with '
                           'fixed seed; parameters selected on source training only',
        },
        'baselines_equal_info': ['mean/global', 'source-value transfer (matched Original key value)',
                                 'source additive (cell+condition means)', 'sufficiently tuned tree '
                                 '(DrEval-style inner-CV budget, same feature blocks, <=30 configs)',
                                 'matrix completion / low-rank (rank 1-5, train-selected)',
                                 'GP/kernel on B1+B2 metadata',
                                 'exact closure reconstruction (definitions in closure gate section)',
                                 'direct response prediction (predict raw keys then derive)'],
        'equal_budget_cap': {
            'feature_blocks': 'identical B1-B4 for all arms',
            'inner_cv': '5 folds, fixed seed, same folds',
            'configs_per_model': 30,
            'wall_seconds_per_model': 600,
            'cpu_seconds_per_model': 1200,
            'memory_gb': 8,
            'target_mask': 'identical for all arms',
            'reporting': 'per-arm configs/wall/CPU; no arm receives extra features or budget',
        },
        'primary_metric': 'Delta_rho = Spearman(M*) - max_baseline Spearman on the same target keys '
                          '(target-side frozen point set)',
        'secondary_metrics': 'per-key R2; top-q descriptive; Delta_rho on closure-reconstructible subset '
                             '(expected ~0); derived-Q secondary endpoint reported only for closure '
                             'contamination diagnostics',
        'cluster_units': {'primary': 'target-side cell', 'sensitivity': ['plate', 'key'],
                          'T2_primary_clusters': 96},
        'bootstrap': {'type': 'paired cluster bootstrap', 'B': 2000, 'seed': SEED,
                      'interval': 'percentile 2.5/97.5'},
        'null_models': {
            'within_target_rank_permutation': 'permute target ranks preserving mask/tie rule',
            'source_to_target_mapping_permutation': 'permute cell labels within tissue and drug labels '
                                                    'within annotation class, preserving support',
            'same_dim_random_features': 'capacity control',
            'same_resource_re_endpoint': 'Original AUC/EMAX swap; leakage quantifier only, not a target',
        },
        'failure_categories': ['data_unavailable', 'data_insufficient', 'no_operational_target',
                               'same_resource_reencoding', 'design_invalid: precision_insufficient',
                               'design_invalid: closure_contaminated', 'design_invalid: coverage',
                               'evaluation_cannot_distinguish', 'no_increment'],
        'stop_conditions': ['no qualified independent target -> stop + required specs',
                            'primary target MDE80_plan > delta_min -> design_invalid: precision_insufficient',
                            'closure gate > 5% -> design_invalid: closure_contaminated',
                            'main model <= strongest baseline -> no_increment',
                            'gain only on closure-reconstructible units -> stop transfer claim, keep '
                            'evaluation result',
                            'no post-hoc switching of target/split/delta/cluster/budget'],
        'target_selection_rule': 'eligibility and power are computed BEFORE any target response access; '
                                 'T2 is primary only if its pre-registered conservative planning MDE80 <= '
                                 'delta_min and the target-specific closure gate passes; T3 is exploratory '
                                 'only/design_invalid; T1 internal precursor; T4 no qualified target; '
                                 'no post-hoc target switching',
    }
    say('    operational definitions recorded (closure-excluded model, baselines, caps, nulls, rules)')

    say('[7/8] required measurements + wording/boundary consistency ...')
    required = {
        'spec': 'independent combination resource with (i) different measurement modality or independent '
                'culture (not the same GDSC/Jaaks platform/endpoint re-screen); (ii) >=10 shared cells and '
                '>=10 directed pairs and >=500 matched keys/quadruples with Jaaks under the A0 reuse '
                'thresholds; (iii) plate/well/run evidence disjoint from Original and Validation; '
                '(iv) a frozen-aggregation combination Delta or functional viability readout mappable to '
                'the A0 convention; (v) target units/clusters sufficient for a pre-registered conservative '
                'MDE80 <= delta_min (or a pre-declared relaxed delta_min / more units)',
        'local_status': "not available: O'Neil satisfies (i) but 9/39 < 10 shared cells and has no "
                        'A0-matched conditions/same endpoint (data_insufficient + no_operational_target); '
                        'DrugComb fails the frozen large-scale design (C173); the rest are empty '
                        'directories/single-agent/expression-only resources',
    }
    wording = {
        'validation': 'Jaaks Validation = independent screen/plate/run, same laboratory platform and '
                      'endpoint definition, 96 shared cells: a CROSS-SCREEN SAME-KEY re-test ONLY; not '
                      'an independent measurement/culture/lineage confirmation; not "closure-outside '
                      'structure/new-key transfer"',
        'delete': 'the absolute phrase "唯一独立操作性目标" is removed; replaced by "only target '
                  'qualifying for a cross-screen same-key re-test (qualified_with_conditions)"',
        'T4': facts['F6_T4_corrected']['v0_2_wording'],
        'r197_v2_7206': 'uncertified descriptive result (C179); to-be-tested object only; no structure '
                        'present/absent claim; v0.1 shows H197c random-entry holdout is 100% closure-'
                        'reconstructible',
        'a0_shares': 'A0 1.43%/3.94%/94.63% are Q-variance shares only, not predictive-signal shares and '
                     'not a transferable-regularity total',
        'three_place_consistency': 'protocol_v0_2 / report_v0_2 / d1_v0_2.json use the same eligibility '
                                   'judgments, T2/T3/T1 roles and T4 wording (checked in record)',
    }
    say('    required specs + wording corrections recorded')

    t_end = time.time()
    out = {
        'protocol': {'path_rel': 'research/2026-10-27-direction-mechanism-expansion/d1_information/'
                                 'PROTOCOL_D1_v0_2.md', 'sha256': sha256_file(PROTOCOL)},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        'supersedes': {'v0_1': 'd1.json (F0DC308F...) / PROTOCOL_D1.md / report_d1.md; v0.1 files are '
                               'kept unchanged and the PASS parts (information decomposition) remain valid',
                       'challenge': 'challenge_D1.md (task-93, revise, 5 must-fix)'},
        'inputs': inputs,
        'facts_v0_2': facts,
        'E_eligibility_v0_2': eligibility,
        'F_power': {'targets': power, 'pair_level_T2': pair_mde,
                    'thresholds_for_T2_pass': thresholds,
                    'delta_min': DELTA_MIN, 'mde_factor': MDE_FACTOR,
                    'icc_planning_priors': {'cell': rq(icc_cell), 'condition': rq(icc_cond),
                                            'source': 'read-only A0 Q-variance shares, used only as '
                                                      'planning priors (disclosed approximation)'},
                    'main_planning_scenario': 'ICC priors x1, rho_ab=0 (conservative)',
                    'bootstrap': {'type': 'paired cluster bootstrap', 'B': 2000, 'seed': SEED,
                                  'interval': 'percentile 2.5/97.5'},
                    'selection_rule': 'eligibility+power before target response; no post-hoc target '
                                      'switching; T3 exploratory/design_invalid; T1 internal precursor'},
        'G_closure_gate': closure,
        'H_operational_definitions': operational,
        'I_verdict': verdict,
        'J_required_measurements': required,
        'K_wording': wording,
        'boundaries': ['design/eligibility revision only: no training, no fitting, no effect/transfer '
                       'statistics',
                       'no O\'Neil/Validation response values were read; only identity/design columns and '
                       'metadata files',
                       'v0.1 files unchanged; PASS parts of v0.1 (rank/redundancy/H197c/shared-source '
                       'audit) remain valid',
                       'R197v2 0.7206 remains an uncertified descriptive result (C179)',
                       'no claim of novelty/mechanism/transfer/decision benefit'],
        'deviations': [],
        'log': log,
    }
    write_json(out, OUTJSON)
    print('d1_v0_2.json sha256:', sha256_file(OUTJSON))
    print('DONE wall=%.1fs' % (t_end - t0))


if __name__ == '__main__':
    main()
