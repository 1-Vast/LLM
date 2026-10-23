"""Small conventional surface-completion menu; no target queries as inputs."""
import numpy as np

RIDGES = (.01, .1, 1.)
BANDWIDTHS = (.5, 2.)
ALPHAS = (.1, .5, .9)
MENU = ['nci', 'mean'] + [f'ridge:{v}' for v in RIDGES] + [
    f'rbf:{b}:{v}' for b in BANDWIDTHS for v in RIDGES] + [f'gaussian:{a}' for a in ALPHAS] + ['mix']


def expectation(solo):
    a = np.repeat(solo[..., :3], 3, axis=-1)
    b = np.tile(solo[..., 3:], (*([1] * (solo.ndim - 1)), 3))
    return np.where((a < 0) | (b < 0), np.minimum(a, b), np.minimum(a, 1) * np.minimum(b, 1))


def predict_pair(name, budget, source_solo, source_y, target_solo, target_anchor=None):
    base = expectation(target_solo)
    r = source_y - expectation(source_solo)
    mean = r.mean(axis=0)
    if name == 'nci':
        return base
    if name == 'mean':
        update = 0 if budget == 0 else .5 * (target_anchor - base[:, 8] - mean[8])[:, None]
        return base + mean + update
    if name == 'mix':
        return .5 * (predict_pair('ridge:0.1', budget, source_solo, source_y, target_solo, target_anchor)
                     + predict_pair('gaussian:0.5', budget, source_solo, source_y, target_solo, target_anchor))
    x, t = source_solo, target_solo
    if budget:
        x = np.column_stack((x, r[:, 8]))
        t = np.column_stack((t, target_anchor - base[:, 8]))
    center = x.mean(axis=0)
    scale = np.maximum(x.std(axis=0), .05)
    x, t = (x - center) / scale, (t - center) / scale
    n = len(x)
    y = r - mean
    parts = name.split(':')
    if parts[0] == 'ridge':
        lam = float(parts[1])
        beta = np.linalg.solve(x.T @ x / n + (lam + 1e-8) * np.eye(x.shape[1]), x.T @ y / n)
        correction = t @ beta
    elif parts[0] == 'gaussian':
        alpha = float(parts[1])
        cov = x.T @ x / n
        regularized = (1 - alpha) * cov + alpha * np.diag(np.diag(cov)) + 1e-8 * np.eye(x.shape[1])
        beta = np.linalg.solve(regularized, (1 - alpha) * x.T @ y / n)
        correction = t @ beta
    elif parts[0] == 'rbf':
        bandwidth, lam = float(parts[1]), float(parts[2])
        def kernel(a, b):
            distance = np.mean((a[:, None, :] - b[None, :, :]) ** 2, axis=-1)
            return np.exp(-distance / (2 * bandwidth ** 2))
        beta = np.linalg.solve(kernel(x, x) + (n * lam + 1e-8) * np.eye(n), y)
        correction = kernel(t, x) @ beta
    else:
        raise ValueError(name)
    return base + mean + correction


def predict_catalog(name, budget, source_solo, source_y, target_solo, target_anchor=None,
                    source_study=None, target_study=None):
    result = np.empty((*target_solo.shape[:2], 9))
    counts = []
    for p in range(source_solo.shape[1]):
        if source_study is None:
            result[:, p] = predict_pair(name, budget, source_solo[:, p], source_y[:, p],
                                       target_solo[:, p], None if budget == 0 else target_anchor[:, p])
            counts.append(len(source_solo))
        else:
            for c in range(len(target_solo)):
                mask = source_study[:, p] != target_study[c, p]
                counts.append(int(mask.sum()))
                if mask.sum() < 2:
                    raise ValueError('Fewer than two source cells after same-pair study exclusion')
                result[c:c + 1, p] = predict_pair(name, budget, source_solo[mask, p], source_y[mask, p],
                                                 target_solo[c:c + 1, p], None if budget == 0 else target_anchor[c:c + 1, p])
    assert np.isfinite(result).all()
    return result[..., :8], counts


def select(predictions, truth):
    risks = {name: float(np.mean((pred - truth[..., :8]) ** 2)) for name, pred in predictions.items()}
    return min(risks, key=risks.get), risks
