"""Versioned production schema for complete scientific episodes (case memory)."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
import os
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "scm-2"


def case_memory_enabled() -> bool:
    """The production feature flag. Off unless explicitly enabled in the environment."""

    return os.environ.get("MAESTRO_CASE_MEMORY_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------------------- enums
class ScientificMeasurementStatus(str, Enum):
    """The six-state measurement model. A status, never a silent zero."""

    NOT_PLANNED = "not_planned"
    PLANNED_MISSING = "planned_missing"
    QC_FAILED = "qc_failed"
    UNDETECTED = "undetected"
    AMBIGUOUS = "ambiguous"
    QUALIFIED = "qualified"

    @property
    def biological(self) -> bool:
        return self in (
            ScientificMeasurementStatus.UNDETECTED,
            ScientificMeasurementStatus.AMBIGUOUS,
            ScientificMeasurementStatus.QUALIFIED,
        )


class CaseKind(str, Enum):
    CANONICAL = "canonical"
    CONTRASTIVE = "contrastive"
    FAILURE = "failure"
    NEGATIVE = "negative"
    ADAPTATION = "adaptation"
    BRIDGE = "bridge"
    REAL_USER_EPISODE = "real_user_episode"


class EvidenceClass(str, Enum):
    MEASURED_FACT = "measured_fact"
    QUALIFIED_EVIDENCE = "qualified_experimental_evidence"
    MODEL_PREDICTION = "model_prediction"
    HISTORICAL_ANALOGY = "historical_analogy"
    MECHANISTIC_INFERENCE = "mechanistic_inference"
    CURATED_ANNOTATION = "curated_annotation"
    SPECULATION = "speculation"


DECISION_STATUSES = (
    "decided", "deferred", "undetermined", "exhausted", "abstained", "continue",
    "revise_attribution", "revise_intervention", "change_intervention_mode", "defer", "open",
)


# ---------------------------------------------------------------------------------------- parts
@dataclass(frozen=True)
class RawDataRef:
    """A pointer to raw or processed data with a checksum, never the data itself."""

    uri: str
    sha256: str
    role: str
    row: int | None = None


@dataclass(frozen=True)
class EpisodeObservation:
    """One condition of one episode with its typed status; a value exists only for biological states."""

    condition_id: str
    status: ScientificMeasurementStatus
    assay: str
    cell_line: str | None = None
    time_h: float | None = None
    dose_nM: float | None = None
    readout: str | None = None
    value: float | None = None
    direction: int | None = None
    """Sign of the directional change (-1, 0, +1) when a directional readout exists; None otherwise."""
    pathway_direction: Mapping[str, float] = field(default_factory=dict)
    """Signed pathway-level projections for this condition (empty when not computed)."""
    replicate_agreement: float | None = None
    detected: bool | None = None
    state_ref: RawDataRef | None = None
    note: str = ""
    availability: str = "pre_action"
    """Whether this observation was available before the queried action, or is outcome_only."""


@dataclass(frozen=True)
class HypothesisClaim:
    """A testable claim. `predicted` maps an action identifier to the reading it would produce."""

    hypothesis_id: str
    claim: str
    assumptions: tuple[str, ...] = ()
    predicted: Mapping[str, str] = field(default_factory=dict)
    advisory: bool = False


@dataclass(frozen=True)
class CandidateAction:
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
class ForecastRecord:
    """A model forecast. Never a measurement; refuses measurement status by contract."""

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
class RealMeasurement:
    action_id: str
    status: ScientificMeasurementStatus
    outcome_label: str | None
    independent_units: int | None = None
    source: str = ""
    conditioning_hypothesis: str | None = None
    """Independently established reference stratum, never inferred from the outcome being predicted."""
    contrast: tuple[str, str] | None = None
    label_kind: str = "measured_outcome"
    """Derived proxy labels are usable only in explicitly requested research evaluation."""
    sampling_frame: str = "unspecified"
    """all_attempts or valid_only; unspecified cannot establish experiment failure frequency."""


@dataclass(frozen=True)
class HypothesisUpdate:
    """What one reading did to the candidate set under the registered rules (append-only)."""

    action_id: str
    contrast: tuple[str, str]
    reading: str
    eliminated: tuple[str, ...] = ()
    qualified: bool = False
    note: str = ""


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


@dataclass(frozen=True)
class BranchingPlan:
    """The registered interpretation plan for every possible reading of one action.

    `on_outcome` maps a reading label to the follow-up (evidence update, hypothesis update, next
    action). `on_ambiguous` and `on_invalid` are mandatory: an ambiguous reading routes to an
    orthogonal assay or a QC action, and an invalid experiment updates no biological hypothesis.
    """

    action_id: str
    on_outcome: Mapping[str, str]
    on_ambiguous: str
    on_invalid: str


@dataclass(frozen=True)
class RetrievedPrecedent:
    """Why one precedent case was retrieved and what must change before reusing it."""

    case_id: str
    hypothesis: str
    score: float
    components: Mapping[str, float]
    matches: tuple[str, ...]
    differences: Mapping[str, Any]
    adaptation: Mapping[str, Any]
    why: str


# ---------------------------------------------------------------------------------------- episode
@dataclass(frozen=True)
class ScientificEpisode:
    """A complete scientific episode: the production case record (schema scm-2)."""

    case_id: str
    case_version: int
    case_kind: CaseKind
    problem_type: str
    user_question: str
    raw_data_references: tuple[RawDataRef, ...]
    data_quality_report: Mapping[str, Any]
    context_fingerprint: Mapping[str, Any]
    initial_observations: tuple[EpisodeObservation, ...]
    initial_hypotheses: tuple[HypothesisClaim, ...]
    hypothesis_graph: Mapping[str, Any]
    retrieved_cases: tuple[RetrievedPrecedent, ...]
    adaptation_map: tuple[AdaptationLink, ...]
    candidate_actions: tuple[CandidateAction, ...]
    virtual_cell_forecasts: tuple[ForecastRecord, ...]
    predicted_outcome_branches: tuple[ForecastRecord, ...]
    real_measurements: tuple[RealMeasurement, ...]
    measurement_quality: Mapping[str, Any]
    qualified_evidence: tuple[Mapping[str, Any], ...]
    hypothesis_updates: tuple[HypothesisUpdate, ...]
    next_action: Mapping[str, Any]
    branching_interpretation_plan: tuple[BranchingPlan, ...]
    final_decision: Mapping[str, Any]
    failure_modes: tuple[FailureMode, ...]
    calibration_history: tuple[CalibrationEntry, ...]
    provenance: Mapping[str, Any]
    problem_statement: str = ""
    supersedes: str | None = None
    schema_version: str = SCHEMA_VERSION

    @property
    def digest(self) -> str:
        return digest(self)


# ---------------------------------------------------------------------------------------- codec
_ENUMS = {
    "case_kind": CaseKind,
    "status": ScientificMeasurementStatus,
    "evidence_class": EvidenceClass,
}
_LISTS = {
    "raw_data_references": RawDataRef,
    "initial_observations": EpisodeObservation,
    "initial_hypotheses": HypothesisClaim,
    "retrieved_cases": RetrievedPrecedent,
    "adaptation_map": AdaptationLink,
    "candidate_actions": CandidateAction,
    "virtual_cell_forecasts": ForecastRecord,
    "predicted_outcome_branches": ForecastRecord,
    "real_measurements": RealMeasurement,
    "hypothesis_updates": HypothesisUpdate,
    "branching_interpretation_plan": BranchingPlan,
    "failure_modes": FailureMode,
    "calibration_history": CalibrationEntry,
}
_SINGLE = {"state_ref": RawDataRef}
_TUPLE_STR = {"assumptions", "prerequisites", "controls", "operations", "valid_when", "failed_when",
              "eliminated", "matches"}
_PAIR = {"contrast", "interval"}


def _clean(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        result = {f.name: _clean(getattr(value, f.name)) for f in fields(value)}
        if isinstance(value, EpisodeObservation) and value.availability == "pre_action":
            result.pop("availability")
        if isinstance(value, RealMeasurement):
            # Preserve pre-extension content identities and append-only digest chains.
            for name, default in (("conditioning_hypothesis", None), ("contrast", None),
                                  ("label_kind", "measured_outcome"), ("sampling_frame", "unspecified")):
                if getattr(value, name) == default:
                    result.pop(name)
        return result
    if isinstance(value, Mapping):
        return {str(k): _clean(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = sorted(value, key=str) if isinstance(value, (set, frozenset)) else value
        return [_clean(v) for v in items]
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return _clean(value.item())
    return value


def episode_to_dict(obj: Any) -> dict:
    """Plain JSON-safe dictionary of an episode or any part (NaN becomes null, enums become values)."""

    return _clean(obj)


def digest(obj: Any) -> str:
    """SHA-256 of the canonical JSON of a record, so equal content always has equal identity."""

    text = json.dumps(episode_to_dict(obj), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build(cls, data: Mapping[str, Any]):
    kwargs = {}
    for f in fields(cls):
        if f.name not in data:
            continue
        value = data[f.name]
        if f.name in _ENUMS and value is not None:
            value = _ENUMS[f.name](value) if not isinstance(value, _ENUMS[f.name]) else value
        elif f.name in _LISTS and cls is ScientificEpisode:
            value = tuple(_build(_LISTS[f.name], v) if isinstance(v, Mapping) else v for v in value)
        elif f.name in _SINGLE and value is not None:
            value = _build(_SINGLE[f.name], value) if isinstance(value, Mapping) else value
        elif f.name in _TUPLE_STR and value is not None:
            value = tuple(value)
        elif f.name in _PAIR and value is not None:
            value = tuple(value)
        elif f.name == "qualified_evidence" and value is not None:
            value = tuple(value)
        kwargs[f.name] = value
    return cls(**kwargs)


def episode_from_dict(data: Mapping[str, Any]) -> ScientificEpisode:
    """Rebuild a `ScientificEpisode` from `episode_to_dict` output; the round trip preserves the digest."""

    return _build(ScientificEpisode, data)


# ---------------------------------------------------------------------------------------- validation
REQUIRED_CONTEXT = ("dataset", "assay", "context")
REQUIRED_PROVENANCE = ("builder", "sources", "created_at", "data_origin")
DATA_ORIGINS = ("real", "synthetic", "mixed")


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def validate_episode(case: ScientificEpisode) -> tuple[str, ...]:
    """Named structural errors; an empty tuple means the episode satisfies the schema.

    These are contract checks, not biological judgements: they enforce that the fields that make an
    episode reusable exist and that no record claims more than its status allows.
    """

    errors: list[str] = []
    for name in ("case_id", "user_question"):
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
    origin = case.provenance.get("data_origin")
    if origin is not None and origin not in DATA_ORIGINS:
        errors.append("invalid:provenance.data_origin")
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
    if len(registered) < 2 and case.case_kind is not CaseKind.NEGATIVE:
        errors.append("missing:two_registered_hypotheses")
    known_actions = set(action_ids)
    for obs in case.initial_observations:
        if obs.availability not in ("pre_action", "outcome_only"):
            errors.append(f"invalid:observation_availability:{obs.condition_id}")
        if not isinstance(obs.status, ScientificMeasurementStatus):
            errors.append(f"invalid:observation_status:{obs.condition_id}")
            continue
        if not obs.status.biological and obs.value is not None:
            errors.append(f"value_without_biological_status:{obs.condition_id}")
        if obs.direction is not None and obs.direction not in (-1, 0, 1):
            errors.append(f"invalid:observation_direction:{obs.condition_id}")
    for m in case.real_measurements:
        if m.sampling_frame not in ("unspecified", "all_attempts", "valid_only"):
            errors.append(f"invalid:measurement_sampling_frame:{m.action_id}")
        if m.action_id not in known_actions:
            errors.append(f"measurement_for_unknown_action:{m.action_id}")
        if not isinstance(m.status, ScientificMeasurementStatus):
            errors.append(f"invalid:measurement_status:{m.action_id}")
        if m.label_kind not in ("measured_outcome", "derived_annotation_proxy"):
            errors.append(f"invalid:measurement_label_kind:{m.action_id}")
        if m.contrast is not None and (len(m.contrast) != 2 or len(set(m.contrast)) != 2):
            errors.append(f"invalid:measurement_contrast:{m.action_id}")
    for f in (*case.virtual_cell_forecasts, *case.predicted_outcome_branches):
        if f.evidence_class is not EvidenceClass.MODEL_PREDICTION:
            errors.append(f"forecast_claims_status:{f.action_id}:{f.evidence_class.value}")
        total = sum(f.branches.values()) if f.branches else 0.0
        if f.refusal is None and f.branches and abs(total - 1.0) > 1e-6:
            errors.append(f"forecast_not_normalised:{f.action_id}:{f.hypothesis_id}")
    qualified_actions = {m.action_id for m in case.real_measurements
                         if m.status is ScientificMeasurementStatus.QUALIFIED
                         and m.label_kind == "measured_outcome"}
    for card in case.qualified_evidence:
        if card.get("action_id") not in qualified_actions:
            errors.append(f"qualified_without_qualified_measurement:{card.get('action_id')}")
    for plan in case.branching_interpretation_plan:
        if plan.action_id not in known_actions:
            errors.append(f"branching_plan_for_unknown_action:{plan.action_id}")
        if _blank(plan.on_ambiguous) or _blank(plan.on_invalid):
            errors.append(f"branching_plan_incomplete:{plan.action_id}")
    status = case.final_decision.get("status")
    if status is not None and status not in DECISION_STATUSES:
        errors.append("invalid:final_decision.status")
    if case.case_kind is CaseKind.ADAPTATION:
        if not case.adaptation_map:
            errors.append("adaptation_case_without_links")
        for link in case.adaptation_map:
            if not (link.source_case and link.target_case) or link.success is None:
                errors.append("adaptation_link_incomplete")
    if case.case_kind is CaseKind.FAILURE and not case.failure_modes:
        errors.append("failure_case_without_failure_mode")
    return tuple(dict.fromkeys(errors))


# ---------------------------------------------------------------------------------------- store
class VersionConflict(Exception):
    """A supersede named a digest that is not the latest version of the case."""


class StoreCorrupt(Exception):
    """The append-only file failed its digest-chain verification."""


def _open_text(path: Path, mode: str):
    """Text opener for JSON lines. Gzip output carries no timestamp, so equal content gives an
    equal file hash; appending is only supported for plain files."""

    path = Path(path)
    if not str(path).endswith(".gz"):
        return open(path, mode.replace("t", ""), encoding="utf-8", newline="\n" if "r" not in mode else None)
    if "r" in mode:
        return gzip.open(path, "rt", encoding="utf-8")
    if "a" in mode:
        raise ValueError("append_to_gzip_unsupported")

    class _Gz(io.TextIOWrapper):
        def close(self):  # closes the underlying file too, which GzipFile would leave open
            try:
                super().close()
            finally:
                handle.close()

    handle = open(path, "wb")
    return _Gz(gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0), encoding="utf-8", newline="\n")


class EpisodeStore:
    """Append-only, digest-chained episode store. Nothing is edited in place."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._records: list[dict] = []
        self._by_case: dict[str, list[dict]] = {}
        self._snapshot_cache: dict[bool, str] = {}
        if self.path and self.path.exists():
            with _open_text(self.path, "r") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        record = json.loads(line)
                        self._records.append(record)
                        self._by_case.setdefault(record["case_id"], []).append(record)
        self.verify()

    def __len__(self) -> int:
        return len(self._records)

    def _flush(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _open_text(self.path, "w") as fh:
            for record in self._records:
                fh.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")

    def get(self, case_id: str, version: int | None = None) -> ScientificEpisode | None:
        versions = self._by_case.get(case_id, ())
        if not versions:
            return None
        if version is None:
            return episode_from_dict(versions[-1]["episode"])
        for record in versions:
            if record["version"] == version:
                return episode_from_dict(record["episode"])
        return None

    def versions(self, case_id: str) -> tuple[int, ...]:
        return tuple(r["version"] for r in self._by_case.get(case_id, ()))

    def latest(self) -> tuple[ScientificEpisode, ...]:
        return tuple(episode_from_dict(records[-1]["episode"])
                     for records in self._by_case.values())

    def _record_for(self, episode: ScientificEpisode) -> dict:
        errors = validate_episode(episode)
        if errors:
            raise ValueError("invalid_episode:" + ",".join(errors))
        known = self.versions(episode.case_id)
        if episode.case_version in known:
            raise VersionConflict(f"version {episode.case_version} of {episode.case_id} already stored")
        return {"case_id": episode.case_id, "version": episode.case_version,
                "digest": episode.digest, "episode": episode_to_dict(episode)}

    def _append_record(self, record: dict) -> None:
        self._records.append(record)
        self._by_case.setdefault(record["case_id"], []).append(record)
        self._snapshot_cache.clear()

    def append(self, episode: ScientificEpisode) -> str:
        record = self._record_for(episode)
        self._append_record(record)
        self._flush()
        return record["digest"]

    def append_many(self, episodes: Iterable[ScientificEpisode]) -> tuple[str, ...]:
        """Validate and persist a batch with one index update and one file write."""

        pending: list[dict] = []
        pending_versions: dict[str, set[int]] = {}
        for episode in episodes:
            record = self._record_for(episode)
            versions = pending_versions.setdefault(episode.case_id, set(self.versions(episode.case_id)))
            if episode.case_version in versions:
                raise VersionConflict(f"version {episode.case_version} of {episode.case_id} already stored")
            versions.add(episode.case_version)
            pending.append(record)
        for record in pending:
            self._append_record(record)
        if pending:
            self._flush()
        return tuple(record["digest"] for record in pending)

    def supersede(self, previous: ScientificEpisode, **changes) -> ScientificEpisode:
        """A new version of `previous` with `changes`; the previous record is never touched."""

        latest = self.get(previous.case_id)
        if latest is None or latest.digest != previous.digest:
            raise VersionConflict(f"{previous.case_id} is not at the stored latest digest")
        data = episode_to_dict(previous)
        data.update(changes)
        data["case_version"] = previous.case_version + 1
        data["supersedes"] = previous.digest
        episode = episode_from_dict(data)
        self.append(episode)
        return episode

    def verify(self) -> None:
        seen: dict[str, str] = {}
        for record in self._records:
            episode = record["episode"]
            if digest(episode) != record["digest"]:
                raise StoreCorrupt(f"digest mismatch for {record['case_id']} v{record['version']}")
            supersedes = episode.get("supersedes")
            if supersedes is not None and seen.get(record["case_id"]) != supersedes:
                raise StoreCorrupt(f"broken version chain for {record['case_id']}")
            seen[record["case_id"]] = record["digest"]

    def snapshot_digest(self, latest_only: bool = True) -> str:
        cached = self._snapshot_cache.get(latest_only)
        if cached is not None:
            return cached
        records = self._records
        if latest_only:
            records = sorted((items[-1] for items in self._by_case.values()),
                             key=lambda r: r["case_id"])
        text = json.dumps([r["digest"] for r in records], separators=(",", ":"))
        result = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self._snapshot_cache[latest_only] = result
        return result
