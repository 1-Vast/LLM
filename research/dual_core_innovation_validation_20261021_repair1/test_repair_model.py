"""Synthetic checks of reproducibility and paid-feedback plumbing, not biology."""
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).parent))
import repair_model as R


@pytest.fixture(autouse=True)
def small_cpu_threads():
    old = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(old)


def inputs():
    rng = np.random.default_rng(18)
    return {k: rng.normal(size=(3, n)).astype("float32")
            for k, n in (("x", 5), ("pert", 5), ("fpA", 4), ("fpB", 4))}


def backend(seed=3):
    return R.FeedbackBackend(R.build_model(5, 4, seed, hidden=4), inputs(), {"a": 0, "b": 1, "c": 2}, steps=3)


def molecular(value=1.0):
    y = np.full((3, 5), value, dtype="float32")
    mask = np.zeros_like(y, dtype=bool)
    mask[1] = True
    return {"y": y, "mask": mask}


def test_seed_precedes_initialization_and_training_reproduces():
    a = R.build_model(5, 4, seed=3, hidden=4)
    b = R.build_model(5, 4, seed=3, hidden=4)
    c = R.build_model(5, 4, seed=4, hidden=4)
    assert R.parameter_id(a) == R.parameter_id(b)
    assert R.parameter_id(a) != R.parameter_id(c)
    tens = R._input_tensors(inputs())
    tens.update(y=torch.ones(3, 3, 5), yobs=torch.ones(3, 3, 5),
                lab=torch.tensor([0.0, 1.0, 0.0]), single=torch.ones(3, dtype=torch.bool))
    R.M.train(a, tens, epochs=2, bs=2, seed=7)
    R.M.train(b, tens, epochs=2, bs=2, seed=7)
    assert R.parameter_id(a) == R.parameter_id(b)


@pytest.mark.parametrize("kind,value", [("f", 1), ("m", molecular())])
def test_paid_observation_changes_shared_model_and_unqueried_predictions(kind, value):
    b = backend()
    initial = b.model_id
    diag = b.observe(kind, "a", value)
    assert initial != b.model_id
    assert diag["before_model_id"] == initial
    assert diag["after_model_id"] == b.model_id
    assert diag["support_keys"] == [[kind, "a"]]
    assert diag["max_unqueried_prediction_delta"] > 1e-8


def test_feedback_is_reproducible_from_same_support():
    a, b = backend(), backend()
    for candidate in (a, b):
        candidate.observe("m", "a", molecular())
        candidate.observe("f", "b", 0)
    assert a.model_id == b.model_id
    assert a.predict() == b.predict()


@pytest.mark.parametrize("key", ["y", "yobs", "lab", "labels", "hidden_outcomes"])
def test_hidden_targets_are_rejected_at_input_boundary(key):
    poisoned = inputs()
    poisoned[key] = np.ones((3, 5))
    with pytest.raises(ValueError, match="targets are forbidden"):
        R.FeedbackBackend(R.build_model(5, 4), poisoned, {"a": 0, "b": 1, "c": 2})


def test_external_input_and_model_changes_cannot_modify_private_backend():
    model, x = R.build_model(5, 4, hidden=4), inputs()
    b = R.FeedbackBackend(model, x, {"a": 0, "b": 1, "c": 2})
    before = b.predict()
    x["x"][:] = 1000
    with torch.no_grad():
        next(model.parameters()).fill_(500)
    assert b.predict() == before


def test_unobserved_molecular_targets_do_not_affect_feedback():
    a, b = backend(), backend()
    first, second = molecular(), molecular()
    first["y"][[0, 2]] = np.nan
    second["y"][[0, 2]] = 1e20
    a.observe("m", "a", first)
    b.observe("m", "a", second)
    assert a.model_id == b.model_id
    assert a.predict() == b.predict()


def test_heldout_outcomes_are_never_requested_by_backend():
    # The backend only receives allowed inputs and one paid label. A separate
    # evaluator's unobserved targets cannot enter initialization or feedback.
    left_hidden = {"a": 1, "b": 0, "c": 0}
    right_hidden = {"a": 1, "b": 1, "c": 1}
    a, b = backend(), backend()
    a.observe("f", "a", left_hidden["a"])
    b.observe("f", "a", right_hidden["a"])
    assert a.model_id == b.model_id
    assert a.predict() == b.predict()
    assert list(a.observations) == [("f", "a")]


def test_invalid_or_duplicate_observation_does_not_modify_model():
    b = backend()
    initial = b.model_id
    for kind, drug, value in [("f", "a", 2), ("f", "unknown", 1), ("m", "a", {"score": 1})]:
        with pytest.raises(ValueError):
            b.observe(kind, drug, value)
        assert b.model_id == initial
        assert not b.observations
    b.observe("f", "a", 1)
    initial = b.model_id
    with pytest.raises(ValueError, match="Duplicate"):
        b.observe("f", "a", 0)
    assert b.model_id == initial


def test_static_and_conventional_update_are_explicit_controls():
    priors = {"a": 0.4, "b": 0.3, "c": 0.2}
    s = R.StaticBackend(priors)
    k = R.KernelBackend(priors, {"a": [1, 0], "b": [1, 0], "c": [0, 1]})
    assert s.observe("f", "a", 1)["max_prediction_delta"] == 0
    old_id = k.model_id
    diag = k.observe("f", "a", 1)
    assert old_id != k.model_id
    assert diag["max_unqueried_prediction_delta"] > 0
    assert k.predict()["b"] > priors["b"]
    assert k.predict()["c"] == priors["c"]
    assert k.observe("m", "b", molecular())["max_prediction_delta"] == 0
