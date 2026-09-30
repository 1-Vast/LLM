"""Agent-owned acquisition using explicit measurement cost and sparse reference forecasts.

The model only predicts registered readings. The shared agent runner owns legality,
budgets, real measurements and evidence updates. Prices are decision preferences,
not parameters fitted to held-out outcomes.
"""
from __future__ import annotations

import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sequence_audit"))
import policies as P
from model import SparseReferenceModel


def value(forecast, weights):
    if forecast.refusal:
        return None
    correct = sum(weights[h] * b.p_correct for h, b in forecast.branches.items())
    wrong = sum(weights[h] * b.p_wrong for h, b in forecast.branches.items())
    # Upper variance bound avoids assuming independent uncertainty in the branches.
    sd = sum(weights[h] * math.sqrt(max(b.value_variance, 0)) for h, b in forecast.branches.items())
    return {"p_correct": correct, "p_wrong": wrong, "utility": correct - 2 * wrong,
            "utility_sd_bound": sd,
            "weighted_branch_wrong_upper95": sum(weights[h] * b.wrong_upper95 for h, b in forecast.branches.items())}


def best_single(menu, forecast_for, weights, price, days):
    choices, unknown = [], {}
    for action in menu:
        forecast = forecast_for(action)
        estimate = value(forecast, weights)
        if estimate is None:
            unknown[P.C.action_id(action)] = forecast.refusal
            continue
        if estimate["utility"] - price > 1e-12:
            choices.append((estimate["utility"] - price, days(action), P.C.action_id(action), action, estimate, forecast))
    best = min(choices, key=lambda x: (-x[0], x[1], x[2])) if choices else None
    return best, unknown


def choose(model, menu, h1, h2, executed, remaining, setting, price, *, marginal_only=False):
    """Replan after the actual first result; never reuse a nonexistent cached continuation."""
    weights = {h1: 0.5, h2: 0.5}
    source = label = None
    if executed and executed[-1]["qc"]:
        source = tuple(executed[-1]["key"])
        label = P.NEUTRAL.get(executed[-1]["outcome"])
        if label is None:
            return None, {"reason": "result_not_a_neutral_planning_observation"}
        initial = model.forecast(source, h1, h2)
        if initial.refusal:
            return None, {"reason": "value_unknown:first_reading_likelihood_unavailable"}
        likelihood = {h: initial.branches[h].probabilities[label] for h in weights}
        total = sum(likelihood.values())
        if total <= 0:
            return None, {"reason": "value_unknown:observed_reading_outside_forecast"}
        weights = {h: p / total for h, p in likelihood.items()}

    def forecast_for(action, first=source, observed=label):
        return model.forecast(action, h1, h2, source=None if marginal_only else first,
                              observed_label=None if marginal_only else observed)

    if executed:
        best, unknown = best_single(menu, forecast_for, weights, price, setting.days)
        if best is None:
            reason = "value_unknown" if unknown else "estimated_net_non_positive"
            return None, {"reason": reason, "unknown_forecasts": unknown, "price": price}
        net, _, _, action, estimate, forecast = best
        return action, note(forecast, weights, estimate, price, expected_net=net,
                            expected_measurements=1.0, after=label or "qc_failure")

    choices, unknown = [], {}
    for first in menu:
        forecast = model.forecast(first, h1, h2)
        immediate = value(forecast, weights)
        if immediate is None:
            unknown[P.C.action_id(first)] = forecast.refusal
            continue
        correct, wrong = immediate["p_correct"], immediate["p_wrong"]
        assays, days = 1.0, setting.days(first)
        followups = {}
        if setting.max_measurements >= 2:
            for observed in P.NEUTRAL.values():
                joint = {h: 0.5 * forecast.branches[h].probabilities[observed] for h in weights}
                mass = sum(joint.values())
                if mass <= 0:
                    continue
                posterior = {h: p / mass for h, p in joint.items()}
                # Use the first action's actual cost, not accumulated expected
                # cost from a mutually exclusive branch, for hard affordability.
                future = [k for k in menu if k != first and k[1] >= first[1]
                          and setting.days(k) + setting.days(first) <= remaining + 1e-12]
                tail, refused = best_single(future, lambda k: forecast_for(k, first, observed),
                                            posterior, price, setting.days)
                if tail is not None:
                    _, _, _, second, estimate, _ = tail
                    followups[observed] = P.C.action_id(second)
                    correct += mass * estimate["p_correct"]
                    wrong += mass * estimate["p_wrong"]
                    assays += mass
                    days += mass * setting.days(second)
                elif refused:
                    unknown.update({f"{P.C.action_id(first)}:{observed}:{k}": v for k, v in refused.items()})
        net = correct - 2 * wrong - price * assays
        if net > 1e-12:
            choices.append((net, days, P.C.action_id(first), first, forecast, immediate,
                            {"expected_terminal_correct": correct, "expected_terminal_wrong": wrong,
                             "expected_measurements": assays, "expected_net": net,
                             "planned_followups": followups}))
    if not choices:
        # Unknown future branches do not turn a known, unprofitable immediate
        # measurement into a claim that no future experiment could have value.
        reason = "value_unknown" if unknown else "estimated_net_non_positive"
        return None, {"reason": reason, "unknown_forecasts": unknown, "price": price}
    _, _, _, first, forecast, immediate, plan = min(choices, key=lambda x: (-x[0], x[1], x[2]))
    return first, note(forecast, weights, immediate, price, **plan)


def note(forecast, weights, estimate, price, **plan):
    return {"evidence_kind": "model_prediction", "price": price, **estimate, **plan,
            "planning_hypothesis_weights": weights,
            "uncertainty_scope": "conditional on estimated reference distributions and planning weights",
            "prediction_by_hypothesis": {h: {"probabilities": b.probabilities,
                "p_correct": b.p_correct, "p_wrong": b.p_wrong,
                "local_support": b.local_support, "parent_support": b.parent_support,
                "basis": b.basis, "prior_strength": b.prior_strength}
                for h, b in forecast.branches.items()}}


def make_policy(cost_per_measurement, *, pooling=True, marginal_only=False, permuted=False):
    if not math.isfinite(cost_per_measurement) or cost_per_measurement < 0:
        raise ValueError("measurement price must be finite and nonnegative")

    def policy(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        if not ctx.params["eliminates"]:
            return None, {"reason": "registered_validator_cannot_eliminate"}
        # Reference tables omit the evaluation fold. Identity and held-out
        # expression are never passed to the predictive model.
        models = ctx.extra.setdefault("sparse_value_models", {})
        model_key = (pooling, permuted)
        if model_key not in models:
            comp = ctx.data.compounds.drop_duplicates("compound").set_index("compound")
            groups = comp["component" if "component" in comp.columns else "skeleton"].to_dict()
            models[model_key] = SparseReferenceModel(ctx.ft_perm if permuted else ctx.ft, ctx.params,
                                                     groups, pooling=pooling)
        cache = ctx.extra.setdefault("sparse_value_choices", {})
        history = tuple((tuple(s["key"]), s["outcome"], s["qc"]) for s in executed)
        key = (h1, h2, history, tuple(menu), remaining, cost_per_measurement, pooling, marginal_only, permuted)
        if key not in cache:
            cache[key] = choose(models[model_key], menu, h1, h2, executed, remaining, setting,
                                cost_per_measurement, marginal_only=marginal_only)
        return cache[key]
    return policy
