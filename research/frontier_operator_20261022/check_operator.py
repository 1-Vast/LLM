"""Synthetic audit of assay-closed functional contrast compression.

No biological file is read. The optimized ordinary reference uses batch Gaussian
conditioning on all acquired observations, independently of sequential updates.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import numpy as np

OUT = Path('D:/MAESTRO/log/20261022/operator_renewal/frontier')


def condition(mean, cov, h, noise, observation):
    cross = cov @ h.T
    innovation = h @ cross + noise
    gain = np.linalg.solve(innovation, cross.T).T
    return mean + gain @ (observation - h @ mean), cov - gain @ cross.T


def score(cov, target, h, noise, cost):
    cross = cov @ h.T
    after = cov - cross @ np.linalg.solve(h @ cross + noise, cross.T)
    before_sign, before_logdet = np.linalg.slogdet(target @ cov @ target.T)
    after_sign, after_logdet = np.linalg.slogdet(target @ after @ target.T)
    assert before_sign > 0 and after_sign > 0
    return .5 * (before_logdet - after_logdet) / cost


def batch_reference(mean0, cov0, rows, observations, noises):
    if not rows:
        return mean0.copy(), cov0.copy()
    indices = np.concatenate(rows)
    noise = np.zeros((len(indices), len(indices)))
    start = 0
    for block in noises:
        stop = start + len(block)
        noise[start:stop, start:stop] = block
        start = stop
    innovation = cov0[np.ix_(indices, indices)] + noise
    cross = cov0[:, indices]
    gain = np.linalg.solve(innovation, cross.T).T
    return (mean0 + gain @ (np.concatenate(observations) - mean0[indices]),
            cov0 - gain @ cross.T)


def main():
    # LP paper's low-variance eigenvector rule, not a reimplementation of training.
    dynamics = np.diag([.99, .1])
    sigma = np.eye(2) - dynamics @ dynamics.T
    _, basis = np.linalg.eigh(sigma)
    candidates = np.array([[0., 0.], [.2, 1.]])
    goal = np.array([0., 1.])
    lp_cost = ((candidates-goal) @ basis[:, :1]) ** 2
    direct_utility = candidates[:, 1]
    assert int(np.argmin(lp_cost)) == 0
    assert int(np.argmax(direct_utility)) == 1

    prior = np.array([[1., .9], [.9, 1.]])
    reporter = np.array([[0., 1.]])
    reporter_mean, _ = condition(np.zeros(2), prior, reporter,
                                 np.array([[.1]]), np.array([1.]))
    assert np.isclose(reporter_mean[0], 9/11)
    naive_functional_mean = 0.  # D H^T=0 discards the reporter.

    errors = dict(mean=0., covariance=0., score=0., batch_mean=0., batch_covariance=0.)
    tasks = []
    checks = 2 + 1
    for seed in range(12):
        rng = np.random.default_rng(seed)
        p = [48, 96][seed % 2]
        utility_count, assay_count = 3, 6
        raw = rng.normal(size=(p, p)) / np.sqrt(p)
        cov = raw @ raw.T + .2*np.eye(p)
        mean = rng.normal(size=p)
        target = rng.normal(size=(utility_count, p)) / np.sqrt(p)
        assays = rng.normal(size=(assay_count, p)) / np.sqrt(p)
        z = np.vstack([target, assays])
        small_mean, small_cov = z @ mean, z @ cov @ z.T
        initial_mean, initial_cov = small_mean.copy(), small_cov.copy()
        small_target = np.eye(len(z))[:utility_count]
        truth = rng.multivariate_normal(mean, cov)
        available = list(range(3))
        selected, rows, observations, noises = [], [], [], []
        for step in range(3):
            full_scores, small_scores, batch_scores = [], [], []
            batch_mean, batch_cov = batch_reference(initial_mean, initial_cov, rows, observations, noises)
            for query in available:
                indices = utility_count + np.array([2*query, 2*query+1])
                h = assays[2*query:2*query+2]
                hsmall = np.eye(len(z))[indices]
                # Shared control induces positively correlated errors.
                noise = .25*np.eye(2) + .1*np.ones((2, 2))
                cost = 3
                full_scores.append(score(cov, target, h, noise, cost))
                small_scores.append(score(small_cov, small_target, hsmall, noise, cost))
                batch_scores.append(score(batch_cov, small_target, hsmall, noise, cost))
            errors['score'] = max(errors['score'], float(np.max(np.abs(np.array(full_scores)-small_scores))),
                                  float(np.max(np.abs(np.array(batch_scores)-small_scores))))
            assert np.allclose(full_scores, small_scores, atol=1e-9, rtol=1e-9)
            assert np.allclose(batch_scores, small_scores, atol=1e-9, rtol=1e-9)
            assert np.argmax(full_scores) == np.argmax(small_scores) == np.argmax(batch_scores)
            query = available.pop(int(np.argmax(full_scores)))
            indices = utility_count + np.array([2*query, 2*query+1])
            h = assays[2*query:2*query+2]
            hsmall = np.eye(len(z))[indices]
            noise = .25*np.eye(2) + .1*np.ones((2, 2))
            observation = h @ truth + rng.multivariate_normal(np.zeros(2), noise)
            mean, cov = condition(mean, cov, h, noise, observation)
            small_mean, small_cov = condition(small_mean, small_cov, hsmall, noise, observation)
            rows.append(indices)
            observations.append(observation)
            noises.append(noise)
            batch_mean, batch_cov = batch_reference(initial_mean, initial_cov, rows, observations, noises)
            errors['mean'] = max(errors['mean'], float(np.max(np.abs(z @ mean-small_mean))))
            errors['covariance'] = max(errors['covariance'], float(np.max(np.abs(z @ cov @ z.T-small_cov))))
            errors['batch_mean'] = max(errors['batch_mean'], float(np.max(np.abs(batch_mean-small_mean))))
            errors['batch_covariance'] = max(errors['batch_covariance'], float(np.max(np.abs(batch_cov-small_cov))))
            assert np.allclose(z @ mean, small_mean, atol=1e-9, rtol=1e-9)
            assert np.allclose(z @ cov @ z.T, small_cov, atol=1e-9, rtol=1e-9)
            assert np.allclose(batch_mean, small_mean, atol=1e-9, rtol=1e-9)
            assert np.allclose(batch_cov, small_cov, atol=1e-9, rtol=1e-9)
            nominations = [int(np.argmax(np.r_[0., values])) for values in
                           [target @ mean, small_mean[:utility_count], batch_mean[:utility_count]]]
            assert nominations[0] == nominations[1] == nominations[2]
            checks += 8
            selected.append(query)
        tasks.append(dict(seed=seed, parameter_dimension=p, compiled_dimension=len(z),
                          selected_bundles=selected, terminal_nomination=nominations[0],
                          full_covariance_entries=p*p, compiled_covariance_entries=len(z)**2,
                          ordinary_cached_covariance_entries=len(z)**2,
                          paid_bundle_cost=9))
    result = dict(utc=datetime.now(timezone.utc).isoformat(),
                  evidence='synthetic only, no biological outcomes read',
                  git_head='ed2e360093d25e577ea02a5011d54d13b32ec8f1',
                  python=platform.python_version(), numpy=np.__version__,
                  code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  assertions=checks, tasks=tasks, maximum_errors=errors,
                  lp_witness=dict(sigma=sigma.tolist(), costs=lp_cost.ravel().tolist(),
                                  lp_choice=0, direct_function_choice=1),
                  correlated_reporter=dict(full_posterior_function=float(reporter_mean[0]),
                                           naive_function_only=naive_functional_mean),
                  outcome='Compression exact; optimized ordinary cache has identical dimension, policy and posterior.')
    output = OUT / 'OPERATION_RESULT.json'
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
