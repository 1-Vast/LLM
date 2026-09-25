"""The LLM repair-proposal arm: the compiler's contract and the arm's arithmetic.

File summary
- Path: tests/test_llm_proposal_arm.py
- Purpose: pin what the proposal arm measures without touching the network. The model
  chooses an operator and its parameters; the framework compiles the choice into a
  typed action; a refusal is reported by name. The tests use a recorded fake client so
  the arithmetic of the arm is checkable offline and a provider outage cannot move it.
- Core points:
  - A proposal that names a premise nothing requires is refused, not repaired.
  - A supplier priced inside the window certifies the menu-only gap; half a unit dearer
    or half as reliable certifies nothing.
  - The menu-only bound excludes both the declared repair catalogue and any earlier
    proposal, so the comparison is against what the shipped menu could already do.
  - A provider failure is recorded as a refused proposal, never raised into the runner.
- Interfaces: pytest test functions
- Depends on: evaluation.llm_proposal_arm, evaluation.licensing_gap
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from evaluation.llm_proposal_arm import (  # noqa: E402
    compile_proposal,
    missing_premises,
    render_problem,
    run_arm,
    score_proposal,
)
from evaluation.licensing_gap import FAMILIES  # noqa: E402

TOLERANCE = 1e-6


class FakeResponse:
    model = "recorded-fake-model"
    finish_reason = "stop"
    usage = {"prompt_tokens": 100, "completion_tokens": 40, "total_tokens": 140}


class FakeClient:
    """A recorded client: it returns the same proposal for every call."""

    def __init__(self, proposal: dict) -> None:
        self.proposal = proposal
        self.calls = 0

    def complete_json(self, messages, max_tokens=None):  # noqa: ANN001, ANN201
        self.calls += 1
        return self.proposal, FakeResponse()


class FailingClient:
    def complete_json(self, messages, max_tokens=None):  # noqa: ANN001, ANN201
        raise RuntimeError("provider unavailable")


def _supplier(premise: str = "engagement", cost: float = 3.25, reliability: float = 1.0) -> dict:
    return {
        "operator": "register_supplier",
        "supplies": premise,
        "cost": cost,
        "reliability": reliability,
        "predicts_licensed": True,
        "rationale": "buy the premise that makes the isolating readout interpretable",
    }


def test_the_rendered_problem_hides_the_repair_catalogue() -> None:
    """The model proposes from the menu and the missing premises alone."""

    problem = FAMILIES["licensing_gap_replacement"]()
    statement = render_problem(problem, missing_premises=missing_premises(problem))
    assert missing_premises(problem) == ("engagement",)
    assert {entry["identifier"] for entry in statement["menu"]} == {"mode_readout", "realisation_readout"}
    assert "repair_actions_already_registered" not in statement


def test_a_wrong_premise_and_a_bad_operator_are_refused_by_name() -> None:
    problem = FAMILIES["licensing_gap_replacement"]()
    action, reason = compile_proposal(problem, _supplier(premise="selectivity"))
    assert action == ()
    assert reason == "premise_not_missing:selectivity"
    action, reason = compile_proposal(problem, {"operator": "invent_an_assay", "cost": 1.0})
    assert action == ()
    assert reason == "unknown_operator:invent_an_assay"
    action, reason = compile_proposal(problem, _supplier(reliability=1.5))
    assert action == ()
    assert reason == "reliability_out_of_range"


def test_a_composition_must_unlock_something() -> None:
    problem = FAMILIES["licensing_gap_replacement"]()
    action, reason = compile_proposal(
        problem,
        {
            "operator": "compose",
            "components": ["mode_readout", "realisation_readout"],
            "cost": 1.0,
            "reliability": 1.0,
        },
    )
    assert action == ()
    assert reason == "first_component_supplies_nothing:mode_readout"


def test_a_supplier_inside_the_window_certifies_the_menu_only_gap() -> None:
    problem = FAMILIES["licensing_gap_replacement"]()
    action, reason = compile_proposal(problem, _supplier())
    assert action and reason == "compiled"
    row = score_proposal(problem, action, reason, _supplier()).as_row()
    assert row["menu_only_admissible"] == pytest.approx(4.0, abs=TOLERANCE)
    assert row["catalogue_admissible"] == pytest.approx(3.75, abs=TOLERANCE)
    assert row["proposal_admissible"] == pytest.approx(3.75, abs=TOLERANCE)
    assert row["certified_value_of_the_proposal"] == pytest.approx(0.25, abs=TOLERANCE)
    assert row["reaches_the_catalogue_value"] is True
    assert row["proposal_is_licensed"] is True
    assert row["rule_arm_loss"] == pytest.approx(3.75, abs=TOLERANCE)


def test_a_dearer_or_less_reliable_supplier_certifies_nothing() -> None:
    problem = FAMILIES["licensing_gap_replacement"]()
    for proposal in (_supplier(cost=3.5), _supplier(reliability=0.5)):
        action, reason = compile_proposal(problem, proposal)
        row = score_proposal(problem, action, reason, proposal).as_row()
        assert row["certified_value_of_the_proposal"] == pytest.approx(0.0, abs=TOLERANCE), proposal
        assert row["proposal_is_licensed"] is False, proposal


def test_an_unbundled_supplier_is_insufficient_on_the_composed_variant() -> None:
    """Control: there the readout costs 1.000, so 3.250 + 1.000 is not worth buying."""

    problem = FAMILIES["licensing_gap_composed"]()
    action, reason = compile_proposal(problem, _supplier(cost=3.25))
    assert action and reason == "compiled"
    row = score_proposal(problem, action, reason, {}).as_row()
    assert row["menu_only_admissible"] == pytest.approx(4.0, abs=TOLERANCE)
    assert row["proposal_admissible"] == pytest.approx(4.0, abs=TOLERANCE)
    assert row["certified_value_of_the_proposal"] == pytest.approx(0.0, abs=TOLERANCE)
    assert row["reaches_the_catalogue_value"] is False


def test_a_composition_may_not_smuggle_a_catalogue_action_into_the_menu() -> None:
    problem = FAMILIES["licensing_gap_composed"]()
    action, reason = compile_proposal(
        problem,
        {"operator": "compose", "components": ["engagement_assay", "realisation_readout"], "cost": 3.75},
    )
    assert action == ()
    assert reason == "component_not_in_the_menu:engagement_assay"


def test_a_menu_composition_is_available_where_the_menu_has_both_stages() -> None:
    """`supplier_choice_binding_budget` keeps both stages in the menu, so composing is legal."""

    from evaluation.contingent_suite import FAMILIES as RECORDED

    problem = RECORDED["supplier_choice_binding_budget"]()
    action, reason = compile_proposal(
        problem,
        {
            "operator": "compose",
            "components": ["cheap_supplier", "gated_readout"],
            "cost": 1.5,
            "reliability": 1.0,
            "predicts_licensed": True,
            "rationale": "one plan sharing a control",
        },
    )
    assert action and reason == "compiled"
    row = score_proposal(problem, action, reason, {}).as_row()
    assert row["menu_only_admissible"] == pytest.approx(3.5, abs=TOLERANCE)
    assert row["proposal_admissible"] == pytest.approx(1.5, abs=TOLERANCE)
    assert row["certified_value_of_the_proposal"] == pytest.approx(2.0, abs=TOLERANCE)


def test_a_bundled_repair_reaches_the_composed_catalogue_value() -> None:
    """On the composed variant only the bundled operator can reach 3.750, and it does."""

    problem = FAMILIES["licensing_gap_composed"]()
    action, reason = compile_proposal(
        problem,
        {
            "operator": "register_supplier_and_bundle",
            "supplies": "engagement",
            "bundled_with": "realisation_readout",
            "cost": 3.25,
            "saving": 0.5,
            "reliability": 1.0,
            "predicts_licensed": True,
            "rationale": "one plan sharing a control",
        },
    )
    assert reason == "compiled" and len(action) == 2
    row = score_proposal(problem, action, reason, {}).as_row()
    assert row["menu_only_admissible"] == pytest.approx(4.0, abs=TOLERANCE)
    assert row["proposal_admissible"] == pytest.approx(3.75, abs=TOLERANCE)
    assert row["certified_value_of_the_proposal"] == pytest.approx(0.25, abs=TOLERANCE)
    assert row["reaches_the_catalogue_value"] is True
    # The unbundled supplier alone cannot reach it: the readout costs 1.000 here.
    unbundled, _ = compile_proposal(problem, _supplier(cost=3.25))
    assert score_proposal(problem, unbundled, "compiled", {}).as_row()[
        "certified_value_of_the_proposal"
    ] == pytest.approx(0.0, abs=TOLERANCE)


def test_a_bundle_that_does_not_need_the_premise_is_refused() -> None:
    problem = FAMILIES["licensing_gap_composed"]()
    action, reason = compile_proposal(
        problem,
        {
            "operator": "register_supplier_and_bundle",
            "supplies": "engagement",
            "bundled_with": "mode_readout",
            "cost": 3.25,
            "saving": 0.5,
        },
    )
    assert action == ()
    assert reason == "bundled_action_does_not_need_the_premise:engagement"


def test_the_arm_aggregates_and_records_provider_failure() -> None:
    problems = {
        "licensing_gap_replacement": FAMILIES["licensing_gap_replacement"](),
        "licensing_gap_menu_already_isolating": FAMILIES["licensing_gap_menu_already_isolating"](),
    }
    payload = run_arm(problems, FakeClient(_supplier()))
    assert payload["problems"] == 2
    assert payload["compiled_proposals"] == 2
    assert payload["admissible_proposal_rate"] == pytest.approx(1.0, abs=TOLERANCE)
    assert payload["novel_proposal_rate_among_compiled"] == pytest.approx(1.0, abs=TOLERANCE)
    assert payload["tokens"]["total_tokens"] == 280

    failed = run_arm(problems, FailingClient())
    assert failed["compiled_proposals"] == 0
    assert failed["admissible_proposal_rate"] == pytest.approx(0.0, abs=TOLERANCE)
    for row in failed["rows"]:
        assert row["refusal"].startswith("provider_failure:")
