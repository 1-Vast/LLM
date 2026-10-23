"""Fixed ordinary predictors for the paid-reference gate; no target preprocessing."""
from copy import deepcopy
from itertools import product
from time import perf_counter

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor


SEED = 20261022
CENTERS = np.array(list(product([0.0, 0.25, 0.5, 0.75, 1.0], repeat=2)))
RESIDUAL_GRID = [{"width": width, "alpha": alpha}
                 for width in (0.1, 0.25, 0.5) for alpha in (0.01, 0.1, 1.0, 10.0)]
DIRECT_GRID = [
    {"model": "extra_trees", "n_estimators": 200, "min_samples_leaf": leaf,
     "max_features": features, "random_state": SEED, "n_jobs": 2}
    for leaf in (5, 20, 50) for features in (0.5, 1.0)
] + [
    {"model": "hist_gradient_boosting", "max_iter": 150, "learning_rate": rate,
     "max_leaf_nodes": leaves, "l2_regularization": 1.0,
     "early_stopping": False, "random_state": SEED}
    for rate in (0.05, 0.1) for leaves in (15, 31, 63)
]
GRIDS = {"effect": deepcopy(RESIDUAL_GRID), "dose": deepcopy(RESIDUAL_GRID),
         "direct": deepcopy(DIRECT_GRID), "combo_direct": deepcopy(DIRECT_GRID)}


def _bliss(effect):
    return effect[:, 0] + effect[:, 1] - effect[:, 0] * effect[:, 1]


def _basis(coordinates, width):
    """25 fixed Gaussians exp(-squared_distance / (2 width^2)) and an intercept."""
    distance = ((coordinates[:, None, :] - CENTERS[None, :, :]) ** 2).sum(axis=2)
    return np.column_stack([np.exp(-distance / (2.0 * width ** 2)), np.ones(len(coordinates))])


def _episode_weights(episode):
    """Equal episode mass, normalized to mean row weight one after label filtering."""
    _, inverse, counts = np.unique(episode, return_inverse=True, return_counts=True)
    return len(episode) / (len(counts) * counts[inverse])


class ResidualModel:
    def __init__(self, coordinate_key, width, coefficients, fit_seconds, solver_fits):
        self.coordinate_key = coordinate_key
        self.width = width
        self.coefficients = coefficients
        self.fit_seconds = fit_seconds
        self.solver_fits = solver_fits

    def predict(self, data, mask):
        idx = np.flatnonzero(mask)
        effect = np.asarray(data["effect"])[idx]
        prediction = _bliss(effect)
        pair = np.asarray(data["pair"])[idx]
        basis = _basis(np.asarray(data[self.coordinate_key])[idx], self.width)
        for key in np.unique(pair):
            if key in self.coefficients:
                selected = pair == key
                prediction[selected] += basis[selected] @ self.coefficients[key]
        return prediction


class DirectModel:
    def __init__(self, feature_key, estimator, fit_seconds):
        self.feature_key = feature_key
        self.estimator = estimator
        self.fit_seconds = fit_seconds
        self.solver_fits = 1

    def predict(self, data, mask):
        idx = np.flatnonzero(mask)
        if not len(idx):
            return np.empty(0, dtype=float)
        return self.estimator.predict(np.asarray(data[self.feature_key])[idx])


def fit_model(arm, param, data, mask):
    started = perf_counter()
    idx = np.flatnonzero(mask)
    # Slice first: neither fitting nor label filtering accesses targets outside mask.
    y = np.asarray(data["y"][idx], dtype=float)
    finite = np.isfinite(y)
    idx, y = idx[finite], y[finite]
    if not len(idx):
        raise ValueError("No finite training labels in the requested mask")
    weights = _episode_weights(np.asarray(data["episode"])[idx])
    if arm in ("effect", "dose"):
        basis = _basis(np.asarray(data[arm])[idx], param["width"])
        residual = y - _bliss(np.asarray(data["effect"])[idx])
        pair = np.asarray(data["pair"])[idx]
        coefficients = {}
        for key in np.unique(pair):
            selected = pair == key
            x, w, target = basis[selected], weights[selected], residual[selected]
            # The intercept receives the same ridge penalty as every Gaussian.
            coefficients[key] = np.linalg.solve(
                x.T @ (w[:, None] * x) + param["alpha"] * np.eye(basis.shape[1]),
                x.T @ (w * target))
        return ResidualModel(arm, param["width"], coefficients,
                             perf_counter() - started, len(coefficients))
    if arm in ("direct", "combo_direct"):
        kwargs = dict(param)
        family = kwargs.pop("model")
        estimator_type = {"extra_trees": ExtraTreesRegressor,
                          "hist_gradient_boosting": HistGradientBoostingRegressor}[family]
        estimator = estimator_type(**kwargs)
        feature_key = "full" if arm == "direct" else "without_mono"
        estimator.fit(np.asarray(data[feature_key])[idx], y, sample_weight=weights)
        return DirectModel(feature_key, estimator, perf_counter() - started)
    raise ValueError(f"Unknown arm: {arm}")
