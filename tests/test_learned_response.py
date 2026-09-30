"""Software boundary tests; constructed arrays are never biological measurements."""
import numpy as np
import pytest
import torch

from virtual_cell.learned_response import DoseAnchoredNetwork, fit_response
from dataclasses import replace
from virtual_cell.interface import safe_predict


def test_zero_dose_boundary_is_exact_for_any_weights():
    net = DoseAnchoredNetwork(5, 3)
    assert torch.equal(net(torch.randn(7, 5), torch.zeros(7)), torch.zeros(7, 3))


def test_small_response_fit_learns_and_restores_selected_epoch():
    rng = np.random.default_rng(11)
    x = rng.normal(size=(80, 3)).astype("float32")
    gate = np.ones(80, dtype="float32")
    y = x[:, :1] * .2
    fit = fit_response(x[:60], gate[:60], y[:60], x[60:], gate[60:], y[60:], seed=11, epochs=45)
    assert np.square(fit.predict(x[60:], gate[60:]) - y[60:]).mean() < np.square(y[60:]).mean()
    assert fit.selected_epoch == min(fit.history, key=lambda h: h["validation_mse"])["epoch"]
    with pytest.raises(ValueError, match="invalid_response_input"):
        fit.predict(np.full((1, 3), np.nan), np.ones(1))


def test_training_refuses_nonfinite_values():
    x = np.ones((5, 3))
    y = np.ones((5, 1))
    with pytest.raises(ValueError, match="invalid_training_data"):
        fit_response(x * np.nan, np.ones(5), y, x, np.ones(5), y, seed=11)


from tests.fixtures.learned_response import registered_model


@pytest.mark.parametrize("changed", ["readout", "dose", "time", "context", "species", "control", "genes"])
def test_learned_query_refuses_before_inference(registered_model, monkeypatch, changed):
    model, request = registered_model
    if changed == "readout":
        request = replace(request, readouts=("viability",))
    elif changed in {"dose", "time"}:
        request = replace(request, intervention=replace(request.intervention, **{"dose" if changed == "dose" else "time_hours": 77}))
    elif changed == "genes":
        model.registrations["baseline"]["genes"] = ["ENSG2", "ENSG1"]
    else:
        key = {"context": "identifier", "species": "species", "control": "control_dataset_id"}[changed]
        request = replace(request, context=replace(request.context, **{key: "wrong"}))
    monkeypatch.setattr(model, "predict", lambda _: pytest.fail("unsupported query reached inference"))
    assessment, prediction = safe_predict(model, request)
    assert prediction.abstain_reason == "query_unsupported"
    assert assessment.limitations


def test_learned_query_keeps_unknown_domain_and_zero_vehicle(registered_model):
    model, request = registered_model
    _, prediction = safe_predict(model, request)
    assert prediction.applicable and prediction.contract_errors() == ()
    assert prediction.in_distribution is None and prediction.confidence is None
    _, vehicle = safe_predict(model, replace(request, intervention=replace(request.intervention, dose=0)))
    assert vehicle.state_change == {"transcript_shift_rms": 0.0}
