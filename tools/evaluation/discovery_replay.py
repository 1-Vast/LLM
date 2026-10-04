"""Equal-budget replay of certified discovery on a measured combination screen.

File summary
- Path: tools/evaluation/discovery_replay.py
- Purpose: evaluate planners for certified combination discovery against a full-factorial
  screen whose every outcome was measured, one campaign per target cell line, with the zero arm,
  fixed rules, static retrieval, world-model variants and the oracle at equal budget.
- Core points:
  - Each campaign shares rounds 1..R-1, then branches: `exploit` buys the top final batch;
    `certify` buys `audit_seeds` independent uniformly random audits from the top kappa x batch
    shortlist and certifies the remainder with `maestro.certification`.
  - Records carry measured hits, certificate outcomes against the hidden labels (false-discovery
    proportion, yield-bound coverage), the world model's own claims (expected remainder hits,
    "P(hit) >= 0.5"), laboratory cost (experiments, dose points, wells, days) and seconds.
  - `summarise` resamples target lines (the unit) for every interval.
  - Promoted from research/certified_discovery (agent, replay, analysis); LLM planner arms stay
    in research.
- Interfaces: `ARMS`, `run_campaign`, `replay_line`, `summarise`, `main` (python -m
  tools.evaluation.discovery_replay).
- Depends on: numpy, `maestro.certification`, `virtual_cell.combination_world`,
  `tools.datasets.combination_screens`.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np

from maestro import certification as cert
from virtual_cell.combination_world import CombinationWorld, CombinationWorldConfig

from ..datasets.combination_screens import ScreenLibrary, load_library, sha256

ARMS = ("random", "heuristic_potency", "heuristic_headroom", "history", "wm_static", "wm_full", "wm_greedy",
        "wm_nocontext", "wm_shuffled", "wm_menu_random", "oracle")
SEEDED_ARMS = ("random", "wm_menu_random")
BOOTSTRAP = 10_000


@dataclass(frozen=True)
class ReplaySpec:
    budget_fraction: float = 0.10
    rounds: int = 4
    kappa: int = 2
    alpha: float = 0.2
    delta: float = 0.1
    audit_seeds: int = 20
    random_seeds: int = 20


class _Static:
    probabilistic = False

    def __init__(self, name, scores):
        self.name, self._scores = name, scores

    def scores(self, measured, values):
        return self._scores


class _World:
    probabilistic = True

    def __init__(self, name, world: CombinationWorld, *, feedback=True, acquisition="p_hit"):
        self.name, self.world, self.feedback, self.acquisition = name, world, feedback, acquisition
        self.last_p_hit = None

    def scores(self, measured, values):
        if self.feedback:
            mean, var = self.world.posterior(measured, values)
        else:
            mean, var = self.world.prior_target.copy(), self.world.prior_var_target.copy()
        self.last_p_hit = self.world.p_hit(mean, var)
        return self.last_p_hit if self.acquisition == "p_hit" else mean


class _MenuRandom(_World):
    def __init__(self, world, seed, factor=2):
        super().__init__("wm_menu_random", world)
        self.rng, self.factor = np.random.default_rng([seed, 31337]), factor

    def choose(self, available, measured, values, k):
        p = self.scores(measured, values)
        candidates = np.flatnonzero(available)
        menu = candidates[np.argsort(-p[candidates], kind="stable")][: self.factor * k]
        return self.rng.choice(menu, size=k, replace=False)


def _top(scores, available, k, rng):
    candidates = np.flatnonzero(available)
    order = np.lexsort((rng.random(candidates.size), -scores[candidates]))
    return candidates[order[:k]]


def run_campaign(library: ScreenLibrary, world: CombinationWorld, arm, spec: ReplaySpec, seed: int, audit_seeds: int) -> dict:
    started = time.perf_counter()
    screen, rows = library.screen, world.rows
    truth = screen.y[rows]
    hits = truth > screen.threshold
    n = rows.size
    budget = int(math.ceil(spec.budget_fraction * n))
    batch = int(math.ceil(budget / spec.rounds))
    rng = np.random.default_rng(seed)
    measured = np.zeros(n, bool)
    choose = getattr(arm, "choose", None)
    per_round = []
    for _ in range(spec.rounds - 1):
        idx = np.flatnonzero(measured)
        k = int(min(batch, budget - measured.sum()))
        chosen = choose(~measured, idx, truth[idx], k) if choose else _top(arm.scores(idx, truth[idx]), ~measured, k, rng)
        measured[chosen] = True
        per_round.append(int(hits[chosen].sum()))
    idx = np.flatnonzero(measured)
    last = int(budget - measured.sum())
    exploit = choose(~measured, idx, truth[idx], last) if choose else None
    final = arm.scores(idx, truth[idx]).copy()
    final_p = None if getattr(arm, "last_p_hit", None) is None else arm.last_p_hit.copy()
    if exploit is None:
        exploit = _top(final, ~measured, last, rng)
    shared = int(hits[measured].sum())
    shortlist = _top(final, ~measured, spec.kappa * last, rng).tolist()
    draws = []
    for draw in range(audit_seeds):
        audit, _ = cert.draw_audit(shortlist, last, random.Random(f"{seed}-{draw}"))
        c = cert.certify(shortlist, final[shortlist], audit, hits[audit].tolist(), alpha=spec.alpha, delta=spec.delta)
        nominated = list(c.nominated)
        true = int(hits[nominated].sum()) if nominated else 0
        remainder = list(c.remainder)
        record = {**c.summary(), "hits": shared + int(hits[audit].sum()), "nominated_true": true,
                  "fdp": (len(nominated) - true) / max(len(nominated), 1),
                  "remainder_hits": int(hits[remainder].sum()), "yield_covered": c.yield_bound <= int(hits[remainder].sum())}
        if final_p is not None and remainder:
            predicted = [i for i in remainder if final_p[i] >= 0.5]
            record.update({"claimed_remainder_hits": float(final_p[remainder].sum()),
                           "predicted_hits": len(predicted), "predicted_true": int(hits[predicted].sum()) if predicted else 0})
        draws.append(record)
    points = int(library.cost_points[rows][measured].sum() + library.cost_points[rows][exploit].sum())
    return {"arm": arm.name, "line": screen.lines[world.target], "seed": seed, "candidates": int(n),
            "line_hits": int(hits.sum()), "budget": budget, "batch": batch, "per_round_hits": per_round,
            "exploit": {"hits": shared + int(hits[exploit].sum())}, "certify": draws, "dose_points": points,
            "wells": points * library.wells_per_point, "days": spec.rounds * library.days_per_round,
            "seconds": round(time.perf_counter() - started, 4)}


def replay_line(task: tuple) -> list[dict]:
    path, line, spec_dict, arms = task
    library, spec = load_library(Path(path)), ReplaySpec(**spec_dict)
    started = time.perf_counter()
    full = CombinationWorld(library.screen, line)
    worlds = {"full": full}
    if "wm_nocontext" in arms:
        worlds["nocontext"] = CombinationWorld(library.screen, line, CombinationWorldConfig(context=False))
    if "wm_shuffled" in arms:
        worlds["shuffled"] = CombinationWorld(library.screen, line, CombinationWorldConfig(shuffle_seed=1000 + line))
    build = round(time.perf_counter() - started, 3)
    s, rows = library.screen, full.rows
    ma, mb = full.mono_mean[s.a[rows], s.c[rows]], full.mono_mean[s.b[rows], s.c[rows]]
    makers = {
        "heuristic_potency": lambda: _Static("heuristic_potency", ma + mb),
        "heuristic_headroom": lambda: _Static("heuristic_headroom", np.minimum(ma, mb) * (1.0 - full.expected[rows])),
        "history": lambda: _Static("history", full.X_target[:, 0]),
        "oracle": lambda: _Static("oracle", s.y[rows]),
        "wm_static": lambda: _World("wm_static", full, feedback=False),
        "wm_full": lambda: _World("wm_full", full),
        "wm_greedy": lambda: _World("wm_greedy", full, acquisition="mean"),
        "wm_nocontext": lambda: _World("wm_nocontext", worlds.get("nocontext", full)),
        "wm_shuffled": lambda: _World("wm_shuffled", worlds.get("shuffled", full)),
    }
    records = []
    for name in arms:
        if name in SEEDED_ARMS:
            for seed in range(spec.random_seeds):
                arm = (_Static("random", np.random.default_rng(seed).random(rows.size)) if name == "random"
                       else _MenuRandom(full, seed))
                records.append(run_campaign(library, full, arm, spec, seed, 1))
        else:
            records.append(run_campaign(library, full, makers[name](), spec, line, spec.audit_seeds))
    for record in records:
        record["world_build_seconds"] = build
        record["world_variances"] = {"s_line": full.s_line, "s_drug": full.s_drug, "s_noise": full.s_noise}
    return records


def _bootstrap(values, statistic=np.mean, seed=20261003):
    values = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    stats = statistic(values[rng.integers(0, values.size, size=(BOOTSTRAP, values.size))], axis=1)
    return [float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))]


def summarise(records: list[dict], reference: str = "history") -> dict:
    """Per-arm totals and paired per-line contrasts; lines are resampled."""
    table: dict[str, dict[str, list]] = {}
    for record in records:
        table.setdefault(record["arm"], {}).setdefault(record["line"], []).append(record)
    lines = sorted(next(iter(table.values())))

    def line_mean(arm, line, key):
        runs = table[arm][line]
        if key == "exploit":
            return float(np.mean([r["exploit"]["hits"] for r in runs]))
        return float(np.mean([d[key] for r in runs for d in r["certify"]]))

    out = {"lines": len(lines), "total_line_hits": int(sum(table[next(iter(table))][l][0]["line_hits"] for l in lines)),
           "arms": {}, "contrasts": {}}
    for arm in table:
        exploit = np.array([line_mean(arm, l, "exploit") for l in lines])
        certify = np.array([line_mean(arm, l, "hits") for l in lines])
        fdp = np.array([line_mean(arm, l, "fdp") for l in lines])
        out["arms"][arm] = {"exploit_hits": float(exploit.sum()), "certify_hits": float(certify.sum()),
                            "fdr": float(fdp.mean()), "fdr_ci": _bootstrap(fdp),
                            "nominated": float(sum(line_mean(arm, l, "nominated") for l in lines)),
                            "yield_coverage": float(np.mean([line_mean(arm, l, "yield_covered") for l in lines])),
                            "seconds_per_campaign": float(np.mean([r["seconds"] for l in lines for r in table[arm][l]]))}
        if arm != reference and reference in table:
            diff = exploit - np.array([line_mean(reference, l, "exploit") for l in lines])
            out["contrasts"][f"{arm}-{reference}"] = {"sum": float(diff.sum()), "ci_mean": _bootstrap(diff)}
    return out


def main(argv=None) -> int:
    for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ.setdefault(variable, "1")
    parser = argparse.ArgumentParser(description="Equal-budget certified-discovery replay on a measured screen.")
    parser.add_argument("--library", required=True, help=".npz written by tools.datasets.combination_screens")
    parser.add_argument("--out", required=True)
    parser.add_argument("--arms", default=",".join(ARMS))
    parser.add_argument("--lines", default="all")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--spec", default="{}", help="JSON overrides for ReplaySpec")
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}: records are write-once")
    library, spec = load_library(Path(args.library)), ReplaySpec(**json.loads(args.spec))
    lines = range(len(library.screen.lines)) if args.lines == "all" else [int(x) for x in args.lines.split(",")]
    tasks = [(args.library, line, asdict(spec), tuple(args.arms.split(","))) for line in lines]
    started = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        records = [record for batch in pool.map(replay_line, tasks) for record in batch]
    out.mkdir(parents=True)
    with open(out / "campaigns.jsonl", "w", encoding="utf-8", newline="\n") as handle:
        handle.writelines(json.dumps(r, sort_keys=True) + "\n" for r in records)
    summary = summarise(records)
    manifest = {"library": library.name, "library_sha256": sha256(Path(args.library)), "spec": asdict(spec),
                "records": len(records), "wall_seconds": round(time.time() - started, 1), "summary": summary}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({name: [v["exploit_hits"], round(v["certify_hits"], 1)] for name, v in summary["arms"].items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
