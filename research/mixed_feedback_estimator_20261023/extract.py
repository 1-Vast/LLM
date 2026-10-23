"""Two-pass source-pair/old-single/control extraction; no function file access."""
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'log/20261022/norman_functional_contract/data'
OUT = ROOT / 'log/20261023/mixed_feedback_estimator'
SHAPE = [33694, 5898240, 442237190]
RENAMES = {'C3orf72': 'FOXL2NB', 'C19orf26': 'CBARP',
           'KIAA1804': 'RP5-862P8.2', 'RHOXF2': 'RHOXF2B'}


def target_name(raw, selections, pairs):
    if raw in selections:
        return selections[raw]
    parts = raw.split('_')
    if len(parts) == 2:
        pair = '|'.join(sorted(RENAMES.get(p, p) for p in parts))
        if pair in pairs:
            return pair
    return None


def accumulate(block, mapping, totals, feature_map, log_sums, cp_sums):
    cells = block[:, 1] - 1
    features = feature_map[block[:, 0] - 1]
    keep = (mapping[cells] >= 0) & (features >= 0)
    cell = cells[keep]
    cp = block[keep, 2] * (10000.0 / totals[cell])
    np.add.at(cp_sums, (mapping[cell], features[keep]), cp)
    np.add.at(log_sums, (mapping[cell], features[keep]), np.log1p(cp))
    return int(keep.sum())


def chunks():
    with gzip.open(DATA / 'GSE133344_raw_matrix.mtx.gz', 'rt') as stream:
        assert next(stream).strip() == '%%MatrixMarket matrix coordinate integer general'
        line = next(stream)
        while line.startswith('%'):
            line = next(stream)
        assert list(map(int, line.split())) == SHAPE
        for chunk in pd.read_csv(stream, sep=' ', header=None, names=['gene', 'cell', 'count'],
                                 dtype=np.int32, chunksize=2_000_000):
            yield chunk.to_numpy()


def self_test():
    choices = {'A_NegCtrl0': 'A', 'NegCtrl0_NegCtrl0': 'CONTROL'}
    assert target_name('A_B', choices, {'A|B'}) == 'A|B'
    assert target_name('B_A', choices, {'A|B'}) == 'A|B'
    assert target_name('A_C', choices, {'A|B'}) is None
    assert target_name('A_NegCtrl0', choices, {'A|B'}) == 'A'
    assert target_name('NegCtrl0_NegCtrl0', choices, {'A|B'}) == 'CONTROL'
    assert target_name('RHOXF2_A', {}, {'A|RHOXF2B'}) == 'A|RHOXF2B'
    block = np.array([[1, 1, 10], [2, 1, 20], [1, 2, 999], [1, 3, 30]], dtype=np.int32)
    logs = np.zeros((2, 1)); cp = logs.copy()
    used = accumulate(block, np.array([0, -1, 1]), np.array([100, 999, 100]),
                      np.array([0, -1]), logs, cp)
    assert used == 2
    np.testing.assert_allclose(cp[:, 0], [1000, 3000])
    np.testing.assert_allclose(logs[:, 0], np.log1p([1000, 3000]))
    print(json.dumps({'synthetic_selector_access': 'PASS', 'real_matrix_opened': False}))


def main():
    started = time.time()
    freeze = json.loads((OUT / 'FREEZE.json').read_text())
    for name, expected in freeze['files'].items():
        path = ROOT / name
        sha = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                sha.update(block)
        assert sha.hexdigest() == expected, name
    outputs = [OUT / 'EXTRACTION_STARTED.json', OUT / 'STATE_BY_GEM.npz', OUT / 'EXTRACTION.json']
    assert not any(p.exists() for p in outputs), 'Extraction already started; inspect existing artifacts, do not rerun'
    pair_file = OUT / 'support/SOURCE_PAIR_METADATA.csv'
    identity_file = ROOT / 'log/20261023/reciprocity_resolution/IDENTITY.json'
    with pair_file.open(newline='') as stream:
        pairs = {r['pair'] for r in csv.DictReader(stream) if int(r['identity_qc_cells']) > 0}
    identity = json.loads(identity_file.read_text())
    genes = identity['targets']
    assert len(pairs) == 73 and len(genes) == len(set(genes)) == 103
    indices = [identity['indices'][g] for g in genes]
    assert len(set(indices)) == 103 and identity['indices']['RHOXF2B'] == 14109
    with gzip.open(DATA / 'GSE133344_raw_genes.tsv.gz', 'rt') as stream:
        reference = [line.rstrip('\n').split('\t') for line in stream]
    assert len(reference) == SHAPE[0]
    assert [reference[i][1] for i in indices] == genes
    metadata = pd.read_csv(DATA / 'GSE133344_raw_cell_identities.csv.gz',
                           usecols=['cell_barcode', 'guide_identity', 'number_of_cells', 'good_coverage'])
    targets = metadata['guide_identity'].str.split('__').str[0]
    possible = set(targets.dropna())
    selections = {}
    for gene in genes:
        original = next((k for k, v in RENAMES.items() if v == gene), gene)
        orientation = original + '_NegCtrl0'
        if orientation not in possible:
            orientation = 'NegCtrl0_' + original
        assert orientation in possible, gene
        selections[orientation] = gene
    controls = {t for t in possible if len(t.split('_')) == 2
                and all(p.startswith('NegCtrl') for p in t.split('_'))
                and t != 'NegCtrl1_NegCtrl0'}
    assert controls == {'NegCtrl0_NegCtrl0', 'NegCtrl10_NegCtrl0', 'NegCtrl11_NegCtrl0'}
    selections.update({t: 'CONTROL' for t in controls})
    named = targets.map(lambda t: target_name(t, selections, pairs) if isinstance(t, str) else None)
    good = metadata['number_of_cells'].eq(1) & metadata['good_coverage'].astype(str).str.lower().eq('true')
    single_control_candidates = int((good & targets.isin(selections)).sum())
    pair_candidates = int((good & named.isin(pairs)).sum())
    assert single_control_candidates == 40247 and pair_candidates == 20395
    candidate = metadata.loc[good & named.notna(), ['cell_barcode']].copy()
    candidate['name'] = named[good & named.notna()]
    candidate['gem'] = candidate['cell_barcode'].str.rsplit('-', n=1).str[-1]
    names = ['CONTROL'] + sorted(genes) + sorted(pairs)
    groups = [(name, str(gem)) for name in names for gem in range(1, 9)]
    group_map = {g: i for i, g in enumerate(groups)}
    assert set(zip(candidate['name'], candidate['gem'])) == set(groups)
    cell_info = {r.cell_barcode: group_map[(r.name, r.gem)] for r in candidate.itertuples()}
    mapping = np.full(SHAPE[1], -1, dtype=np.int32)
    with gzip.open(DATA / 'GSE133344_raw_barcodes.tsv.gz', 'rt') as stream:
        barcode_count = 0
        for index, line in enumerate(stream):
            mapping[index] = cell_info.get(line.strip(), -1)
            barcode_count += 1
    assert barcode_count == SHAPE[1] and int((mapping >= 0).sum()) == len(candidate)
    inputs = [pair_file, identity_file, DATA / 'GSE133344_raw_cell_identities.csv.gz',
              DATA / 'GSE133344_raw_genes.tsv.gz']
    provenance = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    outputs[0].write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                                    'input_sha256': provenance, 'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2))
    totals = np.zeros(SHAPE[1], dtype=np.int64)
    scanned = 0
    for block in chunks():
        cells = block[:, 1] - 1
        allowed = mapping[cells] >= 0
        np.add.at(totals, cells[allowed], block[allowed, 2])
        scanned += len(block)
        if scanned % 40_000_000 == 0:
            print(json.dumps({'pass': 1, 'entries_scanned': scanned}), flush=True)
    assert scanned == SHAPE[2]
    mapping[totals < 2000] = -1
    counts = np.bincount(mapping[mapping >= 0], minlength=len(groups))
    empty = [groups[i] for i in np.flatnonzero(counts == 0)]
    if empty:
        outputs[2].write_text(json.dumps({'status': 'STOP_REQUIRED_GROUP_EMPTY', 'empty_groups': empty}, indent=2))
        raise RuntimeError('Required group empty after fixed UMI QC; no dropping or rerun')
    feature_map = np.full(SHAPE[0], -1, dtype=np.int32)
    feature_map[indices] = np.arange(len(genes))
    log_sums = np.zeros((len(groups), len(genes)), dtype=np.float64)
    cp_sums = log_sums.copy()
    scanned = stored_entries = 0
    for block in chunks():
        stored_entries += accumulate(block, mapping, totals, feature_map, log_sums, cp_sums)
        scanned += len(block)
        if scanned % 40_000_000 == 0:
            print(json.dumps({'pass': 2, 'entries_scanned': scanned}), flush=True)
    assert scanned == SHAPE[2]
    logs = log_sums / counts[:, None]
    cp = cp_sums / counts[:, None]
    assert np.isfinite(logs).all() and np.isfinite(cp).all()
    np.savez_compressed(outputs[1], group_names=np.array([g[0] for g in groups]),
                        gems=np.array([g[1] for g in groups]), genes=np.array(genes),
                        raw_feature_indices=np.array(indices), mean_log1pCP10K=logs,
                        mean_CP10K=cp, counts=counts)
    report = {'status': 'PASS', 'utc': datetime.now(timezone.utc).isoformat(), 'seconds': time.time() - started,
              'matrix_shape': SHAPE, 'passes': 2, 'entries_materialized_each_pass': scanned,
              'numeric_triplet_fields_materialized_total': scanned * 3 * 2,
              'single_control_identity_candidates': single_control_candidates, 'pair_identity_candidates': pair_candidates,
              'cells_retained': int(counts.sum()), 'single_control_cells_retained': int(sum(counts[i] for i,g in enumerate(groups) if '|' not in g[0])),
              'pair_cells_retained': int(sum(counts[i] for i,g in enumerate(groups) if '|' in g[0])),
              'groups': len(groups), 'readouts': len(genes), 'second_pass_selected_readout_entries_accumulated': stored_entries,
              'matrix_compressed_bytes_per_pass': (DATA / 'GSE133344_raw_matrix.mtx.gz').stat().st_size,
              'output_bytes': outputs[1].stat().st_size, 'input_sha256': provenance,
              'function_values_read': 0, 'development_protected_profiles_accumulated': 0,
              'scope': 'Both full raw matrix passes numerically decode all triplets, including excluded cells. Totals accumulated only for fixed source pairs/old singles/controls across all genes; state accumulation only for their fixed 103 readouts. No other doubles accumulated. Per-cell denominators; no pooling across gemgroups. No function files opened.'}
    outputs[2].write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    self_test() if sys.argv[1:] == ['--self-test'] else main()
