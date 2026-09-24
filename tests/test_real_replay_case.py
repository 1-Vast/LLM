"""The DepMap/PRISM partial real case stays explicitly ineligible.

File summary
- Path: tests/test_real_replay_case.py
- Purpose: The DepMap/PRISM partial real case stays explicitly ineligible.
- Core points: assertions here are contract tests, not biological results; each test pins one boundary that must not silently move.
- Interfaces: `test_real_partial_case_keeps_curve_values_private_until_query()`, `test_real_partial_case_ends_in_supported_deferral_not_mechanism_claim()`
- Depends on: evaluation, maestro
"""
from pathlib import Path

from evaluation import CaseRepository, EvaluationRunner, MAESTROCorePolicy, ReplayEnvironment
from maestro import DevelopmentAction


ROOT = Path(__file__).resolve().parents[1]


def _real_case():
    loaded = CaseRepository(
        ROOT / "data" / "evaluation" / "cases" / "public",
        ROOT / "data" / "evaluation" / "cases" / "private",
    ).load()
    return next(item for item in loaded if item[0].public.identifier == "depmap-prism-snu761-egfr-osimertinib-001")


def test_real_partial_case_keeps_curve_values_private_until_query():
    case, outcomes = _real_case()
    environment = ReplayEnvironment(case, outcomes)
    view = environment.view()

    assert case.public.evaluation_status == "retrospective_real_partial"
    assert all(item.source_id for item in case.public.initial_evidence)
    assert "matched_target_engagement" not in {item.action.identifier for item in view.available_actions()}
    assert not view.revealed
    assert all("0.951159" not in item.statement for item in view.case.initial_evidence)

    revealed = environment.query("prism_mts010_osimertinib_curve")

    assert revealed.source_id.endswith("ACH-000537:BRD-K42805893-001-04-9:MTS010")
    assert revealed.metrics["auc"] == "0.951159"
    assert environment.spent == case.public.budget


def test_real_partial_case_ends_in_supported_deferral_not_mechanism_claim():
    case, outcomes = _real_case()

    result = EvaluationRunner().run_case(MAESTROCorePolicy(), case, outcomes)

    assert result.selected_actions == ("prism_mts010_osimertinib_curve",)
    assert result.decision is DevelopmentAction.DEFER
    assert result.decision_supported
    assert not result.autonomous_decision_supported
    assert result.query_coverage
    assert result.qualified_evidence_coverage
