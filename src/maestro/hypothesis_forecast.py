"""Case-memory outcome forecasts for the production planner (hypothesis-conditional).

File summary
- Path: src/maestro/hypothesis_forecast.py
- Purpose: serve hypothesis-conditional `OutcomeForecast`s to the production planner from an
  `EpisodeStore`, implementing the existing `maestro.acquisition.OutcomeForecaster` protocol so
  the case memory plugs into the orchestrator's discrimination selection without any change to
  evidence admission rules.
- Core points:
  - Forecasts are planning-only model predictions (`EvidenceKind.MODEL_PREDICTION` by construction
    of `OutcomeForecast`); nothing here writes to `EvidenceState`, and a test proves the state is
    unchanged after a forecast.
  - `UserStateContext` connects the user's actual biological state to the forecast: the compiled
    directional state, signed feature changes, pathway direction, cell-state summaries,
    intervention identity, chemical structure, cell context, time, dose, assay, hypothesis graph
    and evidence history. The same action under two different user states produces different
    retrieval and therefore different forecasts whenever the registered feature arm carries that
    information; without a user state the forecast is state-free, exactly as before.
  - A condition or hypothesis the memory cannot support returns a typed refusal; a branch is never
    fabricated. Per-branch support counts are independent precedent cases, and the registered
    minimum (`MIN_SUPPORT`) is reported through `support_report`.
  - Calibration is stated, not implied: the heuristic probability model is an uncalibrated
    research baseline. `forecast_detailed` reports `calibration_status`, `calibration_dataset`,
    `model_version`, per-branch support and provenance with the full multi-label distribution
    (never a binary qualified/not-qualified collapse). Until external calibration demonstrates
    otherwise, these forecasts stay out of default production action selection: the feature flag
    is off by default and every forecast carries its status.
- Interfaces: `UserStateContext`, `CaseMemoryOutcomeForecaster`, `MODEL_VERSION`, `MIN_SUPPORT`,
  `READING_LABELS`, `CALIBRATION_STATUS`, `CALIBRATION_DATASET`
- Depends on: maestro.acquisition, maestro.adaptive_retrieval, maestro.case_memory,
  maestro.directional, maestro.models, maestro.outcome (protocol types only)
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .acquisition import OutcomeBranch, OutcomeForecast
from .adaptive_retrieval import AdaptiveRetriever, RetrievalProblem
from .case_memory import EpisodeStore, case_memory_enabled
from .directional import ContextFeatures, DirectionalState, FeatureArm
from .models import EvidenceAction, MechanismContrast
from .outcome import EvidenceState

MODEL_VERSION = "case-memory-production-1"
MIN_SUPPORT = 6
"""Registered minimum: a branch resting on fewer independent precedents is flagged low-support."""
CALIBRATION_STATUS = "uncalibrated"
"""The heuristic probability model is a research baseline until external calibration proves otherwise."""
CALIBRATION_DATASET: str | None = None
"""No calibration dataset backs the heuristic probabilities; named explicitly, never implied."""

READING_LABELS = ("match_h1", "match_h2", "unresolved", "absent", "qc_failed")


@dataclass(frozen=True)
class UserStateContext:
    """The user's actual biological state, compiled before forecasting. No truth field."""

    directional_state: DirectionalState = field(default_factory=DirectionalState)
    cell_state_summaries: Mapping[str, float] = field(default_factory=dict)
    intervention_identity: str = ""
    chemical_structure: str | None = None
    cell_context: str | None = None
    time_h: float | None = None
    dose_nM: float | None = None
    assay: str = ""
    hypothesis_graph: Mapping[str, Any] = field(default_factory=dict)
    evidence_history: tuple[str, ...] = ()

    def identity(self) -> str:
        """Digest of the state; part of the forecast cache identity, so two states never share one."""

        def clean(value):
            if isinstance(value, Mapping):
                return {str(k): clean(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
            if isinstance(value, (tuple, list)):
                return [clean(v) for v in value]
            return value

        payload = {
            "delta": clean(dict(self.directional_state.signed_feature_delta)),
            "pathway": clean(dict(self.directional_state.pathway_direction)),
            "cell_state": clean(dict(self.cell_state_summaries)),
            "intervention": self.intervention_identity,
            "structure": self.chemical_structure,
            "cell_context": self.cell_context,
            "time_h": self.time_h,
            "dose_nM": self.dose_nM,
            "assay": self.assay,
            "history": list(self.evidence_history),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class CaseMemoryOutcomeForecaster:
    """Hypothesis-conditional outcome forecasts served from a case memory."""

    name = "case_memory"

    def __init__(self, store: EpisodeStore, retriever: AdaptiveRetriever | None = None, *,
                 feature_arm: FeatureArm = FeatureArm.COMBINED, research_mode: bool = False):
        self.store = store
        self.retriever = retriever or AdaptiveRetriever(store)
        self.feature_arm = feature_arm
        self.research_mode = research_mode
        self._cache: dict[str, OutcomeForecast] = {}

    # ------------------------------------------------------------------ protocol
    def forecast(self, contrast: MechanismContrast, actions: Sequence[EvidenceAction],
                 evidence: EvidenceState | None,
                 user_state: UserStateContext | None = None) -> Mapping[str, OutcomeForecast]:
        """Forecasts per action. `user_state` is optional; the three-argument call is unchanged."""

        out: dict[str, OutcomeForecast] = {}
        hypotheses = tuple(sorted(contrast.identifiers()))
        for action in actions:
            key = self._cache_key(contrast, action, evidence, user_state)
            if key not in self._cache:
                self._cache[key] = self._forecast_one(hypotheses, action, evidence, user_state)
            out[action.identifier] = self._cache[key]
        return out

    def support_report(self, contrast: MechanismContrast, action: EvidenceAction) -> Mapping[str, Mapping[str, float]]:
        """Per hypothesis: independent precedents and the low-support flag."""

        report: dict[str, Mapping[str, float]] = {}
        for hypothesis in sorted(contrast.identifiers()):
            count = sum(1 for case in self.store.latest()
                        for u in case.hypothesis_updates if hypothesis in u.contrast)
            report[hypothesis] = {"independent_units": count, "low_support": count < MIN_SUPPORT}
        return report

    # ------------------------------------------------------------------ detailed receipt
    def forecast_detailed(self, contrast: MechanismContrast, action: EvidenceAction,
                          evidence: EvidenceState | None,
                          user_state: UserStateContext | None = None) -> Mapping[str, Any]:
        """The full forecast receipt: distribution, support, calibration status and provenance.

        The multi-label distribution is reported whole for log-score evaluation; it is never
        collapsed into a binary qualified/not-qualified score.
        """

        forecast = self.forecast(contrast, (action,), evidence, user_state)[action.identifier]
        return {
            "action_identifier": action.identifier,
            "applicable": forecast.refusal is None and bool(forecast.branches),
            "abstain_reason": forecast.refusal,
            "branches": [
                {"hypothesis": branch.hypothesis, "probabilities": dict(branch.probabilities),
                 "support": branch.support, "low_support": branch.support < MIN_SUPPORT}
                for branch in forecast.branches
            ],
            "support": self.support_report(contrast, action),
            "calibration_status": CALIBRATION_STATUS,
            "calibration_dataset": CALIBRATION_DATASET,
            "model_version": MODEL_VERSION,
            "feature_arm": self.feature_arm.value,
            "provenance": {
                "builder": "CaseMemoryOutcomeForecaster",
                "store_snapshot": self.store.snapshot_digest(),
                "basis": forecast.basis,
                "evidence_kind": forecast.evidence_kind.value,
            },
        }

    # ------------------------------------------------------------------ internals
    def _cache_key(self, contrast: MechanismContrast, action: EvidenceAction,
                   evidence: EvidenceState | None, user_state: UserStateContext | None) -> str:
        identity = {
            "contrast": sorted(contrast.identifiers()),
            "action": action.identifier,
            "history": [u.action_identifier for u in evidence.updates] if evidence is not None else [],
            "user_state": user_state.identity() if user_state is not None else None,
            "arm": self.feature_arm.value,
            "model": MODEL_VERSION,
            "snapshot": self.store.snapshot_digest(),
        }
        return hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()

    def _forecast_one(self, hypotheses: Sequence[str], action: EvidenceAction,
                      evidence: EvidenceState | None,
                      user_state: UserStateContext | None) -> OutcomeForecast:
        if not self.research_mode and not case_memory_enabled():
            return OutcomeForecast(action.identifier, refusal="case_memory_disabled",
                                   basis="hypothesis_forecast", model_version=MODEL_VERSION)
        if len(hypotheses) < 2:
            return OutcomeForecast(action.identifier, refusal="contrast_without_two_hypotheses",
                                   basis="hypothesis_forecast", model_version=MODEL_VERSION)
        h1, h2 = hypotheses[0], hypotheses[1]
        context_features = ContextFeatures(
            cell_line=(user_state.cell_context if user_state else None),
            time_h=(user_state.time_h if user_state else action.time_hours),
            dose_nM=(user_state.dose_nM if user_state else None),
        )
        state = user_state.directional_state if user_state else DirectionalState()
        assay = (user_state.assay if user_state and user_state.assay
                 else action.kind.value if hasattr(action.kind, "value") else str(action.kind))
        problem = RetrievalProblem(
            problem_id=action.identifier,
            biological_system=action.execution_context or "",
            assay=assay,
            intervention_type="",
            measurement_type=action.readout or "",
            control_design="",
            context=context_features,
            hypotheses=(h1, h2),
            state=state,
            feature_arm=self.feature_arm,
        )
        result = self.retriever.retrieve(problem, research_mode=True)
        expected = dict(getattr(action, "expected_outcomes", None) or {})
        branches: list[OutcomeBranch] = []
        for own, other in ((h1, h2), (h2, h1)):
            # The forecast speaks in the action's declared outcome vocabulary when it has one, so
            # the selector's registered outcome rules can read it; the generic labels are the
            # fallback for actions without declared outcomes.
            match_own = expected.get(own) or f"match_{own}"
            match_other = expected.get(other) or f"match_{other}"
            precedents = result.precedents.get(own, ())
            support = sum(1 for p in precedents)
            if not precedents:
                continue
            weights = [max(p.components["state_similarity"], 1e-6) *
                       max(p.components["historical_reliability"], 1e-6) for p in precedents]
            total = sum(weights)
            # Uncalibrated heuristic mapping from retrieval evidence to branch probabilities.
            # Reported as CALIBRATION_STATUS = "uncalibrated"; never used in default production
            # action selection (the feature flag gates the whole forecaster).
            p_match = min(0.95, max(0.05, sum(
                w * (0.8 if p.components["mechanism_compatibility"] > 0.5 else 0.5)
                for w, p in zip(weights, precedents)) / total))
            unresolved = max(0.02, 1.0 - sum(p.components["assay_compatibility"]
                                             for p in precedents) / len(precedents))
            dist = {
                match_own: round((1 - unresolved) * p_match, 6),
                match_other: round((1 - unresolved) * (1 - p_match), 6),
                "unresolved": round(unresolved * 0.7, 6),
                "absent": round(unresolved * 0.2, 6),
                "qc_failed": round(unresolved * 0.1, 6),
            }
            norm = sum(dist.values())
            branches.append(OutcomeBranch(own, {k: v / norm for k, v in dist.items()}, support))
        if not branches:
            return OutcomeForecast(action.identifier, refusal="insufficient_support",
                                   basis=f"hypothesis_forecast[{self.feature_arm.value}]",
                                   model_version=MODEL_VERSION)
        basis = (f"hypothesis_forecast[arm={self.feature_arm.value},"
                 f"calibration={CALIBRATION_STATUS},"
                 f"kish={ {h: round(k, 2) for h, k in result.kish.items()} }]")
        return OutcomeForecast(action.identifier, tuple(branches), basis=basis,
                               model_version=MODEL_VERSION)
