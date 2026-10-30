"""Compare frozen float metadata join against exact original-decimal dose equality."""
import csv
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def records(p, delimiter=','):
    with (gzip.open if p.suffix == '.gz' else open)(p, 'rt', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=delimiter))
def norm(s):
    return re.sub('[^A-Z0-9]', '', str(s).upper())
def core(s):
    m = re.match(r'BRD-[AK]\d{8}', s)
    return m[0] if m else None
def dose(raw):
    m = re.fullmatch(r'([0-9.eE+-]+)\s+(.+)', raw)
    if not m:
        return None
    unit = m[2].lower().replace('µ', 'u').replace('μ', 'u')
    if unit not in ('um', 'nm'):
        return None
    return Decimal(m[1]) / (1000 if unit == 'nm' else 1)
def canonical(v):
    return str(v.normalize())
def summary(keys):
    return {'keys': len(keys), 'drugs': len({k[0] for k in keys}), 'cells': len({k[1] for k in keys})}

protected_names = ['audit_metadata.py', 'metadata_counts.json', 'program_data_audit.md']
before = {p: sha(OUT/p) for p in protected_names}
frozen = json.loads((OUT/'metadata_counts.json').read_text(encoding='utf-8'))
parent = json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
base = ROOT/'data/external/prism_19q4/raw'
tr_path = base/'secondary-screen-replicate-collapsed-treatment-info.csv'
tr_raw = records(tr_path)
tr = pd.read_csv(tr_path, low_memory=False)
tr['core'] = tr.broad_id.map(core)
tr['dose_um'] = pd.to_numeric(tr.dose, errors='coerce')
tr['raw_dose'] = [r['dose'] for r in tr_raw]
actions = defaultdict(set)
action_sources = defaultdict(list)
for i, r in enumerate(tr_raw):
    key = (core(r['broad_id']), Decimal(r['dose']))
    actions[key].add(r['screen_id'])
    action_sources[(key[0], key[1], r['screen_id'])].append(i)
ce = pd.read_csv(base/'secondary-screen-cell-line-info.csv')
valid = {norm(s.split('_')[0]) for s in ce[ce.passed_str_profiling.astype(str).str.lower().eq('true')].ccle_name}
pool = pd.read_csv(base/'secondary-screen-pooling-info.csv')
pool['cell'] = pool.ccle_name.astype(str).str.split('_').str[0].map(norm)
pool = pool[pool.passed_str_profiling.astype(str).str.lower().eq('true')][['cell','screen_id']].drop_duplicates()
available = {(r.cell, r.screen_id) for r in pool.itertuples()}
result = {'preserved_artifacts_before': before, 'inputs_sha256': {}, 'phases': {}}
original_namespace = {'__file__':str(OUT/'audit_metadata.py'), '__name__':'metadata_readonly_replay'}
original_prefix = (OUT/'audit_metadata.py').read_text(encoding='utf-8').split("prov = table(",1)[0]
exec(compile(original_prefix, str(OUT/'audit_metadata.py'), 'exec'), original_namespace)
for phase, rel in [('GSE92742','lincs_l1000_gse92742/GSE92742_Broad_LINCS_sig_info.txt.gz'),
                   ('GSE70138','lincs_l1000_phase2/meta/GSE70138_Broad_LINCS_sig_info_2017-03-06.txt.gz')]:
    path = ROOT/'data/external'/rel
    result['inputs_sha256'][path.relative_to(ROOT).as_posix()] = sha(path)
    raw = records(path, '\t')
    df = pd.read_csv(path, sep='\t', low_memory=False)
    df = df[df.pert_type.eq('trt_cp')].copy()
    parts = df.pert_idose.astype(str).str.extract(r'^([0-9.eE+-]+)\s+(.+)$')
    unit = parts[1].str.replace('µ','u').str.replace('μ','u').str.lower()
    df['dose_um'] = pd.to_numeric(parts[0], errors='coerce') * unit.map({'um':1.0,'nm':0.001})
    df['core'] = df.pert_id.map(core)
    df['cell'] = df.cell_id.map(norm)
    df['dose_dec'] = df.pert_idose.map(dose).map(lambda d: canonical(d) if d is not None else None)
    x = df[['core','cell','dose_um','pert_itime','dose_dec']].drop_duplicates(['core','cell','dose_um','pert_itime'])
    x = x[x.cell.isin(valid)]
    matched = x.merge(tr[['core','dose_um','screen_id']].drop_duplicates(), on=['core','dose_um']).drop_duplicates()
    matched = matched.merge(pool, on=['cell','screen_id'])
    od = original_namespace['lincs'][phase]
    different = od.dose_um.ne(df.dose_um) & ~(od.dose_um.isna() & df.dose_um.isna())
    otr = original_namespace['tr']
    common = sorted(set(df.core.dropna()) & set(tr.core.dropna()))
    cc = sorted(set(df.cell) & valid)
    bx = df[['core','cell','dose_um','pert_itime']].drop_duplicates()
    bx = bx[bx.cell.isin(cc) & bx.core.isin(common)]
    bm = bx.merge(tr[['core','dose_um','screen_id']].drop_duplicates(),on=['core','dose_um'],how='inner').drop_duplicates().merge(pool,on=['cell','screen_id'],how='inner')
    dose_lookup = {(r.core,r.cell,r.dose_um,r.pert_itime):r.dose_dec for r in x.itertuples()}
    floats = {(r.core,r.cell,dose_lookup[(r.core,r.cell,r.dose_um,r.pert_itime)],r.pert_itime,r.screen_id) for r in bm.itertuples()}
    assert len(bm) == frozen['joins'][phase+'_to_secondary']['nominal_equal_um_drug_cell_RNA_time_PRISMscreen_keys']
    exact = set()
    source_rows = {}
    for idx, r in enumerate(raw):
        if r['pert_type'] != 'trt_cp' or norm(r['cell_id']) not in valid:
            continue
        d = dose(r['pert_idose'])
        if d is None:
            continue
        cid, cell = core(r['pert_id']), norm(r['cell_id'])
        for screen in actions.get((cid,d), []):
            if (cell,screen) in available:
                k = (cid,cell,canonical(d),r['pert_itime'],screen)
                exact.add(k)
                source_rows.setdefault(k, idx)
    missing, extra = exact-floats, floats-exact
    details = []
    for key in sorted(missing):
        idx = source_rows[key]
        r = raw[idx]
        m = re.fullmatch(r'([0-9.eE+-]+)\s+(.+)',r['pert_idose'])
        u = m[2].lower().replace('µ','u').replace('μ','u')
        converted_float = float(df.loc[idx,'dose_um'])
        for ti in action_sources[(key[0],Decimal(key[2]),key[4])]:
            trr = tr_raw[ti]
            prism_float = float(tr.loc[ti,'dose_um'])
            builtin_raw_float = float(trr['dose'])
            builtin_lincs_float = float(m[1]) * (0.001 if u == 'nm' else 1.0)
            cause = ['invalid_core_None_equal_None'] if key[0] is None else []
            if float(m[1]) != float(pd.to_numeric(pd.Series([m[1]]), errors='coerce').iloc[0]):
                cause.append('LINCS_pd_to_numeric_parser')
            if prism_float != builtin_raw_float:
                cause.append('PRISM_read_csv_float_parser')
            if builtin_lincs_float != builtin_raw_float:
                cause.append('binary_unit_multiplication_or_float_conversion')
            details.append({'key': list(key), 'LINCS_sig_id': r['sig_id'], 'LINCS_pert_id':r['pert_id'],
                'LINCS_pert_idose_raw':r['pert_idose'], 'LINCS_float_repr':repr(converted_float),
                'LINCS_float_hex':converted_float.hex(), 'LINCS_builtin_conversion_repr':repr(builtin_lincs_float),
                'PRISM_broad_id':trr['broad_id'], 'PRISM_column_name':trr['column_name'],
                'PRISM_dose_raw':trr['dose'], 'PRISM_float_repr':repr(prism_float),
                'PRISM_float_hex':prism_float.hex(), 'PRISM_builtin_float_repr':repr(builtin_raw_float),
                'decimal_equal':dose(r['pert_idose']) == Decimal(trr['dose']), 'cause_flags':cause})
    valid_exact = {k for k in exact if k[0] is not None}
    result['phases'][phase] = {'frozen_float_recomputed':summary(floats), 'parent_null_permitting_decimal_recomputed':summary(exact),
        'matches_parent_decimal':summary(exact) == parent['independent_decimal_join'][phase],
        'corrected_nonnull_decimal_recomputed':summary(valid_exact),
        'corrected_decimal_keys_equal_original_float_keys':valid_exact == floats,
        'null_permitting_float_count':len(matched),
        'original_prefix_count':original_namespace['result']['joins'][phase+'_to_secondary']['nominal_equal_um_drug_cell_RNA_time_PRISMscreen_keys'],
        'all_missing_keys_have_null_core':all(k[0] is None for k in missing),
        'LINCS_float_values_equal_original':not bool(different.any()),
        'PRISM_float_values_equal_original':not bool(otr.dose_um.ne(tr.dose_um).any()),
        'missing_keys_count':len(missing), 'extra_keys_count':len(extra),
        'missing_by_LINCS_unit':dict(Counter(re.fullmatch(r'([0-9.eE+-]+)\s+(.+)',raw[source_rows[k]]['pert_idose'])[2] for k in missing)),
        'cause_flags_over_missing_rows':dict(Counter(c for row in details for c in row['cause_flags'])),
        'missing_keys': [list(k) for k in sorted(missing)], 'extra_keys':[list(k) for k in sorted(extra)],
        'raw_examples_and_causes':details}
for p in [tr_path, base/'secondary-screen-cell-line-info.csv',base/'secondary-screen-pooling-info.csv']:
    result['inputs_sha256'][p.relative_to(ROOT).as_posix()] = sha(p)
result['inputs_match_frozen_hashes'] = all(v == frozen['inputs'][k]['sha256'] for k,v in result['inputs_sha256'].items())
result['preserved_artifacts_after'] = {p:sha(OUT/p) for p in protected_names}
result['protected_artifacts_unchanged'] = before == result['preserved_artifacts_after']
(OUT/'metadata_join_discrepancy.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
for phase, v in result['phases'].items():
    print(phase, json.dumps({k:v[k] for k in v if k not in ['missing_keys','extra_keys','raw_examples_and_causes']},ensure_ascii=False))
    seen = set()
    for row in v['raw_examples_and_causes']:
        group = (tuple(row['cause_flags']),row['LINCS_pert_idose_raw'],row['PRISM_dose_raw'])
        if group not in seen:
            print(json.dumps(row,ensure_ascii=False));seen.add(group)
        if len(seen)>=5:
            break
print('protected_artifacts_unchanged',result['protected_artifacts_unchanged'])
