"""One research decision path, reusing the authoritative production CaseStore."""
from dataclasses import dataclass
from math import isfinite
from typing import Callable

from agent.memory import CaseState, CaseStore
from maestro.models import EvidenceAction, FunctionalInterventionProfile
from virtual_cell.interface import StatePrediction

from .interface import ExecutionBinding, ScientificQuery, StatePrediction as ResearchStatePrediction, raw_prediction_key


def prediction_refusal(value):
    if isinstance(value, (StatePrediction, ResearchStatePrediction)):
        if not value.contract_valid:
            return "invalid_prediction_contract"
        return None if value.applicable else value.abstain_reason
    if isinstance(value, dict):
        return "unsupported_prediction" if value.get("refusal") or value.get("valid") is False else None
    return "unsupported_prediction_type"


@dataclass(frozen=True)
class Candidate:
    action: EvidenceAction
    query: ScientificQuery | None = None
    binding: ExecutionBinding | None = None


@dataclass(frozen=True)
class DecisionResult:
    status: str
    plan_version: int
    actions: tuple[EvidenceAction, ...]
    rejected: dict[str, str]
    predictions: dict[str, object]
    prediction_use: str


class DecisionPath:
    """Injected scientific planner/selector; no third agent or implicit value score."""

    def __init__(self, store: CaseStore, planner: Callable, selector: Callable,
                 predictor: Callable, reviewer: Callable | None = None,
                 repair: Callable | None = None):
        self.store = store
        self.planner = planner
        self.selector = selector
        self.predictor = predictor
        self.reviewer = reviewer
        self.repair = repair
        self._raw_cache = {}  # raw predictions only; decisions are always recomputed

    @staticmethod
    def _reject(candidate, profile, remaining):
        action = candidate.action
        if isinstance(action.cost, bool) or not isinstance(action.cost, (int, float)) or not isfinite(action.cost) or action.cost < 0:
            return "invalid_action_cost"
        if remaining is not None and action.cost > remaining:
            return "unaffordable"
        missing = profile.unmeasured(action.prerequisites)
        return "missing_prerequisites:" + ",".join(missing) if missing else None

    def run(self, case_id, profile: FunctionalInterventionProfile, *, budget=None,
            prediction_use="diagnostic"):
        if prediction_use not in {"diagnostic", "selection"}:
            raise ValueError("prediction use must be explicit")
        case = self.store.open_case(case_id, budget=budget)
        if case.state is CaseState.AWAITING_RESULT:
            return DecisionResult("awaiting_result", case.plan_version, (), {}, {}, prediction_use)
        proposed = tuple(self.planner(case, profile))
        if len({c.action.identifier for c in proposed}) != len(proposed):
            raise ValueError("duplicate candidate identity")
        rejected, predictions = {}, {}

        def prepare(candidates):
            eligible = []
            for candidate in candidates:
                reason = self._reject(candidate, profile, case.remaining_budget)
                if reason:
                    rejected[candidate.action.identifier] = reason
                    continue
                action_id = candidate.action.identifier
                predictions.pop(action_id, None)  # A repaired query must not reuse a stale forecast.
                if candidate.query is None:
                    if candidate.action.requires_virtual_prediction:
                        rejected[action_id] = "required_prediction_missing"
                        continue
                    eligible.append(candidate)
                    continue  # legal evidence acquisition may not have model support
                if candidate.binding is None or candidate.query.action_id != candidate.action.identifier:
                    raise ValueError("prediction/action binding mismatch")
                action, query = candidate.action, candidate.query
                context = action.execution_context or profile.context_identifier
                if action.context_bound and context and query.context != context:
                    raise ValueError("prediction/context binding mismatch")
                endpoint = action.prediction_readout or action.readout
                if endpoint and query.endpoint != endpoint:
                    raise ValueError("prediction/endpoint binding mismatch")
                if action.time_hours is not None and query.time_hours != action.time_hours:
                    raise ValueError("prediction/time binding mismatch")
                key = raw_prediction_key(candidate.query, candidate.binding)
                if key not in self._raw_cache:
                    try:
                        value = self.predictor(candidate.query, candidate.binding)
                    except (RuntimeError, ValueError, OSError) as exc:
                        predictions[candidate.action.identifier] = {"refusal": str(exc)}
                        if action.requires_virtual_prediction:
                            rejected[action_id] = "required_prediction_refused"
                        else:
                            eligible.append(candidate)
                        continue
                    refusal = prediction_refusal(value)
                    if refusal:
                        predictions[candidate.action.identifier] = {"refusal": refusal}
                        if action.requires_virtual_prediction:
                            rejected[action_id] = "required_prediction_refused"
                        else:
                            eligible.append(candidate)
                        continue
                    self._raw_cache[key] = value
                predictions[candidate.action.identifier] = self._raw_cache[key]
                eligible.append(candidate)
            return tuple(eligible)

        eligible = prepare(proposed)
        selection_inputs = predictions if prediction_use == "selection" else {}
        selected = tuple(self.selector(eligible, selection_inputs)) if eligible else ()
        if any(c not in eligible for c in selected):
            raise ValueError("selector returned an unregistered candidate")
        if self.repair is not None and selected:
            selected = tuple(self.repair(selected, profile))
            if any(c.action not in tuple(p.action for p in proposed) for c in selected):
                raise ValueError("repair returned an unregistered action")
            registered = {c.action.identifier: c for c in proposed}
            for candidate in selected:
                original = registered[candidate.action.identifier].query
                query = candidate.query
                if query is not None:
                    scientific_fields = ("action_id", "intervention_sha256", "context", "population",
                                         "endpoint", "time_hours", "outcome_mode")
                    if original is None or any(getattr(query, field) != getattr(original, field)
                                               for field in scientific_fields):
                        raise ValueError("repair changed the registered scientific contract")
            if any(self._reject(c, profile, case.remaining_budget) for c in selected):
                raise ValueError("repaired plan is not executable")
            selected = prepare(selected)  # unchanged raw queries hit the cache
        if len({c.action.identifier for c in selected}) != len(selected):
            raise ValueError("duplicate selected action")
        if any(self._reject(c, profile, case.remaining_budget) for c in selected):
            raise ValueError("final plan violates executable constraints")
        actions = tuple(c.action for c in selected)
        if case.remaining_budget is not None and sum(a.cost for a in actions) > case.remaining_budget:
            raise ValueError("final bundle exceeds budget")
        if self.reviewer is not None:
            self.reviewer(actions, predictions)  # final, advisory-only; no hidden reselection
        snapshot = self.store.record_plan(case_id, actions, ready_to_measure=bool(actions),
                                          context_identifier=profile.context_identifier,
                                          stop_reason=None if actions else "no_executable_candidate")
        return DecisionResult("submitted" if actions else "stopped", snapshot.plan_version,
                              actions, rejected, predictions, prediction_use)
