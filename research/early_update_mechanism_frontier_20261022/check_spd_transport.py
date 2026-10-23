"""Synthetic exact-operation and opposite-gradient checks; no biological I/O."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/early_update_mechanism/frontier'


def softplus(v):
    return np.logaddexp(0, v)


def ordinary_step(a, gm, v, b, eta):
    return a - eta * (softplus(v) * gm + b @ (b.T @ gm))


def main():
    target = OUT / 'SPD_FALSIFIER_RESULT.json'
    assert not target.exists()
    protocol = OUT / 'SPD_FALSIFIER_PROTOCOL.md'
    assert protocol.exists()
    opposite = []
    for seed in range(1701, 1706):
        rng = np.random.default_rng(seed)
        g, v, b = rng.normal(size=8), rng.normal(size=8), rng.normal(size=(8, 2))
        p = np.diag(softplus(v)) + b @ b.T
        eta = .25 / np.linalg.eigvalsh(p)[-1]
        before = float(.5 * g @ g)
        step = -eta * p @ g
        signed_step = eta * g
        molecule = lambda a: float(.5 * (a + g) @ (a + g))
        function = lambda a: float(.5 * (a - g) @ (a - g))
        record = {'seed': seed, 'eta': eta, 'initial_both_losses': before,
                  'spd_molecular_loss': molecule(step), 'spd_functional_loss': function(step),
                  'signed_molecular_loss': molecule(signed_step), 'signed_functional_loss': function(signed_step),
                  'query_directional_derivative': float(g @ p @ g)}
        assert record['spd_molecular_loss'] < before < record['spd_functional_loss']
        assert record['signed_functional_loss'] < before < record['signed_molecular_loss']
        assert record['query_directional_derivative'] > 0
        opposite.append(record)
    g, gq = np.array([1., 0]), np.array([-1., 1.])
    p = np.array([[1., 2.], [2., 5.]])
    noncollinear = {'unweighted_dot': float(gq @ g), 'weighted_dot': float(gq @ p @ g),
                   'p_eigenvalues': np.linalg.eigvalsh(p).tolist()}
    assert noncollinear['unweighted_dot'] < 0 < noncollinear['weighted_dot']
    assert min(noncollinear['p_eigenvalues']) > 0
    equivalence = []
    for seed in range(1801, 1806):
        rng = np.random.default_rng(seed)
        a, v, b = rng.normal(size=8), rng.normal(size=8), rng.normal(size=(8, 2))
        molecular_map = rng.normal(size=(10, 8))
        q, observed = rng.normal(size=10), rng.normal(size=10)
        target_value, eta = rng.normal(), .001
        gm = molecular_map.T @ (molecular_map @ a - observed)
        p = np.diag(softplus(v)) + b @ b.T
        candidate = a - eta * p @ gm
        ordinary = ordinary_step(a, gm, v, b, eta)
        step_error = float(np.max(np.abs(candidate - ordinary)))
        functional_map = q @ molecular_map
        gq = functional_map * (functional_map @ candidate - target_value)
        matrix_gradient = -eta * np.outer(gq, gm)
        analytic = np.concatenate([np.diag(matrix_gradient) / (1 + np.exp(-v)),
                                   ((matrix_gradient + matrix_gradient.T) @ b).ravel()])
        flat = np.concatenate([v, b.ravel()])

        def loss(parameters):
            # Ordinary learned-optimizer implementation, independently composed.
            updated = ordinary_step(a, gm, parameters[:8], parameters[8:].reshape(8, 2), eta)
            prediction = q @ (molecular_map @ updated)
            return float(.5 * (prediction - target_value) ** 2)

        epsilon = 1e-6
        numerical = np.empty_like(flat)
        for i in range(len(flat)):
            delta = np.zeros_like(flat)
            delta[i] = epsilon
            numerical[i] = (loss(flat + delta) - loss(flat - delta)) / (2 * epsilon)
        gradient_error = float(np.max(np.abs(analytic - numerical)))
        assert step_error < 1e-12 and gradient_error < 1e-6
        equivalence.append({'seed': seed, 'step_max_absolute_error': step_error,
                            'outer_gradient_max_absolute_error': gradient_error})
    result = {'scope': 'Synthetic mathematical counterexamples; no biological inputs/performance evidence',
              'protocol_sha256': hashlib.sha256(protocol.read_bytes()).hexdigest(),
              'opposite_gradient': opposite, 'negative_dot_noncollinear_counterexample': noncollinear,
              'ordinary_lowrank_meta_step_equivalence': equivalence,
              'all_checks_passed': True, 'biological_files_read': 0, 'api_calls': 0}
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
