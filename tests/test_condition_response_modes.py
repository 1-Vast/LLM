"""Condition-response backends must not silently ignore conditional requests."""
from dataclasses import replace

import pytest

from tests.fixtures.state import adapter, request as state_request
from tests.fixtures.learned_response import registered_model
from tests.fixtures.state import development_mean_baseline as _baseline
from tests.fixtures.response_rung import _build, _request as response_request
from virtual_cell.interface import QuerySupport, safe_predict


@pytest.fixture(params=("state", "development_mean", "sciplex_response", "learned_response"))
def condition_backend(request, tmp_path):
    if request.param == "state":
        return adapter(tmp_path), state_request()
    if request.param == "development_mean":
        model = _baseline()
        return model, replace(state_request(), model_version=model.model_version)
    if request.param == "sciplex_response":
        model = _build(tmp_path)
        return model, response_request(model)
    return request.getfixturevalue("registered_model")


@pytest.mark.parametrize("changes, reason", [
    ({"forecast_mode": "hypothesis_conditional", "hypotheses": ("h1", "h2")},
     "forecast_mode_not_supported:hypothesis_conditional"),
    ({"forecast_mode": "history_aware", "history": ({"action": "prior", "outcome": "positive"},)},
     "forecast_mode_not_supported:history_aware"),
    ({"forecast_mode": "hypothesis_conditional_history", "hypotheses": ("h1", "h2"),
      "history": ({"action": "prior", "outcome": "positive"},)},
     "forecast_mode_not_supported:hypothesis_conditional_history"),
    ({"hypotheses": ("h1", "h2")}, "hypothesis_conditioning_not_supported"),
    ({"forecast_mode": "state", "hypotheses": ("h1", "h2")}, "hypothesis_conditioning_not_supported"),
    ({"history": ({"action": "prior", "outcome": "positive"},)}, "history_conditioning_not_supported"),
    ({"forecast_mode": "state", "history": ({"action": "prior", "outcome": "positive"},)},
     "history_conditioning_not_supported"),
])
def test_condition_response_refuses_unserved_information(condition_backend, changes, reason, monkeypatch):
    model, ordinary = condition_backend
    assert model.assess_query(ordinary).support is QuerySupport.SUPPORTED
    assert model.assess_query(replace(ordinary, forecast_mode="state")).support is QuerySupport.SUPPORTED
    conditional = replace(ordinary, **changes)
    assert conditional.validation_errors() == ()
    assessment = model.assess_query(conditional)
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert reason in assessment.limitations
    # Direct callers and the protected boundary must both refuse without model inference.
    prediction = model.predict(conditional)
    assert not prediction.applicable and prediction.state_change is None
    assert reason in prediction.limitations or reason in (prediction.abstain_reason or "")
    monkeypatch.setattr(type(model), "predict", lambda self, _: pytest.fail("conditional request reached inference"))
    _, protected = safe_predict(model, conditional)
    assert not protected.applicable and protected.abstain_reason == "query_unsupported"
    assert reason in protected.limitations


def test_state_refusal_precedes_asset_inspection(tmp_path, monkeypatch):
    model = adapter(tmp_path)
    conditional = replace(state_request(), forecast_mode="hypothesis_conditional", hypotheses=("h1", "h2"))
    monkeypatch.setattr(model, "_inspect", lambda _: pytest.fail("unsupported conditional request inspected assets"))
    assert model.assess_query(conditional).support is QuerySupport.UNSUPPORTED
