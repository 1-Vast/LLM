"""Belief-space measurement planning: choose the next real measurement by its effect on the terminal decision.

File summary
- Path: research/belief_planning/planner.py
- Purpose: the agent's planner for a small, budgeted sequence of measurements. The agent holds a
  belief over the competing hypotheses, formed only from real readings. A world model forecasts,
  per hypothesis, how each legal measurement would read given what has already been measured.
  The planner values each measurement by how its possible readings would change the terminal
  decision and the risk that the decision is wrong, looking ahead over the remaining budget
  (exact finite-horizon expectimax). After every real reading the caller replans from the
  updated belief.
- Core points:
  - Coherence. A reading's probability is the belief-weighted mixture of the per-hypothesis
    forecasts. The belief after a reading is Bayes' rule over *all* candidates. The registered
    rules then decide which hypotheses a reading removes; the probability that the removal was
    wrong is the posterior mass of the removed hypotheses. Zeroing a removed hypothesis before
    scoring the decision, as `acquisition.expected_terminal_decision_value` did, counts the
    rule's evidence twice and reports a wrong-elimination probability of zero.
  - Roles. Forecasts only value actions. They never enter `EvidenceState`, never remove a
    hypothesis and are never recorded as a measurement. The belief moves only on real readings,
    through `update_belief`.
  - Termination follows the evidence runner: the first reading that removes a hypothesis ends
    the episode. A stop is worth zero (deferral or an undetermined decision); a correct
    single-survivor decision is worth ``correct_value``; a wrong one costs ``wrong_loss``.
  - Risk. Every plan carries its forecast probability of a wrong decision, and a conservative
    version in which each wrong-eliminating reading is raised to the one-sided Jeffreys upper
    bound of its reference support. With ``wrong_risk_cap`` set, the planner returns the
    highest-value plan whose conservative wrong probability is within the cap (a Lagrangian scan
    over the wrong loss) and otherwise stops by name.
  - Refusals are kept. An action whose forecast is refused is not valued and is listed with the
    reason; if every action is refused the plan stops with ``world_model_refused``.
- Interfaces: `PlanValue`, `BeliefPlan`, `update_belief`, `plan_measurement`
- Depends on: maestro.acquisition (OutcomeForecast, registered costs), maestro.models; research-only caller
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from math import isfinite
from typing import Callable, Mapping, Sequence

from maestro.acquisition import JEFFREYS_PSEUDOCOUNT, REGISTERED_WRONG_ELIMINATION_COST, OutcomeForecast
from maestro.models import EvidenceAction

History = tuple[tuple[str, str], ...]
"""Real (or hypothesised, inside the lookahead) readings so far: ``((action_identifier, label), ...)``."""

_TOLERANCE = 1e-12
UPPER_QUANTILE = 0.95
LAGRANGE_STEPS = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0)
"""Extra wrong loss tried, in order, when a risk cap binds; the first plan within the cap is used."""


@dataclass(frozen=True)
class PlanValue:
    """What a plan from the current state is forecast to deliver."""

    utility: float = 0.0
    p_correct: float = 0.0
    p_wrong: float = 0.0
    p_wrong_upper: float = 0.0
    measurements: float = 0.0
    cost: float = 0.0
    standard_error: float = 0.0
    """Approximate standard error of the immediate step's expected utility, from reference support."""

    def payload(self) -> dict[str, float]:
        return {"utility": self.utility, "p_correct": self.p_correct, "p_wrong": self.p_wrong,
                "p_wrong_upper": self.p_wrong_upper, "measurements": self.measurements, "cost": self.cost,
                "standard_error": self.standard_error}


_STOP = PlanValue()


@dataclass(frozen=True)
class BeliefPlan:
    """The chosen next measurement (or a named stop), with the audit record of every candidate."""

    chosen: str | None
    status: str
    reason: str | None
    value: PlanValue
    evaluations: Mapping[str, PlanValue] = field(default_factory=dict)
    contingent: Mapping[str, str | None] = field(default_factory=dict)
    refusals: Mapping[str, str] = field(default_factory=dict)
    belief: Mapping[str, float] = field(default_factory=dict)
    wrong_loss_used: float = REGISTERED_WRONG_ELIMINATION_COST
    anchor: str | None = None
    """How the baseline anchor acted: None (no baseline), `baseline_kept`, `deviation_supported`,
    `stop_supported` or `baseline_kept_instead_of_stop`."""

    def payload(self) -> dict[str, object]:
        return {
            "chosen": self.chosen, "status": self.status, "reason": self.reason, "anchor": self.anchor,
            "value": self.value.payload(), "belief": dict(self.belief),
            "evaluations": {key: value.payload() for key, value in sorted(self.evaluations.items())},
            "contingent": dict(sorted(self.contingent.items())), "refusals": dict(sorted(self.refusals.items())),
            "wrong_loss_used": self.wrong_loss_used,
        }


def _likelihoods(forecast: OutcomeForecast, candidates: Sequence[str]) -> tuple[dict, dict] | str:
    """Normalised per-hypothesis label probabilities and support, or the reason they are unusable."""

    if forecast.refusal:
        return str(forecast.refusal)
    likelihood, support = {}, {}
    for hypothesis in candidates:
        branch = forecast.branch_for(hypothesis)
        if branch is None:
            return f"forecast_missing_hypothesis:{hypothesis}"
        values = {str(label): float(p) for label, p in branch.probabilities.items()}
        if any(not isfinite(p) or p < 0 for p in values.values()):
            return f"invalid_probability:{hypothesis}"
        total = sum(values.values())
        if total <= 0:
            return f"empty_probability:{hypothesis}"
        likelihood[hypothesis] = {label: p / total for label, p in values.items()}
        support[hypothesis] = max(int(branch.support), 0)
    return likelihood, support


def _upper(p: float, n: int) -> float:
    """One-sided Jeffreys upper bound of a probability estimated as ``p`` from ``n`` units."""

    if p >= 1.0 or n <= 0:
        return 1.0
    return _jeffreys_upper(round(p, 9), int(n))


@lru_cache(maxsize=65536)
def _jeffreys_upper(p: float, n: int) -> float:
    from scipy.stats import beta
    k = p * n
    return float(beta.ppf(UPPER_QUANTILE, k + JEFFREYS_PSEUDOCOUNT, n - k + JEFFREYS_PSEUDOCOUNT))


def update_belief(belief: Mapping[str, float], forecast: OutcomeForecast, label: str) -> dict[str, float]:
    """Bayes' rule for one real reading; hypotheses the forecast cannot score keep their weight.

    A label no hypothesis forecasts (probability zero everywhere) leaves the belief unchanged,
    because a reading the world model did not anticipate carries no usable likelihood.
    """

    candidates = tuple(belief)
    parsed = _likelihoods(forecast, candidates)
    if isinstance(parsed, str):
        return dict(belief)
    likelihood, _ = parsed
    raw = {h: float(belief[h]) * likelihood[h].get(label, 0.0) for h in candidates}
    total = sum(raw.values())
    if total <= _TOLERANCE:
        return dict(belief)
    return {h: value / total for h, value in raw.items()}


def plan_measurement(
    candidates: Sequence[str],
    belief: Mapping[str, float] | None,
    legal: Callable[[History], Sequence[EvidenceAction]],
    forecast: Callable[[EvidenceAction, History], OutcomeForecast],
    consequences: Mapping[str, frozenset[str]],
    *,
    horizon: int,
    history: History = (),
    price: Callable[[EvidenceAction], float] | float = 0.0,
    correct_value: float = 1.0,
    wrong_loss: float = REGISTERED_WRONG_ELIMINATION_COST,
    wrong_risk_cap: float | None = None,
    baseline: str | None = None,
    deviation_z: float | None = None,
) -> BeliefPlan:
    """Choose the next measurement by exact expectimax over the remaining ``horizon`` measurements.

    ``legal(history)`` returns the measurements the runner would offer after ``history`` (budget,
    ordering and repetition rules are the runner's). ``forecast(action, history)`` is the world
    model: per hypothesis, the distribution of registered reading labels for ``action`` given the
    readings in ``history``. ``consequences`` maps a label to the hypotheses the registered rules
    remove. ``price`` is a utility-scale price per measurement, kept apart from assay-day costs.

    Baseline anchoring (safe policy improvement with baseline bootstrapping, Laroche et al. 2019).
    ``baseline`` is the next action of an established protocol, for example a fixed expert order.
    With ``deviation_z`` set, the planner departs from it only when the forecast gain exceeds
    ``deviation_z`` standard errors of the two actions' immediate expected utilities. It stops
    instead of taking the baseline only when the baseline step is forecast negative by that
    margin. A world model built from a few references per class otherwise chases noise that an
    expert order does not (2026-09-27 development replay, SciPlex3 A).
    """

    names = tuple(sorted(set(candidates)))
    if len(names) < 2:
        raise ValueError("at least two candidate hypotheses are required")
    if horizon < 0:
        raise ValueError("horizon must be nonnegative")
    if not (isfinite(correct_value) and isfinite(wrong_loss)) or correct_value <= 0 or wrong_loss <= 0:
        raise ValueError("decision values must be positive and finite")
    if wrong_risk_cap is not None and not 0.0 <= wrong_risk_cap <= 1.0:
        raise ValueError("wrong_risk_cap must be a probability")
    weights = {h: 1.0 / len(names) for h in names} if belief is None else {h: float(belief.get(h, 0.0)) for h in names}
    total = sum(weights.values())
    if total <= 0 or any(not isfinite(w) or w < 0 for w in weights.values()):
        raise ValueError("belief must be a nonnegative distribution with positive mass")
    weights = {h: w / total for h, w in weights.items()}
    pricing = price if callable(price) else (lambda _action, p=float(price): p)
    cache: dict = {}

    def cached_forecast(action, past):
        key = (action.identifier, past)
        if key not in cache:
            cache[key] = forecast(action, past)
        return cache[key]

    def solve(loss: float):
        memo: dict = {}
        refusals: dict[str, str] = {}

        def value(b: Mapping[str, float], past: History, depth: int):
            memo_key = (tuple(round(b[h], 12) for h in names), past, depth)
            if memo_key in memo:
                return memo[memo_key]
            best, best_id, evaluations, contingent = _STOP, None, {}, {}
            if depth > 0:
                for action in sorted(legal(past), key=lambda a: a.identifier):
                    parsed = _likelihoods(cached_forecast(action, past), names)
                    if isinstance(parsed, str):
                        if not past:
                            refusals[action.identifier] = parsed
                        continue
                    likelihood, support = parsed
                    labels = sorted({label for h in names for label in likelihood[h]})
                    variance = 0.0
                    for h in names:
                        right = sum(p for lab, p in likelihood[h].items()
                                    if consequences.get(lab) and h not in consequences[lab])
                        wrong = sum(p for lab, p in likelihood[h].items() if h in consequences.get(lab, frozenset()))
                        spread = (correct_value ** 2 * right * (1 - right) + loss ** 2 * wrong * (1 - wrong)
                                  + 2 * correct_value * loss * right * wrong)
                        variance += b[h] ** 2 * spread / (support[h] + 1.0)
                    u = w = wu = c = m = cost = 0.0
                    follow: dict[str, str | None] = {}
                    for label in labels:
                        mass = sum(b[h] * likelihood[h].get(label, 0.0) for h in names)
                        if mass <= _TOLERANCE:
                            continue
                        post = {h: b[h] * likelihood[h].get(label, 0.0) / mass for h in names}
                        removed = frozenset(consequences.get(label, frozenset())) & set(names)
                        # conservative mass of this reading under each hypothesis it would wrongly remove
                        upper_mass = sum(b[h] * _upper(likelihood[h].get(label, 0.0), support[h]) for h in removed)
                        if removed:
                            survivors = [h for h in names if h not in removed]
                            wrong_given = sum(post[h] for h in removed)
                            right = post[survivors[0]] if len(survivors) == 1 else 0.0
                            u += mass * (correct_value * right - loss * wrong_given)
                            w += mass * wrong_given
                            wu += upper_mass
                            c += mass * right
                            follow[label] = None
                        else:
                            sub, sub_id = value(post, past + ((action.identifier, label),), depth - 1)[:2]
                            u += mass * sub.utility
                            w += mass * sub.p_wrong
                            wu += mass * sub.p_wrong_upper
                            c += mass * sub.p_correct
                            m += mass * sub.measurements
                            cost += mass * sub.cost
                            follow[label] = sub_id
                    step_price = float(pricing(action))
                    item = PlanValue(u - step_price, c, w, min(wu, 1.0), 1.0 + m, float(action.cost) + cost,
                                     variance ** 0.5)
                    evaluations[action.identifier] = item
                    contingent[action.identifier] = follow
                    if item.utility > best.utility + _TOLERANCE:
                        best, best_id = item, action.identifier
            memo[memo_key] = (best, best_id, evaluations, contingent)
            return memo[memo_key]

        top, top_id, evaluations, contingent = value(weights, tuple(history), horizon)
        return top, top_id, evaluations, contingent, refusals

    top, top_id, evaluations, contingent, refusals = solve(wrong_loss)
    used = wrong_loss
    if wrong_risk_cap is not None and top_id is not None and top.p_wrong_upper > wrong_risk_cap + _TOLERANCE:
        for extra in LAGRANGE_STEPS[1:]:
            used = wrong_loss + extra
            candidate = solve(used)
            if candidate[1] is None or candidate[0].p_wrong_upper <= wrong_risk_cap + _TOLERANCE:
                top, top_id, evaluations, contingent, refusals = candidate
                break
        else:
            top_id = None
        if top_id is not None and top.p_wrong_upper > wrong_risk_cap + _TOLERANCE:
            top_id = None
        if top_id is None:
            return BeliefPlan(None, "stopped", "wrong_risk_cap", _STOP, evaluations, {}, refusals, weights, used)
    anchor = None
    if baseline is not None and deviation_z is not None and baseline in evaluations:
        kept = evaluations[baseline]
        if top_id is None:
            if kept.utility + deviation_z * kept.standard_error < 0:
                anchor = "stop_supported"
            else:
                top_id, top, anchor = baseline, kept, "baseline_kept_instead_of_stop"
        elif top_id != baseline:
            margin = deviation_z * (top.standard_error ** 2 + kept.standard_error ** 2) ** 0.5
            if top.utility - kept.utility > margin:
                anchor = "deviation_supported"
            else:
                top_id, top, anchor = baseline, kept, "baseline_kept"
        else:
            anchor = "baseline_kept"
    follow = contingent.get(top_id, {}) if top_id else {}
    if top_id is None:
        if evaluations:
            return BeliefPlan(None, "stopped", "no_positive_value", _STOP, evaluations, {}, refusals, weights, used,
                              anchor)
        reason = "world_model_refused" if refusals else "no_legal_action"
        return BeliefPlan(None, "stopped", reason, _STOP, evaluations, {}, refusals, weights, used, anchor)
    return BeliefPlan(top_id, "selected", None, top, evaluations, follow, refusals, weights, used, anchor)
