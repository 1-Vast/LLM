"""Evidence provenance, immutable public policy inputs, JSON contracts, and round records."""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .models import EvidenceAction


TOOL_SCHEMA_VERSION = "1.0"


def json_value(value: Any, *, depth: int = 0) -> Any:
    """Copy strict JSON values without non-finite numbers, non-string keys or coercion."""
    if depth > 64:
        raise ValueError("JSON nesting exceeds 64 levels.")
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise ValueError("JSON object keys must be strings.")
        return {key: json_value(item, depth=depth + 1) for key, item in value.items()}
    if type(value) is list:
        return [json_value(item, depth=depth + 1) for item in value]
    raise ValueError("Expected strict JSON; non-finite numbers and non-JSON objects are forbidden.")


def json_dumps(value: Any) -> str:
    return json.dumps(json_value(value), ensure_ascii=True, sort_keys=True, allow_nan=False, separators=(",", ":"))


def json_loads(text: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value: str) -> None:
        raise ValueError(f"Non-finite JSON number: {value}")

    return json_value(json.loads(text, object_pairs_hook=pairs, parse_constant=constant))


def nonnegative_number(value: Any, field: str) -> float:
    try:
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError
        return float(value)
    except (ValueError, OverflowError):
        raise ValueError(f"{field} must be a finite non-negative number, not bool.") from None


def string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(type(item) is not str or not item.strip() for item in value):
        raise ValueError(f"{field} must be an array of nonempty strings.")
    return list(value)


def object_fields(value: Any, required: set[str], optional: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object.")
    if required - value.keys():
        raise ValueError(f"{field} missing fields: {sorted(required - value.keys())}")
    if value.keys() - required - optional:
        raise ValueError(f"{field} unknown fields: {sorted(value.keys() - required - optional)}")
    return value


def nonempty_string(value: Any, field: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field} must be a nonempty string.")
    return value


_TYPES = {"object", "array", "string", "number", "integer", "boolean", "null"}
_KEYWORDS = {"type", "properties", "required", "additionalProperties", "items", "enum", "minimum", "maximum",
             "minItems", "maxItems", "minLength", "maxLength", "description", "default"}


def check_schema(schema: Any) -> None:
    """Validate the supported schema subset, rejecting unknown keywords and references."""
    schema = json_value(schema)
    if not isinstance(schema, dict) or set(schema) - _KEYWORDS:
        raise ValueError("Unknown schema keyword or invalid schema object.")
    types = schema.get("type")
    types = [types] if isinstance(types, str) else types
    if not isinstance(types, list) or not types or any(type(item) is not str or item not in _TYPES for item in types):
        raise ValueError("Unknown schema type.")
    if len(types) != len(set(types)):
        raise ValueError("Duplicate schema type.")
    if "description" in schema:
        nonempty_string(schema["description"], "schema.description")
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        raise ValueError("Schema enum must be a nonempty array.")
    if set(schema) & {"properties", "required", "additionalProperties"}:
        if "object" not in types or schema.get("additionalProperties", False) is not False:
            raise ValueError("Object schemas must reject additional properties.")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise ValueError("Schema properties must be an object.")
        required = string_list(schema.get("required", []), "schema.required")
        if len(required) != len(set(required)) or set(required) - properties.keys():
            raise ValueError("Invalid schema required fields.")
        for child in properties.values():
            check_schema(child)
    if "array" in types:
        if "items" not in schema:
            raise ValueError("Array schema requires items.")
        check_schema(schema["items"])
    elif "items" in schema:
        raise ValueError("items requires array type.")
    for low, high, applicable in (("minimum", "maximum", {"number", "integer"}),
                                  ("minItems", "maxItems", {"array"}),
                                  ("minLength", "maxLength", {"string"})):
        for key in (low, high):
            if key not in schema:
                continue
            value = schema[key]
            if not set(types) & applicable or type(value) not in (int, float):
                raise ValueError(f"Invalid schema bound: {key}")
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise ValueError(f"Non-finite schema bound: {key}")
            if low != "minimum" and (type(value) is not int or value < 0):
                raise ValueError(f"Invalid schema length: {key}")
        if low in schema and high in schema and schema[low] > schema[high]:
            raise ValueError("Schema lower bound exceeds upper bound.")
    if "default" in schema:
        validate_schema(schema["default"], schema, "schema.default")


def validate_schema(value: Any, schema: Mapping[str, Any], field: str = "arguments") -> None:
    """Validate strict JSON against a checked schema; booleans are not numeric values."""
    value = json_value(value)
    types = schema["type"]
    types = [types] if isinstance(types, str) else types
    matches = {"object": isinstance(value, dict), "array": type(value) is list, "string": type(value) is str,
               "number": type(value) in (int, float), "integer": type(value) is int,
               "boolean": type(value) is bool, "null": value is None}
    if not any(matches[kind] for kind in types):
        raise ValueError(f"{field} does not match schema type {types}.")
    if "enum" in schema and json_dumps(value) not in {json_dumps(item) for item in schema["enum"]}:
        raise ValueError(f"{field} does not match schema enum.")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        object_fields(value, set(schema.get("required", [])), set(properties), field)
        for key, item in value.items():
            validate_schema(item, properties[key], f"{field}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_schema(item, schema["items"], f"{field}[{index}]")
    for key, actual, is_lower in (("minimum", value, True), ("maximum", value, False),
                                  ("minItems", len(value) if isinstance(value, list) else None, True),
                                  ("maxItems", len(value) if isinstance(value, list) else None, False),
                                  ("minLength", len(value) if isinstance(value, str) else None, True),
                                  ("maxLength", len(value) if isinstance(value, str) else None, False)):
        if key not in schema or actual is None:
            continue
        if key in ("minimum", "maximum") and type(value) not in (int, float):
            continue
        if (is_lower and actual < schema[key]) or (not is_lower and actual > schema[key]):
            raise ValueError(f"{field} violates schema {key}.")


@dataclass(frozen=True)
class SourceCluster:
    """One original experiment and the identifiers that refer to it."""

    cluster_id: str
    source_ids: frozenset[str]
    note: str = ""


class SourceClusterIndex:
    """Map any source identifier to the cluster that counts as one unit of evidence."""

    def __init__(self, clusters: Iterable[SourceCluster] = ()):
        self._clusters: dict[str, SourceCluster] = {}
        self._lookup: dict[str, str] = {}
        for cluster in clusters:
            self.register(cluster)

    def register(self, cluster: SourceCluster) -> SourceCluster:
        if not cluster.cluster_id.strip():
            raise ValueError("cluster_id is required.")
        self._clusters[cluster.cluster_id] = cluster
        for source_id in cluster.source_ids:
            self._lookup[source_id] = cluster.cluster_id
        self._lookup.setdefault(cluster.cluster_id, cluster.cluster_id)
        return cluster

    def cluster_of(self, source_id: str) -> str:
        return self._lookup.get(source_id, source_id)

    def independent(self, source_ids: Iterable[str]) -> frozenset[str]:
        return frozenset(self.cluster_of(item) for item in source_ids if item)

    def count_independent(self, source_ids: Iterable[str]) -> int:
        return len(self.independent(source_ids))

    def is_registered(self, source_id: str) -> bool:
        """Whether a registered cluster names this source (or is this source)."""

        return source_id in self._lookup

    def independence(self, source_ids: Iterable[str]) -> dict[str, frozenset[str]]:
        """Registered clusters and sources whose dependence is unknown, kept apart.

        Two citations of one experiment that nobody registered are two unknown-dependence
        sources, not two independent clusters; only registered clusters count as independent.
        """

        ids = [item for item in source_ids if item]
        return {"independent_clusters": frozenset(self.cluster_of(item) for item in ids if self.is_registered(item)),
                "dependence_unknown": frozenset(item for item in ids if not self.is_registered(item))}

    @property
    def clusters(self) -> tuple[SourceCluster, ...]:
        return tuple(self._clusters.values())

    def cluster_members(self, cluster_id: str) -> frozenset[str]:
        cluster = self._clusters.get(cluster_id)
        return cluster.source_ids if cluster else frozenset()


def build_index(clusters: Sequence[Mapping[str, object]]) -> SourceClusterIndex:
    """Build an index from plain mappings such as parsed JSON or a manifest."""

    index = SourceClusterIndex()
    for entry in clusters:
        identifier = entry.get("cluster_id")
        sources = entry.get("source_ids") or ()
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("Each cluster mapping requires a non-empty cluster_id.")
        index.register(
            SourceCluster(
                cluster_id=identifier.strip(),
                source_ids=frozenset(str(item) for item in sources if str(item)),
                note=str(entry.get("note", "")),
            )
        )
    return index


_HIDDEN_FIELDS = frozenset({
    "truth", "hidden_truth", "ground_truth", "groundtruth", "heldout", "held_out",
    "klass", "mechanism", "annotation", "annotations", "mechanism_annotation",
    "mechanism_class", "mechanism_label", "evaluator", "future_outcome",
    "future_action_outcome", "outcome_truth", "truth_label", "heldout_profile",
    "data", "conditions", "shift", "compounds", "index", "outcomes",
})


def _forbidden_fields(value, path: str = "$") -> list[str]:
    """Reject evaluator-only keys even when callers construct PolicyInput directly."""

    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            name = str(key).strip().lower()
            if name in _HIDDEN_FIELDS:
                problems.append(f"{path}.{key}: evaluator-only field")
            problems.extend(_forbidden_fields(nested, f"{path}.{key}"))
    elif isinstance(value, (tuple, list)):
        for index, nested in enumerate(value):
            problems.extend(_forbidden_fields(nested, f"{path}[{index}]"))
    elif hasattr(value, "__dict__"):
        for key, nested in vars(value).items():
            if str(key).strip().lower() in _HIDDEN_FIELDS:
                problems.append(f"{path}.{key}: evaluator-only field")
            if isinstance(nested, (Mapping, tuple, list)):
                problems.extend(_forbidden_fields(nested, f"{path}.{key}"))
    return problems


def _freeze_value(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_value(nested) for key, nested in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType({key: _freeze_value(nested) for key, nested in value.items()})


@dataclass(frozen=True)
class PolicyInput:
    """The complete public state an acquisition policy is allowed to inspect."""

    visible_evidence: tuple[Any, ...] = ()
    legal_actions: tuple[EvidenceAction, ...] = ()
    budget: float = 0.0
    calibrated_action_distributions: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        evidence = ((self.visible_evidence,) if isinstance(self.visible_evidence, Mapping)
                    else tuple(self.visible_evidence))
        problems = _forbidden_fields(evidence, "$.visible_evidence")
        problems.extend(_forbidden_fields(self.calibrated_action_distributions, "$.calibrated"))
        problems.extend(_forbidden_fields(self.provenance, "$.provenance"))
        if problems:
            raise ValueError("; ".join(problems))
        if (isinstance(self.budget, bool) or not isinstance(self.budget, (int, float))
                or not math.isfinite(float(self.budget)) or self.budget < 0):
            raise ValueError("policy budget must be a finite nonnegative number")
        if not all(isinstance(action, EvidenceAction) for action in self.legal_actions):
            raise TypeError("legal_actions must contain EvidenceAction values")
        identifiers = {action.identifier for action in self.legal_actions}
        distributions = {
            str(identifier): _freeze_mapping(values)
            for identifier, values in self.calibrated_action_distributions.items()
        }
        unknown = set(distributions) - identifiers
        if unknown:
            raise ValueError(f"predictions supplied for non-legal actions: {sorted(unknown)}")
        for action_identifier, distribution in distributions.items():
            if any(isinstance(value, bool) or not isinstance(value, (int, float))
                   or not math.isfinite(float(value)) or float(value) < 0
                   for value in distribution.values()):
                raise ValueError(f"invalid calibrated distribution: {action_identifier}")
        if any(not isinstance(key, str) or not key.strip() for key in self.provenance):
            raise ValueError("policy provenance keys must be nonempty strings")
        object.__setattr__(self, "visible_evidence", tuple(_freeze_value(item) for item in evidence))
        object.__setattr__(self, "legal_actions", tuple(self.legal_actions))
        object.__setattr__(self, "calibrated_action_distributions", MappingProxyType(distributions))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))

    @property
    def action_ids(self) -> tuple[str, ...]:
        return tuple(action.identifier for action in self.legal_actions)

    def distribution_for(self, action_identifier: str) -> Mapping[str, float] | None:
        return self.calibrated_action_distributions.get(action_identifier)


def make_policy_input(
    *,
    visible_evidence: Sequence[Any] = (),
    legal_actions: Sequence[EvidenceAction] = (),
    budget: float,
    calibrated_action_distributions: Mapping[str, Mapping[str, float]] | None = None,
    provenance: Mapping[str, str] | None = None,
) -> PolicyInput:
    """Build a policy input without accepting an evaluator or raw-data object."""

    return PolicyInput(
        visible_evidence=tuple(visible_evidence),
        legal_actions=tuple(legal_actions),
        budget=budget,
        calibrated_action_distributions=calibrated_action_distributions or {},
        provenance=provenance or {},
    )


def _finite(value: object) -> bool:
    return type(value) in (int, float) and isfinite(value)


class ComparabilityStatus(str, Enum):
    """Whether the evidence the round starts from is comparable at all."""

    COMPARABLE = "comparable"
    CONDITION_MISMATCH = "condition_mismatch"
    MODE_UNMATCHED = "mode_unmatched"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EvidenceLayer:
    """L1: what is known, what conflicts, and whether it can be compared yet."""

    records: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    comparability_status: ComparabilityStatus = ComparabilityStatus.UNKNOWN
    missing_reason: tuple[str, ...] = ()

    def problems(self) -> tuple[str, ...]:
        issues: list[str] = []
        if self.comparability_status is ComparabilityStatus.UNKNOWN and not self.missing_reason:
            issues.append("l1_comparability_unknown_without_reason")
        if self.comparability_status is ComparabilityStatus.CONDITION_MISMATCH and not self.missing_reason:
            issues.append("l1_condition_mismatch_without_missing_reason")
        return tuple(issues)


@dataclass(frozen=True)
class WorldModelLayer:
    """L2: a prediction with its applicability, never a measurement.

    ``in_distribution`` is mandatory even when no model ran, because the decision
    layer's reranking rule reads it: a round that omits it makes "the model said a
    strong response" indistinguishable from "the model guessed".
    """

    in_distribution: bool | None
    model_id: str | None = None
    mean: float | None = None
    interval: tuple[float, float] | None = None
    abstain_reason: str | None = None
    validation_status: str = "unknown"
    readout: str | None = None

    @classmethod
    def no_model(cls, reason: str = "no_world_model_registered") -> "WorldModelLayer":
        """The record a round writes when no model answered, declared rather than omitted."""

        return cls(in_distribution=False, model_id=None, abstain_reason=reason)

    def problems(self) -> tuple[str, ...]:
        issues: list[str] = []
        if self.in_distribution is None:
            issues.append("l2_in_distribution_missing")
        elif type(self.in_distribution) is not bool:
            issues.append("l2_in_distribution_not_boolean")
        if self.mean is not None and not _finite(self.mean):
            issues.append("l2_mean_not_finite")
        if self.interval is not None and (
            len(self.interval) != 2 or not all(_finite(value) for value in self.interval)
        ):
            return tuple(issues + ["l2_invalid_interval"])
        if self.interval is not None and self.interval[0] > self.interval[1]:
            issues.append("l2_interval_inverted")
        if self.in_distribution and self.mean is None:
            issues.append("l2_in_distribution_without_mean")
        if self.in_distribution is False and not self.abstain_reason:
            issues.append("l2_abstention_without_reason")
        if self.abstain_reason and (self.mean is not None or self.interval is not None):
            issues.append("l2_abstention_contains_prediction")
        return tuple(issues)


@dataclass(frozen=True)
class RejectedCandidate:
    """One candidate the decision layer did not choose, with the reason."""

    action_identifier: str
    reason: str


@dataclass(frozen=True)
class DecisionLayer:
    """L3: what was chosen, what was rejected and why, and whether the round defers."""

    chosen: tuple[str, ...] = ()
    rejected: tuple[RejectedCandidate, ...] = ()
    rationale: str = ""
    registered_predictions: Mapping[str, float] = field(default_factory=dict)
    defer_flag: bool = False

    def problems(self) -> tuple[str, ...]:
        issues: list[str] = []
        if not isinstance(self.rejected, (tuple, list)):
            return ("l3_rejected_missing_or_invalid",)
        if any(not _finite(value) for value in self.registered_predictions.values()):
            issues.append("l3_prediction_not_finite")
        if self.chosen and not self.rationale.strip():
            issues.append("l3_chosen_without_rationale")
        if self.defer_flag and self.chosen:
            issues.append("l3_defer_with_execution")
        for candidate in self.rejected:
            if not candidate.reason.strip():
                issues.append(f"l3_rejected_without_reason:{candidate.action_identifier}")
            if candidate.action_identifier in self.chosen:
                issues.append(f"l3_rejected_and_chosen:{candidate.action_identifier}")
        return tuple(issues)


@dataclass(frozen=True)
class ExecutionLayer:
    """L4: what a real result changed, and whether it removed an entered hypothesis.

    ``contradiction_flag`` is the narrower, checkable reading of "the new result
    opposes the previous explanation": a hypothesis the round began with is no longer
    compatible. A probability shift that leaves the compatible set unchanged does not
    set it, and that is deliberate — this flag exists to detect a system that never
    revises, not to score how strongly it revised.
    """

    observed: Mapping[str, float] = field(default_factory=dict)
    belief_delta: Mapping[str, float] = field(default_factory=dict)
    contradiction_flag: bool = False
    stop_decision: str | None = None
    result_id: str | None = None

    def problems(self) -> tuple[str, ...]:
        issues: list[str] = []
        if type(self.contradiction_flag) is not bool:
            issues.append("l4_contradiction_flag_missing_or_invalid")
        if any(not _finite(value) for value in (*self.observed.values(), *self.belief_delta.values())):
            issues.append("l4_nonfinite_value")
        if self.contradiction_flag and not self.belief_delta:
            issues.append("l4_contradiction_without_belief_delta")
        if self.observed and not self.result_id:
            issues.append("l4_observation_without_result_id")
        return tuple(issues)


@dataclass(frozen=True)
class RoundRecord:
    """One complete traversal of evidence -> world model -> decision -> execution."""

    session_id: str
    round_index: int
    evidence: EvidenceLayer
    world_model: WorldModelLayer
    decision: DecisionLayer
    execution: ExecutionLayer

    def problems(self) -> tuple[str, ...]:
        return (
            *self.evidence.problems(),
            *self.world_model.problems(),
            *self.decision.problems(),
            *self.execution.problems(),
        )

    def validate(self) -> "RoundRecord":
        """Refuse an incomplete round instead of writing one that reads as complete."""

        issues = self.problems()
        if issues:
            raise ValueError("Round record is not writable: " + ", ".join(issues))
        return self

    def to_payload(self) -> Mapping[str, object]:
        self.validate()
        return {
            "schema": "maestro.round.v1",
            "session_id": self.session_id,
            "round_index": self.round_index,
            "layers": {
                "L1_evidence": {
                    "records": list(self.evidence.records),
                    "conflicts": list(self.evidence.conflicts),
                    "comparability_status": self.evidence.comparability_status.value,
                    "missing_reason": list(self.evidence.missing_reason),
                },
                "L2_world_model": {
                    "model_id": self.world_model.model_id,
                    "mean": self.world_model.mean,
                    "interval": list(self.world_model.interval) if self.world_model.interval else None,
                    "in_distribution": self.world_model.in_distribution,
                    "abstain_reason": self.world_model.abstain_reason,
                    "validation_status": self.world_model.validation_status,
                    "readout": self.world_model.readout,
                },
                "L3_decision": {
                    "chosen": list(self.decision.chosen),
                    "rejected": [
                        {"action": item.action_identifier, "reason": item.reason}
                        for item in self.decision.rejected
                    ],
                    "rationale": self.decision.rationale,
                    "registered_predictions": dict(sorted(self.decision.registered_predictions.items())),
                    "defer_flag": self.decision.defer_flag,
                },
                "L4_execution": {
                    "result_id": self.execution.result_id,
                    "observed": dict(sorted(self.execution.observed.items())),
                    "belief_delta": dict(sorted(self.execution.belief_delta.items())),
                    "contradiction_flag": self.execution.contradiction_flag,
                    "stop_decision": self.execution.stop_decision,
                },
            },
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "RoundRecord":
        """Require the three safety fields on disk; defaults never repair omissions."""
        try:
            if payload["schema"] != "maestro.round.v1":
                raise ValueError("unknown_round_schema")
            layers = payload["layers"]
            evidence = dict(layers["L1_evidence"])
            world = dict(layers["L2_world_model"])
            decision = dict(layers["L3_decision"])
            execution = dict(layers["L4_execution"])
            for layer, name in ((world, "in_distribution"), (decision, "rejected"), (execution, "contradiction_flag")):
                if name not in layer:
                    raise ValueError(f"mandatory_field_missing:{name}")
            if not isinstance(decision["rejected"], list):
                raise ValueError("invalid_rejected_array")
            evidence["comparability_status"] = ComparabilityStatus(evidence["comparability_status"])
            decision["rejected"] = tuple(
                RejectedCandidate(item["action"], item["reason"]) for item in decision["rejected"]
            )
            return cls(payload["session_id"], payload["round_index"], EvidenceLayer(**evidence),
                       WorldModelLayer(**world), DecisionLayer(**decision), ExecutionLayer(**execution)).validate()
        except (KeyError, TypeError, AttributeError) as error:
            raise ValueError(f"invalid_round_record:{error}") from error


def write_round(path: Path | str, record: RoundRecord) -> str:
    """Validate, write and return the SHA-256 of one round record."""

    record.validate()
    encoded = (json.dumps(record.to_payload(), indent=1, ensure_ascii=True, sort_keys=False, allow_nan=False) + "\n").encode("utf-8")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()


def read_round(path: Path | str) -> Mapping[str, object]:
    payload = json_loads(Path(path).read_text(encoding="utf-8"))
    RoundRecord.from_payload(payload)
    return payload


def review_run(records: Sequence[RoundRecord]) -> Mapping[str, object]:
    """Report the two run-level findings a per-round validator cannot see."""

    rounds = len(records)
    revisions = [record.round_index for record in records if record.execution.contradiction_flag]
    executed = [record.round_index for record in records if record.execution.observed]
    return {
        "rounds": rounds,
        "rounds_with_a_result": len(executed),
        "rounds_that_revised_a_judgement": len(revisions),
        "judgement_never_changed": bool(records) and not revisions and bool(executed),
        "reading": (
            "A run that imported results and never set contradiction_flag has never removed a hypothesis it "
            "entered with; that is a finding about the run, not a clean trace."
        ),
    }


def rejected_from_selection(
    available: Iterable[str],
    chosen: Iterable[str],
    *,
    waiting: Sequence[str] = (),
    budget_exceeded: Sequence[str] = (),
    adds_no_coverage: Sequence[str] = (),
    reason_overrides: Mapping[str, str] | None = None,
) -> tuple[RejectedCandidate, ...]:
    """Name a reason for every candidate the decision layer did not choose.

    The reasons come from the selector's own outputs rather than from a generic
    "not selected", because the difference between a blocked candidate and an
    unaffordable one is what a reader needs in order to challenge the choice.
    """

    selected = set(chosen)
    reasons: dict[str, str] = {}
    for entry in waiting:
        identifier, _, detail = str(entry).partition(": ")
        reasons[identifier] = f"waiting_for_prerequisite:{detail}" if detail else "waiting_for_prerequisite"
    for identifier in budget_exceeded:
        reasons[str(identifier)] = "exceeds_budget"
    for identifier in adds_no_coverage:
        reasons[str(identifier)] = "adds_no_coverage"
    reasons.update({str(key): str(value) for key, value in (reason_overrides or {}).items()})
    rejected: list[RejectedCandidate] = []
    for identifier in available:
        name = str(identifier)
        if name in selected:
            continue
        rejected.append(RejectedCandidate(name, reasons.get(name, "not_selected_by_selector")))
    return tuple(rejected)
