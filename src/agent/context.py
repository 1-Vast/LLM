"""Task interpretation and bounded context, including planning-only model briefings."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any, Mapping, Sequence, TYPE_CHECKING
from .knowledge import BiologicalConditions, EvidenceLedger, EvidenceRecord, status_for_kind
from .memory import MemoryEntry, MemoryKind, MemoryScope, MemoryStore
import math
from maestro.models import EvidenceAction
from maestro.judgment import PredictionReliabilityLedger
from virtual_cell.interface import REUSE_NOTE_PREFIX
from virtual_cell.interface import PredictionRequest, QueryAssessment, StatePrediction
from .llm import JsonCompleter


if TYPE_CHECKING:
    from .case_store import MeasurementResult
    from .tool_runtime import ToolExecution
    from .llm import VisualInspection
@dataclass(frozen=True)
class TaskIntent:
    """Structured extraction of a user request, with explicit missing-information fields."""

    task_type: str
    research_question: str
    target_or_targets: tuple[str, ...]
    interventions: tuple[str, ...]
    biological_context: str | None
    phenotype_endpoint: str | None
    supplied_evidence: tuple[str, ...]
    constraints: tuple[str, ...]
    missing_information: tuple[str, ...]
    needs_visual_review: bool
    evidence_gaps: tuple[str, ...] = ()

    @property
    def requires_clarification(self) -> bool:
        """Only a missing *task* field blocks planning; a missing measurement does not.

        The distinction used to rest on prompt wording, so a cautious model
        could stop the whole loop by listing the very measurements the
        registered evidence menu exists to acquire. ``missing_information`` is
        now a closed vocabulary of task fields, validated after the call, and
        anything else the model reports becomes an evidence gap that planning
        must address rather than a reason to refuse to plan.
        """

        return bool(self.missing_information)


@dataclass(frozen=True)
class ContextPacket:
    """A bounded, provenance-preserving context packet handed to the planner."""

    intent: TaskIntent
    evidence: tuple[EvidenceRecord, ...]
    memories: tuple[MemoryEntry, ...]
    rendered: str
    visual_reviews: tuple[str, ...] = ()
    included_record_ids: tuple[str, ...] = ()
    omitted_record_ids: tuple[str, ...] = ()
    omission_reasons: tuple[str, ...] = ()
    budget_error: str | None = None


class TaskInterpreter:
    """Uses structured LLM output to extract a task without silently filling gaps."""

    def __init__(self, client: JsonCompleter):
        self._client = client

    def interpret(self, user_message: str) -> TaskIntent:
        prompt = """You are MAESTRO's scientific task triage component. Return JSON only.
Extract the request without inventing experimental facts. Separate explicitly supplied
evidence from requested work. If mechanism diagnosis lacks a critical
field, name it in missing_information using ONLY these words: target, intervention,
biological_context, phenotype_endpoint, existing_observation. Any other gap belongs in
evidence_gaps, which describes measurements the registered evidence menu could acquire;
an absent target engagement, comparator result, dose, exposure duration, or residual
activity is an evidence gap, never missing task information. Mark needs_visual_review
true only when an attached figure, microscopy image, plot, gel, pathology image, or
other visual asset is necessary. Use this exact object shape:
{
  \"task_type\": \"mechanism_diagnosis|evidence_review|analysis_planning|other\",
  \"research_question\": \"...\",
  \"target_or_targets\": [\"...\"], \"interventions\": [\"...\"],
  \"biological_context\": null, \"phenotype_endpoint\": null,
  \"supplied_evidence\": [\"...\"], \"constraints\": [\"...\"],
  \"missing_information\": [\"...\"], \"evidence_gaps\": [\"...\"],
  \"needs_visual_review\": false
}"""
        result, _ = self._client.complete_json(
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
            ]
        )
        return TaskIntent(
            task_type=_required_text(result, "task_type"),
            research_question=_required_text(result, "research_question"),
            target_or_targets=_string_tuple(result.get("target_or_targets")),
            interventions=_string_tuple(result.get("interventions")),
            biological_context=_optional_text(result.get("biological_context")),
            phenotype_endpoint=_optional_text(result.get("phenotype_endpoint")),
            supplied_evidence=_string_tuple(result.get("supplied_evidence")),
            constraints=_string_tuple(result.get("constraints")),
            missing_information=_task_fields(result.get("missing_information")),
            evidence_gaps=_string_tuple(result.get("evidence_gaps"))
            + _non_task_fields(result.get("missing_information")),
            needs_visual_review=bool(result.get("needs_visual_review", False)),
        )


class ContextBuilder:
    """Creates a bounded, provenance-preserving context instead of replaying all history."""

    def __init__(self, evidence: EvidenceLedger, memory: MemoryStore, *, max_characters: int = 12_000):
        self._evidence = evidence
        self._memory = memory
        self._max_characters = max_characters

    def build(self, intent: TaskIntent, *, memory_scope: MemoryScope | None = None,
              biological_conditions: BiologicalConditions | None = None) -> ContextPacket:
        query = " ".join(
            part
            for part in (
                intent.research_question,
                " ".join(intent.target_or_targets),
                " ".join(intent.interventions),
                intent.biological_context or "",
            )
            if part
        )
        entities = _intent_entities(intent)
        conditions = biological_conditions or BiologicalConditions(context=intent.biological_context)
        evidence = self._evidence.retrieve(query, entities=entities, scope=memory_scope,
                                          biological_conditions=conditions)
        memories = self._memory.search(
            query, kinds=(MemoryKind.EPISODIC, MemoryKind.SEMANTIC), scope=memory_scope
        )
        return self._packet(intent, evidence, memories)

    def source_groups(self, source_ids: Sequence[str]) -> dict[str, str]:
        """Resolve registered source aliases without treating unknown sources as verified."""
        groups = {}
        for identifier in source_ids:
            source = self._evidence.get_source(identifier)
            groups[identifier] = source.cluster if source is not None else identifier
        return groups

    def add_visual_reviews(
        self,
        packet: ContextPacket,
        reviews: Sequence["VisualInspection"],
    ) -> ContextPacket:
        """Expose visual observations to planning while preserving their non-evidence status."""

        summaries = tuple(
            f"{review.path.name}: observations={'; '.join(review.observations) or 'none'}; "
            f"relevance={review.decision_relevance}; "
            f"limitations={'; '.join(review.limitations) or 'none'}"
            for review in reviews
        )
        if not summaries:
            return packet
        return self._packet(packet.intent, packet.evidence, packet.memories, visual_reviews=summaries)

    def add_tool_execution(self, packet: ContextPacket, execution: "ToolExecution") -> ContextPacket:
        """Persist dataset observations with provenance, then expose their limits to the planner."""

        source = f"tool:{execution.tool_id}:{execution.dataset_path.name}"
        limitations = "; ".join(execution.limitations) or "No limitations supplied by the tool."
        records = (
            self._evidence.add_evidence(
                "\n".join(execution.observations) or "Structured tool result; see payload.",
                source=source,
                context=(
                    f"Dataset-derived observation from {execution.dataset_path.name}; "
                    f"selection rationale: {execution.rationale}; limitations: {limitations}"
                ),
                status=status_for_kind(execution.evidence_kind),
                evidence_kind=execution.evidence_kind,
                payload={"tool_payload": dict(execution.payload),
                         "receipt": execution.to_dict().get("receipt")},
            ),
        )
        return self._packet(
            packet.intent,
            records + packet.evidence,
            packet.memories,
            visual_reviews=packet.visual_reviews,
        )

    def record_result(self, result: "MeasurementResult", *, case_id: str | None = None) -> EvidenceRecord:
        """Persist a result with its original evidence kind and source conditions."""

        limitations = "; ".join(result.limitations) or "No result limitations supplied."
        if case_id is not None and (not result.result_id or type(result.plan_version) is not int or result.plan_version < 1):
            raise ValueError("result_projection_requires_accepted_identity")
        return self._evidence.add_evidence(
            result.statement,
            source=result.source_id,
            context=(
                f"Result for action {result.action_identifier}; kind={result.evidence_kind.value}; "
                f"context={result.context_identifier or 'unspecified'}; "
                f"time_hours={result.time_hours if result.time_hours is not None else 'unknown'}; "
                f"conditions={dict(result.conditions)}; metrics={dict(result.metrics)}; "
                f"record_count={result.record_count}; biological_replicates={result.biological_replicates}; "
                f"limitations={limitations}"
            ),
            status=status_for_kind(result.evidence_kind),
            evidence_kind=result.evidence_kind,
            case_id=case_id,
            identifier=("result:" + json.dumps([case_id, result.result_id], separators=(",", ":")))
                       if case_id is not None else None,
            payload={"result_id": result.result_id, "plan_version": result.plan_version,
                     "action_identifier": result.action_identifier, "case_id": case_id,
                     "context_identifier": result.context_identifier, "time_hours": result.time_hours,
                     "conditions": dict(result.conditions), "metrics": dict(result.metrics),
                     "independent_units": result.independent_units, "quality_passed": result.quality_passed,
                     "record_count": result.record_count, "biological_replicates": result.biological_replicates,
                     "limitations": list(result.limitations), "interpretation_fields": list(result.interpretation_fields)},
        )

    def record_real_measurement(self, result: "MeasurementResult") -> EvidenceRecord:
        """Backward-compatible physical-measurement entry point."""

        return self.record_result(result)

    def _packet(
        self,
        intent: TaskIntent,
        evidence: tuple[EvidenceRecord, ...],
        memories: tuple[MemoryEntry, ...],
        *,
        visual_reviews: tuple[str, ...] = (),
    ) -> ContextPacket:
        required_sections = [
            "TASK\n" + intent.research_question,
            "SUPPLIED EVIDENCE\n" + "\n".join(intent.supplied_evidence or ("None supplied.",)),
            "TASK DETAILS (requested state; not measured evidence)\n" + json.dumps(
                {key: value for key, value in asdict(intent).items()
                 if key not in {"research_question", "supplied_evidence"}},
                ensure_ascii=False, separators=(",", ":"),
            ),
        ]
        mandatory = "\n\n".join(required_sections)
        if len(mandatory) > self._max_characters:
            return ContextPacket(
                intent, evidence, memories,
                "CONTEXT_BUDGET_INSUFFICIENT\nMandatory task state exceeds the configured context budget.",
                budget_error="mandatory_task_state_exceeds_context_budget",
            )
        remaining = self._max_characters - len(mandatory)
        sections = list(required_sections)
        included: list[str] = []
        omitted: list[str] = []
        reasons: list[str] = []
        for item in evidence:
            card = _evidence_card(item)
            if len(card) + 2 <= remaining:
                sections.append(card)
                included.append(item.identifier)
                remaining -= len(card) + 2
            else:
                omitted.append(item.identifier)
                reasons.append(f"{item.identifier}: insufficient_context_budget")
        for index, review in enumerate(visual_reviews, start=1):
            card = "VISUAL REVIEW (not measured evidence)\n" + review
            if len(card) + 2 <= remaining:
                sections.append(card)
                remaining -= len(card) + 2
            else:
                reasons.append(f"visual_review_{index}: insufficient_context_budget")
        for item in memories:
            card = f"MEMORY (not new evidence)\n[{item.status.value}; {item.provenance}] {item.content}"
            if len(card) + 2 <= remaining:
                sections.append(card)
                remaining -= len(card) + 2
            else:
                reasons.append(f"memory:{item.identifier}: insufficient_context_budget")
        return ContextPacket(
            intent=intent,
            evidence=evidence,
            memories=memories,
            rendered="\n\n".join(sections),
            visual_reviews=visual_reviews,
            included_record_ids=tuple(included),
            omitted_record_ids=tuple(omitted),
            omission_reasons=tuple(reasons),
        )


def _evidence_card(item: EvidenceRecord) -> str:
    """The statement, provenance, and qualification text are one indivisible unit."""

    heading = "DATASET TOOL OUTPUT" if item.source.startswith("tool:") else "SOURCED EVIDENCE"
    card = (
        f"{heading} [{item.identifier}]\n"
        f"ORIGIN: {item.evidence_kind.value}; STATUS: {item.status.value}; SOURCE: {item.source}\n"
        f"STATEMENT: {item.statement}\n"
        f"CONTEXT AND LIMITATIONS: {item.context or 'No context supplied.'}"
    )
    if item.source_lineage_ids:
        card += "\nSOURCE_LINEAGE: " + json.dumps(list(item.source_lineage_ids), ensure_ascii=True)
    if item.payload:
        card += "\nSTRUCTURED_DATA: " + json.dumps(dict(item.payload), ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    return card


def _intent_entities(intent: TaskIntent) -> tuple[str, ...]:
    """Use task-extracted entities directly; original Chinese labels remain intact."""

    return tuple(dict.fromkeys((*intent.target_or_targets, *intent.interventions)))


def _required_text(data: dict[str, Any], field: str) -> str:
    value = _optional_text(data.get(field))
    if value is None:
        raise ValueError(f"Task interpretation is missing '{field}'.")
    return value


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


# A missing *task* field is one of these and nothing else. The closed set is enforced
# here rather than trusted from the model, so a prose answer cannot block planning.
TASK_FIELDS: frozenset[str] = frozenset(
    {"target", "intervention", "biological_context", "phenotype_endpoint", "existing_observation"}
)


def _task_fields(value: object) -> tuple[str, ...]:
    """Keep only entries naming a closed-vocabulary task field."""

    return tuple(
        item.strip().lower()
        for item in _string_tuple(value)
        if item.strip().lower() in TASK_FIELDS
    )


def _non_task_fields(value: object) -> tuple[str, ...]:
    """Everything else the model listed: an evidence gap, not a blocked task field."""

    return tuple(item for item in _string_tuple(value) if item.strip().lower() not in TASK_FIELDS)


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
    from virtual_cell.interface import prediction_request_errors
    rows: list[WorldModelRow] = []
    for action in actions:
        request = requests.get(action.identifier)
        if request is None:
            continue
        prediction = predictions.get(action.identifier)
        assessment = assessments.get(action.identifier)
        readout = action.prediction_readout or (request.readouts[0] if len(request.readouts) == 1 else None)
        validation = assessment.validation_status.value if assessment is not None else None
        errors = prediction_request_errors(prediction, request) if prediction is not None else ("not_answered",)
        if errors or prediction is None or not prediction.applicable:
            rows.append(
                WorldModelRow(
                    action=action.identifier,
                    intervention=request.intervention.identifier,
                    status="abstained",
                    readout=readout,
                    validation_status=validation,
                    model_version=request.model_version,
                    abstain_reason=errors[0] if errors else (prediction.abstain_reason or "not_answered"),
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
