"""Replay every arm in every target line of a screen and write one record per campaign.

File summary
- Path: research/certified_discovery/replay.py
- Purpose: the development and confirmatory runner. One process per target line builds the
  line's world models once and runs every arm against them at equal budget.
- Core points: deterministic given (library, spec, arms, seeds); BLAS threads pinned to one per
  worker; output is a write-once JSONL plus a manifest with the spec, library provenance,
  source digests and wall time; an existing output directory is refused.
- Interfaces: `ARMS`, `run_line`, `main` (python -m research.certified_discovery.replay).
- Depends on: numpy, `agent`, `world`, `screens`.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path

for _variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_variable, "1")

import numpy as np  # noqa: E402

from . import agent  # noqa: E402
from .screens import CACHE, Library, load_library, sha256  # noqa: E402
from .world import TransferWorld, WorldConfig  # noqa: E402

ARMS = ("random", "heuristic_potency", "heuristic_headroom", "history", "wm_static", "wm_full",
        "wm_greedy", "wm_nocontext", "wm_shuffled", "wm_menu_random", "oracle")
RANDOM_SEEDS = 20
SOURCES = ("screens.py", "world.py", "agent.py", "certify.py", "replay.py")


def run_line(task: tuple) -> list[dict]:
    library_path, line, spec_dict, arms, world_overrides = task
    lib = load_library(Path(library_path))
    spec = agent.CampaignSpec(**spec_dict)
    started = time.perf_counter()
    base = WorldConfig(**world_overrides)
    worlds = {"full": TransferWorld(lib, line, base)}
    if "wm_nocontext" in arms:
        worlds["nocontext"] = TransferWorld(lib, line, replace(base, context=False))
    if "wm_shuffled" in arms:
        worlds["shuffled"] = TransferWorld(lib, line, replace(base, shuffle_seed=1000 + line))
    build_seconds = time.perf_counter() - started
    full = worlds["full"]
    records = []
    for name in arms:
        if name == "random":
            for seed in range(RANDOM_SEEDS):
                records.append(agent.run_campaign(lib, full, agent.RandomArm(full.rows.size, seed), replace(spec, audit_seeds=1), seed))
            continue
        if name.startswith("heuristic_"):
            arm = agent.HeuristicArm(full, name.split("_", 1)[1])
        elif name == "history":
            arm = agent.HistoryArm(full)
        elif name == "oracle":
            arm = agent.OracleArm(full)
        elif name == "wm_menu_random":
            for seed in range(RANDOM_SEEDS):
                records.append(agent.run_campaign(lib, full, agent.MenuRandomArm(full, seed), replace(spec, audit_seeds=1), seed))
            continue
        elif name == "wm_static":
            arm = agent.WorldArm(TransferWorldView(full, feedback=False), name)
        elif name == "wm_full":
            arm = agent.WorldArm(full, name)
        elif name == "wm_greedy":
            arm = agent.WorldArm(full, name, acquisition="mean")
        elif name == "wm_nocontext":
            arm = agent.WorldArm(worlds["nocontext"], name)
        elif name == "wm_shuffled":
            arm = agent.WorldArm(worlds["shuffled"], name)
        else:
            raise ValueError(f"unknown arm {name}")
        records.append(agent.run_campaign(lib, full, arm, spec, seed=line))
    for record in records:
        record["world_build_seconds"] = round(build_seconds, 3)
        record["eb"] = {key: {"s_drug": w.s_drug, "s_noise": w.s_noise} for key, w in worlds.items()}
    return records


class TransferWorldView:
    """The same fitted world with feedback switched off (no refit, identical prior)."""

    def __init__(self, world: TransferWorld, *, feedback: bool):
        self._world, self._feedback = world, feedback

    def posterior(self, measured, values):
        if not self._feedback:
            return self._world.prior_target.copy(), self._world.prior_var_target.copy()
        return self._world.posterior(measured, values)

    def p_hit(self, mean, var):
        return self._world.p_hit(mean, var)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--library", default=str(CACHE / "oneil_v1.npz"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--arms", default=",".join(ARMS))
    parser.add_argument("--lines", default="all", help="comma-separated line indices or 'all'")
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--spec", default="{}", help="JSON overrides for CampaignSpec")
    parser.add_argument("--world", default="{}", help="JSON overrides for WorldConfig")
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}: records are write-once")
    lib: Library = load_library(Path(args.library))
    spec = agent.CampaignSpec(**json.loads(args.spec))
    world_overrides = json.loads(args.world)
    lines = range(len(lib.lines)) if args.lines == "all" else [int(x) for x in args.lines.split(",")]
    arms = tuple(args.arms.split(","))
    tasks = [(args.library, line, asdict(spec), arms, world_overrides) for line in lines]
    started = time.time()
    out.mkdir(parents=True)
    records = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for batch in pool.map(run_line, tasks):
            records.extend(batch)
    with open(out / "campaigns.jsonl", "w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    here = Path(__file__).resolve().parent
    manifest = {
        "library": lib.name, "library_path": args.library, "library_sha256": sha256(Path(args.library)),
        "provenance": lib.provenance, "spec": asdict(spec), "world": world_overrides, "arms": arms,
        "lines": len(list(lines)), "random_seeds": RANDOM_SEEDS, "records": len(records),
        "wall_seconds": round(time.time() - started, 1), "workers": args.workers,
        "sources": {name: sha256(here / name) for name in SOURCES},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"records": len(records), "wall_seconds": manifest["wall_seconds"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
