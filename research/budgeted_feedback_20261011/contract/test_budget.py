"""A common cap must charge waiting as well as measurements."""
import pytest

from research.budgeted_feedback_20261011.contract.budget import CampaignBudget


def test_two_rounds_must_displace_measurements():
    budget = CampaignBudget(18, 1, 2, "read-equivalent scenario")
    assert budget.require_feasible(16, 1) == 18
    assert budget.require_feasible(14, 2) == 18
    with pytest.raises(ValueError, match="exceeds total"):
        budget.require_feasible(16, 2)


def test_other_cost_cannot_be_spent_again_as_measurements():
    budget = CampaignBudget(18, 1, 2, "read-equivalent scenario")
    assert budget.require_feasible(12, 2, other_cost=2) == 18
    with pytest.raises(ValueError, match="exceeds total"):
        budget.require_feasible(14, 2, other_cost=2)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True])
def test_invalid_prices_refuse(value):
    with pytest.raises(ValueError):
        CampaignBudget(18, value, 2, "read-equivalent scenario")


def test_fractional_resources_and_stop_without_purchase():
    budget = CampaignBudget(0.3, 0.1, 0, "declared units")
    assert budget.require_feasible(3, 0) == pytest.approx(0.3)
    assert budget.require_feasible(0, 0) == 0
    with pytest.raises(ValueError):
        budget.cost(True, 0)
    with pytest.raises(ValueError):
        budget.cost(1, 0, other_cost=float("nan"))
