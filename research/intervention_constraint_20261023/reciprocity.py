"""Necessary compatibility conditions on a fixed endpoint matrix, no model fitting."""
from datetime import datetime, timezone
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/intervention_constraint'
SOURCE = ROOT / 'log/20261022/norman_numeric_qualification/SINGLE_RNA_FEATURES.npz'
SYMBOLS = ROOT / 'log/20261022/norman_functional_contract/data/GSE133344_raw_genes.tsv.gz'
ALIASES = {'C3orf72': 'FOXL2NB', 'C19orf26': 'CBARP', 'KIAA1804': 'RP5-862P8.2', 'RHOXF2': 'RHOXF2B'}
TOL = 1e-12


def examine(matrix):
    """Rows=response coordinates; columns=perturbed target, same identity order."""
    assert matrix.ndim == 2 and matrix.shape[0] == matrix.shape[1] and np.isfinite(matrix).all()
    n = len(matrix)
    pairs, adjacency = [], [[] for _ in range(n)]
    for i, j in itertools.combinations(range(n), 2):
        a, b = float(matrix[i, j]), float(matrix[j, i])
        za, zb = abs(a) <= TOL, abs(b) <= TOL
        same = not za and not zb and np.sign(a) == np.sign(b)
        pairs.append({'i': i, 'j': j, 'R_ij': a, 'R_ji': b, 'same_nonzero_sign': bool(same),
                      'exact_opposite_sign': bool(a != 0 and b != 0 and np.sign(a) != np.sign(b)),
                      'exact_one_sided_zero': bool((a == 0) != (b == 0)),
                      'opposite_nonzero_sign': bool(not za and not zb and not same),
                      'one_sided_numerical_zero': bool(za != zb), 'both_numerical_zero': bool(za and zb)})
        if same:
            # R_ij/s_j = R_ji/s_i implies log(s_j)-log(s_i)=log|R_ij/R_ji|.
            ratio = float(np.log(abs(a)) - np.log(abs(b)))
            adjacency[i].append((j, ratio))
            adjacency[j].append((i, -ratio))
    potential = np.full(n, np.nan)
    components = 0
    for start in range(n):
        if np.isfinite(potential[start]):
            continue
        components += 1
        potential[start] = 0.
        stack = [start]
        while stack:
            i = stack.pop()
            for j, ratio in adjacency[i]:
                if not np.isfinite(potential[j]):
                    potential[j] = potential[i] + ratio
                    stack.append(j)
    defects = [abs((potential[j] - potential[i]) - ratio)
               for i in range(n) for j, ratio in adjacency[i] if i < j]
    cycles = []
    for i, j, k in itertools.combinations(range(n), 3):
        factors = [matrix[i, j], matrix[j, k], matrix[k, i], matrix[j, i], matrix[k, j], matrix[i, k]]
        if all(abs(v) > TOL for v in factors):
            p, q = float(np.prod(factors[:3])), float(np.prod(factors[3:]))
            cycles.append(abs(p - q) / (abs(p) + abs(q)))
    result = {'targets': n, 'reciprocal_pairs': len(pairs),
              'exact_nonpositive_diagonal': int(np.sum(np.diag(matrix) <= 0)),
              'exact_opposite_sign_pairs': sum(p['exact_opposite_sign'] for p in pairs),
              'exact_one_sided_zero_pairs': sum(p['exact_one_sided_zero'] for p in pairs),
              'positive_diagonal': int(np.sum(np.diag(matrix) > TOL)),
              'nonpositive_or_numerical_zero_diagonal': int(np.sum(np.diag(matrix) <= TOL)),
              'same_sign_pairs': sum(p['same_nonzero_sign'] for p in pairs),
              'opposite_sign_pairs': sum(p['opposite_nonzero_sign'] for p in pairs),
              'one_sided_numerical_zero_pairs': sum(p['one_sided_numerical_zero'] for p in pairs),
              'both_numerical_zero_pairs': sum(p['both_numerical_zero'] for p in pairs),
              'fully_nonzero_triangles': len(cycles),
              'triangle_normalized_defect_quantiles': np.quantile(cycles, [0, .25, .5, .75, 1]).tolist() if cycles else [],
              'same_sign_graph_components': components,
              'same_sign_graph_max_log_ratio_cycle_defect': max(defects, default=0.),
              'tolerance': TOL, 'tolerance_scope': 'numerical-zero only, not biological significance'}
    return result, pairs


def identity():
    # This command never loads response values.
    with np.load(SOURCE) as stored:
        genes = stored['genes'].tolist()
    with gzip.open(SYMBOLS, 'rt') as stream:
        rows = [line.rstrip('\n').split('\t') for line in stream]
    assert len(rows) == 33694 and all(len(row) == 2 for row in rows)
    names = [ALIASES.get(row[1], row[1]) for row in rows]
    mapping = {gene: [i for i, symbol in enumerate(names) if symbol == gene] for gene in genes}
    assert len(genes) == len(set(genes)) == 103
    report = {'status': 'PASS' if all(len(v) == 1 for v in mapping.values()) else 'STOP_IDENTITY',
              'targets': genes, 'feature_indices': mapping,
              'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'symbols_sha256': hashlib.sha256(SYMBOLS.read_bytes()).hexdigest(),
              'response_values_loaded': 0}
    (OUT / 'RECIPROCITY_IDENTITY.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ['status', 'response_values_loaded']}))


def main():
    report = json.loads((OUT / 'RECIPROCITY_IDENTITY.json').read_text())
    assert report['status'] == 'PASS' and hashlib.sha256(SOURCE.read_bytes()).hexdigest() == report['source_sha256']
    assert not (OUT / 'RECIPROCITY_RESULT.json').exists(), 'Completed gate must not be repeated automatically'
    for path in ['constructive/PREFIT.md', 'biology/PREFIT_RECIPROCITY.md']:
        assert (OUT / path).is_file()
    with np.load(SOURCE) as stored:
        assert stored['genes'].tolist() == report['targets']
        features = stored['features']
    indices = [report['feature_indices'][gene][0] for gene in report['targets']]
    matrix = features[:, indices].T
    result, pairs = examine(matrix)
    np.savez_compressed(OUT / 'RECIPROCITY_MATRIX.npz', genes=np.array(report['targets']), response=matrix)
    for pair in pairs:
        pair['gene_i'], pair['gene_j'] = report['targets'][pair['i']], report['targets'][pair['j']]
    (OUT / 'RECIPROCITY_PAIRS.json').write_text(json.dumps(pairs))
    result.update(utc=datetime.now(timezone.utc).isoformat(),
                  status='EXACT_INTERFACE_INCOMPATIBLE' if result['exact_opposite_sign_pairs'] or result['exact_one_sided_zero_pairs'] or result['exact_nonpositive_diagonal'] else 'NECESSARY_SIGN_GATE_ONLY_NO_SUFFICIENCY',
                  new_function_labels_loaded=0, protected_values_loaded=0,
                  scope='Declared exact positive-conjugate quadratic endpoint interface, not generic cellular potential biology or prediction performance')
    (OUT / 'RECIPROCITY_RESULT.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    identity() if sys.argv[1:] == ['identity'] else main()
