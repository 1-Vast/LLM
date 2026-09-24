"""Regression tests for the audited evaluation-infrastructure defects.

File summary
- Path: tests/test_evaluation_integrity.py
- Purpose: Pin the terminal-information, quantity-typing, split, reachability, cost and provenance contracts.
- Core points: each test reproduces one independently verified defect; they are written to fail on the pre-fix code and must not be weakened to make a run pass.
- Interfaces: `test_public_contract_survives_budget_exhaustion()`, `test_rna_record_cannot_satisfy_a_protein_prerequisite()`, `test_split_assignment_is_global_over_groups()`, `test_scorer_reachability_agrees_with_executable_search()`, `test_sole_valid_alternative_route_is_not_all_waste()`, `test_planner_enumeration_is_non_anticipative()`
- Depends on: evaluation.cases, evaluation.scoring, evaluation.baselines, evaluation.feasibility, evaluation.case_builder, evaluation.evidence_base, maestro.models
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from evaluation.baselines import _public_prompt
from evaluation.case_builder import assign_split
from evaluation.cases import (
    EvidenceMenuItem,
    PublicCase,
    ReplayCase,
    ReplayEnvironment,
    RevealedEvidence,
    ScoringSpec,
    DecisionRule,
)
from evaluation.evidence_base import SourceRelease
from evaluation.feasibility import legal_actions, enumerate_executed_sequences, enumerate_public_plans
from evaluation.scoring import reachable_decisions, score_submission
from maestro.models import (
    BiologicalQuantity,
    DevelopmentAction,
    EvidenceAction,
    EvidenceActionKind,
    EvidenceKind,
)


def _action(identifier: str, **overrides) -> EvidenceMenuItem:
    defaults = dict(
        identifier=identifier,
        description=f"registered capability {identifier}",
        cost=1.0,
        distinguishes=("h1", "h2"),
        kind=EvidenceActionKind.READOUT_MEASUREMENT,
        expected_outcomes={"h1": "positive", "h2": "negative"},
    )
    defaults.update(overrides)
    available = defaults.pop("available", True)
    return EvidenceMenuItem(action=EvidenceAction(**defaults), available=available)


def _revealed(identifier: str, outcome: str, fields: tuple[str, ...]) -> RevealedEvidence:
    return RevealedEvidence(
        action_identifier=identifier,
        outcome=outcome,
        statement=f"result of {identifier}",
        source_id=f"source:{identifier}",
        context_identifier="ctx",
        time_hours=None,
        conditions={},
        metrics={},
        record_count=1,
        biological_replicates=1,
        record_validated=True,
        biological_quality="passed",
        interpretation_fields=fields,
        limitations=(),
        evidence_kind=EvidenceKind.REAL_MEASUREMENT,
        independent_units=1,
    )


def _case(actions, rules, *, budget: float = 2.0, critical=frozenset()) -> ReplayCase:
    public = PublicCase(
        identifier="fixture-case",
        provenance="synthetic software fixture; not a biological record",
        evaluation_status="fixture",
        initial_evidence=(),
        hypotheses=({"identifier": "h1", "description": "one", "development_action": "continue"},
                    {"identifier": "h2", "description": "two", "development_action": "revise_attribution"}),
        actions=tuple(actions),
        budget=budget,
        context_identifier="ctx",
    )
    return ReplayCase(public, ScoringSpec(decision_rules=tuple(rules), critical_actions=frozenset(critical)))


# --------------------------------------------------------------- A. contract

def test_public_contract_survives_budget_exhaustion():
    """At zero budget every terminal policy must still see the public declarations.

    The deterministic interpretation rule reads `expected_outcomes` from the
    case, so a prompt that drops them when the menu empties compares policies
    on different information.
    """

    case = _case([_action("a"), _action("b")], [])
    environment = ReplayEnvironment(case, {"a": _revealed("a", "positive", ("f:a",)),
                                           "b": _revealed("b", "negative", ("f:b",))})
    environment.query("a")
    environment.query("b")
    view = environment.view()
    assert view.remaining_budget == pytest.approx(0.0)
    assert view.available_actions() == ()

    prompt = _public_prompt(view, list(view.available_actions()))
    declared = {item["identifier"]: item for item in prompt["public_actions"]}
    assert set(declared) == {"a", "b"}
    for item in declared.values():
        assert item["expected_outcome_by_hypothesis"] == {"h1": "positive", "h2": "negative"}
    assert all(item["acquired"] for item in declared.values())


def test_public_contract_excludes_private_material():
    """Parity is achieved by publishing public declarations, never private ones."""

    rule = DecisionRule(decision=DevelopmentAction.CONTINUE, required_outcomes={"a": "positive"})
    case = _case([_action("a"), _action("b")], [rule], critical={"a"})
    environment = ReplayEnvironment(case, {"a": _revealed("a", "positive", ("f:a",)),
                                           "b": _revealed("b", "negative", ("f:b",))})
    environment.query("a")
    serialised = json.dumps(_public_prompt(environment.view(), list(environment.view().available_actions())))
    for forbidden in ("critical_action", "decision_rule", "required_outcomes", "archetype", "licensed"):
        assert forbidden not in serialised


# ---------------------------------------------------------------- B. typing

def test_rna_record_cannot_satisfy_a_protein_prerequisite():
    """An RNA measurement is not a protein measurement, and never substitutes for one."""

    rna = _action(
        "rna",
        kind=EvidenceActionKind.RNA_ABUNDANCE_MEASUREMENT,
        quantity=BiologicalQuantity.RNA_ABUNDANCE,
        supplies=("abundance:target_rna",),
    )
    assert rna.action.quantity is BiologicalQuantity.RNA_ABUNDANCE
    assert not rna.action.quantity.satisfies(BiologicalQuantity.PROTEIN_ABUNDANCE)
    assert not rna.action.quantity.satisfies(BiologicalQuantity.TARGET_OCCUPANCY)
    assert rna.action.quantity.satisfies(BiologicalQuantity.RNA_ABUNDANCE)

    protein = _action(
        "protein",
        kind=EvidenceActionKind.PROTEIN_ABUNDANCE_MEASUREMENT,
        quantity=BiologicalQuantity.PROTEIN_ABUNDANCE,
    )
    assert protein.action.quantity.satisfies(BiologicalQuantity.PROTEIN_ABUNDANCE)
    # Nothing in the ladder is a higher-quality version of another quantity:
    # viability does not answer an occupancy question in either direction.
    assert not BiologicalQuantity.VIABILITY.satisfies(BiologicalQuantity.TARGET_OCCUPANCY)
    assert not BiologicalQuantity.TARGET_OCCUPANCY.satisfies(BiologicalQuantity.VIABILITY)


def test_bridge_estimate_never_satisfies_a_direct_measurement_requirement():
    """A validated bridge may scope an inference; it cannot become a measurement."""

    estimate = _action(
        "bridge",
        kind=EvidenceActionKind.RNA_ABUNDANCE_MEASUREMENT,
        quantity=BiologicalQuantity.PROTEIN_ABUNDANCE,
        quantity_is_estimated=True,
    )
    assert estimate.action.quantity_is_estimated is True
    assert not estimate.action.satisfies_direct_requirement(BiologicalQuantity.PROTEIN_ABUNDANCE)
    direct = _action("direct", quantity=BiologicalQuantity.PROTEIN_ABUNDANCE)
    assert direct.action.satisfies_direct_requirement(BiologicalQuantity.PROTEIN_ABUNDANCE)


# ----------------------------------------------------------------- C. splits

def test_split_assignment_is_global_over_groups():
    """A gene appearing in several archetypes must land in exactly one partition."""

    order = ("BRAF", "EGFR", "ALK")
    first = assign_split("BRAF", order)
    second = assign_split("BRAF", order)
    assert first == second
    labels = {gene: assign_split(gene, order) for gene in order}
    assert set(labels.values()) <= {"development", "test"}
    # The label must not depend on any archetype-local ordering.
    assert assign_split("EGFR", order) == assign_split("EGFR", ("EGFR", "BRAF", "ALK"))


def test_comparator_selection_is_blind_to_hidden_response():
    """The offered comparator must not be ranked by the response the agent buys."""

    from evaluation.case_builder import select_comparator
    from evaluation.evidence_base import ExposureRecord

    def record(compound: str, auc: float) -> ExposureRecord:
        return ExposureRecord(
            model_id="ACH-000001", ccle_name="LINE", gene="GENE", compound=compound,
            broad_id=f"BRD-{compound}", screen_id="MTS010", auc=auc, ic50=None, ec50=None,
            curve_r2=0.9, moa="inhibitor", phase="Phase 1",
        )

    candidates = [record("alpha", 0.95), record("beta", 0.20)]
    permuted = [record("alpha", 0.20), record("beta", 0.95)]
    assert select_comparator(candidates).compound == select_comparator(permuted).compound


# ------------------------------------------------------- D. reachability/cost

def test_scorer_reachability_agrees_with_executable_search():
    """A decision whose evidence cannot legally execute is not reachable."""

    blocked = _action("blocked", prerequisites=("missing:no_provider",))
    other = _action("other", supplies=("f:other",))
    rule = DecisionRule(decision=DevelopmentAction.REVISE_INTERVENTION, required_outcomes={"blocked": "positive"})
    case = _case([blocked, other], [rule])
    outcomes = {"blocked": _revealed("blocked", "positive", ("f:blocked",)),
                "other": _revealed("other", "negative", ("f:other",))}

    assert DevelopmentAction.REVISE_INTERVENTION not in reachable_decisions(
        case, outcomes, budget=case.public.budget
    )
    score = score_submission(
        case, outcomes, decision=DevelopmentAction.DEFER, observed={}, evidence_ids=(),
        spent=0.0, submission_valid=True,
    )
    assert score.verdict.value == "correct"


def test_sole_valid_alternative_route_is_not_all_waste():
    """A licensing route the policy legitimately took is not wasted expenditure."""

    canonical = _action("canonical")
    alternative = _action("alternative")
    rules = [
        DecisionRule(decision=DevelopmentAction.REVISE_ATTRIBUTION, required_outcomes={"canonical": "positive"}),
        DecisionRule(decision=DevelopmentAction.REVISE_ATTRIBUTION, required_outcomes={"alternative": "positive"}),
    ]
    case = _case([canonical, alternative], rules, critical={"canonical"})
    outcomes = {"canonical": _revealed("canonical", "positive", ("f:c",)),
                "alternative": _revealed("alternative", "positive", ("f:a",))}
    observed = {"alternative": outcomes["alternative"]}

    score = score_submission(
        case, outcomes, decision=DevelopmentAction.REVISE_ATTRIBUTION, observed=observed,
        evidence_ids=("alternative",), spent=1.0, submission_valid=True,
    )
    assert score.verdict.value == "correct"
    assert score.waste_cost == pytest.approx(0.0)
    assert score.redundant_cost == pytest.approx(0.0)


def test_prerequisite_cost_is_retained_in_the_minimum_certificate():
    """The cost of a required prerequisite belongs to the certificate, not to waste."""

    supplier = _action("supplier", supplies=("f:premise",), cost=1.0)
    dependent = _action("dependent", prerequisites=("f:premise",), cost=1.0)
    rule = DecisionRule(decision=DevelopmentAction.CONTINUE, required_outcomes={"dependent": "positive"})
    case = _case([supplier, dependent], [rule], critical={"dependent"})
    outcomes = {"supplier": _revealed("supplier", "positive", ("f:premise",)),
                "dependent": _revealed("dependent", "positive", ("f:dep",))}
    observed = dict(outcomes)

    score = score_submission(
        case, outcomes, decision=DevelopmentAction.CONTINUE, observed=observed,
        evidence_ids=("dependent",), spent=2.0, submission_valid=True,
    )
    assert score.verdict.value == "correct"
    assert score.required_cost == pytest.approx(2.0)
    assert score.waste_cost == pytest.approx(0.0)


def test_provider_failure_preserves_accrued_cost_and_acquisitions():
    """A failed run reports what was already paid for, not a zeroed ledger."""

    from evaluation.runner import _provider_failure

    class _Policy:
        name = "stub"

    case = _case([_action("a"), _action("b")], [])
    acquired = (_revealed("a", "positive", ("f:a",)),)
    result = _provider_failure(
        _Policy(), case, "run", "decision", "provider unavailable",
        revealed=acquired, spent=1.0, selected_actions=("a",),
    )
    assert result.selected_actions == ("a",)
    assert result.spent == pytest.approx(1.0)
    assert result.revealed == acquired
    assert result.stop_reason == "provider_error"


# ------------------------------------------------------------- E. provenance

def test_stale_provenance_sidecar_is_rejected(tmp_path: Path):
    """A mutated release with an unchanged sidecar flag must not be accepted."""

    release = tmp_path / "synthetic.csv"
    release.write_text("mutated,payload\n", encoding="utf-8")
    sidecar = tmp_path / "synthetic.csv.provenance.json"
    sidecar.write_text(
        json.dumps({"md5_match": True, "release": "synthetic", "file_name": release.name,
                    "declared_md5": "0" * 32}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="digest"):
        SourceRelease.from_provenance(release)


# --------------------------------------------------- shared legal transitions

def test_legal_actions_matches_the_replay_environment():
    """One feasibility function decides execution and scoring alike."""

    supplier = _action("supplier", supplies=("f:premise",))
    dependent = _action("dependent", prerequisites=("f:premise",))
    expensive = _action("expensive", cost=3.0)
    unavailable = _action("unavailable", available=False)
    case = _case([supplier, dependent, expensive, unavailable], [])
    outcomes = {name: _revealed(name, "positive", ("f:premise",) if name == "supplier" else (f"f:{name}",))
                for name in ("supplier", "dependent", "expensive", "unavailable")}
    environment = ReplayEnvironment(case, outcomes)

    legal = {item.action.identifier for item in legal_actions(case.public, (), 0.0, frozenset())}
    assert legal == {"supplier"}
    for identifier in ("dependent", "expensive", "unavailable"):
        with pytest.raises(ValueError):
            ReplayEnvironment(case, outcomes).query(identifier)

    environment.query("supplier")
    view = environment.view()
    legal_after = {
        item.action.identifier
        for item in legal_actions(case.public, view.queried_actions, case.public.budget - view.remaining_budget,
                                  frozenset({"f:premise"}))
    }
    assert legal_after == {"dependent"}


def test_planner_enumeration_is_non_anticipative():
    """Identical public information yields identical plans under permuted hidden outcomes."""

    case = _case([_action("a"), _action("b")], [])
    world_one = {"a": _revealed("a", "positive", ("f:a",)), "b": _revealed("b", "negative", ("f:b",))}
    world_two = {"a": _revealed("a", "negative", ("f:a",)), "b": _revealed("b", "positive", ("f:b",))}

    plans_one = enumerate_public_plans(case.public)
    plans_two = enumerate_public_plans(case.public)
    assert plans_one == plans_two

    executed_one = enumerate_executed_sequences(case.public, world_one)
    executed_two = enumerate_executed_sequences(case.public, world_two)
    # The evaluator's executed-sequence oracle may legitimately differ between
    # worlds; the planner's own enumeration may not depend on them at all.
    assert isinstance(executed_one, tuple) and isinstance(executed_two, tuple)
    assert plans_one == enumerate_public_plans(replace(case.public, identifier="renamed"))
