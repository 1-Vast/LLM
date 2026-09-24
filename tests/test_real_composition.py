"""The composition repair on the frozen real cases: what it is worth, and the control.

File summary
- Path: tests/test_real_composition.py
- Purpose: pin the real-package certificate of the composed gated plan. The retyping
  repair is worth 0.000 on this package; the composition is not, and the difference is a
  declared saving rather than a change to any case.
- Core points:
  - The re-reading moves one field per readout and nothing else, and it is available in 27
    of 58 cases.
  - A zero saving keeps the composed object and buys nothing: the attribution control.
  - At the shipped budget the value is the saving; at a budget one stage lower it is the
    loss no legal sequence can avoid, which is a strictly larger feasibility gain.
- Interfaces: pytest test functions
- Depends on: evaluation.real_composition, evaluation.cases
"""
from pathlib import Path

import pytest

from evaluation.cases import CaseRepository
from evaluation.real_composition import (
    composition_certificate,
    gated_case_problem,
    measure_package,
    minimum_saving,
    required_gate_pairs,
)

PACKAGE = Path(__file__).resolve().parents[1] / "data" / "evaluation" / "cases" / "real_v3"


def _cases():
    repository = CaseRepository(PACKAGE / "public", PACKAGE / "private")
    return [case.public for case, _ in repository.load()]


def test_the_gated_reading_moves_one_field_per_readout_and_nothing_else():
    case = _cases()[0]
    problem = gated_case_problem(case)
    assert problem.budget == float(case.budget)
    assert [action.identifier for action in problem.actions] == [
        item.action.identifier for item in case.actions
    ]
    for original, gated in zip(case.actions, problem.actions):
        assert gated.cost == pytest.approx(float(original.action.cost))
        declared = {
            str(entry["identifier"]): original.action.expected_outcomes.get(
                str(entry["identifier"]), "unknown"
            )
            for entry in case.hypotheses
        }
        assert gated.supplies == {
            outcome: tuple(original.action.supplies) for outcome in set(declared.values())
        }
        if original.action.prerequisites:
            assert gated.prerequisites == ()
            assert gated.interpretation_gate == original.action.prerequisites[0]
            assert gated.uninterpretable_model
        else:
            assert gated.prerequisites == tuple(original.action.prerequisites)
            assert gated.interpretation_gate is None


def test_the_gate_reading_is_available_in_27_of_the_58_frozen_cases():
    cases = _cases()
    assert len(cases) == 58
    assert sum(1 for case in cases if required_gate_pairs(case)) == 27


def test_a_zero_saving_keeps_the_composed_object_and_buys_nothing():
    """The attribution control: remove the declared saving and the value is exactly zero."""

    payload = measure_package(PACKAGE, budgets=(2.0,), savings=(0.0,))
    cell = payload["cells"][0]
    assert cell["cases_with_a_composed_object"] == 27
    assert cell["cases_where_the_repair_is_worth_something"] == 0
    assert cell["total_value"] == 0.0
    assert all(row["complete"] for row in cell["rows"])


def test_at_the_shipped_budget_the_repair_is_worth_its_declared_saving():
    payload = measure_package(PACKAGE, budgets=(2.0,), savings=(0.5,))
    cell = payload["cells"][0]
    assert cell["cases"] == 58
    assert cell["complete"] == 58
    assert cell["cases_where_the_repair_is_worth_something"] == 21
    assert cell["median_value_where_positive"] == pytest.approx(0.5)
    assert cell["total_value"] == pytest.approx(10.5)
    for row in cell["rows"]:
        assert row["value"] >= 0.0
        if row["value"] > 0.0:
            assert row["closed_optimum"] < row["menu_optimum"]


def test_below_the_sequence_cost_the_repair_is_a_feasibility_gain_not_a_discount():
    payload = measure_package(PACKAGE, budgets=(1.5,), savings=(0.5,))
    cell = payload["cells"][0]
    assert cell["cases_where_the_repair_is_worth_something"] == 21
    assert cell["median_value_where_positive"] == pytest.approx(2.5)
    assert cell["median_value_where_positive"] > 0.5


def test_the_saving_threshold_is_reported_per_case_rather_than_assumed():
    cases = {case.identifier: case for case in _cases()}
    thresholds = measure_package(PACKAGE, budgets=(2.0,), savings=(0.5,))[
        "minimum_saving_at_the_shipped_budget"
    ]
    assert thresholds["cases_searched"] == 27
    assert thresholds["cases_with_a_threshold_at_or_below_2_0"] == 27
    assert thresholds["median_threshold"] == pytest.approx(0.05)
    values = sorted(set(thresholds["thresholds"].values()))
    assert values == [0.05, 1.05]
    small = next(
        identifier for identifier, value in thresholds["thresholds"].items() if value == 0.05
    )
    assert minimum_saving(gated_case_problem(cases[small])) == pytest.approx(0.05)


def test_a_case_without_a_declared_premise_has_no_gate_to_compose():
    cases = {case.identifier: case for case in _cases()}
    without = next(case for case in cases.values() if not required_gate_pairs(case))
    problem = gated_case_problem(without)
    certificate = composition_certificate(problem, saving=1.0, case=without.identifier)
    assert certificate.composed_actions == 0
    assert certificate.value == pytest.approx(0.0)
    assert minimum_saving(problem) is None
