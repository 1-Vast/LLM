"""Agent core: acquisition arms, campaign loop, terminal audit and typed claims.

File summary
- Path: research/certified_discovery/agent.py
- Purpose: run one equal-budget discovery campaign in one target cell line for one arm, and
  return what it measured, what it claims about untested candidates, and what those claims
  turned out to be worth against the hidden labels.
- Core points:
  - Budget: ceil(fraction x candidates) experiments in `rounds` equal batches; laboratory cost
    in dose points (and wells where the source declares replicates) and turnaround days.
  - Every arm only ranks; the loop buys the top unmeasured batch (seeded random tie-break).
  - Terminal round, two variants from the same state: `exploit` buys the top batch; `certify`
    fixes a shortlist of kappa x batch top candidates and their scores, buys a uniformly random
    batch-sized audit from it, and certifies the untested remainder (certify.certify).
  - The world-model arms also make the naive claim a model-trusting agent would make: the
    largest top set whose mean posterior non-hit probability is <= alpha (Bayesian FDR), and
    the expected hit count of the remainder. Both are scored against the hidden labels.
- Interfaces: `CampaignSpec`, arms (`RandomArm`, `HeuristicArm`, `HistoryArm`, `WorldArm`,
  `MenuRandomArm`, `OracleArm`), `run_campaign`.
- Depends on: numpy, `certify`, `world`, `screens`.
"""
from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass

import numpy as np

from . import certify as cert
from .screens import Library
from .world import TransferWorld


@dataclass(frozen=True)
class CampaignSpec:
    budget_fraction: float = 0.10
    rounds: int = 4
    kappa: int = 3            # shortlist = kappa x final batch
    alpha: float = 0.2        # FDR level for certified nominations
    delta: float = 0.1        # 1 - confidence of the yield lower bound
    audit_seeds: int = 20     # independent audit draws per deterministic campaign
    wells_per_point: int = 1  # replicate wells behind one dose-point record


class RandomArm:
    name = "random"
    probabilistic = False

    def __init__(self, n: int, seed: int):
        self.rng = np.random.default_rng(seed)
        self.n = n

    def scores(self, measured, values):
        return self.rng.random(self.n)


class HeuristicArm:
    """Fixed single-agent rules; no combination data, no learning."""

    probabilistic = False

    def __init__(self, world: TransferWorld, kind: str):
        lib, rows = world.lib, world.rows
        ma, mb = world.mono_mean[lib.a[rows], lib.c[rows]], world.mono_mean[lib.b[rows], lib.c[rows]]
        if kind == "potency":
            self._scores = ma + mb
        elif kind == "headroom":
            self._scores = np.minimum(ma, mb) * (1.0 - world.expected[rows])
        else:
            raise ValueError(kind)
        self.name = f"heuristic_{kind}"

    def scores(self, measured, values):
        return self._scores


class HistoryArm:
    """Static retrieval: the pair's shrunk mean label in other lines."""

    name = "history"
    probabilistic = False

    def __init__(self, world: TransferWorld):
        self._scores = world.X_target[:, 0]

    def scores(self, measured, values):
        return self._scores


class WorldArm:
    probabilistic = True

    def __init__(self, world: TransferWorld, name: str, acquisition: str = "p_hit"):
        self.world, self.name, self.acquisition = world, name, acquisition
        self.last_p_hit = None

    def scores(self, measured, values):
        mean, var = self.world.posterior(measured, values)
        self.last_p_hit = self.world.p_hit(mean, var)
        return self.last_p_hit if self.acquisition == "p_hit" else mean


class MenuRandomArm:
    """Uniform choice from the world model's top menu_factor x k: the no-knowledge planner control."""

    probabilistic = True

    def __init__(self, world: TransferWorld, seed: int, menu_factor: int = 2):
        self.world, self.menu_factor = world, menu_factor
        self.rng = np.random.default_rng([seed, 31337])
        self.name = "wm_menu_random"
        self.last_p_hit = None

    def scores(self, measured, values):
        mean, var = self.world.posterior(measured, values)
        self.last_p_hit = self.world.p_hit(mean, var)
        return self.last_p_hit

    def choose(self, available, measured, values, k):
        p_hit = self.scores(measured, values)
        candidates = np.flatnonzero(available)
        menu = candidates[np.argsort(-p_hit[candidates], kind="stable")][: self.menu_factor * k]
        return self.rng.choice(menu, size=k, replace=False)


class OracleArm:
    name = "oracle"
    probabilistic = False

    def __init__(self, world: TransferWorld):
        self._scores = world.lib.y[world.rows]

    def scores(self, measured, values):
        return self._scores


def _top(scores: np.ndarray, available: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    candidates = np.flatnonzero(available)
    order = np.lexsort((rng.random(candidates.size), -scores[candidates]))
    return candidates[order[:k]]


def _bayes_fdr_selection(p_hit: np.ndarray, alpha: float) -> np.ndarray:
    """Largest top-ranked set whose mean posterior non-hit probability is <= alpha."""
    order = np.argsort(-p_hit, kind="stable")
    running = np.cumsum(1.0 - p_hit[order]) / np.arange(1, p_hit.size + 1)
    passing = np.flatnonzero(running <= alpha)
    return order[: passing[-1] + 1] if passing.size else order[:0]


def run_campaign(lib: Library, world: TransferWorld, arm, spec: CampaignSpec, seed: int) -> dict:
    """Run the shared rounds once, then branch into the exploit and certify terminal rounds."""
    started = time.perf_counter()
    rows = world.rows
    truth = lib.y[rows]
    hits_truth = truth > lib.threshold
    n = rows.size
    budget = int(math.ceil(spec.budget_fraction * n))
    batch = int(math.ceil(budget / spec.rounds))
    rng = np.random.default_rng(seed)
    measured = np.zeros(n, bool)
    order: list[int] = []
    per_round = []
    planner = getattr(arm, "choose", None)    # a black-box planner picks batches itself
    for _ in range(spec.rounds - 1):
        idx = np.flatnonzero(measured)
        k = int(min(batch, budget - measured.sum()))
        if planner is not None:
            chosen = planner(~measured, idx, truth[idx], k)
        else:
            chosen = _top(arm.scores(idx, truth[idx]), ~measured, k, rng)
        measured[chosen] = True
        order.extend(chosen.tolist())
        per_round.append(int(hits_truth[chosen].sum()))
    idx = np.flatnonzero(measured)
    last = int(budget - measured.sum())
    if planner is not None:
        exploit_pick = planner(~measured, idx, truth[idx], last)
    final_scores = arm.scores(idx, truth[idx]).copy()
    final_p = getattr(arm, "last_p_hit", None)
    final_p = None if final_p is None else final_p.copy()
    shared_hits = int(hits_truth[measured].sum())

    if planner is None:
        exploit_pick = _top(final_scores, ~measured, last, rng)
    exploit = {"hits": shared_hits + int(hits_truth[exploit_pick].sum()),
               "last_round_hits": int(hits_truth[exploit_pick].sum())}

    shortlist = _top(final_scores, ~measured, spec.kappa * last, rng)
    certified = []
    for draw in range(spec.audit_seeds):
        audit_rng = np.random.default_rng([seed, draw, 7919])
        audit, _ = cert.draw_audit(shortlist, last, audit_rng)
        certificate = cert.certify(shortlist, final_scores[shortlist], audit, hits_truth[audit],
                                   alpha=spec.alpha, delta=spec.delta)
        remainder_hits = int(hits_truth[certificate.remainder].sum())
        nominated_true = int(hits_truth[certificate.nominated].sum())
        record = {
            **certificate.summary(),
            "hits": shared_hits + int(hits_truth[audit].sum()),
            "nominated_true": nominated_true,
            "fdp": (certificate.nominated.size - nominated_true) / max(certificate.nominated.size, 1),
            "remainder_hits": remainder_hits,
            "yield_covered": certificate.yield_bound <= remainder_hits,
        }
        if final_p is not None:
            remainder = certificate.remainder
            naive = remainder[_bayes_fdr_selection(final_p[remainder], spec.alpha)]
            naive_true = int(hits_truth[naive].sum())
            predicted = remainder[final_p[remainder] >= 0.5]       # "the model says hit"
            record.update({
                "naive_nominated": int(naive.size), "naive_true": naive_true,
                "naive_fdp": (naive.size - naive_true) / max(naive.size, 1),
                "claimed_remainder_hits": float(final_p[remainder].sum()),
                "predicted_hits": int(predicted.size), "predicted_true": int(hits_truth[predicted].sum()),
                "predicted_claimed_precision": float(final_p[predicted].mean()) if predicted.size else None,
            })
        certified.append(record)
    return {
        "arm": arm.name, "line": lib.lines[world.target], "seed": seed, "candidates": int(n),
        "line_hits": int(hits_truth.sum()), "budget": budget, "batch": batch, "rounds": spec.rounds,
        "dose_points": int(lib.cost_points[rows][measured].sum() + lib.cost_points[rows][exploit_pick].sum()),
        "wells": int((lib.cost_points[rows][measured].sum() + lib.cost_points[rows][exploit_pick].sum())
                     * spec.wells_per_point),
        "days": spec.rounds * lib.days_per_round, "per_round_hits": per_round,
        "exploit": exploit, "certify": certified, "seconds": round(time.perf_counter() - started, 4),
        "planner_events": getattr(arm, "events", None),
        "world": {"s_drug": world.s_drug, "s_noise": world.s_noise} if hasattr(world, "s_drug") else None,
        "spec": asdict(spec),
    }
