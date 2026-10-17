"""Development arms: build every program library from SOURCE data only, with full trajectories.

File summary
- Path: research/program_revision_20261017/develop.py
- Purpose: run the registered library-construction arms on the development bench (I2, fixed
  A-optimal probe design, 10 source projects, support -> query) and write LIBRARIES.json plus
  one JSONL trajectory per arm. Reads only SOURCE drugs x SOURCE lines (`Domain(open_future=False)`).
- Arms (PROTOCOL.md section 4):
  - seed_fixed: the pre-specified seed library, never edited;
  - stepwise: conventional forward selection over the same language on all query outcomes;
  - maestro_enum: the MAESTRO loop (per-project counterexample diagnosis, committed predictions,
    distinguishing experiment, frozen acceptance) with the enumerative proposer;
  - maestro_llm: the same loop with the deepseek-flash proposer (same candidates per step);
  - maestro_enum_empty / maestro_llm_empty: the same loops starting from an empty library;
  - maestro_enum_joint / maestro_llm_joint: the same loops where an edit may also change the
    measurement program (swap a design probe and add the program that reads it), i.e. response
    abstraction and measurement design learned jointly instead of response-then-measurement.
- Interfaces: ``python -B develop.py --arms seed_fixed,stepwise,...`` (refuses unless FREEZE.json
  exists and its digests match, so every arm runs under the frozen protocol).
"""
from __future__ import annotations

import argparse
import json
import time

from common import CACHE, HERE, write_json
from engine import STRONG, Domain, fixed_probe_design
from freeze import check_freeze
from revise import Bench, EnumerativeProposer, ProgramLibrary, run_revision, seed_library, stepwise_search

ROUNDS = 2
CANDIDATES_PER_STEP = 6
BUDGET = 120


def library_record(lib, acc, seconds, extra=None, design=None):
    rec = {"programs": [{"scope": p.scope, "state": p.state, "origin": p.origin, "key": p.key} for p in lib.programs],
           "design": list(design),
           "digest": lib.digest(), "complexity": lib.complexity(), "accounting": acc, "seconds": round(seconds, 1)}
    rec.update(extra or {})
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="unfrozen code check: 1 round, budget 12, output in tmp/")
    ap.add_argument("--arms", default="seed_fixed,stepwise,maestro_enum,maestro_llm,maestro_enum_empty,"
                                      "maestro_llm_empty,maestro_enum_joint,maestro_llm_joint")
    args = ap.parse_args()
    global ROUNDS, BUDGET
    if args.smoke:
        ROUNDS, BUDGET = 1, 12
    else:
        check_freeze()
    dom = Domain(open_future=False)
    probes = fixed_probe_design(dom, 8)
    t = time.time()
    bench = Bench(dom, "I2", probes)
    build = time.time() - t
    path = (CACHE / "LIBRARIES_smoke.json") if args.smoke else (HERE / "LIBRARIES.json")
    out = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    out["_bench"] = {"info": "I2", "probes": probes, "strong": STRONG, "projects": bench.projects,
                     "rounds": ROUNDS, "candidates_per_step": CANDIDATES_PER_STEP, "budget": BUDGET,
                     "build_seconds": round(build, 1)}
    tdir = (CACHE / "smoke_trajectories") if args.smoke else (HERE / "trajectories")
    tdir.mkdir(exist_ok=True)
    seed, dropped = seed_library(bench)
    for arm in args.arms.split(","):
        bench.revealed = set()
        t = time.time()
        with (tdir / f"{arm}.jsonl").open("w", encoding="utf-8", newline="\n") as log:
            if arm == "seed_fixed":
                lib, acc, extra = seed, {"evaluated": 0, "distinguishing_wells": 0}, {"dropped": dropped}
            elif arm == "stepwise":
                lib, _, acc = stepwise_search(bench, seed, n_screen=100, budget=BUDGET, log=log)
                extra = {}
            else:
                start = ProgramLibrary() if arm.endswith("_empty") else seed
                joint = arm.endswith("_joint")
                if "llm" in arm:
                    from llm_proposer import LLMProposer
                    prop = LLMProposer(CACHE / "llm_ledger.jsonl", n=CANDIDATES_PER_STEP, joint=joint)
                else:
                    prop = EnumerativeProposer(CANDIDATES_PER_STEP, joint=joint)
                lib, traj, acc = run_revision(bench, start, prop, rounds=ROUNDS, project_mode=True, log=log,
                                              budget_candidates=BUDGET)
                extra = {"llm_spend": prop.spend()} if "llm" in arm else {}
                refused = sum(1 for e in traj for c in e["candidates"] if c["decision"] == "refused")
                extra["refused"] = refused
                extra["proposed"] = sum(len(e["candidates"]) for e in traj)
        out[arm] = library_record(lib, acc, time.time() - t, extra, acc.get("design", probes))
        write_json(path, out)
        print(arm, json.dumps(out[arm])[:800], flush=True)


if __name__ == "__main__":
    main()
