"""Interface fixtures and policy math, not evidence of biological validity."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
import pandas as pd

spec = importlib.util.spec_from_file_location("sequential_study", Path(__file__).with_name("sequential.py"))
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


def candidates():
    result = []
    for index in range(4):
        base = {"drug": f"drug{index}", "dose_uM": 5.0, "cell": "cell", "plate": "plate",
                "time_hours": 24.0, "split": "development", "reference_prediction": 1 + index / 10,
                "state_prediction": 1 + index / 10, "model_provenance_sha256": "fixture"}
        result.append(({**base, "condition_id": f"screen{index}", "response_role": "screen", "subset_sha256": f"screenhash{index}", "observed_rms": 1.1 + index / 10},
                       {**base, "condition_id": f"validation{index}", "response_role": "technical_validation", "subset_sha256": f"validationhash{index}", "observed_rms": 1.2 + index / 10}))
    return result


TRANSFER = {"slope": 0.8, "forecast_update_samples": [-.5, .5], "unacquired_rmse": .2, "acquired_rmse": .1}


def test_exact_lookahead_integral_and_stop():
    means = np.array([1.0, 0.9, 0.5, 0.1])
    samples = np.array([-.5, .5])
    one, _ = s.expected_best(means, (0, 1, 2, 3), samples, 1)
    two, _ = s.expected_best(means, (0, 1, 2, 3), samples, 2)
    assert two >= one >= means.max()
    view = [{"condition_id": str(i), "forecast": value, "acquired": False} for i, value in enumerate(means)]
    assert s.choose(view, 2, [0.0], "lookahead")[0] is None


def test_two_purchases_and_future_labels_isolated(tmp_path):
    items = candidates()
    first = s.episode(items, "state", TRANSFER, tmp_path / "first", "case1", "lookahead")
    altered = [(screen, {**validation, "observed_rms": -999}) for screen, validation in items]
    second = s.episode(altered, "state", TRANSFER, tmp_path / "second", "case2", "lookahead")
    assert [step["selected"] for step in first["steps"]] == [step["selected"] for step in second["steps"]]
    assert first["final_choice"] == second["final_choice"]
    assert first["budget"]["recorded_use"] == 3
    assert first["budget"]["reserved"] == 0
    for step in first["steps"]:
        assert all("observed_rms" not in row for row in step["public_view"])


def test_same_information_replay_and_duplicate_refusal(tmp_path):
    first = s.episode(candidates(), "reference", TRANSFER, tmp_path / "first", "case1", "lookahead")
    actions = [step["selected"] for step in first["steps"] if step["selected"] is not None]
    second = s.episode(candidates(), "reference", TRANSFER, tmp_path / "second", "case2", "myopic", shared_actions=actions)
    assert first["final_choice"] == second["final_choice"]
    with pytest.raises(ValueError, match="duplicate_acquisition"):
        s.episode(candidates(), "reference", TRANSFER, tmp_path / "third", "case3", "myopic", shared_actions=["screen0", "screen0"])


def test_stop_preserves_validation_budget(tmp_path):
    result = s.episode(candidates(), "reference", TRANSFER, tmp_path, "case", "stop")
    assert result["budget"]["recorded_use"] == 1
    assert result["initial_choice"] == result["final_choice"]


def test_dual_core_gate_refuses_inactive_state_and_no_opportunity():
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from eligibility import require_dual_core_opportunity, StudyNotEligible
    summary = {"endpoint": "signed_noise_corrected_mean_squared_native_rna_delta",
        "reference": {"myopic": {"mean_gain_vs_no_update": -.1}, "lookahead": {"mean_gain_vs_no_update": -.1}},
        "state": {"myopic": {"mean_gain_vs_no_update": .2}, "lookahead": {"mean_gain_vs_no_update": .1}}}
    with pytest.raises(StudyNotEligible, match="STATE_representation_inactive_gamma_zero_fallback"):
        require_dual_core_opportunity(pd.DataFrame({"state_representation_active": [False]}), summary)
    with pytest.raises(StudyNotEligible, match="no_development_gain_over_myopic_and_stop"):
        require_dual_core_opportunity(pd.DataFrame({"state_representation_active": [True]}), summary)
