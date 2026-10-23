"""Check real feature/label outputs and predecessor continuity without protected values."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/norman_numeric_qualification'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


previous = json.loads((ROOT / 'log/20261022/norman_functional_contract/VERIFICATION.json').read_text())
drift = [name for name, expected in previous['files'].items()
         if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
data = np.load(OUT / 'SINGLE_RNA_FEATURES.npz')
assert data['features'].shape == (103, 33694) and len(set(data['genes'])) == 103
assert np.isfinite(data['features']).all()
counts = pd.read_csv(OUT / 'RNA_QC_COUNTS.csv')
assert counts.retained_cells.sum() == 40247
assert not set(counts.target) & {'BAK1', 'BCL2L11'}
functions = pd.read_csv(OUT / 'FUNCTION_SOURCE_DEVELOPMENT.csv')
assert functions['split'].value_counts().to_dict() == {'source': 3160, 'development': 1051}
assert len(functions.pair.unique()) == len(functions)
assert np.isfinite(functions.growth).all()
assert set(functions.gene_a) | set(functions.gene_b) == set(data['genes'])
assert functions.mirror_abs_difference.max() < 1e-12
prior = pd.read_csv(OUT / 'SINGLE_GROWTH_PRIORS.csv')
assert set(prior.gene) == set(data['genes'])
assert json.loads((OUT / 'FUNCTION_MASK_REPORT.json').read_text())['protected_values_converted'] == 0
files = {}
for folder in (OUT, Path(__file__).resolve().parent):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'VERIFICATION.json':
            files[path.relative_to(ROOT).as_posix()] = digest(path)
result = {'status': 'FAIL' if drift else 'PASS_LOCAL',
          'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
          'scope': 'Actual RNA feature shape/finiteness, cell counts, exported permitted label uniqueness, prior joins and local byte continuity; not performance/global provenance repair',
          'files': files}
(OUT / 'VERIFICATION.json').write_text(json.dumps(result, indent=2))
print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))
print('Current files sealed:', len(files))
assert not drift
