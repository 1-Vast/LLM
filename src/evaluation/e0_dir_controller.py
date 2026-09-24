from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Mapping, Protocol, Sequence
import numpy as np
from .e0_dir_core import *

class DIRRouter(Protocol):
    def choose(self, view: Mapping[str, object]) -> DIRDecision: ...

class PredictionProvider(Protocol):
    def predict(self, action: ActionSpec, hypothesis: LatentHypothesis) -> Sequence[float]: ...

def visible_view(episode: DIREpisode, arm: str) -> dict[str, object]:
    p=episode.pair
    base={"episode_id":episode.episode_id,"goal":list(p.goal),"actual_hat":list(p.actual_hat),"menus":{"realization":[a.action_id for a in episode.realization_menu],"hypothesis":[a.action_id for _,a in episode.hypothesis_menu]},"max_new_queries":episode.max_new_queries}
    if arm == "dir": base.update(r_goal=list(p.r_goal),r_realization=list(p.r_realization))
    elif arm == "raw": base.update(ideal_hat=list(p.ideal_hat))
    elif arm == "corrupted":
        eta=np.linspace(0.01,0.01*len(p.goal),len(p.goal)); base.update(r_goal=list(p.r_goal+eta),r_realization=list(p.r_realization-eta))
    else: raise ValueError("unknown_arm")
    return base

def choose_candidates(episode: DIREpisode, decision: DIRDecision, provider: PredictionProvider) -> tuple[tuple[str,...], str, float]:
    if decision.branch is DIRRepairBranch.KEEP: return (), episode.initial_action.action_id, 0.0
    if decision.branch is DIRRepairBranch.REALIZATION:
        pairs=[(a.action_id, provider.predict(a,episode.initial_hypothesis)) for a in episode.realization_menu]
    else:
        pairs=[(a.action_id, provider.predict(a,h)) for h,a in episode.hypothesis_menu]
    if not pairs: return (), episode.initial_action.action_id, 0.0
    target=np.asarray(episode.pair.goal); chosen=min(pairs,key=lambda x: float(np.sum((np.asarray(x[1])-target)**2)))
    return tuple(x[0] for x in pairs), chosen[0], float(len(pairs))

def execute_step(episode: DIREpisode, decision: DIRDecision, provider: PredictionProvider, *, api_attempts: int=0, fallback: bool=False) -> DIRStepRecord:
    queried, selected, cost=choose_candidates(episode,decision,provider)
    return DIRStepRecord(episode.episode_id,decision,queried,selected,cost,api_attempts,fallback)

def score_observation(obs: E0Observation, episode: DIREpisode, *, epsilon: float=1e-8) -> float:
    if obs.episode_id != episode.episode_id or obs.response_basis_id != episode.pair.response_basis_id: raise ValueError("observation_binding_mismatch")
    return normalized_loss(obs.observed_response, episode.pair.goal, epsilon)

