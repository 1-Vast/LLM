"""Section 37 row 2: a fitted response model with exact value-of-information selection.

File summary
- Path: src/evaluation/voi_arm.py
- Purpose: fill the row the table has never run. The arm reads the same public menu as every
  other, but it selects by expected value of information under an outcome model **fitted on
  the development split**, rather than by a fixed order, a declared score or a repair.
- Core points:
  - The fitted quantity is each action's reliability: how often, on development cases, the
    record that action returned carried the outcome the case declared for one of its
    explanations. It is a measured number, not a declaration, and it is what makes the
    outcome model non-degenerate and the value of information finite.
  - Value of information is computed exactly on the two registered explanations under a
    uniform prior: the expected reduction in Bayes decision loss, per unit of cost. An action
    whose expected reduction does not cover its cost is not bought, which is what makes this
    a value-of-information arm rather than a buy-everything arm.
  - The decision step is the shared deterministic interpretation rule, so the only difference
    from the expert baseline is *which* action is selected and when acquisition stops.
  - Nothing here is a biological model. It estimates how often a registered readout returned
    a declared outcome, on one package's development split.
- Interfaces: `fit_action_reliability`, `SimpleModelVOIPolicy`, `expected_value_of_information`
- Depends on: evaluation.baselines, evaluation.cases
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .baselines import ExpertWorkflowPolicy, _prerequisites_met
from .cases import ReplayCase, ReplayView, RevealedEvidence

# A reliability estimated from very few development cases would swing between 0 and 1 on one
# record, so the estimate is smoothed towards "declared" with a one-observation prior. The
# prior is declared here and reported with the fitted table.
SMOOTHING_PRIOR_SUCCESSES = 1.0
SMOOTHING_PRIOR_TRIALS = 2.0
WRONG_DECISION_LOSS = 10.0
DEFERRAL_LOSS = 4.0


def fit_action_reliability(
    cases: Sequence[tuple[ReplayCase, Mapping[str, RevealedEvidence]]],
    *,
    development_cases: Sequence[str],
) -> Mapping[str, float]:
    """How often each action's record carried an outcome the case declared for an explanation.

    Fitted on the development split only. An action never observed there is absent from the
    table, and the policy then falls back to the declared model for it, which is recorded.
    """

    allowed = set(development_cases)
    successes: dict[str, float] = {}
    trials: dict[str, float] = {}
    for case, outcomes in cases:
        if case.public.identifier not in allowed:
            continue
        for identifier, record in outcomes.items():
            item = case.public.action(identifier)
            if item is None:
                continue
            declared = set(item.action.expected_outcomes.values())
            if not declared:
                continue
            trials[identifier] = trials.get(identifier, 0.0) + 1.0
            if record.outcome in declared:
                successes[identifier] = successes.get(identifier, 0.0) + 1.0
    return {
        identifier: (successes.get(identifier, 0.0) + SMOOTHING_PRIOR_SUCCESSES)
        / (count + SMOOTHING_PRIOR_TRIALS)
        for identifier, count in sorted(trials.items())
    }


def _outcome_model(
    item, hypotheses: Sequence[str], reliability: float
) -> Mapping[str, Mapping[str, float]]:
    """The fitted model: the declared outcome with probability ``reliability``, the rest spread."""

    declared = {name: item.action.expected_outcomes.get(name) for name in hypotheses}
    labels = sorted({label for label in declared.values() if label})
    model: dict[str, dict[str, float]] = {}
    for name in hypotheses:
        own = declared.get(name)
        if own is None or len(labels) < 2:
            model[name] = {label: 1.0 / len(labels) for label in labels} if labels else {}
            continue
        others = [label for label in labels if label != own]
        model[name] = {own: reliability}
        for label in others:
            model[name][label] = (1.0 - reliability) / len(others)
    return model


def _bayes_loss(belief: Mapping[str, float], decisions: Mapping[str, str]) -> float:
    """Expected loss of the best terminal act under a belief over the two explanations."""

    options = {*decisions.values(), "defer"}
    best = min(
        sum(
            weight * (0.0 if decisions.get(name) == option else WRONG_DECISION_LOSS)
            for name, weight in belief.items()
        )
        if option != "defer"
        else DEFERRAL_LOSS
        for option in options
    )
    return best


def expected_value_of_information(
    view: ReplayView, item, reliability: float
) -> float:
    """Expected reduction in decision loss from buying one action, under the fitted model."""

    hypotheses = [str(entry["identifier"]) for entry in view.case.hypotheses[:2]]
    decisions = {str(entry["identifier"]): str(entry["development_action"]) for entry in view.case.hypotheses[:2]}
    if len(hypotheses) < 2:
        return 0.0
    belief = {name: 1.0 / len(hypotheses) for name in hypotheses}
    for record in view.revealed:
        observed = view.case.action(record.action_identifier)
        if observed is None:
            continue
        declared = observed.action.expected_outcomes
        if not set(hypotheses).issubset(declared) or len({declared[name] for name in hypotheses}) < 2:
            continue
        updated = {
            name: belief[name] * (0.9 if declared[name] == record.outcome else 0.1) for name in hypotheses
        }
        total = sum(updated.values())
        if total > 0:
            belief = {name: value / total for name, value in updated.items()}
    before = _bayes_loss(belief, decisions)
    model = _outcome_model(item, hypotheses, reliability)
    labels = sorted({label for name in hypotheses for label in model[name]})
    after = 0.0
    for label in labels:
        mass = sum(belief[name] * model[name].get(label, 0.0) for name in hypotheses)
        if mass <= 0:
            continue
        posterior = {
            name: belief[name] * model[name].get(label, 0.0) / mass for name in hypotheses
        }
        after += mass * _bayes_loss(posterior, decisions)
    return before - after


@dataclass
class SimpleModelVOIPolicy(ExpertWorkflowPolicy):
    """Row 2: buy the action with the best value of information per unit cost, or stop."""

    reliability: Mapping[str, float] = field(default_factory=dict)
    default_reliability: float = 0.5
    name: str = "simple_model_voi"

    def next_action(self, view: ReplayView) -> str | None:
        candidates = [item for item in view.available_actions() if _prerequisites_met(item, view)]
        best: tuple[float, str] | None = None
        for item in candidates:
            reliability = float(self.reliability.get(item.action.identifier, self.default_reliability))
            value = expected_value_of_information(view, item, reliability)
            cost = max(float(item.action.cost), 1e-9)
            if value <= cost:
                # Buying it costs more than the decision it could improve. Refusing to buy is
                # the value-of-information answer, not a failure to find an action.
                continue
            score = value / cost
            if best is None or (score, item.action.identifier) > (best[0], best[1]):
                best = (score, item.action.identifier)
        return best[1] if best is not None else None
