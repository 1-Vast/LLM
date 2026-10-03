"""Bounded case orchestration, evidence acquisition, and deterministic decision checks."""
from __future__ import annotations

import uuid
import math
import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Callable, Mapping, Sequence
if TYPE_CHECKING:
    from maestro.hypothesis_forecast import UserStateContext
from maestro.contrast import MAESTROAgent
from maestro.acquisition import DiscriminationPlan, OutcomeForecaster, outcome_consequences, select_discriminating_action, select_expected_coverage
from maestro.decision import DecisionEngine, DevelopmentDecision
from maestro.handoff import ComparabilityStatus, DecisionLayer, EvidenceLayer, ExecutionLayer, RoundRecord, WorldModelLayer, rejected_from_selection, review_run
from maestro.outcome import EvidenceState, InterpretationTable, MeasuredPremise, OutcomeRule, ValidatedEvidenceUpdate, admit_evidence, default_rules_for, scope_rank
from maestro.handoff import SourceClusterIndex
from maestro.composition import ActionTopology
from maestro.judgment import PredictionReliabilityLedger, ScoredPrediction
from maestro.repair import RepairController, RepairLedger, RepairRecord
from .case_store import CaseSnapshot, CaseState, CaseStore, MeasurementResult, ResultImport
from .memory import EpistemicStatus, MemoryKind, MemoryScope, MemoryStore, ReflectionRecord, RunLogger, reflect_on_result
from .prediction import PredictionCoordinator
from .llm import DeepSeekChatClient, LLMError, MAESTROSettings, VisualInspection, VisualInspector
from .decision_critic import CritiqueOutcome, TypeSafeJevClient, TypeSafeSettings, TypedDecisionCritic
from .context import ContextBuilder, TaskIntent, TaskInterpreter, WorldModelRow, render_world_model_briefing, summarize_world_model, world_model_rows
from .knowledge import EvidenceLedger
from maestro.models import ContrastCheck, DecisionStatus, DevelopmentAction, EvidenceAction, EvidenceActionKind, EvidenceKind, EvidenceScope, FunctionalInterventionProfile, MeasurementStatus, MechanismContrast, MechanismHypothesis, NonDiscriminabilityReason, PremiseRequirement, RepairKind, RepairProposal
from .planner import LLMRepairDraft, MechanismContrastPlanner
from .tool_runtime import ToolExecution, ToolRouter, ToolRuntimeError
from virtual_cell.interface import prediction_request_errors
from virtual_cell.interface import PredictionCache, QueryAssessment, VirtualCellQueryTemplate, VirtualCellWorldModel
from virtual_cell import PredictionRequest, StatePrediction
from virtual_cell.state_adapter import StateAdapterConfig, StateCapabilityAdapter


@dataclass(frozen=True)
class AcceptedLLMRepair:
    draft: LLMRepairDraft
    contrast: MechanismContrast
    check: ContrastCheck


@dataclass(frozen=True)
class RepairOutcome:
    """Where check and repair left the contrast this round."""

    contrast: MechanismContrast
    check: ContrastCheck
    repair: RepairProposal | None
    records: tuple[RepairRecord, ...]
    stop_reason: str | None
    llm_repair: LLMRepairDraft | None


@dataclass(frozen=True)
class MAESTROTurn:
    """A fully auditable result from one user-facing MAESTRO interaction."""

    session_id: str
    intent: TaskIntent
    response: str
    contrast: MechanismContrast | None = None
    check: ContrastCheck | None = None
    repair: RepairProposal | None = None
    visual_inspections: tuple[VisualInspection, ...] = ()
    tool_executions: tuple[ToolExecution, ...] = ()
    case: CaseSnapshot | None = None
    llm_repair: LLMRepairDraft | None = None
    selected_actions: tuple[EvidenceAction, ...] = ()
    prediction: StatePrediction | None = None
    prediction_assessment: QueryAssessment | None = None
    repair_records: tuple[RepairRecord, ...] = ()
    repair_stop_reason: str | None = None
    action_predictions: Mapping[str, StatePrediction] = field(default_factory=dict)
    action_prediction_assessments: Mapping[str, QueryAssessment] = field(default_factory=dict)
    action_prediction_requests: Mapping[str, PredictionRequest] = field(default_factory=dict)
    # What the repair planner was shown about this round's virtual-cell queries.
    world_model_rows: tuple[WorldModelRow, ...] = ()
    # The menu's dependency structure under this round's profile (ActionTopology.summary()).
    action_topology: Mapping[str, object] = field(default_factory=dict)
    # One typed decision model's advisory review of this round, when one is configured.
    decision_review: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MAESTROCaseLoop:
    """Bounded execution trace for one case; only supplied results advance rounds."""

    case_id: str
    turns: tuple[MAESTROTurn, ...]
    reflections: tuple[ReflectionRecord, ...]
    stop_reason: str
    decision: DevelopmentDecision | None = None
    evidence_state: EvidenceState | None = None
    repair_trajectory: tuple[dict[str, object], ...] = ()
    measured_premises: tuple[MeasuredPremise, ...] = ()


class MAESTROOrchestrator:
    """Single-controller agent that keeps planning, observations, and evidence distinct."""

    _decision_critic: TypedDecisionCritic | None = None
    _runtime_client: object | None = None
    _decision_repeats: int = 1
    _outcome_forecaster: OutcomeForecaster | None = None
    _selection_strategy: str = "budgeted_coverage"

    def __init__(
        self,
        *,
        interpreter: TaskInterpreter,
        context_builder: ContextBuilder,
        planner: MechanismContrastPlanner,
        visual_inspector: VisualInspector,
        memory: MemoryStore,
        logger: RunLogger,
        controller: MAESTROAgent | None = None,
        tool_router: ToolRouter | None = None,
        case_store: CaseStore | None = None,
        enable_llm_repair: bool = False,
        virtual_cell: VirtualCellWorldModel | None = None,
        repair_controller: RepairController | None = None,
        interpretation_table: InterpretationTable | None = None,
        decision_engine: DecisionEngine | None = None,
        reliability: PredictionReliabilityLedger | None = None,
        source_clusters: SourceClusterIndex | None = None,
        max_repair_attempts: int = 3,
        power_aware_selection: bool = False,
        prediction_cache: PredictionCache | None = None,
        reuse_predictions: bool = True,
        max_parallel_predictions: int = 1,
        decision_critic: TypedDecisionCritic | None = None,
        outcome_forecaster: OutcomeForecaster | None = None,
        discrimination_selection: bool = False,
        selection_strategy: str | None = None,
        forecast_failure_policy: str = "stop",
    ):
        if selection_strategy is not None and (power_aware_selection or discrimination_selection):
            raise ValueError("Use selection_strategy or legacy flags, not both.")
        strategy = selection_strategy if selection_strategy is not None else (
            "discrimination" if discrimination_selection else
            "expected_coverage" if power_aware_selection else "budgeted_coverage"
        )
        if strategy not in ("budgeted_coverage", "expected_coverage", "discrimination"):
            raise ValueError("Unknown selection_strategy.")
        if strategy == "discrimination" and outcome_forecaster is None:
            raise ValueError("discrimination_selection requires an outcome_forecaster.")
        if forecast_failure_policy not in ("stop", "coverage"):
            raise ValueError("Unknown forecast_failure_policy.")
        self._interpreter = interpreter
        self._context_builder = context_builder
        self._planner = planner
        self._visual_inspector = visual_inspector
        self._memory = memory
        self._logger = logger
        self._controller = controller or MAESTROAgent()
        self._tool_router = tool_router
        self._case_store = case_store
        self._enable_llm_repair = enable_llm_repair
        self._repair_controller = repair_controller or RepairController(
            self._controller, max_attempts=max_repair_attempts
        )
        self._interpretation_table = interpretation_table or InterpretationTable()
        self._decision_engine = decision_engine or DecisionEngine()
        self._reliability = reliability or PredictionReliabilityLedger()
        # Scores restore planning reliability only, never mechanism conclusions.
        self._source_clusters = source_clusters or SourceClusterIndex()
        self._repair_ledgers: dict[str, RepairLedger] = {}
        self._evidence_states: dict[str, EvidenceState] = {}
        self._active_scientific_cases: set[str] = set()
        self._round_records: dict[str, RoundRecord] = {}
        self._round_results: dict[str, dict[str, RoundRecord]] = {}
        # What a result that arrives outside the case loop can be scored against:
        # the turn and the action of the plan that asked for it, recorded by run().
        # Exact plan identity for cases; anonymous repeated actions are ambiguous.
        self._reconciliation: dict[tuple[str, int, str], tuple["MAESTROTurn", EvidenceAction]] = {}
        self._reconciliation_by_action: dict[str, tuple["MAESTROTurn", EvidenceAction] | None] = {}
        self._selection_strategy = strategy
        self._forecast_failure_policy = forecast_failure_policy
        self._predictions = PredictionCoordinator(
            virtual_cell, logger,
            cache=prediction_cache if prediction_cache is not None else PredictionCache() if reuse_predictions else None,
            max_parallel_predictions=max_parallel_predictions,
        )
        self._decision_critic = decision_critic
        # Forecasts of each action's reading under each hypothesis. Without the flag they are
        # computed and logged beside the coverage choice (shadow); with it they choose the action.
        self._outcome_forecaster = outcome_forecaster
        self._restore_prediction_reliability()

    @property
    def selection_strategy(self) -> str:
        return self._selection_strategy

    @property
    def prediction_cache(self) -> PredictionCache | None:
        return self._predictions.cache

    @property
    def decision_critic(self) -> TypedDecisionCritic | None:
        return self._decision_critic

    def repair_ledger(self, case_id: str) -> RepairLedger:
        return self._repair_ledgers.setdefault(case_id, RepairLedger())

    def evidence_state(self, case_id: str) -> EvidenceState | None:
        return self._evidence_states.get(case_id)

    def recovery_capabilities(self, case_id: str) -> Mapping[str, object]:
        """Facts can resume; absent original scientific state cannot be reopened."""
        history = bool(self._case_store and self._case_store.result_identities(case_id))
        continuation = not history or case_id in self._active_scientific_cases
        return {"receive_results": self._case_store is not None,
                "query_facts_and_budget": self._case_store is not None,
                "scientific_continuation": continuation,
                "mechanism_state_restored": False,
                "reason": None if continuation else "scientific_state_not_restored"}

    def _restore_prediction_reliability(self) -> None:
        if self._case_store is None:
            return
        for receipt in self._case_store.prediction_scores():
            payload = receipt["score"]
            if payload.get("schema") != "runtime_prediction_score_v1":
                continue  # Historical research scores have no runtime aggregation contract.
            if payload.get("policy") != self._reliability.policy:
                raise ValueError("prediction_reliability_policy_mismatch")
            entry = dict(payload["entry"])
            for key in ("interval", "descriptive_interval"):
                if entry[key] is not None:
                    entry[key] = tuple(entry[key])
            if entry["result_id"] != receipt["result_id"] or entry["request_id"] != receipt["request_id"]:
                raise ValueError("prediction_reliability_identity_mismatch")
            pair = self._case_store.prediction_for_result(receipt["case_id"], receipt["result_id"])
            fact = self._case_store.measurement(receipt["case_id"], receipt["result_id"])
            request = PredictionRequest.from_dict(pair["payload"]["request"])
            answer = StatePrediction.from_dict(pair["payload"]["prediction"])
            if (not _answers(answer, request) or request.request_id != receipt["request_id"]
                    or request.case_id != receipt["case_id"] or request.plan_version != receipt["plan_version"]
                    or entry["action_identifier"] != receipt["action_identifier"]
                    or entry["model_version"] != answer.model_version or entry["readout"] not in request.readouts
                    or entry["context_identifier"] != fact.context_identifier
                    or entry["predicted_value"] != (answer.state_change or {}).get(entry["readout"])
                    or entry["realized_value"] != _to_float(fact.metrics.get(entry["readout"]))):
                raise ValueError("prediction_reliability_pair_mismatch")
            self._reliability.record(ScoredPrediction(**entry))

    @classmethod
    def from_workspace(
        cls,
        workspace: Path,
        *,
        state_directory: Path | None = None,
        enable_virtual_cell: bool = True,
        case_store: CaseStore | None = None,
        disable_case_store: bool = False,
        client: DeepSeekChatClient | None = None,
        source_clusters: SourceClusterIndex | None = None,
        max_repair_attempts: int = 3,
        virtual_cell: VirtualCellWorldModel | None = None,
        interpretation_table: InterpretationTable | None = None,
        decision_engine: DecisionEngine | None = None,
        max_parallel_predictions: int = 1,
        enable_decision_critic: bool = True,
        decision_repeats: int = 1,
        knowledge_packages: Sequence[Path] = (),
        outcome_forecaster: OutcomeForecaster | None = None,
        discrimination_selection: bool = False,
        selection_strategy: str | None = None,
        forecast_failure_policy: str = "stop",
    ) -> "MAESTROOrchestrator":
        """Create a controller; evaluations may supply an isolated state directory.

        ``client`` may be any structured completer, including the reviewed
        non-LLM template. ``virtual_cell`` replaces the default State adapter
        with any backend that satisfies the world-model protocol.
        """

        if selection_strategy is not None and discrimination_selection:
            raise ValueError("Use selection_strategy or legacy flags, not both.")
        settings = MAESTROSettings.from_workspace(workspace, require_provider=client is None)
        # The typed decision model is optional: with no TypeSafe block in the environment or
        # .env the critic is simply absent, and the loop behaves exactly as before.
        typesafe = TypeSafeSettings.from_workspace(workspace) if enable_decision_critic else None
        runtime_client = client if client is not None else DeepSeekChatClient(settings)
        runtime_directory = state_directory or settings.log_directory
        logger = RunLogger(runtime_directory)
        memory = MemoryStore(runtime_directory / "memory.sqlite")
        evidence = EvidenceLedger(runtime_directory / "evidence.sqlite")
        knowledge_package = workspace / "data" / "knowledge" / "biological_constraints.json"
        if knowledge_package.is_file():
            evidence.load_knowledge_package(knowledge_package)
        for package in knowledge_packages:
            evidence.load_knowledge_package(package if package.is_absolute() else workspace / package)
        controller = cls(
            interpreter=TaskInterpreter(runtime_client),
            context_builder=ContextBuilder(evidence, memory),
            planner=MechanismContrastPlanner(runtime_client),
            visual_inspector=VisualInspector(runtime_client, settings.vision_model),
            memory=memory,
            logger=logger,
            tool_router=ToolRouter(runtime_client, workspace / "tools"),
            selection_strategy=selection_strategy if selection_strategy is not None else (
                "discrimination" if discrimination_selection else "expected_coverage"),
            forecast_failure_policy=forecast_failure_policy,
            case_store=None if disable_case_store else case_store if case_store is not None else CaseStore(runtime_directory / "cases.sqlite"),
            enable_llm_repair=True,
            virtual_cell=(
                virtual_cell
                if virtual_cell is not None
                else (StateCapabilityAdapter(replace(StateAdapterConfig.from_workspace(workspace),
                                                      output_directory=runtime_directory / "artifacts" / "state"))
                      if enable_virtual_cell else None)
            ),
            interpretation_table=interpretation_table,
            decision_engine=decision_engine,
            source_clusters=source_clusters,
            max_repair_attempts=max_repair_attempts,
            max_parallel_predictions=max_parallel_predictions,
            decision_critic=(
                TypedDecisionCritic(TypeSafeJevClient(typesafe)) if typesafe is not None else None
            ),
            outcome_forecaster=outcome_forecaster,
        )
        # Keep the client the components share, so a run can report what it was charged. The
        # per-response usage is otherwise parsed and dropped at every call site.
        controller._runtime_client = runtime_client
        # Repetition is what lets a ranking earn the right to move a selection; each repeat
        # is a paid call, so the default asks once and says so rather than charging for it.
        controller._decision_repeats = max(1, int(decision_repeats))
        return controller

    @property
    def provider_usage(self) -> dict[str, int]:
        """What the language-model provider has charged this controller so far, if it knows.

        Empty when the runtime is a reviewed template or a stub, which report no usage by
        construction, so an empty mapping means "nothing metered", not "nothing spent".
        """

        return dict(getattr(self._runtime_client, "provider_usage", {}) or {})

    def run(
        self,
        user_message: str,
        *,
        available_actions: Sequence[EvidenceAction],
        intervention_profile: FunctionalInterventionProfile,
        image_paths: Sequence[Path] = (),
        dataset_paths: Sequence[Path] = (),
        case_id: str | None = None,
        budget: float | None = None,
        prediction_request: PredictionRequest | None = None,
        virtual_cell_template: VirtualCellQueryTemplate | None = None,
        expected_hypothesis_identifiers: Sequence[str] = (),
        expected_hypotheses: Sequence[MechanismHypothesis] = (),
        prior_evidence: Sequence[MeasuredPremise] = (),
        session_id: str | None = None,
        user_state: UserStateContext | None = None,
    ) -> MAESTROTurn:
        """Execute one bounded cycle without fabricating a biological result or tool capability."""

        if budget is not None and (
            isinstance(budget, bool) or not isinstance(budget, (int, float))
            or not math.isfinite(budget) or budget < 0
        ):
            raise ValueError("Budget must be finite and nonnegative.")
        session_id = session_id or str(uuid.uuid4())
        if user_state is not None:
            from maestro.hypothesis_forecast import UserStateContext
            if not isinstance(user_state, UserStateContext):
                raise ValueError("user_state_requires_compiled_context")
            if user_state.cell_context is not None and user_state.cell_context != intervention_profile.context_identifier:
                raise ValueError("user_state_context_mismatch")
        case_id = case_id or session_id
        case = self._case_store.open_case(case_id, budget=budget) if self._case_store else None
        awaiting_current_plan = case is not None and case.state is CaseState.AWAITING_RESULT
        if awaiting_current_plan:
            self._logger.event(
                "case_awaiting_result", {"case_id": case_id, "plan_version": case.plan_version},
                session_id=session_id,
            )
            return MAESTROTurn(
                session_id=session_id,
                intent=TaskIntent("awaiting_result", "Resume the persisted measurement plan.",
                                  (), (), intervention_profile.context_identifier, None,
                                  (), (), (), False),
                response="This case is awaiting measurements for its current plan; import those results before submitting a new execution plan.",
                case=case,
            )
        if case is not None and not self.recovery_capabilities(case_id)["scientific_continuation"]:
            self._logger.event("scientific_continuation_blocked", {"case_id": case_id,
                               "reason": "scientific_state_not_restored"}, session_id=session_id)
            return MAESTROTurn(
                session_id=session_id,
                intent=TaskIntent("scientific_recovery_blocked", "Original scientific state is unavailable.",
                                  (), (), intervention_profile.context_identifier, None, (), (), (), False),
                response="Facts, budget and pending-result reception remain available. Original mechanism, repair and decision state is not restored; create an explicitly registered new analysis instead of continuing this case.",
                case=case, repair_stop_reason="scientific_state_not_restored",
            )
        self._active_scientific_cases.add(case_id)
        self._logger.event(
            "runtime_contract",
            {"selection_strategy": self._selection_strategy,
             "selection_parameters": {"forecast_failure_policy": self._forecast_failure_policy},
             "prediction_use": "outcome_selection" if self._selection_strategy == "discrimination" else "response_advisory",
             "response_priority_use": "diagnostic" if self._selection_strategy == "expected_coverage" else "last_tiebreak",
             "rule_contract": "registered_interpretation_table_or_default_rules_for_contrast",
             "registered_rules": [json.loads(json.dumps(asdict(rule), default=sorted)) for rule in self._interpretation_table.rules],
             "action_menu": [asdict(action) for action in available_actions], "budget": budget,
             "remaining_budget": case.remaining_budget if case is not None else budget,
             "user_state_identity": user_state.identity() if user_state is not None else None,
             "model_backend": self._predictions.backend_name()}, session_id=session_id,
        )
        self._logger.event(
            "task_received",
            {
                "message": user_message,
                "available_action_count": len(available_actions),
                "dataset_count": len(dataset_paths),
            },
            session_id=session_id,
        )
        intent = self._interpreter.interpret(user_message)
        self._logger.event("task_interpreted", asdict(intent), session_id=session_id)
        self._memory.remember(
            user_message,
            kind=MemoryKind.WORKING,
            status=EpistemicStatus.PROPOSED,
            provenance="user_message",
            session_id=session_id,
            scope=MemoryScope(case_id=case_id, task_type=intent.task_type, biological_context=intent.biological_context),
        )
        from .knowledge import BiologicalConditions

        context = self._context_builder.build(
            intent,
            memory_scope=MemoryScope(case_id=case_id, task_type=intent.task_type, biological_context=intent.biological_context),
            biological_conditions=BiologicalConditions(
                context=intervention_profile.context_identifier or intent.biological_context,
                time_hours=intervention_profile.time_hours,
                species=(prediction_request.context.species if prediction_request else
                         virtual_cell_template.context.species if virtual_cell_template else None),
            ),
        )
        self._logger.event(
            "context_built",
            {
                "evidence_count": len(context.evidence),
                "memory_count": len(context.memories),
                "included_record_ids": context.included_record_ids,
                "omitted_record_ids": context.omitted_record_ids,
                "omission_reasons": context.omission_reasons,
                "budget_error": context.budget_error,
            },
            session_id=session_id,
        )
        if context.budget_error is not None:
            self._logger.event(
                "context_budget_insufficient", {"reason": context.budget_error}, session_id=session_id
            )
            return MAESTROTurn(
                session_id=session_id,
                intent=intent,
                response="The required task state exceeds the configured context budget; no plan was generated.",
                case=case,
            )

        tool_executions = self._run_dataset_tool(context, dataset_paths, session_id)
        for execution in tool_executions:
            context = self._context_builder.add_tool_execution(context, execution)

        visual_inspections = self._inspect_visuals(intent, image_paths, session_id)
        context = self._context_builder.add_visual_reviews(context, visual_inspections)
        if intent.requires_clarification:
            response = self._clarification_response(intent, visual_inspections)
            self._logger.event("clarification_requested", {"missing": intent.missing_information}, session_id=session_id)
            return MAESTROTurn(
                session_id=session_id,
                intent=intent,
                response=response,
                visual_inspections=visual_inspections,
                tool_executions=tool_executions,
                case=case,
            )

        if prediction_request is not None and virtual_cell_template is not None:
            raise ValueError("Provide either prediction_request or virtual_cell_template, not both.")
        feedback_marks = self._planner_feedback_marks()
        try:
            proposal = self._planner.propose(
                context,
                available_actions,
                required_hypothesis_identifiers=expected_hypothesis_identifiers,
                expected_hypotheses=expected_hypotheses,
            )
        finally:
            # Logged whether or not the correction succeeded; a failure still
            # propagates, because an evaluation records it as a lost case.
            self._log_planner_feedback(feedback_marks, "contrast_planner", session_id)
        contrast = proposal.to_contrast(available_actions)
        remaining = case.remaining_budget if case and case.remaining_budget is not None else budget
        prediction_candidates, prediction_rejected = [], {}
        for action in available_actions:
            if isinstance(action.cost, bool) or not isinstance(action.cost, (int, float)) or not math.isfinite(action.cost) or action.cost < 0:
                prediction_rejected[action.identifier] = "invalid_action_cost"
            elif remaining is not None and action.cost > remaining:
                prediction_rejected[action.identifier] = "unaffordable"
            elif missing := intervention_profile.unmeasured(action.prerequisites):
                prediction_rejected[action.identifier] = "missing_prerequisites:" + ",".join(missing)
            else:
                prediction_candidates.append(action)
        self._logger.event(
            "virtual_cell_candidates_filtered",
            {"eligible_action_ids": [a.identifier for a in prediction_candidates],
             "rejected": prediction_rejected, "remaining_budget": remaining,
             "scope": "prediction calls only; the registered evidence menu remains available"},
            session_id=session_id,
        )
        world = self._predictions.query(
            contrast, intent, case, case_id, session_id, tuple(prediction_candidates),
            prediction_request=prediction_request, template=virtual_cell_template,
        )
        action_requests, action_assessments, action_predictions = (
            world.requests, world.assessments, world.predictions
        )
        effective_request, prediction, prediction_assessment = world.request, world.prediction, world.assessment
        briefing_rows = world_model_rows(
            available_actions, action_requests, action_assessments, action_predictions, self._reliability
        )
        topology = ActionTopology.build(available_actions, intervention_profile).summary()
        self._logger.event("action_topology", topology, session_id=session_id)
        review = self._review_plan(
            contrast, available_actions, intervention_profile, briefing_rows, topology, session_id,
            evidence_summary=context.rendered,
        )
        reviewed_action_ids = [action.identifier for action in contrast.actions()]
        reviewed_conditions = [asdict(action) for action in contrast.actions()]
        selection = self._select_budgeted_actions(
            contrast, available_actions, intervention_profile, case, budget, session_id,
            prediction=prediction, prediction_request=effective_request,
            action_predictions=action_predictions, action_requests=action_requests, case_id=case_id,
            prior_evidence=prior_evidence,
            user_state=user_state,
        )
        acquisition_stop = self._acquisition_stop_reason(session_id)
        if selection is not None and selection.actions and ((self._selection_strategy == "discrimination") or not selection.uncovered):
            contrast = replace(
                contrast,
                plan=selection.actions[0],
                additional_plans=selection.actions[1:],
            )
        if contrast.plan is not None:
            prediction = action_predictions.get(contrast.plan.identifier)
            prediction_assessment = action_assessments.get(contrast.plan.identifier)
        outcome = self._check_and_repair(
            context, contrast, intervention_profile, available_actions, prediction, action_predictions,
            case_id=case_id, session_id=session_id, world_model_briefing=render_world_model_briefing(briefing_rows),
            action_topology=topology, advisory_findings=review.findings,
        )
        contrast, check, repair, llm_repair = outcome.contrast, outcome.check, outcome.repair, outcome.llm_repair
        repair_records, repair_stop_reason = outcome.records, outcome.stop_reason
        prediction = action_predictions.get(contrast.plan.identifier) if contrast.plan is not None else None
        prediction_assessment = action_assessments.get(contrast.plan.identifier) if contrast.plan is not None else None
        execution_actions = self._execution_actions(
            contrast, check, repair, intervention_profile, available_actions
        )
        if self._selection_strategy in ("expected_coverage", "discrimination") and selection is not None:
            allowed = {action.identifier for action in selection.actions}
            execution_actions = tuple(action for action in execution_actions if action.identifier in allowed)
        execution_stop = None
        remaining = case.remaining_budget if case and case.remaining_budget is not None else budget
        if remaining is not None and sum(action.cost for action in execution_actions) > remaining:
            execution_stop = "Planned action exceeds the remaining case budget."
            self._logger.event(
                "execution_budget_rejected",
                {"selected_action_ids": [action.identifier for action in execution_actions], "remaining_budget": remaining},
                session_id=session_id,
            )
            execution_actions = ()
        final_audit = {
            "reviewed_action_ids": reviewed_action_ids if review.model_version else [],
            "submitted_action_ids": [action.identifier for action in execution_actions],
            "reviewed_conditions": reviewed_conditions if review.model_version else [],
            "submitted_conditions": [asdict(action) for action in execution_actions],
            "review_matches_submitted_plan": (
                reviewed_conditions == [asdict(action) for action in execution_actions]
                if review.model_version else None
            ),
            "scope": "complete declared action conditions; review remains advisory, no additional model call",
        }
        self._logger.event("final_plan_audit", final_audit, session_id=session_id)
        selection_source = (
            self._selection_strategy
        ) if selection is not None else "planner_and_directed_repair"
        self._logger.event(
            "prediction_usage",
            {"backend": self._predictions.backend_name(), "selection_source": selection_source,
             "response_prediction_use": "advisory_and_constraint_checks",
             "response_priority_use": (
                 "last_tiebreak_only" if selection_source in ("discrimination", "budgeted_coverage")
                 else "diagnostic_only"
             ),
             "outcome_forecast_use": (
                 "selection" if (self._selection_strategy == "discrimination") and selection is not None
                 else "shadow" if self._outcome_forecaster is not None and selection is not None
                 else "not_used"
             ),
             "queried_action_ids": list(action_requests),
             "submitted_action_ids": final_audit["submitted_action_ids"]},
            session_id=session_id,
        )
        if awaiting_current_plan:
            execution_actions = ()
            self._logger.event(
                "case_awaiting_result", {"case_id": case_id, "plan_version": case.plan_version},
                session_id=session_id,
            )
        elif self._case_store:
            stop_reason = execution_stop or (None if repair is None or repair.replacement_action else repair.interpretation_boundary)
            if acquisition_stop is not None and not execution_actions:
                stop_reason = acquisition_stop
            case = self._case_store.record_plan(
                case_id,
                execution_actions,
                ready_to_measure=bool(execution_actions),
                context_identifier=intervention_profile.context_identifier,
                stop_reason=stop_reason,
            )
        self._logger.event("contrast_proposed", asdict(proposal), session_id=session_id)
        self._logger.experiment(
            "contrast_checked",
            {
                "contrast": asdict(contrast),
                "check": asdict(check),
                "repair": asdict(repair) if repair else None,
                "repair_records": [record.as_trajectory() for record in repair_records],
                "repair_stop_reason": repair_stop_reason,
                "llm_repair": asdict(llm_repair) if llm_repair else None,
                "prediction": asdict(prediction) if prediction else None,
                "prediction_assessment": asdict(prediction_assessment) if prediction_assessment else None,
                "action_predictions": {key: asdict(value) for key, value in action_predictions.items()},
                "action_prediction_assessments": {key: asdict(value) for key, value in action_assessments.items()},
                "world_model_rows": [row.as_payload() for row in briefing_rows],
                "selected_action_ids": [action.identifier for action in execution_actions],
                "visual_inspection_count": len(visual_inspections),
                "tool_execution_count": len(tool_executions),
            },
            session_id=session_id,
        )
        self._memory.remember(
            self._memory_summary(contrast, check, repair),
            kind=MemoryKind.EPISODIC,
            status=EpistemicStatus.PROPOSED,
            provenance="mechanism_contrast_run",
            session_id=session_id,
        )
        turn = MAESTROTurn(
            session_id=session_id,
            intent=intent,
            response=(
                "This case is awaiting measurements for its current plan; import those results before submitting a new execution plan."
                if awaiting_current_plan
                else self._decision_response(contrast, check, repair, visual_inspections, tool_executions)
            )
            + summarize_world_model(briefing_rows),
            contrast=contrast,
            check=check,
            repair=repair,
            visual_inspections=visual_inspections,
            tool_executions=tool_executions,
            case=case,
            llm_repair=llm_repair,
            selected_actions=execution_actions,
            prediction=prediction,
            prediction_assessment=prediction_assessment,
            repair_records=repair_records,
            repair_stop_reason=repair_stop_reason,
            action_predictions=action_predictions,
            action_prediction_assessments=action_assessments,
            action_prediction_requests=action_requests,
            world_model_rows=briefing_rows,
            action_topology=topology,
            decision_review={**review.payload(), **final_audit} if review.model_version else {},
        )
        for action in execution_actions:
            if case is not None:
                self._reconciliation[(case_id, case.plan_version, action.identifier)] = (turn, action)
                request = action_requests.get(action.identifier)
                answer = action_predictions.get(action.identifier)
                if (request is not None and answer is not None and answer.applicable and _answers(answer, request)
                        and request.case_id == case_id and request.plan_version == case.plan_version):
                    self._case_store.record_prediction(case_id, case.plan_version, action.identifier, request.request_id,
                        {"schema": "state_response_pair_v1", "request": request.to_dict(), "prediction": asdict(answer),
                         "action": {name: getattr(action, name) for name in (
                             "identifier", "description", "cost", "distinguishes", "prediction_readout",
                             "execution_context", "context_bound", "time_hours", "expected_conditions")},
                         "biological_context": intent.biological_context})
            if action.identifier in self._reconciliation_by_action:
                self._reconciliation_by_action[action.identifier] = None
            else:
                self._reconciliation_by_action[action.identifier] = (turn, action)
        self._write_plan_round(
            turn,
            context=context,
            profile=intervention_profile,
            check=check,
            repair=repair,
            selection=selection,
            available_actions=available_actions,
            execution_actions=execution_actions,
        )
        return turn

    def _check_and_repair(
        self,
        context,
        contrast: MechanismContrast,
        profile: FunctionalInterventionProfile,
        available_actions: Sequence[EvidenceAction],
        prediction: StatePrediction | None,
        action_predictions: Mapping[str, StatePrediction],
        *,
        case_id: str,
        session_id: str,
        world_model_briefing: str,
        action_topology: Mapping[str, object] | None = None,
        advisory_findings: Sequence[str] = (),
    ) -> RepairOutcome:
        """Check the contrast, run the ruled repair, then give the LLM one repair attempt.

        The LLM's attempt is made against the original failure and the ruled
        repair stays the baseline: an LLM draft is adopted only after the
        deterministic re-check, and a ruled repair only when re-checking removed
        every failure it was triggered by.
        """

        check = self._controller.check_contrast(contrast, profile, prediction, self._reliability)
        ledger = self.repair_ledger(case_id)
        rule_outcome = self._repair_controller.run(
            contrast,
            check,
            available_actions,
            profile,
            prediction,
            ledger=ledger,
            action_predictions=action_predictions,
            reliability=self._reliability,
        )
        repair = rule_outcome.proposal
        repair_records = rule_outcome.records
        repair_stop_reason = rule_outcome.stop_reason
        # The LLM gets its repair attempt against the original failure; the ruled repair is the baseline.
        accepted_repair = self._propose_llm_repair(
            context, contrast, check, available_actions, profile, prediction, session_id,
            action_predictions=action_predictions,
            world_model_briefing=world_model_briefing,
            action_topology=action_topology,
            advisory_findings=advisory_findings,
        )
        llm_repair = accepted_repair.draft if accepted_repair else None
        if accepted_repair is not None:
            contrast = accepted_repair.contrast
            check = accepted_repair.check
            if check.ready_for_mechanism_update:
                repair = None
            else:
                follow_up = self._repair_controller.run(
                    contrast, check, available_actions, profile, prediction, ledger=ledger,
                    action_predictions=action_predictions, reliability=self._reliability,
                )
                repair = follow_up.proposal
                repair_records = repair_records + follow_up.records
                repair_stop_reason = follow_up.stop_reason
                if follow_up.check.ready_for_mechanism_update:
                    contrast, check = follow_up.contrast, follow_up.check
                    repair = None
        elif rule_outcome.check.ready_for_mechanism_update:
            # Adopt a ruled repair only when re-checking removed every failure it was triggered by.
            contrast, check = rule_outcome.contrast, rule_outcome.check
            repair = None
        return RepairOutcome(contrast, check, repair, tuple(repair_records), repair_stop_reason, llm_repair)

    def _write_plan_round(
        self,
        turn: MAESTROTurn,
        *,
        context,
        profile: FunctionalInterventionProfile,
        check: ContrastCheck,
        repair: RepairProposal | None,
        selection,
        available_actions: Sequence[EvidenceAction],
        execution_actions: Sequence[EvidenceAction],
    ) -> RoundRecord | None:
        """Write the structured handoff this round's plan implies, if it is complete.

        The record is the round's L1 to L4 state as structured data. An incomplete
        record is refused and logged rather than written, because a written record
        with a missing mandatory field is read later as though the field had been
        answered.
        """

        contrast = turn.contrast
        assert contrast is not None  # the caller writes only after a contrast exists
        defer_flag = repair is not None and repair.kind is RepairKind.DEFER
        comparability = ComparabilityStatus.UNKNOWN
        if NonDiscriminabilityReason.UNMATCHED_INTERVENTION_MODE in check.reasons:
            comparability = ComparabilityStatus.MODE_UNMATCHED
        elif check.ready_for_mechanism_update:
            comparability = ComparabilityStatus.COMPARABLE if profile.mode else ComparabilityStatus.UNKNOWN
        elif (
            NonDiscriminabilityReason.MISSING_PREREQUISITE in check.reasons
            or NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT in check.reasons
        ):
            comparability = ComparabilityStatus.INSUFFICIENT_EVIDENCE
        missing_reason = tuple(check.missing_prerequisites)
        if comparability is ComparabilityStatus.UNKNOWN and not missing_reason:
            missing_reason = ("comparability_not_declared",)
        plan = contrast.plan
        readout = None
        if plan is not None:
            readout = plan.prediction_readout or plan.readout
        prediction = turn.prediction
        if prediction is None:
            world_model = WorldModelLayer.no_model()
        else:
            mean = None
            if prediction.applicable and prediction.state_change and readout:
                value = prediction.state_change.get(readout)
                mean = float(value) if isinstance(value, (int, float)) else None
            band = prediction.interval_for(readout) if readout else None
            world_model = WorldModelLayer(
                # L2 is a decision gate: only an explicit True licenses in-domain use.
                # The raw prediction still retains None when distribution is unknown.
                in_distribution=prediction.in_distribution is True,
                model_id=prediction.model_version,
                mean=mean,
                interval=(band.low, band.high) if band is not None else None,
                abstain_reason=(
                    None
                    if prediction.applicable
                    else prediction.abstain_reason or "; ".join(prediction.limitations) or "unsupported"
                ),
                validation_status=(
                    turn.prediction_assessment.validation_status.value
                    if turn.prediction_assessment is not None
                    else "unknown"
                ),
                readout=readout,
            )
        registered_predictions: dict[str, float] = {}
        for action in available_actions:
            if not action.prediction_readout:
                continue
            action_prediction = turn.action_predictions.get(action.identifier)
            if action_prediction is None or not action_prediction.state_change:
                continue
            value = action_prediction.state_change.get(action.prediction_readout)
            if isinstance(value, (int, float)):
                registered_predictions[action.identifier] = float(value)
        # A blocked candidate is blocked by its own declaration, not by the selector,
        # so the reason is derived here as well and merged with the selector's list.
        waiting = list(selection.waiting_for_prerequisites) if selection is not None else []
        for action in available_actions:
            missing = profile.unmeasured(action.prerequisites)
            if not missing:
                continue
            entry = f"{action.identifier}: {', '.join(missing)}"
            if entry not in waiting:
                waiting.append(entry)
        record = RoundRecord(
            session_id=turn.session_id,
            round_index=int(turn.case.plan_version) if turn.case and turn.case.plan_version else 1,
            evidence=EvidenceLayer(
                records=tuple(context.included_record_ids),
                conflicts=contrast.identifiers(),
                comparability_status=comparability,
                missing_reason=missing_reason,
            ),
            world_model=world_model,
            decision=DecisionLayer(
                chosen=tuple(action.identifier for action in execution_actions),
                rejected=rejected_from_selection(
                    (action.identifier for action in available_actions),
                    (action.identifier for action in execution_actions),
                    waiting=tuple(waiting),
                    reason_overrides=(selection.rejection_reasons if selection is not None else {}),
                ),
                rationale="; ".join(reason.value for reason in check.reasons) or "ready_for_mechanism_update",
                registered_predictions=registered_predictions,
                defer_flag=defer_flag,
            ),
            execution=ExecutionLayer(
                stop_decision=(
                    "deferred"
                    if defer_flag
                    else "planned_pending_result"
                    if execution_actions
                    else "no_executable_action"
                )
            ),
        )
        if not self._logger.round(record, stage="plan",
                                  case_id=turn.case.case_id if turn.case else None,
                                  plan_version=turn.case.plan_version if turn.case else None):
            return None
        self._round_records[turn.session_id] = record
        return record

    def _write_result_round(
        self,
        turn: MAESTROTurn,
        action: EvidenceAction,
        result: MeasurementResult,
        admission: ValidatedEvidenceUpdate | None,
        state: EvidenceState | None,
        *,
        result_id: str,
    ) -> RoundRecord | None:
        """Update this round's L4 layer from the real result that arrived.

        Each result fills its own copy of the original plan view. RunLogger
        persists immutable result views; the run review reads every result.
        CaseStore remains the fact authority. These in-process caches do not
        restore scientific state after a restart.
        """

        plan = self._round_records.get(turn.session_id)
        if plan is None:
            return None
        eliminated: tuple[str, ...] = ()
        if admission is not None and state is not None:
            for update in state.updates:
                if update.result_id == admission.result_id:
                    eliminated = tuple(update.eliminated)
        observed: dict[str, float] = {}
        for name, value in dict(result.metrics or {}).items():
            number = _to_float(value)
            if number is not None:
                observed[str(name)] = number
        # Belief delta is set membership, not probability: a removed hypothesis is
        # marked -1, an admitted field +1, and nothing here is a posterior.
        belief_delta: dict[str, float] = {name: -1.0 for name in eliminated}
        for field_name in (admission.admitted_fields if admission is not None else ()):
            belief_delta[str(field_name)] = 1.0
        record = replace(
            plan,
            execution=ExecutionLayer(
                observed=observed,
                belief_delta=belief_delta,
                contradiction_flag=bool(admission is not None and admission.admissible and eliminated),
                stop_decision=f"result_imported:{action.identifier}",
                result_id=result_id,
            ),
        )
        if not self._logger.round(record, stage="result",
                                  case_id=turn.case.case_id if turn.case else None,
                                  plan_version=turn.case.plan_version if turn.case else None):
            return None
        self._round_results.setdefault(turn.session_id, {})[result_id] = record
        return record

    def _execution_actions(
        self,
        contrast: MechanismContrast,
        check: ContrastCheck,
        repair: RepairProposal | None,
        profile: FunctionalInterventionProfile,
        available_actions: Sequence[EvidenceAction],
    ) -> tuple[EvidenceAction, ...]:
        """Decide what to execute now, using the same rule as the replay evaluation.

        A ready contrast executes its bundle. A failing one executes the repair
        target, and when that target's own interpretation premise is not yet
        measured, the registered capability that supplies it becomes the step
        instead. An explicit deferral executes nothing: the repair layer has
        just reported that no registered edit can make this contrast decide, so
        running the failing plan would spend the budget on a measurement already
        known not to separate the explanations.
        """

        if check.ready_for_mechanism_update:
            return contrast.actions()
        if repair is not None and repair.kind is RepairKind.DEFER:
            return ()
        functional_plan = (
            contrast.plan
            if (
                contrast.plan is not None
                and contrast.plan.kind is EvidenceActionKind.FUNCTIONAL_MEASUREMENT
                and not profile.unmeasured(contrast.plan.prerequisites)
            )
            else None
        )
        candidates = (
            functional_plan,
            repair.replacement_action if repair is not None else None,
            contrast.plan,
        )
        step = self._controller.next_executable_action(candidates, profile, available_actions)
        return (step,) if step is not None else ()

    def run_case_loop(
        self,
        user_message: str,
        *,
        available_actions: Sequence[EvidenceAction],
        intervention_profile: FunctionalInterventionProfile,
        result_provider: Callable[[EvidenceAction, MAESTROTurn], MeasurementResult | None],
        case_id: str,
        budget: float | None = None,
        max_rounds: int = 4,
        image_paths: Sequence[Path] = (),
        dataset_paths: Sequence[Path] = (),
        prediction_request: PredictionRequest | None = None,
        virtual_cell_template: VirtualCellQueryTemplate | None = None,
        expected_hypothesis_identifiers: Sequence[str] = (),
        expected_hypotheses: Sequence[MechanismHypothesis] = (),
        user_state: UserStateContext | None = None,
    ) -> MAESTROCaseLoop:
        """Run plan-observe-reflect cycles, stopping before any unsupplied measurement.

        ``result_provider`` is an explicit boundary: it may return a real result
        for a selected action or ``None`` to leave the case awaiting that result.
        ``expected_hypotheses`` registers the explanations' definitions once for
        every round, so a reworded model answer keeps the registered meaning
        instead of ending the loop as a changed definition.
        """

        if expected_hypotheses and not expected_hypothesis_identifiers:
            expected_hypothesis_identifiers = tuple(item.identifier for item in expected_hypotheses)

        if max_rounds < 1:
            raise ValueError("max_rounds must be positive.")
        if self._case_store is None:
            raise RuntimeError("Multi-round execution requires a configured CaseStore.")
        self._case_store.open_case(case_id, budget=budget)
        if self._case_store.result_identities(case_id):
            self._logger.event("scientific_continuation_blocked", {"case_id": case_id,
                               "reason": "scientific_loop_state_not_restored"}, session_id=case_id)
            return MAESTROCaseLoop(case_id, (), (), "scientific_loop_state_not_restored")
        profile = intervention_profile
        loop_token = f"loop-{uuid.uuid4().hex[:12]}"
        turns: list[MAESTROTurn] = []
        reflections: list[ReflectionRecord] = []
        stop_reason = "max_rounds_reached"
        state: EvidenceState | None = None
        admitted_scopes: dict[str, EvidenceScope] = {}
        observed_units: dict[str, int] = {}
        evidence_ids: list[str] = []
        measured_premises: list[MeasuredPremise] = []
        hypothesis_signature: tuple[tuple[str, str, str | None, object], ...] | None = None
        decision: DevelopmentDecision | None = None
        for round_index in range(1, max_rounds + 1):
            result_quality_failed = False
            turn = self.run(
                user_message,
                available_actions=available_actions,
                intervention_profile=profile,
                image_paths=image_paths if round_index == 1 else (),
                dataset_paths=dataset_paths if round_index == 1 else (),
                case_id=case_id,
                budget=budget,
                prediction_request=prediction_request,
                virtual_cell_template=virtual_cell_template,
                expected_hypothesis_identifiers=expected_hypothesis_identifiers,
                expected_hypotheses=expected_hypotheses,
                prior_evidence=measured_premises,
                user_state=user_state,
                session_id=f"{loop_token}-round-{round_index}",
            )
            turns.append(turn)
            if turn.contrast is not None:
                signature = tuple(sorted(
                    (item.identifier, item.description, item.causal_factor, item.proposed_action)
                    for item in turn.contrast.hypotheses
                ))
                if hypothesis_signature is not None and signature != hypothesis_signature:
                    # A wording/definition change is not evidence that refuted hypotheses
                    # are alive again. New identifiers retain history but require new rules;
                    # changed definitions under old identifiers retain the original state.
                    previous_ids = {item[0] for item in hypothesis_signature}
                    if previous_ids != set(turn.contrast.identifiers()):
                        state = self._state_for_round(case_id, state, turn.contrast)
                    self._logger.event(
                        "hypothesis_definition_changed",
                        {"previous": hypothesis_signature, "proposed": signature,
                         "action": "require_new_rule_registration"}, session_id=turn.session_id,
                    )
                    decision = DevelopmentDecision(
                        status=DecisionStatus.DEFERRED, action=DevelopmentAction.DEFER,
                        evidence_ids=tuple(evidence_ids),
                        unmet_requirements=("hypothesis_definition_changed:requires_new_rule_registration",),
                        rationale="The planner changed the registered explanation definitions during a measured loop.",
                        boundary="No old interpretation rule is applied to a changed hypothesis; prior refutations remain recorded.",
                    )
                    self._case_store.record_decision(case_id, status=decision.status.value)
                    stop_reason = "hypothesis_definition_changed"
                    break
                hypothesis_signature = signature
                state = self._state_for_round(case_id, state, turn.contrast)
            if not turn.selected_actions:
                stop_reason = (
                    turn.repair_stop_reason if turn.repair_stop_reason == "scientific_state_not_restored"
                    else "awaiting_result" if turn.case is not None and turn.case.state is CaseState.AWAITING_RESULT
                    else "no_executable_action"
                )
                break
            awaiting = False
            for action in turn.selected_actions:
                result = result_provider(action, turn)
                if result is None:
                    awaiting = True
                    continue
                if result.action_identifier != action.identifier:
                    raise ValueError("Result action does not match the selected action being executed.")
                if (result.evidence_kind is not EvidenceKind.REAL_MEASUREMENT and not (
                        action.kind is EvidenceActionKind.EVIDENCE_REVIEW and result.evidence_kind in (
                            EvidenceKind.DERIVED_ANALYSIS, EvidenceKind.RETRIEVED_SOURCE))):
                    self._logger.event("nonmeasurement_result_rejected", {"case_id": case_id,
                        "action_identifier": action.identifier, "evidence_kind": result.evidence_kind.value},
                        session_id=turn.session_id)
                    awaiting = True
                    continue
                imported = self.import_measurement(case_id, result)
                result = replace(result, result_id=imported.result_id)
                if not imported.created:
                    # A repeated result identifier is not a second observation; the
                    # admission below would otherwise score the same measurement twice.
                    self._logger.event(
                        "duplicate_result_ignored",
                        {"case_id": case_id, "result_id": imported.result_id},
                        session_id=turn.session_id,
                    )
                    continue
                reflection = reflect_on_result(case_id, imported.result_id, result)
                self._record_reflection(reflection, turn.session_id)
                reflections.append(reflection)
                admission: ValidatedEvidenceUpdate | None = None
                if state is not None and turn.contrast is not None:
                    state, admission = self._interpret_observation(
                        case_id, state, turn.contrast, profile, result, action, turn,
                        prior_evidence=measured_premises,
                    )
                    measured_premises.extend(admission.measured_premises)
                    if admission.admissible:
                        evidence_ids.append(admission.result_id)
                        for field_name in admission.admitted_fields:
                            admitted_scopes[field_name] = _stronger_scope(
                                admitted_scopes.get(field_name), admission.scope
                            )
                            observed_units[field_name] = max(
                                observed_units.get(field_name, 0),
                                result.independent_units if result.independent_units is not None else 0,
                            )
                self._score_repair_result(case_id, turn, action, result, admission)
                self._write_result_round(
                    turn, action, result, admission, state, result_id=imported.result_id
                )
                profile = self._profile_after_result(profile, result, admission)
                if not result.quality_passed:
                    stop_reason = "result_quality_failed"
                    result_quality_failed = True
                    # Drain this committed bundle. A provider returns an available
                    # result or None; it must not silently start an unrelated plan.
                    # Stop new rounds only after all sibling results are processed.
            snapshot = self._case_store.snapshot(case_id)
            if awaiting or snapshot.state is CaseState.AWAITING_RESULT:
                stop_reason = "awaiting_result" if stop_reason == "max_rounds_reached" else stop_reason
                break
            if state is not None and turn.contrast is not None:
                decision = self._decide(
                    case_id, state, turn.contrast, admitted_scopes, observed_units, evidence_ids, turn, snapshot
                )
                if result_quality_failed:
                    break
                if decision is not None and decision.is_terminal:
                    # A terminal decision ends the case in the same transition that produced it.
                    self._case_store.record_decision(case_id, status=decision.status.value)
                    stop_reason = f"decision:{decision.status.value}"
                    break
            if result_quality_failed:
                break
            if snapshot.remaining_budget is not None and snapshot.remaining_budget <= 0:
                stop_reason = "budget_exhausted"
                break
        records = tuple(
            record for turn in turns if turn.session_id in self._round_records
            for record in (tuple(self._round_results.get(turn.session_id, {}).values())
                           or (self._round_records[turn.session_id],))
        )
        if records:
            self._logger.event(
                "round_records_reviewed",
                dict(review_run(records)),
                session_id=case_id,
            )
        return MAESTROCaseLoop(
            case_id,
            tuple(turns),
            tuple(reflections),
            stop_reason,
            decision=decision,
            evidence_state=state,
            repair_trajectory=self.repair_ledger(case_id).trajectory(),
            measured_premises=tuple(measured_premises),
        )

    def _state_for_round(
        self,
        case_id: str,
        state: EvidenceState | None,
        contrast: MechanismContrast,
    ) -> EvidenceState:
        """Open the evidence state, and make a hypothesis-space change explicit.

        A later round can present different hypothesis identifiers.  Silently
        keeping the old compatible set would let a renamed hypothesis inherit an
        already-eliminated status, and would let a new contrast inherit a
        resolution it never earned, so the change is recorded as a migration and
        the compatible set is rebuilt from the new pair.  Prior update records are
        kept as history, not as standing conclusions.
        """

        expected = {hypothesis.identifier for hypothesis in contrast.hypotheses}
        if state is None:
            return EvidenceState.open(contrast.hypotheses)
        if set(state.candidates | state.eliminated) == expected:
            return state
        self._logger.event(
            "hypothesis_space_migrated",
            {
                "case_id": case_id,
                "previous_candidates": sorted(state.candidates),
                "previous_eliminated": sorted(state.eliminated),
                "new_hypotheses": sorted(expected),
                "retained_update_records": len(state.updates),
            },
            session_id=case_id,
        )
        return EvidenceState(
            candidates=frozenset(expected),
            eliminated=frozenset(),
            updates=state.updates,
            independent_source_clusters=state.independent_source_clusters,
        )

    def _decide(
        self,
        case_id: str,
        state: EvidenceState,
        contrast: MechanismContrast,
        admitted_scopes: Mapping[str, EvidenceScope],
        observed_units: Mapping[str, int],
        evidence_ids: Sequence[str],
        turn: MAESTROTurn,
        snapshot: CaseSnapshot,
    ) -> DevelopmentDecision:
        """Compute the stage decision from this round's admitted evidence."""

        self._evidence_states[case_id] = state
        decision = self._decision_engine.decide(
            state,
            contrast,
            admitted_scopes=admitted_scopes,
            observed_units=observed_units,
            evidence_ids=tuple(dict.fromkeys(evidence_ids)),
            remaining_budget=snapshot.remaining_budget,
            executable_actions=turn.selected_actions,
        )
        self._logger.event(
            "development_decision",
            {
                "case_id": case_id,
                "status": decision.status.value,
                "action": decision.action.value if decision.action else None,
                "unmet_requirements": list(decision.unmet_requirements),
                "terminal": decision.is_terminal,
            },
            session_id=turn.session_id,
        )
        return decision

    def _interpret_observation(
        self,
        case_id: str,
        state: EvidenceState,
        contrast: MechanismContrast,
        profile: FunctionalInterventionProfile,
        result: MeasurementResult,
        action: EvidenceAction,
        turn: MAESTROTurn,
        *,
        prior_evidence: Sequence[MeasuredPremise] = (),
    ) -> tuple[EvidenceState, ValidatedEvidenceUpdate]:
        """Interpret a result against its own action, then admit it exactly once."""

        table = (
            self._interpretation_table
            if self._interpretation_table.rules
            else InterpretationTable(default_rules_for(contrast))
        )
        plan = self._action_for_result(contrast, result, action)
        interpretation = table.interpret(result, contrast, profile, plan, prior_evidence=prior_evidence)
        cluster = self._source_clusters.cluster_of(result.source_id) if result.source_id else None
        admission = admit_evidence(
            interpretation, result, independent_units=result.independent_units,
            action=plan, source_cluster=cluster,
        )
        updated = state.apply(interpretation, result, source_cluster=cluster, action=plan)
        self._evidence_states[case_id] = updated
        self._logger.event(
            "outcome_interpreted",
            {
                "case_id": case_id,
                "result_id": result.result_id,
                "action_identifier": result.action_identifier,
                "interpreted_against_action": plan.identifier if plan is not None else None,
                "outcome_class": interpretation.outcome_class.value,
                "scope": interpretation.scope.value,
                "rule_identifier": interpretation.rule_identifier,
                "conditions_matched": interpretation.conditions_matched,
                "unmatched_conditions": list(interpretation.unmatched_conditions),
                "eliminates": sorted(interpretation.eliminates),
                "admissible": admission.admissible,
                "admitted_fields": list(admission.admitted_fields),
                "refused_fields": list(interpretation.refused_fields),
                "supporting_result_ids": list(interpretation.supporting_result_ids),
                "supporting_fields": list(interpretation.supporting_fields),
                "measured_premises": [asdict(item) for item in admission.measured_premises],
                "admitted_scope": admission.scope.value if admission.admissible else None,
                "statistically_usable": admission.statistically_usable,
                "remaining_candidates": sorted(updated.candidates),
                "source_cluster": cluster,
            },
            session_id=turn.session_id,
        )
        return updated, admission

    @staticmethod
    def _action_for_result(
        contrast: MechanismContrast,
        result: MeasurementResult,
        action: EvidenceAction | None,
    ) -> EvidenceAction | None:
        """Bind a result to the action that produced it, not to the primary plan.

        A bundle can contain actions with different time points or readouts.  The
        result's own action wins; the primary plan is only a fallback when the
        bundle holds no matching action, and a bundle-wide condition is never
        applied to every result in it.
        """

        for candidate in contrast.actions():
            if candidate.identifier == result.action_identifier:
                return candidate
        if action is not None and action.identifier == result.action_identifier:
            return action
        return None

    def _score_repair_result(
        self,
        case_id: str,
        turn: MAESTROTurn,
        action: EvidenceAction,
        result: MeasurementResult,
        admission: ValidatedEvidenceUpdate | None,
    ) -> None:
        """Score the executed edit, never the disappearance of a later plan failure."""

        ledger = self.repair_ledger(case_id)
        for record in turn.repair_records:
            if not record.adopted or record.gap_resolved is not None:
                continue
            if record.action_identifier != action.identifier or result.action_identifier != action.identifier:
                continue
            if turn.contrast is None or record.contrast_identifier != turn.contrast.identifier:
                continue
            if admission is None:
                continue
            qualified = admission.admissible and admission.statistically_usable
            if record.promised_fields and record.promised_fields != ("outcome_separation",):
                required_scope = EvidenceScope.INTERVENTION_IMPLEMENTATION
                resolved = qualified and all(
                    admission.admits(name, required_scope=required_scope)
                    for name in record.promised_fields
                )
            else:
                # A readout repair promises an actual discriminating observation;
                # adopting another plan or receiving any QC-passing assay is not enough.
                resolved = qualified and admission.interpretation.can_update_mechanism and bool(
                    admission.interpretation.eliminates
                )
            ledger.resolve_fingerprint(
                record.fingerprint, bool(resolved), result_id=admission.result_id, target=record
            )
            self._logger.event(
                "repair_gap_scored",
                {
                    "case_id": case_id,
                    "attempt": record.attempt,
                    "fingerprint": record.fingerprint,
                    "kind": record.kind.value,
                    "action_identifier": action.identifier,
                    "result_id": admission.result_id,
                    "promised_fields": list(record.promised_fields),
                    "admitted_fields": list(admission.admitted_fields),
                    "gap_resolved": bool(resolved),
                },
                session_id=turn.session_id,
            )

    def _score_prediction(
        self, turn: MAESTROTurn, action: EvidenceAction, result: MeasurementResult,
        admission: ValidatedEvidenceUpdate | None = None,
    ) -> None:
        """Calibrate with matched real readouts, independently of mechanism licensing.

        A surprising but qualified observation should score a prediction even
        when it has no registered mechanism interpretation. A prediction, an
        unmatched assay or a borrowed other-action prediction must never do so.
        """

        per_action = getattr(turn, "action_predictions", None)
        if per_action is not None:
            prediction = per_action.get(action.identifier)
        else:
            # Compatibility with archived single-action turns only.
            prediction = turn.prediction
        if (
            result.quality_passed is not True
            or result.evidence_kind is not EvidenceKind.REAL_MEASUREMENT
            or result.action_identifier != action.identifier
            or not isinstance(result.independent_units, int)
            or isinstance(result.independent_units, bool)
            or result.independent_units < 1
            or prediction is None
            or not prediction.applicable
            or not result.source_id
        ):
            return
        request = (getattr(turn, "action_prediction_requests", None) or {}).get(action.identifier)
        if request is not None:
            if result.plan_version is not None and request.plan_version != result.plan_version:
                return
            if not _answers(prediction, request) or not _states_action_condition(request, action):
                return
            if result.context_identifier != request.context.identifier:
                return
            predicted_time = request.intervention.time_hours
            if predicted_time is not None and (
                result.time_hours is None or not math.isfinite(result.time_hours)
                or abs(result.time_hours - predicted_time) > 1.0
            ):
                return
        expected_context = action.execution_context
        if expected_context is None and action.context_bound:
            expected_context = getattr(getattr(turn, "intent", None), "biological_context", None)
        if expected_context and result.context_identifier != expected_context:
            return
        if action.time_hours is not None and (
            result.time_hours is None or not math.isfinite(result.time_hours)
            or abs(result.time_hours - action.time_hours) > 1.0
        ):
            return
        if any(result.conditions.get(key) != value for key, value in action.expected_conditions.items()):
            return
        readout = action.prediction_readout
        if not readout or not prediction.state_change:
            return
        predicted = prediction.state_change.get(readout)
        if not isinstance(predicted, (int, float)) or isinstance(predicted, bool) or not math.isfinite(predicted):
            return
        raw = result.metrics.get(readout) if result.metrics else None
        realized = _to_float(raw)
        if realized is None or isinstance(raw, bool):
            return
        interval: tuple[float, float] | None = None
        descriptive: tuple[float, float] | None = None
        band = prediction.interval_for(readout)
        if band is not None and band.claims_coverage:
            interval = (band.low, band.high)
        elif band is not None and math.isfinite(band.low) and math.isfinite(band.high):
            descriptive = (band.low, band.high)
        else:
            uncertainty = prediction.uncertainty
            if isinstance(uncertainty, (int, float)) and math.isfinite(uncertainty) and uncertainty >= 0:
                # A point estimate plus/minus a scalar spread is descriptive; it is
                # recorded but never graded as a coverage-claiming interval.
                descriptive = (float(predicted) - float(uncertainty), float(predicted) + float(uncertainty))
        model_version = prediction.model_version or "unknown"
        clusters = getattr(self, "_source_clusters", None)
        cluster = clusters.cluster_of(result.source_id) if clusters is not None else result.source_id
        before = len(self._reliability.records)
        entry = ScoredPrediction(
            model_version=model_version,
            readout=readout,
            predicted_value=float(predicted),
            realized_value=realized,
            interval=interval,
            descriptive_interval=descriptive,
            context_identifier=result.context_identifier,
            request_id=prediction.request_id,
            action_identifier=action.identifier,
            source_cluster=cluster,
            result_id=result.result_id,
            time_hours=result.time_hours,
            condition_fingerprint=json.dumps(dict(result.conditions), sort_keys=True, separators=(",", ":")),
        )
        if self._case_store is not None and request is not None and result.result_id is not None:
            self._case_store.record_prediction_score(request.case_id, result.result_id, request.request_id,
                {"schema": "runtime_prediction_score_v1", "policy": dict(self._reliability.policy),
                 "entry": asdict(entry)}, conditions_matched=True)
        self._reliability.record(entry)
        if len(self._reliability.records) == before:
            self._logger.event(
                "prediction_reliability_duplicate_ignored",
                {"result_id": result.result_id, "source_cluster": cluster, "readout": readout},
                session_id=turn.session_id,
            )
            return
        summary = self._reliability.summarize(model_version, readout, result.context_identifier)
        self._logger.event(
            "prediction_reliability_scored",
            {
                "scope": summary.scope,
                "records": summary.records,
                "miss_rate": summary.miss_rate,
                "weight": summary.weight,
                "revoked": summary.revoked,
                "provisional": summary.provisional,
            },
            session_id=turn.session_id,
        )

    def _select_budgeted_actions(
        self,
        contrast: MechanismContrast,
        available_actions: Sequence[EvidenceAction],
        profile: FunctionalInterventionProfile,
        case: CaseSnapshot | None,
        budget: float | None,
        session_id: str,
        *,
        prediction: StatePrediction | None = None,
        prediction_request: PredictionRequest | None = None,
        action_predictions: Mapping[str, StatePrediction] | None = None,
        action_requests: Mapping[str, PredictionRequest] | None = None,
        case_id: str | None = None,
        prior_evidence: Sequence[MeasuredPremise] = (),
        user_state: UserStateContext | None = None,
    ):
        remaining = case.remaining_budget if case and case.remaining_budget is not None else budget
        if remaining is None:
            return None
        needed = {name for action in available_actions for name in action.required_premises}
        satisfied = {
            action.identifier for action in available_actions
            if action.supplies and set(action.supplies) <= needed
            and self._premise_action_satisfied(action, contrast, profile, prior_evidence)
        }
        if satisfied:
            self._logger.event(
                "satisfied_premise_actions_excluded", {"action_ids": sorted(satisfied)}, session_id=session_id,
            )
        available_actions = tuple(action for action in available_actions if action.identifier not in satisfied)
        try:
            priorities = self._prediction_action_priorities(
                prediction, prediction_request, available_actions,
                action_predictions=action_predictions, action_requests=action_requests,
            )
            discriminating = self._discriminating_selection(
                contrast, available_actions, profile, remaining, priorities, case_id, session_id, user_state=user_state,
            )
            path = "budgeted"
            if discriminating is not None and (self._selection_strategy == "discrimination"):
                # The forecast-driven choice replaces the coverage choice only when a caller asked
                # for it; the coverage path below is then not consulted.
                selection = discriminating.plan
                path = "discrimination"
            elif (self._selection_strategy == "expected_coverage"):
                path = "expected_coverage"
                # Magnitude priorities are logged, not used, on this path: letting them break ties
                # here failed its pre-registered keep rule on 2026-09-26 (tier A utility interval
                # included zero; tier B wrong eliminations rose by 0.044). A world model reaches
                # this path through outcome forecasts, where magnitude is only the last tie-break.
                expected = select_expected_coverage(
                    contrast.identifiers(), available_actions, profile, remaining,
                    source_groups=self._context_builder.source_groups(
                        tuple(ref for action in available_actions for ref in action.source_ids)),
                )
                if expected.status != "optimal":
                    self._logger.event(
                        "budget_selection_rejected",
                        {"error": expected.reason or expected.status},
                        session_id=session_id,
                    )
                    return expected.plan
                selection = expected.plan
                self._logger.event(
                    "expected_coverage_selection_completed",
                    {
                        "selected_action_ids": [action.identifier for action in selection.actions],
                        "coverage_probability": dict(sorted(expected.coverage_probability.items())),
                        "expected_coverage": expected.expected_coverage,
                        "assumptions": list(expected.assumptions),
                        "dependence_groups": dict(expected.dependence_groups),
                        "rejected": [
                            {"action": item.action_identifier, "reason": item.reason}
                            for item in expected.rejected
                        ],
                    },
                    session_id=session_id,
                )
            else:
                selection = self._controller.select_budgeted_evidence(
                    contrast.identifiers(), available_actions, profile, remaining,
                    action_priorities=priorities,
                )
        except ValueError as error:
            self._logger.event("budget_selection_rejected", {"error": str(error)}, session_id=session_id)
            return None
        if satisfied:
            selection = replace(selection, rejection_reasons={
                **selection.rejection_reasons,
                **{identifier: "premise_already_measured_under_same_conditions" for identifier in satisfied},
            })
        self._logger.event(
            "budget_selection_completed",
            {
                "selected_action_ids": [action.identifier for action in selection.actions],
                "covered": sorted(selection.covered),
                "uncovered": sorted(selection.uncovered),
                "total_cost": selection.total_cost,
                "waiting_for_prerequisites": selection.waiting_for_prerequisites,
                "prediction_action_priorities": priorities,
                # Which selector chose, and whether the priorities could move its choice: never on
                # the power-aware coverage path; as the last tie-break of the other two.
                "selection_path": path,
                "prediction_priorities_used": bool(priorities) and path != "expected_coverage",
            },
            session_id=session_id,
        )
        return selection

    def _premise_action_satisfied(
        self,
        action: EvidenceAction,
        contrast: MechanismContrast,
        profile: FunctionalInterventionProfile,
        evidence: Sequence[MeasuredPremise],
    ) -> bool:
        """An admitted, adequately replicated assay at the same coordinates need not be bought again."""

        if not evidence or profile.unmeasured(action.supplies):
            return False
        rules = self._interpretation_rules(contrast)
        for name in action.supplies:
            minimum = max([1] + [
                rule.minimum_independent_units for rule in rules
                if name in rule.matched_fields or any(name.startswith(prefix) for prefix in rule.required_prefixes)
                or any(requirement.field == name for requirement in rule.evidence_requirements)
            ] + [requirement.minimum_units for requirement in self._decision_engine.requirements
                 if name in requirement.satisfied_by])
            requirement = PremiseRequirement(
                name, action.quantity, entity=action.entity, site=action.site, units=action.units,
                context_identifier=action.execution_context or (profile.context_identifier if action.context_bound else None),
                time_hours=action.time_hours,
            )
            if not any(
                item.grant.source_action == action.identifier
                and isinstance(item.independent_units, int) and not isinstance(item.independent_units, bool)
                and item.independent_units >= minimum
                and scope_rank(item.scope) >= scope_rank(EvidenceScope.INTERVENTION_IMPLEMENTATION)
                and not requirement.unmet_reasons(item.grant)
                and all(item.conditions.get(key) == value for key, value in action.expected_conditions.items())
                for item in evidence
            ):
                return False
        return True

    def _interpretation_rules(self, contrast: MechanismContrast) -> tuple[OutcomeRule, ...]:
        """The rules that will read this contrast's results; acquisition values readings by them too."""

        return tuple(self._interpretation_table.rules) or default_rules_for(contrast)

    def _discriminating_selection(
        self,
        contrast: MechanismContrast,
        available_actions: Sequence[EvidenceAction],
        profile: FunctionalInterventionProfile,
        remaining: float,
        priorities: Mapping[str, float],
        case_id: str | None,
        session_id: str,
        *, user_state: UserStateContext | None = None,
    ) -> DiscriminationPlan | None:
        """Ask the forecaster how each action would read under each hypothesis, and choose by it.

        The plan is always logged; it drives the round only with ``discrimination_selection``.
        A decision-mode failure stops selection unless coverage fallback was explicitly requested.
        """

        forecaster = self._outcome_forecaster
        plans = self.__dict__.setdefault("_discrimination_plans", {})
        plans.pop(session_id, None)
        if forecaster is None:
            return None
        evidence = self._evidence_states.get(case_id) if case_id and hasattr(self, "_evidence_states") else None
        candidates = contrast.identifiers() & evidence.candidates if evidence is not None else contrast.identifiers()
        try:
            forecasts = dict(forecaster.forecast(contrast, available_actions, evidence, user_state=user_state)
                             if user_state is not None else forecaster.forecast(contrast, available_actions, evidence))
        except Exception as error:  # a model component failing must not stop the round
            self._logger.event(
                "outcome_forecast_failed",
                {"forecaster": getattr(forecaster, "name", type(forecaster).__name__), "error": type(error).__name__},
                session_id=session_id,
            )
            if self._selection_strategy == "discrimination" and self._forecast_failure_policy == "stop":
                from maestro.composition import BudgetedEvidencePlan
                plan = DiscriminationPlan(BudgetedEvidencePlan(actions=(), total_cost=0.0, covered=frozenset(),
                                          uncovered=frozenset(candidates), waiting_for_prerequisites=()),
                                          (), status="forecast_failed", reason=type(error).__name__)
                plans[session_id] = plan
                return plan
            self._logger.event("outcome_forecast_fallback",
                               {"policy": "coverage", "mode": "diagnostic" if self._selection_strategy != "discrimination" else "explicit_fallback"},
                               session_id=session_id)
            return None
        plan = select_discriminating_action(
            frozenset(candidates), available_actions, profile, remaining, forecasts,
            outcome_consequences(self._interpretation_rules(contrast)), action_priorities=priorities,
        )
        plans[session_id] = plan
        self._logger.event(
            "discrimination_selection_computed",
            {
                "forecaster": getattr(forecaster, "name", type(forecaster).__name__),
                "drives_selection": (self._selection_strategy == "discrimination"),
                "forecast_bases": {key: value.basis for key, value in sorted(forecasts.items())},
                **plan.payload(),
            },
            session_id=session_id,
        )
        return plan

    def _acquisition_stop_reason(self, session_id: str) -> str | None:
        """A named reason to defer when forecast-driven selection found nothing admissible."""

        plan = self.__dict__.get("_discrimination_plans", {}).pop(session_id, None)
        if plan is None or not (self._selection_strategy == "discrimination") or plan.status == "selected":
            return None
        return f"acquisition_{plan.status}: {plan.reason}"

    def _prediction_action_priorities(
        self,
        prediction: StatePrediction | None,
        request: PredictionRequest | None,
        actions: Sequence[EvidenceAction],
        *,
        action_predictions: Mapping[str, StatePrediction] | None = None,
        action_requests: Mapping[str, PredictionRequest] | None = None,
    ) -> Mapping[str, float]:
        """Rank actions by their *own* declared readout, never by a shared scalar.

        Each action is scored on the value the model returned for that action's
        declared readout.  A readout that is absent from the prediction
        contributes nothing, so an action cannot inherit priority from a readout
        it does not use, and swapping two readouts' predictions swaps the two
        actions' priorities.  The score is an exploratory magnitude for one
        declared readout, and the selector only consults it after coverage, cost,
        and set size are equal, so it can never buy an extra or costlier action.
        A prediction whose request states another exposure time or context than the
        action declares answers a different condition and ranks nothing.
        """

        per_action = dict(action_predictions or {})
        per_request = dict(action_requests or {})
        if not per_action and (prediction is None or not prediction.applicable or not prediction.state_change):
            return {}
        priorities: dict[str, float] = {}
        for action in actions:
            readout = action.prediction_readout
            if not readout or action.prediction_relevance <= 0:
                continue
            # With per-action queries an action is ranked only by the prediction
            # for its own condition; it never borrows another action's number.
            source = per_action.get(action.identifier) if per_action else prediction
            source_request = per_request.get(action.identifier) if per_action else request
            if source is None or not source.applicable or not source.state_change:
                continue
            if (
                source_request is None or not source.contract_valid
                or source.in_distribution is not True
                or not _answers(source, source_request)
                or readout not in source_request.readouts
                or not _states_action_condition(source_request, action)
            ):
                continue
            model_version = source.model_version or (source_request.model_version if source_request else "")
            context_identifier = source_request.context.identifier if source_request is not None else ""
            value = source.state_change.get(readout)
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                continue
            weight = self._reliability.weight(model_version, readout, context_identifier)
            if weight <= 0.0:
                continue
            priorities[action.identifier] = abs(float(value)) * action.prediction_relevance * weight
        return priorities

    def _record_reflection(self, reflection: ReflectionRecord, session_id: str) -> None:
        self._memory.remember(
            reflection.render(),
            kind=MemoryKind.EPISODIC,
            status=EpistemicStatus.DERIVED,
            provenance=f"post_observation_reflection:{reflection.case_id}:{reflection.result_id}",
            session_id=session_id,
            scope=MemoryScope(case_id=reflection.case_id),
            parent_ids=(reflection.result_id,),
        )
        self._logger.event(
            "post_observation_reflection",
            asdict(reflection),
            session_id=session_id,
        )

    @staticmethod
    def _profile_after_result(
        profile: FunctionalInterventionProfile,
        result: MeasurementResult,
        admission: ValidatedEvidenceUpdate | None,
    ) -> FunctionalInterventionProfile:
        """Update only admitted, adequately replicated fields and retain their source."""

        if admission is None or not admission.admissible or not admission.statistically_usable:
            return profile
        if admission.action_identifier != result.action_identifier:
            return profile
        if admission.scope not in (EvidenceScope.INTERVENTION_IMPLEMENTATION, EvidenceScope.MECHANISM_CONTRAST):
            return profile
        fields = dict(profile.functional_states)
        measured = dict(profile.measured_fields)
        protein = profile.protein_abundance
        for name in admission.admitted_fields:
            if name.startswith("functional:"):
                fields[name.removeprefix("functional:")] = MeasurementStatus.MEASURED
            elif name == "protein_abundance":
                protein = MeasurementStatus.MEASURED
            else:
                measured[name] = MeasurementStatus.MEASURED
        return replace(
            profile, functional_states=fields, measured_fields=measured, protein_abundance=protein,
            source_ids=tuple(dict.fromkeys(profile.source_ids + (result.source_id,))),
        )

    def _propose_llm_repair(
        self,
        context,
        contrast: MechanismContrast,
        check: ContrastCheck,
        available_actions: Sequence[EvidenceAction],
        intervention_profile: FunctionalInterventionProfile,
        prediction: StatePrediction | None,
        session_id: str,
        *,
        action_predictions: Mapping[str, StatePrediction] | None = None,
        world_model_briefing: str = "",
        action_topology: Mapping[str, object] | None = None,
        advisory_findings: Sequence[str] = (),
    ) -> AcceptedLLMRepair | None:
        if not self._enable_llm_repair or check.ready_for_mechanism_update:
            return None
        feedback_marks = self._planner_feedback_marks()
        try:
            draft = self._planner.propose_repair(
                context, contrast, check, available_actions, world_model_briefing=world_model_briefing,
                action_topology=action_topology, advisory_findings=advisory_findings,
            )
        except (LLMError, ValueError) as error:
            self._logger.event(
                "llm_repair_rejected",
                {"error": str(error)},
                session_id=session_id,
            )
            return None
        finally:
            self._log_planner_feedback(feedback_marks, "repair_planner", session_id)
        repaired = draft.apply(contrast, available_actions)
        if repaired is None:
            # Either no repair was offered or it named an unregistered action;
            # the ruled repair stays the baseline and the refusal is on record.
            self._logger.event(
                "llm_repair_not_applicable",
                {
                    "action_identifier": draft.action_identifier,
                    "reason": "no_action_proposed" if draft.action_identifier is None else "unregistered_action",
                },
                session_id=session_id,
            )
            return None
        repaired_prediction = (
            action_predictions.get(repaired.plan.identifier) if repaired.plan is not None else None
        ) if action_predictions is not None else (
            prediction if repaired.plan == contrast.plan else None
        )
        recheck = self._controller.check_contrast(
            repaired, intervention_profile, repaired_prediction, self._reliability
        )
        executable_premise_repair = self._is_executable_premise_repair(
            draft, repaired, check, recheck, intervention_profile
        )
        if not recheck.ready_for_mechanism_update and not executable_premise_repair:
            self._logger.event(
                "llm_repair_not_adopted",
                {
                    "remaining_reasons": [reason.value for reason in recheck.reasons],
                    "action_identifier": draft.action_identifier,
                },
                session_id=session_id,
            )
            return None
        self._logger.event(
            "llm_repair_adopted",
            {
                "action_identifier": draft.action_identifier,
                "mechanism_update_ready": recheck.ready_for_mechanism_update,
                "adoption_kind": "premise_measurement" if executable_premise_repair else "mechanism_ready",
                "remaining_reasons": [reason.value for reason in recheck.reasons],
            },
            session_id=session_id,
        )
        return AcceptedLLMRepair(draft, repaired, recheck)

    @staticmethod
    def _is_executable_premise_repair(
        draft: LLMRepairDraft,
        repaired: MechanismContrast,
        original: ContrastCheck,
        recheck: ContrastCheck,
        profile: FunctionalInterventionProfile,
    ) -> bool:
        """Allow a verified prerequisite measurement, never a premature mechanism update."""

        action = repaired.plan
        if draft.action_identifier is None or action is None:
            return False
        if not action.cost >= 0 or profile.unmeasured(action.prerequisites):
            return False
        missing_function = NonDiscriminabilityReason.MISSING_FUNCTIONAL_MEASUREMENT in original.reasons
        missing_other = NonDiscriminabilityReason.MISSING_PREREQUISITE in original.reasons
        is_functional = action.kind.value == "functional_measurement"
        is_prerequisite_measurement = action.kind.value == "protein_abundance_measurement"
        resolves_a_missing_premise = (missing_function and is_functional) or (missing_other and is_prerequisite_measurement)
        return resolves_a_missing_premise and recheck.executable

    # Planner feedback streams: attribute on the planner -> event kind in the run log.
    _PLANNER_FEEDBACK = (
        ("contract_violations", "planner_contract_violation"),
        ("critic_findings", "planner_critic_feedback"),
    )

    def _planner_feedback_marks(self) -> tuple[int, ...]:
        return tuple(len(getattr(self._planner, name, ())) for name, _ in self._PLANNER_FEEDBACK)

    def _review_plan(
        self,
        contrast: MechanismContrast,
        available_actions: Sequence[EvidenceAction],
        profile: FunctionalInterventionProfile,
        briefing_rows,
        topology: Mapping[str, object],
        session_id: str,
        *, evidence_summary: str = "",
    ) -> CritiqueOutcome:
        """Take one typed second opinion on this round's plan, if a decision model is configured.

        The review is advisory by construction: its findings are shown to the repair planner and
        its judgments are recorded, and neither can mark a premise measured or remove an
        explanation. A provider failure returns refusals, so the round continues unchanged.
        """

        critic = self._decision_critic
        if critic is None or contrast.plan is None:
            return CritiqueOutcome()
        outcome = critic.review_plan(
            contrast,
            available_actions,
            check=self._controller.check_contrast(contrast, profile, None, self._reliability),
            topology=topology,
            world_model_rows=[row.as_payload() for row in briefing_rows],
            evidence_summary=evidence_summary,
            context_identifier=profile.context_identifier,
            repeats=self._decision_repeats,
        )
        self._logger.event("typed_decision_review", outcome.payload(), session_id=session_id)
        return outcome

    def _log_planner_feedback(self, marks: tuple[int, ...], component: str, session_id: str) -> None:
        """Record every violation and critic finding the planner fed back to the model."""

        for (name, kind), before in zip(self._PLANNER_FEEDBACK, marks):
            entries = list(getattr(self._planner, name, ())[before:])
            if entries:
                self._logger.event(kind, {"component": component, "violations": entries}, session_id=session_id)

    def import_measurement(self, case_id: str, result: MeasurementResult) -> ResultImport:
        """Accept one planned real result; the next run retrieves it as measured evidence."""

        if self._case_store is None:
            raise RuntimeError("Measurement import requires a configured CaseStore.")
        imported = self._case_store.import_measurement(case_id, result)
        result = self._case_store.measurement(case_id, imported.result_id)
        if result.quality_passed:
            record = self._context_builder.record_result(result, case_id=case_id)
            self._logger.event(
                "measurement_imported",
                {"case_id": case_id, "result_id": imported.result_id, "evidence_id": record.identifier,
                 "new_fact": imported.created, "plan_version": result.plan_version},
                session_id=case_id,
            )
        elif imported.created:
            self._logger.event(
                "measurement_quality_failed",
                {"case_id": case_id, "result_id": imported.result_id},
                session_id=case_id,
            )
        self._reconcile(case_id, result)
        return imported

    def record_revealed_result(self, result: MeasurementResult, *, case_id: str | None = None) -> None:
        """Admit an authorized reveal and advance its plan when this runtime owns a case."""

        if case_id is not None and self._case_store is not None:
            self.import_measurement(case_id, result)
            return
        if not result.quality_passed:
            return
        record = self._context_builder.record_result(result)
        self._logger.event(
            "evaluation_result_authorized",
            {"result_id": result.result_id, "evidence_id": record.identifier, "kind": result.evidence_kind.value},
            session_id=result.result_id or "evaluation",
        )
        self._reconcile(None, result)

    def _reconcile(self, case_id: str | None, result: MeasurementResult) -> None:
        """Score a result against the prediction this controller made for its action.

        Reconciliation belongs to the arrival of a result, not to one code path
        that happens to have a turn in hand. Scoring only inside the case loop
        left every single-shot caller -- an imported measurement, an authorized
        reveal -- permanently unreconciled, so a ledger fed only by those callers
        stays empty and no readout can ever be revoked. A result whose action was
        never planned has no prediction to be scored against and is left alone;
        every other guard is `_score_prediction`'s, unchanged.
        """

        if case_id is not None and self._case_store is not None:
            version = self._case_store.result_plan_version(case_id, result.result_id)
            result = replace(result, plan_version=version)
            entry = self._reconciliation.get((case_id, version, result.action_identifier))
            if entry is None:
                receipt = self._case_store.prediction_for_result(case_id, result.result_id)
                if receipt is not None and receipt["payload"].get("schema") == "state_response_pair_v1":
                    try:
                        payload = receipt["payload"]
                        request = PredictionRequest.from_dict(payload["request"])
                        answer = StatePrediction.from_dict(payload["prediction"])
                        action = EvidenceAction(**payload["action"])
                        if (request.request_id != receipt["request_id"] or request.case_id != case_id
                                or request.plan_version != version or not _answers(answer, request)):
                            raise ValueError("prediction_receipt_identity_mismatch")
                        turn = SimpleNamespace(action_predictions={action.identifier: answer},
                            action_prediction_requests={action.identifier: request},
                            intent=SimpleNamespace(biological_context=payload["biological_context"]),
                            session_id=request.request_id)
                        entry = (turn, action)
                    except (KeyError, TypeError, ValueError) as error:
                        self._logger.event("prediction_reconciliation_refused", {"result_id": result.result_id,
                            "reason": str(error)}, session_id=case_id)
        else:
            entry = self._reconciliation_by_action.get(result.action_identifier)
        if entry is None:
            return
        turn, action = entry
        self._score_prediction(turn, action, result)

    def _run_dataset_tool(
        self,
        context,
        dataset_paths: Sequence[Path],
        session_id: str,
    ) -> tuple[ToolExecution, ...]:
        if self._tool_router is None or not dataset_paths:
            return ()
        try:
            executions = self._tool_router.select_and_execute_many(
                context, dataset_paths, plan_version=session_id
            )
        except ToolRuntimeError as error:
            self._logger.event(
                "dataset_tool_failed",
                {
                    "error": str(error),
                    "failure_trace": asdict(error.failure_trace) if error.failure_trace else None,
                    "receipt": asdict(error.receipt) if error.receipt else None,
                },
                session_id=session_id,
            )
            executions = error.completed_executions
        if not executions:
            self._logger.event("dataset_tool_not_selected", {}, session_id=session_id)
            return ()
        for execution in executions:
            self._logger.event("dataset_tool_executed", asdict(execution), session_id=session_id)
        return executions

    def _inspect_visuals(
        self, intent: TaskIntent, image_paths: Sequence[Path], session_id: str
    ) -> tuple[VisualInspection, ...]:
        if not image_paths:
            return ()
        inspections = self._visual_inspector.inspect(
            tuple(image_paths), question=intent.research_question
        )
        self._logger.event(
            "visual_assets_inspected",
            {"paths": [item.path for item in inspections], "results": [asdict(item) for item in inspections]},
            session_id=session_id,
        )
        return inspections

    @staticmethod
    def _clarification_response(
        intent: TaskIntent, inspections: tuple[VisualInspection, ...]
    ) -> str:
        required = "; ".join(intent.missing_information)
        visual_note = (
            " Visible observations of the supplied images were recorded, but they cannot establish "
            "a mechanism on their own."
            if inspections
            else ""
        )
        return (
            f"The task was interpreted as '{intent.task_type}'. Before a mechanism contrast can be "
            f"constructed, supply: {required}.{visual_note}"
        )

    @staticmethod
    def _decision_response(
        contrast: MechanismContrast,
        check: ContrastCheck,
        repair: RepairProposal | None,
        inspections: tuple[VisualInspection, ...],
        tool_executions: tuple[ToolExecution, ...],
    ) -> str:
        pair = " vs ".join(hypothesis.identifier for hypothesis in contrast.hypotheses)
        reasons = "; ".join(reason.value for reason in check.reasons) or "none"
        action = ", ".join(item.identifier for item in contrast.actions()) or "none"
        repair_name = repair.replacement_action.identifier if repair and repair.replacement_action else "none"
        visual_note = (
            f" Inspected {len(inspections)} visual asset(s); their observations only revise the next question."
            if inspections
            else ""
        )
        tool_note = (
            f" Ran dataset tool(s) {', '.join(item.tool_id for item in tool_executions)}; "
            "their output retains data sources and limitations."
            if tool_executions
            else ""
        )
        return (
            f"Constructed mechanism contrast {pair} with candidate evidence plan {action}. "
            f"Mechanism update currently possible: {check.ready_for_mechanism_update}; "
            f"check reasons: {reasons}. "
            f"Directed repair: {repair.kind.value if repair else 'not_required'} "
            f"(replacement action: {repair_name}). "
            f"Interpretation boundary: "
            f"{repair.interpretation_boundary if repair else 'The plan awaits a real result.'}"
            f"{visual_note}{tool_note}"
        )

    @staticmethod
    def _memory_summary(
        contrast: MechanismContrast, check: ContrastCheck, repair: RepairProposal | None
    ) -> str:
        return (
            f"Contrast {contrast.identifier}; hypotheses="
            f"{','.join(hypothesis.identifier for hypothesis in contrast.hypotheses)}; "
            f"ready={check.ready_for_mechanism_update}; repair={repair.kind.value if repair else 'not_required'}; "
            "This is a proposed plan, not measured evidence."
        )


def _answers(prediction: StatePrediction, request: PredictionRequest) -> bool:
    """Whether a prediction is the serving model's answer to exactly this request."""

    return not prediction_request_errors(prediction, request)


def _states_action_condition(request: PredictionRequest, action: EvidenceAction) -> bool:
    """Whether a request states no exposure time or context that contradicts the action's own.

    A request that leaves time to its perturbation label states nothing to contradict; one that
    states 24 h cannot rank an action declared at 72 h, whatever it predicted.
    """

    stated = request.intervention.time_hours
    if action.time_hours is not None and stated is not None and abs(stated - action.time_hours) > 1.0:
        return False
    if action.execution_context is not None and request.context.identifier != action.execution_context:
        return False
    if action.expected_conditions:
        try:
            return request.intervention.for_action(action, request.context, request.readouts) == request.intervention
        except ValueError:
            return False
    return True


def _stronger_scope(
    current: EvidenceScope | None, incoming: EvidenceScope
) -> EvidenceScope:
    """Keep the strongest admission a field has earned across observations."""

    if current is None or scope_rank(incoming) > scope_rank(current):
        return incoming
    return current


def _to_float(value: object) -> float | None:
    """Parse a declared metric without turning an unparsable value into zero."""

    if isinstance(value, (int, float)) and math.isfinite(value):
        return float(value)
    if isinstance(value, str):
        try:
            parsed = float(value.strip())
        except ValueError:
            return None
        return parsed if math.isfinite(parsed) else None
    return None
