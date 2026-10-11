"""Reference-only priors and fixed-probe residual updates for an exposed replay.

The deployment interface accepts basal expression and explicitly bought scalar
responses only. Crossfit residuals exclude the complete held context from prior
fitting, including basal normalization and feature selection. Covariances are
predictive heuristics, not calibrated uncertainty or biological mechanisms.
"""
from dataclasses import dataclass, field

import numpy as np


def _column_mean(values):
    counts = np.isfinite(values).sum(axis=0)
    if np.any(counts == 0):
        raise ValueError("every reference drug needs at least one finite response")
    return np.where(np.isfinite(values), values, 0.0).sum(axis=0) / counts


@dataclass
class BasalPrior:
    family: str
    response_mean: np.ndarray
    genes: np.ndarray
    center: np.ndarray
    scale: np.ndarray
    basal: np.ndarray
    response: np.ndarray
    neighbors: int
    coefficients: np.ndarray | None = None

    def predict(self, target_basal):
        target = np.asarray(target_basal, dtype=float)
        if target.shape != self.center.shape or not np.isfinite(target).all():
            raise ValueError("one finite target basal vector on the reference gene axis required")
        if self.family == "mean":
            return self.response_mean.copy()
        vector = ((target - self.center) / self.scale)[self.genes]
        if self.family == "ridge":
            return self.response_mean + vector @ self.coefficients
        distances = np.square(self.basal - vector).sum(axis=1)
        nearest = np.argsort(distances, kind="stable")[:self.neighbors]
        available = np.isfinite(self.response[nearest])
        counts = available.sum(axis=0)
        totals = np.where(available, self.response[nearest], 0.0).sum(axis=0)
        return np.divide(totals, counts, out=self.response_mean.copy(), where=counts > 0)


def fit_prior(basal_ref, y_ref, *, prior="mean", n_neighbors=15,
              n_features=256, prior_alpha=100.0):
    """Fit a simple prior on reference contexts; missing responses stay missing.

    Linear ridge uses reference drug means to fill missing training responses.
    kNN uses only available neighbor responses and falls back to reference means.
    Neither operation imputes a missing target outcome.
    """
    basal = np.asarray(basal_ref, dtype=float)
    response = np.asarray(y_ref, dtype=float)
    if basal.ndim != 2 or response.ndim != 2 or len(basal) != len(response):
        raise ValueError("aligned reference basal and response matrices required")
    if len(basal) < 2 or not np.isfinite(basal).all() or np.isinf(response).any():
        raise ValueError("at least two finite reference basal contexts and finite-or-missing responses required")
    if prior not in {"mean", "knn", "ridge"}:
        raise ValueError("unknown prior family")
    if n_neighbors < 1 or n_features < 1 or prior_alpha <= 0:
        raise ValueError("positive neighbor count, feature count and ridge penalty required")
    response_mean = _column_mean(response)
    center = basal.mean(axis=0)
    variance = basal.var(axis=0)
    scale = np.sqrt(variance)
    scale[scale < 1e-12] = 1.0
    genes = np.argsort(-variance, kind="stable")[:min(n_features, basal.shape[1])]
    standardized = ((basal - center) / scale)[:, genes]
    coefficients = None
    if prior == "ridge":
        centered_y = np.where(np.isfinite(response), response - response_mean, 0.0)
        gram = standardized.T @ standardized + prior_alpha * np.eye(len(genes))
        coefficients = np.linalg.solve(gram, standardized.T @ centered_y)
    return BasalPrior(prior, response_mean, genes, center, scale, standardized,
                      response.copy(), min(n_neighbors, len(basal)), coefficients)


@dataclass
class ReferenceModel:
    prior_model: BasalPrior
    residuals_: np.ndarray
    crossfit_predictions_: np.ndarray
    fold_ids_: np.ndarray
    valid_counts_: np.ndarray
    residual_bank_: np.ndarray
    differential_bank_: np.ndarray
    residual_scale_: float
    differential_scale_: float
    config: dict
    _features: dict = field(default_factory=dict)

    def predict_prior(self, target_basal):
        return self.prior_model.predict(target_basal)

    def select_probes(self, count=8):
        """Greedy pivoted reference residual diversity; no target inputs.

        At each step choose the largest unexplained differential residual
        column and remove its projection. This is a panel heuristic, not EVSI.
        """
        bank = self.differential_bank_.copy()
        if not 0 < count <= bank.shape[1]:
            raise ValueError("probe count must fit the drug axis")
        selected = []
        for _ in range(count):
            norms = np.einsum("ij,ij->j", bank, bank)
            norms[selected] = -np.inf
            chosen = int(np.argmax(norms))
            selected.append(chosen)
            length = np.sqrt(max(norms[chosen], 0.0))
            if length > 1e-12:
                direction = bank[:, chosen] / length
                bank -= np.outer(direction, direction @ bank)
        return np.asarray(selected, dtype=int)

    def fit_update_features(self, rank=4):
        """PCA loadings of centered, crossfitted differential reference errors."""
        if rank < 1:
            raise ValueError("positive residual rank required")
        if rank not in self._features:
            bank = self.differential_bank_
            values, vectors = np.linalg.eigh(bank @ bank.T)
            keep = np.argsort(values)[::-1][:min(rank, len(values))]
            keep = keep[values[keep] > 1e-12]
            # Loadings include their reference standard deviation. With an
            # isotropic latent prior, F F.T is the truncated error covariance.
            self._features[rank] = bank.T @ vectors[:, keep] / np.sqrt(max(len(bank) - 1, 1))
        return self._features[rank].copy()

    def predict(self, target_basal, probe_indices=(), probe_values=(), *,
                method="none", rank=4, ridge=1.0, shuffle_seed=20261011):
        """Return means using only the prior and explicitly purchased probes.

        ``conditional`` refits the empirical conditional-residual family on
        this functional endpoint. It is not a reproduction of historical RNA
        weights, cross-endpoint measurements, or their uncertainty claims.
        ``shuffled`` uses a seeded cyclic derangement of bought values.
        """
        baseline = self.predict_prior(target_basal)
        if method not in {"none", "no_update", "offset", "lowrank", "shuffled", "conditional"}:
            raise ValueError("unknown update method")
        indices = np.asarray(probe_indices)
        if indices.size == 0:
            indices = np.array([], dtype=int)
        elif indices.dtype.kind not in "iu":
            raise ValueError("probe indices must be integers")
        indices = indices.astype(int, copy=False)
        values = np.asarray(probe_values, dtype=float)
        if indices.ndim != 1 or values.shape != indices.shape:
            raise ValueError("aligned bought probe indices and scalar responses required")
        if (len(np.unique(indices)) != len(indices) or np.any(indices < 0)
                or np.any(indices >= len(baseline)) or not np.isfinite(values).all()):
            raise ValueError("unique valid probe indices and finite purchased values required")
        if ridge <= 0 or not np.isfinite(ridge):
            raise ValueError("positive finite residual ridge required")
        if method in {"none", "no_update"} or not len(indices):
            return baseline
        if method == "shuffled":
            if len(indices) < 2:
                raise ValueError("shuffled identity control needs at least two probes")
            shift = int(np.random.default_rng(shuffle_seed).integers(1, len(indices)))
            values = np.roll(values, shift)
        innovation = values - baseline[indices]
        if method == "offset":
            return baseline + innovation.mean()
        if method in {"lowrank", "shuffled"}:
            features = self.fit_update_features(rank)
            probe_features = features[indices]
            center = probe_features.mean(axis=0)
            design = probe_features - center
            gram = design.T @ design + ridge * self.differential_scale_ * np.eye(features.shape[1])
            coefficients = np.linalg.solve(gram, design.T @ (innovation - innovation.mean()))
            return baseline + innovation.mean() + (features - center) @ coefficients
        # Computing only the queried covariance columns avoids D x D storage.
        bank = self.residual_bank_
        cross = bank.T @ bank[:, indices] / max(len(bank) - 1, 1)
        gram = cross[indices] + ridge * self.residual_scale_ * np.eye(len(indices))
        return baseline + cross @ np.linalg.solve(gram, innovation)


def fit_reference(basal_ref, y_ref, *, prior="mean", n_neighbors=15,
                  n_features=256, prior_alpha=100.0, crossfit_folds=5,
                  seed=20261011):
    """Fit the prior and residual bank without receiving any target outcomes.

    Complete contexts are held out in seeded folds. Every fold refits its
    normalization, selected genes and predictor on that fold's training rows.
    Missing residuals are imputed to their reference column mean only when
    constructing covariance/PCA banks, i.e. zero after centering; validity
    counts and raw NaN residuals remain available for the audit.
    """
    basal = np.asarray(basal_ref, dtype=float)
    response = np.asarray(y_ref, dtype=float)
    if len(basal) < 3 or crossfit_folds < 2:
        raise ValueError("at least three reference contexts and two crossfit folds required")
    config = dict(prior=prior, n_neighbors=n_neighbors, n_features=n_features,
                  prior_alpha=prior_alpha)
    full_prior = fit_prior(basal, response, **config)
    order = np.random.default_rng(seed).permutation(len(basal))
    folds = min(int(crossfit_folds), len(basal))
    fold_ids = np.empty(len(basal), dtype=int)
    fold_ids[order] = np.arange(len(basal)) % folds
    predictions = np.empty(response.shape, dtype=float)
    for fold in range(folds):
        keep = fold_ids != fold
        fitted = fit_prior(basal[keep], response[keep], **config)
        for held in np.flatnonzero(~keep):
            predictions[held] = fitted.predict(basal[held])
    residuals = response - predictions
    valid = np.isfinite(residuals)
    centered = residuals - _column_mean(residuals)
    bank = np.where(valid, centered, 0.0)
    row_counts = valid.sum(axis=1)
    if np.any(row_counts == 0):
        raise ValueError("each reference context needs a finite response")
    row_offset = np.where(valid, residuals, 0.0).sum(axis=1) / row_counts
    differential = residuals - row_offset[:, None]
    differential -= _column_mean(differential)
    differential_bank = np.where(valid, differential, 0.0)
    denominator = max(len(basal) - 1, 1)
    residual_scale = max(float(np.median(np.square(bank).sum(axis=0) / denominator)), 1e-12)
    differential_scale = max(float(np.median(np.square(differential_bank).sum(axis=0) / denominator)), 1e-12)
    config.update(crossfit_folds=folds, seed=seed)
    return ReferenceModel(full_prior, residuals, predictions, fold_ids,
                          valid.sum(axis=0), bank, differential_bank,
                          residual_scale, differential_scale, config)
