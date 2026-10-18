"""Build (in parallel) the cached scenarios of the development tasks and of the held-out task groups.

File summary
- Path: research/acquisition_program_20261018/ap_build.py
- Purpose: for each (fold, target group, noise scenario) compute the lookahead features, the counterfactual table of
  final ridge scores and the comparator scores, and cache them under tmp/acquisition_program/. The held-out kind is
  built only after the incumbent program is frozen (`evaluate.py` enforces this through FREEZE.json).
- Kinds: `dev` = folds 0 and 1 (each trained on the other), target groups 0 and 1, noise salts dev1..dev5, all complete campaigns
  per task; `held` = folds 2, 3, 4 (trained on the other four), target groups 2 and 3, noise salts fresh1..fresh5,
  6 campaigns per task (folds are exposed data; groups and salts are disjoint from the development ones).
- Usage: ``python -B ap_build.py dev|held``.
"""
from __future__ import annotations

import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ap_task as A  # noqa: E402
import bench  # noqa: E402

CACHE = HERE.parents[1] / "tmp" / "acquisition_program"
KINDS = {"dev": {"folds": ((0, (1,)), (1, (0,))), "groups": (0, 1), "salts": tuple(f"dev{k}" for k in range(1, 6)), "ncamp": 99},
         "held": {"folds": ((2, None), (3, None), (4, None)), "groups": (2, 3), "salts": tuple(f"fresh{k}" for k in range(1, 6)), "ncamp": 99}}
_TABLES = None


def _tables():
    global _TABLES
    if _TABLES is None:
        _TABLES = bench.load_tables()
    return _TABLES


def get_task(kind: str, ev: int, group: int):
    cfg = KINDS[kind]
    train = dict(cfg["folds"])[ev]
    fold = bench.make_fold(_tables(), ev, train)
    return A.make_task(fold, group, cfg["ncamp"])


def path_for(kind, ev, group, salt) -> Path:
    return CACHE / kind / f"f{ev}_g{group}_{salt}.pkl"


def job(args):
    kind, ev, group, salt = args
    out = path_for(kind, ev, group, salt)
    if out.exists():
        return str(out), 0.0
    t0 = time.time()
    task = get_task(kind, ev, group)
    sc = A.build_scenario(task, salt)
    sc.pop("hidden")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as fh:
        pickle.dump(sc, fh)
    return str(out), time.time() - t0


def load_all(kind: str) -> list:
    """[(Task, [scenario dicts with hidden restored])] for every (fold, group) of the kind."""

    cfg = KINDS[kind]
    out = []
    for ev, _ in cfg["folds"]:
        for g in cfg["groups"]:
            task = get_task(kind, ev, g)
            scs = []
            for salt in cfg["salts"]:
                with open(path_for(kind, ev, g, salt), "rb") as fh:
                    sc = pickle.load(fh)
                sc["hidden"] = A.scenario_hidden(task.fold, salt)
                scs.append(sc)
            out.append((task, scs))
    return out


def main(kind: str) -> None:
    if kind == "held":
        import seal
        seal.check(1)
        seal.check(2)
    cfg = KINDS[kind]
    jobs = [(kind, ev, g, s) for ev, _ in cfg["folds"] for g in cfg["groups"] for s in cfg["salts"]]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=10) as ex:
        for path, sec in ex.map(job, jobs):
            print(Path(path).name, round(sec), f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
