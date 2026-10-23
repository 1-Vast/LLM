"""Independent saved-output arithmetic, no original diagnostic rerun."""
import itertools
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'log/20261023/reciprocity_resolution'
r = json.loads((OUT / 'RESULT.json').read_text())
with np.load(OUT / 'RESPONSE_MATRIX.npz') as z:
    a, genes = z['response'], z['genes'].tolist()
pairs = json.loads((OUT / 'PAIRS.json').read_text())
assert a.shape == (103, 103) and len(genes) == len(set(genes)) == 103
assert len(pairs) == 5253
opposite = onezero = 0
triangles, equal_sign_triangle_products, unequal_sign_triangle_products = [], 0, 0
for row, (i, j) in zip(pairs, itertools.combinations(range(103), 2)):
    x, y = float(a[i, j]), float(a[j, i])
    assert row['i'] == i and row['j'] == j and row['gene_i'] == genes[i] and row['gene_j'] == genes[j]
    assert row['R_ij'] == x and row['R_ji'] == y
    opposite += x * y < 0
    onezero += (x == 0) != (y == 0)
for i, j, k in itertools.combinations(range(103), 3):
    vals = [a[i, j], a[j, k], a[k, i], a[j, i], a[k, j], a[i, k]]
    if all(abs(v) > 1e-12 for v in vals):
        p, q = np.prod(vals[:3]), np.prod(vals[3:])
        triangles.append(abs(p-q)/(abs(p)+abs(q)))
        equal_sign_triangle_products += np.sign(p) == np.sign(q)
        unequal_sign_triangle_products += np.sign(p) != np.sign(q)
assert opposite == r['exact_opposite_sign_pairs'] == 2498
assert onezero == r['exact_one_sided_zero_pairs'] == 292
assert np.count_nonzero(np.diag(a) <= 0) == r['exact_nonpositive_diagonal'] == 2
assert len(triangles) == r['fully_nonzero_triangles']
assert np.allclose(np.quantile(triangles, [0, .25, .5, .75, 1]), r['triangle_normalized_defect_quantiles'], rtol=0, atol=1e-15)
report = {'status': 'SAVED_ARITHMETIC_PASS', 'opposite_sign_pairs': int(opposite),
          'one_sided_exact_zero_pairs': int(onezero),
          'nonpositive_diagonal_targets': [genes[i] for i in np.where(np.diag(a) <= 0)[0]],
          'nonpositive_diagonal_values': np.diag(a)[np.diag(a) <= 0].tolist(),
          'eligible_triangles': len(triangles), 'triangle_products_equal_sign': int(equal_sign_triangle_products),
          'triangle_products_unequal_sign': int(unequal_sign_triangle_products),
          'triangles_exact_normalized_defect_one': int(np.count_nonzero(np.array(triangles) == 1)),
          'original_RNA_features_read': False, 'new_function_values_read': 0,
          'diagnostic_rerun': False, 'saved_matrix_arithmetic_only': True}
(OUT / 'scope/SAVED_ARITHMETIC.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
