"""Conditional cell-level uncertainty audit for an authenticated RNA scalar.

These quantities describe sampled control cells under an exchangeability
assumption. They do not estimate independent cultures or biological/batch
variance fractions, and must not be added again to observed residual moments.
"""
import numpy as np


def _interval(values):
    values = np.asarray(values, dtype=float)
    return np.quantile(values, [.025, .975]).tolist() if len(values) else None


def audit_groups(groups, weights, metadata, bootstrap_draws=2000, seed=20261009):
    """Keep each cell's gene vector intact during the within-group bootstrap.

    The supplied weights are the complete endpoint definition: no normalization,
    independent-gene assumption, added noise or extra variance term is applied.
    Each group uses its actual number of observed cells, including n!=32.
    """
    weights = np.asarray(weights, dtype=float)
    if weights.ndim != 1 or not len(weights) or not np.isfinite(weights).all():
        raise ValueError("finite_endpoint_weight_vector_required")
    if len(groups) != len(metadata) or not len(groups):
        raise ValueError("one_metadata_record_per_nonempty_group_required")
    if not isinstance(bootstrap_draws, int) or bootstrap_draws < 1:
        raise ValueError("positive_bootstrap_draw_count_required")
    rows = []
    for position, (values, source) in enumerate(zip(groups, metadata)):
        values = np.asarray(values, dtype=float)
        if values.ndim != 2 or values.shape[1] != len(weights) or len(values) < 2 or not np.isfinite(values).all():
            raise ValueError("at_least_two_finite_axis_matched_cells_required")
        n = len(values)
        shifted_values = values - values[0]
        shifted_scalar = shifted_values @ weights
        scalar = shifted_scalar + float(values[0] @ weights)
        # Translation leaves variance unchanged and gives exact zero for a
        # constant scalar, avoiding roundoff in its floating-point mean.
        scalar_variance = float(np.var(shifted_scalar, ddof=1))
        diagonal_variance = float(np.sum(np.var(shifted_values, axis=0, ddof=1) * weights ** 2))
        full_mean_variance, diagonal_mean_variance = scalar_variance / n, diagonal_variance / n
        rng = np.random.default_rng(np.random.SeedSequence([seed, position]))
        indices = rng.integers(0, n, size=(bootstrap_draws, n))
        sampled = shifted_values[indices]
        bootstrap_scalar = scalar[indices]
        bootstrap_full = np.var(shifted_scalar[indices], axis=1, ddof=1) / n
        bootstrap_diagonal = np.sum(np.var(sampled, axis=1, ddof=1) * weights ** 2, axis=1) / n
        positive = bootstrap_diagonal > 0
        rows.append(dict(group_index=position, metadata=dict(source), cells=n, genes=len(weights),
            scalar_mean=float(scalar.mean()), scalar_sample_variance=scalar_variance,
            scalar_sample_mean_variance=full_mean_variance,
            diagonal_only_scalar_sample_variance=diagonal_variance,
            diagonal_only_sample_mean_variance=diagonal_mean_variance,
            covariance_sample_mean_variance=full_mean_variance - diagonal_mean_variance,
            full_to_diagonal_ratio=full_mean_variance / diagonal_mean_variance if diagonal_mean_variance > 0 else None,
            bootstrap_percentile_95=dict(scalar_mean=_interval(bootstrap_scalar.mean(1)),
                scalar_sample_mean_variance=_interval(bootstrap_full),
                diagonal_only_sample_mean_variance=_interval(bootstrap_diagonal),
                covariance_sample_mean_variance=_interval(bootstrap_full - bootstrap_diagonal),
                full_to_diagonal_ratio=_interval(bootstrap_full[positive] / bootstrap_diagonal[positive])),
            ratio_defined_bootstrap_draws=int(positive.sum())))
    return dict(groups=rows, endpoint_weights=weights.tolist(), bootstrap_draws=bootstrap_draws, seed=seed,
        bootstrap_unit="A complete gene vector from one cell, resampled only within its registered group.",
        assumption="Conditional exchangeable cells within each group; not independent cultures or biological replicates.",
        limitations="s2/n and bootstrap intervals are conditional sampling diagnostics. Group means cannot identify biological or batch variance fractions. Observed residual covariance already contains measurement variation; do not add this variance twice.")


def select_numerical_tie(losses, costs, complexities, absolute_tolerance=1e-12, relative_tolerance=1e-10):
    """Prospective rule: loss tolerance, then lower cost, simpler model, index.

    This does not alter any existing frozen experiment or selection outcome.
    """
    losses, costs, complexities = [np.asarray(values, dtype=float) for values in (losses, costs, complexities)]
    if losses.ndim != 1 or not len(losses) or costs.shape != losses.shape or complexities.shape != losses.shape:
        raise ValueError("aligned_nonempty_tie_selection_vectors_required")
    if not all(np.isfinite(values).all() for values in (losses, costs, complexities)):
        raise ValueError("finite_tie_selection_values_required")
    if absolute_tolerance < 0 or relative_tolerance < 0:
        raise ValueError("nonnegative_tie_tolerances_required")
    best = float(losses.min())
    tolerance = absolute_tolerance + relative_tolerance * abs(best)
    eligible = np.flatnonzero(losses <= best + tolerance).tolist()
    selected = min(eligible, key=lambda index: (costs[index], complexities[index], index))
    return dict(selected=selected, eligible=eligible, best_loss=best, tolerance=tolerance,
                selected_loss=float(losses[selected]), prospective_only=True)
