"""Research-only exact Monte Carlo top-m gain; input directions remain caller-owned."""
import numpy as np


def gains(mean, directions, normals, m):
    """Partition each newly owned draw array in place; avoid its full-size copy."""
    current = float(np.sort(mean)[-m:].sum())
    result = []
    for direction in directions:
        draws = mean[None] + normals[:, None] * direction[None]
        draws.partition(len(mean) - m, axis=1)
        result.append(float(draws[:, -m:].sum(1).mean() - current))
    return np.array(result)


def kg_values(belief, m, available, normals):
    current = float(np.sort(belief.mean)[-m:].sum())
    result = {}
    for i in available:
        direction = belief.cov[:, i] / np.sqrt(belief.cov[i, i] + belief.obs_var[i])
        draws = belief.mean[None] + normals[:, None] * direction[None]
        draws.partition(len(belief.mean) - m, axis=1)
        result[i] = float(draws[:, -m:].sum(1).mean() - current)
    return result
