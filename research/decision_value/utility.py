"""Fixed signed RNA utility and explicitly model-dependent decision protection."""
import numpy as np
from scipy.stats import norm

RNA_ENDPOINT = "named39RNA"


def utility(values, endpoint=RNA_ENDPOINT):
    if endpoint != RNA_ENDPOINT:
        raise ValueError("unsupported_endpoint_scientific_permission_required")
    return np.asarray(values).sum(axis=-1)


def permission_blocks(endpoint=RNA_ENDPOINT, independent_model_risk_certificate=False,
                      cost_utility_registered=False, failure_latency_registered=False):
    return [reason for passed, reason in (
        (endpoint == RNA_ENDPOINT, "unsupported_endpoint_scientific_permission_required"),
        (independent_model_risk_certificate, "independent_model_risk_certificate_missing"),
        (cost_utility_registered, "cost_utility_registration_missing"),
        (failure_latency_registered, "failure_latency_registration_missing")) if not passed]


def _top5(means):
    return np.argsort(-means, axis=-1, kind="stable")[..., :5].copy()


def _allowed(proposal, proposal_means, incumbent_means, pair_variance, incumbent, p_min):
    incoming = ~np.isin(proposal, incumbent)
    outgoing = ~(proposal[..., :, None] == incumbent).any(axis=-2)
    active = incoming[..., :, None] & outgoing[..., None, :]
    difference = proposal_means[..., :, None] - incumbent_means[..., None, :]
    # Up to 25 pairs at each of eight updates; nominal Gaussian-model bound.
    required_z = norm.ppf(1-(1-p_min)/(25*8))
    safe = (difference > 0) & (difference >= required_z*np.sqrt(np.maximum(pair_variance, 0.)))
    return (~active | safe).all(axis=(-2, -1))


def protected_selection(mean, covariance, incumbent, p_min=.95):
    incumbent = np.asarray(incumbent, dtype=int)
    proposal = _top5(mean)
    incoming = sorted(set(proposal)-set(incumbent))
    outgoing = sorted(set(incumbent)-set(proposal))
    variance = np.diag(covariance)[proposal, None] + np.diag(covariance)[None, incumbent] - 2*covariance[np.ix_(proposal, incumbent)]
    accepted = bool(_allowed(proposal, mean[proposal], mean[incumbent], variance, incumbent, p_min))
    probabilities = []
    for q in incoming:
        for r in outgoing:
            sd = np.sqrt(max(covariance[q, q]+covariance[r, r]-2*covariance[q, r], 0.))
            difference = mean[q]-mean[r]
            probability = norm.cdf(difference/sd) if sd > 0 else (1. if difference > 0 else .5 if difference == 0 else 0.)
            probabilities.append(dict(incoming=q, outgoing=r, probability=float(probability)))
    return dict(selected=proposal.tolist() if accepted else incumbent.tolist(), proposal=proposal.tolist(),
                incoming=incoming, outgoing=outgoing, accepted=accepted,
                pair_probabilities=probabilities, model_only=True)


def expected_gains(mean, covariance, incumbent, normals, gated=False):
    """Raw nonnegative paired gains for every A; caller supplies fresh iid normals."""
    n = len(mean)//2
    incumbent = np.asarray(incumbent, dtype=int)
    mu, bb = mean[:n], covariance[:n, :n]
    avar = np.maximum(np.diag(covariance)[n:], 0.)
    direction = np.divide(covariance[:n, n:].T, np.sqrt(avar)[:, None],
                          out=np.zeros((n, n)), where=avar[:, None] > 0)
    draws = mu[None, None, :] + direction[:, None, :]*np.asarray(normals)[None, :, None]
    proposal = _top5(draws)
    proposal_mean = np.take_along_axis(draws, proposal, axis=-1)
    incumbent_mean = draws[..., incumbent]
    gains = proposal_mean.sum(-1)-incumbent_mean.sum(-1)
    if gated:
        proposal_direction = np.take_along_axis(direction[:, None, :], proposal, axis=-1)
        delta_direction = proposal_direction[..., :, None]-direction[:, None, None, incumbent]
        pair_variance = np.diag(bb)[proposal, None] + np.diag(bb)[None, None, None, incumbent] - 2*bb[proposal[..., :, None], incumbent] - delta_direction**2
        gains = np.where(_allowed(proposal, proposal_mean, incumbent_mean, pair_variance, incumbent, .95), gains, 0.)
    current = mu[_top5(mu)].sum()-mu[incumbent].sum()
    incumbent_direction = direction[:, incumbent].sum(-1)
    highest = np.partition(direction, n-5, axis=1)[:, -5:].sum(-1)-incumbent_direction
    lowest = np.partition(direction, 4, axis=1)[:, :5].sum(-1)-incumbent_direction
    caps = max(float(current), 0.) + 3*np.maximum(abs(highest), abs(lowest))
    return np.maximum(gains, 0.), caps


def estimate(mean, covariance, incumbent, normals, gated=False):
    """Hoeffding lower bound for clipped model EVSI, not model-risk uncertainty."""
    raw, caps = expected_gains(mean, covariance, incumbent, normals, gated)
    clipped = np.minimum(raw, caps[:, None])
    radius = caps*np.sqrt(np.log(146*8/.05)/(2*len(normals)))
    return dict(gross_model_EVSI_sample=raw.mean(-1), truncated_EVSI_sample=clipped.mean(-1),
                mc_lower=clipped.mean(-1)-radius, cap=caps, mc_integration_only=True)
