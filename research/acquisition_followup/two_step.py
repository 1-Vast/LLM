"""Bounded two-measurement planning on existing, real SciPlex3 reference transitions.

The agent evaluates a small contingent plan; the world model supplies label
distributions. Only a purchased real result goes through the evidence path.
This is an exploratory policy, not a change to production defaults.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "acquisition_link"))
import evaluate as V

C, E = V.C, V.E
LABELS = (V.MATCH[True], V.MATCH[False], V.UNRESOLVED, V.ABSENT)
LABEL_OF = {"eliminate_b": LABELS[0], "eliminate_a": LABELS[1],
            "ambiguous": V.UNRESOLVED, "undetected": V.ABSENT}


def probabilities(forecast, hypothesis):
    branch = forecast.branch_for(hypothesis)
    return {label: (branch.support * branch.probabilities.get(label, 0.0) + 0.5)
            / (branch.support + 2.0) for label in LABELS}


def conditional_forecast(ft, params, first, label, second, h1, h2):
    """Same reference compound at both conditions; no product of marginal forecasts."""
    identifier = C.action_id(second)
    if first not in ft.tables or second not in ft.tables or not params["eliminates"]:
        return V.OutcomeForecast(identifier, refusal="paired_condition_not_supported")
    a = C.loo_outcomes(ft, first, params["floor"], params["margin"])
    b = C.loo_outcomes(ft, second, params["floor"], params["margin"])
    branches = []
    for own, other in ((h1, h2), (h2, h1)):
        def mapped(value):
            if own == h2 and value in ("eliminate_b", "eliminate_a"):
                value = "eliminate_a" if value == "eliminate_b" else "eliminate_b"
            return LABEL_OF.get(value)

        table = ft.tables[second]
        refs = [c for c, klass in zip(table.names, table.klass)
                if klass == own and (c, other) in a and mapped(a[c, other]) == label]
        if not refs:
            return V.OutcomeForecast(identifier, refusal=f"no_paired_reference_for_branch:{own}:{label}")
        readings = [mapped(b[c, other]) for c in refs]
        branches.append(V.OutcomeBranch(own, {y: readings.count(y) / len(refs) for y in LABELS}, len(refs)))
    return V.OutcomeForecast(identifier, tuple(branches),
                             basis=f"paired training references; fold {ft.fold}; {C.action_id(first)}={label}")


def plan_two_step(menu, h1, h2, forecasts, conditional, *, budget=16.0, horizon=2):
    """Score terminal outcomes with the first-reading likelihood under each hypothesis.

    Neutral first readings change planning weights, never the mechanism evidence
    set. A zero-immediate-value measurement may be selected if its continuation
    is useful. Unsupported conditional branches stop without invented readings.
    """
    choices = []
    for first in menu:
        forecast = forecasts[C.action_id(first)]
        if forecast.refusal or E.days(first) > budget:
            continue
        p = {h: probabilities(forecast, h) for h in (h1, h2)}
        correct = 0.5 * (p[h1][LABELS[0]] + p[h2][LABELS[1]])
        wrong = 0.5 * (p[h1][LABELS[1]] + p[h2][LABELS[0]])
        immediate_utility = correct - 2 * wrong
        expected_days = E.days(first)
        followups, refusals = {}, {}
        if horizon in (1, 2):
            for label in (V.UNRESOLVED, V.ABSENT):
                tails = []
                for second in menu:
                    if second == first or second[1] < first[1] or E.days(first) + E.days(second) > budget:
                        continue
                    next_forecast = conditional(first, label, second)
                    if next_forecast.refusal:
                        refusals[f"{label}:{C.action_id(second)}"] = next_forecast.refusal
                        continue
                    q = {h: probabilities(next_forecast, h) for h in (h1, h2)}
                    c = 0.5 * (p[h1][label] * q[h1][LABELS[0]] + p[h2][label] * q[h2][LABELS[1]])
                    w = 0.5 * (p[h1][label] * q[h1][LABELS[1]] + p[h2][label] * q[h2][LABELS[0]])
                    if c > 2 * w + 1e-12:
                        tails.append((c - 2 * w, E.days(second), C.action_id(second), second, c, w))
                if tails:
                    tail = min(tails, key=lambda x: (-x[0], x[1], x[2]))
                    followups[label] = tail[3]
                    correct += tail[4]
                    wrong += tail[5]
                    expected_days += 0.5 * (p[h1][label] + p[h2][label]) * tail[1]
        utility = correct - 2 * wrong
        selection_utility = utility if horizon == 2 else immediate_utility
        if selection_utility > 1e-12:
            choices.append({"first": first, "followups": followups, "p_correct": correct,
                            "p_wrong": wrong, "utility": utility, "expected_days": expected_days,
                            "selection_utility": selection_utility, "immediate_utility": immediate_utility,
                            "conditional_refusals": refusals})
    return min(choices, key=lambda x: (-x["selection_utility"], x["expected_days"], C.action_id(x["first"]))) if choices else None


def policy(ctx, compound, h1, h2, executed, menu, *, horizon=2, permuted=False):
    # No held-out identity or target profile enters planning. Cache by contrast,
    # horizon and training-label control; the chosen real result selects a branch.
    cache = ctx.extra.setdefault("two_step_plans", {})
    key = (h1, h2, horizon, permuted)
    if key not in cache:
        ft = ctx.ft_perm if permuted else ctx.ft
        forecaster = V.ReferenceCardForecaster(ft, ctx.params)
        forecasts = {C.action_id(k): forecaster.forecast_key(k, h1, h2) for k in ctx.tier.keys}
        cache[key] = plan_two_step(
            ctx.tier.keys, h1, h2, forecasts,
            lambda a, y, b: conditional_forecast(ft, ctx.params, a, y, b, h1, h2), horizon=horizon,
        )
    plan = cache[key]
    if plan is None:
        return None, {"reason": "no_positive_terminal_utility"}
    if not executed:
        return plan["first"], {**plan, "followups": {y: C.action_id(k) for y, k in plan["followups"].items()},
                              "evidence_kind": "model_prediction"}
    label = LABEL_OF.get(executed[0]["outcome"])
    chosen = plan["followups"].get(label)
    if chosen not in menu:
        return None, {"reason": "no_supported_positive_utility_continuation", "observed_label": label}
    return chosen, {"conditioned_on": executed[0]["action"], "observed_label": label,
                    "evidence_kind": "model_prediction"}
