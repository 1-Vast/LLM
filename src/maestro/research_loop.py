"""Small, replayable auto-research loop.

The loop deliberately stays below the planner/orchestrator boundary: it selects one
discriminating experiment, records the observation, and can be replayed from its
immutable receipt.  Forecasts are advisory; a refused forecast never spends budget.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class HypothesisPair:
    first: str
    second: str

    def __post_init__(self) -> None:
        if not self.first or not self.second or self.first == self.second:
            raise ValueError("hypothesis_pair_requires_two_distinct_ids")

    @property
    def ids(self) -> tuple[str, str]:
        return self.first, self.second


@dataclass(frozen=True)
class ActionCandidate:
    identifier: str
    cost: float
    expected_information: float
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.identifier or self.cost <= 0 or self.expected_information < 0:
            raise ValueError("invalid_action_candidate")

    @property
    def value_per_cost(self) -> float:
        return self.expected_information / self.cost


@dataclass(frozen=True)
class Forecast:
    action_id: str
    probabilities: Mapping[str, float]
    information_gain: float | None = None
    refusal: str | None = None
    basis: str = ""
    support: int | None = None
    scope: str = ""

    def __post_init__(self) -> None:
        if not self.action_id:
            raise ValueError("forecast_requires_action_id")
        if any(float(p) < 0 for p in self.probabilities.values()):
            raise ValueError("forecast_probabilities_must_be_nonnegative")
        if self.refusal is None and not self.probabilities:
            raise ValueError("forecast_requires_outcomes_or_refusal")
        if self.information_gain is not None and self.information_gain < 0:
            raise ValueError("forecast_information_gain_must_be_nonnegative")
        if self.support is not None and self.support < 0:
            raise ValueError("forecast_support_must_be_nonnegative")

    @property
    def entropy(self) -> float:
        import math
        total = sum(float(v) for v in self.probabilities.values())
        if total <= 0:
            return 0.0
        return -sum((p := float(v) / total) * math.log(p) for v in self.probabilities.values() if v)


class Executor(Protocol):
    def execute(self, action: ActionCandidate) -> "Observation": ...


@dataclass(frozen=True)
class Observation:
    """An execution result; failures stay in the history and never become evidence."""

    action_id: str
    outcome: str
    success: bool = True
    detail: Mapping[str, Any] = field(default_factory=dict)
    source_id: str = ""
    context_identifier: str = ""
    independent_units: int | None = None
    quality_passed: bool = True
    evidence_kind: str = "real_measurement"

    def __post_init__(self) -> None:
        if not self.action_id or not self.outcome:
            raise ValueError("observation_requires_identity_and_outcome")
        if self.independent_units is not None and self.independent_units < 0:
            raise ValueError("independent_units_must_be_nonnegative")
        if self.evidence_kind not in {"real_measurement", "execution_failure", "qc_failure"}:
            raise ValueError("unsupported_observation_kind")

    @property
    def admissible(self) -> bool:
        """Only qualified, sourced, independent measurements update hypothesis support."""
        return (self.success and self.quality_passed and self.evidence_kind == "real_measurement"
                and bool(self.source_id) and bool(self.context_identifier)
                and self.independent_units is not None and self.independent_units > 0)


@dataclass(frozen=True)
class ResearchState:
    hypotheses: HypothesisPair
    remaining_budget: float
    observations: tuple[Observation, ...] = ()
    selected_actions: tuple[str, ...] = ()
    stop_reason: str | None = None

    @property
    def finished(self) -> bool:
        return self.stop_reason is not None


class ResearchLoop:
    """Budgeted experiment loop with explicit abstention and deterministic replay."""

    def __init__(self, hypotheses: HypothesisPair, actions: Sequence[ActionCandidate],
                 forecasts: Mapping[str, Forecast], executor: Executor, *, budget: float,
                 confidence_threshold: float = 0.95):
        if budget < 0:
            raise ValueError("budget_must_be_nonnegative")
        if not 0 < confidence_threshold <= 1:
            raise ValueError("invalid_confidence_threshold")
        self.hypotheses = hypotheses
        self.actions = {a.identifier: a for a in actions}
        self.forecasts = dict(forecasts)
        self.executor = executor
        self.confidence_threshold = confidence_threshold
        self.state = ResearchState(hypotheses, float(budget))

    def _posterior(self) -> dict[str, float]:
        counts = {h: 1.0 for h in self.hypotheses.ids}
        for obs in self.state.observations:
            if obs.outcome in counts and obs.admissible:
                counts[obs.outcome] += 1.0
        total = sum(counts.values())
        return {h: counts[h] / total for h in counts}

    def _choose(self) -> tuple[ActionCandidate, Forecast] | None:
        available = []
        for identifier, action in self.actions.items():
            if identifier in self.state.selected_actions or action.cost > self.state.remaining_budget:
                continue
            forecast = self.forecasts.get(identifier)
            if forecast is None or forecast.refusal is not None:
                continue
            gain = action.expected_information if forecast.information_gain is None else forecast.information_gain
            available.append((gain / action.cost, identifier, action, forecast))
        if not available:
            return None
        _, _, action, forecast = max(available, key=lambda row: (row[0], row[1]))
        return action, forecast

    def step(self) -> ResearchState:
        if self.state.finished:
            return self.state
        posterior = self._posterior()
        if max(posterior.values()) >= self.confidence_threshold and self.state.observations:
            self.state = ResearchState(self.hypotheses, self.state.remaining_budget,
                                       self.state.observations, self.state.selected_actions,
                                       "confidence_reached")
            return self.state
        if self.state.remaining_budget <= 0:
            self.state = ResearchState(self.hypotheses, 0.0, self.state.observations,
                                       self.state.selected_actions, "budget_exhausted")
            return self.state
        choice = self._choose()
        if choice is None:
            reason = "no_admissible_action" if self.state.remaining_budget else "budget_exhausted"
            self.state = ResearchState(self.hypotheses, self.state.remaining_budget,
                                       self.state.observations, self.state.selected_actions, reason)
            return self.state
        action, _ = choice
        observation = self.executor.execute(action)
        if observation.action_id != action.identifier:
            raise ValueError("executor_returned_wrong_action")
        # Evidence is retained even when it cannot update either hypothesis.  This
        # makes malformed/novel readouts visible in the replay receipt instead of
        # silently steering the posterior.
        if observation.outcome not in self.hypotheses.ids:
            retained = Observation(observation.action_id, observation.outcome, False,
                                   {**dict(observation.detail), "validation": "unknown_outcome"})
            self.state = ResearchState(self.hypotheses, self.state.remaining_budget - action.cost,
                                       self.state.observations + (retained,),
                                       self.state.selected_actions + (action.identifier,),
                                       "invalid_observation")
            return self.state
        self.state = ResearchState(self.hypotheses, self.state.remaining_budget - action.cost,
                                   self.state.observations + (observation,),
                                   self.state.selected_actions + (action.identifier,))
        return self.state

    def run(self, max_steps: int | None = None) -> ResearchState:
        limit = max_steps if max_steps is not None else len(self.actions) + 1
        for _ in range(max(0, limit)):
            before = self.state
            self.step()
            if self.state.finished or self.state == before:
                break
        if not self.state.finished and max_steps is not None and len(self.state.selected_actions) >= max_steps:
            self.state = ResearchState(self.hypotheses, self.state.remaining_budget,
                                       self.state.observations, self.state.selected_actions,
                                       "step_limit_reached")
        return self.state

    def receipt(self) -> Mapping[str, Any]:
        return {"hypotheses": self.hypotheses.ids,
                "state": {"remaining_budget": self.state.remaining_budget,
                           "observations": [o.__dict__ for o in self.state.observations],
                           "selected_actions": self.state.selected_actions,
                           "stop_reason": self.state.stop_reason},
                "digest": self.digest()}

    def digest(self) -> str:
        payload = {"hypotheses": self.hypotheses.ids, "budget": self.state.remaining_budget,
                   "observations": [o.__dict__ for o in self.state.observations],
                   "selected": self.state.selected_actions, "stop": self.state.stop_reason}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
