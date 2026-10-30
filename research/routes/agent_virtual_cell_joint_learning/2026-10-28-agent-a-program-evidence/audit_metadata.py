"""Read open metadata only; no effects, expression matrices, sealed inputs, or network."""
from pathlib import Path
import hashlib
import json
import re
from collections import Counter
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
inputs = {}

def record(rel):
    p = ROOT / rel
    b = p.read_bytes()
    inputs[rel] = {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
    return p

def table(rel, sep=','):
    d = pd.read_csv(record(rel), sep=sep, low_memory=False)
    inputs[rel].update(rows=len(d), columns=list(d.columns))
    return d

def norm(x):
    return re.sub('[^A-Z0-9]', '', str(x).upper())

def counts(s):
    return {str(k): int(v) for k, v in s.value_counts(dropna=False).items()}

result = {'scope': 'metadata-only; candidate intersections, not observed effect coverage',
          'inputs': inputs, 'lincs': {}, 'prism': {}, 'sciplex': {}, 'joins': {}}
lincs = {}
for name, base, suff in [('GSE92742', 'data/external/lincs_l1000_gse92742', ''),
                         ('GSE70138', 'data/external/lincs_l1000_phase2/meta', '_2017-03-06')]:
    sig = table(f'{base}/{name}_Broad_LINCS_sig_info{suff}.txt.gz', '\t')
    pert = table(f'{base}/{name}_Broad_LINCS_pert_info{suff}.txt.gz', '\t')
    cell_suff = '_2017-04-28' if name == 'GSE70138' else ''
    table(f'{base}/{name}_Broad_LINCS_cell_info{cell_suff}.txt.gz', '\t')
    d = sig[sig.pert_type.eq('trt_cp')].copy()
    dose_parts = d.pert_idose.astype(str).str.extract(r'^([0-9.eE+-]+)\s+(.+)$')
    units = dose_parts[1].str.replace('µ', 'u').str.replace('μ', 'u').str.lower()
    multiplier = units.map({'um': 1.0, 'nm': 0.001})
    d['dose_um'] = pd.to_numeric(dose_parts[0], errors='coerce') * multiplier
    d['core'] = d.pert_id.astype(str).str.extract(r'^(BRD-[AK]\d{8})', expand=False)
    d['cell'] = d.cell_id.map(norm)
    lincs[name] = d
    result['lincs'][name] = {'all_signatures': len(sig), 'compound_signatures': len(d),
        'compound_ids': int(d.pert_id.nunique()), 'cells': sorted(d.cell_id.unique().tolist()),
        'RNA_time_tokens': counts(d.pert_itime), 'dose_tokens': counts(dose_parts[1]),
        'distil_id_not_independent_culture': True,
        'pert_schema': list(pert.columns), 'measured_proximal_action_columns': []}

for screen in ['primary', 'secondary']:
    base = 'data/external/prism_19q4/raw/'
    tr = table(base + screen + '-screen-replicate-collapsed-treatment-info.csv')
    ce = table(base + screen + '-screen-cell-line-info.csv')
    tr['core'] = tr.broad_id.str.extract(r'^(BRD-[AK]\d{8})', expand=False)
    tr['dose_um'] = pd.to_numeric(tr.dose, errors='coerce')
    ce['cell'] = ce.ccle_name.astype(str).str.split('_').str[0].map(norm)
    valid = ce[ce.passed_str_profiling.astype(str).str.lower().eq('true')]
    text = record(base + screen + '-screen-readme.txt').read_text(encoding='utf-8-sig')
    result['prism'][screen] = {'treatment_rows': len(tr), 'unique_broad_ids': int(tr.broad_id.nunique()),
        'unique_core_ids': int(tr.core.nunique()), 'cell_rows': len(ce), 'STR_pass_cell_rows': len(valid),
        'dose_values': sorted(tr.dose_um.dropna().unique().tolist()),
        'target_nonmissing_rows': int(tr.target.notna().sum()), 'measured_proximal_action_columns': [],
        'readme_relevant_lines': [f'{i}: {line}' for i, line in enumerate(text.splitlines(), 1)
            if re.search(r'dose -|detection_plate -|replicate-collapsed|collapsed across|hour|days', line, re.I)]}
    pool = None
    if screen == 'secondary':
        rp = table(base + 'secondary-screen-replicate-treatment-info.csv')
        pool = table(base + 'secondary-screen-pooling-info.csv')
        pool['cell'] = pool.ccle_name.astype(str).str.split('_').str[0].map(norm)
        result['prism'][screen]['plate_time_tokens'] = counts(rp.detection_plate.str.extract(r'(\d+H)', expand=False))
        result['prism'][screen]['plate_examples'] = rp.detection_plate.drop_duplicates().head(15).tolist()
        result['prism'][screen]['replicate_rows'] = len(rp)
        result['prism'][screen]['independent_culture_id_present'] = False
    for phase, ld in lincs.items():
        common = sorted(set(ld.core.dropna()) & set(tr.core.dropna()))
        common_cells = sorted(set(ld.cell) & set(valid.cell))
        t = tr[['core','dose_um','screen_id']].drop_duplicates()
        x = ld[['core','cell','dose_um','pert_itime']].drop_duplicates()
        x = x[x.cell.isin(common_cells) & x.core.isin(common)]
        matched = x.merge(t, on=['core', 'dose_um'], how='inner').drop_duplicates()
        if pool is not None:
            p = pool[pool.passed_str_profiling.astype(str).str.lower().eq('true')][['cell','screen_id']].drop_duplicates()
            matched = matched.merge(p, on=['cell','screen_id'], how='inner')
        result['joins'][f'{phase}_to_{screen}'] = {'core_compound_intersection': len(common),
            'normalized_cell_name_intersection': common_cells,
            'lincs_drug_cell_RNA_time_dose_keys_in_drug_and_cell_intersection': len(x),
            'nominal_equal_um_drug_cell_RNA_time_PRISMscreen_keys': len(matched),
            'matched_core_drugs': int(matched.core.nunique()), 'matched_cells': int(matched.cell.nunique()),
            'RNA_time_tokens_of_matches': counts(matched.pert_itime),
            'examples': matched.head(12).to_dict('records'),
            'qualification': 'BRD core ignores formulation; cell labels are not matched cultures; no effect missingness checked; RNA time is not PRISM endpoint time'}

prov = table('data/processed/sciplex_pilot_v2/observation_provenance.csv')
table('data/processed/sciplex_pilot_v2/condition_classification.csv')
table('data/processed/sciplex_pilot_v2/well_summaries.csv')
for version in ['v1', 'v2']:
    rel = f'data/processed/sciplex_pilot_{version}/pilot_manifest.json'
    manifest = json.loads(record(rel).read_text(encoding='utf-8-sig'))
    result['sciplex'][version] = {'sources_current_stat': {k: {'path': v['file'],
        'exists': (ROOT / v['file']).is_file(),
        'current_bytes': (ROOT / v['file']).stat().st_size if (ROOT / v['file']).is_file() else None,
        'manifest_bytes': v['bytes'], 'matrix_bytes_read': False}
        for k, v in manifest['sources'].items()}, 'use_restrictions': manifest.get('use_restrictions', [])}
result['sciplex']['recomputed_provenance'] = {'rows': len(prov), 'classification': counts(prov.classification),
    'study_rows': counts(prov.study), 'cells': counts(prov.cell_line), 'dose_units': counts(prov.dose_unit),
    'biological_replicate_id': counts(prov.biological_replicate_id),
    'RNA_time_columns': [c for c in prov if 'time' in c.lower()],
    'interventions': sorted(set(prov.first_intervention.dropna()) | set(prov.second_intervention.dropna()))}
names = set(result['sciplex']['recomputed_provenance']['interventions']) - {'control'}
for phase, ld in lincs.items():
    result['joins'][f'sciplex_to_{phase}_casefold_name_candidate'] = sorted(n for n in names if n.casefold() in set(ld.pert_iname.dropna().str.casefold()))
for screen in ['primary','secondary']:
    rel = f'data/external/prism_19q4/raw/{screen}-screen-replicate-collapsed-treatment-info.csv'
    p = pd.read_csv(ROOT / rel, usecols=['name'])
    result['joins'][f'sciplex_to_{screen}_casefold_name_candidate'] = sorted(n for n in names if n.casefold() in set(p.name.dropna().str.casefold()))
old = ['research/eight_directions_20261026/report.md',
       'research/2026-10-27-agent-cell-identifiability-r106/report.md',
       'research/2026-10-27-agent-cell-identifiability-r107/report.md',
       'research/2026-10-27-innovation-scouting/logic_constraints/spec_v3.md']
for rel in old:
    record(rel)
result['old_evidence'] = {'read_documents': old,
    'eight_directions': 'Same nominal target families, distinct SMILES, 16 held-out compounds; functional heterogeneity and finite-interaction/refit comparisons. No measured engagement, independent culture, or cross-chemical sufficiency established.',
    'R106_R107': 'Annotation-feature top-k/ranking comparisons and random-split robustness; no matched measured-proximal-action sufficiency test.',
    'logic_constraints': 'C1 QA only; same-target groups not sufficient for functional equivalence. No positive sufficiency result found in inspected documents.'}
result['assumptions'] = ['PRISM dose interpreted as uM only where README says so; nominal dose equality is not intracellular exposure equality.',
    'LINCS pert_idose parsing normalizes microM symbols/case and converts nM to uM; no rounding tolerance is used.',
    'CCLE prefix and normalized LINCS cell names are a candidate-name link; modified lines/culture/batches are not equated.',
    'A metadata join is not proof that the corresponding matrix value exists or passed assay QC.',
    'No measured action is inferred from moa, target, RNA or drug identifiers.']
(OUT / 'metadata_counts.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'joins': result['joins'], 'sciplex': result['sciplex']}, ensure_ascii=False, indent=2))
