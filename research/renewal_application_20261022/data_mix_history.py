"""Preserve historical MIX-seq decision and inspect schema only; never expression/treated abundance."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import h5py

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/renewal_application/data'
OUT.mkdir(parents=True, exist_ok=True)
COMMIT = 'ef49d423fcaa'
BASE = 'research/astra/kinetic_horizon_20261010/'
historical = {}
for name in ('README.md', 'PROTOCOL.md', 'LITERATURE.md', 'FREEZE.json', 'mixseq_index.py'):
    payload = subprocess.check_output(['git', 'show', COMMIT + ':' + BASE + name], cwd=ROOT)
    path = OUT / ('historical_mix_' + name.replace('.', '_') + '.txt')
    assert not path.exists()
    path.write_bytes(payload)
    historical[name] = {'git_commit': COMMIT, 'git_path': BASE + name,
                        'saved': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(payload).hexdigest()}
source = ROOT / 'data/external/mixseq_scperturb/mcfarland_2020.h5ad'
with h5py.File(source, 'r') as handle:
    obs = handle['obs']
    schema = {}
    for name in obs.keys():
        item = obs[name]
        if isinstance(item, h5py.Dataset):
            schema[name] = {'kind': 'dataset', 'shape': list(item.shape), 'dtype': str(item.dtype)}
        else:
            schema[name] = {'kind': 'group', 'children': list(item.keys())}
    safe_fields = ('DepMap_ID', 'cell_line', 'channel', 'perturbation', 'time', 'dose_value', 'hash_tag')
    categories = {}
    for name in safe_fields:
        if name not in obs:
            continue
        item = obs[name]
        if isinstance(item, h5py.Group) and 'categories' in item:
            values = item['categories'][...]
            categories[name] = sorted(str(v.decode('utf-8') if isinstance(v, bytes) else v) for v in values)
        elif isinstance(item, h5py.Dataset):
            values = item[...]
            categories[name] = sorted({str(v.decode('utf-8') if isinstance(v, bytes) else v) for v in values})
    x = handle['X']
    expression_schema = {'kind': 'dataset', 'shape': list(x.shape), 'dtype': str(x.dtype)} if isinstance(x, h5py.Dataset) else {'kind': 'group', 'children': list(x.keys()), 'attrs': {k: str(v) for k, v in x.attrs.items()}}
record = {'utc': datetime.now(timezone.utc).isoformat(), 'historical_records': historical,
    'local_h5ad': {'path': str(source.relative_to(ROOT)), 'bytes': source.stat().st_size,
                  'obs_schema': schema, 'safe_metadata_categories': categories, 'X_schema_only': expression_schema},
    'expression_values_read': False, 'functional_values_read': False, 'treated_cell_abundance_computed': False,
    'decision': 'DO_NOT_REOPEN historical six-drug early-RNA-to-PRISM5day/STATE transport/measurement policy task',
    'limit': 'This preserves a scoped historical negative; it does not prove all static MIX-seq RNA tasks invalid or require universal independent biology/same-cell trajectories.'}
(OUT / 'MIX_HISTORY_AND_SCHEMA.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'history_files': len(historical), 'obs_fields': list(schema), 'metadata_category_counts': {k: len(v) for k, v in categories.items()}, 'expression_schema': expression_schema}))
