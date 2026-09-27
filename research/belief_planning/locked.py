"""The registered runs: the development replay, and the one-time external evaluation behind the vault.

File summary
- Path: research/belief_planning/locked.py
- Purpose: run the frozen arms (`replay.LADDER` plus `replay.AGENT`) through one sealed interface.
  - `--dev`: the 20 registered development tasks (SciPlex3 A/B, L1000 LT/T).
  - `--external`: the GSE70138 study, once, only after `freeze.json` verifies and registers the
    external manifest's digest.
- Core points:
  - Refuses to run unless every frozen file still hashes to its registered digest.
  - The vault is opened at most once. Opening appends to `vault_access.jsonl`, and a second
    opening is refused unless the record shows the first did not reach the replay.
  - Nothing after the opening is tuned. The analysis is `analysis.py`, frozen with the rest.
- Run:
  - python -m research.belief_planning.locked --dev [--workers N]
  - python -m research.belief_planning.locked --external [--workers N]
- Depends on: replay.py, external_phase2.py, tasks.py, research/external_validation/firewall.py
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import pickle
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(variable, "1")

from research.external_validation import firewall as F  # noqa: E402

from . import replay as R  # noqa: E402
from . import tasks as T  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = T.ROOT
OUT = ROOT / "outputs" / "belief_planning_20260927"
FREEZE = HERE / "freeze.json"
MANIFEST = HERE / "manifests" / "gse70138_p2ld.json"
ACCESS_LOG = OUT / "external" / "vault_access.jsonl"
NAMES = tuple(R.LADDER) + tuple(R.AGENT)


def verified_freeze() -> dict:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    problems = F.verify_freeze(freeze, ROOT)
    if problems:
        raise F.FreezeMismatch("; ".join(problems))
    return freeze


def environment() -> dict:
    import numpy
    import pandas
    import scipy
    import sklearn
    return {"python": sys.version.split()[0], "platform": platform.platform(), "numpy": numpy.__version__,
            "pandas": pandas.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__}


def _write(path: Path, records) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


# ------------------------------------------------------------------------------ development
def dev_task(task, names):
    from threadpoolctl import threadpool_limits
    dataset, tier, fold = task
    with threadpool_limits(limits=1):
        data, ctx, setting = T.load(dataset, tier, fold)
        unit = T.units(dataset)[T.UNIT[dataset]].astype(str).to_dict()
        result = R.run({"dataset": dataset}, ctx, fold, tier, setting, names, unit)
    result["task"] = task
    return result


def run_dev(workers: int, names) -> None:
    verified_freeze()
    out = OUT / "registered" / "dev"
    manifest = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "environment": environment(),
                "arms": list(names), "tasks": {}, "problems": {}, "hyperparameters": {}, "validator": {}}
    features = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(dev_task, t, names): t for t in T.TASKS}
        for future in as_completed(futures):
            result = future.result()
            d, t, f = result["task"]
            name = f"{d}_{t}_{f}"
            _write(out / f"{name}.jsonl.gz", result["records"])
            manifest["tasks"][name] = {"episodes": result["episodes"], "records": len(result["records"])}
            manifest["problems"][name] = result["problems"]
            manifest["hyperparameters"][name] = result["world_hyperparameters"]
            manifest["validator"][name] = result["validator"]
            features += [{**f, "dataset": d} for f in result["features"]]
            print(name, len(result["records"]), "problems", len(result["problems"]), flush=True)
    import pandas as pd
    pd.DataFrame(features).to_csv(out / "compound_features.csv", index=False)
    manifest["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    (out / "manifest.json").write_bytes(json.dumps(manifest, indent=1, default=str).encode("utf-8"))


# ------------------------------------------------------------------------------ external
def _open_vault(freeze: dict) -> dict:
    manifest_sha = F.sha256_file(MANIFEST)
    registered = (freeze.get("external_study") or {}).get("manifest_sha256")
    if registered != manifest_sha:
        raise F.FreezeMismatch("external manifest digest is not the registered one")
    ACCESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    if ACCESS_LOG.exists():
        entries = [json.loads(line) for line in ACCESS_LOG.read_text(encoding="utf-8").splitlines() if line]
        if any(e.get("event") == "replay_started" for e in entries):
            raise RuntimeError("vault_already_opened: the external replay has already run once")
    entry = {"event": "vault_opened", "at_utc": datetime.now(timezone.utc).isoformat(), "study": "GSE70138",
             "manifest_sha256": manifest_sha, "freeze_sha256": F.sha256_file(FREEZE)}
    with ACCESS_LOG.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def _log(event: str, **extra) -> None:
    with ACCESS_LOG.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"event": event, "at_utc": datetime.now(timezone.utc).isoformat(), **extra}) + "\n")


def external_chunk(path: str, names, start: int, stop: int):
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1), open(path, "rb") as fh:
        study = pickle.load(fh)
    ctx, setting, unit = study["ctx"], study["setting"], study["unit"]
    from . import external_phase2 as X
    episodes = T.E.episode_list(ctx, X.TEST_FOLD)[start:stop]
    with threadpool_limits(limits=1):
        return R.run({"dataset": "gse70138"}, ctx, X.TEST_FOLD, "P2LD", setting, names, unit, episodes=episodes)


def run_external(workers: int, names) -> None:
    from . import external_phase2 as X
    freeze = verified_freeze()
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    _open_vault(freeze)
    t0 = time.time()
    data, ctx, setting, summary = X.open_study(man)
    unit = {t["compound"]: str(t["unit"]) for t in man["test_compounds"]}
    episodes = T.E.episode_list(ctx, X.TEST_FOLD)
    out = OUT / "external"
    opened = out / "opened_study.pkl"
    with opened.open("wb") as fh:
        pickle.dump({"ctx": ctx, "setting": setting, "unit": unit}, fh)
    summary["episodes"] = len(episodes)
    summary["opened_seconds"] = time.time() - t0
    (out / "study_summary.json").write_bytes(json.dumps(summary, indent=1, default=str).encode("utf-8"))
    _log("replay_started", episodes=len(episodes), pool=summary["pool"],
         eligible_test_compounds=summary["eligible_test_compounds"])
    chunk = max(1, len(episodes) // (workers * 4) + 1)
    records, problems, hyper, features = [], [], None, []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(external_chunk, str(opened), names, s, min(s + chunk, len(episodes)))
                   for s in range(0, len(episodes), chunk)]
        for future in as_completed(futures):
            result = future.result()
            records += result["records"]
            problems += result["problems"]
            hyper = hyper or result["world_hyperparameters"]
            features += result["features"]
    import pandas as pd
    pd.DataFrame(features).drop_duplicates("compound").to_csv(out / "compound_features.csv", index=False)
    records.sort(key=lambda r: (r["compound"], r["h1"], r["h2"], r["arm"]))
    _write(out / "records.jsonl.gz", records)
    manifest = {"completed_at_utc": datetime.now(timezone.utc).isoformat(), "environment": environment(),
                "arms": list(names), "episodes": len(episodes), "records": len(records), "problems": problems,
                "world_hyperparameters": hyper, "validator": summary["validator"],
                "freeze_sha256": F.sha256_file(FREEZE), "manifest_sha256": F.sha256_file(MANIFEST)}
    (out / "replay_manifest.json").write_bytes(json.dumps(manifest, indent=1, default=str).encode("utf-8"))
    _log("replay_completed", records=len(records), problems=len(problems))
    print("external records", len(records), "problems", len(problems))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true")
    parser.add_argument("--external", action="store_true")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    if args.dev:
        run_dev(args.workers, NAMES)
    if args.external:
        run_external(args.workers, NAMES)


if __name__ == "__main__":
    main()
