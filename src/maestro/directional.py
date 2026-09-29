"""Directional biological features for case construction, retrieval and forecasts.

File summary
- Path: src/maestro/directional.py
- Purpose: turn a signed per-feature state change (for example moderated z-scores of a
  transcriptomic signature) into the directional feature sets the case memory uses, so that
  direction - not only magnitude - enters retrieval, case comparison and forecasts.
- Core points:
  - State features: signed feature deltas, ranked up/down features, pathway direction (signed
    gene-set projection), gene-set scores, population shift, and replicate statistics. Features a
    measurement never produced stay absent; a missing or failed measurement is never a zero.
  - Context features are kept typed (cell line, tissue, disease context, assay, batch, time, dose,
    control type, chemical unit, scaffold, engagement and functional-activity status).
  - Realisation features keep `dose_nominal` apart from `dose_realized` and measured engagement,
    functional activity and downstream response apart from each other. An unknown realised dose is
    `None` with an uncertainty note, never the nominal dose relabelled.
  - `feature_vector` selects one of the registered feature arms (scalar, signed direction, pathway
    direction, combined) so the arms are compared on identical data; `cosine` is the frozen
    similarity of the external protocol.
- Interfaces: `RealizationRecord`, `DirectionalState`, `ContextFeatures`, `FeatureArm`,
  `directional_state_from_shift`, `pathway_projection`, `feature_vector`, `cosine`,
  `ranked_features`, `population_shift_index`
- Depends on: standard library only
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

from .case_memory import ScientificMeasurementStatus


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
