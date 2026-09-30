"""One chemical unit cannot supply a meaningful resampled uncertainty interval."""
from copy import deepcopy

from research.dual_core_live.reanalyse import correct_intervals


def test_single_unit_intervals_removed_without_changing_estimates_or_input():
    source = {"reading": {"units": 1, "mean": .6, "ci": [.6, .6]}, "utility": 1,
              "many": {"units": 6, "mean": .5, "ci": [.2, .8]}}
    frozen = deepcopy(source)
    result, changes = correct_intervals(source)
    assert source == frozen and result["utility"] == 1
    assert result["reading"]["mean"] == .6 and result["reading"]["ci"] is None
    assert result["many"] == source["many"]
    assert len(changes) == 1 and changes[0]["reason"] == "insufficient_independent_units"


def test_zero_observed_variance_is_conditional_and_existing_refusals_preserved():
    source = {"delta": {"units": 6, "mean": 0, "ci": [0, 0]},
              "physical": {"units": 1, "mean": 0, "ci": None}}
    result, _ = correct_intervals(source)
    assert result["delta"]["uncertainty_status"] == "zero_observed_variance_conditional_bootstrap"
    assert result["physical"] == source["physical"]
