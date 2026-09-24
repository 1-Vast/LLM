"""G2 candidate-case screening without exposing evaluator-only outcomes to policies.

File summary
- Path: src/evaluation/screening.py
- Purpose: Apply G2 eligibility gates to registered candidate cases.
- Core points:
  - `assess_candidate` applies G2 eligibility gates to a registered candidate case.
  - Screening reads only provenance and source cluster metadata, never hidden results.
- Interfaces: `load_candidate_registry`, `assess_candidate`, `assess_registry`, `CandidateCase`, `CandidateAssessment`
- Depends on: (standard library only)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CandidateCase:
    """Source-screening record, not an evaluation case or a scientific verdict."""

    identifier: str
    source_clusters: tuple[str, ...]
    biological_context: str
    category: str
    status: str
    action_identifiers: tuple[str, ...]
    hidden_result_actions: tuple[str, ...]
    decision_branch_actions: tuple[str, ...]
    provenance_complete: bool
    conditions_complete: bool
    selection_blinded_to_policy: bool
    independent_review_status: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class CandidateAssessment:
    """Eligibility verdict for one candidate case, with its blocking reasons."""

    identifier: str
    eligible_for_development: bool
    blocking_reasons: tuple[str, ...]


def load_candidate_registry(path: Path) -> tuple[CandidateCase, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("candidates"), list):
        raise ValueError("Candidate registry requires a 'candidates' list.")
    candidates = tuple(_candidate(value) for value in data["candidates"])
    identifiers = [candidate.identifier for candidate in candidates]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Candidate identifiers must be unique.")
    return candidates


def assess_candidate(candidate: CandidateCase) -> CandidateAssessment:
    """Apply G2 eligibility criteria without reading hidden outcome values."""

    blockers: list[str] = []
    if candidate.status != "screened":
        blockers.append("candidate_not_screened")
    if len(candidate.source_clusters) < 1 or not candidate.provenance_complete:
        blockers.append("incomplete_provenance")
    if not candidate.conditions_complete:
        blockers.append("incomplete_condition_metadata")
    if len(candidate.action_identifiers) < 2:
        blockers.append("fewer_than_two_real_action_paths")
    if len(candidate.hidden_result_actions) < 2:
        blockers.append("insufficient_hidden_result_coverage")
    if len(candidate.decision_branch_actions) < 2:
        blockers.append("no_registered_action_tradeoff")
    if not candidate.selection_blinded_to_policy:
        blockers.append("selection_not_blinded_to_policy")
    if candidate.independent_review_status != "completed":
        blockers.append("independent_review_incomplete")
    return CandidateAssessment(candidate.identifier, not blockers, tuple(blockers))


def assess_registry(path: Path) -> tuple[CandidateAssessment, ...]:
    return tuple(assess_candidate(candidate) for candidate in load_candidate_registry(path))


def _candidate(data: Any) -> CandidateCase:
    if not isinstance(data, dict):
        raise ValueError("Each candidate must be an object.")
    status = _text(data, "status")
    if status not in {"screened", "screening", "excluded"}:
        raise ValueError("Candidate status must be screened, screening, or excluded.")
    review = _text(data, "independent_review_status")
    if review not in {"not_started", "in_progress", "completed", "not_applicable"}:
        raise ValueError("Candidate independent_review_status is invalid.")
    return CandidateCase(
        identifier=_text(data, "identifier"),
        source_clusters=_texts(data, "source_clusters", require_items=True),
        biological_context=_text(data, "biological_context"),
        category=_text(data, "category"),
        status=status,
        action_identifiers=_texts(data, "action_identifiers"),
        hidden_result_actions=_texts(data, "hidden_result_actions"),
        decision_branch_actions=_texts(data, "decision_branch_actions"),
        provenance_complete=_bool(data, "provenance_complete"),
        conditions_complete=_bool(data, "conditions_complete"),
        selection_blinded_to_policy=_bool(data, "selection_blinded_to_policy"),
        independent_review_status=review,
        notes=_texts(data, "notes", require_items=True),
    )


def _text(data: dict[str, Any], name: str) -> str:
    value = data.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Candidate '{name}' must be nonempty text.")
    return value.strip()


def _texts(data: dict[str, Any], name: str, *, require_items: bool = False) -> tuple[str, ...]:
    value = data.get(name)
    if (
        not isinstance(value, list)
        or (require_items and not value)
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise ValueError(f"Candidate '{name}' must be a list of nonempty text.")
    return tuple(item.strip() for item in value)


def _bool(data: dict[str, Any], name: str) -> bool:
    value = data.get(name)
    if type(value) is not bool:
        raise ValueError(f"Candidate '{name}' must be a boolean.")
    return value
