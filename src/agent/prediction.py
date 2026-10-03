"""Bound queries, safe model calls, cache reuse and prediction records only."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from typing import Mapping, Sequence

from maestro.models import EvidenceAction, MechanismContrast
from virtual_cell import PredictionRequest, StatePrediction
from virtual_cell.interface import PredictionCache, QueryAssessment, VirtualCellQueryTemplate, VirtualCellWorldModel, safe_predict
from .case_store import CaseSnapshot
from .context import TaskIntent
from .memory import RunLogger


@dataclass(frozen=True)
class WorldModelQueries:
    """One round's virtual-cell answers: per registered action, and the plan-level view.

    ``request``/``assessment``/``prediction`` are what the controller reads when no
    per-action map exists (an explicit request, or a template without per-action
    labels); with a per-action map they are the plan action's own entries.
    """

    requests: dict[str, PredictionRequest] = field(default_factory=dict)
    assessments: dict[str, QueryAssessment] = field(default_factory=dict)
    predictions: dict[str, StatePrediction] = field(default_factory=dict)
    request: PredictionRequest | None = None
    assessment: QueryAssessment | None = None
    prediction: StatePrediction | None = None


class PredictionCoordinator:
    """No action selection, measurement interpretation or mechanism mutation."""

    def __init__(self, backend: VirtualCellWorldModel | None, logger: RunLogger, *,
                 cache: PredictionCache | None = None, max_parallel_predictions: int = 1):
        if type(max_parallel_predictions) is not int or max_parallel_predictions < 1:
            raise ValueError("max_parallel_predictions must be a positive integer.")
        self.backend = backend
        self._logger = logger
        self.cache = cache
        self.max_parallel_predictions = max_parallel_predictions

    def query(
        self,
        contrast: MechanismContrast,
        intent: TaskIntent,
        case: CaseSnapshot | None,
        case_id: str,
        session_id: str,
        available_actions: Sequence[EvidenceAction],
        *,
        prediction_request: PredictionRequest | None,
        template: VirtualCellQueryTemplate | None,
    ) -> WorldModelQueries:
        """Ask the virtual cell about this round's actions, once per distinct query.

        A template with per-action labels yields one request per registered
        action, so each action is ranked by its own condition. Otherwise the
        single explicit or template request belongs only to the plan action
        that prompted it, never to a neighbour.
        """

        not_built = {}
        action_requests = self._build_action_prediction_requests(
            template, intent, contrast, case_id, case, session_id, available_actions, rejections=not_built
        )
        if not_built:
            self._logger.event("virtual_cell_query_not_built", {"reasons": not_built}, session_id=session_id)
        if template is not None and template.action_interventions:
            answered = self.predict_many(action_requests, session_id)
            assessments = {key: pair[0] for key, pair in answered.items() if pair[0] is not None}
            predictions = {key: pair[1] for key, pair in answered.items() if pair[1] is not None}
            plan = contrast.plan.identifier if contrast.plan is not None else None
            return WorldModelQueries(
                action_requests, assessments, predictions, None,
                assessments.get(plan) if plan else None, predictions.get(plan) if plan else None,
            )
        if contrast.plan is None or contrast.plan.identifier not in {a.identifier for a in available_actions}:
            return WorldModelQueries()
        request = prediction_request or self._build_prediction_request(
            template, intent, contrast, case_id, case, session_id
        )
        if request is not None:
            try:
                bound = request.intervention.for_action(contrast.plan, request.context, request.readouts)
                if bound != request.intervention:
                    raise ValueError("explicit_query_action_conditions_mismatch")
            except ValueError as error:
                self._logger.event("virtual_cell_query_not_built",
                                   {"reasons": {contrast.plan.identifier: str(error)}}, session_id=session_id)
                return WorldModelQueries()
        assessment, prediction = self.predict(request, session_id)
        requests: dict[str, PredictionRequest] = {}
        assessments: dict[str, QueryAssessment] = {}
        predictions: dict[str, StatePrediction] = {}
        if request is not None and contrast.plan is not None:
            requests[contrast.plan.identifier] = request
            if assessment is not None:
                assessments[contrast.plan.identifier] = assessment
            if prediction is not None:
                predictions[contrast.plan.identifier] = prediction
        return WorldModelQueries(requests, assessments, predictions, request, assessment, prediction)

    def predict_many(
        self, requests: Mapping[str, PredictionRequest], session_id: str
    ) -> dict[str, tuple[QueryAssessment | None, StatePrediction | None]]:
        """Answer independent requests, dispatching distinct misses concurrently when allowed.

        Inference runs at most once per distinct query in a round, including when
        reuse across rounds is disabled. A duplicate is rebound to its lineage. Recording
        and logging happen in request order on the calling thread, so the run
        record is identical whether or not inference ran in parallel.
        """

        answered: dict[str, tuple[QueryAssessment | None, StatePrediction | None]] = {}
        pending: dict[str, PredictionRequest] = {}
        for identifier, request in requests.items():
            hit = self._reused_prediction(request, session_id)
            if hit is not None:
                answered[identifier] = hit
            else:
                pending[identifier] = request
        distinct: dict[str, str] = {}
        origins: dict[str, str] = {}
        for identifier, request in pending.items():
            key = PredictionCache.key_for(request, self.backend_name()) or f"uncacheable:{identifier}"
            origins[identifier] = distinct.setdefault(key, identifier)
        computed: dict[str, tuple[QueryAssessment | None, StatePrediction | None]] = {}
        if self.backend is not None and self.max_parallel_predictions > 1 and len(distinct) > 1:
            workers = min(self.max_parallel_predictions, len(distinct))
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="virtual-cell") as pool:
                futures = {
                    identifier: pool.submit(safe_predict, self.backend, pending[identifier])
                    for identifier in distinct.values()
                }
            computed = {identifier: future.result() for identifier, future in futures.items()}
        for identifier, request in pending.items():
            origin = origins[identifier]
            if origin != identifier:
                reused = self._reused_prediction(request, session_id)
                if reused is not None:
                    answered[identifier] = reused
                    continue
                assessment, prediction = computed[origin]
                if prediction is not None:
                    prediction = replace(
                        prediction, request_id=request.request_id, compute_cost=0.0,
                        limitations=tuple(prediction.limitations) + (
                            f"reused_prediction_from_request:{pending[origin].request_id}; identical query in this round.",
                        ),
                    )
                    self._record_prediction(request, assessment, prediction, session_id)
                answered[identifier] = (assessment, prediction)
            elif identifier in computed:
                assessment, prediction = computed[identifier]
                self._record_prediction(request, assessment, prediction, session_id)
                answered[identifier] = (assessment, prediction)
            else:
                answered[identifier] = self.predict(request, session_id)
                computed[identifier] = answered[identifier]
        return {identifier: answered[identifier] for identifier in requests}

    def backend_name(self) -> str:
        return getattr(self.backend, "name", None) or type(self.backend).__name__

    def predict(
        self, request: PredictionRequest | None, session_id: str
    ) -> tuple[QueryAssessment | None, StatePrediction | None]:
        if request is None or self.backend is None:
            return None, None
        reused = self._reused_prediction(request, session_id)
        if reused is not None:
            return reused
        assessment, prediction = safe_predict(self.backend, request)
        self._record_prediction(request, assessment, prediction, session_id)
        return assessment, prediction

    def _reused_prediction(
        self, request: PredictionRequest, session_id: str
    ) -> tuple[QueryAssessment, StatePrediction] | None:
        """An earlier answer to the identical query, rebound to this request and logged."""

        if self.cache is None or self.backend is None:
            return None
        backend = self.backend_name()
        cached = self.cache.lookup(request, backend)
        if cached is None:
            return None
        assessment, prediction, origin = cached
        self._logger.experiment(
            "virtual_cell_prediction_reused",
            {
                "request_id": request.request_id,
                "reused_from_request_id": origin,
                "backend": backend,
                "artifact_ref": prediction.artifact_ref,
                "cache": self.cache.stats(),
            },
            session_id=session_id,
        )
        return assessment, prediction

    def _record_prediction(
        self,
        request: PredictionRequest,
        assessment: QueryAssessment,
        prediction: StatePrediction,
        session_id: str,
    ) -> None:
        """Keep a fresh answer for reuse and write its assessment and outcome to the run log."""

        if self.cache is not None:
            self.cache.store(request, self.backend_name(), assessment, prediction)
        self._logger.event(
            "virtual_cell_query_assessed",
            {
                "request_id": request.request_id,
                "support": assessment.support.value,
                "missing_inputs": assessment.missing_inputs,
                "limitations": assessment.limitations,
                "model_identifier": assessment.capabilities.model_identifier,
                "model_version": assessment.capabilities.model_version,
            },
            session_id=session_id,
        )
        self._logger.experiment(
            "virtual_cell_prediction_completed",
            {
                "request_id": request.request_id,
                "applicable": prediction.applicable,
                "artifact_ref": prediction.artifact_ref,
                "limitations": prediction.limitations,
                "supported_variables": prediction.supported_variables,
                "abstain_reason": prediction.abstain_reason,
                "in_distribution": prediction.in_distribution,
            },
            session_id=session_id,
        )

    @staticmethod
    def _build_action_prediction_requests(
        template: VirtualCellQueryTemplate | None,
        intent: TaskIntent,
        contrast: MechanismContrast,
        case_id: str,
        case: CaseSnapshot | None,
        session_id: str,
        available_actions: Sequence[EvidenceAction],
        *, rejections: dict[str, str] | None = None,
    ) -> dict[str, PredictionRequest]:
        """One request per registered action that names its own exact condition.

        The action's declared exposure and dose replace the shared template's.
        Contradictory or unexpressible conditions refuse a query, never fall back
        to a shared condition. Other-context actions cannot borrow this template.
        """

        if template is None or not template.action_interventions:
            return {}
        registered = {action.identifier: action for action in available_actions}
        requests: dict[str, PredictionRequest] = {}
        for action_identifier, label in template.action_interventions.items():
            action = registered.get(action_identifier)
            if action is None:
                continue
            if action.execution_context is not None and action.execution_context != template.context.identifier:
                if rejections is not None:
                    rejections[action_identifier] = f"execution_context_differs_from_template:{action.execution_context}"
                continue
            time_hours = (
                action.time_hours
                if template.time_hours is not None and action.time_hours is not None
                else template.time_hours
            )
            request = template.build(
                request_id=f"{session_id}.{action_identifier}",
                case_id=case_id,
                contrast_id=contrast.identifier,
                plan_version=(case.plan_version + 1) if case else 1,
                intended_targets=intent.target_or_targets,
                intervention_identifier=label,
                time_hours=time_hours,
            )
            try:
                intervention = request.intervention.for_action(action, request.context, request.readouts)
            except ValueError as error:
                if rejections is not None:
                    rejections[action_identifier] = str(error)
                continue
            requests[action_identifier] = replace(request, intervention=intervention)
        return requests

    @staticmethod
    def _build_prediction_request(
        template: VirtualCellQueryTemplate | None,
        intent: TaskIntent,
        contrast: MechanismContrast,
        case_id: str,
        case: CaseSnapshot | None,
        session_id: str,
    ) -> PredictionRequest | None:
        if template is None:
            return None
        return template.build(
            request_id=f"{session_id}.state",
            case_id=case_id,
            contrast_id=contrast.identifier,
            plan_version=(case.plan_version + 1) if case else 1,
            intended_targets=intent.target_or_targets,
        )
