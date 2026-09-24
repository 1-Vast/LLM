"""Planning-only rendering of this round's virtual-cell queries for the agent's own reasoning.

File summary
- Path: src/agent/world_model_briefing.py
- Purpose: let the LLM side of the agent see what the virtual cell said about each
  registered action, in a form that cannot be mistaken for evidence. Before this, the
  world model only broke numeric ties in the selector and the repair planner never saw it.
- Core points:
  - One row per queried action: its readout, the predicted value and band, whether the
    band claims coverage, distribution membership, validation status, and how much the
    reliability ledger still trusts that readout; or the abstention and its reason.
  - An abstention is reported as "no supported answer", never as a null effect.
  - The heading states the boundary the controller enforces anyway: a prediction cannot
    satisfy a prerequisite, eliminate a hypothesis or replace a result.
- Interfaces: `WorldModelRow`, `world_model_rows`, `render_world_model_briefing`, `summarize_world_model`
- Depends on: maestro.models, maestro.reliability, virtual_cell.interface
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from maestro.models import EvidenceAction
from maestro.reliability import PredictionReliabilityLedger
from virtual_cell.cache import REUSE_NOTE_PREFIX
from virtual_cell.interface import PredictionRequest, QueryAssessment, StatePrediction

BRIEFING_HEADING = (
    "VIRTUAL-CELL PREDICTIONS (planning-only model output; not measured evidence)\n"
    "A prediction may inform which registered action to propose. It cannot satisfy a prerequisite, "
    "eliminate a hypothesis, or stand in for an unmeasured result. An abstention means the model has "
    "no supported answer for that action; it is not a null effect. reliability_weight is how much "
    "later real results still let this readout influence planning (1.0 until scored, 0.0 when revoked)."
)


@dataclass(frozen=True)
class WorldModelRow:
    """What the virtual cell returned for one registered action this round."""

    action: str
    intervention: str
    status: str
    readout: str | None = None
    value: float | None = None
    interval: tuple[float, float] | None = None
    interval_claims_coverage: bool | None = None
    interval_level: float | None = None
    in_distribution: bool | None = None
    validation_status: str | None = None
    model_version: str | None = None
    reliability_weight: float | None = None
    reliability_revoked: bool | None = None
    reliability_scored_pairs: int | None = None
    abstain_reason: str | None = None
    reused_from_request: str | None = None

    def as_payload(self) -> dict[str, object]:
        return {key: value for key, value in asdict(self).items() if value is not None}


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(f"{float(value):.6g}")


def _reused_from(prediction: StatePrediction) -> str | None:
    for note in prediction.limitations:
        if note.startswith(REUSE_NOTE_PREFIX):
            return note[len(REUSE_NOTE_PREFIX):].split(";", 1)[0]
    return None


def world_model_rows(
    actions: Sequence[EvidenceAction],
    requests: Mapping[str, PredictionRequest],
    assessments: Mapping[str, QueryAssessment],
    predictions: Mapping[str, StatePrediction],
    reliability: PredictionReliabilityLedger | None = None,
) -> tuple[WorldModelRow, ...]:
    """One row per registered action that was queried, in catalogue order."""

    rows: list[WorldModelRow] = []
    for action in actions:
        request = requests.get(action.identifier)
        if request is None:
            continue
        prediction = predictions.get(action.identifier)
        assessment = assessments.get(action.identifier)
        readout = action.prediction_readout or (request.readouts[0] if len(request.readouts) == 1 else None)
        validation = assessment.validation_status.value if assessment is not None else None
        if prediction is None or not prediction.applicable:
            rows.append(
                WorldModelRow(
                    action=action.identifier,
                    intervention=request.intervention.identifier,
                    status="abstained",
                    readout=readout,
                    validation_status=validation,
                    model_version=request.model_version,
                    abstain_reason=(prediction.abstain_reason if prediction is not None else None) or "not_answered",
                )
            )
            continue
        value = _number(prediction.state_change.get(readout)) if readout and prediction.state_change else None
        band = prediction.interval_for(readout) if readout else None
        interval = None
        if band is not None and _number(band.low) is not None and _number(band.high) is not None:
            interval = (_number(band.low), _number(band.high))
        summary = None
        if reliability is not None and readout:
            summary = reliability.summarize(
                prediction.model_version or request.model_version, readout, request.context.identifier
            )
        rows.append(
            WorldModelRow(
                action=action.identifier,
                intervention=request.intervention.identifier,
                status="predicted",
                readout=readout,
                value=value,
                interval=interval,
                interval_claims_coverage=band.claims_coverage if band is not None else None,
                interval_level=_number(band.level) if band is not None and band.claims_coverage else None,
                in_distribution=prediction.in_distribution,
                validation_status=validation,
                model_version=prediction.model_version,
                reliability_weight=_number(summary.weight) if summary is not None else None,
                reliability_revoked=summary.revoked if summary is not None else None,
                reliability_scored_pairs=summary.scored if summary is not None else None,
                reused_from_request=_reused_from(prediction),
            )
        )
    return tuple(rows)


def render_world_model_briefing(rows: Sequence[WorldModelRow], *, max_rows: int = 24) -> str:
    """The labelled prompt section, or an empty string when nothing was queried."""

    if not rows:
        return ""
    shown = list(rows)[:max_rows]
    lines = [BRIEFING_HEADING]
    lines.extend(json.dumps(row.as_payload(), ensure_ascii=True, allow_nan=False, sort_keys=True) for row in shown)
    if len(rows) > len(shown):
        lines.append(f"({len(rows) - len(shown)} further queried action(s) omitted for context budget.)")
    return "\n".join(lines)


def summarize_world_model(rows: Sequence[WorldModelRow]) -> str:
    """One sentence for the user-facing turn response."""

    if not rows:
        return ""
    predicted = [row for row in rows if row.status == "predicted"]
    abstained = [row for row in rows if row.status != "predicted"]
    reused = sum(1 for row in predicted if row.reused_from_request)
    parts = [f"{len(predicted)} of {len(rows)} action queries answered"]
    if reused:
        parts.append(f"{reused} reused from an identical earlier query")
    if abstained:
        reasons = sorted({row.abstain_reason or "not_answered" for row in abstained})
        parts.append("abstained on " + ", ".join(row.action for row in abstained) + " (" + "; ".join(reasons) + ")")
    return " Virtual cell: " + "; ".join(parts) + ". Predictions are planning-only and were not used as evidence."
