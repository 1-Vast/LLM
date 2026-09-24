"""Small dose-anchored response regressor; latent coordinates are not functional assays."""
from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn


class DoseAnchoredNetwork(nn.Module):
    """Predict a transcript shift with exactly zero shift at vehicle dose.

    The zero boundary is structural. Monotonicity of each gene is deliberately not
    imposed: real feedback, stress and cell-cycle responses need not be monotone.
    """

    def __init__(self, input_size: int, output_size: int):
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(input_size, 128), nn.GELU(),
                                    nn.Linear(128, 64), nn.GELU(), nn.Linear(64, output_size))

    def forward(self, features, dose_gate):
        return self.layers(features) * dose_gate[:, None]


@dataclass
class ResponseFit:
    network: DoseAnchoredNetwork
    history: list[dict[str, float]]
    selected_epoch: int
    seed: int

    def predict(self, features: np.ndarray, dose_gate: np.ndarray) -> np.ndarray:
        if not np.isfinite(features).all() or not np.isfinite(dose_gate).all() or np.any(dose_gate < 0):
            raise ValueError("invalid_response_input")
        device = next(self.network.parameters()).device
        self.network.eval()
        with torch.no_grad():
            return self.network(torch.as_tensor(features, dtype=torch.float32, device=device),
                                torch.as_tensor(dose_gate, dtype=torch.float32, device=device)).cpu().numpy()


def fit_response(train_x, train_gate, train_y, validation_x, validation_gate, validation_y,
                 *, seed: int, epochs: int = 150, patience: int = 20, device: str = "cpu") -> ResponseFit:
    """Use validation only for early stopping; this function accepts no test labels."""
    arrays = [np.asarray(a, dtype=np.float32) for a in
              (train_x, train_gate, train_y, validation_x, validation_gate, validation_y)]
    if any(not np.isfinite(a).all() for a in arrays) or len(train_x) == 0 or len(validation_x) == 0:
        raise ValueError("invalid_training_data")
    if np.any(arrays[1] < 0) or np.any(arrays[4] < 0):
        raise ValueError("negative_dose_gate")
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.set_num_threads(4)
    if device == "cuda":
        torch.cuda.manual_seed_all(seed)
    model = DoseAnchoredNetwork(arrays[0].shape[1], arrays[2].shape[1]).to(device)
    x, gate, y, vx, vg, vy = [torch.as_tensor(a, device=device) for a in arrays]
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    best, chosen, stale, history, state = float("inf"), 0, 0, [], None
    for epoch in range(1, epochs + 1):
        model.train()
        order = torch.randperm(len(x), device=device)
        for batch in order.split(256):
            optimizer.zero_grad(set_to_none=True)
            loss = (model(x[batch], gate[batch]) - y[batch]).square().mean()
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            train_loss = float((model(x, gate) - y).square().mean())
            value = float((model(vx, vg) - vy).square().mean())
        history.append({"epoch": epoch, "train_mse": train_loss, "validation_mse": value})
        if value < best:
            best, chosen, stale, state = value, epoch, 0, copy.deepcopy(model.state_dict())
        else:
            stale += 1
        if stale >= patience:
            break
    model.load_state_dict(state)
    return ResponseFit(model, history, chosen, seed)


class LearnedTranscriptWorldModel:
    """Serve a fitted ensemble on explicit baseline-RNA registrations, not outcomes.

    Registration permits execution, not an in-distribution or causal claim. The
    backend keeps distribution status unknown until a separate domain validation
    exists, so the agent cannot silently promote this experiment into authority.
    """

    def __init__(self, directory: Path, registrations: dict):
        self.directory = Path(directory)
        self.registrations = registrations
        self.parameters = dict(np.load(self.directory / "model_parameters.npz", allow_pickle=False))
        self.models = []
        paths = sorted(self.directory.glob("multimodal_neural_*.pt"))
        if len(paths) != 3:
            raise ValueError("three_registered_seeds_required")
        digest = hashlib.sha256((self.directory / "model_parameters.npz").read_bytes())
        for path in paths:
            digest.update(path.read_bytes())
            net = DoseAnchoredNetwork(len(self.parameters["multimodal_neural_feature_mean"]),
                                      len(self.parameters["target_components"]))
            net.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
            net.eval()
            self.models.append(ResponseFit(net, [], 0, 0))
        self.model_version = "sciplex_transcript_" + digest.hexdigest()[:16]

    def capabilities(self):
        from .interface import ModelCapabilities
        return ModelCapabilities("dose_anchored_transcript", self.model_version,
                                 "matched baseline RNA and radius-2 molecular fingerprints", "canonical SMILES",
                                 ("drug",), True, True, True, None)

    def assess_query(self, request):
        from .interface import QueryAssessment, QuerySupport
        errors = list(request.validation_errors())
        if errors:
            return QueryAssessment(QuerySupport.UNSUPPORTED, (), tuple(errors), self.capabilities())
        if request.model_version != self.model_version:
            errors.append("model_version_mismatch")
        errors.extend("readout_not_served:" + name for name in request.readouts if name != "transcript_shift_rms")
        record = self.registrations.get(request.context.dataset_id)
        if record is None:
            errors.append("baseline_unregistered")
        else:
            if request.context.control_dataset_id != request.context.dataset_id:
                errors.append("matched_control_identity_mismatch")
            if request.context.identifier != record["context"]:
                errors.append("context_mismatch")
            if request.context.species != "Homo sapiens":
                errors.append("species_not_registered")
            if request.intervention.identifier != record["compound"]:
                errors.append("compound_mismatch")
            if request.intervention.mode != "drug" or request.intervention.time_hours != 24:
                errors.append("intervention_time_or_mode_unsupported")
            if request.intervention.dose_unit != "nM" or request.intervention.dose not in {0, 10, 100, 1000, 10000}:
                errors.append("dose_not_registered")
            baseline = np.asarray(record["baseline"])
            if baseline.shape != (len(self.parameters["genes"]),) or not np.isfinite(baseline).all():
                errors.append("baseline_coordinates_invalid")
            if not np.array_equal(record.get("genes"), self.parameters["genes"]):
                errors.append("baseline_gene_order_mismatch")
        return QueryAssessment(QuerySupport.UNSUPPORTED if errors else QuerySupport.SUPPORTED, (), tuple(errors), self.capabilities())

    def predict(self, request):
        from rdkit import Chem
        from rdkit.Chem import rdFingerprintGenerator
        from .interface import QuerySupport, StatePrediction
        assessment = self.assess_query(request)
        if assessment.support is not QuerySupport.SUPPORTED:
            return StatePrediction(False, None, None, assessment.limitations, request_id=request.request_id,
                                   model_version=self.model_version, in_distribution=False, abstain_reason="query_unsupported")
        record = self.registrations[request.context.dataset_id]
        mol = Chem.MolFromSmiles(record["smiles"])
        if mol is None:
            return StatePrediction(False, None, None, ("invalid_registered_structure",), request_id=request.request_id,
                                   model_version=self.model_version, in_distribution=False, abstain_reason="invalid_registered_structure")
        fingerprint = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=512).GetFingerprintAsNumPy(mol)
        latent = np.asarray(record["baseline"]) @ self.parameters["baseline_components"].T
        dose = np.log1p(request.intervention.dose) / np.log1p(10000.)
        features = np.r_[fingerprint, latent, dose][None, :]
        features = (features - self.parameters["multimodal_neural_feature_mean"]) / self.parameters["multimodal_neural_feature_scale"]
        shift = np.mean([model.predict(features, np.array([dose])) for model in self.models], axis=0) @ self.parameters["target_components"]
        return StatePrediction(True, {"transcript_shift_rms": float(np.sqrt(np.mean(shift ** 2)))}, None,
                               ("RNA shift only; no functional assay or causal mechanism inferred.",
                                "This registration is executable; independent domain validation is absent."),
                               request_id=request.request_id, model_version=self.model_version,
                               supported_variables=("transcript_shift_rms",), confidence=None, in_distribution=None,
                               uncertainty_components={"distribution": "Independent domain validation absent.",
                                                       "measurement": "Single-study pseudobulk and source replicate uncertainty."})
