"""Two-pass streaming single/control-only RNA QC and pseudobulk, no double-state features."""
from collections import Counter
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261022/norman_functional_contract'
OUT = ROOT / 'log/20261022/norman_numeric_qualification'
DATA = BASE / 'data'
RENAMES = {'C3orf72': 'FOXL2NB', 'C19orf26': 'CBARP',
           'KIAA1804': 'RP5-862P8.2', 'RHOXF2': 'RHOXF2B'}


def chunks():
    with gzip.open(DATA / 'GSE133344_raw_matrix.mtx.gz', 'rt') as stream:
        next(stream)
        line = next(stream)
        while line.startswith('%'):
            line = next(stream)
        shape = list(map(int, line.split()))
        assert shape == [33694, 5898240, 442237190]
        for chunk in pd.read_csv(stream, sep=' ', header=None, names=['gene', 'cell', 'count'],
                                 dtype=np.int32, chunksize=2_000_000):
            yield chunk.to_numpy()


def main():
    started = time.time()
    metadata = pd.read_csv(DATA / 'GSE133344_raw_cell_identities.csv.gz',
                           usecols=['cell_barcode', 'guide_identity', 'number_of_cells', 'good_coverage'])
    targets = metadata['guide_identity'].str.split('__').str[0]
    possible = set(targets.dropna())
    panel = json.loads((BASE / 'IDENTITY_JOIN.json').read_text())['matched_single_genes']
    selections = {}
    for gene in panel:
        if gene in {'BAK1', 'BCL2L11'}:
            continue
        original = next((k for k, v in RENAMES.items() if v == gene), gene)
        orientation = original + '_NegCtrl0'
        if orientation not in possible:
            orientation = 'NegCtrl0_' + original
        assert orientation in possible, gene
        selections[orientation] = gene
    controls = {t for t in possible if len(t.split('_')) == 2
                and all(p.startswith('NegCtrl') for p in t.split('_'))
                and t != 'NegCtrl1_NegCtrl0'}
    selections.update({t: 'CONTROL' for t in controls})
    good = metadata['good_coverage'].astype(str).str.lower().eq('true')
    keep = metadata['number_of_cells'].eq(1) & good & targets.isin(selections)
    candidate = metadata.loc[keep].copy()
    candidate['target'] = targets[keep].map(selections)
    candidate['gemgroup'] = candidate['cell_barcode'].str.rsplit('-', n=1).str[-1]
    groups = sorted(set(zip(candidate['target'], candidate['gemgroup'])))
    group_map = {g: i for i, g in enumerate(groups)}
    cell_info = {r.cell_barcode: group_map[(r.target, r.gemgroup)] for r in candidate.itertuples()}
    mapping = np.full(5898240, -1, dtype=np.int32)
    with gzip.open(DATA / 'GSE133344_raw_barcodes.tsv.gz', 'rt') as stream:
        for index, line in enumerate(stream):
            mapping[index] = cell_info.get(line.strip(), -1)
    totals = np.zeros(len(mapping), dtype=np.int64)
    scanned = 0
    for block in chunks():
        cells = block[:, 1] - 1
        allowed = mapping[cells] >= 0
        np.add.at(totals, cells[allowed], block[allowed, 2])
        scanned += len(block)
        if scanned % 40_000_000 == 0:
            print(json.dumps({'pass': 1, 'entries_scanned': scanned}), flush=True)
    assert scanned == 442237190
    mapping[totals < 2000] = -1
    counts = np.bincount(mapping[mapping >= 0], minlength=len(groups))
    for target, gem in groups:
        if target != 'CONTROL' and counts[group_map[(target, gem)]]:
            assert ('CONTROL', gem) in group_map and counts[group_map[('CONTROL', gem)]] > 0
    sums = np.zeros((len(groups), 33694), dtype=np.float64)
    scanned = 0
    for block in chunks():
        cells = block[:, 1] - 1
        allowed = mapping[cells] >= 0
        cell = cells[allowed]
        gene = block[allowed, 0] - 1
        normalized = np.log1p(block[allowed, 2] * (10000.0 / totals[cell]))
        np.add.at(sums, (mapping[cell], gene), normalized)
        scanned += len(block)
        if scanned % 40_000_000 == 0:
            print(json.dumps({'pass': 2, 'entries_scanned': scanned}), flush=True)
    assert scanned == 442237190
    means = sums / np.maximum(counts[:, None], 1)
    profiles = []
    retained = []
    for target in sorted(set(selections.values()) - {'CONTROL'}):
        weighted = np.zeros(33694)
        ncell = 0
        for group_index, (name, gem) in enumerate(groups):
            if name == target and counts[group_index]:
                weighted += counts[group_index] * (means[group_index] - means[group_map[('CONTROL', gem)]])
                ncell += int(counts[group_index])
        if ncell:
            retained.append(target)
            profiles.append(weighted / ncell)
    features = np.asarray(profiles)
    assert np.isfinite(features).all()
    np.savez_compressed(OUT / 'SINGLE_RNA_FEATURES.npz', genes=np.asarray(retained), features=features)
    pd.DataFrame([{'target': name, 'gemgroup': gem, 'retained_cells': int(counts[i])}
                  for i, (name, gem) in enumerate(groups)]).to_csv(OUT / 'RNA_QC_COUNTS.csv', index=False)
    report = {'status': 'PASS', 'utc_end': datetime.now(timezone.utc).isoformat(),
              'seconds': time.time() - started, 'entries_each_pass': scanned,
              'identity_QC_single_control_candidates': int(keep.sum()),
              'RNA_UMI_QC_retained_single_control_cells': int(counts.sum()),
              'retained_target_genes': len(retained), 'feature_shape': list(features.shape),
              'selected_control_targets': sorted(controls), 'group_count': len(groups),
              'zero_cell_targets': sorted(set(selections.values()) - {'CONTROL'} - set(retained)),
              'double_RNA_entries_accumulated': 0, 'functional_values_used': 0,
              'normalization': 'Declared log1pCP10K gemgroup-control mean variant, not exact author normalization'}
    (OUT / 'RNA_QC_REPORT.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
