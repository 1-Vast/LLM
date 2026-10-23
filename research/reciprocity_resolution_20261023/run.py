"""Author-label/reference exact join; reuse finite diagnostic, preserve prior STOP."""
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/reciprocity_resolution'
SOURCE = ROOT / 'log/20261022/norman_numeric_qualification/SINGLE_RNA_FEATURES.npz'
SYMBOLS = ROOT / 'log/20261022/norman_functional_contract/data/GSE133344_raw_genes.tsv.gz'
PRIMARY = ROOT / 'log/20261022/norman_functional_contract/root_sources/population.source.txt'
DIAGNOSTIC = ROOT / 'research/intervention_constraint_20261023/reciprocity.py'
spec = importlib.util.spec_from_file_location('original_diagnostic', DIAGNOSTIC)
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity():
    with np.load(SOURCE) as stored:
        genes = stored['genes'].tolist()
    with gzip.open(SYMBOLS, 'rt') as stream:
        rows = [line.rstrip('\n').split('\t') for line in stream]
    assert len(genes) == len(set(genes)) == 103 and len(rows) == 33694
    symbols = [row[1] for row in rows]
    indices = {g: [i for i, symbol in enumerate(symbols) if symbol == g] for g in genes}
    assert all(len(v) == 1 for v in indices.values())
    assert indices['RHOXF2B'] == [14109]
    assert rows[14109] == ['ENSG00000203989', 'RHOXF2B']
    assert rows[14112] == ['ENSG00000131721', 'RHOXF2']
    text = PRIMARY.read_text(encoding='utf-8')
    assert 'This guide lands between RHOXF2 and RHOXF2B' in text
    record = {'status': 'AUTHOR_LABEL_COORDINATE_JOIN_SUPPORTED', 'targets': genes,
              'indices': {g: v[0] for g, v in indices.items()},
              'ensembl_ids': {g: rows[v[0]][0] for g, v in indices.items()},
              'input_hashes': {str(p.relative_to(ROOT)): digest(p) for p in [SOURCE, SYMBOLS, PRIMARY, DIAGNOSTIC]},
              'response_values_loaded': 0,
              'scope': 'Author perturbation labels matched to unchanged exact reference symbols; no physical targeting/force proof'}
    (OUT / 'IDENTITY.json').write_text(json.dumps(record, indent=2))
    print(json.dumps({'status': record['status'], 'targets': len(genes), 'response_values_loaded': 0}))


def main():
    record = json.loads((OUT / 'IDENTITY.json').read_text())
    assert record['status'] == 'AUTHOR_LABEL_COORDINATE_JOIN_SUPPORTED'
    for name, expected in record['input_hashes'].items():
        assert digest(ROOT / name) == expected
    assert not (OUT / 'RESULT.json').exists(), 'Already completed; review saved result rather than rerun'
    for name in ['identity/INDEPENDENT.md', 'scope/INDEPENDENT.md', 'scope/CODE_REVIEW.md']:
        assert (OUT / name).is_file()
    with np.load(SOURCE) as stored:
        assert stored['genes'].tolist() == record['targets']
        features = stored['features']
    assert features.shape == (103, 33694)
    matrix = features[:, [record['indices'][g] for g in record['targets']]].T
    result, pairs = diagnostic.examine(matrix)
    for pair in pairs:
        pair['gene_i'] = record['targets'][pair['i']]
        pair['gene_j'] = record['targets'][pair['j']]
    np.savez_compressed(OUT / 'RESPONSE_MATRIX.npz', genes=np.array(record['targets']), response=matrix)
    (OUT / 'PAIRS.json').write_text(json.dumps(pairs))
    result.update(status='EXACT_DECLARED_INTERFACE_INCOMPATIBLE' if result['exact_nonpositive_diagonal'] or result['exact_opposite_sign_pairs'] or result['exact_one_sided_zero_pairs'] else 'NECESSARY_SIGN_CHECKS_ONLY_NO_SUFFICIENCY',
                  utc=datetime.now(timezone.utc).isoformat(), input_hashes=record['input_hashes'],
                  newly_loaded_single_RNA_values=int(features.size), tested_target_coordinate_values=int(matrix.size),
                  new_function_values_loaded=0, development_values_loaded=0, protected_values_loaded=0,
                  scope='Saved author-label endpoint algebra, not rejection of generic biological potentials or a predictive performance result')
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != 'input_hashes'}, indent=2))


if __name__ == '__main__':
    identity() if sys.argv[1:] == ['identity'] else main()
