"""Measurement choice from declared detection power, or from predicted readings under each hypothesis.

File summary
- Path: src/maestro/acquisition.py
- Purpose: choose an evidence bundle by the *probability that it answers* rather than by the
  labels it mentions, using the ``detection_power`` every action may already declare; and, when a
  forecaster predicts how each action would read under each hypothesis, choose the single next
  measurement by how well the registered interpretation rules would separate the hypotheses.
- Core points:
  - Plain set cover reads a bundle as covering a hypothesis whenever one selected action claims
    it. An assay that returns an uninterpretable result half the time covers it half the time, so
    the bundle's coverage is ``1 - prod(1 - p_a)`` per hypothesis: a stochastic set-cover
    objective, solved exactly here over the small pools the framework actually has.
  - The objective is expected coverage, not information value and not experimental utility; the
    cost, size, prediction-priority and identifier tie-breaks keep the choice auditable and
    deterministic. A prediction priority is consulted only after coverage, cost and size, so it
    can break a tie but never buy an extra or costlier action.
  - An action that declares no ``detection_power`` is treated as certain and *named* in the
    returned assumptions, because assuming a value and hiding the assumption is how a declared
    field stops being a declaration.
  - A pool above the exhaustive cap returns ``too_large`` rather than a heuristic answer, for the
    same reason ``selection.py`` refuses: an exact method that silently becomes approximate is a
    claim the code cannot keep.
  - ``select_discriminating_action`` reads an ``OutcomeForecast``: per hypothesis, the predicted
    distribution over registered outcome labels and the number of independent measured units it
    rests on. What a reading would eliminate comes from the registered rules, never from the
    forecast, so absence and unresolved readings earn no credit however differently the
    hypotheses predict them. The choice is lexicographic: legality and budget; a wrong-risk gate
    at the break-even of the declared utility; the one-sided 95% lower bound of rule-conditioned
    discrimination (correct minus wrong elimination probability); support; cost; exposure time;
    predicted magnitude; identifier. Zero support refuses by name; thin support is served,
    flagged and discounted by the Jeffreys prior, never deleted.
  - A forecast is a planning prediction. It chooses which real measurement to buy and never
    reaches ``EvidenceState``; one measurement is chosen per round because forecasts of different
    actions on the same system are not independent, and the loop replans on the real result.
- Interfaces: `ExpectedCoveragePlan`, `select_expected_coverage`, `OutcomeBranch`,
  `OutcomeForecast`, `OutcomeForecaster`, `ActionDiscrimination`, `DiscriminationPlan`,
  `outcome_consequences`, `select_discriminating_action`
- Depends on: maestro.models, maestro.outcome (registered rules and the evidence state),
  maestro.handoff (rejection reasons), maestro.selection (the plan type)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from math import isfinite, sqrt
from typing import Iterable, Mapping, Protocol, Sequence

from .handoff import RejectedCandidate
from .models import EvidenceAction, EvidenceKind, EvidenceScope, FunctionalInterventionProfile, MechanismContrast
from .outcome import EvidenceState, OutcomeRule
from .selection import BudgetedEvidencePlan

MAXIMUM_CANDIDATES = 16
_TOLERANCE = 1e-12


@dataclass(frozen=True)
class ExpectedCoveragePlan:
    """A bundle, the probability it answers each hypothesis, and what it cost."""

    plan: BudgetedEvidencePlan
    coverage_probability: Mapping[str, float] = field(default_factory=dict)
    expected_coverage: float = 0.0
    rejected: tuple[RejectedCandidate, ...] = ()
    assumptions: tuple[str, ...] = ()
    status: str = "optimal"
    reason: str | None = None
    dependence_groups: Mapping[str, str] = field(default_factory=dict)

    def probability_of(self, hypothesis: str) -> float:
        return float(self.coverage_probability.get(hypothesis, 0.0))


def _probability(action: EvidenceAction) -> float:
    return 1.0 if action.detection_power is None else float(action.detection_power)


def _coverage_probabilities(
    selected: Sequence[EvidenceAction], required: frozenset[str], groups: Mapping[str, str]
) -> dict[str, float]:
    probabilities: dict[str, float] = {}
    for hypothesis in required:
        group_power: dict[str, float] = {}
        for action in selected:
            if hypothesis in action.distinguishes:
                group = groups[action.identifier]
                group_power[group] = max(group_power.get(group, 0.0), _probability(action))
        remaining = 1.0
        for power in group_power.values():
            remaining *= 1.0 - power
        probabilities[hypothesis] = 1.0 - remaining
    return probabilities


def _dependence_groups(actions: Sequence[EvidenceAction], sources: Mapping[str, str]) -> dict[str, str]:
    """Freeze connected source clusters over the menu; shared evidence is not a new trial.

    Within a component, max(p) is a conservative union bound under unknown dependence.
    Distinct components still require the explicit conditional-independence assumption.
    Actions without provenance retain the legacy independent-trial assumption.
    """
    components: list[tuple[set[str], set[str]]] = []
    for action in actions:
        refs = {sources.get(ref, ref) for ref in action.source_ids}
        members = {action.identifier}
        merged = [(ids, keys) for ids, keys in components if keys & refs]
        for ids, keys in merged:
            members.update(ids)
            refs.update(keys)
            components.remove((ids, keys))
        components.append((members, refs))
    return {identifier: min(members) for members, _ in components for identifier in members}


def select_expected_coverage(
    required: frozenset[str],
    actions: Sequence[EvidenceAction],
    profile: FunctionalInterventionProfile,
    budget: float,
    *,
    coverage_threshold: float = 0.0,
    weights: Mapping[str, float] | None = None,
    source_groups: Mapping[str, str] | None = None,
    action_priorities: Mapping[str, float] | None = None,
) -> ExpectedCoveragePlan:
    """Maximise expected coverage under a budget; ties go to cost, size, priority, then label.

    ``coverage_threshold`` is the probability above which a hypothesis counts as covered in the
    returned sets. The default of zero reproduces set semantics for the covered/uncovered fields
    while the objective still uses the probabilities, so a caller can see the difference between
    "covered in name" and "covered with stated probability".

    ``action_priorities`` are the world model's per-action magnitudes. They are summed over a
    bundle and consulted only between plans of equal expected coverage, cost and size, exactly as
    ``BudgetedEvidenceSelector`` does; without them the label decides, as before.
    """

    if isinstance(budget, bool) or not isfinite(budget) or budget < 0:
        raise ValueError("Budget must be nonnegative.")
    if len({action.identifier for action in actions}) != len(actions):
        raise ValueError("duplicate_action_identifier")
    for action in actions:
        if isinstance(action.cost, bool) or not isinstance(action.cost, (int, float)) or not isfinite(action.cost) or action.cost < 0:
            raise ValueError("invalid_action_cost")
        if action.detection_power is not None and (isinstance(action.detection_power, bool)
                or not isinstance(action.detection_power, (int, float))
                or not isfinite(action.detection_power) or not 0 <= action.detection_power <= 1):
            raise ValueError("invalid_detection_power")
    if source_groups is not None and (any(not isinstance(k, str) or not k.strip()
            or not isinstance(v, str) or not v.strip() for k, v in source_groups.items())
            or {ref for action in actions for ref in action.source_ids} - source_groups.keys()):
        raise ValueError("incomplete_source_groups")
    if not 0.0 <= coverage_threshold <= 1.0:
        raise ValueError("A coverage threshold must lie in [0, 1].")
    weights = dict(weights or {})
    if set(weights) - required or any(
        isinstance(value, bool) or not isfinite(value) or value < 0 for value in weights.values()
    ):
        raise ValueError("Weights must be finite nonnegative values for required hypotheses.")
    priorities = dict(action_priorities or {})
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
           for value in priorities.values()):
        raise ValueError("invalid_action_priority")
    if not required:
        return ExpectedCoveragePlan(
            plan=BudgetedEvidencePlan((), frozenset(), frozenset(), 0.0, ()),
            expected_coverage=0.0,
        )

    executable: list[EvidenceAction] = []
    waiting: list[str] = []
    for action in sorted(actions, key=lambda item: item.identifier):
        if action.cost < 0:
            continue
        missing = profile.unmeasured(action.prerequisites)
        if missing:
            waiting.append(f"{action.identifier}: {', '.join(missing)}")
        else:
            executable.append(action)
    assumptions = tuple(
        f"assumed_certain_execution:{action.identifier}"
        for action in executable
        if action.detection_power is None
    )
    groups = _dependence_groups(executable, source_groups or {})
    if len(set(groups.values())) < len(executable):
        assumptions += ("worst_case_dependence_within_source_component",)
    if len(set(groups.values())) > 1:
        assumptions += ("conditional_independence_between_source_components",)
    if len(executable) > 1 and any(not action.source_ids for action in executable):
        assumptions += ("unverified_independence_for_actions_without_source_ids",)
    if len(executable) > MAXIMUM_CANDIDATES:
        rejected = tuple(
            RejectedCandidate(action.identifier, "exact_candidate_limit_exceeded")
            for action in actions
        )
        return ExpectedCoveragePlan(
            plan=BudgetedEvidencePlan(
                (), frozenset(), required, 0.0, tuple(waiting),
                {item.action_identifier: item.reason for item in rejected},
            ),
            assumptions=assumptions,
            status="too_large",
            dependence_groups=groups,
            rejected=rejected,
            reason=(
                f"candidate pool has {len(executable)} executable actions; exact enumeration stops at "
                f"{MAXIMUM_CANDIDATES}"
            ),
        )

    best: tuple[EvidenceAction, ...] = ()
    best_probabilities: dict[str, float] = {hypothesis: 0.0 for hypothesis in required}
    best_expected = 0.0
    best_cost = 0.0
    for size in range(1, len(executable) + 1):
        for candidate in combinations(executable, size):
            cost = sum(action.cost for action in candidate)
            if cost > budget + _TOLERANCE:
                continue
            probabilities = _coverage_probabilities(candidate, required, groups)
            expected = sum(weights.get(name, 1.0) * value for name, value in probabilities.items())
            if _is_better(candidate, expected, cost, best, best_expected, best_cost, priorities):
                best, best_probabilities, best_expected, best_cost = (
                    candidate,
                    probabilities,
                    expected,
                    cost,
                )

    covered = frozenset(
        hypothesis
        for hypothesis, probability in best_probabilities.items()
        if probability > coverage_threshold + _TOLERANCE
    )
    rejected = _rejections(actions, best, best_probabilities, budget, profile, groups)
    plan = BudgetedEvidencePlan(
        actions=best,
        covered=covered & required,
        uncovered=required - covered,
        total_cost=best_cost,
        waiting_for_prerequisites=tuple(waiting),
        rejection_reasons={item.action_identifier: item.reason for item in rejected},
    )
    return ExpectedCoveragePlan(
        plan=plan,
        coverage_probability=best_probabilities,
        expected_coverage=best_expected,
        rejected=rejected,
        assumptions=assumptions,
        dependence_groups=groups,
    )


def _is_better(
    candidate: Sequence[EvidenceAction],
    expected: float,
    cost: float,
    best: Sequence[EvidenceAction],
    best_expected: float,
    best_cost: float,
    priorities: Mapping[str, float] | None = None,
) -> bool:
    if abs(expected - best_expected) > _TOLERANCE:
        return expected > best_expected
    if abs(cost - best_cost) > _TOLERANCE:
        return cost < best_cost
    if len(candidate) != len(best):
        return len(candidate) < len(best)
    if priorities and best:
        priority = sum(priorities.get(action.identifier, 0.0) for action in candidate)
        best_priority = sum(priorities.get(action.identifier, 0.0) for action in best)
        if abs(priority - best_priority) > _TOLERANCE:
            return priority > best_priority
    return tuple(action.identifier for action in candidate) < tuple(action.identifier for action in best)


def _rejections(
    actions: Sequence[EvidenceAction],
    chosen: Sequence[EvidenceAction],
    probabilities: Mapping[str, float],
    budget: float,
    profile: FunctionalInterventionProfile,
    groups: Mapping[str, str],
) -> tuple[RejectedCandidate, ...]:
    """Name why each unselected action is absent, from what the selection knows."""

    selected = {action.identifier for action in chosen}
    chosen_cost = sum(action.cost for action in chosen)
    rejected: list[RejectedCandidate] = []
    for action in actions:
        if action.identifier in selected:
            continue
        missing = profile.unmeasured(action.prerequisites)
        widened = _coverage_probabilities((*chosen, action), frozenset(probabilities),
                                          {**groups, action.identifier: groups.get(action.identifier, action.identifier)})
        gain = sum(widened.values()) - sum(probabilities.values())
        if missing:
            reason = f"waiting_for_prerequisite:{', '.join(missing)}"
        elif chosen_cost + action.cost > budget + _TOLERANCE:
            reason = "exceeds_budget"
        elif gain <= _TOLERANCE:
            reason = "no_marginal_expected_coverage"
        else:
            reason = "not_selected"
        rejected.append(RejectedCandidate(action.identifier, reason))
    return tuple(rejected)


# ---------------------------------------------------------------------------------------------
# Choosing by predicted discrimination: how each hypothesis would make the registered rules read.

LOWER_BOUND_Z = 1.6448536269514722
"""One-sided 95% standard-normal quantile used for the conservative discrimination bound."""

JEFFREYS_PSEUDOCOUNT = 0.5
"""Dirichlet(1/2) mass added to every outcome label: the Jeffreys prior, which shrinks thin support hard."""

REGISTERED_WRONG_ELIMINATION_COST = 2.0
"""Loss of a wrong elimination in units of a correct one: the declared +1/0/-2 measurement-choice
utility of the 2026-09-26 protocol. A case may declare its own; the gate's break-even follows it."""

LOW_SUPPORT_UNITS = 1
"""A branch resting on this many independent measured units is served, flagged and discounted."""


@dataclass(frozen=True)
class OutcomeBranch:
    """How the registered reading of one action is forecast to come out if one hypothesis is true.

    ``probabilities`` maps outcome labels (the ``outcome_label`` of registered rules) to forecast
    probabilities that sum to one. ``support`` counts the independent measured units (reference
    compounds, not simulation draws) the forecast rests on; it sets how hard the forecast is
    shrunk and how wide its interval is.
    """

    hypothesis: str
    probabilities: Mapping[str, float]
    support: int


@dataclass(frozen=True)
class OutcomeForecast:
    """A planning prediction of one action's reading under each competing hypothesis.

    A forecaster that has no basis for an action says so in ``refusal`` with a named reason. The
    record is a model prediction by construction: a forecast claiming measurement status is
    refused, so prediction confidence cannot be read as measured evidence.
    """

    action_identifier: str
    branches: tuple[OutcomeBranch, ...] = ()
    basis: str = ""
    refusal: str | None = None
    model_version: str | None = None
    evidence_kind: EvidenceKind = EvidenceKind.MODEL_PREDICTION

    def branch_for(self, hypothesis: str) -> OutcomeBranch | None:
        return next((branch for branch in self.branches if branch.hypothesis == hypothesis), None)


class OutcomeForecaster(Protocol):
    """Anything that can forecast, per registered action, the reading under each hypothesis."""

    name: str

    def forecast(
        self,
        contrast: MechanismContrast,
        actions: Sequence[EvidenceAction],
        evidence: EvidenceState | None,
    ) -> Mapping[str, OutcomeForecast]:
        ...


@dataclass(frozen=True)
class ActionDiscrimination:
    """What the selector computed for one action, and the named reason it was or was not chosen."""

    action_identifier: str
    admissible: bool
    reason: str
    p_correct: float | None = None
    p_wrong: float | None = None
    discrimination: float | None = None
    discrimination_lower: float | None = None
    total_variation: float | None = None
    support: int = 0
    low_support: bool = False
    cost: float = 0.0
    time_hours: float | None = None
    priority: float = 0.0

    def payload(self) -> dict[str, object]:
        return {
            "admissible": self.admissible, "reason": self.reason, "p_correct": self.p_correct,
            "p_wrong": self.p_wrong, "discrimination": self.discrimination,
            "discrimination_lower": self.discrimination_lower, "total_variation": self.total_variation,
            "support": self.support, "low_support": self.low_support, "cost": self.cost,
            "time_hours": self.time_hours, "priority": self.priority,
        }


@dataclass(frozen=True)
class DiscriminationPlan:
    """The chosen next measurement, every candidate's evaluation, and the named status."""

    plan: BudgetedEvidencePlan
    evaluations: tuple[ActionDiscrimination, ...]
    status: str = "selected"
    reason: str | None = None
    assumptions: tuple[str, ...] = ()

    @property
    def chosen(self) -> ActionDiscrimination | None:
        if not self.plan.actions:
            return None
        chosen = self.plan.actions[0].identifier
        return next((item for item in self.evaluations if item.action_identifier == chosen), None)

    def payload(self) -> dict[str, object]:
        return {
            "status": self.status, "reason": self.reason,
            "chosen": self.plan.actions[0].identifier if self.plan.actions else None,
            "assumptions": list(self.assumptions),
            "rejection_reasons": dict(sorted(self.plan.rejection_reasons.items())),
            "evaluations": {item.action_identifier: item.payload() for item in self.evaluations},
        }


def outcome_consequences(rules: Iterable[OutcomeRule]) -> dict[str, frozenset[str]]:
    """What each registered reading would remove from the compatible set.

    Only a rule at mechanism-contrast scope removes anything, which is exactly when
    ``EvidenceState.apply`` removes anything. A label shared by several rules takes the union, so
    the wrong-elimination risk it carries is never understated.
    """

    consequences: dict[str, frozenset[str]] = {}
    for rule in rules:
        removed = frozenset(rule.eliminates) if rule.scope is EvidenceScope.MECHANISM_CONTRAST else frozenset()
        consequences[rule.outcome_label] = consequences.get(rule.outcome_label, frozenset()) | removed
    return consequences


def _forecast_problem(forecast: OutcomeForecast, identifier: str, candidates: frozenset[str]) -> str | None:
    if forecast.refusal:
        return str(forecast.refusal)
    if forecast.action_identifier != identifier:
        return "forecast_for_another_action"
    if forecast.evidence_kind is EvidenceKind.REAL_MEASUREMENT:
        return "forecast_claims_measurement_status"
    seen: set[str] = set()
    for branch in forecast.branches:
        if branch.hypothesis in seen:
            return f"duplicate_branch:{branch.hypothesis}"
        seen.add(branch.hypothesis)
        support = branch.support
        if isinstance(support, bool) or not isinstance(support, int) or support < 0:
            return f"invalid_support:{branch.hypothesis}"
        values = list(branch.probabilities.values())
        if not values or any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0
            for value in values
        ) or abs(sum(values) - 1.0) > 1e-6:
            return f"invalid_probabilities:{branch.hypothesis}"
    for hypothesis in sorted(candidates):
        branch = forecast.branch_for(hypothesis)
        if branch is None:
            return f"forecast_missing_hypothesis:{hypothesis}"
        if branch.support == 0:
            return f"no_reference_for_hypothesis:{hypothesis}"
    return None


def _score(
    forecast: OutcomeForecast,
    candidates: frozenset[str],
    consequences: Mapping[str, frozenset[str]],
) -> tuple[float, float, float, float | None, int, float]:
    """Pooled correct and wrong elimination probabilities, discrimination variance, TV and support.

    Each branch is a Dirichlet posterior with the Jeffreys prior over every registered label plus
    any label the forecast adds. A correct reading removes a candidate other than the branch's
    hypothesis and not that hypothesis; a wrong reading removes it. The pooled values average the
    branches (a uniform prior over the candidates), and the variance of the pooled discrimination
    is the weighted sum of the independent branch variances.
    """

    labels = sorted(set(consequences) | {label for branch in forecast.branches for label in branch.probabilities})
    ordered = sorted(candidates)
    weight = 1.0 / len(ordered)
    p_correct = p_wrong = variance = observed_correct = 0.0
    means: list[dict[str, float]] = []
    supports: list[int] = []
    for hypothesis in ordered:
        branch = forecast.branch_for(hypothesis)
        if branch is None:
            raise ValueError(f"forecast_missing_hypothesis:{hypothesis}")
        alpha = {label: branch.probabilities.get(label, 0.0) * branch.support + JEFFREYS_PSEUDOCOUNT for label in labels}
        total = sum(alpha.values())
        removes = {label: consequences.get(label, frozenset()) & candidates for label in labels}
        correct = [label for label in labels if removes[label] and hypothesis not in removes[label]]
        wrong = [label for label in labels if hypothesis in removes[label]]
        a_correct = sum(alpha[label] for label in correct)
        a_wrong = sum(alpha[label] for label in wrong)
        signed, squared = a_correct - a_wrong, a_correct + a_wrong
        p_correct += weight * a_correct / total
        p_wrong += weight * a_wrong / total
        variance += weight * weight * max(squared / total - (signed / total) ** 2, 0.0) / (total + 1.0)
        observed_correct += sum(branch.probabilities.get(label, 0.0) for label in correct) * branch.support
        means.append({label: alpha[label] / total for label in labels})
        supports.append(branch.support)
    total_variation = (
        0.5 * sum(abs(means[0][label] - means[1][label]) for label in labels) if len(means) == 2 else None
    )
    return p_correct, p_wrong, variance, total_variation, min(supports), observed_correct


def select_discriminating_action(
    candidates: frozenset[str],
    actions: Sequence[EvidenceAction],
    profile: FunctionalInterventionProfile,
    budget: float,
    forecasts: Mapping[str, OutcomeForecast],
    consequences: Mapping[str, frozenset[str]],
    *,
    action_priorities: Mapping[str, float] | None = None,
    wrong_elimination_cost: float = REGISTERED_WRONG_ELIMINATION_COST,
) -> DiscriminationPlan:
    """Choose the one next measurement the registered rules are forecast to read most decisively.

    ``candidates`` are the hypotheses still compatible with the evidence; ``consequences`` maps each
    registered outcome label to what it would remove (see ``outcome_consequences``). The order is:

    1. the action is executable now, affordable, names a candidate, and has a usable forecast;
    2. its expected wrong-elimination risk is below the break-even of the declared utility
       (correct probability > ``wrong_elimination_cost`` x wrong probability, both Jeffreys-shrunk);
    3. the one-sided 95% lower bound of discrimination (correct minus wrong probability) is highest;
    4. then more support, lower cost, earlier exposure, larger predicted magnitude, smaller label.

    Nothing here reads a result or updates belief. An empty plan carries a named status.
    """

    if isinstance(budget, bool) or not isfinite(budget) or budget < 0:
        raise ValueError("Budget must be nonnegative.")
    if (isinstance(wrong_elimination_cost, bool) or not isinstance(wrong_elimination_cost, (int, float))
            or not isfinite(wrong_elimination_cost) or wrong_elimination_cost <= 0):
        raise ValueError("wrong_elimination_cost must be a positive finite number.")
    if len({action.identifier for action in actions}) != len(actions):
        raise ValueError("duplicate_action_identifier")
    priorities = dict(action_priorities or {})
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
           for value in priorities.values()):
        raise ValueError("invalid_action_priority")
    candidates = frozenset(candidates)
    assumptions = {"consequences_from_registered_rules", "uniform_prior_over_candidates", "one_measurement_per_round"}
    ordered = sorted(actions, key=lambda item: item.identifier)
    if len(candidates) < 2:
        empty = BudgetedEvidencePlan(
            (), frozenset(), frozenset(), 0.0, (),
            {action.identifier: "fewer_than_two_candidate_hypotheses" for action in ordered},
        )
        return DiscriminationPlan(empty, (), "nothing_to_discriminate", "fewer_than_two_candidate_hypotheses",
                                  tuple(sorted(assumptions)))

    evaluations: list[ActionDiscrimination] = []
    waiting: list[str] = []
    for action in ordered:
        base = dict(cost=float(action.cost), time_hours=action.time_hours,
                    priority=float(priorities.get(action.identifier, 0.0)))
        missing = profile.unmeasured(action.prerequisites)
        reason: str | None = None
        if action.cost < 0:
            reason = "invalid_action_cost"
        elif missing:
            waiting.append(f"{action.identifier}: {', '.join(missing)}")
            reason = f"waiting_for_prerequisite:{', '.join(missing)}"
        elif action.cost > budget + _TOLERANCE:
            reason = "exceeds_budget"
        elif not set(action.distinguishes) & candidates:
            reason = "declares_no_candidate_hypothesis"
        elif action.identifier not in forecasts:
            reason = "no_outcome_forecast"
        else:
            problem = _forecast_problem(forecasts[action.identifier], action.identifier, candidates)
            if problem is not None:
                reason = f"forecast_refused:{problem}"
        if reason is not None:
            evaluations.append(ActionDiscrimination(action.identifier, False, reason, **base))
            continue
        forecast = forecasts[action.identifier]
        assumptions.update(
            f"forecast_label_not_registered:{label}"
            for branch in forecast.branches for label in branch.probabilities if label not in consequences
        )
        p_correct, p_wrong, variance, total_variation, support, observed = _score(forecast, candidates, consequences)
        discrimination = p_correct - p_wrong
        lower = discrimination - LOWER_BOUND_Z * sqrt(variance)
        low_support = support <= LOW_SUPPORT_UNITS
        if low_support:
            assumptions.add(f"low_support:{action.identifier}")
        admissible = p_correct > wrong_elimination_cost * p_wrong + _TOLERANCE
        verdict = (
            "admissible" if admissible
            else "no_reference_reading_eliminates_correctly" if observed <= _TOLERANCE
            else "wrong_elimination_risk_not_below_break_even"
        )
        evaluations.append(ActionDiscrimination(
            action.identifier, admissible, verdict, p_correct=p_correct, p_wrong=p_wrong,
            discrimination=discrimination, discrimination_lower=lower, total_variation=total_variation,
            support=support, low_support=low_support, **base,
        ))

    def key(item: ActionDiscrimination) -> tuple:
        return (-(item.discrimination_lower or 0.0), -item.support, item.cost, item.time_hours or 0.0,
                -item.priority, item.action_identifier)

    admissible = sorted((item for item in evaluations if item.admissible), key=key)
    reasons = {item.action_identifier: item.reason for item in evaluations if not item.admissible}
    if not admissible:
        empty = BudgetedEvidencePlan((), frozenset(), candidates, 0.0, tuple(waiting), reasons)
        return DiscriminationPlan(
            empty, tuple(evaluations), "no_admissible_action",
            "no measurement is forecast to eliminate correctly below the wrong-risk break-even",
            tuple(sorted(assumptions)),
        )
    best = admissible[0]
    for item in admissible[1:]:
        reasons[item.action_identifier] = _lost_on(item, best)
    chosen = next(action for action in ordered if action.identifier == best.action_identifier)
    covered = frozenset(chosen.distinguishes) & candidates
    plan = BudgetedEvidencePlan((chosen,), covered, candidates - covered, float(chosen.cost), tuple(waiting), reasons)
    return DiscriminationPlan(plan, tuple(evaluations), "selected", None, tuple(sorted(assumptions)))


def _lost_on(item: ActionDiscrimination, best: ActionDiscrimination) -> str:
    """Name the first key on which an admissible action lost to the chosen one."""

    if (item.discrimination_lower or 0.0) != (best.discrimination_lower or 0.0):
        return "lower_conservative_discrimination"
    if item.support != best.support:
        return "less_support_at_equal_discrimination"
    if item.cost != best.cost:
        return "costlier_at_equal_discrimination"
    if (item.time_hours or 0.0) != (best.time_hours or 0.0):
        return "later_at_equal_discrimination"
    if item.priority != best.priority:
        return "smaller_predicted_response_at_equal_discrimination"
    return "identifier_tie_break"
