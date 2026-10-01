"""Real execution of software routing; constructed forecasts are not biology."""
import numpy as np
import pytest

from research.astra.influence_audit import compare_paths, software_swaps


def test_no_action_change_has_undefined_conditional_terminal_influence():
    result = compare_paths({"q": {"action": "a", "terminal": "correct"}},
                           {"q": {"action": "a", "terminal": "wrong"}})
    assert result["action_influence"] == 0
    assert result["terminal_changes_given_action_change"] is None


def test_abstention_changes_not_counted_as_concrete_action_switch():
    result = compare_paths({"q": {"action": None}}, {"q": {"action": "a"}})
    assert result["abstention_changes"] == 1
    assert result["concrete_action_changes"] == 0
    assert result["terminal_utility"] == "not_identified"


def test_forecast_policy_and_timing_swaps_execute_actual_path(tmp_path):
    result = software_swaps(tmp_path)
    assert len(result["records"]) == 12
    assert result["forecast_swap"]["concrete_action_changes"] == 1
    assert result["policy_swap"]["concrete_action_changes"] == 1
    assert result["timing_swap"]["action_changes"] == 0
    assert all(r["forecaster_calls"] == 2 for r in result["records"])
    assert all(not r["observed_real_experiment"] for r in result["records"])
    assert all(r["planned_cost"] == 1 and r["actual_experiment_cost"] is None for r in result["records"])
    for record in result["records"]:
        first_forecast = record["events"].index("forecast:a")
        planner = record["events"].index("planner")
        assert (first_forecast < planner) == (record["timing"] == "early")


@pytest.mark.parametrize("count", [True, False, 0, -1, 1.5])
def test_request_count_must_be_declared_positive_integer(count):
    from tools.datasets.state_prospective_input import validate_requests
    with pytest.raises(ValueError, match="positive predeclared"):
        validate_requests(None, ["drug"], count, {})


@pytest.mark.parametrize("menu", [[], ["a", "a"], ["[('DMSO_TF', 0.0, 'uM')]"]])
def test_query_menu_cannot_include_controls_or_duplicates(menu):
    from tools.datasets.state_prospective_input import validate_requests
    with pytest.raises(ValueError, match="unique noncontrol"):
        validate_requests(None, menu, 1, {})


def test_nonfinite_request_placeholders_are_rejected():
    import anndata as ad
    import pandas as pd
    from tools.datasets.state_prospective_input import CONTROL, CONTEXT, KEY, PERT, build_requests, validate_requests
    contract = {"axis": ["A", "B"], "feature_count": 2, "mapping": {CONTROL: 0, "drug": 1}}
    baseline = ad.AnnData(obs=pd.DataFrame({PERT: [CONTROL], "cell_name": [CONTEXT], "plate": ["p"],
                                           "role": ["baseline_control"]}, index=["c"]))
    baseline.uns["state_feature_axis"] = ["A", "B"]
    baseline.obsm[KEY] = np.array([[1., 2.]], dtype=np.float32)
    query = build_requests(baseline, ["drug"], 2, contract)
    query.obsm[KEY][1, 0] = np.nan
    with pytest.raises(ValueError, match="nonfinite query"):
        validate_requests(query, ["drug"], 2, contract)
