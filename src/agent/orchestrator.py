"""Single-controller loop that keeps planning, observations, and evidence distinct.

File summary
- Path: src/agent/orchestrator.py
- Purpose: Drive one bounded MAESTRO cycle and the multi-round case loop.
- Core points:
  - `run` executes one bounded cycle; `run_case_loop` stops before any unsupplied measurement.
  - A real measurement never becomes a model prediction or a fabricated biological result.
  - Adopted repairs are scored against later real results via `gap_resolved`.
  - Each round's virtual-cell answers are shown to the LLM repair planner as a labelled
    planning-only briefing, and an identical query is answered once per run, not per round.
  - When a typed decision model is configured, each round also gets one calibrated second
    opinion; its findings reach the repair planner as advice and its judgments are recorded,
    but a judgment can never satisfy a premise or eliminate an explanation.
  - Each round analyses the menu as a dependency graph (`maestro.topology`): what can run
    now, how many supplier steps each action is away, and which premises no registered
    action supplies. The analysis is logged, kept on the turn, and shown to the repair planner.
- Interfaces: `MAESTROOrchestrator`, `run`, `run_case_loop`, `import_measurement`, `MAESTROTurn`, `MAESTROCaseLoop`
- Depends on: maestro.contrast, maestro.decision, maestro.outcome, maestro.repair, maestro.reliability, maestro.provenance, agent.audit, agent.cases, agent.configuration, agent.context, agent.knowledge, agent.llm, agent.memory, agent.planner, agent.reflection, agent.tool_runtime, agent.vision, agent.world_model_briefing, virtual_cell
"""
from __future__ import annotations

import uuid
import math
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Callable, Mapping, Sequence

from maestro.contrast import MAESTROAgent
from maestro.acquisition import select_expected_coverage
from maestro.decision import DecisionEngine, DevelopmentDecision
from maestro.handoff import (
    ComparabilityStatus,
    DecisionLayer,
    EvidenceLayer,
    ExecutionLayer,
    RoundRecord,
    WorldModelLayer,
    rejected_from_selection,
    review_run,
    write_round,
)
from maestro.outcome import (
    EvidenceState,
    InterpretationTable,
    MeasuredPremise,
    ValidatedEvidenceUpdate,
    admit_evidence,
    default_rules_for,
    scope_rank,
)
from maestro.provenance import SourceClusterIndex
from maestro.topology import ActionTopology
from maestro.reliability import PredictionReliabilityLedger
from maestro.repair import RepairController, RepairLedger, RepairRecord
from .audit import RunLogger
from .cases import CaseSnapshot, CaseStore, MeasurementResult, ResultImport
from .configuration import MAESTROSettings
from .decision_critic import CritiqueOutcome, TypedDecisionCritic
from .context import ContextBuilder, TaskIntent, TaskInterpreter
from .knowledge import EvidenceLedger
from .llm import DeepSeekChatClient, LLMError
from .memory import EpistemicStatus, MemoryKind, MemoryScope, MemoryStore
from maestro.models import (
    ContrastCheck,
    DecisionStatus,
    DevelopmentAction,
    EvidenceAction,
    EvidenceActionKind,
    EvidenceKind,
    EvidenceScope,
    FunctionalInterventionProfile,
    MechanismContrast,
    MechanismHypothesis,
    MeasurementStatus,
    NonDiscriminabilityReason,
    RepairKind,
    RepairProposal,
)
from .planner import LLMRepairDraft, MechanismContrastPlanner
from .reflection import ReflectionRecord, reflect_on_result
from .tool_runtime import ToolExecution, ToolRouter, ToolRuntimeError
from .typesafe import TypeSafeJevClient, TypeSafeSettings
from .vision import VisualInspection, VisualInspector
from .world_model_briefing import (
    WorldModelRow,
    render_world_model_briefing,
    summarize_world_model,
    world_model_rows,
)
from virtual_cell.interface import safe_predict
from virtual_cell import (
    PredictionCache,
    PredictionRequest,
    QueryAssessment,
    StateAdapterConfig,
    StateCapabilityAdapter,
    StatePrediction,
    VirtualCellQueryTemplate,
    VirtualCellWorldModel,
)


@dataclass(frozen=True)
class AcceptedLLMRepair:
    draft: LLMRepairDraft
    contrast: MechanismContrast
    check: ContrastCheck


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

    # A partially constructed controller (tests build one without __init__) must
    # still answer "is prediction reuse enabled?" rather than raise.
    _prediction_cache: PredictionCache | None = None
    _max_parallel_predictions: int = 1
    _decision_critic: TypedDecisionCritic | None = None
    _runtime_client: object | None = None

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
    ):
        if (
            isinstance(max_parallel_predictions, bool)
            or not isinstance(max_parallel_predictions, int)
            or max_parallel_predictions < 1
        ):
            raise ValueError("max_parallel_predictions must be a positive integer.")
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
        self._virtual_cell = virtual_cell
        self._repair_controller = repair_controller or RepairController(
            self._controller, max_attempts=max_repair_attempts
        )
        self._interpretation_table = interpretation_table or InterpretationTable()
        self._decision_engine = decision_engine or DecisionEngine()
        self._reliability = reliability or PredictionReliabilityLedger()
        self._source_clusters = source_clusters or SourceClusterIndex()
        self._repair_ledgers: dict[str, RepairLedger] = {}
        self._evidence_states: dict[str, EvidenceState] = {}
        self._round_records: dict[str, RoundRecord] = {}
        self._power_aware_selection = power_aware_selection
        # A multi-round case re-queries every action every round with unchanged
        # model inputs. Reuse is keyed on those inputs only; see virtual_cell.cache.
        self._prediction_cache = (
            prediction_cache if prediction_cache is not None else PredictionCache() if reuse_predictions else None
        )
        # Independent per-action queries may run concurrently, but only when the
        # caller declares the backend safe to call from several threads.
        self._max_parallel_predictions = max_parallel_predictions
        self._decision_critic = decision_critic

    @property
    def prediction_cache(self) -> PredictionCache | None:
        return self._prediction_cache

    @property
    def decision_critic(self) -> TypedDecisionCritic | None:
        return self._decision_critic

    def repair_ledger(self, case_id: str) -> RepairLedger:
        return self._repair_ledgers.setdefault(case_id, RepairLedger())

    def evidence_state(self, case_id: str) -> EvidenceState | None:
        return self._evidence_states.get(case_id)

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
    ) -> "MAESTROOrchestrator":
        """Create a controller; evaluations may supply an isolated state directory.

        ``client`` may be any structured completer, including the reviewed
        non-LLM template. ``virtual_cell`` replaces the default State adapter
        with any backend that satisfies the world-model protocol.
        """

        settings = MAESTROSettings.from_workspace(workspace)
        # The typed decision model is optional: with no TypeSafe block in the environment or
        # .env the critic is simply absent, and the loop behaves exactly as before.
        typesafe = TypeSafeSettings.from_workspace(workspace) if enable_decision_critic else None
        runtime_client = client or DeepSeekChatClient(settings)
        runtime_directory = state_directory or settings.log_directory
        logger = RunLogger(runtime_directory)
        memory = MemoryStore(runtime_directory / "memory.sqlite")
        evidence = EvidenceLedger(runtime_directory / "evidence.sqlite")
        knowledge_package = workspace / "data" / "knowledge" / "biological_constraints.json"
        if knowledge_package.is_file():
            evidence.load_knowledge_package(knowledge_package)
        controller = cls(
            interpreter=TaskInterpreter(runtime_client),
            context_builder=ContextBuilder(evidence, memory),
            planner=MechanismContrastPlanner(runtime_client),
            visual_inspector=VisualInspector(runtime_client, settings.vision_model),
            memory=memory,
            logger=logger,
            tool_router=ToolRouter(runtime_client, workspace / "tools"),
            power_aware_selection=True,
            case_store=None if disable_case_store else case_store if case_store is not None else CaseStore(runtime_directory / "cases.sqlite"),
            enable_llm_repair=True,
            virtual_cell=(
                virtual_cell
                if virtual_cell is not None
                else StateCapabilityAdapter(StateAdapterConfig.from_workspace(workspace)) if enable_virtual_cell else None
            ),
            interpretation_table=interpretation_table,
            decision_engine=decision_engine,
            source_clusters=source_clusters,
            max_repair_attempts=max_repair_attempts,
            max_parallel_predictions=max_parallel_predictions,
            decision_critic=(
                TypedDecisionCritic(TypeSafeJevClient(typesafe)) if typesafe is not None else None
            ),
        )
        # Keep the client the components share, so a run can report what it was charged. The
        # per-response usage is otherwise parsed and dropped at every call site.
        controller._runtime_client = runtime_client
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
        session_id: str | None = None,
    ) -> MAESTROTurn:
        """Execute one bounded cycle without fabricating a biological result or tool capability."""

        session_id = session_id or str(uuid.uuid4())
        case_id = case_id or session_id
        case = self._case_store.open_case(case_id, budget=budget) if self._case_store else None
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
        context = self._context_builder.build(
            intent,
            memory_scope=MemoryScope(case_id=case_id, task_type=intent.task_type, biological_context=intent.biological_context),
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
        world = self._query_world_model(
            contrast, intent, case, case_id, session_id, available_actions,
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
        )
        selection = self._select_budgeted_actions(
            contrast, available_actions, intervention_profile, case, budget, session_id,
            prediction=prediction, prediction_request=effective_request,
            action_predictions=action_predictions, action_requests=action_requests,
        )
        if selection is not None and selection.actions and not selection.uncovered:
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
        if self._power_aware_selection and selection is not None:
            allowed = {action.identifier for action in selection.actions}
            execution_actions = tuple(action for action in execution_actions if action.identifier in allowed)
        if self._case_store:
            case = self._case_store.record_plan(
                case_id,
                execution_actions,
                ready_to_measure=bool(execution_actions),
                context_identifier=intervention_profile.context_identifier,
                stop_reason=None if repair is None or repair.replacement_action else repair.interpretation_boundary,
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
            response=self._decision_response(contrast, check, repair, visual_inspections, tool_executions)
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
            decision_review=review.payload() if review.model_version else {},
        )
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

        check = self._controller.check_contrast(contrast, profile, prediction)
        ledger = self.repair_ledger(case_id)
        rule_outcome = self._repair_controller.run(
            contrast,
            check,
            available_actions,
            profile,
            prediction,
            ledger=ledger,
            action_predictions=action_predictions,
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
                    action_predictions=action_predictions,
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
        path = self._round_path(turn.session_id, suffix="plan")
        try:
            digest = write_round(path, record)
        except ValueError as error:
            self._logger.event(
                "round_record_rejected", {"session_id": turn.session_id, "reason": str(error)}, session_id=turn.session_id
            )
            return None
        self._logger.event(
            "round_record_written",
            {"path": str(path), "sha256": digest, "layers": 4},
            session_id=turn.session_id,
        )
        self._round_records[turn.session_id] = record
        return record

    def _round_path(self, session_id: str, *, suffix: str) -> Path:
        return self._logger.root / "rounds" / f"{session_id}.{suffix}.json"

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

        The plan record is read back from where it was written and re-issued with the
        execution layer filled, so the two files together are the round: what was
        planned, and what the measurement did to the judgement.
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
        path = self._round_path(turn.session_id, suffix="result")
        try:
            digest = write_round(path, record)
        except ValueError as error:
            self._logger.event(
                "round_record_rejected", {"session_id": turn.session_id, "reason": str(error)}, session_id=turn.session_id
            )
            return None
        self._round_records[turn.session_id] = record
        self._logger.event(
            "round_result_recorded",
            {
                "path": str(path),
                "sha256": digest,
                "result_id": result_id,
                "contradiction_flag": record.execution.contradiction_flag,
            },
            session_id=turn.session_id,
        )
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
                stop_reason = "no_executable_action"
                break
            awaiting = False
            for action in turn.selected_actions:
                result = result_provider(action, turn)
                if result is None:
                    awaiting = True
                    continue
                if result.action_identifier != action.identifier:
                    raise ValueError("Result action does not match the selected action being executed.")
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
                self._score_prediction(turn, action, result, admission)
                self._write_result_round(
                    turn, action, result, admission, state, result_id=imported.result_id
                )
                profile = self._profile_after_result(profile, result, admission)
                if not result.quality_passed:
                    stop_reason = "result_quality_failed"
                    result_quality_failed = True
                    awaiting = True
                    break
            snapshot = self._case_store.snapshot(case_id)
            if state is not None and turn.contrast is not None:
                decision = self._decide(
                    case_id, state, turn.contrast, admitted_scopes, observed_units, evidence_ids, turn, snapshot
                )
                if decision is not None and decision.is_terminal:
                    # A terminal decision ends the case in the same transition that produced it.
                    self._case_store.record_decision(case_id, status=decision.status.value)
                    if not result_quality_failed:
                        stop_reason = f"decision:{decision.status.value}"
                    break
            if awaiting:
                stop_reason = "awaiting_result" if stop_reason == "max_rounds_reached" else stop_reason
                break
            if snapshot.remaining_budget is not None and snapshot.remaining_budget <= 0:
                stop_reason = "budget_exhausted"
                break
        records = tuple(
            self._round_records[turn.session_id] for turn in turns if turn.session_id in self._round_records
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
        updated = state.apply(interpretation, result, source_cluster=cluster)
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
            if not _answers(prediction, request):
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
        self._reliability.record_pair(
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

    def _query_world_model(
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

        action_requests = self._build_action_prediction_requests(
            template, intent, contrast, case_id, case, session_id, available_actions
        )
        if action_requests:
            answered = self._predict_many(action_requests, session_id)
            assessments = {key: pair[0] for key, pair in answered.items() if pair[0] is not None}
            predictions = {key: pair[1] for key, pair in answered.items() if pair[1] is not None}
            plan = contrast.plan.identifier if contrast.plan is not None else None
            return WorldModelQueries(
                action_requests, assessments, predictions, None,
                assessments.get(plan) if plan else None, predictions.get(plan) if plan else None,
            )
        request = prediction_request or self._build_prediction_request(
            template, intent, contrast, case_id, case, session_id
        )
        assessment, prediction = self._predict_virtual_cell(request, session_id)
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

    def _predict_many(
        self, requests: Mapping[str, PredictionRequest], session_id: str
    ) -> dict[str, tuple[QueryAssessment | None, StatePrediction | None]]:
        """Answer independent requests, dispatching distinct misses concurrently when allowed.

        Inference runs at most once per distinct query in a round: a duplicate
        is answered from the reuse store after its twin is recorded. Recording
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
        computed: dict[str, tuple[QueryAssessment, StatePrediction]] = {}
        if self._virtual_cell is not None and self._max_parallel_predictions > 1 and len(pending) > 1:
            distinct: dict[str, str] = {}
            for identifier, request in pending.items():
                key = PredictionCache.key_for(request, self._backend_name()) or f"uncacheable:{identifier}"
                distinct.setdefault(key, identifier)
            workers = min(self._max_parallel_predictions, len(distinct))
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="virtual-cell") as pool:
                futures = {
                    identifier: pool.submit(safe_predict, self._virtual_cell, pending[identifier])
                    for identifier in distinct.values()
                }
            computed = {identifier: future.result() for identifier, future in futures.items()}
        for identifier, request in pending.items():
            if identifier in computed:
                assessment, prediction = computed[identifier]
                self._record_prediction(request, assessment, prediction, session_id)
                answered[identifier] = (assessment, prediction)
            else:
                answered[identifier] = self._predict_virtual_cell(request, session_id)
        return {identifier: answered[identifier] for identifier in requests}

    def _backend_name(self) -> str:
        return getattr(self._virtual_cell, "name", None) or type(self._virtual_cell).__name__

    def _predict_virtual_cell(
        self, request: PredictionRequest | None, session_id: str
    ) -> tuple[QueryAssessment | None, StatePrediction | None]:
        if request is None or self._virtual_cell is None:
            return None, None
        reused = self._reused_prediction(request, session_id)
        if reused is not None:
            return reused
        assessment, prediction = safe_predict(self._virtual_cell, request)
        self._record_prediction(request, assessment, prediction, session_id)
        return assessment, prediction

    def _reused_prediction(
        self, request: PredictionRequest, session_id: str
    ) -> tuple[QueryAssessment, StatePrediction] | None:
        """An earlier answer to the identical query, rebound to this request and logged."""

        if self._prediction_cache is None or self._virtual_cell is None:
            return None
        backend = self._backend_name()
        cached = self._prediction_cache.lookup(request, backend)
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
                "cache": self._prediction_cache.stats(),
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

        if self._prediction_cache is not None:
            self._prediction_cache.store(request, self._backend_name(), assessment, prediction)
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
    ) -> dict[str, PredictionRequest]:
        """One request per registered action that names its own exact condition."""

        if template is None or not template.action_interventions:
            return {}
        registered = {action.identifier for action in available_actions}
        return {
            action_identifier: template.build(
                request_id=f"{session_id}.{action_identifier}",
                case_id=case_id,
                contrast_id=contrast.identifier,
                plan_version=(case.plan_version + 1) if case else 1,
                intended_targets=intent.target_or_targets,
                intervention_identifier=label,
            )
            for action_identifier, label in template.action_interventions.items()
            if action_identifier in registered
        }

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
    ):
        remaining = case.remaining_budget if case and case.remaining_budget is not None else budget
        if remaining is None:
            return None
        try:
            priorities = self._prediction_action_priorities(
                prediction, prediction_request, available_actions,
                action_predictions=action_predictions, action_requests=action_requests,
            )
            if self._power_aware_selection:
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
        self._logger.event(
            "budget_selection_completed",
            {
                "selected_action_ids": [action.identifier for action in selection.actions],
                "covered": sorted(selection.covered),
                "uncovered": sorted(selection.uncovered),
                "total_cost": selection.total_cost,
                "waiting_for_prerequisites": selection.waiting_for_prerequisites,
                "prediction_action_priorities": priorities,
            },
            session_id=session_id,
        )
        return selection

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
        recheck = self._controller.check_contrast(repaired, intervention_profile, repaired_prediction)
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
            check=self._controller.check_contrast(contrast, profile),
            topology=topology,
            world_model_rows=[row.as_payload() for row in briefing_rows],
            context_identifier=profile.context_identifier,
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
        if imported.created and result.quality_passed:
            record = self._context_builder.record_result(result)
            self._logger.event(
                "measurement_imported",
                {"case_id": case_id, "result_id": imported.result_id, "evidence_id": record.identifier},
                session_id=case_id,
            )
        elif imported.created:
            self._logger.event(
                "measurement_quality_failed",
                {"case_id": case_id, "result_id": imported.result_id},
                session_id=case_id,
            )
        return imported

    def record_revealed_result(self, result: MeasurementResult) -> None:
        """Expose an evaluator-authorized result without changing the evaluator CaseStore."""

        if not result.quality_passed:
            return
        record = self._context_builder.record_result(result)
        self._logger.event(
            "evaluation_result_authorized",
            {"result_id": result.result_id, "evidence_id": record.identifier, "kind": result.evidence_kind.value},
            session_id=result.result_id or "evaluation",
        )

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

    return prediction.request_id == request.request_id and prediction.model_version == request.model_version


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
