"""Independent saved-matrix arithmetic and local artifact continuity, no refit."""
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/reciprocity_resolution'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    identity = json.loads((OUT / 'IDENTITY.json').read_text())
    result = json.loads((OUT / 'RESULT.json').read_text())
    data = np.load(OUT / 'RESPONSE_MATRIX.npz')
    matrix = data['response']
    assert matrix.shape == (103, 103) and data['genes'].tolist() == identity['targets']
    assert np.isfinite(matrix).all()
    for name, expected in identity['input_hashes'].items():
        assert digest(ROOT / name) == expected
    pairs = json.loads((OUT / 'PAIRS.json').read_text())
    assert len(pairs) == 5253
    assert {(r['i'], r['j']) for r in pairs} == set(itertools.combinations(range(103), 2))
    exact_opposite = exact_onezero = 0
    for row in pairs:
        i, j = row['i'], row['j']
        a, b = matrix[i, j], matrix[j, i]
        assert row['gene_i'] == identity['targets'][i] and row['gene_j'] == identity['targets'][j]
        assert row['R_ij'] == a and row['R_ji'] == b
        opposite = bool(a != 0 and b != 0 and np.sign(a) != np.sign(b))
        onezero = bool((a == 0) != (b == 0))
        assert row['exact_opposite_sign'] == opposite and row['exact_one_sided_zero'] == onezero
        exact_opposite += opposite
        exact_onezero += onezero
    assert result['exact_opposite_sign_pairs'] == exact_opposite
    assert result['exact_one_sided_zero_pairs'] == exact_onezero
    assert result['exact_nonpositive_diagonal'] == int((matrix.diagonal() <= 0).sum())
    assert result['status'] == ('EXACT_DECLARED_INTERFACE_INCOMPATIBLE' if exact_opposite or exact_onezero or (matrix.diagonal() <= 0).any() else 'NECESSARY_SIGN_CHECKS_ONLY_NO_SUFFICIENCY')
    defects = []
    for i, j, k in itertools.combinations(range(103), 3):
        values = [matrix[i, j], matrix[j, k], matrix[k, i], matrix[j, i], matrix[k, j], matrix[i, k]]
        if all(abs(v) > 1e-12 for v in values):
            p = values[0] * values[1] * values[2]
            q = values[3] * values[4] * values[5]
            defects.append(abs(p - q) / (abs(p) + abs(q)))
    assert result['fully_nonzero_triangles'] == len(defects)
    assert np.allclose(np.quantile(defects, [0, .25, .5, .75, 1]), result['triangle_normalized_defect_quantiles'], rtol=0, atol=1e-14)
    for folder, filename in [('identity', 'INDEPENDENT_SEAL.json'), ('scope', 'INDEPENDENT_SEAL.json'),
                             ('identity', 'RESULT_REVIEW_SEAL.json'), ('scope', 'RESULT_SEAL.json')]:
        seal = json.loads((OUT / folder / filename).read_text())
        entries = seal.get('files', seal)
        for name, expected in entries.items():
            assert digest(ROOT / name) == expected
        for name in ['CROSS.md', 'RESULT_REVIEW.md', 'RESULT_CROSS.md']:
            assert (OUT / folder / name).is_file()
    previous = json.loads((ROOT / 'log/20261023/intervention_constraint/VERIFICATION.json').read_text())
    drift = [name for name, expected in previous['files'].items() if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
    assert not drift, drift
    report = {'status': 'PASS_LOCAL', 'targets': 103, 'saved_coordinates_checked': 10609, 'reciprocal_pairs_checked': 5253,
              'triangles_checked': len(defects), 'independent_report_seals_checked': 4,
              'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
              'scope': 'Exact saved-number arithmetic and local continuity, not biological significance, causality or global provenance repair'}
    (OUT / 'AUDIT.json').write_text(json.dumps(report, indent=2))
    files = {}
    for folder in [OUT, Path(__file__).resolve().parent]:
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path.name != 'VERIFICATION.json':
                files[path.relative_to(ROOT).as_posix()] = digest(path)
    (OUT / 'VERIFICATION.json').write_text(json.dumps({**report, 'files': files}, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
