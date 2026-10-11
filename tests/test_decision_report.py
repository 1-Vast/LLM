"""Cost and dependence cannot turn a weak campaign into evidence of agent benefit."""
from dataclasses import replace

import pytest

from tools.evaluation.decision_report import CampaignResult, paired_campaign_report
from maestro.campaign_budget import CampaignBudget


def rows():
    return [CampaignResult(str(i), str(i // 4), arm, "observed_readout", "a" * 64, 16,
                           1.0 if arm == "batch" else 1.1, 16, 1 if arm == "batch" else 16)
            for i in range(8) for arm in ("batch", "adaptive")]


def report(records, **kwargs):
    return paired_campaign_report(records, reference="batch", candidate="adaptive",
                                  measurement_price=0.0, turnaround_price=0.01, **kwargs)


def test_roundtrips_can_outweigh_positive_raw_utility_and_replicates_do_not_inflate_power():
    result = report(rows())
    assert result["raw_utility_increment"] == pytest.approx(0.1)
    assert result["net_utility_increment"] == pytest.approx(-0.05)
    assert result["measurement_increment"] == 0
    assert result["turnaround_increment"] == 15
    assert result["campaigns"] == 8 and result["independent_clusters"] == 2
    assert result["signflip"]["min_attainable_one_sided_p"] == 0.25


@pytest.mark.parametrize("field,value", [("problem_sha256", "b" * 64), ("endpoint", "another"),
                                       ("measurement_budget", 20), ("cluster_id", "foreign")])
def test_fair_comparison_rejects_changed_task(field, value):
    records = rows()
    records[-1] = replace(records[-1], **{field: value})
    with pytest.raises(ValueError, match="changes endpoint, problem, cluster or budget"):
        report(records)


def test_missing_pairs_and_duplicate_results_are_not_silently_removed():
    with pytest.raises(ValueError, match="same nonempty campaigns"):
        report(rows()[:-1])
    with pytest.raises(ValueError, match="duplicate"):
        report([*rows(), rows()[-1]])


def test_budget_violations_and_undeclared_prices_cannot_be_scored_as_zero_cost():
    with pytest.raises(ValueError, match="exceeds measurement budget"):
        replace(rows()[0], measurements=17)
    for price in (None, float("nan"), -1.0, True):
        with pytest.raises(ValueError, match="resource prices"):
            paired_campaign_report(rows(), reference="batch", candidate="adaptive",
                                   measurement_price=price, turnaround_price=0.0)


def test_single_independent_campaign_does_not_get_bootstrap_certainty():
    result = report(rows()[:2])
    assert result["cluster_bootstrap_95"] is None
    assert result["signflip"]["min_attainable_one_sided_p"] == 0.5


def test_monte_carlo_signflip_cannot_claim_a_zero_p_value():
    records = [replace(row, cluster_id=row.campaign_id) for row in
               [CampaignResult(str(i), str(i), arm, "observed", "a" * 64, 1,
                               0.0 if arm == "batch" else 1.0, 0, 0)
                for i in range(30) for arm in ("batch", "adaptive")]]
    result = report(records)
    assert not result["signflip"]["exact"]
    assert result["signflip"]["p_greater"] >= result["signflip"]["monte_carlo_resolution"] > 0


def test_equal_measurement_counts_can_still_violate_total_resource_fairness():
    with pytest.raises(ValueError, match="exceeds total resource budget"):
        report(rows(), resource_budget=CampaignBudget(18, 1, 2, "read-equivalents"))
    assert report(rows())["resource_budget"] is None


def test_two_rounds_displace_measurements_under_the_same_resource_cap():
    records = [replace(row, measurements=14, turnarounds=2) if row.arm == "adaptive" else row
               for row in rows()]
    result = report(records, resource_budget=CampaignBudget(18, 1, 2, "read-equivalents"))
    assert result["resource_budget"]["mean_spend"] == {"batch": 18, "adaptive": 18}
    assert result["measurement_increment"] == -2
    assert result["turnaround_increment"] == 1


def test_api_and_overhead_are_charged_in_declared_resource_and_utility_units():
    records = [replace(row, measurements=12, turnarounds=2,
                       other_resource_cost=2, other_utility_cost=0.2) if row.arm == "adaptive" else row
               for row in rows()]
    result = report(records, resource_budget=CampaignBudget(18, 1, 2, "read-equivalents"))
    assert result["resource_budget"]["maximum_spend"] == {"batch": 18, "adaptive": 18}
    assert result["net_utility_increment"] == pytest.approx(-0.11)
    with pytest.raises(ValueError, match="exceeds total"):
        report([replace(row, other_resource_cost=3) if row.arm == "adaptive" else row
                for row in records], resource_budget=CampaignBudget(18, 1, 2, "read-equivalents"))


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -1, True])
def test_total_budget_and_other_costs_reject_invalid_declarations(invalid):
    with pytest.raises(ValueError):
        CampaignBudget(18, invalid, 2, "read-equivalents")
    with pytest.raises(ValueError):
        replace(rows()[0], other_resource_cost=invalid)
    with pytest.raises(ValueError):
        replace(rows()[0], other_utility_cost=invalid)


def test_production_budget_preserves_checked_research_prototype():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert (root / "src/maestro/campaign_budget.py").read_bytes() == (
        root / "research/budgeted_feedback_20261011/contract/budget.py").read_bytes()
    budget = CampaignBudget(0.3, 0.1, 0, "declared units")
    assert budget.require_feasible(3, 0) == pytest.approx(0.3)
    with pytest.raises(ValueError):
        budget.require_feasible(True, 0)


def test_individually_paired_endpoints_cannot_be_pooled_in_different_units():
    records = [replace(row, endpoint="RNA correlation") if row.campaign_id == "0" else row
               for row in rows()]
    with pytest.raises(ValueError, match="pooled campaigns must share one endpoint"):
        report(records)


def test_finite_inputs_cannot_overflow_a_paired_utility_difference():
    records = [replace(row, terminal_utility=-1e308 if row.arm == "batch" else 1e308)
               for row in rows()[:2]]
    with pytest.raises(ValueError, match="derived campaign differences must be finite"):
        report(records)


def test_equal_overflowing_arm_costs_are_rejected_before_cancellation():
    with pytest.raises(ValueError, match="derived campaign costs must be finite"):
        paired_campaign_report(rows(), reference="batch", candidate="adaptive",
                               measurement_price=1e308, turnaround_price=0.0)


def test_finite_paired_effects_cannot_overflow_aggregation_or_bootstrap():
    records = [replace(row, terminal_utility=0.0 if row.arm == "batch" else 5e307)
               for row in rows()]
    with pytest.raises(ValueError, match="campaign aggregation must remain finite"):
        report(records)
    # The original sum is finite, but repeatedly sampling the large cluster
    # can overflow the bootstrap numerator.
    records = [replace(row, terminal_utility=(1e308 if row.campaign_id == "0" else 0.0)
                       if row.arm == "adaptive" else 0.0, cluster_id=row.campaign_id)
               for row in rows()[:4]]
    with pytest.raises(ValueError, match="bootstrap aggregation must remain finite"):
        report(records)
