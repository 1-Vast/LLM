"""Validate G2 candidate screening against the eligibility registry.

File summary
- Path: tests/test_candidate_screening.py
- Purpose: Validate G2 candidate screening against the eligibility registry.
- Core points:
  - Asserts blocking reasons for incomplete provenance, conditions, and review.
  - `assess_registry` flags ineligible candidates without reading hidden results.
- Interfaces: `test_*` functions
- Depends on: evaluation.screening
"""
from pathlib import Path

from evaluation.screening import CandidateCase, assess_candidate, assess_registry


ROOT = Path(__file__).resolve().parents[1]


def test_current_real_partial_case_is_explicitly_ineligible_for_directed_repair_evaluation():
    assessment = assess_registry(ROOT / "data/evaluation/candidate_registry.json")[0]

    assert not assessment.eligible_for_development
    assert assessment.blocking_reasons == (
        "incomplete_condition_metadata", "fewer_than_two_real_action_paths",
        "insufficient_hidden_result_coverage", "no_registered_action_tradeoff",
        "independent_review_incomplete",
    )


def test_candidate_assessment_requires_real_branches_and_independent_review():
    candidate = CandidateCase(
        identifier="screened-example", source_clusters=("source-a", "source-b"),
        biological_context="context", category="premise_missing", status="screened",
        action_identifiers=("functional", "mode"), hidden_result_actions=("functional", "mode"),
        decision_branch_actions=("functional", "mode"), provenance_complete=True,
        conditions_complete=True, selection_blinded_to_policy=True,
        independent_review_status="completed", notes=("Schema-only test fixture.",),
    )

    assert assess_candidate(candidate).eligible_for_development
