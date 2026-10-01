"""Software contracts for actual tensor pairing, not efficacy tests."""
import numpy as np
import pytest
import torch

from research.astra.paired_state import CONTROL, PairedBasal, paired_hook, tensor_digest


def batch(action="A", count=3):
    encoding = torch.zeros(count, 2)
    encoding[:, {"A": 0, "B": 1, CONTROL: 0}[action]] = 1
    return {"ctrl_cell_emb": torch.full((count, 2), 9.0), "pert_name": [action] * count,
            "pert_emb": encoding, "batch": torch.ones(count, dtype=torch.long)}


def pairing():
    return PairedBasal(np.arange(6, dtype=np.float32).reshape(3, 2), ["A", "B"],
                       [4, 1, 4], ["c4", "c1", "c4"], {"A": 0, "B": 1})


class Model:
    def predict_step(self, value, **kwargs):
        return {"preds": value["ctrl_cell_emb"] + value["pert_emb"]}


def test_same_ordered_actual_tensor_and_metadata_across_actions():
    paired = pairing()
    original = Model.predict_step
    a, b, control = batch("A"), batch("B"), batch(CONTROL)
    with paired_hook(Model, paired):
        model = Model()
        model.predict_step(a)
        model.predict_step(b)
        model.predict_step(control)
        paired.validate_complete()
    assert Model.predict_step is original
    assert paired.calls[0]["basal_sha256"] == paired.calls[1]["basal_sha256"]
    assert paired.calls[0]["source_indices_zero_based"] == [4, 1, 4]
    assert paired.calls[2]["basal_sha256"] == tensor_digest(control["ctrl_cell_emb"])
    assert torch.equal(a["ctrl_cell_emb"], torch.full((3, 2), 9.0))
    assert torch.equal(a["batch"], torch.ones(3, dtype=torch.long))


@pytest.mark.parametrize("mutation", ["count", "menu", "encoding", "repeat"])
def test_reject_frozen_query_mutation_and_restore(mutation):
    paired, original = pairing(), Model.predict_step
    value = batch("A", 2 if mutation == "count" else 3)
    if mutation == "menu":
        value["pert_name"] = ["unknown"] * 3
    if mutation == "encoding":
        value["pert_emb"] = torch.zeros(3, 2)
    with pytest.raises(ValueError):
        with paired_hook(Model, paired):
            if mutation == "repeat":
                Model().predict_step(batch("A"))
            Model().predict_step(value)
    assert Model.predict_step is original


def test_missing_action_never_completes():
    paired = pairing()
    with paired_hook(Model, paired):
        Model().predict_step(batch("A"))
    with pytest.raises(ValueError, match="not every"):
        paired.validate_complete()


def test_metadata_or_actual_input_mutation_rejected():
    class Mutating(Model):
        def predict_step(self, value, **kwargs):
            value["batch"].zero_()
            return super().predict_step(value, **kwargs)
    paired = pairing()
    with pytest.raises(ValueError, match="mutated"):
        with paired_hook(Mutating, paired):
            Mutating().predict_step(batch("A"))


def test_backend_failure_restores_hook():
    class Failed(Model):
        def predict_step(self, value, **kwargs):
            raise RuntimeError("real failure fixture")
    original = Failed.predict_step
    with pytest.raises(RuntimeError):
        with paired_hook(Failed, pairing()):
            Failed().predict_step(batch("A"))
    assert Failed.predict_step is original
