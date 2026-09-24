"""Software boundary tests; constructed arrays are never biological measurements."""
import numpy as np
import pytest
import torch

from virtual_cell.learned_response import DoseAnchoredNetwork, fit_response
from evaluation.model_validation import molecular_split, paired_interval
from dataclasses import replace
from virtual_cell.learned_response import LearnedTranscriptWorldModel
from virtual_cell.interface import Intervention, PredictionRequest, SystemContext, safe_predict


def test_molecular_aliases_never_cross_partitions():
    molecules = [f"molecule-{i}" for i in range(100)]
    split = molecular_split(molecules + molecules[:20])
    assert split == molecular_split(molecules[::-1])
    assert {s: list(split.values()).count(s) for s in set(split.values())} == {
        "train": 60, "validation": 15, "calibration": 10, "test": 15}


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


def test_cluster_interval_counts_molecules_not_cells():
    result = paired_interval(np.array([1., 1., -1.]), np.array(["a", "a", "b"]))
    assert result["clusters"] == 2
    assert result["mean"] == 0


def test_training_refuses_nonfinite_values():
    x = np.ones((5, 3))
    y = np.ones((5, 1))
    with pytest.raises(ValueError, match="invalid_training_data"):
        fit_response(x * np.nan, np.ones(5), y, x, np.ones(5), y, seed=11)


@pytest.fixture
def registered_model(tmp_path):
    genes = np.array(["ENSG1", "ENSG2"])
    np.savez(tmp_path / "model_parameters.npz", genes=genes,
             target_components=np.ones((1, 2)), baseline_components=np.ones((16, 2)),
             multimodal_neural_feature_mean=np.zeros(529), multimodal_neural_feature_scale=np.ones(529))
    for seed in (11, 29, 47):
        torch.save(DoseAnchoredNetwork(529, 1).state_dict(), tmp_path / f"multimodal_neural_{seed}.pt")
    record = {"context": "A549", "compound": "example", "smiles": "CCO", "baseline": [1., 2.], "genes": genes}
    model = LearnedTranscriptWorldModel(tmp_path, {"baseline": record})
    request = PredictionRequest("query", "case", "contrast", 1, Intervention("example", "drug", (), 100, "nM", 24),
                                SystemContext("A549", "constructed test", "baseline", "baseline", "Homo sapiens"),
                                ("transcript_shift_rms",), model.model_version)
    return model, request


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
