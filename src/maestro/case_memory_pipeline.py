"""The feature-flagged production call path from user data to a branching plan.

File summary
- Path: src/maestro/case_memory_pipeline.py
- Purpose: the real, gated call path
  `user data -> ProblemCompiler -> hypothesis graph -> AdaptiveRetriever ->
  CaseMemoryOutcomeForecaster -> decision-value action ranking -> branching interpretation plan`,
  with the registered activation gates, so the production orchestrator and the runtime tool share
  one implementation.
- Core points:
  - Default production behaviour is unchanged: with `MAESTRO_CASE_MEMORY_ENABLED` unset or false,
    `run_case_memory_path` returns a typed refusal (`case_memory_disabled`) before any retrieval.
  - The case-memory forecaster is used only when every gate holds: the forecast mode is supported,
    the minimum independent support is met, the forecast is not abstaining, the prediction is
    explicitly a model prediction, and the evidence state is byte-identical before and after the
    forecast (no mutation). Each failed gate is named.
  - The compiled user state (directional state, pathway direction, cell context, time, dose,
    assay, intervention identity) reaches the forecaster through `UserStateContext`, so the same
    action under two different user states can rank differently.
  - Everything the path returns is planning-only: rankings and branching plans are decision
    support, and only qualified real measurements may update evidence - through `case_update`.
- Interfaces: `CaseMemoryPathResult`, `PathGateFailure`, `run_case_memory_path`,
  `user_state_from_compiled`
- Depends on: maestro.{case_memory,problem_compiler,adaptive_retrieval,hypothesis_forecast,
  case_update,directional,hypothesis_graph}, maestro.models, maestro.outcome
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .adaptive_retrieval import AdaptiveRetriever, RetrievalProblem
from .case_memory import EpisodeStore, ScientificMeasurementStatus, case_memory_enabled
from .case_update import ActionRanking, branching_interpretation_plan, rank_actions_by_decision_value
from .case_memory import BranchingPlan, CandidateAction
from .directional import ContextFeatures, FeatureArm
from .hypothesis_forecast import (
    CALIBRATION_DATASET,
    CALIBRATION_STATUS,
    MIN_SUPPORT,
    MODEL_VERSION,
    CaseMemoryOutcomeForecaster,
    UserStateContext,
)
from .models import EvidenceAction, MechanismContrast
from .outcome import EvidenceState
from .problem_compiler import CompiledProblem

SUPPORTED_FORECAST_MODES = ("state", "hypothesis_conditional", "history_aware",
                            "hypothesis_conditional_history")


@dataclass(frozen=True)
class PathGateFailure:
    gate: str
    detail: str


@dataclass(frozen=True)
class CaseMemoryPathResult:
    """What the gated path produced, or the named gate that stopped it."""

    activated: bool
    gate_failures: tuple[PathGateFailure, ...]
    retrieval: Mapping[str, Any] = field(default_factory=dict)
    forecasts: Mapping[str, Any] = field(default_factory=dict)
    rankings: tuple[ActionRanking, ...] = ()
    branching_plans: tuple[BranchingPlan, ...] = ()
    calibration_status: str = CALIBRATION_STATUS
    calibration_dataset: str | None = CALIBRATION_DATASET
    model_version: str = ""
    refusal: str | None = None


def user_state_from_compiled(compiled: CompiledProblem) -> UserStateContext:
    """Bridge the compiler output into the forecaster's state context (no truth field)."""

    context = compiled.context
    cell_lines = context.get("cell_lines") or []
    graph = compiled.hypothesis_graph
    return UserStateContext(
        directional_state=compiled.directional_state,
        cell_state_summaries=dict(compiled.directional_state.cell_state_proportion),
        intervention_identity=str(context.get("intervention") or ""),
        cell_context=cell_lines[0] if cell_lines else None,
        time_h=compiled.time_h,
        dose_nM=compiled.dose_nM,
        assay=compiled.assay or "",
        hypothesis_graph={"hypotheses": dict(graph.hypotheses), "advisory": graph.advisory} if graph else {},
        evidence_history=(),
    )


def _gates(store: EpisodeStore, forecast_mode: str, support: Mapping[str, Mapping[str, float]],
           abstaining: bool) -> tuple[PathGateFailure, ...]:
    """The registered activation gates; every failure is named."""

    failures: list[PathGateFailure] = []
    if not case_memory_enabled():
        failures.append(PathGateFailure("feature_flag", "MAESTRO_CASE_MEMORY_ENABLED is unset or false"))
    if forecast_mode not in SUPPORTED_FORECAST_MODES:
        failures.append(PathGateFailure("forecast_mode", f"unsupported:{forecast_mode}"))
    if not len(store):
        failures.append(PathGateFailure("support", "the episode store is empty"))
    low = [h for h, s in support.items() if s.get("low_support")]
    if low:
        failures.append(PathGateFailure("support", f"below minimum independent support: {sorted(low)}"))
    if abstaining:
        failures.append(PathGateFailure("abstention", "the forecast is abstaining"))
    return tuple(failures)


def run_case_memory_path(
    compiled: CompiledProblem,
    store: EpisodeStore,
    contrast: MechanismContrast,
    actions: Sequence[EvidenceAction],
    evidence: EvidenceState | None,
    *,
    candidate_actions: Sequence[CandidateAction] = (),
    consequences: Mapping[str, frozenset] | None = None,
    feature_arm: FeatureArm = FeatureArm.COMBINED,
    forecast_mode: str = "hypothesis_conditional",
    research_mode: bool = False,
) -> CaseMemoryPathResult:
    """Run the gated path. Research evaluation passes `research_mode=True` explicitly.

    The evidence state is compared before and after forecasting; any mutation is itself a gate
    failure (`evidence_mutation`), so a forecast can never smuggle an update into the state.
    """

    if not research_mode and not case_memory_enabled():
        return CaseMemoryPathResult(False, (PathGateFailure(
            "feature_flag", "MAESTRO_CASE_MEMORY_ENABLED is unset or false"),),
            refusal="case_memory_disabled")
    if not compiled.usable:
        fatal = [d for d in compiled.diagnostics if d.severity == "fatal"]
        return CaseMemoryPathResult(False, tuple(PathGateFailure("compiler", d.code) for d in fatal),
                                    refusal="compiled_problem_not_usable")
    user_state = user_state_from_compiled(compiled)
    forecaster = CaseMemoryOutcomeForecaster(store, feature_arm=feature_arm, research_mode=True)
    support = forecaster.support_report(contrast, actions[0]) if actions else {}
    state_before = repr(evidence) if evidence is not None else None
    detailed = {a.identifier: forecaster.forecast_detailed(contrast, a, evidence, user_state)
                for a in actions}
    state_after = repr(evidence) if evidence is not None else None
    abstaining = all(d["abstain_reason"] is not None or not d["applicable"] for d in detailed.values())
    failures = list(_gates(store, forecast_mode, support, abstaining))
    if research_mode and not case_memory_enabled():
        failures = [f for f in failures if f.gate != "feature_flag"]
    if state_before != state_after:
        failures.append(PathGateFailure("evidence_mutation", "the forecast mutated the evidence state"))
    for d in detailed.values():
        if d["provenance"].get("evidence_kind") != "model_prediction":
            failures.append(PathGateFailure("evidence_kind", "forecast is not marked model_prediction"))
    retrieval_payload: dict[str, Any] = {}
    if actions:
        problem = RetrievalProblem(
            problem_id=compiled.problem_id, biological_system="",
            assay=compiled.assay or "", intervention_type="", measurement_type="",
            control_design=compiled.control_design or "",
            context=ContextFeatures(cell_line=user_state.cell_context, time_h=user_state.time_h,
                                    dose_nM=user_state.dose_nM),
            hypotheses=tuple(sorted(contrast.identifiers())),
            state=user_state.directional_state, feature_arm=feature_arm)
        retrieval = forecaster.retriever.retrieve(problem, research_mode=True)
        retrieval_payload = {
            "stage1": {"eligible": list(retrieval.stage1.eligible),
                       "excluded": dict(retrieval.stage1.excluded)},
            "kish": dict(retrieval.kish), "usable": dict(retrieval.usable),
        }
    rankings: tuple[ActionRanking, ...] = ()
    plans: tuple[BranchingPlan, ...] = ()
    if not failures and candidate_actions and consequences is not None:
        forecasts = {a.identifier: forecaster.forecast(contrast, (a,), evidence, user_state)[a.identifier]
                     for a in actions}
        rankings = rank_actions_by_decision_value(
            tuple(sorted(contrast.identifiers())), candidate_actions, forecasts, consequences)
        plans = tuple(branching_interpretation_plan(a, sorted(consequences))
                      for a in candidate_actions)
    return CaseMemoryPathResult(
        activated=not failures, gate_failures=tuple(failures), retrieval=retrieval_payload,
        forecasts=detailed, rankings=rankings, branching_plans=plans,
        model_version=MODEL_VERSION,
        refusal=None if not failures else "gates_failed:" + ",".join(f.gate for f in failures))
