"""One descriptive projection of already exposed contrasts; not a predictor."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/contrast_transport_mechanism'
PRIOR = ROOT / 'log/20261023/replicated_contrast'
RTOL = 256 * np.finfo(float).eps


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_design(gene, guide, labels):
    assert gene.shape[0] == guide.shape[0] and gene.shape[0] % 2 == 0
    assert np.isfinite(gene).all() and np.isfinite(guide).all()
    assert np.allclose(gene.sum(axis=1), 2, rtol=0, atol=1e-14)
    gi = {g: i for i, g in enumerate(labels['role_gene'])}
    assert gene.shape[1] == len(gi)
    assert guide.shape[1] == len(labels['role_guide'])
    children = {g: [] for g in gi}
    for j, h in enumerate(labels['role_guide']):
        g = labels['guide_parent'][h]
        children[g].append(j)
        np.testing.assert_allclose(3 * guide[:, j], gene[:, gi[g]], rtol=0, atol=1e-14)
    assert all(len(v) == 3 for v in children.values())
    return np.column_stack((np.ones(gene.shape[0] // 2), gene[::2] - gene[1::2]))


def basis(design):
    with threadpool_limits(limits=1):
        u, s, _ = np.linalg.svd(design, full_matrices=False)
    tolerance = max(design.shape) * np.finfo(float).eps * s[0]
    return u[:, s > tolerance], s, tolerance


def correlation(values, reference):
    centered = values - values.mean(axis=0)
    norms = np.linalg.norm(centered, axis=0)
    floor = RTOL * np.maximum(np.linalg.norm(reference, axis=0), np.finfo(float).tiny)
    if np.any(norms <= floor):
        return None
    return float(centered[:, 0] @ centered[:, 1] / np.prod(norms))


def decompose(design, values):
    assert values.shape == (len(design), 2) and np.isfinite(values).all()
    q, singular, tolerance = basis(design)
    additive = q @ (q.T @ values)
    residual = values - additive
    centered = values - values.mean(axis=0)
    ac = additive - additive.mean(axis=0)
    total = float(centered[:, 0] @ centered[:, 1])
    add = float(ac[:, 0] @ ac[:, 1])
    rem = float(residual[:, 0] @ residual[:, 1])
    covariance_floor = RTOL * max(float(np.prod(np.linalg.norm(centered, axis=0))), np.finfo(float).tiny)
    defined = abs(total) > covariance_floor
    residual_fraction = rem / total if defined else None
    residual_corr = correlation(residual, values)
    result = dict(contrasts=len(values), nuisance_columns=design.shape[1], rank=q.shape[1],
                  residual_dimension=len(values)-q.shape[1], svd_tolerance=float(tolerance),
                  total_cross_product=total, additive_cross_product=add, residual_cross_product=rem,
                  additive_fraction=add/total if defined else None, residual_fraction=residual_fraction,
                  original_correlation=correlation(values, values),
                  additive_correlation=correlation(additive, values), residual_correlation=residual_corr,
                  original_rms=np.sqrt(np.mean(values**2, axis=0)).tolist(),
                  additive_rms=np.sqrt(np.mean(additive**2, axis=0)).tolist(),
                  residual_rms=np.sqrt(np.mean(residual**2, axis=0)).tolist(),
                  orthogonality_error=float(np.max(np.abs(q.T @ residual))),
                  cross_product_decomposition_error=abs(total-add-rem),
                  residual_mean=np.mean(residual, axis=0).tolist(),
                  screen=bool(total > covariance_floor and residual_corr is not None and
                              residual_corr >= .5 and residual_fraction is not None and residual_fraction >= .25))
    scale = max(float(np.linalg.norm(values)**2), np.finfo(float).tiny)
    assert result['cross_product_decomposition_error'] <= RTOL * scale
    return result, dict(design=design, basis=q, singular_values=singular, delta=values,
                        additive=additive, residual=residual)


def main():
    assert not (OUT / 'PROJECTION_RESULT.json').exists()
    freeze = json.loads((OUT / 'EXECUTION_FREEZE.json').read_text())
    for name, expected in freeze['files'].items():
        assert sha(ROOT / name) == expected, name
    begin = time.perf_counter()
    identity = np.load(OUT / 'source/IDENTITY_NUISANCE_MATRICES.npz')
    labels = json.loads((OUT / 'source/IDENTITY_NUISANCE_LABELS.json').read_text())
    design = make_design(identity['role_gene'], identity['role_guide'], labels)
    with np.load(PRIOR / 'CONTRAST_ARRAYS.npz') as saved:
        values = saved['delta']
    assert values.shape == (512, 2)
    result, arrays = decompose(design, values)
    np.savez_compressed(OUT / 'PROJECTION_ARRAYS.npz', **arrays)
    result.update(utc=datetime.now(timezone.utc).isoformat(), seconds=time.perf_counter()-begin,
                  arrays_sha256=sha(OUT / 'PROJECTION_ARRAYS.npz'),
                  scope='Exposed-data descriptive position-gene/guide projection, not GI or heldout prediction',
                  goal='ACTIVE / NOT_ACHIEVED')
    (OUT / 'PROJECTION_RESULT.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
