"""Fixed-menu Gaussian feedback; outcomes enter only through paid buy(index)."""
import numpy as np


def fit_joint(error_B, error_A, available):
    """Zero-mean error second moment, complete contexts, fixed diagonal shrink."""
    complete = available.all(axis=1) & np.isfinite(error_B).all(axis=1) & np.isfinite(error_A).all(axis=1)
    count = int(complete.sum())
    if count < 2:
        raise ValueError("joint_feedback_needs_two_complete_contexts")
    errors = np.concatenate([error_B[complete], error_A[complete]], axis=1)
    moment = errors.T @ errors / count
    covariance = .5 * moment + .5 * np.diag(np.diag(moment))
    covariance += np.eye(len(covariance)) * 1e-12
    return covariance, count


def common_joint(covariance, obsvar):
    """Embed original A=B+offset+independent-noise model in [B,A] order."""
    return np.block([[covariance, covariance],
                     [covariance, covariance + np.diag(obsvar)]])


def condition(mean, covariance, index_A, value):
    coordinate = len(mean) // 2 + index_A
    variance = covariance[coordinate, coordinate]
    if variance <= 0:
        return mean.copy(), covariance.copy()
    column = covariance[:, coordinate].copy()
    updated_mean = mean + column / variance * (value - mean[coordinate])
    updated_cov = covariance - np.outer(column, column) / variance
    return updated_mean, .5 * (updated_cov + updated_cov.T)


def top5(mean):
    return np.lexsort((np.arange(len(mean)), -mean))[:5].tolist()


def replay(mean_B, offset, joint_cov, buy, policy="kg", schedule=None):
    """Eight unique paid A reveals, then commit five B indices without reading B."""
    n = len(mean_B)
    mean = np.concatenate([mean_B, mean_B + offset])
    covariance = joint_cov.copy()
    if n < 8 or covariance.shape != (2*n, 2*n) or not np.isfinite(mean).all() or not np.isfinite(covariance).all():
        raise ValueError("invalid_joint_feedback_inputs")
    if schedule is None and policy == "boundary":
        order = np.lexsort((np.arange(n), -mean_B))
        midpoint = .5 * (mean_B[order[4]] + mean_B[order[5]])
        schedule = np.lexsort((np.arange(n), abs(mean_B-midpoint)))[:8].tolist()
    if schedule is not None:
        schedule = list(schedule)
        if len(schedule) != 8 or len(set(schedule)) != 8 or any(i < 0 or i >= n for i in schedule):
            raise ValueError("schedule_must_have_eight_unique_menu_indices")
    elif policy != "kg":
        raise ValueError("unknown_feedback_policy")
    normals = np.random.default_rng(20261008).standard_normal(64)
    purchased, history = [], []
    for step in range(8):
        if schedule is None:
            current = mean[top5(mean[:n])].sum()
            gains = []
            for i in range(n):
                if i in purchased:
                    continue
                variance = max(covariance[n+i, n+i], 0.)
                direction = covariance[:n, n+i] / np.sqrt(variance) if variance > 0 else np.zeros(n)
                draws = mean[None, :n] + normals[:, None] * direction[None]
                gain = np.partition(draws, n-5, axis=1)[:, -5:].sum(1).mean() - current
                gains.append((float(gain), -i))
            _, negative_index = max(gains)
            index = -negative_index
        else:
            index = schedule[step]
        # Record the purchase request and cost before the callback releases A.
        row = dict(step=step, purchased_A=index, cumulative_A_cost=step+1)
        history.append(row)
        predicted, variance = mean[n+index], max(covariance[n+index, n+index], 0.)
        value = float(buy(index))
        if not np.isfinite(value):
            raise ValueError("paid_A_returned_nonfinite_outcome")
        row.update(predicted_A=float(predicted), variance_A=float(variance), observed_A=value,
                   innovation_z=float((value-predicted)/np.sqrt(variance)) if variance > 0 else None)
        mean, covariance = condition(mean, covariance, index, value)
        purchased.append(index)
    selected = top5(mean[:n])
    history.append(dict(committed_B=selected, cost_after_five_B=13))
    return dict(selected=selected, history=history, purchased_A=purchased, cost=13,
                posterior_mean_B=mean[:n], posterior_cov_B=covariance[:n, :n])
