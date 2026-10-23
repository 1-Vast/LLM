"""Metadata-only identity audit; never access RNA response or functional values."""
import csv
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/reciprocity_resolution/identity'
BASE = ROOT / 'log/20261022/norman_functional_contract'
SOURCES = {
    'rna': ROOT / 'log/20261022/norman_numeric_qualification/SINGLE_RNA_FEATURES.npz',
    'genes': BASE / 'data/GSE133344_raw_genes.tsv.gz',
    'cell_identity': BASE / 'data/GSE133344_raw_cell_identities.csv.gz',
    'chosen_final': ROOT / 'log/20261022/norman_matched_guide/root_sources/chosen_final.body',
    'chosen_sharing': ROOT / 'log/20261022/norman_matched_guide/root_sources/chosen_sharing.body',
    'author_population': BASE / 'root_sources/population.source.txt',
    'author_notebook': BASE / 'root_sources/population.body',
    'pseudobulk_code': ROOT / 'research/norman_numeric_qualification_20261022/rna_pseudobulk.py',
}
ALIASES = {'C3orf72': 'FOXL2NB', 'C19orf26': 'CBARP',
           'KIAA1804': 'RP5-862P8.2', 'RHOXF2': 'RHOXF2B'}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with np.load(SOURCES['rna']) as stored:
        targets = stored['genes'].tolist()  # explicitly no stored['features'] access
    with gzip.open(SOURCES['genes'], 'rt') as stream:
        rows = [line.rstrip('\n').split('\t') for line in stream]
    with gzip.open(SOURCES['cell_identity'], 'rt', newline='') as stream:
        labels = sorted({row['guide_identity'].split('__')[0] for row in csv.DictReader(stream)})
    maps = {}
    for name in ['chosen_final', 'chosen_sharing']:
        with SOURCES[name].open(newline='') as stream:
            maps[name] = [{key: row[key] for key in ['gene', 'guide_id', 'protospacer']}
                          for row in csv.DictReader(stream)]
    inverse = {v: k for k, v in ALIASES.items()}
    mapping = []
    for target in targets:
        raw_label = inverse.get(target, target)
        historical = [i for i, (_, symbol) in enumerate(rows)
                      if symbol == raw_label or (target != 'RHOXF2B' and ALIASES.get(symbol, symbol) == target)]
        intended = [i for i, (_, symbol) in enumerate(rows)
                    if symbol == target or (symbol != 'RHOXF2' and ALIASES.get(symbol, symbol) == target)]
        exact = [i for i, (_, symbol) in enumerate(rows) if symbol == target]
        mapping.append({'target_label': target, 'historical_raw_label': raw_label,
                        'historical_indices': historical, 'author_intended_indices': intended,
                        'exact_canonical_symbol_indices': exact,
                        'historical_single_labels': [x for x in labels
                                                    if x in [raw_label + '_NegCtrl0', 'NegCtrl0_' + raw_label]],
                        'chosen_final': [r for r in maps['chosen_final'] if r['gene'] == raw_label]})
    assert len(targets) == 103 and len(rows) == 33694
    assert all(len(r['historical_indices']) == len(r['author_intended_indices']) == 1 for r in mapping)
    assert all(len(r['exact_canonical_symbol_indices']) == 1 for r in mapping)
    assert all(len(r['historical_single_labels']) >= 1 for r in mapping)
    report = {
        'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'TWO_DISTINCT_METADATA_CONTRACTS_AVAILABLE_NOT_PHYSICAL_FORCE_IDENTIFICATION',
        'targets': len(targets), 'reference_features': len(rows),
        'rna_response_arrays_accessed': 0, 'functional_values_accessed': 0,
        'source_sha256': {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in SOURCES.items()},
        'rho_reference_rows': [{'zero_based_index': i, 'ensembl_id': row[0], 'symbol': row[1]}
                               for i, row in enumerate(rows) if row[1] in ['RHOXF2', 'RHOXF2B']],
        'rho_chosen': {k: [r for r in v if r['gene'] in ['RHOXF2', 'RHOXF2B']] for k, v in maps.items()},
        'mapping': mapping,
    }
    (OUT / 'METADATA_AUDIT.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ['status', 'targets', 'reference_features', 'rna_response_arrays_accessed']}))


if __name__ == '__main__':
    main()
