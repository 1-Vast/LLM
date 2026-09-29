"""Adaptive, adaptation-aware retrieval of precedent episodes (production).

File summary
- Path: src/maestro/adaptive_retrieval.py
- Purpose: retrieve precedent scientific episodes for one open problem in four stages and report,
  for every case, why it was retrieved and what must change before it is reused. Directional state
  features are a first-class stage: retrieval on the scalar arm is a different, registered arm, not
  the default.
- Core points:
  - Stage 1, hard compatibility: biological system, assay, time scale, dose scale, control design,
    measurement type, unit compatibility, quality status and intervention type; every exclusion
    carries a named reason.
  - Stage 2, mechanism and hypothesis graph: a precedent supports the hypothesis its reading
    licensed; the mechanism compatibility term is the share of the problem's neighbourhood
    evidence mass behind each hypothesis.
  - Stage 3, directional state similarity: cosine over the registered feature arm
    (`directional.FeatureArm`) of the problem against each precedent's directional state. The
    scalar arm keeps magnitude only, so the arms differ exactly by the directional information.
  - Stage 4, adaptation-aware rerank: the nine-term case score
    (state similarity + mechanism + assay + temporal compatibility + evidence quality +
    historical reliability - adaptation cost - domain shift - measurement mismatch), each term in
    [0, 1], with the full component report per case. The score is never a black-box number.
  - Retrieval is read-only over the store and carries the feature flag: with
    `case_memory_enabled() == False` `retrieve` raises unless `research_mode=True` is passed, so an
    unvalidated planner cannot activate by default while research evaluation stays possible.
- Interfaces: `RetrievalProblem`, `RetrievalResult`, `StageOneReport`, `AdaptiveRetriever`,
  `SCORE_TERMS`, `MIN_EFFECTIVE_PRECEDENTS`
- Depends on: maestro.case_memory, maestro.directional
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .case_memory import (
    EpisodeStore,
    RetrievedPrecedent,
    ScientificEpisode,
    ScientificMeasurementStatus,
    case_memory_enabled,
)
from .directional import ContextFeatures, DirectionalState, FeatureArm, cosine

SCORE_TERMS = (
    "state_similarity", "mechanism_compatibility", "assay_compatibility", "temporal_compatibility",
    "evidence_quality", "historical_reliability", "adaptation_cost", "domain_shift",
    "measurement_mismatch",
)
MIN_EFFECTIVE_PRECEDENTS = 2.0
"""Kish effective number below which a retrieved set is reported as not usable."""
ADAPTATION_PRIOR_COST = 0.25
"""Declared prior cost per incompatible context attribute when no transfer history exists."""


@dataclass(frozen=True)
class RetrievalProblem:
    """The retrieval view of an open problem. No truth field: labels never enter retrieval."""

    problem_id: str
    biological_system: str
    assay: str
    intervention_type: str
    measurement_type: str
    control_design: str
    context: ContextFeatures
    hypotheses: tuple[str, str]
    state: DirectionalState = field(default_factory=DirectionalState)
    feature_arm: FeatureArm = FeatureArm.COMBINED


@dataclass(frozen=True)
class StageOneReport:
    eligible: tuple[str, ...]
    excluded: Mapping[str, str]
    """case_id -> the named incompatibility reason."""


@dataclass(frozen=True)
class RetrievalResult:
    stage1: StageOneReport
    precedents: Mapping[str, tuple[RetrievedPrecedent, ...]]
    """hypothesis -> its reranked precedents with full component reports."""
    kish: Mapping[str, float]
    usable: Mapping[str, bool]
    reason: Mapping[str, str | None]


def _temporal_compatible(a: float | None, b: float | None) -> float:
    if a is None or b is None or a <= 0 or b <= 0:
        return 0.5
    ratio = a / b if a >= b else b / a
    return max(0.0, 1.0 - math.log2(min(ratio, 16.0)) / 4.0)


class AdaptiveRetriever:
    """Four-stage retrieval over an `EpisodeStore` with per-case explanations."""

    def __init__(self, store: EpisodeStore, *, historical_reliability: Mapping[str, float] | None = None,
                 adaptation_history: Mapping[tuple, Mapping[str, float]] | None = None):
        self.store = store
        self.historical_reliability = dict(historical_reliability or {})
        self.adaptation_history = dict(adaptation_history or {})

    # ------------------------------------------------------------------ stage 1
    def hard_compatibility(self, problem: RetrievalProblem,
                           cases: Sequence[ScientificEpisode] | None = None) -> StageOneReport:
        eligible, excluded = [], {}
        for case in cases if cases is not None else self.store.latest():
            reason = self._incompatibility(problem, case)
            if reason is None:
                eligible.append(case.case_id)
            else:
                excluded[case.case_id] = reason
        return StageOneReport(tuple(sorted(eligible)), dict(sorted(excluded.items())))

    def _incompatibility(self, problem: RetrievalProblem, case: ScientificEpisode) -> str | None:
        ctx = case.context_fingerprint
        if ctx.get("biological_system") and ctx.get("biological_system") != problem.biological_system:
            return "incompatible:biological_system"
        if ctx.get("assay") and ctx.get("assay") != problem.assay:
            return "incompatible:assay"
        if ctx.get("measurement_type") and ctx.get("measurement_type") != problem.measurement_type:
            return "incompatible:measurement_type"
        if ctx.get("control_design") and ctx.get("control_design") != problem.control_design:
            return "incompatible:control_design"
        if ctx.get("intervention_type") and ctx.get("intervention_type") != problem.intervention_type:
            return "incompatible:intervention_type"
        if ctx.get("quality_status") == "failed":
            return "incompatible:quality_status"
        case_ctx = ContextFeatures(
            cell_line=ctx.get("cell_line"), assay=ctx.get("assay"),
            time_h=ctx.get("time_h"), dose_nM=ctx.get("dose_nM"),
            control_type=ctx.get("control_design"), chemical_unit=ctx.get("chemical_unit"),
        )
        flags = problem.context.compatibility_with(case_ctx)
        for name, ok in flags.items():
            if not ok:
                return f"incompatible:{name}"
        return None

    # ------------------------------------------------------------------ stage 2/3/4
    def retrieve(self, problem: RetrievalProblem, *, top_k: int = 5,
                 research_mode: bool = False) -> RetrievalResult:
        if not research_mode and not case_memory_enabled():
            raise PermissionError("case_memory_disabled:pass research_mode=True for evaluation")
        stage1 = self.hard_compatibility(problem)
        eligible = set(stage1.eligible)
        by_hypothesis: dict[str, list[RetrievedPrecedent]] = {h: [] for h in problem.hypotheses}
        kish: dict[str, float] = {}
        usable: dict[str, bool] = {}
        reason: dict[str, str | None] = {}
        for hypothesis in problem.hypotheses:
            scored = []
            for case in self.store.latest():
                if case.case_id not in eligible:
                    continue
                support = self._case_supports(case, hypothesis)
                if support is None:
                    continue
                components = self._components(problem, case, hypothesis)
                score = self.case_score(components)
                scored.append((score, components, case, support))
            scored.sort(key=lambda item: (-item[0], item[2].case_id))
            precedents = tuple(
                RetrievedPrecedent(
                    case_id=case.case_id,
                    hypothesis=hypothesis,
                    score=round(score, 6),
                    components={k: round(v, 6) for k, v in components.items()},
                    matches=self._matches(problem, case),
                    differences=self._differences(problem, case),
                    adaptation=self._adaptation(problem, case),
                    why=self._why(problem, case, hypothesis, components, support),
                )
                for score, components, case, support in scored[:top_k]
                if components["state_similarity"] > 0.0 or problem.feature_arm is FeatureArm.SCALAR
            )
            by_hypothesis[hypothesis] = list(precedents)
            weights = [p.components["state_similarity"] *
                       max(0.0, sum(p.components[t] for t in SCORE_TERMS[1:6])
                           - p.components["adaptation_cost"] - p.components["domain_shift"]
                           - p.components["measurement_mismatch"])
                       for p in precedents]
            total2 = sum(w * w for w in weights)
            kish[hypothesis] = (sum(weights) ** 2 / total2) if total2 > 0 else 0.0
            usable[hypothesis] = kish[hypothesis] >= MIN_EFFECTIVE_PRECEDENTS
            reason[hypothesis] = (None if usable[hypothesis]
                                  else "fewer_than_two_effective_precedents" if precedents
                                  else "no_eligible_precedent_after_stage1")
        return RetrievalResult(stage1, {h: tuple(v) for h, v in by_hypothesis.items()}, kish, usable, reason)

    # ------------------------------------------------------------------ terms
    def _case_supports(self, case: ScientificEpisode, hypothesis: str) -> str | None:
        """The reading kind with which this case supports `hypothesis`, or None when it does not."""

        for update in case.hypothesis_updates:
            if hypothesis in update.contrast and update.eliminated:
                return update.reading
        for claim in case.initial_hypotheses:
            if claim.hypothesis_id == hypothesis and not claim.advisory:
                return "class_membership"
        return None

    def _case_state(self, case: ScientificEpisode) -> DirectionalState:
        delta: dict[str, float] = {}
        pathway: dict[str, float] = {}
        for obs in case.initial_observations:
            if obs.status.biological and obs.readout and obs.value is not None and obs.direction:
                delta[obs.readout] = obs.value * obs.direction
            for name, value in obs.pathway_direction.items():
                pathway[name] = value
        return DirectionalState(signed_feature_delta=delta, pathway_direction=pathway)

    def _components(self, problem: RetrievalProblem, case: ScientificEpisode,
                    hypothesis: str) -> dict[str, float]:
        ctx = case.context_fingerprint
        case_state = self._case_state(case)
        from .directional import feature_vector
        a = feature_vector(problem.state, problem.feature_arm)
        if problem.feature_arm is FeatureArm.SCALAR or not a:
            # A state-free problem (or the scalar arm) cannot discriminate by direction: similarity
            # is presence of a measured state, never a fabricated directional match.
            state_sim = 1.0 if case_state.magnitude > 0 else 0.0
        else:
            b = feature_vector(case_state, problem.feature_arm)
            state_sim = max(0.0, cosine(a, b))
        mech = 0.5
        updates = [u for u in case.hypothesis_updates if hypothesis in u.contrast]
        if updates:
            mech = min(1.0, 0.5 + 0.25 * len(updates))
        assay = 1.0 if ctx.get("assay") == problem.assay else 0.0
        temporal = _temporal_compatible(ctx.get("time_h"), problem.context.time_h)
        agreements = [o.replicate_agreement for o in case.initial_observations
                      if o.replicate_agreement is not None]
        quality = sum(agreements) / len(agreements) if agreements else 0.5
        reliability = float(self.historical_reliability.get(case.case_id, 0.5))
        differing = self._differences(problem, case)
        key = tuple(sorted(differing))
        history = self.adaptation_history.get(key)
        if history is not None:
            cost = float(history.get("cost", ADAPTATION_PRIOR_COST * len(differing)))
        else:
            cost = min(1.0, ADAPTATION_PRIOR_COST * len(differing))
        shift = 1.0 - state_sim
        mismatch = 0.0 if ctx.get("measurement_type", problem.measurement_type) == problem.measurement_type else 1.0
        return {
            "state_similarity": state_sim,
            "mechanism_compatibility": mech,
            "assay_compatibility": assay,
            "temporal_compatibility": temporal,
            "evidence_quality": quality,
            "historical_reliability": reliability,
            "adaptation_cost": cost,
            "domain_shift": shift,
            "measurement_mismatch": mismatch,
        }

    @staticmethod
    def case_score(components: Mapping[str, float]) -> float:
        """The additive nine-term score of the design specification."""

        return (components["state_similarity"] + components["mechanism_compatibility"]
                + components["assay_compatibility"] + components["temporal_compatibility"]
                + components["evidence_quality"] + components["historical_reliability"]
                - components["adaptation_cost"] - components["domain_shift"]
                - components["measurement_mismatch"])

    # ------------------------------------------------------------------ explanation
    def _matches(self, problem: RetrievalProblem, case: ScientificEpisode) -> tuple[str, ...]:
        ctx = case.context_fingerprint
        out = []
        for name, value in (("assay", problem.assay), ("biological_system", problem.biological_system),
                            ("control_design", problem.control_design),
                            ("measurement_type", problem.measurement_type),
                            ("intervention_type", problem.intervention_type)):
            if ctx.get(name) == value:
                out.append(name)
        if ctx.get("cell_line") and ctx.get("cell_line") == problem.context.cell_line:
            out.append("cell_line")
        return tuple(sorted(out))

    def _differences(self, problem: RetrievalProblem, case: ScientificEpisode) -> Mapping[str, object]:
        ctx = case.context_fingerprint
        out: dict[str, object] = {}
        for name, want in (("cell_line", problem.context.cell_line), ("time_h", problem.context.time_h),
                           ("dose_nM", problem.context.dose_nM), ("assay", problem.assay)):
            got = ctx.get(name)
            if got is not None and want is not None and got != want:
                out[name] = {"case": got, "problem": want}
        return out

    def _adaptation(self, problem: RetrievalProblem, case: ScientificEpisode) -> Mapping[str, object]:
        differing = self._differences(problem, case)
        operations = tuple(f"recalibrate:{name}" for name in sorted(differing))
        key = tuple(sorted(differing))
        history = self.adaptation_history.get(key, {})
        return {"operations": operations, "differences": sorted(differing),
                "cost": min(1.0, float(history.get("cost", ADAPTATION_PRIOR_COST * len(differing)))),
                "supported": bool(history), "basis": "transfer_history" if history else "declared_prior"}

    def _why(self, problem: RetrievalProblem, case: ScientificEpisode, hypothesis: str,
             components: Mapping[str, float], support: str) -> str:
        return (f"supports {hypothesis} via {support}; state similarity "
                f"{components['state_similarity']:.2f} on arm {problem.feature_arm.value}; "
                f"assay {components['assay_compatibility']:.0f}, temporal "
                f"{components['temporal_compatibility']:.2f}, adaptation cost "
                f"{components['adaptation_cost']:.2f}, domain shift {components['domain_shift']:.2f}")
