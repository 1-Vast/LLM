"""Inspect archive headers and identifiers only, never biological scalar outcomes."""
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/strategy_rethink'
FILES = {
    'phase1': ROOT / 'data/external/lincs_l1000_gse92742/derived/blockq_phase1.npz',
    'routes': ROOT / 'research/knowledge_transfer_20261012/cache/dev_routes.npz',
    'generic': ROOT / 'research/knowledge_transfer_20261012/cache/dev_generic.npy',
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def header(handle):
    version = np.lib.format.read_magic(handle)
    reader = (np.lib.format.read_array_header_1_0 if version == (1, 0)
              else np.lib.format.read_array_header_2_0)
    shape, fortran, dtype = reader(handle)
    return {'shape': list(shape), 'fortran': fortran, 'dtype': str(dtype)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'files': {}, 'outcome_arrays_cast': False}
    for name, path in FILES.items():
        item = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest(path)}
        if path.suffix == '.npz':
            with zipfile.ZipFile(path) as archive:
                item['arrays'] = {key: header(archive.open(key)) for key in archive.namelist()}
        else:
            with path.open('rb') as handle:
                item['arrays'] = {'array': header(handle)}
        report['files'][name] = item
    with np.load(FILES['routes'], allow_pickle=False) as archive:
        ids = {key: archive[key] for key in ('comp', 'line', 'fold', 'regime')}
    mask = ids['regime'] == 'A'
    comps = np.unique(ids['comp'][mask])
    report['regime_A'] = {
        'rows': int(mask.sum()), 'compounds': len(comps),
        'lines': np.unique(ids['line'][mask]).tolist(),
        'fold_compound_counts': {str(f): len(np.unique(ids['comp'][mask & (ids['fold'] == f)]))
                                 for f in np.unique(ids['fold'])},
        'min_lines_per_compound': min(int(np.sum(mask & (ids['comp'] == c))) for c in comps),
        'compounds_per_line': {str(l): len(np.unique(ids['comp'][mask & (ids['line'] == l)]))
                               for l in np.unique(ids['line'])},
    }
    # Retain only identifier lists; no activities, norms, predictions or expression scalars.
    report['identifier_rows'] = {key: value[mask].tolist() for key, value in ids.items()}
    target = OUT / 'SCHEMA_AUDIT.json'
    with target.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps({'report': str(target), 'regime_A': report['regime_A']}))


if __name__ == '__main__':
    main()
