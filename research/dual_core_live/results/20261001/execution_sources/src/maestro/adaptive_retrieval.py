"""Directional state features and adaptation-aware retrieval with explicit compatibility gates."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

from .case_memory import (
    EpisodeStore,
    RetrievedPrecedent,
    ScientificEpisode,
    ScientificMeasurementStatus,
    case_memory_enabled,
)


class FeatureArm(str, Enum):
    """The registered feature arms of the directional comparison (external protocol section 4)."""

    SCALAR = "scalar"
    SIGNED_DIRECTION = "signed_direction"
    PATHWAY_DIRECTION = "pathway_direction"
    COMBINED = "combined"


@dataclass(frozen=True)
class RealizationRecord:
    """What was actually realised, kept apart from what was nominal.

    Every quantity is a typed status plus an optional value; an unknown realised dose is a status,
    never the nominal dose relabelled, and never a zero.
    """

    dose_nominal: float | None = None
    dose_realized: float | None = None
    dose_realized_uncertainty: float | None = None
    engagement: ScientificMeasurementStatus = ScientificMeasurementStatus.NOT_PLANNED
    engagement_value: float | None = None
    functional_activity: ScientificMeasurementStatus = ScientificMeasurementStatus.NOT_PLANNED
    functional_activity_value: float | None = None
    downstream_response: ScientificMeasurementStatus = ScientificMeasurementStatus.NOT_PLANNED
    downstream_response_value: float | None = None
    note: str = ""

    def validation_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        for name in ("dose_nominal", "dose_realized", "dose_realized_uncertainty"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
                errors.append(f"invalid:{name}")
        for name, status, value in (
            ("engagement", self.engagement, self.engagement_value),
            ("functional_activity", self.functional_activity, self.functional_activity_value),
            ("downstream_response", self.downstream_response, self.downstream_response_value),
        ):
            if not isinstance(status, ScientificMeasurementStatus):
                errors.append(f"invalid:{name}_status")
            elif not status.biological and value is not None:
                errors.append(f"value_without_biological_status:{name}")
        return tuple(errors)


@dataclass(frozen=True)
class ContextFeatures:
    """Typed context of a measurement or a case; every field stays a separate feature."""

    cell_line: str | None = None
    tissue: str | None = None
    disease_context: str | None = None
    assay: str | None = None
    batch: str | None = None
    time_h: float | None = None
    dose_nM: float | None = None
    control_type: str | None = None
    chemical_unit: str | None = None
    compound_scaffold: str | None = None
    engagement_status: ScientificMeasurementStatus = ScientificMeasurementStatus.NOT_PLANNED
    functional_activity_status: ScientificMeasurementStatus = ScientificMeasurementStatus.NOT_PLANNED

    def compatibility_with(self, other: "ContextFeatures") -> Mapping[str, bool]:
        """Field-wise hard-compatibility flags used by stage 1 of retrieval."""

        out = {}
        for name in ("cell_line", "tissue", "disease_context", "assay", "control_type", "chemical_unit"):
            a, b = getattr(self, name), getattr(other, name)
            out[name] = a is None or b is None or a == b
        for name in ("time_h", "dose_nM"):
            a, b = getattr(self, name), getattr(other, name)
            out[name] = a is None or b is None or (a > 0 and b > 0 and 0.25 <= a / b <= 4.0)
        return out


@dataclass(frozen=True)
class DirectionalState:
    """The directional feature bundle of one condition.

    Every mapping is sparse: a feature that was not measured is absent, never zero-filled.
    """

    signed_feature_delta: Mapping[str, float] = field(default_factory=dict)
    ranked_up_features: tuple[str, ...] = ()
    ranked_down_features: tuple[str, ...] = ()
    pathway_direction: Mapping[str, float] = field(default_factory=dict)
    gene_set_score: Mapping[str, float] = field(default_factory=dict)
    cell_state_proportion: Mapping[str, float] = field(default_factory=dict)
    population_shift: float | None = None
    time_slope: float | None = None
    dose_slope: float | None = None
    replicate_variance: float | None = None
    replicate_agreement: float | None = None

    @property
    def magnitude(self) -> float:
        return math.sqrt(sum(v * v for v in self.signed_feature_delta.values()))


def ranked_features(delta: Mapping[str, float], top: int = 50) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """The `top` features by signed change in each direction (deterministic tie-break by name)."""

    up = sorted((k for k, v in delta.items() if v > 0), key=lambda k: (-delta[k], k))[:top]
    down = sorted((k for k, v in delta.items() if v < 0), key=lambda k: (delta[k], k))[:top]
    return tuple(up), tuple(down)


def pathway_projection(delta: Mapping[str, float], gene_sets: Mapping[str, Sequence[str]]) -> dict[str, float]:
    """Signed standardised projection of a state change onto each gene set.

    The score is the mean signed delta of the set's measured members, scaled by the square root of
    the member count so sets of different size stay comparable. A set with no measured member is
    absent from the result, never scored zero.
    """

    out: dict[str, float] = {}
    for name, members in gene_sets.items():
        present = [delta[g] for g in members if g in delta]
        if not present:
            continue
        out[name] = round(sum(present) / math.sqrt(len(present)), 6)
    return out


def population_shift_index(delta: Mapping[str, float]) -> float | None:
    """Fraction of measured features that move in the dominant direction; None when empty."""

    if not delta:
        return None
    up = sum(1 for v in delta.values() if v > 0)
    down = sum(1 for v in delta.values() if v < 0)
    total = up + down
    if total == 0:
        return 0.0
    return (up - down) / total


def directional_state_from_shift(
    delta: Mapping[str, float],
    gene_sets: Mapping[str, Sequence[str]] = (),
    *,
    top: int = 50,
    replicate_variance: float | None = None,
    replicate_agreement: float | None = None,
) -> DirectionalState:
    """Build the directional state of one condition from its signed per-feature changes."""

    up, down = ranked_features(delta, top)
    pathway = pathway_projection(delta, gene_sets) if gene_sets else {}
    return DirectionalState(
        signed_feature_delta={k: float(v) for k, v in delta.items()},
        ranked_up_features=up,
        ranked_down_features=down,
        pathway_direction=pathway,
        gene_set_score=dict(pathway),
        population_shift=population_shift_index(delta),
        replicate_variance=replicate_variance,
        replicate_agreement=replicate_agreement,
    )


def feature_vector(state: DirectionalState, arm: FeatureArm) -> dict[str, float]:
    """The retrieval/forecast feature vector of one registered arm on identical data.

    `scalar` keeps only the magnitude (the development status quo: direction never enters).
    `signed_direction` keeps gene-level signed changes. `pathway_direction` keeps the signed
    pathway projection. `combined` concatenates both with a namespace prefix so they cannot collide.
    """

    if arm is FeatureArm.SCALAR:
        return {"__magnitude__": state.magnitude}
    if arm is FeatureArm.SIGNED_DIRECTION:
        return dict(state.signed_feature_delta)
    if arm is FeatureArm.PATHWAY_DIRECTION:
        return dict(state.pathway_direction)
    if arm is FeatureArm.COMBINED:
        out = {f"gene:{k}": v for k, v in state.signed_feature_delta.items()}
        out.update({f"pathway:{k}": v for k, v in state.pathway_direction.items()})
        return out
    raise ValueError(f"unknown_feature_arm:{arm}")


def cosine(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    """Cosine over the shared support; 0.0 when either side is empty or the support is disjoint."""

    shared = set(a) & set(b)
    if not shared:
        return 0.0
    dot = sum(a[k] * b[k] for k in shared)
    na = math.sqrt(sum(a[k] * a[k] for k in shared))
    nb = math.sqrt(sum(b[k] * b[k] for k in shared))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


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
    state_context: ContextFeatures | None = None
    """Context of the already observed state, distinct from the future action context."""


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

    def _case_state(self, case: ScientificEpisode,
                    context: ContextFeatures | None = None) -> DirectionalState:
        """Use one identifiable pre-action condition; outcomes never become retrieval inputs."""

        if (case.provenance.get("builder") == "tools.case_memory.build_cases"
                and case.provenance.get("builder_version") in (None, "loo-proxy-2")):
            # Older immutable proxy archives predate visibility metadata and put future
            # signatures in initial_observations. A defaulted field cannot make them inputs.
            return DirectionalState()
        observations = [obs for obs in case.initial_observations
                        if obs.availability == "pre_action" and obs.status.biological]
        if context is not None:
            observations = [obs for obs in observations if all(
                want is None or got == want for want, got in (
                    (context.cell_line, obs.cell_line), (context.assay, obs.assay),
                    (context.time_h, obs.time_h), (context.dose_nM, obs.dose_nM)))]
        conditions = {(obs.condition_id, obs.cell_line, obs.assay, obs.time_h, obs.dose_nM)
                      for obs in observations}
        if len(conditions) != 1:
            return DirectionalState()
        delta: dict[str, float] = {}
        pathway: dict[str, float] = {}
        for obs in observations:
            if obs.status.biological and obs.readout and obs.value is not None and obs.direction:
                value = obs.value * obs.direction
                if obs.readout in delta and delta[obs.readout] != value:
                    return DirectionalState()  # replicate aggregation belongs to preprocessing
                delta[obs.readout] = value
            for name, value in obs.pathway_direction.items():
                if name in pathway and pathway[name] != value:
                    return DirectionalState()
                pathway[name] = value
        return DirectionalState(signed_feature_delta=delta, pathway_direction=pathway)

    def _components(self, problem: RetrievalProblem, case: ScientificEpisode,
                    hypothesis: str) -> dict[str, float]:
        ctx = case.context_fingerprint
        case_state = self._case_state(case, problem.state_context or problem.context)

        a = feature_vector(problem.state, problem.feature_arm)
        if problem.feature_arm is FeatureArm.SCALAR or not a:
            # No directional input means no directional weighting. Outcome-only cases may still
            # support the frequency baseline; the forecaster separately requires measured labels.
            state_sim = 1.0
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
