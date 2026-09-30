"""Replay sparse-reference acquisition and matched baselines on existing real data."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# Each worker is deliberately one BLAS thread; parallelism is across folds.
for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "outputs/sparse_value/evaluation"
sys.path.insert(0, str(ROOT / "research/sequence_audit"))
sys.path.insert(0, str(HERE))

import lincs_evaluate as LE
import lincs_prepare as LP
import policies as P
from threadpoolctl import threadpool_limits

C, E = P.C, P.E
COSTS = (0.0, .005, .01, .02, .05, .1, .2)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen():
    freeze = json.loads((HERE / "freeze.json").read_text(encoding="utf-8"))
    for name, expected in freeze["sha256"].items():
        if digest(HERE / name) != expected:
            raise RuntimeError(f"Frozen file changed: {name}")
    return freeze


def arm_table(dataset):
    from policy import make_policy

    repaired = P.arms(dataset)
    legacy = P.arms(dataset, frozen_replay=True)
    arms = {"legacy_fallback": legacy["two_step_fallback"], "fixed_fallback": repaired["two_step_fallback"],
            "two_step": repaired["two_step"], "fixed": repaired["fixed"],
            "da_unconditioned": repaired["da_unconditioned"]}
    arms.update({f"sparse_{cost:g}": make_policy(cost) for cost in COSTS})
    arms.update({"marginal_0.02": make_policy(.02, marginal_only=True),
                 "paired_only_0.02": make_policy(.02, pooling=False),
                 "permuted_0.02": make_policy(.02, permuted=True)})
    return arms


def run_fold(task):
    dataset, tier_name, fold = task
    with threadpool_limits(limits=1):
        spec = C.load_protocol()
        if dataset == "l1000":
            data = LP.load()
            tier = LP.tiers()[tier_name]
            detected = data.conditions.detected.to_numpy(bool)
            ctx = LE.context(data, tier, fold, detected, spec)
            setting = LP.setting(tier)
            group_column = "component"
        else:
            data = C.load()
            detected = C.detected_flags(data, C.detection_null(data, spec))
            ctx, _ = next(E.contexts(data, spec, detected, None, tier_names=(tier_name,), folds=(fold,)))
            setting = P.sciplex3_setting(ctx.tier)
            group_column = "skeleton"
        compounds = data.compounds.drop_duplicates("compound").set_index("compound")
        arms = arm_table(dataset)
        records = []
        for compound, truth, decoy, h1, h2 in E.episode_list(ctx, fold):
            for name, arm in arms.items():
                row = P.run_matched(name, arm, ctx, compound, truth, h1, h2, setting, qc_rule="continue")
                violations = P.audit_record(row, setting)
                if violations:
                    raise AssertionError((dataset, tier_name, fold, name, compound, violations))
                records.append({"dataset": dataset, "tier": tier_name, "fold": fold, "decoy": decoy,
                                "unit": str(compounds.loc[compound, group_column]), **row})
        return task, records, {key: value for key, value in ctx.params.items() if key != "grid"}


def main():
    freeze = frozen()
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = [(dataset, tier, fold) for dataset, tiers in (("sciplex3", ("A", "B")), ("l1000", ("LT", "T")))
             for tier in tiers for fold in range(5)]
    counts, calibration = {}, {}
    started = datetime.now(timezone.utc).isoformat()
    with ProcessPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(run_fold, task): task for task in tasks}
        for job in as_completed(jobs):
            (dataset, tier, fold), rows, params = job.result()
            name = f"{dataset}_{tier}_{fold}.jsonl"
            with (OUT / name).open("w", encoding="utf-8", newline="\n") as stream:
                for row in rows:
                    stream.write(json.dumps(C.clean(row), allow_nan=False) + "\n")
            counts[name] = len(rows)
            calibration[f"{dataset}|{tier}|{fold}"] = C.clean(params)
            print(f"{name}: {len(rows)} records", flush=True)
    sources = [HERE / name for name in ("evaluate.py", "policy.py", "model.py", "protocol.json")]
    sources += [Path(P.__file__), Path(C.__file__), Path(E.__file__), Path(LE.__file__), Path(LP.__file__)]
    prepared = [path for folder in (C.PREPARED, C.FROZEN, LP.OUT)
                for path in folder.iterdir() if path.is_file()]
    manifest = {"freeze": freeze, "started_at_utc": started, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "exploratory reuse: SciPlex3 and L1000 decision results informed this design; not independent validation",
                "files": counts, "records": sum(counts.values()), "cost_per_measurement_grid": COSTS,
                "arms": list(arm_table("l1000")), "validator_calibration": calibration,
                "source_sha256": {str(path.relative_to(ROOT)): digest(path) for path in sources},
                "prepared_sha256": {str(path.relative_to(ROOT)): digest(path) for path in prepared},
                "environment": {"python": sys.version, "executable": sys.executable, "workers": 4, "blas_threads_per_worker": 1}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Saved {manifest['records']} records", flush=True)


if __name__ == "__main__":
    main()
