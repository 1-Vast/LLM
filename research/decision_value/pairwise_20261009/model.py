"""Training-only, decision-focused one-observation correction research helpers."""
import importlib.util
from pathlib import Path

import numpy as np
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location(
    "pairwise_authenticated_kernels", ROOT / "research/map_module_replacement_20261009/kernel.py")
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)

REPRESENTATIONS = kernel.ARMS
ALPHAS = (0., .1, .25, .5, 1.)
ETAS = (0., .5, 1.)
LAMBDAS = (None, 1., 10., 100.)
SIZES = (4, 8, 16)
SEEDS = (11, 23, 47)
SIMPLE = ("no_update", "empirical_full", "fixed_shrink", "cv_shrink", "gated_cv_shrink")
ARMS = (*SIMPLE, "matched_strength_empirical",
        *(r + "_only" for r in REPRESENTATIONS),
        *(r + "_feedback" for r in REPRESENTATIONS),
        "knowledge_feedback_only", "selective_knowledge")
TRAIN_KEYS = ("train_A", "train_B", "precision_B", "state_B", "state_available_B", "basal")


def training_view(arrays, indices):
    """Strip all held labels before fitting, tuning, or computing a target prior."""
    return {key: np.asarray(arrays[key])[indices].copy() for key in TRAIN_KEYS}


def public_view(arrays, held):
    return {key: np.asarray(arrays[key])[held].copy()
            for key in ("state_B", "state_available_B", "basal")}


def prior(history, target):
    precision = history["precision_B"]
    totals = precision.sum(0)
    support = history["state_available_B"]
    counts = support.sum(0)
    if np.any(totals <= 0) or np.any(counts <= 0):
        raise ValueError("missing_training_reference_support")
    mean = (history["train_B"] * precision).sum(0) / totals
    centre = np.where(support, history["state_B"], 0.).sum(0) / counts
    return mean + .5 * np.where(target["state_available_B"], target["state_B"] - centre, 0.)


def histories(complete, held, seed):
    available = sorted(set(complete) - {held})
    if held not in complete or len(available) < max(SIZES):
        raise ValueError("insufficient_complete_history_support")
    shuffled = np.random.default_rng(np.random.SeedSequence([seed, held])).permutation(available)
    return {size: sorted(shuffled[:size].tolist()) for size in SIZES}


def pairs_and_query(mean):
    if len(mean) < 8 or not np.isfinite(mean).all():
        raise ValueError("eight_finite_menu_candidates_required")
    order = np.lexsort((np.arange(len(mean)), -mean))
    pairs = [[int(i), int(j)] for i in order[2:5] for j in order[5:8]]
    midpoint = .5 * (mean[order[4]] + mean[order[5]])
    query = int(np.lexsort((np.arange(len(mean)), abs(mean - midpoint)))[0])
    return pairs, query, order[:5].tolist()


def condition_mask(records):
    return np.array([[a["dose"] == b["dose"] and a["unit"] == b["unit"]
                      for b in records] for a in records], dtype=float)


def prepare_kernels(records, features):
    kernels, metadata = kernel.candidate_kernels(records, features)
    eigens = {}
    for representation, matrix in kernels.items():
        values, vectors = np.linalg.eigh(matrix)
        if values.min() < -1e-8:
            raise ValueError("drug_kernel_not_PSD")
        eigens[representation] = (np.maximum(values, 0.), vectors)
    return kernels, eigens, condition_mask(records), metadata


def fit(history, kernels, mask):
    count = len(history["train_B"])
    if count < 2:
        raise ValueError("two_complete_history_rows_required")
    error_B, error_A = [], []
    for held in range(count):
        keep = [i for i in range(count) if i != held]
        training = training_view(history, keep)
        prediction = prior(training, public_view(history, held))
        offset = (training["train_A"] - training["train_B"]).mean(0)
        error_B.append(history["train_B"][held] - prediction)
        error_A.append(history["train_A"][held] - prediction - offset)
    error_B, error_A = np.array(error_B), np.array(error_A)
    matrices, rho = kernel.covariances(error_B, error_A, kernels)
    # A Schur product on both roles keeps PSD and blocks every cross-dose transfer.
    for name in matrices:
        matrices[name] *= np.tile(mask, (2, 2))
    basal_centre = history["basal"].mean(0)
    centred = history["basal"] - basal_centre
    lengths = np.linalg.norm(centred, axis=1)
    normalized = np.divide(centred, lengths[:, None], out=np.zeros_like(centred),
                           where=lengths[:, None] > 0)
    cell_values, cell_vectors = np.linalg.eigh(normalized @ normalized.T)
    return dict(error_B=error_B, error_A=error_A, matrices=matrices, rho=rho,
                offset=(history["train_A"] - history["train_B"]).mean(0),
                basal_centre=basal_centre, normalized_basal=normalized,
                cell_values=np.maximum(cell_values, 0.), cell_vectors=cell_vectors)


def cell_similarity(fitted, target):
    centred = target["basal"] - fitted["basal_centre"]
    length = np.linalg.norm(centred)
    return fitted["normalized_basal"] @ (centred / length) if length > 0 else np.zeros(len(fitted["error_B"]))


def adapter(fitted, target, eigen, penalty):
    """Tensor-product ridge residual mean; OFF is an exact zero correction."""
    if penalty is None:
        return np.zeros(fitted["error_B"].shape[1])
    drug_values, drug_vectors = eigen
    cell_values, cell_vectors = fitted["cell_values"], fitted["cell_vectors"]
    cache = fitted.setdefault("adapter_cache", {})
    key = (id(drug_values), penalty)
    if key not in cache:
        transformed = cell_vectors.T @ fitted["error_B"] @ drug_vectors
        cache[key] = transformed / (cell_values[:, None] * drug_values[None, :] + penalty)
    return ((cell_similarity(fitted, target) @ cell_vectors) @ cache[key] * drug_values) @ drug_vectors.T


def pair_regret(mean, outcomes, pairs):
    pair = np.asarray(pairs, dtype=int)
    difference = outcomes[pair[:, 0]] - outcomes[pair[:, 1]]
    preferred = mean[pair[:, 0]] - mean[pair[:, 1]]
    choose_first = (preferred > 0) | ((preferred == 0) & (pair[:, 0] < pair[:, 1]))
    return float(np.mean(np.where(choose_first, np.maximum(-difference, 0.), np.maximum(difference, 0.))))


def movement(mean, baseline, pairs):
    pair = np.asarray(pairs, dtype=int)
    return (mean - baseline)[pair[:, 0]] - (mean - baseline)[pair[:, 1]]


def predict(fitted, target, base, query, observed_A, eigens,
            representation=None, penalty=None, eta=0., alpha=0., gated=False):
    n = len(base)
    correction = adapter(fitted, target, eigens[representation], penalty) if representation else np.zeros(n)
    covariance = fitted["matrices"]["empirical"]
    if representation:
        covariance = kernel.blend(covariance, fitted["matrices"][representation], eta)
    cross = covariance[:n, n + query]
    variance = float(covariance[n + query, n + query])
    actual_alpha, innovation, innovation_z = float(alpha), 0., None
    similarity = np.maximum(cell_similarity(fitted, target), 0.)
    square_sum = float(similarity @ similarity)
    n_eff = float(similarity.sum() ** 2 / square_sum) if square_sum > 0 else 0.
    support_factor = 0. if n_eff < 2 else min(1., n_eff / 4.)
    outlier_factor = 1.
    if alpha > 0:
        if observed_A is None or not np.isfinite(observed_A):
            raise ValueError("paid_finite_A_observation_required")
        innovation = float(observed_A - base[query] - fitted["offset"][query])
        innovation_z = innovation / np.sqrt(variance) if variance > 0 else None
        if gated:
            outlier_factor = min(1., 3. / abs(innovation_z)) if innovation_z else 1.
            actual_alpha *= support_factor * outlier_factor
    if variance <= 0:
        actual_alpha = 0.
    change = actual_alpha * cross / variance * innovation if actual_alpha else np.zeros(n)
    mean = base + correction + change
    posterior = covariance[:n, :n].copy()
    if actual_alpha:
        posterior -= actual_alpha * np.outer(cross, cross) / variance
    return dict(mean=mean, covariance=.5 * (posterior + posterior.T),
                alpha_effective=actual_alpha, innovation=innovation, innovation_z=innovation_z,
                n_eff=n_eff, support_factor=support_factor, outlier_factor=outlier_factor,
                adapter_correction=correction, feedback_increment=change,
                variance_A=variance, predicted_A=float(base[query] + fitted["offset"][query]))


def pair_diagnostics(prediction, pairs, scale=1.):
    pair = np.asarray(pairs, dtype=int)
    mean, covariance = prediction["mean"], prediction["covariance"]
    delta = mean[pair[:, 0]] - mean[pair[:, 1]]
    variance = np.maximum(covariance[pair[:, 0], pair[:, 0]] + covariance[pair[:, 1], pair[:, 1]]
                          - 2 * covariance[pair[:, 0], pair[:, 1]], 1e-12)
    return delta, variance, norm.cdf(delta / (np.sqrt(variance) * scale))


def configs(chosen, matched_alpha):
    result = {"no_update": dict(), "empirical_full": dict(alpha=1.),
              "fixed_shrink": dict(alpha=.1), "cv_shrink": dict(alpha=chosen["empirical_alpha"]),
              "gated_cv_shrink": dict(alpha=chosen["gated_empirical_alpha"], gated=True),
              "matched_strength_empirical": dict(alpha=matched_alpha)}
    for representation in REPRESENTATIONS:
        penalty = chosen[representation]["penalty"]
        result[representation + "_only"] = dict(representation=representation, penalty=penalty)
        result[representation + "_feedback"] = dict(representation=representation, penalty=penalty,
            eta=chosen[representation]["eta"], alpha=chosen[representation]["alpha"], gated=True)
    result["knowledge_feedback_only"] = dict(result["knowledge_feedback"], penalty=None)
    result["selective_knowledge"] = dict(result["knowledge_feedback"])
    return result


def choose(history, kernels, eigens, mask):
    """All tuning and movement matching consume only historical inner-fold labels."""
    count = len(history["train_B"])
    inner, folds = [], []
    for fold in range(3):
        keep = [i for i in range(count) if i % 3 != fold]
        held = [i for i in range(count) if i % 3 == fold]
        fitted = fit(training_view(history, keep), kernels, mask)
        folds.append(dict(keep_positions=keep, held_positions=held))
        for cell in held:
            target = public_view(history, cell)
            base = prior(training_view(history, keep), target)
            pairs, query, _ = pairs_and_query(base)
            inner.append(dict(fitted=fitted, target=target, base=base, pairs=pairs, query=query,
                              observed_A=float(history["train_A"][cell, query]), outcomes=history["train_B"][cell]))

    def forecasts(configuration):
        return [predict(row["fitted"], row["target"], row["base"], row["query"],
                        row["observed_A"], eigens, **configuration) for row in inner]

    def loss(configuration):
        values = forecasts(configuration)
        return float(np.mean([pair_regret(pred["mean"], row["outcomes"], row["pairs"])
                              for pred, row in zip(values, inner)]))

    alpha_scores = [(alpha, loss(dict(alpha=alpha))) for alpha in ALPHAS]
    gated_scores = [(alpha, loss(dict(alpha=alpha, gated=True))) for alpha in ALPHAS]
    chosen = dict(empirical_alpha=min(alpha_scores, key=lambda row: (row[1], row[0]))[0])
    chosen["gated_empirical_alpha"] = min(gated_scores, key=lambda row: (row[1], row[0]))[0]
    diagnostics = dict(empirical_alpha_losses=[dict(alpha=a, regret=v) for a, v in alpha_scores])
    diagnostics["gated_empirical_alpha_losses"] = [dict(alpha=a, regret=v) for a, v in gated_scores]
    for representation in REPRESENTATIONS:
        penalty_scores = [(penalty, loss(dict(representation=representation, penalty=penalty)))
                          for penalty in LAMBDAS]
        penalty = min(enumerate(penalty_scores), key=lambda row: (row[1][1], row[0]))[1][0]
        tuning = []
        for eta in ETAS:
            for alpha in ALPHAS:
                value = loss(dict(representation=representation, penalty=penalty, eta=eta, alpha=alpha, gated=True))
                tuning.append(dict(eta=eta, alpha=alpha, regret=value))
        best = min(tuning, key=lambda row: (row["regret"], row["alpha"], row["eta"]))
        chosen[representation] = dict(penalty=penalty, eta=best["eta"], alpha=best["alpha"])
        diagnostics[representation] = dict(penalty_losses=[dict(penalty=p, regret=v) for p, v in penalty_scores],
                                           feedback_losses=tuning)

    preliminary = configs(chosen, 0.)
    knowledge = forecasts(preliminary["knowledge_feedback"])
    target_variances, full_variances = [], []
    clipped_normal_second_moment = float(1 - 6 * norm.pdf(3) + 16 * norm.sf(3))
    for row, pred in zip(inner, knowledge):
        pair = np.asarray(row["pairs"])
        q, n = row["query"], len(row["base"])
        empirical = row["fitted"]["matrices"]["empirical"]
        mixed = kernel.blend(empirical, row["fitted"]["matrices"]["knowledge"], chosen["knowledge"]["eta"])
        cross = mixed[:n, n + q]
        reliability = chosen["knowledge"]["alpha"] * pred["support_factor"]
        target_variances.extend((reliability ** 2 *
            (cross[pair[:, 0]] - cross[pair[:, 1]]) ** 2 / mixed[n + q, n + q] *
            clipped_normal_second_moment).tolist())
        cross = empirical[:n, n + q]
        full_variances.extend(((cross[pair[:, 0]] - cross[pair[:, 1]]) ** 2 / empirical[n + q, n + q]).tolist())
    target_rms = float(np.sqrt(np.mean(target_variances)))
    full_rms = float(np.sqrt(np.mean(full_variances)))
    uncapped = target_rms / full_rms if full_rms > 0 else 0.
    matched_alpha = min(1., uncapped)
    configurations = configs(chosen, matched_alpha)
    scales, losses = {}, {}
    for arm, configuration in configurations.items():
        predicted = forecasts(configuration)
        standardized = []
        for pred, row in zip(predicted, inner):
            delta, variance, _ = pair_diagnostics(pred, row["pairs"])
            pair = np.array(row["pairs"])
            real = row["outcomes"][pair[:, 0]] - row["outcomes"][pair[:, 1]]
            standardized.extend(((delta - real) / np.sqrt(variance)).tolist())
        scales[arm] = max(1., float(np.sqrt(np.mean(np.square(standardized)))))
        losses[arm] = loss(configuration)
    best_simple = min(SIMPLE, key=lambda arm: (losses[arm], SIMPLE.index(arm)))
    return dict(chosen=chosen, configurations=configurations, probability_scales=scales,
                selected_simple=best_simple, inner_losses=losses, inner_folds=folds, tuning=diagnostics,
                matched_strength=dict(alpha=matched_alpha, uncapped_alpha=uncapped, capped=uncapped > 1.,
                    target_pair_movement_RMS=target_rms, empirical_full_pair_movement_RMS=full_rms,
                    achieved_pair_movement_RMS=matched_alpha * full_rms,
                    residual_match_error=matched_alpha * full_rms - target_rms,
                    matching="model-implied training-OOF expected feedback movement; Gaussian clipped-Z second moment",
                    clipped_normal_second_moment=clipped_normal_second_moment))


def commit(prediction, base, pairs, initial, scale, selective=False):
    delta, variance, probabilities = pair_diagnostics(prediction, pairs, scale)
    means = prediction["mean"]
    proposal = np.lexsort((np.arange(len(means)), -means))[:5].tolist()
    incoming, outgoing = sorted(set(proposal) - set(initial)), sorted(set(initial) - set(proposal))
    checks = []
    for i in incoming:
        for j in outgoing:
            covariance = prediction["covariance"]
            sd = np.sqrt(max(covariance[i, i] + covariance[j, j] - 2 * covariance[i, j], 1e-12)) * scale
            checks.append(dict(incoming=i, outgoing=j, probability=float(norm.cdf((means[i] - means[j]) / sd))))
    accepted = not selective or all(row["probability"] >= .95 for row in checks)
    decisions = []
    for (i, j), difference, probability in zip(pairs, delta, probabilities):
        preference = i if difference > 0 or (difference == 0 and i < j) else j
        decisions.append(None if selective and .05 < probability < .95 else int(preference))
    return dict(selected=proposal if accepted else list(initial), proposal=proposal, swap_accepted=accepted,
                swap_checks=checks, pair_probabilities=probabilities.tolist(), pair_variances=variance.tolist(),
                pair_delta=delta.tolist(), pair_decisions=decisions, probability_scale=scale,
                mean=means.tolist(), alpha_effective=prediction["alpha_effective"],
                innovation=prediction["innovation"], innovation_z=prediction["innovation_z"],
                n_eff=prediction["n_eff"], support_factor=prediction["support_factor"],
                outlier_factor=prediction["outlier_factor"], predicted_A=prediction["predicted_A"],
                variance_A=prediction["variance_A"])
