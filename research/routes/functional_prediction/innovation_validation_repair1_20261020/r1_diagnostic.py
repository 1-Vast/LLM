"""One bounded development run; does not consume any real or old evaluation input."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
LEGACY = HERE.parent / "innovation_validation_20261020"
sys.path.insert(0, str(LEGACY))
import iv_worlds as W
import r1_core as C
import r1_search as S
import r1_artifacts as A

CONFIG = {"seeds": [93021, 93022], "kinds": ["null", "lowrank", "alias", "compose"],
          "n_drugs": 12, "budget": 4, "candidate_cap_each_generation": 12,
          "arms": ["inh_kg", "rst_kg", "lat_aopt", "lat_kg"], "threads": 1,
          "label": "POST_REVIEW_ENGINEERING_DEVELOPMENT_ONLY", "maximum_seconds": 1800}


def freeze():
    files = sorted(HERE.glob("r1_*.py")) + [HERE / "PROTOCOL.md"]
    return {"config": CONFIG, "files": {p.name: A.file_hash(p) for p in files}}


def run_stream(kind, seed, out):
    stream = W.make_stream(kind, seed, n_drugs=CONFIG["n_drugs"])
    world, schedule = stream["world"], stream["schedule"]
    static, sid = world.static, f"{kind}_{seed}"
    mask = np.zeros(static.n, bool)
    for cls in np.unique(static.pair_class):
        mask[np.flatnonzero(static.pair_class == cls)[::2]] = True
    libs = {name: S.Library() for name in ("inh_kg", "rst_kg")}
    released, rows, records = list(schedule["H0"]), [], {name: [] for name in libs}
    resources = {arm: {"process_cpu_seconds": 0., "elapsed_seconds": 0.}
                 for arm in CONFIG["arms"] + ["shared_history_fit"]}

    def measured(arm, function):
        wall, cpu = time.perf_counter(), time.process_time()
        value = function()
        resources[arm]["process_cpu_seconds"] += time.process_time() - cpu
        resources[arm]["elapsed_seconds"] += time.perf_counter() - wall
        return value

    def campaigns(arm, fitted, model, cells, gen, role):
        path = out / "models" / f"{sid}_{arm}_{role}_{gen}.npz"
        digest = A.save_fits(path, fitted)
        # Anchors use exactly the cached deployed fit; no fit is performed here.
        for cell in cells:
            for contract in (["E", "T"] if role == "task" else ["E"]):
                chosen_mask = None if contract == "E" else mask
                policy = "aopt" if arm == "lat_aopt" else "kg"
                result = S.run_task(world, static, cell, model, fitted, policy, CONFIG["budget"],
                                    contract, chosen_mask, S.seed_of("repair1", sid, cell, contract))
                metric, campaign, nominated, belief, trace = result
                rows.append({"arm": arm, "gen": gen, "role": role, "cell": cell, "contract": contract,
                             "utility": metric["utility"], "oracle": metric["oracle"],
                             "base": belief.base.tolist(), "pool": (np.ones(static.n, bool) if chosen_mask is None else ~mask).tolist(),
                             "probes": list(campaign.queried), "values": list(campaign.queried.values()),
                             "nominated": list(nominated), "programs": A.gate_programs(fitted),
                             "artifact": path.relative_to(out).as_posix(), "artifact_sha256": digest})

    for generation, batch in enumerate(schedule["batches"], 1):
        model = measured("shared_history_fit", lambda: C.build_models(world, released, static))
        for arm in CONFIG["arms"]:
            def tasks():
                if arm in libs:
                    lib = libs[arm]
                    fitted = S.make_fits(lib, model, lib.deployed)
                else:
                    fitted = [C.fit_program(C.Program("N", "null"), model, {}),
                              C.fit_program(C.Program("C3", "cont", k=3), model, {})]
                campaigns(arm, fitted, model, batch, generation, "task")
            measured(arm, tasks)
        for arm, lib in libs.items():
            rec = measured(arm, lambda: S.evolve("inherit" if arm == "inh_kg" else "restart", lib,
                            world, static, f"{sid}|{arm}", generation, list(released), batch,
                            released + batch, CONFIG["budget"], False,
                            CONFIG["candidate_cap_each_generation"]))
            records[arm].append(rec)
        released += batch
        model = measured("shared_history_fit", lambda: C.build_models(world, released, static))
        for arm, lib in libs.items():
            def anchors():
                fitted = S.make_fits(lib, model, lib.deployed)
                cells = schedule["A_old"][:1] + schedule["A_new"][:1]
                campaigns(arm, fitted, model, cells, generation, "anchor")
            measured(arm, anchors)
    for arm, lib in libs.items():
        resources[arm]["candidate_evals"] = lib.n_candidate_evals
        resources[arm]["candidate_validation_replays"] = lib.n_val_replays
    output = {"sid": sid, "kind": kind, "seed": seed, "label": CONFIG["label"],
              "rows": rows, "generation_records": records, "resources": resources}
    path = out / f"{sid}.json"
    path.write_text(json.dumps(output, indent=1) + "\n", encoding="utf-8")
    return output


def summary(streams):
    output = []
    for stream in streams:
        for contract in ("E", "T"):
            values = {arm: float(np.mean([row["utility"] for row in stream["rows"]
                      if row["arm"] == arm and row["contract"] == contract
                      and row["role"] == "task" and row["gen"] >= 2])) for arm in CONFIG["arms"]}
            output.append({"sid": stream["sid"], "contract": contract, "mean_utility": values,
                           "inherit_minus_restart": values["inh_kg"] - values["rst_kg"],
                           "inherit_minus_latent_aopt": values["inh_kg"] - values["lat_aopt"],
                           "inherit_minus_latent_kg": values["inh_kg"] - values["lat_kg"]})
    return {"label": CONFIG["label"], "scientific_support": "NOT_TESTED_BY_THIS_DIAGNOSTIC",
            "resource_estimand": "EQUAL_CANDIDATE_CEILINGS_NOT_EQUAL_ACTUAL_CPU",
            "streams": output}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "DEVELOPMENT_RUN")
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("Refusing to overwrite a started development run")
    args.out.mkdir(parents=True)
    (args.out / "FREEZE.json").write_text(json.dumps(freeze(), indent=2) + "\n", encoding="utf-8")
    start, streams = time.perf_counter(), []
    try:
        with threadpool_limits(limits=1):
            for kind in CONFIG["kinds"]:
                for seed in CONFIG["seeds"]:
                    if time.perf_counter() - start > CONFIG["maximum_seconds"]:
                        raise TimeoutError("Development elapsed ceiling exceeded")
                    streams.append(run_stream(kind, seed, args.out))
                    print(f"{kind}_{seed}: complete ({time.perf_counter() - start:.1f}s)", flush=True)
        result = summary(streams)
        result["elapsed_seconds"] = time.perf_counter() - start
        (args.out / "SUMMARY.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        (args.out / "FAILED.json").write_text(json.dumps({"error": repr(exc), "completed_streams": len(streams)}) + "\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
