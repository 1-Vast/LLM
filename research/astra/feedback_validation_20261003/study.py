"""Matched-budget discovery campaigns scored against independent validation outcomes.

File summary
- Path: research/astra/feedback_validation_20261003/study.py
- Purpose: for every target cell line of a `Panel`, run equal-budget campaigns for static
  retrieval, static transfer models, the same transfer model updated with purchased target-line
  measurements, a within-round feedback-shuffle control, random and oracle arms; record every
  purchase and score it on the screen call, the hidden validation call and the validation label.
- Core points:
  - The world model is the frozen empirical-Bayes `TransferWorld` with context off; arms only
    change how its in-context posterior is used or which values it is fed (wrappers adapted from
    WS1 `feedback_decomposition.py`). Labels reach an arm only through purchased experiments.
  - The loop mirrors the frozen `agent.run_campaign` shared rounds and exploit branch, with the
    frozen `_top` tie-break; there is no certify branch here.
  - Validation outcomes are never visible to any arm; they are joined only after a campaign ends.
  - Controls: within-round residual shuffle (breaks drug-outcome pairing) and wrong-line feedback
    (the same pairs' labels from another line: breaks target-line specificity). `rate_feedback`
    learns the screen call itself (history_rate prior + in-context posterior on a 0/100 label).
  - Unit of analysis: the target line. Elapsed time is reported in rounds (a static arm could
    buy its whole budget in one round; feedback needs `rounds` sequential rounds).
- Interfaces: `Panel`, `Budget`, `ARMS`, `STATIC_ARMS`, `run_line`, `campaign`.
- Depends on: numpy, scipy, scikit-learn, research.certified_discovery (frozen; imported only).
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, replace

import numpy as np
from scipy import special

from research.certified_discovery import agent
from research.certified_discovery.screens import Library
from research.certified_discovery.world import TransferWorld, WorldConfig

RANDOM_SEEDS = 20
SHUFFLE_SEEDS = 10
STATIC_ARMS = ("history_mean", "history_rate", "ridge_static", "gbm_static")
CONTROL_SEEDS = 10
FEEDBACK_ARM = "feedback"
WORLD = WorldConfig(context=False)


@dataclass
class Panel:
    """One screen as a candidate library plus hidden screen and validation outcomes."""

    name: str
    stratum: str
    library: Library                 # y = screen label agents learn from; history = other lines
    screen_hit: np.ndarray           # discovery call on the purchased (screen) measurement
    valid_hit: np.ndarray            # call on the independent validation measurement
    valid_y: np.ndarray              # validation label (NaN where missing)
    valid_efficacious: np.ndarray    # validation measurement shows meaningful efficacy
    valid_missing: np.ndarray        # no validation outcome (never imputed; reported)
    screen_hit_strict: np.ndarray | None = None   # strict-majority calls (sensitivity)
    valid_hit_strict: np.ndarray | None = None
    replicate: str = ""


@dataclass(frozen=True)
class Budget:
    fraction: float = 0.10
    rounds: int = 4


class Posterior:
    """The frozen world's in-context residual model with a replaceable prior and usage mode."""

    def __init__(self, world: TransferWorld, prior: np.ndarray | None = None):
        self.w = world
        self.prior = world.prior_target.copy() if prior is None else np.asarray(prior, float)
        self.Z = world.Z_target
        self.prior_var = np.einsum("ij,jk,ik->i", self.Z, world.A, self.Z) + world.s_noise
        self.Zu = self.Z[:, 1:]
        self.prior_drug_var = np.einsum("ij,jk,ik->i", self.Zu, world.A[1:, 1:], self.Zu)

    def predict(self, measured, values, mode: str) -> np.ndarray:
        w = self.w
        if mode == "static" or len(measured) == 0:
            return self.prior.copy()
        measured = np.asarray(measured, int)
        resid = np.asarray(values, float) - self.prior[measured]
        Zm = self.Z[measured]
        cov = np.linalg.inv(w.A_inv + Zm.T @ Zm / w.s_noise)
        eff = cov @ (Zm.T @ resid) / w.s_noise
        if mode == "full":
            return self.prior + self.Z @ eff
        if mode == "offset":
            return self.prior + eff[0]
        raise ValueError(mode)


class WrongLineFeedback:
    """Feed the same pairs' screen labels from a randomly chosen other line (target specificity control)."""

    def __init__(self, post: "Posterior", world: TransferWorld, seed: int):
        lib = world.lib
        others = np.setdiff1d(np.unique(lib.c), [world.target])
        donor = int(np.random.default_rng([seed, world.target, 777]).choice(others))
        rows = np.flatnonzero(lib.c == donor)
        by_pair = dict(zip(world.pair_id[rows].tolist(), lib.y[rows].tolist()))
        target_pairs = world.pair_id[world.rows]
        self.fed = np.array([by_pair.get(int(p), np.nan) for p in target_pairs])
        self.fed = np.where(np.isfinite(self.fed), self.fed, post.prior)
        self.post, self.donor = post, donor

    def __call__(self, idx, values):
        idx = np.asarray(idx, int)
        return self.post.predict(idx, self.fed[idx], "full")


class ShuffledFeedback:
    """Feed the model residuals permuted among the experiments bought in the same round."""

    def __init__(self, post: Posterior, seed: int):
        self.post = post
        self.rng = np.random.default_rng([seed, 4242])
        self.fed: dict[int, float] = {}

    def __call__(self, idx, values):
        idx = np.asarray(idx, int)
        new = np.array([i for i in idx.tolist() if i not in self.fed], int)
        if new.size:
            v = np.asarray(values, float)[np.searchsorted(idx, new)]
            r = v - self.post.prior[new]
            fed = self.post.prior[new] + r[self.rng.permutation(new.size)]
            self.fed.update(zip(new.tolist(), fed.tolist()))
        return self.post.predict(idx, np.array([self.fed[i] for i in idx.tolist()], float), "full")


def history_rate(world: TransferWorld, screen_hit: np.ndarray) -> np.ndarray:
    """Shrunk screen-call rate of each pair in the other lines; ties broken by the shrunk mean label."""
    lib = world.lib
    hist = world.history_rows
    pid = world.pair_id
    n_pairs = int(pid.max()) + 1
    hits = np.bincount(pid[hist], weights=screen_hit[hist].astype(float), minlength=n_pairs)
    count = np.bincount(pid[hist], minlength=n_pairs).astype(float)
    k0 = world.config.shrink
    base = float(screen_hit[hist].mean()) if hist.size else 0.0
    rate = (hits + k0 * base) / (count + k0)
    return 1000.0 * rate[pid[world.rows]] + world.X_target[:, 0] / 1000.0


def gbm_prior(world: TransferWorld) -> np.ndarray:
    from sklearn.ensemble import HistGradientBoostingRegressor

    model = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, random_state=0)
    model.fit(world.X_history, world.lib.y[world.history_rows])
    return model.predict(world.X_target)


def campaign(world: TransferWorld, score, seed: int, budget: Budget) -> list[np.ndarray]:
    """Shared rounds plus exploit branch of the frozen loop; returns purchases per round."""
    rows = world.rows
    truth = world.lib.y[rows]
    n = rows.size
    total = int(math.ceil(budget.fraction * n))
    batch = int(math.ceil(total / budget.rounds))
    rng = np.random.default_rng(seed)
    measured = np.zeros(n, bool)
    rounds: list[np.ndarray] = []
    for _ in range(budget.rounds - 1):
        idx = np.flatnonzero(measured)
        k = int(min(batch, total - measured.sum()))
        chosen = agent._top(score(idx, truth[idx]), ~measured, k, rng)
        measured[chosen] = True
        rounds.append(chosen)
    idx = np.flatnonzero(measured)
    last = int(total - measured.sum())
    rounds.append(agent._top(score(idx, truth[idx]), ~measured, last, rng))
    return rounds


def _record(panel: Panel, world: TransferWorld, rounds: list[np.ndarray]) -> dict:
    local = np.concatenate(rounds)
    rows = world.rows[local]
    screen = panel.screen_hit[rows]
    valid = panel.valid_hit[rows] & ~panel.valid_missing[rows]
    vy = panel.valid_y[rows]
    strict = None
    if panel.screen_hit_strict is not None and panel.valid_hit_strict is not None:
        strict = int((panel.screen_hit_strict[rows] & panel.valid_hit_strict[rows]).sum())
    return {
        "purchases": [r.tolist() for r in rounds],
        "screen_hits": int(screen.sum()),
        "screen_hits_nonmissing": int((screen & ~panel.valid_missing[rows]).sum()),
        "validated": int((screen & valid).sum()),
        "validated_strict": strict,
        "validated_pairs": world.pair_id[rows[screen & valid]].tolist(),
        "valid_calls": int(valid.sum()),
        "valid_missing": int(panel.valid_missing[rows].sum()),
        "valid_y_sum": float(np.nansum(vy)), "valid_y_n": int(np.isfinite(vy).sum()),
        "validated_efficacious": int((screen & valid & panel.valid_efficacious[rows]).sum()),
        "wells": int(world.lib.cost_points[rows].sum()),
        "screen_hits_per_round": [int(panel.screen_hit[world.rows[r]].sum()) for r in rounds],
    }


def run_line(panel: Panel, line: int, budgets: dict[str, Budget]) -> dict:
    lib = panel.library
    t0 = time.perf_counter()
    world = TransferWorld(lib, line, WORLD)
    build = time.perf_counter() - t0
    rows = world.rows
    post = Posterior(world)
    gbm = gbm_prior(world)
    gpost = Posterior(world, prior=gbm)
    hpost = Posterior(world, prior=world.X_target[:, 0])
    rate = history_rate(world, panel.screen_hit)
    binary = replace(lib, y=100.0 * panel.screen_hit.astype(float), threshold=50.0)
    bworld = TransferWorld(binary, line, WORLD)
    rpost = Posterior(bworld, prior=bworld.X_target[:, 0])
    oracle_screen = 1000.0 * panel.screen_hit[rows] + lib.y[rows] / 1000.0
    vy = np.nan_to_num(panel.valid_y[rows], nan=-1e6)
    oracle_valid = 1000.0 * (panel.screen_hit[rows] & panel.valid_hit[rows]) + vy / 1e9
    fixed = {
        "history_mean": world.X_target[:, 0], "history_rate": rate, "ridge_static": post.prior,
        "gbm_static": gbm, "oracle_screen": oracle_screen, "oracle_validated": oracle_valid,
    }
    out = {"panel": panel.name, "stratum": panel.stratum, "replicate": panel.replicate, "line": lib.lines[line],
           "line_index": line, "candidates": int(rows.size), "rows": rows.tolist(),
           "pair_ids": world.pair_id[rows].tolist(),
           "line_screen_hits": int(panel.screen_hit[rows].sum()),
           "line_validated": int((panel.screen_hit[rows] & panel.valid_hit[rows] & ~panel.valid_missing[rows]).sum()),
           "line_valid_missing": int(panel.valid_missing[rows].sum()),
           "s_line": world.s_line, "s_drug": world.s_drug, "s_noise": world.s_noise,
           "world_build_seconds": round(build, 3), "budgets": {}}
    seed = line
    for tag, budget in budgets.items():
        arms: dict = {}
        for name, scores in fixed.items():
            arms[name] = _record(panel, world, campaign(world, lambda i, v, s=scores: s, seed, budget))
        arms["feedback"] = _record(panel, world, campaign(world, lambda i, v: post.predict(i, v, "full"), seed, budget))
        arms["offset_only"] = _record(panel, world, campaign(world, lambda i, v: post.predict(i, v, "offset"), seed, budget))
        arms["history_feedback"] = _record(panel, world, campaign(world, lambda i, v: hpost.predict(i, v, "full"), seed, budget))
        arms["gbm_feedback"] = _record(panel, world, campaign(world, lambda i, v: gpost.predict(i, v, "full"), seed, budget))
        arms["rate_feedback"] = _record(panel, world, campaign(bworld, lambda i, v: rpost.predict(i, v, "full"),
                                                               seed, budget))
        arms["shuffle"] = [_record(panel, world, campaign(world, ShuffledFeedback(post, s), seed, budget))
                           for s in range(SHUFFLE_SEEDS)]
        arms["wrong_line"] = [_record(panel, world, campaign(world, WrongLineFeedback(post, world, s), seed, budget))
                              for s in range(CONTROL_SEEDS)]
        arms["random"] = [_record(panel, world, campaign(world, agent.RandomArm(rows.size, s).scores, s, budget))
                          for s in range(RANDOM_SEEDS)]
        out["budgets"][tag] = {"fraction": budget.fraction, "rounds": budget.rounds, "arms": arms}
    out["seconds"] = round(time.perf_counter() - t0, 2)
    return out


ARMS = STATIC_ARMS + ("feedback", "offset_only", "history_feedback", "gbm_feedback", "rate_feedback", "shuffle",
                      "wrong_line", "random", "oracle_screen", "oracle_validated")
