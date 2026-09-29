"""Typed records for the evidence-grounded scientific case memory.

File summary
- Path: research/scientific_case_memory/case_schema.py
- Purpose: define what one case, one open problem and their parts are, how they serialise, how a
  content digest is taken, and which named errors a case can carry. A case is a validated
  decision trajectory, not a document: it holds observations with a typed measurement status,
  competing hypotheses, a costed action menu, forecasts kept apart from real measurements,
  qualified evidence, updates, a decision, failure modes, an adaptation map, a calibration
  history and provenance.
- Core points:
  - Measurement status is one of six values (`MeasurementStatus`): not planned, planned but not
    measured, QC failed, undetected, ambiguous, qualified. A failed or missing measurement is
    never converted to a zero; the status is what a downstream reader must branch on.
  - Case kinds are canonical, contrastive, failure and adaptation. A reading inside a case also
    carries a reading kind (`ReadingKind`), so failure and negative precedents can be removed
    from a memory in an ablation without deleting the cases that hold them.
  - Cases are immutable. A new fact makes a new version whose `supersedes` names the previous
    content digest; nothing is edited in place (`case_store.py` enforces this).
  - Evidence classes separate measured fact, qualified evidence, model prediction, historical
    analogy, mechanistic inference and speculation (`EvidenceClass`); `validate_case` refuses a
    forecast carrying measurement status and a qualified item without a passing measurement.
  - `OpenProblem` is the typed representation of a user's problem before any hypothesis exists.
    It carries no truth field, so it cannot leak a held-out label into retrieval.
- Interfaces: `CaseKind`, `ReadingKind`, `MeasurementStatus`, `EvidenceClass`, `ProblemType`,
  `Case`, `OpenProblem`, `Observation`, `HypothesisClaim`, `ActionSpec`, `KnowledgeRef`,
  `ForecastRecord`, `Measurement`, `HypothesisUpdate`, `FailureMode`, `AdaptationLink`,
  `CalibrationEntry`, `RawDataRef`, `validate_case`, `validate_open_problem`, `digest`,
  `to_dict`, `case_from_dict`
- Depends on: standard library only
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Any, Mapping

SCHEMA_VERSION = "scm-1"


class CaseKind(str, Enum):
    CANONICAL = "canonical"
    CONTRASTIVE = "contrastive"
    FAILURE = "failure"
    ADAPTATION = "adaptation"


class ReadingKind(str, Enum):
    """What one registered reading of a case turned out to be."""

    CANONICAL = "canonical"      # detected, QC passed, the reading removed the wrong hypothesis
    MISLEADING = "misleading"    # detected, QC passed, the reading matched the decoy: a failure precedent
    NEGATIVE = "negative"        # measured and undetected: a negative precedent
    AMBIGUOUS = "ambiguous"      # measured, detected, profile unresolved
    QC_FAILED = "qc_failed"      # ran and failed its quality rule


class MeasurementStatus(str, Enum):
    NOT_PLANNED = "not_planned"
    PLANNED_MISSING = "planned_missing"
    QC_FAILED = "qc_failed"
    UNDETECTED = "undetected"
    AMBIGUOUS = "ambiguous"
    QUALIFIED = "qualified"

    @property
    def biological(self) -> bool:
        return self in (MeasurementStatus.UNDETECTED, MeasurementStatus.AMBIGUOUS, MeasurementStatus.QUALIFIED)


class EvidenceClass(str, Enum):
    MEASURED_FACT = "measured_fact"
    QUALIFIED_EVIDENCE = "qualified_evidence"
    MODEL_PREDICTION = "model_prediction"
    HISTORICAL_ANALOGY = "historical_analogy"
    MECHANISTIC_INFERENCE = "mechanistic_inference"
    SPECULATION = "speculation"


class ProblemType(str, Enum):
    MECHANISM_CONTRAST_TRANSCRIPTOMIC = "mechanism_contrast_transcriptomic"
    GENETIC_PHARMACOLOGICAL = "genetic_pharmacological_discrepancy"
    ENGAGEMENT_REPAIR = "engagement_repair"
    TRANSCRIPTOMIC_VIABILITY_DISCORDANCE = "transcriptomic_viability_discordance"


DECISION_STATUSES = ("decided", "deferred", "undetermined", "exhausted", "abstained", "continue", "revise_attribution",
                     "revise_intervention", "change_intervention_mode", "defer", "open")


# ---------------------------------------------------------------------------------------- parts
@dataclass(frozen=True)
class RawDataRef:
    """A pointer to raw or processed data with a checksum, never the data itself."""

    uri: str
    sha256: str
    role: str
    row: int | None = None


@dataclass(frozen=True)
class Observation:
    """One condition of one case with its typed status.

    `readout` is the observable name, `value` its number when a value exists. A value is `None`
    unless the status is biological; a failed or missing measurement never carries a zero.
    """

    condition_id: str
    status: MeasurementStatus
    assay: str
    cell_line: str | None = None
    time_h: float | None = None
    dose_nM: float | None = None
    readout: str | None = None
    value: float | None = None
    replicate_agreement: float | None = None
    detected: bool | None = None
    state_ref: RawDataRef | None = None
    note: str = ""


@dataclass(frozen=True)
class HypothesisClaim:
    """A testable claim. `predicted` maps an action identifier to the reading it would produce."""

    hypothesis_id: str
    claim: str
    assumptions: tuple[str, ...] = ()
    predicted: Mapping[str, str] = field(default_factory=dict)
    advisory: bool = False
    """An advisory hypothesis is kept in the graph and the report but is not a member of the
    registered candidate set, so it can never be eliminated by the evidence rules."""


@dataclass(frozen=True)
class ActionSpec:
    action_id: str
    description: str
    assay: str
    cost_wells: float
    duration_days: float
    readout: str
    cell_line: str | None = None
    time_h: float | None = None
    dose_nM: float | None = None
    prerequisites: tuple[str, ...] = ()
    controls: tuple[str, ...] = ()
    detection_power: float | None = None
    available: bool = True


@dataclass(frozen=True)
class KnowledgeRef:
    source: str
    identifier: str
    statement: str
    evidence_class: EvidenceClass = EvidenceClass.HISTORICAL_ANALOGY
    sha256: str | None = None


@dataclass(frozen=True)
class ForecastRecord:
    """A model forecast. It is never a measurement and refuses measurement status."""

    action_id: str
    hypothesis_id: str
    branches: Mapping[str, float]
    support: float
    model_version: str
    basis: str
    interval: tuple[float, float] | None = None
    applicable: bool = True
    refusal: str | None = None
    evidence_class: EvidenceClass = EvidenceClass.MODEL_PREDICTION


@dataclass(frozen=True)
class Measurement:
    action_id: str
    status: MeasurementStatus
    outcome_label: str | None
    independent_units: int | None = None
    source: str = ""


@dataclass(frozen=True)
class HypothesisUpdate:
    """What one reading did to the candidate set under the registered rules (append-only)."""

    action_id: str
    contrast: tuple[str, str]
    reading: str
    eliminated: tuple[str, ...] = ()
    qualified: bool = False
    reading_kind: ReadingKind = ReadingKind.AMBIGUOUS
    note: str = ""
    codes: str = ""
    """For a reference case: one character per pool class in pool order, the registered validator's
    reading of this compound at this condition against that class as decoy (0 matches its own
    class, 1 matches the decoy, 2 unresolved, 3 undetected, - not scored). `contrast` is then
    (own class, "*pool*") and `reading_kind` is the most severe kind present."""


@dataclass(frozen=True)
class FailureMode:
    code: str
    description: str
    action_id: str | None = None
    contrast: tuple[str, str] | None = None
    severity: str = "informational"


@dataclass(frozen=True)
class AdaptationLink:
    """One recorded transfer of a source case's reading onto a target problem."""

    source_case: str
    target_case: str
    differences: Mapping[str, Any]
    operations: tuple[str, ...]
    cost: float
    success: bool | None
    valid_when: tuple[str, ...] = ()
    failed_when: tuple[str, ...] = ()


@dataclass(frozen=True)
class CalibrationEntry:
    """A graded forecast: what a memory or a model said and what was later measured."""

    model_version: str
    action_id: str
    forecast: float
    realised: float
    kind: str = "reading_probability"
    snapshot: str = ""


# ---------------------------------------------------------------------------------------- case
@dataclass(frozen=True)
class Case:
    case_id: str
    case_version: int
    case_kind: CaseKind
    problem_type: ProblemType
    problem_statement: str
    user_question: str
    raw_data_references: tuple[RawDataRef, ...]
    data_quality_report: Mapping[str, Any]
    context_fingerprint: Mapping[str, Any]
    initial_observations: tuple[Observation, ...]
    initial_hypotheses: tuple[HypothesisClaim, ...]
    candidate_actions: tuple[ActionSpec, ...]
    retrieved_knowledge: tuple[KnowledgeRef, ...]
    virtual_cell_predictions: tuple[ForecastRecord, ...]
    predicted_outcome_branches: tuple[ForecastRecord, ...]
    real_measurements: tuple[Measurement, ...]
    measurement_quality: Mapping[str, Any]
    qualified_evidence: tuple[Mapping[str, Any], ...]
    hypothesis_updates: tuple[HypothesisUpdate, ...]
    final_decision: Mapping[str, Any]
    next_action: Mapping[str, Any]
    failure_modes: tuple[FailureMode, ...]
    adaptation_map: tuple[AdaptationLink, ...]
    calibration_history: tuple[CalibrationEntry, ...]
    provenance: Mapping[str, Any]
    supersedes: str | None = None
    schema_version: str = SCHEMA_VERSION

    @property
    def digest(self) -> str:
        return digest(self)

    def readings(self) -> tuple[HypothesisUpdate, ...]:
        return self.hypothesis_updates


@dataclass(frozen=True)
class OpenProblem:
    """A user's problem compiled before any hypothesis is built (design section 4). No truth field."""

    problem_id: str
    biological_system: str
    cell_line_or_context: str
    tissue_or_disease: str | None
    intervention: str
    compound_identity: Mapping[str, Any]
    chemical_structure: str | None
    nominal_target: str | None
    measured_engagement: MeasurementStatus
    functional_activity: MeasurementStatus
    time_h: float | None
    dose_nM: float | None
    assay: str
    control_design: str
    replicates: int | None
    batch: str | None
    observed_features: tuple[str, ...]
    pathway_readouts: Mapping[str, float]
    phenotype: str | None
    measurement_status: Mapping[str, MeasurementStatus]
    quality_status: Mapping[str, Any]
    known_constraints: tuple[str, ...]
    user_goal: str
    history: tuple[Mapping[str, Any], ...] = ()


# ---------------------------------------------------------------------------------------- codec
_ENUMS = {"case_kind": CaseKind, "problem_type": ProblemType, "status": MeasurementStatus,
          "evidence_class": EvidenceClass, "reading_kind": ReadingKind,
          "measured_engagement": MeasurementStatus, "functional_activity": MeasurementStatus}
_LISTS = {"raw_data_references": RawDataRef, "initial_observations": Observation,
          "initial_hypotheses": HypothesisClaim, "candidate_actions": ActionSpec,
          "retrieved_knowledge": KnowledgeRef, "virtual_cell_predictions": ForecastRecord,
          "predicted_outcome_branches": ForecastRecord, "real_measurements": Measurement,
          "hypothesis_updates": HypothesisUpdate, "failure_modes": FailureMode,
          "adaptation_map": AdaptationLink, "calibration_history": CalibrationEntry}
_SINGLE = {"state_ref": RawDataRef}
_TUPLE_STR = {"assumptions", "prerequisites", "controls", "operations", "valid_when", "failed_when",
              "eliminated", "observed_features", "known_constraints"}
_PAIR = {"contrast", "interval"}


def _clean(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _clean(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _clean(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = sorted(value, key=str) if isinstance(value, (set, frozenset)) else value
        return [_clean(v) for v in items]
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return _clean(value.item())
    return value


def to_dict(obj: Any) -> dict:
    """Plain JSON-safe dictionary of a case or any part (NaN becomes null, enums become values)."""
    return _clean(obj)


def digest(obj: Any) -> str:
    """SHA-256 of the canonical JSON of a record, so equal content always has equal identity."""
    text = json.dumps(to_dict(obj), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build(cls, data: Mapping[str, Any]):
    kwargs = {}
    for f in fields(cls):
        if f.name not in data:
            continue
        value = data[f.name]
        if f.name in _ENUMS and value is not None:
            value = _ENUMS[f.name](value)
        elif f.name in _LISTS and cls is Case:
            value = tuple(_build(_LISTS[f.name], v) for v in value)
        elif f.name in _SINGLE and value is not None:
            value = _build(_SINGLE[f.name], value)
        elif f.name == "measurement_status" and isinstance(value, Mapping):
            value = {k: MeasurementStatus(v) for k, v in value.items()}
        elif f.name in _TUPLE_STR and value is not None:
            value = tuple(value)
        elif f.name in _PAIR and value is not None:
            value = tuple(value)
        elif f.name in ("qualified_evidence", "history") and value is not None:
            value = tuple(value)
        kwargs[f.name] = value
    return cls(**kwargs)


def case_from_dict(data: Mapping[str, Any]) -> Case:
    """Rebuild a `Case` from `to_dict` output; the round trip preserves the digest."""
    return _build(Case, data)


# ---------------------------------------------------------------------------------------- validation
REQUIRED_CONTEXT = ("dataset", "assay", "context")
REQUIRED_PROVENANCE = ("builder", "sources", "created_at")


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def validate_case(case: Case) -> tuple[str, ...]:
    """Named structural errors; an empty tuple means the case satisfies the schema.

    These are contract checks, not biological judgements: they enforce that the fields that make a
    case reusable exist and that no record claims more than its status allows.
    """

    errors: list[str] = []
    for name in ("case_id", "problem_statement", "user_question"):
        if _blank(getattr(case, name)):
            errors.append(f"missing:{name}")
    if type(case.case_version) is not int or case.case_version < 1:
        errors.append("invalid:case_version")
    if case.case_version > 1 and not case.supersedes:
        errors.append("missing:supersedes")
    if case.case_version == 1 and case.supersedes:
        errors.append("invalid:first_version_supersedes")
    for key in REQUIRED_CONTEXT:
        if _blank(case.context_fingerprint.get(key)):
            errors.append(f"missing:context_fingerprint.{key}")
    for key in REQUIRED_PROVENANCE:
        if _blank(case.provenance.get(key)):
            errors.append(f"missing:provenance.{key}")
    if not case.raw_data_references:
        errors.append("missing:raw_data_references")
    for ref in case.raw_data_references:
        if _blank(ref.uri) or not (isinstance(ref.sha256, str) and len(ref.sha256) == 64):
            errors.append(f"invalid:raw_data_reference:{ref.uri}")
    if not case.candidate_actions:
        errors.append("missing:candidate_actions")
    action_ids = [a.action_id for a in case.candidate_actions]
    if len(set(action_ids)) != len(action_ids):
        errors.append("duplicate:action_id")
    hypothesis_ids = [h.hypothesis_id for h in case.initial_hypotheses]
    if len(set(hypothesis_ids)) != len(hypothesis_ids):
        errors.append("duplicate:hypothesis_id")
    registered = [h for h in case.initial_hypotheses if not h.advisory]
    if len(registered) < 2:
        errors.append("missing:two_registered_hypotheses")
    known_actions = set(action_ids)
    for obs in case.initial_observations:
        if not isinstance(obs.status, MeasurementStatus):
            errors.append(f"invalid:observation_status:{obs.condition_id}")
            continue
        if not obs.status.biological and obs.value is not None:
            errors.append(f"value_without_biological_status:{obs.condition_id}")
    for m in case.real_measurements:
        if m.action_id not in known_actions:
            errors.append(f"measurement_for_unknown_action:{m.action_id}")
        if not isinstance(m.status, MeasurementStatus):
            errors.append(f"invalid:measurement_status:{m.action_id}")
    for f in (*case.virtual_cell_predictions, *case.predicted_outcome_branches):
        if f.evidence_class is not EvidenceClass.MODEL_PREDICTION:
            errors.append(f"forecast_claims_status:{f.action_id}:{f.evidence_class.value}")
        total = sum(f.branches.values()) if f.branches else 0.0
        if f.refusal is None and f.branches and abs(total - 1.0) > 1e-6:
            errors.append(f"forecast_not_normalised:{f.action_id}:{f.hypothesis_id}")
    qualified_actions = {m.action_id for m in case.real_measurements if m.status is MeasurementStatus.QUALIFIED}
    for card in case.qualified_evidence:
        if card.get("action_id") not in qualified_actions:
            errors.append(f"qualified_without_qualified_measurement:{card.get('action_id')}")
    for u in case.hypothesis_updates:
        if u.qualified and not u.eliminated and u.reading_kind is ReadingKind.CANONICAL:
            errors.append(f"canonical_reading_without_elimination:{u.action_id}")
    status = case.final_decision.get("status")
    if status not in DECISION_STATUSES:
        errors.append("invalid:final_decision.status")
    if _blank(case.final_decision.get("basis")):
        errors.append("missing:final_decision.basis")
    if case.case_kind is CaseKind.ADAPTATION:
        if not case.adaptation_map:
            errors.append("adaptation_case_without_links")
        for link in case.adaptation_map:
            if not (link.source_case and link.target_case) or link.success is None:
                errors.append("adaptation_link_incomplete")
    if case.case_kind is CaseKind.FAILURE and not case.failure_modes:
        errors.append("failure_case_without_failure_mode")
    if case.case_kind is CaseKind.CONTRASTIVE and not any(
            fm.code.startswith("contrast") for fm in case.failure_modes) and not case.adaptation_map:
        errors.append("contrastive_case_without_contrast")
    return tuple(dict.fromkeys(errors))


def validate_open_problem(problem: OpenProblem) -> tuple[str, ...]:
    """Errors that would make a user's problem unusable, including a missing-becomes-zero conversion."""

    errors: list[str] = []
    for name in ("problem_id", "biological_system", "cell_line_or_context", "intervention", "assay",
                 "control_design", "user_goal"):
        if _blank(getattr(problem, name)):
            errors.append(f"missing:{name}")
    if not isinstance(problem.measured_engagement, MeasurementStatus):
        errors.append("invalid:measured_engagement")
    if not isinstance(problem.functional_activity, MeasurementStatus):
        errors.append("invalid:functional_activity")
    for name, status in problem.measurement_status.items():
        if not isinstance(status, MeasurementStatus):
            errors.append(f"invalid:measurement_status:{name}")
    for name in ("time_h", "dose_nM"):
        value = getattr(problem, name)
        if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
            errors.append(f"invalid:{name}")
    for name, value in problem.pathway_readouts.items():
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"invalid:pathway_readout:{name}")
        elif problem.measurement_status.get(name) in (MeasurementStatus.QC_FAILED, MeasurementStatus.PLANNED_MISSING,
                                                      MeasurementStatus.NOT_PLANNED) and value == 0.0:
            errors.append(f"missing_or_failed_reported_as_zero:{name}")
    if "truth" in problem.quality_status or "label" in problem.quality_status:
        errors.append("truth_field_in_open_problem")
    return tuple(dict.fromkeys(errors))
