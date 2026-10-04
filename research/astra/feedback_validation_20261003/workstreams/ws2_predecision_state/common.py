"""Shared helpers for WS2 (predecision state, coupling, input legality).

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws2_predecision_state/common.py
- Purpose: wrap the FROZEN certified-discovery world model and campaign loop (imported, never
  edited) so WS2 can ablate feature groups, swap the line-similarity source, decompose the
  context-shuffle control and replay campaigns with the registered spec.
- Core points:
  - Feature columns of `TransferWorld` with context (frozen order):
    0 pair_mean, 1 drug_max, 2 drug_min            (H: other lines' labels only)
    3 sim_pair_mean, 4 sim_drug_max, 5 sim_drug_min (S: other lines' labels, weighted by a
                                                     line similarity built from the TARGET
                                                     line's single-agent profile)
    6 mono_mean_max, 7 mono_mean_min, 8 mono_top_max, 9 mono_top_min (M: target-line singles)
    10 expected                                    (E: target-line Bliss expectation; the same
                                                     quantity the O'Neil label subtracts)
  - `MaskedWorld` keeps a subset of columns; `SimilarityWorld` replaces the line similarity;
    `PartialShuffleWorld` applies one component of the frozen shuffle control at a time.
  - `run_arm` runs `agent.run_campaign` exactly as `replay.run_line` does (seed = line index for
    deterministic arms) with the registered development spec (kappa 2, alpha 0.2, delta 0.1).
- Interfaces: ONEIL, ALMANAC, OUT, load, MaskedWorld, SimilarityWorld, PartialShuffleWorld,
  StaticView, run_arm, prior_metrics, bootstrap_ci, sha256_file.
- Depends on: numpy, scipy, research.certified_discovery (frozen; read-only import).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

for _variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_variable, "1")

import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.certified_discovery import agent  # noqa: E402
from research.certified_discovery.screens import CACHE, Library, load_library  # noqa: E402
from research.certified_discovery.world import TransferWorld, WorldConfig, _rbf_similarity, _zscore_columns  # noqa: E402,F401

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
ONEIL = CACHE / "oneil_v1.npz"
ALMANAC = CACHE / "almanac_v1.npz"
SPEC = agent.CampaignSpec(kappa=2, audit_seeds=2)   # exploit hits do not depend on audit_seeds

GROUPS = {
    "H": [0, 1, 2],
    "S": [3, 4, 5],
    "M": [6, 7, 8, 9],
    "E": [10],
}
COLUMN_NAMES = ["pair_mean", "drug_max", "drug_min", "sim_pair_mean", "sim_drug_max", "sim_drug_min",
                "mono_mean_max", "mono_mean_min", "mono_top_max", "mono_top_min", "expected"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path = ONEIL) -> Library:
    return load_library(path)


def columns_for(groups: str) -> list[int]:
    cols: list[int] = []
    for g in groups:
        cols += GROUPS[g]
    return sorted(cols)


class MaskedWorld(TransferWorld):
    """TransferWorld whose ridge prior sees only the listed feature columns.

    `identity_kernel=True` also replaces the drug-similarity kernel by the identity (as the
    frozen context=False world does), so feature effects and kernel effects can be separated.
    """

    def __init__(self, library, target_line, config=WorldConfig(), *, columns=None, identity_kernel=False,
                 line_sim=None):
        self._columns = columns
        self._identity_kernel = identity_kernel
        self._line_sim_override = line_sim
        super().__init__(library, target_line, config)

    def _build_context(self) -> None:
        super()._build_context()
        if self._line_sim_override is not None:
            sim = np.array(self._line_sim_override, float, copy=True)
            np.fill_diagonal(sim, 0.0)
            self.line_sim = sim
        if self._identity_kernel:
            self.drug_kernel = np.eye(self.drug_kernel.shape[0])

    def _fit_prior(self) -> None:
        if self._columns is not None:
            self.X_history = self.X_history[:, self._columns]
            self.X_target = self.X_target[:, self._columns]
        super()._fit_prior()


SimilarityWorld = MaskedWorld   # alias: a MaskedWorld built with `line_sim=`


class PartialShuffleWorld(TransferWorld):
    """One component of the frozen shuffle control at a time (same RNG stream as world.py).

    components: subset of {"line_sim", "drug_kernel", "mono", "expected_formula"}.
    "expected_formula" recomputes `expected` from (possibly shuffled) mono_mean with the
    product-of-means formula the frozen shuffle uses, instead of the per-dose library value.
    """

    def __init__(self, library, target_line, seed, components, config=WorldConfig()):
        self._seed, self._components = seed, set(components)
        super().__init__(library, target_line, config)

    def _build_context(self) -> None:
        lib, cfg = self.lib, self.config
        n_drugs, n_lines = lib.mono_mean.shape
        line_sim = _rbf_similarity(_zscore_columns(lib.mono_mean.T))
        drug_sim = _rbf_similarity(_zscore_columns(lib.mono_mean))
        mono_mean = np.nan_to_num(lib.mono_mean, nan=float(np.nanmean(lib.mono_mean)))
        mono_top = np.nan_to_num(lib.mono_top, nan=float(np.nanmean(lib.mono_top)))
        rng = np.random.default_rng(self._seed)
        line_perm = rng.permutation(n_lines)
        drug_perm = rng.permutation(n_drugs)
        orders = [rng.permutation(n_drugs) for _ in range(n_lines)]
        if "line_sim" in self._components:
            line_sim = line_sim[np.ix_(line_perm, line_perm)]
        if "drug_kernel" in self._components:
            drug_sim = drug_sim[np.ix_(drug_perm, drug_perm)]
        if "mono" in self._components:
            for column in range(n_lines):
                mono_mean[:, column] = mono_mean[orders[column], column]
                mono_top[:, column] = mono_top[orders[column], column]
        expected = lib.expected.copy()
        if "expected_formula" in self._components:
            expected = 1.0 - (1.0 - np.clip(mono_mean[lib.a, lib.c], 0, 1)) * (
                1.0 - np.clip(mono_mean[lib.b, lib.c], 0, 1))
        self.line_sim, self.mono_mean, self.mono_top, self.expected = line_sim, mono_mean, mono_top, expected
        self.drug_kernel = np.eye(n_drugs)
        if cfg.context and cfg.drug_similarity:
            self.drug_kernel = 0.5 * np.eye(n_drugs) + 0.5 * drug_sim


class StaticView:
    """Feedback switched off on an already fitted world (replay.TransferWorldView equivalent)."""

    def __init__(self, world):
        self._world = world
        self.lib, self.rows = world.lib, world.rows

    def posterior(self, measured, values):
        return self._world.prior_target.copy(), self._world.prior_var_target.copy()

    def p_hit(self, mean, var):
        return self._world.p_hit(mean, var)


def run_arm(lib: Library, world, kind: str, line: int, spec: agent.CampaignSpec = SPEC) -> dict:
    """Run one campaign. kind: wm_full | wm_static | wm_greedy | history | heuristic_potency | ..."""
    if kind == "wm_full":
        arm = agent.WorldArm(world, kind)
    elif kind == "wm_static":
        arm = agent.WorldArm(StaticView(world), kind)
    elif kind == "wm_greedy":
        arm = agent.WorldArm(world, kind, acquisition="mean")
    elif kind == "history":
        arm = agent.HistoryArm(world)
    elif kind.startswith("heuristic_"):
        arm = agent.HeuristicArm(world, kind.split("_", 1)[1])
    else:
        raise ValueError(kind)
    return agent.run_campaign(lib, world, arm, spec, seed=line)


def selected_rows(lib: Library, world, kind: str, line: int, spec: agent.CampaignSpec = SPEC):
    """Campaign-candidate indices bought by the exploit variant (rounds 1-4), in order."""
    rng = np.random.default_rng(line)
    rows = world.rows
    truth = lib.y[rows]
    n = rows.size
    import math
    budget = int(math.ceil(spec.budget_fraction * n))
    batch = int(math.ceil(budget / spec.rounds))
    if kind == "wm_full":
        arm = agent.WorldArm(world, kind)
    elif kind == "wm_static":
        arm = agent.WorldArm(StaticView(world), kind)
    elif kind == "history":
        arm = agent.HistoryArm(world)
    else:
        raise ValueError(kind)
    measured = np.zeros(n, bool)
    order = []
    for _ in range(spec.rounds - 1):
        idx = np.flatnonzero(measured)
        k = int(min(batch, budget - measured.sum()))
        chosen = agent._top(arm.scores(idx, truth[idx]), ~measured, k, rng)
        measured[chosen] = True
        order.extend(chosen.tolist())
    idx = np.flatnonzero(measured)
    last = int(budget - measured.sum())
    final = agent._top(arm.scores(idx, truth[idx]).copy(), ~measured, last, rng)
    order.extend(final.tolist())
    return np.array(order, int)


def prior_metrics(world, y: np.ndarray, threshold: float = 10.0) -> dict:
    """Ranking power of the static prior on the target line (no feedback)."""
    prior = world.prior_target
    n = prior.size
    budget = int(np.ceil(0.10 * n))
    hits = y > threshold
    top = np.argsort(-prior, kind="stable")[:budget]
    auc = None
    if 0 < hits.sum() < n:
        ranks = stats.rankdata(prior)
        auc = float((ranks[hits].sum() - hits.sum() * (hits.sum() + 1) / 2) / (hits.sum() * (~hits).sum()))
    return {"spearman": float(stats.spearmanr(prior, y).correlation), "auc": auc,
            "hits_top_budget": int(hits[top].sum()), "line_hits": int(hits.sum()), "budget": budget}


def bootstrap_ci(values, statistic=np.mean, n_boot: int = 4000, seed: int = 20261003) -> list[float]:
    values = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, values.size, size=(n_boot, values.size))
    boot = np.array([statistic(values[d]) for d in draws])
    return [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]


def write_json(name: str, payload: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps(payload, indent=1, sort_keys=True, default=float), encoding="utf-8")
    return path


__all__ = ["ROOT", "OUT", "ONEIL", "ALMANAC", "SPEC", "GROUPS", "COLUMN_NAMES", "load", "columns_for",
           "MaskedWorld", "SimilarityWorld", "PartialShuffleWorld", "StaticView", "run_arm", "selected_rows",
           "prior_metrics", "bootstrap_ci", "sha256_file", "write_json", "WorldConfig", "TransferWorld",
           "replace", "agent"]
