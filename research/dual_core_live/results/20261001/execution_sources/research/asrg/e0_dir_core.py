from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import hashlib, json, math
from typing import Mapping, Sequence
import numpy as np

def _vec(x: Sequence[float], name: str, dim: int | None = None) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    if a.ndim != 1 or (dim is not None and len(a) != dim) or not np.isfinite(a).all():
        raise ValueError(f"invalid_{name}")
    return a

class DIRRepairBranch(str, Enum):
    REALIZATION = "repair_realization"
    HYPOTHESIS = "repair_hypothesis"
    KEEP = "keep"

@dataclass(frozen=True)
class ActionSpec:
    action_id: str
    label: str
    intervention_mode: str
    dose: float
    dose_unit: str
    context_id: str
    model_id: str
    latent_space_id: str
    response_basis_id: str
    control_pool_id: str
    candidate_role: str = "actual"
    def __post_init__(self):
        if not self.action_id or not self.label or self.dose < 0 or not math.isfinite(self.dose): raise ValueError("invalid_action")

@dataclass(frozen=True)
class LatentHypothesis:
    hypothesis_id: str
    latent: tuple[float, ...]
    latent_space_id: str
    source_action_id: str
    support_status: str
    def __post_init__(self): _vec(self.latent, "latent")

@dataclass(frozen=True)
class PredictionPair:
    goal: tuple[float, ...]
    ideal_hat: tuple[float, ...]
    actual_hat: tuple[float, ...]
    model_id: str
    response_basis_id: str
    control_pool_id: str
    projection_sha256: str
    def __post_init__(self):
        n = len(self.goal); _vec(self.goal,"goal",n); _vec(self.ideal_hat,"ideal_hat",n); _vec(self.actual_hat,"actual_hat",n)
        rg = np.asarray(self.goal)-np.asarray(self.ideal_hat); rr=np.asarray(self.ideal_hat)-np.asarray(self.actual_hat); rt=np.asarray(self.goal)-np.asarray(self.actual_hat)
        if not np.allclose(rg+rr,rt,rtol=1e-9,atol=1e-10): raise ValueError("residual_identity_failed")
    @property
    def r_goal(self): return np.asarray(self.goal)-np.asarray(self.ideal_hat)
    @property
    def r_realization(self): return np.asarray(self.ideal_hat)-np.asarray(self.actual_hat)
    @property
    def r_total(self): return np.asarray(self.goal)-np.asarray(self.actual_hat)

@dataclass(frozen=True)
class DIREpisode:
    episode_id: str
    pair: PredictionPair
    initial_action: ActionSpec
    initial_hypothesis: LatentHypothesis
    realization_menu: tuple[ActionSpec, ...]
    hypothesis_menu: tuple[tuple[LatentHypothesis, ActionSpec], ...]
    max_new_queries: int = 4
    def __post_init__(self):
        if self.max_new_queries < 0 or len(self.realization_menu) > self.max_new_queries or len(self.hypothesis_menu) > self.max_new_queries: raise ValueError("invalid_query_budget")

@dataclass(frozen=True)
class DIRDecision:
    branch: DIRRepairBranch
    reason: str = ""
    def __post_init__(self):
        if not isinstance(self.branch, DIRRepairBranch): raise ValueError("invalid_branch")

@dataclass(frozen=True)
class DIRStepRecord:
    episode_id: str
    decision: DIRDecision
    queried_action_ids: tuple[str, ...]
    selected_action_id: str
    prediction_cost: float
    api_attempts: int = 0
    fallback: bool = False

@dataclass(frozen=True)
class E0Observation:
    episode_id: str
    action_id: str
    observed_response: tuple[float, ...]
    response_basis_id: str
    source_id: str
    independent_unit_id: str
    def __post_init__(self): _vec(self.observed_response,"observed_response")

def canonical_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def normalized_loss(observed: Sequence[float], goal: Sequence[float], epsilon: float = 1e-8) -> float:
    y, g = _vec(observed,"observed"), _vec(goal,"goal")
    if len(y) != len(g) or not math.isfinite(epsilon) or epsilon <= 0: raise ValueError("invalid_loss_inputs")
    return float(np.sum((y-g)**2)/(np.sum(g**2)+epsilon))

