"""Cost and dependence cannot turn a weak campaign into evidence of agent benefit."""
from dataclasses import replace

import pytest

from tools.evaluation.decision_report import CampaignResult, paired_campaign_report


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
