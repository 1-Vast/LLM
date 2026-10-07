"""Independent scalar-ridge and ranking-boundary arithmetic for verification.

This module does not import worker methods or policy code. It computes Gaussian
posteriors by batch conditioning and boundary integrals with scipy.stats.norm.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm


def topfive(values):
    return sorted(range(len(values)), key=lambda i: (-values[i], i))[:5]


def condition(prior, covariance, observation_variance, offset, indices, values):
    if not indices:
        return np.array(prior, copy=True), np.array(covariance, copy=True)
    selected = np.asarray(indices, int)
    cross = covariance[:, selected]
    marginal = covariance[np.ix_(selected, selected)] + np.diag(observation_variance[selected])
    innovation = values[selected] - offset[selected] - prior[selected]
    mean = prior + cross @ np.linalg.solve(marginal, innovation)
    posterior = covariance - cross @ np.linalg.solve(marginal, cross.T)
    return mean, posterior


def crossing_scores(mean, covariance, observation_variance, available):
    inside = topfive(mean)
    outside = sorted(set(range(len(mean))) - set(inside), key=lambda i: (-mean[i], i))
    difference = np.asarray(mean)[inside, None] - np.asarray(mean)[outside][None]
    result = {}
    details = {}
    for query in sorted(available):
        variance = covariance[query, query] + observation_variance[query]
        assert np.isfinite(variance) and variance > 0
        leverage = (covariance[inside, query][:, None] - covariance[outside, query][None]) / np.sqrt(variance)
        sd = np.abs(leverage)
        valid = sd > 0
        z = np.divide(difference, sd, out=np.full_like(sd, np.inf), where=valid)
        gains = sd * norm.pdf(z) - difference * norm.cdf(-z)
        gains = np.maximum(gains, 0.)
        best = np.unravel_index(gains.argmax(), gains.shape)
        result[query] = float(gains[best])
        details[query] = {"incumbent": inside[best[0]], "challenger": outside[best[1]],
                          "mean_gap": float(difference[best]), "observation_gap_sd": float(sd[best]),
                          "signed_observation_leverage": float(leverage[best])}
    return result, details


def fit_ridge(features, squared_error, design=False):
    x = np.array(features, copy=True)
    if design:
        x[:, [0, 1, x.shape[1] - 3]] = 0.
    positive = np.asarray(squared_error)[np.asarray(squared_error) > 0]
    floor = max(float(np.median(positive)) * .01, 1e-12)
    target = np.log(squared_error + floor)
    centre = np.mean(x, axis=0)
    scale = np.std(x, axis=0)
    scale[scale <= 1e-12] = 1.
    standard = (x - centre) / scale
    intercept = float(target.mean())
    # QR least squares on augmented observations independently reproduces ridge.
    augmented = np.concatenate((standard, np.sqrt(1000.) * np.eye(standard.shape[1])), axis=0)
    response = np.concatenate((target - intercept, np.zeros(standard.shape[1])))
    coefficients = np.linalg.lstsq(augmented, response, rcond=None)[0]
    return {"centre": centre, "scale": scale, "coef": coefficients, "intercept": intercept,
            "predicted_centre": float((standard @ coefficients + intercept).mean()), "floor": floor,
            "design": design}


def predict(model, features):
    x = np.array(features, copy=True)
    if model["design"]:
        x[:, [0, 1, x.shape[1] - 3]] = 0.
    return (x - model["centre"]) / model["scale"] @ model["coef"] + model["intercept"]


def nearest_distance(target, reference):
    centred = reference - np.mean(reference, axis=0)
    query = target - np.mean(reference, axis=0)
    norms = np.linalg.norm(centred, axis=1) * np.linalg.norm(query) + 1e-12
    return float(np.clip(1 - np.max(centred @ query / norms), 0, 2))


def reference_features(arrays, held, excluded=(), permuted=False):
    keep = np.ones(len(arrays["basal"]), bool)
    keep[list(excluded)] = False
    keep[held] = False
    qualified = arrays["availability_B"] & keep[:, None]
    precision = arrays["precision_B"] * qualified
    precision /= precision.sum(axis=0)
    m0 = np.sum(precision * arrays["train_B"], axis=0)
    state = arrays["state_B_permuted"] if permuted else arrays["state_B"]
    state_mask = arrays["state_available_B_permuted"] if permuted else arrays["state_available_B"]
    state_qualified = state_mask & keep[:, None]
    count = state_qualified.sum(axis=0)
    state_mean = np.sum(np.where(state_qualified, state, 0), axis=0) / count
    correction = .5 * (state[held] - state_mean)
    present = state_mask[held]
    correction = np.where(present, correction, 0.)
    availability = qualified.sum(axis=0) / keep.sum()
    state_availability = count / keep.sum()
    variance = np.nanvar(np.where(qualified, arrays["train_B"], np.nan), axis=0, ddof=1)
    distance = nearest_distance(arrays["basal"][held], arrays["basal"][keep])
    n = len(m0)
    features = np.column_stack((np.log(np.abs(correction) + 1e-12), np.repeat(distance, n),
                                np.log10(arrays["dose"]), arrays["plate_design"], availability,
                                state_availability, np.log(np.maximum(variance, 1e-12)),
                                availability < 1., state_availability < 1.))
    eligible = arrays["availability_A"][held] & arrays["availability_B"][held] & present
    return features, (m0 + correction - arrays["train_B"][held]) ** 2, eligible, m0


def dataset(arrays, included, permuted=False):
    features, errors, groups = [], [], []
    excluded = np.flatnonzero(~included)
    for held in np.flatnonzero(included):
        x, e, selected, _ = reference_features(arrays, int(held), excluded, permuted)
        features.append(x[selected]); errors.append(e[selected]); groups.extend([int(held)] * int(selected.sum()))
    return np.concatenate(features), np.concatenate(errors), np.asarray(groups)
