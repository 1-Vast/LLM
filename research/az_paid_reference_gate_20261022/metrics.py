"""Locked nominal actions and episode-to-MASTER macro scoring for one role."""
import numpy as np


def _groups(episode, valid_mask):
    episode = np.asarray(episode)
    valid_mask = np.asarray(valid_mask, dtype=bool)
    if episode.ndim != 1 or valid_mask.shape != episode.shape:
        raise ValueError("episode and valid_mask must be equally sized vectors")
    groups = []
    for key in np.unique(episode):
        idx = np.flatnonzero(episode == key)
        if np.any(valid_mask[idx]) != np.all(valid_mask[idx]):
            raise ValueError("Paid-input validity must be constant within each episode")
        groups.append((int(key), idx, bool(np.all(valid_mask[idx]))))
    return groups


def make_actions(pred, effect, episode, valid_mask, k=5):
    """Select nominal row indices using prediction and paid effects only; never y."""
    pred, effect = np.asarray(pred), np.asarray(effect)
    groups = _groups(episode, valid_mask)
    if pred.shape != np.asarray(episode).shape or effect.shape != (len(pred), 2):
        raise ValueError("pred and effect must align with nominal episode rows")
    actions = {}
    for key, idx, valid in groups:
        if not valid or len(idx) < k:
            continue
        if not (np.isfinite(pred[idx]).all() and np.isfinite(effect[idx]).all()):
            raise ValueError("Valid paid-input rows require finite predictions and effects")
        utility = pred[idx] - effect[idx].max(axis=1)
        actions[key] = idx[np.lexsort((idx, -utility))[:k]].tolist()
    return actions


def evaluate(y, pred, episode, master, effect, valid_mask, actions, *,
             assigned_masters, k=5, minimum_coverage=0.95):
    """Score fixed actions on common panels; missing outcomes never change actions.

    All rows supplied must belong to one upstream role. Denominators include every
    nominal episode/row, including input abstentions. MASTER vectors follow the
    explicit assigned_masters order; None means zero contributing episodes.
    """
    y, pred, effect = np.asarray(y), np.asarray(pred), np.asarray(effect)
    master = np.asarray(master)
    groups = _groups(episode, valid_mask)
    n = len(np.asarray(episode))
    if y.shape != (n,) or pred.shape != (n,) or master.shape != (n,) or effect.shape != (n, 2):
        raise ValueError("All arrays must align with nominal episode rows")
    assigned = np.asarray(assigned_masters).tolist()
    if len(set(assigned)) != len(assigned):
        raise ValueError("assigned_masters must be unique")
    master_index = {key: i for i, key in enumerate(assigned)}
    values = {metric: [[] for _ in assigned] for metric in ("mae", "utility", "oracle_utility", "regret")}
    input_counts = np.zeros(len(assigned), dtype=int)
    forecast_counts = np.zeros(len(assigned), dtype=int)
    recommendation_counts = np.zeros(len(assigned), dtype=int)
    expected_keys = {key for key, idx, valid in groups if valid and len(idx) >= k}
    if set(actions) != expected_keys:
        raise ValueError("Actions must cover every eligible nominal input episode, before seeing y")
    input_episodes = forecast_episodes = recommendation_episodes = finite_rows = 0
    for key, idx, valid in groups:
        identities = np.unique(master[idx])
        if len(identities) != 1 or identities[0] not in master_index:
            raise ValueError("Each episode must belong to one explicitly assigned MASTER")
        cell = master_index[identities[0]]
        if not valid:
            continue
        input_episodes += 1
        input_counts[cell] += 1
        if not (np.isfinite(pred[idx]).all() and np.isfinite(effect[idx]).all()):
            raise ValueError("Valid paid-input rows require finite predictions and effects")
        finite = np.isfinite(y[idx])
        finite_rows += int(finite.sum())
        if finite.sum() >= 5:
            values["mae"][cell].append(float(np.abs(y[idx[finite]] - pred[idx[finite]]).mean()))
            forecast_counts[cell] += 1
            forecast_episodes += 1
        if len(idx) < k:
            continue
        chosen = np.asarray(actions[key])
        if (chosen.shape != (k,) or not np.issubdtype(chosen.dtype, np.integer)
                or len(np.unique(chosen)) != k or not np.isin(chosen, idx).all()):
            raise ValueError("Each fixed action must contain k distinct rows of its own episode")
        # Full-target completeness supports the same panel for selected U and oracle regret.
        if not finite.all():
            continue
        observed_utility = y[idx] - effect[idx].max(axis=1)
        utility = float((y[chosen] - effect[chosen].max(axis=1)).mean())
        oracle = float(np.sort(observed_utility)[-k:].mean())
        values["utility"][cell].append(utility)
        values["oracle_utility"][cell].append(oracle)
        values["regret"][cell].append(oracle - utility)
        recommendation_counts[cell] += 1
        recommendation_episodes += 1

    per_master = {metric: [float(np.mean(v)) if v else None for v in cells]
                  for metric, cells in values.items()}

    def aggregate(metric):
        available = [v for v in per_master[metric] if v is not None]
        return float(np.mean(available)) if available else None

    def coverage(count, contributions):
        proportion = count / len(groups) if groups else 0.0
        missing = [key for key, count in zip(assigned, contributions) if count == 0]
        return {"episodes": int(count), "episode_coverage": float(proportion),
                "zero_contributor_masters": missing,
                "coverage_pass": bool(proportion >= minimum_coverage and assigned and not missing)}

    input_result = coverage(input_episodes, input_counts)
    forecast = coverage(forecast_episodes, forecast_counts)
    forecast["mae"] = aggregate("mae")
    forecast["finite_target_rows"] = finite_rows
    forecast["finite_target_row_coverage"] = finite_rows / n if n else 0.0
    forecast["coverage_pass"] = bool(forecast["coverage_pass"]
                                      and forecast["finite_target_row_coverage"] >= minimum_coverage)
    recommendation = coverage(recommendation_episodes, recommendation_counts)
    recommendation.update({metric: aggregate(metric) for metric in ("utility", "oracle_utility", "regret")})
    return {"mae": forecast["mae"], "utility": recommendation["utility"],
            "oracle_utility": recommendation["oracle_utility"], "regret": recommendation["regret"],
            "nominal_rows": n, "nominal_episodes": len(groups), "assigned_masters": assigned,
            "input": input_result, "forecast": forecast, "recommendation": recommendation,
            "per_master": per_master,
            "per_master_episode_counts": {"input": input_counts.tolist(),
                                          "forecast": forecast_counts.tolist(),
                                          "recommendation": recommendation_counts.tolist()},
            "coverage_pass": bool(input_result["coverage_pass"] and forecast["coverage_pass"]
                                   and recommendation["coverage_pass"])}


def score(y, pred, episode, master, effect, valid_mask, *, assigned_masters,
          nominal_actions=None, k=5, minimum_coverage=0.95):
    actions = (make_actions(pred, effect, episode, valid_mask, k=k)
               if nominal_actions is None else nominal_actions)
    return evaluate(y, pred, episode, master, effect, valid_mask, actions,
                    assigned_masters=assigned_masters, k=k, minimum_coverage=minimum_coverage)


def paired_bootstrap(candidate, baseline, *, higher_is_better=False,
                     n_boot=10000, seed=20261022):
    """Percentile paired MASTER bootstrap; positive gain always favors candidate."""
    candidate, baseline = np.asarray(candidate, dtype=float), np.asarray(baseline, dtype=float)
    if (candidate.ndim != 1 or candidate.shape != baseline.shape or not candidate.size
            or not np.isfinite(candidate).all() or not np.isfinite(baseline).all()):
        raise ValueError("Bootstrap needs aligned finite vectors of contributing MASTERs")
    gain = candidate - baseline if higher_is_better else baseline - candidate
    rng = np.random.default_rng(seed)
    samples = rng.integers(0, len(gain), size=(n_boot, len(gain)))
    distribution = gain[samples].mean(axis=1)
    low, high = np.percentile(distribution, [2.5, 97.5])
    return {"gain": float(gain.mean()), "mean": float(gain.mean()),
            "ci95": [float(low), float(high)], "lower": float(low), "upper": float(high),
            "n_masters": len(gain), "n_boot": n_boot, "seed": seed}
