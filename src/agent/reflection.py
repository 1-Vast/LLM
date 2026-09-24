"""Deterministic post-observation reflections that retain evidence boundaries.

File summary
- Path: src/agent/reflection.py
- Purpose: Classify a result after observation without over-claiming what it supports.
- Core points:
  - `reflect_on_result` classifies execution state without a mechanism verdict.
  - A failed or non-measurement record is not a real measurement result and never updates the contrast.
- Interfaces: `reflect_on_result`, `ReflectionRecord`
- Depends on: agent.cases
"""
from __future__ import annotations

from dataclasses import dataclass

from .cases import MeasurementResult


@dataclass(frozen=True)
class ReflectionRecord:
    """A post-observation reflection pairing an outcome class with a bounded next step."""

    case_id: str
    action_identifier: str
    result_id: str
    outcome_class: str
    next_step: str
    limitations: tuple[str, ...]

    def render(self) -> str:
        return (
            f"Post-observation reflection for action '{self.action_identifier}': "
            f"outcome_class={self.outcome_class}; next_step={self.next_step}; "
            f"limitations={'; '.join(self.limitations) or 'none'}."
        )


def reflect_on_result(case_id: str, result_id: str, result: MeasurementResult) -> ReflectionRecord:
    """Classify execution state without promoting a result to a mechanism verdict."""

    if not result.quality_passed:
        outcome_class = "record_quality_failed"
        next_step = "Do not use this record to update the mechanism contrast; obtain a qualified replacement result."
    elif result.evidence_kind.value != "real_measurement":
        outcome_class = "non_measurement_record_received"
        next_step = "Retain source limitations; use only the record's declared interpretation fields."
    elif not result.interpretation_fields:
        outcome_class = "measurement_without_interpretation_premise"
        next_step = "Keep the result as evidence, but do not unlock a prerequisite or mechanism update."
    else:
        outcome_class = "qualified_result_received"
        next_step = "Replan using only the explicit interpretation fields and remaining registered actions."
    return ReflectionRecord(
        case_id=case_id,
        action_identifier=result.action_identifier,
        result_id=result_id,
        outcome_class=outcome_class,
        next_step=next_step,
        limitations=result.limitations,
    )
