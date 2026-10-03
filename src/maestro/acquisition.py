"""Measurement choice from declared detection power, or from predicted readings under each hypothesis."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite, sqrt
from typing import TYPE_CHECKING, Iterable, Mapping, Protocol, Sequence

if TYPE_CHECKING:
    from .hypothesis_forecast import UserStateContext

from .handoff import RejectedCandidate
from .models import EvidenceAction, EvidenceKind, EvidenceScope, FunctionalInterventionProfile, MechanismContrast
from .outcome import EvidenceState, OutcomeRule
from .composition import BudgetedEvidencePlan, finite_number, select_budgeted_subset, validate_action_menu, validate_priorities

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

    validate_action_menu(actions, budget)
    for action in actions:
        if action.detection_power is not None and (isinstance(action.detection_power, bool)
                or not isinstance(action.detection_power, (int, float))
                or not isfinite(action.detection_power) or not 0 <= action.detection_power <= 1):
            raise ValueError("invalid_detection_power")
    if source_groups is not None and (any(not isinstance(k, str) or not k.strip()
            or not isinstance(v, str) or not v.strip() for k, v in source_groups.items())
            or {ref for action in actions for ref in action.source_ids} - source_groups.keys()):
        raise ValueError("incomplete_source_groups")
    if not finite_number(coverage_threshold) or not 0.0 <= coverage_threshold <= 1.0:
        raise ValueError("A coverage threshold must lie in [0, 1].")
    weights = dict(weights or {})
    if set(weights) - required or any(
        not finite_number(value) or value < 0 for value in weights.values()
    ):
        raise ValueError("Weights must be finite nonnegative values for required hypotheses.")
    priorities = dict(action_priorities or {})
    validate_priorities(priorities)
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

    def objective(candidate):
        probabilities = _coverage_probabilities(candidate, required, groups)
        return sum(weights.get(name, 1.0) * probabilities[name] for name in sorted(required))

    best = select_budgeted_subset(executable, budget, objective, priorities)
    best_probabilities = _coverage_probabilities(best, required, groups)
    best_expected = objective(best)
    best_cost = sum(action.cost for action in best)

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
    compounds, not simulation draws) the forecast rests on. Empirical branches receive the
    planner's Jeffreys prior. An already regularised Dirichlet prediction instead supplies
    ``posterior_concentration``: its total posterior mass, including prior mass. The planner
    preserves that prediction's mean and uses the concentration only for uncertainty. The
    concentration is not an independent measured-unit count. A concentration based on Kish
    effective support is a weighted-frequency approximation, not an exact conjugate posterior.
    """

    hypothesis: str
    probabilities: Mapping[str, float]
    support: int
    posterior_concentration: float | None = None

    def __post_init__(self) -> None:
        concentration = self.posterior_concentration
        if concentration is not None and (
            isinstance(concentration, bool) or not isinstance(concentration, (int, float))
            or not isfinite(concentration) or concentration <= 0
        ):
            raise ValueError("invalid_posterior_concentration")


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
    outcome_mode: str = "attempted_experiment"
    """valid_readout is conditional on successful measurement, not a complete planning forecast."""

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
        user_state: UserStateContext | None = None,
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


# ---------------------------------------------------------------------------------------------
# Decision-sensitive value of information
@dataclass(frozen=True)
class DecisionValue:
    """Expected terminal-decision value of one legal action.

    The forecast only supplies a distribution for the *reading*. The terminal
    decision is recomputed from the surviving hypotheses for every reading, so
    predictive uncertainty that cannot change a decision receives zero value.
    """

    action_identifier: str
    expected_value: float
    expected_loss_before: float
    expected_loss_after: float
    decision_sensitivity: float
    expected_wrong_decision: float
    cost: float
    admissible: bool = True
    reason: str = "admissible"

    @property
    def net_value(self) -> float:
        return self.expected_value - self.cost

    def payload(self) -> dict[str, object]:
        return {
            "action_identifier": self.action_identifier,
            "expected_value": self.expected_value,
            "net_value": self.net_value,
            "expected_loss_before": self.expected_loss_before,
            "expected_loss_after": self.expected_loss_after,
            "decision_sensitivity": self.decision_sensitivity,
            "expected_wrong_decision": self.expected_wrong_decision,
            "cost": self.cost,
            "admissible": self.admissible,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DecisionValuePlan:
    """The decision-sensitive choice and the audit record for every candidate."""

    chosen: DecisionValue | None
    evaluations: tuple[DecisionValue, ...]
    status: str
    reason: str | None = None

    def payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "chosen": self.chosen.action_identifier if self.chosen else None,
            "evaluations": {item.action_identifier: item.payload() for item in self.evaluations},
        }


def _posterior_decision(
    posterior: Mapping[str, float],
    candidates: Sequence[str],
    *,
    wrong_decision_loss: float,
    defer_loss: float,
) -> tuple[str, float, float]:
    """Return the Bayes action, its risk and its wrong-decision probability."""

    ordered = tuple(sorted(candidates))
    options = [("defer", float(defer_loss), 0.0)]
    options.extend(
        (candidate, float(wrong_decision_loss) * (1.0 - float(posterior.get(candidate, 0.0))),
         1.0 - float(posterior.get(candidate, 0.0)))
        for candidate in ordered
    )
    # Keep deferral as the deterministic tie-break. It is safer at a boundary
    # and makes sensitivity independent of dictionary insertion order.
    return min(options, key=lambda item: (item[1], 0 if item[0] == "defer" else 1, item[0]))


def expected_terminal_decision_value(
    candidates: frozenset[str] | Sequence[str],
    forecast: OutcomeForecast,
    consequences: Mapping[str, frozenset[str]],
    *,
    prior: Mapping[str, float] | None = None,
    wrong_decision_loss: float = REGISTERED_WRONG_ELIMINATION_COST,
    defer_loss: float = 1.0,
    measurement_cost: float = 0.0,
) -> DecisionValue:
    """Compute myopic expected value from terminal decision loss.

    ``consequences`` is the registered observation-to-elimination map. A
    forecast that changes magnitude while leaving the surviving decision the
    same therefore has zero decision sensitivity and zero expected value.

    The decision here is a Bayes action under ``wrong_decision_loss`` and
    ``defer_loss``; an informative reading may change that action even when no
    hypothesis is eliminated. This value does not authorize an evidence update
    or a validator terminal decision, and is not the registered replay utility.
    """

    if forecast.outcome_mode != "attempted_experiment":
        raise ValueError("experiment_validity_probability_required")
    ordered = tuple(sorted(set(candidates)))
    if len(ordered) < 2:
        raise ValueError("at least two candidate hypotheses are required")
    problem = _forecast_problem(forecast, forecast.action_identifier, frozenset(ordered))
    if problem:
        raise ValueError(problem)
    if (not finite_number(wrong_decision_loss) or not finite_number(defer_loss)
            or not finite_number(measurement_cost)
            or wrong_decision_loss <= 0 or defer_loss < 0 or measurement_cost < 0):
        raise ValueError("decision losses and measurement cost must be nonnegative")
    weights = {name: 1.0 / len(ordered) for name in ordered}
    if prior is not None:
        if set(prior) - set(ordered) or any(not finite_number(v) or v < 0 for v in prior.values()):
            raise ValueError("prior must contain finite nonnegative candidate masses")
        raw = {name: float(prior.get(name, 0.0)) for name in ordered}
        total = sum(raw.values())
        if total <= 0:
            raise ValueError("prior must assign positive mass to a candidate")
        weights = {name: value / total for name, value in raw.items()}
    before_decision, before_loss, _ = _posterior_decision(
        weights, ordered, wrong_decision_loss=wrong_decision_loss, defer_loss=defer_loss
    )
    labels = sorted({label for branch in forecast.branches for label in branch.probabilities} | set(consequences))
    if not labels:
        raise ValueError("forecast has no outcome labels")
    if forecast.refusal:
        raise ValueError(f"forecast_refused:{forecast.refusal}")
    likelihood = {}
    for hypothesis in ordered:
        branch = forecast.branch_for(hypothesis)
        if branch is None:
            raise ValueError(f"forecast_missing_hypothesis:{hypothesis}")
        values = {label: float(branch.probabilities.get(label, 0.0)) for label in labels}
        if any(not isfinite(value) or value < 0 for value in values.values()):
            raise ValueError(f"invalid_probability:{hypothesis}")
        total = sum(values.values())
        if total <= 0:
            raise ValueError(f"empty_probability:{hypothesis}")
        likelihood[hypothesis] = values
    masses = {label: sum(weights[h] * likelihood[h][label] for h in ordered) for label in labels}
    after_loss = 0.0
    wrong_probability = 0.0
    sensitivity = 0.0
    for label, mass in masses.items():
        if mass <= 0:
            continue
        removed = set(consequences.get(label, frozenset())) & set(ordered)
        # Bayes' rule over every candidate. The registered rule then restricts which decisions
        # are available, but the removed hypotheses keep their posterior mass. That mass is the
        # probability that the rule removed the truth. Zeroing it before scoring (the first
        # version) counted the reading twice and reported a wrong-decision probability of zero
        # for every single-survivor reading.
        posterior = {h: weights[h] * likelihood[h][label] / mass for h in ordered}
        decision, loss, wrong = _posterior_decision(
            posterior, tuple(h for h in ordered if h not in removed),
            wrong_decision_loss=wrong_decision_loss, defer_loss=defer_loss,
        )
        after_loss += mass * loss
        wrong_probability += mass * wrong if decision != "defer" else 0.0
        sensitivity += mass * (decision != before_decision)
    expected_value = float(before_loss - after_loss)
    return DecisionValue(
        action_identifier=forecast.action_identifier,
        expected_value=expected_value,
        expected_loss_before=float(before_loss),
        expected_loss_after=float(after_loss),
        decision_sensitivity=float(sensitivity),
        expected_wrong_decision=float(wrong_probability),
        cost=float(measurement_cost),
        admissible=expected_value > measurement_cost + _TOLERANCE,
        reason="admissible" if expected_value > measurement_cost + _TOLERANCE else "non_positive_net_value",
    )


def decision_sensitivity(
    candidates: frozenset[str] | Sequence[str],
    forecast: OutcomeForecast,
    consequences: Mapping[str, frozenset[str]],
    **kwargs,
) -> float:
    """Return the probability that observing an action changes the terminal decision."""

    return expected_terminal_decision_value(candidates, forecast, consequences, **kwargs).decision_sensitivity


def select_decision_sensitive_action(
    candidates: frozenset[str],
    actions: Sequence[EvidenceAction],
    profile: FunctionalInterventionProfile,
    budget: float,
    forecasts: Mapping[str, OutcomeForecast],
    consequences: Mapping[str, frozenset[str]],
    *,
    prior: Mapping[str, float] | None = None,
    wrong_decision_loss: float = REGISTERED_WRONG_ELIMINATION_COST,
    defer_loss: float = 1.0,
    measurement_costs: Mapping[str, float] | None = None,
) -> DecisionValuePlan:
    """Select the legal action with the highest positive expected terminal value.

    ``EvidenceAction.cost`` remains the hard budget cost (for example assay-days).
    ``measurement_costs`` optionally supplies a separate utility-scale price for
    the value calculation, which keeps experimental cost units from being mixed
    with the terminal-loss units.
    """

    validate_action_menu(actions, budget)
    utility_costs = dict(measurement_costs or {})
    if any(not finite_number(value) or value < 0
           for value in utility_costs.values()):
        raise ValueError("measurement costs must be finite and nonnegative")
    evaluations: list[DecisionValue] = []
    for action in sorted(actions, key=lambda item: item.identifier):
        reason = None
        if action.cost < 0:
            reason = "invalid_action_cost"
        elif action.cost > budget + _TOLERANCE:
            reason = "exceeds_budget"
        elif profile.unmeasured(action.prerequisites):
            reason = "waiting_for_prerequisite:" + ",".join(profile.unmeasured(action.prerequisites))
        elif action.identifier not in forecasts:
            reason = "no_outcome_forecast"
        if reason is not None:
            evaluations.append(DecisionValue(action.identifier, 0.0, 0.0, 0.0, 0.0, 0.0,
                                             float(utility_costs.get(action.identifier, action.cost)), False, reason))
            continue
        try:
            problem = _forecast_problem(forecasts[action.identifier], action.identifier, candidates)
            if problem:
                raise ValueError(problem)
            item = expected_terminal_decision_value(
                candidates, forecasts[action.identifier], consequences, prior=prior,
                wrong_decision_loss=wrong_decision_loss, defer_loss=defer_loss,
                measurement_cost=float(utility_costs.get(action.identifier, action.cost)),
            )
        except (TypeError, ValueError) as error:
            item = DecisionValue(action.identifier, 0.0, 0.0, 0.0, 0.0, 0.0,
                                 float(utility_costs.get(action.identifier, action.cost)), False,
                                 f"invalid_forecast:{error}")
        evaluations.append(item)
    admissible = [item for item in evaluations if item.admissible]
    if not admissible:
        return DecisionValuePlan(None, tuple(evaluations), "no_admissible_action", "no action can improve the terminal decision after cost")
    chosen = max(admissible, key=lambda item: (item.net_value, item.decision_sensitivity, -item.cost, item.action_identifier))
    return DecisionValuePlan(chosen, tuple(evaluations), "selected")


# Short names used by research code and reports.
myopic_expected_decision_value = expected_terminal_decision_value
select_myopic_edv = select_decision_sensitive_action
expected_decision_value = expected_terminal_decision_value
select_expected_decision_action = select_decision_sensitive_action


def _forecast_problem(forecast: OutcomeForecast, identifier: str, candidates: frozenset[str]) -> str | None:
    if forecast.outcome_mode != "attempted_experiment":
        return "experiment_validity_probability_required"
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

    Empirical branches receive a Jeffreys prior over the registered and forecast labels.
    Branches declaring posterior concentration already include their prior: no extra probability
    mass is added, including for labels present only in the registered rules. A correct reading
    removes a candidate other than the branch's
    hypothesis and not that hypothesis; a wrong reading removes it. The pooled values average the
    branches (a uniform prior over the candidates), and the variance of the pooled discrimination
    is the weighted sum of the independent branch variances. Shared training artifacts can
    correlate branches; this approximation does not model that covariance, fitted-parameter
    uncertainty or domain shift. Its normal lower bound is not a calibrated coverage guarantee.
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
        if branch.posterior_concentration is None:
            alpha = {label: branch.probabilities.get(label, 0.0) * branch.support
                     + JEFFREYS_PSEUDOCOUNT for label in labels}
        else:
            alpha = {label: branch.probabilities.get(label, 0.0)
                     * branch.posterior_concentration for label in labels}
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
       (correct probability > ``wrong_elimination_cost`` x wrong probability, with each branch
       regularised once by either its forecaster or the legacy Jeffreys prior);
    3. the one-sided 95% lower bound of discrimination (correct minus wrong probability) is highest;
    4. then more support, lower cost, earlier exposure, larger predicted magnitude, smaller label.

    Nothing here reads a result or updates belief. An empty plan carries a named status.
    """

    validate_action_menu(actions, budget)
    if (isinstance(wrong_elimination_cost, bool) or not isinstance(wrong_elimination_cost, (int, float))
            or not isfinite(wrong_elimination_cost) or wrong_elimination_cost <= 0):
        raise ValueError("wrong_elimination_cost must be a positive finite number.")
    priorities = dict(action_priorities or {})
    validate_priorities(priorities)
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
