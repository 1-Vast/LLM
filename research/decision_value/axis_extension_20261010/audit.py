"""Retained-byte axis audit; no network or numerical producer imports."""
import hashlib
import io
import json
from pathlib import Path

import h5py
import numpy as np
from scipy.sparse import csr_matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'research/decision_value/observation_reliability/axis'
PRIOR = HERE.parent / 'axis_recovery_20261010/calibration_v2'
REVISION = 'fdf87abece385feea6fa5e9944ab46e173b6af50'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(obj, stream, indent=2, allow_nan=False)
        stream.write('\n')


def lines(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines()] if Path(path).exists() else []


class Cached(io.RawIOBase):
    """Only exact, hash-verified retained source ranges are readable."""
    def __init__(self, file, extension=False):
        self.size = read(PRIOR / 'CENSUSES.json')[file]['file_bytes']
        self.position, self.spans = 0, []
        records = [(OLD, r) for r in lines(OLD / 'NETWORK.jsonl')]
        records += [(PRIOR, r) for p in ('NETWORK.jsonl', 'CACHE_REUSE.jsonl') for r in lines(PRIOR / p)]
        if extension:
            records += [(HERE, r) for r in lines(HERE / 'NETWORK.jsonl')]
        self.paths = set()
        for folder, row in records:
            if row.get('file') != file or row.get('status', 'RETAINED') not in ('RETAINED', 'REUSED'):
                continue
            assert row['source_revision'] == REVISION
            path = ROOT / row['asset'] if 'asset' in row else folder / row['path']
            body = path.read_bytes()
            assert len(body) == row['bytes'] == row['end'] - row['start'] + 1
            assert hashlib.sha256(body).hexdigest() == row['sha256']
            if row.get('status') != 'REUSED':
                assert row['http_status'] == 206
            self.spans.append((row['start'], body))
            self.paths.add(path)
        self.spans.sort(key=lambda x: x[0])

    def at(self, first, stop):
        assert 0 <= first <= stop <= self.size
        cursor, parts = first, []
        for offset, body in self.spans:
            if offset > cursor:
                break
            end = min(stop, offset + len(body))
            if end > cursor:
                parts.append(body[cursor - offset:end - offset])
                cursor = end
            if cursor == stop:
                return b''.join(parts)
        if first == stop:
            return b''
        raise ValueError(f'unretained_range:{first}:{stop}')

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        return self.position
    def readinto(self, buffer):
        n = min(len(buffer), self.size - self.position)
        buffer[:n] = self.at(self.position, self.position + n)
        self.position += n
        return n


def extract(source, dataset, start, stop):
    assert dataset.compression is None and not dataset.shuffle and not dataset.fletcher32
    parts, cursor, stride = [], start, dataset.dtype.itemsize
    while cursor < stop:
        if dataset.chunks is None:
            end, offset, origin = stop, dataset.id.get_offset(), 0
        else:
            origin = cursor // dataset.chunks[0] * dataset.chunks[0]
            info = dataset.id.get_chunk_info_by_coord((origin,))
            assert info.filter_mask == 0
            offset, end = info.byte_offset, min(stop, origin + dataset.chunks[0])
        parts.append(source.at(offset + (cursor-origin)*stride, offset + (end-origin)*stride))
        cursor = end
    return np.frombuffer(b''.join(parts), dtype=dataset.dtype)


def vectors(file, rows, extension=False):
    source = Cached(file, extension)
    protocol = read(PRIOR / 'PROTOCOL.json')
    names = read(PRIOR / f'inputs/{file}_GENES.json')
    census = read(PRIOR / 'CENSUSES.json')[file]
    raw, stored = [], []
    with h5py.File(source, 'r') as h5:
        assert h5['X'].attrs['shape'][1] == len(names) == 62710
        for row in rows:
            lo, hi = map(int, extract(source, h5['X/indptr'], row, row+2))
            indices = extract(source, h5['X/indices'], lo, hi)
            values = extract(source, h5['X/data'], lo, hi)
            assert len(indices) == len(values) == len(np.unique(indices))
            assert np.all((indices >= 0) & (indices < len(names)))
            assert np.isfinite(values).all() and (values >= 0).all()
            dense = np.zeros(len(names), dtype=np.float64)
            dense[indices] = values
            raw.append(np.log1p(dense))
            offset = census['layouts']['obsm/X_hvg']['offset'] + row*8000
            target = np.frombuffer(source.at(offset, offset+8000), dtype='<f4')
            assert np.isfinite(target).all() and (target >= 0).all()
            stored.append(target[protocol['endpoint']['coordinates']].astype(np.float64))
    return names, np.asarray(raw), np.asarray(stored)


def matching(names, matrix, targets, symbols, consistency=None):
    """Filter candidates row-by-row; compare every source gene at fixed tolerance."""
    records = []
    for column, symbol in enumerate(symbols):
        candidates = np.arange(len(names))
        for row in np.argsort(-np.abs(targets[:, column])):
            candidates = candidates[np.abs(matrix[row, candidates]-targets[row, column]) <= 1e-5]
        expected = names.index(symbol)
        nonzero = int((np.abs(targets[:, column]) > 1e-5).sum())
        error = float(np.max(np.abs(matrix[:, expected]-targets[:, column])))
        consistent, held_nonzero, held_error = True, None, None
        if consistency is not None:
            held_raw, held_target = consistency
            held_error = float(np.max(np.abs(held_raw[:, expected]-held_target[:, column])))
            held_nonzero = int((np.abs(held_target[:, column]) > 1e-5).sum())
            consistent = held_error <= 1e-5 and held_nonzero >= 1
        passed = len(candidates) == 1 and candidates[0] == expected and names.count(symbol) == 1 and nonzero >= 2 and consistent
        records.append(dict(gene=symbol,matching_source_indices=candidates.tolist(),matching_source_symbols=[names[int(i)] for i in candidates],nonzero_cells=nonzero,expected_max_error=error,consistency_nonzero_cells=held_nonzero,consistency_max_error=held_error,passed=bool(passed)))
    return records


def binary_groups(file, rows):
    jobs = read(PRIOR / 'INDEX_LAYOUTS.json')[file]
    lookup = {job['row']: job for job in jobs}
    source = Cached(file)
    columns, pointers = [], [0]
    for row in rows:
        indices = np.frombuffer(b''.join(source.at(a,b+1) for a,b in lookup[row]['indices']), dtype='<i4')
        assert len(indices) == len(np.unique(indices)) == lookup[row]['nnz']
        columns.append(indices)
        pointers.append(pointers[-1]+len(indices))
    return csr_matrix((np.ones(pointers[-1],dtype=bool),np.concatenate(columns),np.asarray(pointers)),shape=(len(rows),62710))


def support_matches(matrix, expected):
    csc = matrix.tocsc()
    signatures = [csc.indices[csc.indptr[g]:csc.indptr[g+1]].tobytes() for g in range(csc.shape[1])]
    return [[g for g,p in enumerate(signatures) if p == signatures[e]] for e in expected]


def check_freeze(path):
    for name, expected in read(path)['sha256'].items():
        assert sha(ROOT / name) == expected, name


def c44_audit():
    check_freeze(HERE / 'C44_FREEZE.json')
    old_rows = next(x['row_ids'] for x in read(OLD / 'RESULTS.json')['files'] if x['file']=='c44.h5ad')
    groups = read(PRIOR / 'ROW_MANIFEST.json')['groups']
    discovery = sorted(r for g in groups if g['file']=='c44.h5ad' for r in g['discovery_rows'])
    held = sorted(r for g in groups if g['file']=='c44.h5ad' for r in g['holdout_rows'])
    assert (len(old_rows),len(discovery),len(held)) == (224,19,9)
    assert len(set(old_rows+discovery+held)) == 252
    names, matrix, targets = vectors('c44.h5ad',old_rows+discovery+held)
    symbols = read(PRIOR / 'PROTOCOL.json')['endpoint']['symbols']
    reduced = matching(names,matrix[:243],targets[:243],symbols)
    full = matching(names,matrix,targets,symbols)
    output = dict(status='PASS_HISTORICAL_UNION_FILE_LOCAL_ENDPOINT39' if all(r['passed'] for r in full) else 'BLOCKED',source_file='c44.h5ad',source_revision=REVISION,rows=old_rows+discovery+held,old_control_count=224,new_discovery_count=19,previously_read_holdout_count=9,old_plus_discovery_passes=sum(x['passed'] for x in reduced),reduced_failures=[x for x in reduced if not x['passed']],union_passes=sum(x['passed'] for x in full),records=full,max_error=max(x['expected_max_error'] for x in full),new_network_bytes=0,all_union_cells_previously_exposed=True,fresh_holdout=False,original_results_superseded=False,model_axis_certified=False,P06_execution_released=False)
    write(HERE / 'C44_UNION.json',output)
    print(json.dumps({k:v for k,v in output.items() if k not in ('rows','records','reduced_failures')}))


if __name__ == '__main__':
    c44_audit()
