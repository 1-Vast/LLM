"""The four-layer round: structured handoffs instead of prose between layers.

File summary
- Path: src/maestro/handoff.py
- Purpose: make report section 30 executable — evidence, world model, decision and
  execution exchange structured records, three fields are mandatory
  (``in_distribution``, ``rejected[]``, ``contradiction_flag``), and a round that
  omits one is refused rather than written.
- Core points:
  - A round is a file, not a function call: every layer's output is a record with
    named fields, so a later reader can audit it and a run can be re-scored offline.
  - ``rejected[]`` carries a reason per rejected candidate. Without it, an improvement
    cannot be attributed to new information, to the model, or to the selection rule.
  - ``contradiction_flag`` records whether a result removed a hypothesis the round
    entered with. A run in which it is never set has never revised a judgement, and
    ``review_run`` reports that as a finding rather than as a healthy trace.
  - Nothing here is evidence: a world-model record is a prediction, and its mandatory
    fields exist so that a decision layer cannot read it as a measurement.
- Interfaces: `ComparabilityStatus`, `EvidenceLayer`, `WorldModelLayer`, `DecisionLayer`,
  `ExecutionLayer`, `RejectedCandidate`, `RoundRecord`, `write_round`, `read_round`,
  `review_run`
- Depends on: (standard library only)
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .tool_contracts import json_loads


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
