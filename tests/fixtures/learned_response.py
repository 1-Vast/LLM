"""Constructed registered response model; random weights are never fitted here."""
import numpy as np
import pytest
import torch

from virtual_cell.learned_response import DoseAnchoredNetwork, LearnedTranscriptWorldModel
from virtual_cell.interface import Intervention, PredictionRequest, SystemContext


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
