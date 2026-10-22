"""Parent-owned prediction backends; observations enter only through observe().

The reused PPODE is the original study's model, not a full ProteinTalks replica.
Determinism is tested on one CPU/software configuration; seeds do not promise
identical results across hardware, torch versions, or CUDA implementations.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random

import numpy as np
import torch
import torch.nn.functional as F


_SOURCE = Path(__file__).resolve().parent.parent / "dual_core_innovation_validation_20261021" / "ptv_models.py"
_SPEC = importlib.util.spec_from_file_location("_repair_original_ptv_models", _SOURCE)
M = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(M)
INPUT_KEYS = ("x", "pert", "fpA", "fpB")


def build_model(n_prot, n_fp, seed=0, hidden=16, variant="full", device="cpu"):
    """Seed before construction, including initialization; fail on nondeterminism."""
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True)
    return M.PPODE(n_prot, n_fp, hidden=hidden, variant=variant).to(device)


def parameter_id(model):
    """Hash actual state tensors, including buffers, rather than a version counter."""
    h = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        arr = value.detach().cpu().contiguous().numpy()
        h.update(name.encode())
        h.update(str((arr.dtype, arr.shape)).encode())
        h.update(arr.tobytes())
    return h.hexdigest()


def _input_tensors(inputs):
    if isinstance(inputs, (list, tuple)):
        if not inputs or any(set(item) != set(INPUT_KEYS) for item in inputs):
            raise ValueError("Input items must contain only x, pert, fpA, fpB; targets are forbidden")
        inputs = {k: np.stack([item[k] for item in inputs]) for k in INPUT_KEYS}
    if not isinstance(inputs, dict) or set(inputs) != set(INPUT_KEYS):
        raise ValueError("Input tensors must contain only x, pert, fpA, fpB; targets are forbidden")
    out = {}
    for k in INPUT_KEYS:
        value = torch.as_tensor(inputs[k], dtype=torch.float32).detach().clone()
        if value.ndim == 2:
            value = value.unsqueeze(-1)
        if value.ndim != 3 or value.shape[-1] != 1 or not torch.isfinite(value).all():
            raise ValueError(f"Invalid input tensor {k}")
        out[k] = value
    if out["x"].shape != out["pert"].shape or out["fpA"].shape != out["fpB"].shape:
        raise ValueError("Input dimensions do not match")
    if len({v.shape[0] for v in out.values()}) != 1:
        raise ValueError("Candidate counts do not match")
    return out


def _validate_observation(kind, drug, value, drugs, seen):
    if drug not in drugs or kind not in ("f", "m"):
        raise ValueError("Unknown observation kind or drug")
    if (kind, drug) in seen:
        raise ValueError("Duplicate observation")
    if kind == "f":
        if not isinstance(value, (bool, int, float, np.integer, np.floating)) or value not in (0, 1):
            raise ValueError("Functional observations must be binary")
        return float(value)
    if not isinstance(value, dict) or set(value) != {"y", "mask"}:
        raise ValueError("Molecular observations require exactly y and mask")
    y = torch.as_tensor(value["y"], dtype=torch.float32).detach().clone()
    mask = torch.as_tensor(value["mask"]).detach().clone()
    if y.ndim != 2 or y.shape[0] != 3 or y.shape != mask.shape:
        raise ValueError("Molecular y and mask must have shape [3, n_proteins]")
    if not torch.all((mask == 0) | (mask == 1)) or not mask.any():
        raise ValueError("Molecular mask must be binary and contain observed values")
    mask = mask.bool()
    if not torch.isfinite(y[mask]).all():
        raise ValueError("Observed molecular values must be finite")
    # Unobserved values never reach a loss, including NaNs and poisoned targets.
    return {"y": torch.where(mask, y, 0.0), "mask": mask}


def _diagnostics(backend, kind, drug, before_id, before):
    after = backend.predict()
    return {
        "kind": kind, "drug": drug,
        "before_model_id": before_id, "after_model_id": backend.model_id,
        "support_keys": [[k, d] for k, d in backend.observations],
        "max_prediction_delta": max(abs(after[d] - before[d]) for d in before),
        "max_unqueried_prediction_delta": max(
            (abs(after[d] - before[d]) for d in before
             if not any(support_drug == d for _, support_drug in backend.observations)),
            default=0.0),
    }


class FeedbackBackend:
    """Update a private PPODE copy from accumulated, paid support observations.

    Molecular payloads use [6h,24h,48h] x proteins. A 24h-only assay must set
    the mask to false at the other two times. No released-data object or loader
    is retained. The evaluator owns observation retrieval and payment.
    """
    def __init__(self, model, inputs, drug_rows, steps=2, lr=5e-4):
        if steps < 1 or lr <= 0:
            raise ValueError("Feedback steps and learning rate must be positive")
        self.model = copy.deepcopy(model)
        self.inputs = _input_tensors(inputs)
        self.drug_rows = dict(drug_rows)
        n = self.inputs["x"].shape[0]
        if not self.drug_rows or set(self.drug_rows.values()) != set(range(n)) or len(self.drug_rows) != n:
            raise ValueError("drug_rows must map each candidate to one unique input row")
        if self.inputs["x"].shape[1] != model.n_prot:
            raise ValueError("Protein dimension does not match the model")
        self.device = next(self.model.parameters()).device
        self.inputs = {k: v.to(self.device) for k, v in self.inputs.items()}
        self.steps = int(steps)
        self.observations = {}
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-4)
        self.model.eval()

    @property
    def model_id(self):
        return parameter_id(self.model)

    @torch.no_grad()
    def predict(self):
        self.model.eval()
        _, p = self.model(*[self.inputs[k] for k in INPUT_KEYS])
        return {drug: float(p[row].cpu()) for drug, row in self.drug_rows.items()}

    def observe(self, kind, drug, value):
        value = _validate_observation(kind, drug, value, self.drug_rows, self.observations)
        if kind == "m":
            if self.model.variant == "no_traj":
                raise ValueError("Molecular feedback requires a trajectory model")
            if value["y"].shape[1] != self.model.n_prot:
                raise ValueError("Molecular protein dimension does not match the model")
            value = {k: v.to(self.device) for k, v in value.items()}
        before_id, before = self.model_id, self.predict()
        self.observations[kind, drug] = value
        # Eval mode makes feedback deterministic even if a supplied model has dropout.
        self.model.eval()
        support_drugs = list(dict.fromkeys(d for _, d in self.observations))
        rows = [self.drug_rows[d] for d in support_drugs]
        positions = {d: i for i, d in enumerate(support_drugs)}
        for _ in range(self.steps):
            y, p = self.model(*[self.inputs[k][rows] for k in INPUT_KEYS])
            functional, molecular = [], []
            for (obs_kind, obs_drug), observation in self.observations.items():
                pos = positions[obs_drug]
                if obs_kind == "f":
                    target = torch.tensor(observation, device=self.device)
                    functional.append(F.binary_cross_entropy(p[pos].clamp(1e-5, 1 - 1e-5), target))
                else:
                    mask = observation["mask"]
                    molecular.append(((y[pos][mask] - observation["y"][mask]) ** 2).mean())
            loss = 0.8 * torch.stack(functional).mean() if functional else 0.0
            if molecular:
                loss = loss + 0.2 * torch.stack(molecular).mean()
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
        if not all(np.isfinite(p) for p in self.predict().values()):
            raise RuntimeError("Nonfinite feedback prediction")
        return _diagnostics(self, kind, drug, before_id, before)


class StaticBackend:
    """Frozen probabilities. Paid observations are logged but do not update it."""
    def __init__(self, priors):
        self.priors = {d: float(p) for d, p in priors.items()}
        if not self.priors or any(not np.isfinite(p) or not 0 <= p <= 1 for p in self.priors.values()):
            raise ValueError("Priors must be finite probabilities")
        self.observations = {}

    @property
    def model_id(self):
        return hashlib.sha256(json.dumps(self.priors, sort_keys=True).encode()).hexdigest()

    def predict(self):
        return dict(self.priors)

    def observe(self, kind, drug, value):
        value = _validate_observation(kind, drug, value, self.priors, self.observations)
        before_id, before = self.model_id, self.predict()
        self.observations[kind, drug] = value
        return _diagnostics(self, kind, drug, before_id, before)


class KernelBackend(StaticBackend):
    """Conventional feature-similarity residual update from functional labels.

    Positive cosine similarities share binary-label residuals. Unit shrinkage
    avoids extrapolating one observation at full strength to every drug.
    Molecular observations are logged but unused: this comparator has no
    molecular-to-functional observation model.
    """
    def __init__(self, priors, features):
        super().__init__(priors)
        if set(features) != set(self.priors):
            raise ValueError("Features must cover exactly the candidate drugs")
        self.drugs = list(self.priors)
        x = np.asarray([features[d] for d in self.drugs], dtype=float)
        if x.ndim != 2 or not np.isfinite(x).all():
            raise ValueError("Features must be finite vectors")
        x = x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)
        self.sim = np.clip(x @ x.T, 0, 1)
        np.fill_diagonal(self.sim, 1.0)

    @property
    def model_id(self):
        h = hashlib.sha256(super().model_id.encode())
        h.update(self.sim.tobytes())
        h.update(json.dumps(sorted((d, v) for (k, d), v in self.observations.items() if k == "f")).encode())
        return h.hexdigest()

    def predict(self):
        p = np.asarray([self.priors[d] for d in self.drugs])
        support = [(self.drugs.index(d), value - self.priors[d])
                   for (kind, d), value in self.observations.items() if kind == "f"]
        if support:
            idx, residual = zip(*support)
            weight = self.sim[:, list(idx)]
            p += weight @ np.asarray(residual) / (1.0 + weight.sum(axis=1))
        return {d: float(v) for d, v in zip(self.drugs, np.clip(p, 1e-5, 1 - 1e-5))}
