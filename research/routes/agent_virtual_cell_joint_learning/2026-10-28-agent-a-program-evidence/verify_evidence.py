"""Coordinator recomputation; original outcomes and protocols remain untouched."""
import ast
import csv
import gzip
import hashlib
import json
import re
import sys
import time
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import numpy as np
from pypdf import PdfReader

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def records(path, delimiter=','):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8-sig', newline='') as stream:
        yield from csv.DictReader(stream, delimiter=delimiter)


def norm(value):
    return re.sub('[^A-Z0-9]', '', value.upper())


def core(value):
    found = re.match(r'BRD-[AK]\d{8}', value)
    return found.group() if found else None


def nominal_joins():
    base = ROOT / 'data/external/prism_19q4/raw'
    valid_cells = {norm(x['ccle_name'].split('_')[0]) for x in records(base / 'secondary-screen-cell-line-info.csv')
                   if x['passed_str_profiling'].lower() == 'true'}
    available = defaultdict(set)
    for row in records(base / 'secondary-screen-pooling-info.csv'):
        if row['passed_str_profiling'].lower() == 'true':
            available[row['screen_id']].add(norm(row['ccle_name'].split('_')[0]))
    actions = defaultdict(set)
    for row in records(base / 'secondary-screen-replicate-collapsed-treatment-info.csv'):
        cid = core(row['broad_id'])
        if cid is not None:
            actions[(cid, Decimal(row['dose']))].add(row['screen_id'])
    result = {}
    phases = [
        ('GSE92742', 'lincs_l1000_gse92742/GSE92742_Broad_LINCS_sig_info.txt.gz'),
        ('GSE70138', 'lincs_l1000_phase2/meta/GSE70138_Broad_LINCS_sig_info_2017-03-06.txt.gz'),
    ]
    for phase, rel in phases:
        keys = set()
        for row in records(ROOT / 'data/external' / rel, '\t'):
            if row['pert_type'] != 'trt_cp':
                continue
            cell = norm(row['cell_id'])
            if cell not in valid_cells:
                continue
            match = re.fullmatch(r'([0-9.eE+-]+)\s+(.+)', row['pert_idose'])
            if not match:
                continue
            unit = match[2].lower().replace('µ', 'u').replace('μ', 'u')
            if unit not in ('um', 'nm'):
                continue
            dose = Decimal(match[1]) / (1000 if unit == 'nm' else 1)
            cid = core(row['pert_id'])
            if cid is None:
                continue
            for screen in actions.get((cid, dose), []):
                if cell in available[screen]:
                    keys.add((cid, cell, str(dose.normalize()), row['pert_itime'], screen))
        result[phase] = {'keys': len(keys), 'drugs': len({k[0] for k in keys}),
                         'cells': len({k[1] for k in keys})}
    return result


def main():
    start = time.perf_counter()
    if '--repair-join-only' in sys.argv:
        result = json.loads((OUT / 'verification.json').read_text(encoding='utf-8'))
        result['correction'] = 'v0 allowed unmatched compound IDs to join through None; invalid IDs now excluded. Original v0 retained. Exact diagnostic not rerun.'
        result['independent_decimal_join'] = nominal_joins()
        meta = json.loads((OUT / 'metadata_counts.json').read_text(encoding='utf-8'))
        result['join_matches_agent_count'] = all(result['independent_decimal_join'][phase]['keys'] ==
            meta['joins'][phase + '_to_secondary']['nominal_equal_um_drug_cell_RNA_time_PRISMscreen_keys']
            for phase in ('GSE92742', 'GSE70138'))
        result['join_repair_wall_seconds'] = time.perf_counter() - start
        (OUT / 'verification_v1.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({k: result[k] for k in ('correction', 'independent_decimal_join', 'join_matches_agent_count', 'join_repair_wall_seconds')}, ensure_ascii=False))
        return
    result = {'scope': 'saved numerical diagnostics, exact counterexample and metadata only; no biological effect experiment'}
    m1path = ROOT / 'research/2026-10-28-m1-stage2-run/m1_stage2.json'
    m1 = json.loads(m1path.read_text(encoding='utf-8'))
    result['M1'] = {'sha256': sha(m1path),
        'H1_pass_recomputed': sum(x['TV_256bin'] <= x['tolerance'] for x in m1['H1']),
        'H1_count': len(m1['H1']), 'H2_converged': sum(x['converged'] for x in m1['H2']),
        'H2_max_marginal_error': max(x['max_marginal_error'] for x in m1['H2']),
        'H3_pass_recomputed': m1['H3']['TV_candidate_oracle'] <= m1['H3']['tolerance'],
        'H3_TV': m1['H3']['TV_candidate_oracle']}
    # Execute only the inspected histogram function; do not import/run M1 training.
    source = ROOT / 'research/2026-10-28-m1-stage2-run/run_m1_stage2.py'
    tree = ast.parse(source.read_text(encoding='utf-8-sig'))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'hist_tv')
    namespace = {'np': np, 'Y_BOX': 2.0, 'Y_DIM': 4}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
    truth = np.array([[1., .25, .25, .25], [-1., .25, .25, .25],
                      [-1., .25, .25, .25], [1., .25, .25, .25]])
    swapped = truth.copy()
    swapped[:, 0] *= -1
    tv = namespace['hist_tv']
    choices = swapped[:, 0].reshape(2, 2).argmax(axis=1)
    utility = truth[:, 0].reshape(2, 2)
    result['exact_conditional_counterexample'] = {
        'H1_pooled_TV': tv(truth, swapped),
        'per_condition_TV': [tv(truth[i:i+1], swapped[i:i+1]) for i in range(4)],
        'toy_mean_simple_regret': float(np.mean(utility.max(axis=1) - utility[np.arange(2), choices])),
        'CI': None, 'CI_reason': 'complete deterministic construction, not sampled biological units',
        'does_not_show': 'does not measure conditional error of the actual fitted M1 model'}
    m3path = ROOT / 'research/2026-10-28-m3-stage2-run/m3_stage2.json'
    m3 = json.loads(m3path.read_text(encoding='utf-8'))
    env = m3['environment']
    p = np.array(env['p_h'])[:, None]
    b, mu, pi, m = (np.array(env[k]) for k in ('b', 'mu', 'pi_2', 'm_wrong'))
    var = mu * (1 - mu)
    weights = [p*pi**2*(var+(mu-m)**2)/b, np.ones_like(b), np.sqrt(var/b),
               p*pi*np.abs(mu-m)/b, b*(1-b), p*pi**2*var/b]
    expected = {a['id']: w/w.sum() for a, w in zip(m3['arms'], weights)}
    rows = m3['per_arm']
    result['M3'] = {'sha256': sha(m3path), 'records': len(rows),
        'weights_match_code_formula': all(np.allclose(x['allocation_weights'], expected[x['arm_id']]) for x in rows),
        'weights_sum_one': all(abs(np.array(x['allocation_weights']).sum()-1) < 1e-12 for x in rows),
        'frequency_sum_one': all(abs(np.array(x['realized_allocation_frequency']).sum()-1) < 1e-12 for x in rows),
        'allocations_each': sorted({x['equal_budget_audit']['n_alloc'] for x in rows}),
        'declared_decision_AL_rule': next(a['rule'] for a in m3['arms'] if a['id'] == 'S_decision_AL'),
        'executed_decision_AL_rule': 'p*pi*abs(mu-m)/b',
        'oracle_variance_used': True, 'fitted_GP_observed': False,
        'two_run_identity_not_independently_replayed': True}
    meta = json.loads((OUT / 'metadata_counts.json').read_text(encoding='utf-8'))
    result['metadata_inputs_hash_match'] = {rel: sha(ROOT / rel) == v['sha256'] for rel, v in meta['inputs'].items()}
    result['independent_decimal_join'] = nominal_joins()
    result['join_matches_agent_count'] = all(result['independent_decimal_join'][phase]['keys'] ==
        meta['joins'][phase + '_to_secondary']['nominal_equal_um_drug_cell_RNA_time_PRISMscreen_keys']
        for phase in ('GSE92742', 'GSE70138'))
    text = PdfReader(OUT / 'sources/subclones_supplement.pdf').pages[16].extract_text()
    scores = {name: float(value) for name, value in re.findall(r'^(P\d+_[A-Z]\d+)\s+([0-9.]+)\s*$', text, re.M)}
    result['reported_TableS3'] = {'source': 'subclones_supplement.pdf page17', 'scores': scores,
        'clones': len(scores), 'min': min(scores.values()), 'max': max(scores.values()),
        'interpretation': 'reported normalized clone means, not original independent replicate outcomes', 'biological_CI': None}
    result['wall_seconds'] = time.perf_counter()-start
    (OUT / 'verification_v1.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('metadata_inputs_hash_match', 'reported_TableS3')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
