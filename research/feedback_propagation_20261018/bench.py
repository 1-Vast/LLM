"""Chemically separated, outcome-masked bench for the feedback-propagation study.

File summary
- Path: research/feedback_propagation_20261018/bench.py
- Purpose: build, for one held-out MoA-family fold of exposed PRISM 19Q4, everything an arm may read
  (`Fold`) and, separately, everything only the oracle and the grader may read (`Hidden`).
- Core points:
  - Inherited unchanged from `research/indication_triage_20261016`: the cached tables, MoA-family folds,
    endpoint (selective residual on the training generic profile, robust z <= -3 and log2 FC <= -1),
    campaign membership (64 compounds by salted hash), the heteroscedastic probe-noise model and the
    World (structure prior + low-rank covariance).
  - New here: (1) a chemical purge. Training compounds whose ECFP4 Tanimoto to any compound of the
    evaluation fold reaches `SEPARATION` are removed from that fold's training set, so no evaluation
    compound has a training analogue at or above the boundary. (2) Admissible lines are the lines measured
    for at least `MIN_TRAIN_FINITE` of the training compounds (training information only).
    (3) Outcomes are reachable only through `Oracle.observe`; unqueried cells are never read by an arm.
  - A probe is the scoring matrix value plus synthetic noise. It is NOT an independent measurement of the
    cell it grades; the primary utilities therefore count unmeasured pairs only.
- Interfaces: `load_tables`, `make_fold`, `Fold`, `Hidden`, `Oracle`, `probe_sd`, `pool_vector`, `pool_order`, `pool_lines`, constants.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TRIAGE = ROOT / "research/indication_triage_20261016"
if str(TRIAGE) not in sys.path:
    sys.path.insert(0, str(TRIAGE))
import common as tc  # noqa: E402  (indication_triage_20261016/common.py)
from world import World, call_score  # noqa: E402,F401

SEPARATION = 0.5        # ECFP4 Tanimoto at or above which a training compound is purged
MIN_TRAIN_FINITE = 0.90  # a line is admissible if this share of training compounds measured it
FOLLOW_UP, CAP = tc.FOLLOW_UP, tc.CAP
CACHE = tc.CACHE


def load_tables() -> dict:
    T = dict(np.load(CACHE / "tables.npz"))
    build = json.loads((TRIAGE / "BUILD.json").read_text(encoding="utf-8"))
    if tc.sha256(CACHE / "tables.npz") != build["tables_sha256"]:
        raise SystemExit("TABLES_DIGEST_MISMATCH: rerun indication_triage_20261016/build.py")
    noise = build["probe_noise"]
    T["sigma_probe"] = noise["sigma_probe"]
    T["noise_bins"] = noise["sigma_replicate_by_centre"]
    T["noise_factor"] = noise["median3_variance_factor"]
    T["pool"] = pool_vector(T["lines"])
    return T


def probe_sd(Y: np.ndarray, T: dict, mult: float = 1.0) -> np.ndarray:
    """Probe noise SD per cell: replicate spread of the published value's effect bin (as in indication triage)."""

    b = T["noise_bins"]
    rep = np.select([Y <= -2.0, Y <= -1.0, Y <= 0.0],
                    [b["le_-2"]["sigma_replicate"], b["-2_-1"]["sigma_replicate"], b["-1_0"]["sigma_replicate"]],
                    b["gt_0"]["sigma_replicate"])
    return mult * np.sqrt(2.0 * T["noise_factor"]) * rep


@dataclass
class Hidden:
    """Outcome side of a fold. Only `Oracle` and the grader read it."""

    Y: np.ndarray            # published profiles, NaN = not measured
    truth: np.ndarray        # registered selective events
    sd: np.ndarray           # probe noise SD per cell
    z: np.ndarray            # frozen standard normal per cell (common random numbers)
    family: np.ndarray = None  # (n,) MoA family label; analysis clustering only, never given to an arm


@dataclass
class Fold:
    """Everything a policy may read about one evaluation fold."""

    fold: int
    train_folds: tuple
    cores: np.ndarray
    lineage: np.ndarray
    lines: np.ndarray
    pid: np.ndarray          # (L,) pool of every line
    world: World
    G: np.ndarray
    prior: np.ndarray        # (n, L) structure-prior mean profiles
    design: np.ndarray       # sparse-design line order (64)
    avail: np.ndarray        # (L,) admissible lines
    campaigns: list
    n_train: int
    n_purged: int
    max_sim_before: np.ndarray   # (n,) max Tanimoto to the unpurged candidate training set
    max_sim_after: np.ndarray    # (n,) max Tanimoto to the purged training set
    noise_bins: dict = field(default=None, repr=False)        # probe-noise model (for training-time augmentation only)
    noise_factor: float = 0.0
    train_idx: np.ndarray = field(default=None, repr=False)   # indices into the tables of the purged training set
    hidden: Hidden = field(repr=False, default=None)
    cache: dict = field(default_factory=dict, repr=False)

    def oracle(self) -> "Oracle":
        return Oracle(self.hidden)


class Oracle:
    """Query interface to the evaluation outcomes: returns noisy values for queried cells and logs them."""

    def __init__(self, hidden: Hidden):
        self._h = hidden
        n, L = hidden.Y.shape
        self.queried = np.zeros((n, L), dtype=bool)
        self.failed = np.zeros((n, L), dtype=bool)
        self.units = 0

    def observe(self, i: int, lines) -> np.ndarray:
        lines = np.asarray(lines, dtype=int)
        h = self._h
        y = h.Y[i, lines] + h.sd[i, lines] * h.z[i, lines]
        self.queried[i, lines] = True
        self.failed[i, lines] |= ~np.isfinite(y)
        self.units += len(lines)
        return y


def make_fold(T: dict, eval_fold: int, train_folds=None, *, separation: float = SEPARATION, noise_mult: float = 1.0,
              noise_salt: str = "probe") -> Fold:
    """Fold context. `train_folds` defaults to every other fold; the purge then removes close analogues."""

    folds = T["fold"]
    if train_folds is None:
        train_folds = tuple(sorted(set(int(f) for f in folds) - {eval_fold}))
    test = np.where(folds == eval_fold)[0]
    cand = np.where(np.isin(folds, train_folds))[0]
    sim = tc.tanimoto(T["fp"][test], T["fp"][cand])
    before = sim.max(1)
    keep = sim.max(0) < separation
    train = cand[keep]
    after = tc.tanimoto(T["fp"][test], T["fp"][train]).max(1)
    Y = T["Y"].astype(np.float64)
    G = np.nanmedian(Y[train], axis=0)
    world = World(Y[train], T["fp"][train], G, max(T["sigma_probe"] * noise_mult, 1e-3))
    cores = T["cores"][test]
    z = np.stack([np.random.default_rng(tc.h(str(c), noise_salt) % (2 ** 32)).standard_normal(Y.shape[1]) for c in cores])
    hidden = Hidden(Y=Y[test], truth=tc.events(Y[test], G), sd=probe_sd(Y[test], T, noise_mult), z=z, family=T["family"][test])
    avail = np.isfinite(Y[train]).mean(0) >= MIN_TRAIN_FINITE
    return Fold(fold=eval_fold, train_folds=tuple(train_folds), cores=cores, lineage=T["lineage"], lines=T["lines"], pid=T["pool"],
                world=world, G=G, prior=world.prior(T["fp"][test]), design=world.sparse_design(64), avail=avail,
                campaigns=tc.campaigns(cores), n_train=int(len(train)), n_purged=int((~keep).sum()),
                max_sim_before=before, max_sim_after=after, train_idx=train, hidden=hidden,
                noise_bins=T["noise_bins"], noise_factor=T["noise_factor"])


def pool_vector(lines) -> np.ndarray:
    """(L,) pool id of every panel line in the PRISM primary screen HTS (23 pools of about 24 lines).

    Source: secondary-screen-pooling-info.csv, which carries the pool of every line in the primary screens HTS and
    MTS004 (the same 23 pools up to a few lines). Compounds screened only in MTS004 (12% of the cores) use the HTS
    grouping here; the two groupings agree for about 97% of the lines. The compound plate and well are NOT available
    for the replicate-collapsed primary data, so a pool is a measurement-granularity fact, not a priced unit.
    """

    import pandas as pd

    pool = pd.read_csv(tc.PRISM / "secondary-screen-pooling-info.csv")
    hts = pool[pool["screen_id"] == "HTS"].set_index("row_name")["pool_id"].reindex(list(lines))
    codes = {p: k for k, p in enumerate(sorted(hts.dropna().unique()))}
    return np.array([codes[p] for p in hts], dtype=np.int16)


def pool_order(fold: "Fold") -> list:
    """Pools in greedy A-optimal order under the base covariance (all compounds share it); cached on the fold.

    Each step picks the pool whose admissible lines remove the most total residual variance given probe noise, then
    updates the covariance, exactly as `World.sparse_design` does for single lines.
    """

    if "pool_order" not in fold.cache:
        W = fold.world
        S = W.V @ W.V.T + np.diag(W.D)
        pools = sorted(set(fold.pid.tolist()))
        order, left = [], list(pools)
        while left:
            best = None
            for p in left:
                ls = np.where((fold.pid == p) & fold.avail)[0]
                if len(ls) == 0:
                    red = -1.0
                else:
                    A = S[np.ix_(ls, ls)] + W.s2 * np.eye(len(ls))
                    red = float(np.trace(S[:, ls] @ np.linalg.solve(A, S[ls, :])))
                if best is None or red > best[0]:
                    best = (red, p)
            order.append(best[1])
            left.remove(best[1])
            ls = np.where((fold.pid == best[1]) & fold.avail)[0]
            if len(ls):
                A = S[np.ix_(ls, ls)] + W.s2 * np.eye(len(ls))
                S = S - S[:, ls] @ np.linalg.solve(A, S[ls, :])
        fold.cache["pool_order"] = order
    return fold.cache["pool_order"]


def pool_lines(fold: "Fold", p: int) -> np.ndarray:
    """Admissible panel lines of pool `p`."""

    key = ("pool_lines", int(p))
    if key not in fold.cache:
        fold.cache[key] = np.where((fold.pid == p) & fold.avail)[0]
    return fold.cache[key]
