"""Dose-anchored transcript and population models with validation-only fitting."""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import numpy as np
import torch
from torch import nn
from .interface import Interval
from .biology import GeneSet, score_gene_set
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist


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




def _population(value):
    value = np.asarray(value, dtype=np.float32)
    if value.ndim != 2 or min(value.shape) < 1 or not np.isfinite(value).all():
        raise ValueError("invalid_cell_population")
    return value


def population_mmd(predicted, observed, bandwidth: float) -> float:
    """Biased Gaussian MMD²; supports unequal set sizes and no cell pairing.

    Bandwidth must be fixed from training data, not selected on test outcomes.
    This descriptive distance is not an uncertainty or significance estimate.
    """
    x, y = _population(predicted), _population(observed)
    if x.shape[1] != y.shape[1] or not np.isfinite(bandwidth) or bandwidth <= 0:
        raise ValueError("invalid_distribution_coordinates_or_bandwidth")
    kernel = lambda a, b: np.exp(-cdist(a, b, "sqeuclidean") / (2 * bandwidth ** 2))
    return float(max(0., kernel(x, x).mean() + kernel(y, y).mean() - 2 * kernel(x, y).mean()))


@dataclass(frozen=True)
class PopulationPair:
    """One matched experimental context, with independently sampled populations.

    group is the outer split unit (e.g. chemical connectivity identity), not a
    cell ID. condition contains only inference-available intervention/context
    covariates. dose_gate is a dimensionless nonnegative dose transform.
    """
    control: np.ndarray
    treated: np.ndarray
    condition: np.ndarray
    dose_gate: float
    group: str

    def validate(self):
        x, y = _population(self.control), _population(self.treated)
        c = np.asarray(self.condition)
        if (x.shape[1] != y.shape[1] or c.ndim != 1 or not len(c)
                or not np.isfinite(c).all() or not np.isfinite(self.dose_gate)
                or self.dose_gate < 0 or not self.group.strip()):
            raise ValueError("invalid_population_condition")


class ConditionalPopulationFlow(nn.Module):
    """Small control-set-conditioned vector field with a structural vehicle anchor.

    Mean and standard deviation provide permutation-invariant population context.
    This is a modest set encoder, not a reproduction of State/STACK attention.
    """
    def __init__(self, dimensions: int, condition_size: int):
        super().__init__()
        self.dimensions, self.condition_size = dimensions, condition_size
        self.velocity = nn.Sequential(nn.Linear(3 * dimensions + condition_size + 1, 64),
                                      nn.SiLU(), nn.Linear(64, 64), nn.SiLU(),
                                      nn.Linear(64, dimensions))

    def forward(self, cells, time, condition, context, dose_gate):
        features = torch.cat((cells, time, condition.expand(len(cells), -1),
                              context.expand(len(cells), -1)), dim=1)
        return self.velocity(features) * dose_gate

    def predict_population(self, control, condition, dose_gate: float, *, steps: int = 16):
        control = _population(control)
        condition = np.asarray(condition, dtype=np.float32)
        if (control.shape[1] != self.dimensions or condition.shape != (self.condition_size,)
                or not np.isfinite(condition).all() or not np.isfinite(dose_gate)
                or dose_gate < 0 or not isinstance(steps, int) or steps < 1):
            raise ValueError("invalid_population_query")
        if dose_gate == 0:
            return control.copy()
        device = next(self.parameters()).device
        x = torch.as_tensor(control, device=device)
        context = torch.cat((x.mean(0), x.std(0, unbiased=False)))
        c = torch.as_tensor(condition, device=device)
        self.eval()
        with torch.no_grad():
            for i in range(steps):
                # Midpoint integration in numerical flow time, not hours.
                t = torch.full((len(x), 1), i / steps, device=device)
                v = self(x, t, c, context, dose_gate)
                x = x + self(x + v / (2 * steps), t + 0.5 / steps, c, context, dose_gate) / steps
        result = x.cpu().numpy()
        if not np.isfinite(result).all():
            raise ValueError("nonfinite_population_prediction")
        return result


def fit_population_flow(training, validation, *, bandwidth: float, seed: int = 0,
                        epochs: int = 80, batch_cells: int = 32):
    """Equal-condition minibatch OT flow matching, selected by validation MMD.

    No test population is accepted. Validate chemical/study split identities;
    preprocessing, metadata provenance and pretraining overlap remain caller duties.
    """
    if not training or not validation or epochs < 1 or batch_cells < 2:
        raise ValueError("invalid_population_training_config")
    for pair in (*training, *validation):
        pair.validate()
    if {p.group for p in training} & {p.group for p in validation}:
        raise ValueError("population_split_group_overlap")
    d, c = training[0].control.shape[1], len(training[0].condition)
    if any(p.control.shape[1] != d or len(p.condition) != c for p in (*training, *validation)):
        raise ValueError("population_training_coordinates_mismatch")
    if not np.isfinite(bandwidth) or bandwidth <= 0:
        raise ValueError("invalid_population_bandwidth")
    rng = np.random.default_rng(seed)
    # Keep this experiment's seed from modifying the agent's torch RNG state.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        model = ConditionalPopulationFlow(d, c)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    training_contexts = []
    for pair in training:
        control = torch.as_tensor(pair.control, dtype=torch.float32)
        training_contexts.append((torch.cat((control.mean(0), control.std(0, unbiased=False))),
                                  torch.as_tensor(pair.condition, dtype=torch.float32)))
    best, state, history = float("inf"), None, []
    for epoch in range(1, epochs + 1):
        model.train()
        losses = []
        for index in rng.permutation(len(training)):
            p = training[index]
            x = p.control[rng.choice(len(p.control), batch_cells, replace=len(p.control) < batch_cells)]
            y = p.treated[rng.choice(len(p.treated), batch_cells, replace=len(p.treated) < batch_cells)]
            # Equal-mass minibatch OT; not inferred cell identity.
            rows, cols = linear_sum_assignment(cdist(x, y, "sqeuclidean"))
            x, y = torch.as_tensor(x[rows], dtype=torch.float32), torch.as_tensor(y[cols], dtype=torch.float32)
            t = torch.as_tensor(rng.uniform(size=(batch_cells, 1)), dtype=torch.float32)
            context, c_tensor = training_contexts[index]
            prediction = model((1 - t) * x + t * y, t, c_tensor, context, p.dose_gate)
            loss = (prediction - (y - x)).square().mean()
            if not torch.isfinite(loss):
                raise ValueError("nonfinite_population_training_loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        score = float(np.mean([population_mmd(model.predict_population(p.control, p.condition, p.dose_gate),
                                             p.treated, bandwidth) for p in validation]))
        history.append({"epoch": epoch, "flow_loss": float(np.mean(losses)), "validation_mmd": score})
        if score < best:
            best, state = score, copy.deepcopy(model.state_dict())
    model.load_state_dict(state)
    model.eval()
    return model, history
