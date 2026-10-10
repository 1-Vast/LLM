"""Joint A/B conditional means and genuinely out-of-fold residual covariances."""
import numpy as np

from research.decision_value.pairwise_20261009 import model as base
from research.decision_value.pairwise_v3 import support


def baseline(history, target):
    if not np.isfinite(target["state_B"]).all() or not np.asarray(target["state_available_B"]).all():
        raise ValueError("finite_complete_target_STATE_support_required")
    mean_B = base.prior(history, target)
    offset = (history["train_A"] - history["train_B"]).mean(0)
    return mean_B, mean_B + offset


def baseline_bank(history):
    count, menu = history["train_B"].shape
    if count < 2:
        return np.zeros((count, menu)), np.zeros((count, menu)), np.zeros((count, menu)), np.zeros((count, menu))
    predicted_B, predicted_A = [], []
    for held in range(count):
        keep = [i for i in range(count) if i != held]
        means = baseline(base.training_view(history, keep), base.public_view(history, held))
        predicted_B.append(means[0])
        predicted_A.append(means[1])
    predicted_B, predicted_A = np.array(predicted_B), np.array(predicted_A)
    return history["train_B"] - predicted_B, history["train_A"] - predicted_A, predicted_B, predicted_A


def fit_mean(history, eigens, reference, representation=None, penalty=10.):
    """A singleton history retains the baseline with an exactly zero adapter."""
    if len(history["train_B"]) < 1:
        raise ValueError("nonempty_mean_history_required")
    precision = history["precision_B"]
    available = history["state_available_B"]
    totals, counts = precision.sum(0), available.sum(0)
    if np.any(totals <= 0) or np.any(counts <= 0):
        raise ValueError("missing_training_reference_support")
    fitted = dict(base_mean_B=(history["train_B"] * precision).sum(0) / totals,
        state_centre=np.where(available, history["state_B"], 0.).sum(0) / counts,
        offset=(history["train_A"] - history["train_B"]).mean(0),
        history_basal=history["basal"].copy(), representation=representation,
        penalty=penalty, coefficients_B=None, coefficients_A=None, cell_vectors=None)
    if representation is None or penalty is None or len(history["train_B"]) == 1:
        return fitted
    error_B, error_A, _, _ = baseline_bank(history)
    gram, _ = support.cell_kernel(history["basal"], history["basal"][0], reference)
    cell_values, cell_vectors = np.linalg.eigh(gram)
    cell_values = np.maximum(cell_values, 0.)
    drug_values, drug_vectors = eigens[representation]
    denominator = cell_values[:, None] * drug_values[None, :] + penalty
    fitted.update(cell_vectors=cell_vectors,
        coefficients_B=(cell_vectors.T @ error_B @ drug_vectors) / denominator * drug_values,
        coefficients_A=(cell_vectors.T @ error_A @ drug_vectors) / denominator * drug_values)
    return fitted


def mean(fitted, target, eigens, reference):
    """Return conditional B and A means; target accepts public inputs only."""
    fitted = fitted.get("mean_model", fitted)
    if not np.isfinite(target["state_B"]).all() or not np.asarray(target["state_available_B"]).all():
        raise ValueError("finite_complete_target_STATE_support_required")
    support.standardize(target["basal"], reference)
    mean_B = fitted["base_mean_B"] + .5 * (target["state_B"] - fitted["state_centre"])
    mean_A = mean_B + fitted["offset"]
    if fitted["coefficients_B"] is not None:
        _, weights = support.cell_kernel(fitted["history_basal"], target["basal"], reference)
        row = weights @ fitted["cell_vectors"]
        _, vectors = eigens[fitted["representation"]]
        mean_B = mean_B + row @ fitted["coefficients_B"] @ vectors.T
        mean_A = mean_A + row @ fitted["coefficients_A"] @ vectors.T
    return mean_B, mean_A


def fit(history, kernels, eigens, mask, reference, representation=None, penalty=10.):
    count = len(history["train_B"])
    if count < 2:
        raise ValueError("two_history_rows_required_for_joint_moments")
    mean_model = fit_mean(history, eigens, reference, representation, penalty)
    old_B, old_A, baseline_B, baseline_A = baseline_bank(history)
    loo_B, loo_A = [], []
    for held in range(count):
        keep = [i for i in range(count) if i != held]
        # The entire adapter and its own baseline-residual bank exclude held labels.
        held_model = fit_mean(base.training_view(history, keep), eigens, reference, representation, penalty)
        predicted_B, predicted_A = mean(held_model, base.public_view(history, held), eigens, reference)
        loo_B.append(predicted_B)
        loo_A.append(predicted_A)
    loo_B, loo_A = np.array(loo_B), np.array(loo_A)
    error_B, error_A = history["train_B"] - loo_B, history["train_A"] - loo_A
    old_matrices, old_rho = base.kernel.covariances(old_B, old_A, kernels)
    refit_matrices, refit_rho = base.kernel.covariances(error_B, error_A, kernels)
    for matrices in (old_matrices, refit_matrices):
        for name in matrices:
            matrices[name] *= np.tile(mask, (2, 2))
    return dict(mean_model=mean_model, baseline_loo_B=baseline_B, baseline_loo_A=baseline_A,
        old_error_B=old_B, old_error_A=old_A, loo_mean_B=loo_B, loo_mean_A=loo_A,
        error_B=error_B, error_A=error_A, old_matrices=old_matrices, refit_matrices=refit_matrices,
        old_rho=old_rho, refit_rho=refit_rho)


def predict(fitted, target, query, observed_A, eigens, reference, residual_kind="refit",
            representation=None, eta=0., alpha=.1, gated=True):
    mean_B, mean_A = mean(fitted, target, eigens, reference)
    matrices = fitted[residual_kind + "_matrices"]
    covariance = matrices["empirical"]
    if representation:
        covariance = base.kernel.blend(covariance, matrices[representation], eta)
    n = len(mean_B)
    cross, variance_A = covariance[:n, n + query], float(covariance[n + query, n + query])
    diagnostics = support.assess(fitted["mean_model"]["history_basal"], target["basal"], reference)
    effective_alpha, innovation, innovation_z, outlier_factor = float(alpha), 0., None, 1.
    if alpha > 0:
        if observed_A is None or not np.isfinite(observed_A):
            raise ValueError("paid_finite_A_observation_required")
        innovation = float(observed_A - mean_A[query])
        innovation_z = innovation / np.sqrt(variance_A) if variance_A > 0 else None
        if gated:
            outlier_factor = min(1., 3. / abs(innovation_z)) if innovation_z else 1.
            effective_alpha *= diagnostics["weight"] * outlier_factor
    if variance_A <= 0:
        effective_alpha = 0.
    increment = effective_alpha * cross / variance_A * innovation if effective_alpha else np.zeros(n)
    posterior = covariance[:n, :n].copy()
    if effective_alpha:
        posterior -= effective_alpha * np.outer(cross, cross) / variance_A
    return dict(mean=mean_B + increment, mean_B_before=mean_B, mean_A=mean_A,
        covariance=.5 * (posterior + posterior.T), alpha_effective=effective_alpha,
        innovation=innovation, innovation_z=innovation_z, outlier_factor=outlier_factor,
        predicted_A=float(mean_A[query]), variance_A=variance_A, feedback_increment=increment,
        support=diagnostics, residual_kind=residual_kind)
