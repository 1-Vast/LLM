"""Dose-anchored transcript inference and registered readouts."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import numpy as np
import torch
from torch import nn
from .interface import Interval
from .biology import GeneSet, score_gene_set


def transcript_readouts(samples, genes, readouts, gene_sets=()):
    """Project ensemble RNA shifts without converting model spread to confidence.

    Each row is one model's gene-aligned response, not one independent cell.
    Gene-set means retain their sign and use the existing strict membership rule.
    The envelope includes the ensemble point estimate (important for nonlinear RMS).
    """
    samples = np.asarray(samples)
    genes = tuple(str(gene) for gene in genes)
    if (samples.ndim != 2 or samples.shape[0] == 0 or samples.shape[1] != len(genes)
            or not genes or len(set(genes)) != len(genes) or not np.isfinite(samples).all()):
        raise ValueError("invalid_transcript_ensemble")
    sets = {"rna_set:" + item.identifier: item for item in gene_sets}
    indices = {"rna_gene:" + gene: i for i, gene in enumerate(genes)}
    point = samples.mean(axis=0)
    values, intervals = {}, {}
    for name in readouts:
        if name == "transcript_shift_rms":
            value = float(np.sqrt(np.mean(point ** 2)))
            members = np.sqrt(np.mean(samples ** 2, axis=1))
            basis = "Ensemble member RMS and RMS of mean response; descriptive envelope only."
        elif name in indices:
            members = samples[:, indices[name]]
            value = float(point[indices[name]])
            basis = "Ensemble member RNA shifts; no predictive coverage claim."
        elif name in sets:
            gene_set = sets[name]
            members = np.array([score_gene_set(dict(zip(genes, row)), gene_set) for row in samples])
            value = float(members.mean())
            basis = f"Mean RNA shift; gene_set={gene_set.digest}; source={gene_set.source_sha256}; descriptive ensemble envelope."
        else:
            raise ValueError("readout_not_served:" + name)
        values[name] = value
        intervals[name] = Interval(float(min(members.min(), value)), float(max(members.max(), value)), basis=basis)
    return values, intervals


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




class LearnedTranscriptWorldModel:
    """Serve a fitted ensemble on explicit baseline-RNA registrations, not outcomes.

    Registration permits execution, not an in-distribution or causal claim. The
    backend keeps distribution status unknown until a separate domain validation
    exists, so the agent cannot silently promote this experiment into authority.
    """

    def __init__(self, directory: Path, registrations: dict, *, gene_sets: tuple[GeneSet, ...] = ()):
        self.directory = Path(directory)
        self.registrations = registrations
        self.gene_sets = tuple(gene_sets)
        if len({item.identifier for item in self.gene_sets}) != len(self.gene_sets):
            raise ValueError("gene_set_identifiers_must_be_unique")
        for item in self.gene_sets:
            if (not item.identifier.strip() or not item.members or len(set(item.members)) != len(item.members)
                    or not item.source.strip() or not item.rule.strip()
                    or len(item.source_sha256) != 64
                    or any(c not in "0123456789abcdefABCDEF" for c in item.source_sha256)):
                raise ValueError("invalid_gene_set_registration")
        self.parameters = dict(np.load(self.directory / "model_parameters.npz", allow_pickle=False))
        self.models = []
        paths = sorted(self.directory.glob("multimodal_neural_*.pt"))
        if len(paths) != 3:
            raise ValueError("three_registered_seeds_required")
        digest = hashlib.sha256((self.directory / "model_parameters.npz").read_bytes())
        digest.update(b"signed_transcript_readouts_v1")
        digest.update(json.dumps([asdict(item) for item in sorted(self.gene_sets, key=lambda x: x.identifier)],
                                 sort_keys=True).encode("utf-8"))
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
        from .interface import QueryAssessment, QuerySupport, condition_response_limitations
        errors = list(request.validation_errors())
        if errors:
            return QueryAssessment(QuerySupport.UNSUPPORTED, (), tuple(errors), self.capabilities())
        errors.extend(condition_response_limitations(request))
        if request.model_version != self.model_version:
            errors.append("model_version_mismatch")
        genes = set(str(gene) for gene in self.parameters["genes"])
        gene_readouts = {"rna_gene:" + gene for gene in genes}
        sets = {"rna_set:" + item.identifier: item for item in self.gene_sets}
        for name in request.readouts:
            if name == "transcript_shift_rms" or name in gene_readouts:
                continue
            if name in sets:
                if not set(sets[name].members).issubset(genes):
                    errors.append("readout_missing_genes:" + name)
            else:
                errors.append("readout_not_served:" + name)
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
        samples = np.concatenate([model.predict(features, np.array([dose])) for model in self.models], axis=0) @ self.parameters["target_components"]
        if not np.isfinite(samples).all():
            return StatePrediction(False, None, None, ("A transcript ensemble member returned a nonfinite value.",),
                                   request_id=request.request_id, model_version=self.model_version,
                                   in_distribution=None, abstain_reason="nonfinite_transcript_prediction")
        values, intervals = transcript_readouts(samples, self.parameters["genes"], request.readouts, self.gene_sets)
        return StatePrediction(True, values, None,
                               ("RNA shift only; no functional assay or causal mechanism inferred.",
                                "Gene-set scores are RNA proxies, not measured pathway or target activity.",
                                "Ensemble envelopes describe model disagreement, not calibrated predictive intervals.",
                                "This registration is executable; independent domain validation is absent."),
                               request_id=request.request_id, model_version=self.model_version,
                               supported_variables=tuple(values), intervals=intervals, confidence=None, in_distribution=None,
                               uncertainty_components={"distribution": "Independent domain validation absent.",
                                                       "ensemble": "Three fitted seeds; their spread excludes unmeasured assay noise and domain shift.",
                                                       "measurement": "Single-study pseudobulk and source replicate uncertainty."})
