"""Independent design-only verification. Never load response columns."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import sys
import unicodedata
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAIR = ROOT / 'research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv'
PRISM = ROOT / 'data/external/prism_19q4/raw'
COLS = ['Well', 'Cell line', 'Drug 1', 'Drug 2', 'Conc 1 (uM)',
        'Conc 2 (uM)', 'Failed QC', 'Iteration', 'file', 'Plate']

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def label(value):
    return unicodedata.normalize('NFKC', value).strip().casefold()

def dose(value):
    return format(Decimal(value).normalize(), 'f')

assert all(word not in str(PAIR).lower() for word in ('sealed', 'reserve', 'holdout', 'vault'))
raw = pd.read_csv(PAIR, usecols=COLS, dtype=str, keep_default_na=False)
assert set(raw.columns) == set(COLS)
assert set(raw['Failed QC']) == {'True', 'False'}
good = raw.loc[raw['Failed QC'].eq('False')].copy()
controls = {'dmso', 'high control', 'low control'}
combo = good.loc[~good['Drug 1'].map(label).isin(controls)
                 & ~good['Drug 2'].map(label).isin(controls)
                 & good['Drug 1'].map(label).ne(good['Drug 2'].map(label))].copy()
train_stages = {str(i) for i in range(1, 16)}
terminal_stage = 'validation (random, round 15)'
counts = {}
overlap_rows = None
for mode in ('exact_labels_decimal_doses', 'nfkc_strip_casefold_decimal_doses'):
    norm = (lambda value: value) if mode.startswith('exact') else label
    keys, pairs, directed = [], [], []
    for r in combo[COLS].to_dict('records'):
        a = (norm(r['Drug 1']), dose(r['Conc 1 (uM)']))
        b = (norm(r['Drug 2']), dose(r['Conc 2 (uM)']))
        pair = tuple(sorted((a, b)))
        pairs.append(pair)
        keys.append((norm(r['Cell line']), pair))
        directed.append((norm(r['Cell line']), a, b))
    c = combo.assign(key=keys, pair=pairs, directed=directed)
    tr = c.loc[c.Iteration.isin(train_stages)]
    va = c.loc[c.Iteration.eq(terminal_stage)]
    tk, vk = set(tr.key), set(va.key)
    overlap = tk & vk
    pair_cells = c.groupby('pair')['Cell line'].nunique()
    groups = c.groupby(['Cell line', 'Iteration', 'pair'])
    counts[mode] = {
        'qc_combo_rows': len(c), 'all_unordered_pairs': c.pair.nunique(),
        'pairs_in_one_cell_label': int((pair_cells == 1).sum()),
        'cell_iteration_pair_groups': groups.ngroups,
        'groups_with_two_files': int((groups.file.nunique() == 2).sum()),
        'validation_rows': len(va), 'validation_unique_keys': len(vk),
        'overlap_keys': len(overlap), 'nonoverlap_validation_keys': len(vk-tk),
        'validation_new_cell_labels': sorted(set(va['Cell line'].map(norm))-set(tr['Cell line'].map(norm))),
        'validation_new_drug_labels': sorted((set(va['Drug 1'].map(norm)) | set(va['Drug 2'].map(norm))) -
                                             (set(tr['Drug 1'].map(norm)) | set(tr['Drug 2'].map(norm)))),
        'directed_overlap_keys': len(set(tr.directed) & set(va.directed)),
        'shared_keys': [repr(k) for k in sorted(overlap)],
        'overlap_training_stages': sorted(tr.loc[tr.key.isin(overlap), 'Iteration'].unique()),
        'validation_overlap_rows': len(va.loc[va.key.isin(overlap)]),
        'training_overlap_rows': len(tr.loc[tr.key.isin(overlap)]),
    }
    if mode.startswith('exact'):
        overlap_rows = c.loc[c.key.isin(overlap) & (c.Iteration.isin(train_stages) | c.Iteration.eq(terminal_stage)), COLS]
        overlap_rows.to_csv(HERE / 'independent_overlap_mapping.csv', index=False)

def meta(name, cols):
    return pd.read_csv(PRISM / name, usecols=cols, dtype=str, keep_default_na=False)

p = meta('primary-screen-replicate-collapsed-treatment-info.csv', ['screen_id', 'dose', 'broad_id', 'name'])
s = meta('secondary-screen-replicate-treatment-info.csv', ['screen_id', 'dose', 'broad_id', 'name', 'perturbation_type'])
p = p.loc[p.screen_id.eq('HTS') & p.dose.map(dose).eq('2.5')]
s = s.loc[s.perturbation_type.eq('experimental_treatment')]
s = s.loc[s.dose.map(dose).eq('2.5')]
pc = meta('primary-screen-cell-line-info.csv', ['depmap_id', 'passed_str_profiling'])
sc = meta('secondary-screen-cell-line-info.csv', ['depmap_id', 'passed_str_profiling'])
assert set(pc.passed_str_profiling.map(label)) <= {'true', 'false', '', 'na'}
assert set(sc.passed_str_profiling.map(label)) <= {'true', 'false', '', 'na'}
pcids = set(pc.loc[pc.passed_str_profiling.map(label).eq('true'), 'depmap_id']) - {'', 'NA'}
scids = set(sc.loc[sc.passed_str_profiling.map(label).eq('true'), 'depmap_id']) - {'', 'NA'}
prism = {'common_full_batch_ids_at_2_5': len(set(p.broad_id) & set(s.broad_id)),
         'common_STR_metadata_cell_ids': len(pcids & scids),
         'meaning': 'identity metadata only; no finite response, independence or measured-pair assertion'}
expected = json.loads((HERE / 'qualification.json').read_text(encoding='utf-8'))
checks = {str(path): sha(ROOT / path) == record['sha256'] for path, record in expected['inputs'].items()}
out = {'python': sys.executable, 'response_columns_loaded': False,
       'allowlisted_PAIR_columns': COLS, 'source_hash_matches_qualification': checks,
       'independent_script_sha256': sha(Path(__file__)),
       'overlap_mapping_sha256': sha(HERE / 'independent_overlap_mapping.csv'),
       'raw_rows': len(raw), 'QC_pass_rows': len(good),
       'observed_plate_groups': good.groupby(['Cell line', 'Iteration', 'file', 'Plate']).ngroups,
       'batchie': counts, 'prism': prism,
       'limits': ['No chemical entity alias dictionary applied.',
                  'No response, prediction, transfer or independence verified.',
                  'Full-file bytes read only for SHA256 provenance; response columns never parsed.']}
(HERE / 'independent_verification.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(out, ensure_ascii=False, indent=2))
