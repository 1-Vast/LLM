"""Frozen label-free public-state geometry and continuous support diagnostics."""
import numpy as np


def freeze_reference(public_basal):
    values = np.asarray(public_basal, dtype=float)
    if values.ndim != 2 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("finite_public_basal_reference_required")
    centre = values.mean(0)
    scale = np.sqrt(np.mean((values - centre) ** 2, axis=0))
    scale = np.where(scale > 0, scale, 1.)
    standardized = (values - centre) / scale
    distances = squared_distance(standardized, standardized)
    positive = distances[np.triu_indices(len(values), 1)]
    positive = positive[positive > 0]
    bandwidth = float(np.median(positive)) if len(positive) else 1.
    return dict(centre=centre, scale=scale, bandwidth_sq=bandwidth,
                reference_standardized=standardized, public_context_count=len(values),
                degenerate_reference=not bool(len(positive)))


def squared_distance(left, right):
    left, right = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    return np.maximum(np.square(left).sum(1)[:, None] + np.square(right).sum(1)[None, :]
                      - 2 * left @ right.T, 0.)


def standardize(values, reference):
    values = np.asarray(values, dtype=float)
    if values.shape[-1] != len(reference["centre"]) or not np.isfinite(values).all():
        raise ValueError("finite_matched_public_state_required")
    return (values - reference["centre"]) / reference["scale"]


def cell_kernel(history_basal, target_basal, reference):
    history = standardize(history_basal, reference)
    target = standardize(target_basal, reference).reshape(1, -1)
    gram = np.exp(-squared_distance(history, history) / (2 * reference["bandwidth_sq"]))
    weights = np.exp(-squared_distance(history, target)[:, 0] / (2 * reference["bandwidth_sq"]))
    return gram, weights


def assess(history_basal, target_basal, reference):
    history = standardize(history_basal, reference)
    target = standardize(target_basal, reference).reshape(1, -1)
    distances = squared_distance(history, target)[:, 0]
    weights = np.exp(-distances / (2 * reference["bandwidth_sq"]))
    weight_square_sum = float(weights @ weights)
    n_eff = float(weights.sum() ** 2 / weight_square_sum) if weight_square_sum > 0 else 0.
    ratio = float(distances.min() / reference["bandwidth_sq"]) if len(distances) else None
    support_factor = n_eff / (n_eff + 4.)
    distance_factor = 1. / (1. + ratio) if ratio is not None else 0.
    return dict(n_eff=n_eff, support_factor=support_factor, distance_ratio=ratio,
                distance_factor=distance_factor, weight=support_factor * distance_factor,
                weights=weights.tolist())
