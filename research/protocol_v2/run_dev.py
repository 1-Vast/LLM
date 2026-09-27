"""The protocol-v2 development screen: every arm through the truth-free runner on the 20 development tasks.

File summary
- Path: research/protocol_v2/run_dev.py
- Purpose: run the arms pre-registered in `protocol.json` (`development_screen`) on the
  registered development episodes, with the protocol-v2 contracts: the public view, availability
  menus, measurement states, and truth joined only by the scoring pass.
- Core points:
  - Execution writes truth-free traces (`traces/`). The scoring pass then joins each episode's
    truth (`scored/`), and fails closed on a missing one.
  - Evaluation-side outcome tables (`tables/`) hold every available condition's registered
    reading per episode, for exact counterfactual analyses (headroom conditional on a first
    action). No arm ever receives them.
  - `development_record` writes the run's provenance (commit, dirty flag, digests, environment,
    command, seed). On a dirty tree it is marked unregistered, which this run is.
  - The replay check compares arms shared with belief-planning-1 against its registered records
    at the decision level; mismatches are reported with whether each compound had unavailable
    planned conditions.
- Run: python -m research.protocol_v2.run_dev [--workers N] [--tasks sciplex3:A:1,...] [--out DIR]
- Interfaces: `ARMS`, `run_task`, `main`
- Depends on: contracts.py, runner.py, safe.py, registry.py, research/belief_planning, research/external_validation
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(variable, "1")

from research.belief_planning import arms as BA  # noqa: E402
from research.external_validation import arms as A  # noqa: E402

from . import contracts as K  # noqa: E402
from . import registry as G  # noqa: E402
from . import runner as RN  # noqa: E402
from .safe import max_train_similarity, safe_arm  # noqa: E402

T, P, C, E = K.T, K.T.P, K.T.C, K.T.E
HERE = Path(__file__).resolve().parent
ROOT = G.ROOT
PROTOCOL = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
STOP = bool(PROTOCOL["calibration"]["stop_gate_result"])
EPS = float(PROTOCOL["calibration"]["belief_contamination_eps"])
OUT = ROOT / "outputs" / "protocol_v2_20260927" / "dev"
REGISTERED = ROOT / "outputs" / "belief_planning_20260927" / "registered" / "dev"
SEED = 20260927

ARMS = {
    "fixed": ("primary_comparator", lambda real: A.fixed),
    "random_legal": ("lower_bound", lambda real: A.random_legal),
    "myopic_edv": ("non_agent_model_baseline", lambda real: A.myopic_edv()),
    "belief": ("current_planner", lambda real: BA.belief_arm()),
    "anchored": ("current_anchored_planner", lambda real: BA.belief_arm(anchor=True)),
    "safe": ("primary_candidate", lambda real: safe_arm(gate_novelty=True, allow_model_stop=STOP)),
    "safe_class": ("sensitivity", lambda real: safe_arm(gate_novelty=False, allow_model_stop=STOP)),
    "belief_robust": ("robustness", lambda real: BA.belief_arm(contamination=EPS)),
    "oracle": ("bound", lambda real: A.make_oracle(real, E.execute)),
}
CODE = ["research/protocol_v2/__init__.py", "research/protocol_v2/contracts.py", "research/protocol_v2/runner.py",
        "research/protocol_v2/safe.py", "research/protocol_v2/registry.py", "research/protocol_v2/run_dev.py",
        "research/protocol_v2/records.py", "research/protocol_v2/headroom.py", "research/protocol_v2/calibration.py",
        "research/protocol_v2/attribution.py", "research/belief_planning/arms.py", "research/belief_planning/world.py",
        "research/belief_planning/tasks.py", "research/external_validation/arms.py",
        "research/external_validation/firewall.py", "research/sequence_audit/policies.py",
        "research/dynamic_world_model/common.py", "research/dynamic_world_model/episodes.py",
        "src/maestro/planning.py", "src/maestro/acquisition.py", "src/maestro/outcome.py"]
DATA = ["outputs/dynamic_world_model_20260926/prepared/conditions.csv",
        "outputs/dynamic_world_model_20260926/prepared/shifts.npz",
        "outputs/sequence_audit_20260926/l1000/prepared/compounds.csv",
        "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv",
        "outputs/sequence_audit_20260926/l1000/prepared/shifts.npz",
        "outputs/sequence_audit_20260926/l1000/prepared/tiers.json"]


def _write(path: Path, rows) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, default=_default) + "\n")
    return G.sha256_file(path)


def _default(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, (set, frozenset, tuple)):
        return sorted(value) if isinstance(value, (set, frozenset)) else list(value)
    return str(value)


def run_task(task, names):
    from threadpoolctl import threadpool_limits
    dataset, tier, fold = task
    started = time.time()
    with threadpool_limits(limits=1):
        data, real_ctx, setting = T.load(dataset, tier, fold)
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        heldout = set(comp.index[comp.fold == fold])
        episodes = E.episode_list(real_ctx, fold)
        training = tuple(c for c in real_ctx.tier.compounds if comp.fold.get(c) != fold)
        view = K.public_view(real_ctx, heldout, training_compounds=training)
        problems = K.public_view_problems(view, heldout)
        units = T.units(dataset)
        unit_of = units[T.UNIT[dataset]].astype(str).to_dict()
        scaffold_of = {c: (s if isinstance(s, str) and s else None) for c, s in units["murcko_scaffold"].items()}
        world = BA.world_for(view, "on", "true")
        arms = {name: ARMS[name][1](real_ctx) for name in names}
        traces, tables = [], []
        for compound, _truth_not_passed, decoy, h1, h2 in episodes:
            available = view.data.availability[compound]
            local = RN.local_setting(setting, available)
            meta = {"dataset": dataset, "tier": tier, "fold": fold, "decoy": decoy, "unit": unit_of.get(compound, compound),
                    "scaffold": scaffold_of.get(compound), "max_train_tanimoto": max_train_similarity(view, world, compound)}
            for name, arm in arms.items():
                trace = RN.run_episode(name, arm, view, real_ctx, compound, h1, h2, setting)
                problems += [f"{name}:{compound}:{p}" for p in RN.audit_trace(trace, local)]
                trace.update(meta, role=ARMS[name][0], reads_hidden_outcomes=name == "oracle")
                traces.append(trace)
            table = {}
            for key in local.keys:
                result = E.execute(real_ctx, compound, key, h1, h2)
                table[C.action_id(key)] = {"state": K.measurement_state(result).value, "outcome": result["outcome"]}
            tables.append({**meta, "compound": compound, "h1": h1, "h2": h2, "outcomes": table,
                           "unavailable_conditions": len(setting.keys) - len(local.keys)})
        # scoring pass: the truth is joined only now, after every arm has run
        truth_of = {(c, a, b): t for c, t, _, a, b in episodes}
        scored = [{**trace, "score": K.score(trace, truth_of[(trace["compound"], trace["h1"], trace["h2"])])}
                  for trace in traces]
        for row in tables:
            row["truth"] = truth_of[(row["compound"], row["h1"], row["h2"])]
    return {"task": task, "traces": traces, "scored": scored, "tables": tables, "problems": problems,
            "episodes": len(episodes), "seconds": time.time() - started,
            "world_hyperparameters": view.extra.get("world_hyperparameters")}


def replay_check(name: str, scored: list, tables: list) -> dict:
    """Decision-level comparison with belief-planning-1 for arms both runs share."""
    path = REGISTERED / f"{name}.jsonl.gz"
    if not path.is_file():
        return {"status": "registered_records_missing"}
    shared = set(ARMS) & {"fixed", "random_legal", "myopic_edv", "belief", "anchored", "oracle"}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        old = [r for r in (json.loads(line) for line in fh) if r["arm"] in shared]
    new = [{**{k: v for k, v in r.items() if k != "score"}, "final": r["score"]["final"]} for r in scored
           if r["arm"] in shared]
    incomplete = {t["compound"] for t in tables if t["unavailable_conditions"]}
    report = G.compare_decisions([{k: r.get(k) for k in ("arm", "compound", "h1", "h2", "stop", "final", "measurements",
                                                          "steps")} for r in old],
                                 [{k: r.get(k) for k in ("arm", "compound", "h1", "h2", "stop", "final", "measurements",
                                                          "steps")} for r in new])
    # the registered steps carry no `state`; compare on the fields both records have
    report["problems"] = [p for p in report["problems"] if not p["problem"].endswith("_state_differs")]
    report["problem_count"] = len(report["problems"])
    report["identical_decisions"] = not report["problems"]
    report["mismatches_on_incomplete_compounds"] = sum(p["episode"][1] in incomplete for p in report["problems"])
    report["mismatches_elsewhere"] = report["problem_count"] - report["mismatches_on_incomplete_compounds"]
    report["problems"] = [{"episode": list(p["episode"]), "problem": p["problem"]} for p in report["problems"][:20]]
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--tasks", default="")
    parser.add_argument("--arms", default=",".join(ARMS))
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    out = Path(args.out)
    tasks = [(d, t, int(f)) for d, t, f in (x.split(":") for x in args.tasks.split(",") if x)] or list(T.TASKS)
    names = [n for n in args.arms.split(",") if n]
    record = G.development_record(out / "run_record.json", "protocol-v2-dev-screen",
                                  protocol_files=["research/protocol_v2/protocol.json"], code_files=CODE,
                                  data_files=DATA, command=[sys.executable, "-m", "research.protocol_v2.run_dev",
                                                            *sys.argv[1:]], seed=SEED)
    print("record", record["status"], "commit", record["git_commit"], "dirty", record["git_dirty"], flush=True)
    manifest = {"run_record_sha256": record["record_sha256"], "arms": names, "tasks": {}, "problems": {},
                "replay_check": {}, "outputs_sha256": {}, "world_hyperparameters": {}}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_task, t, names): t for t in tasks}
        for future in as_completed(futures):
            result = future.result()
            d, t, f = result["task"]
            name = f"{d}_{t}_{f}"
            for kind in ("traces", "scored", "tables"):
                manifest["outputs_sha256"][f"{kind}/{name}.jsonl.gz"] = _write(out / kind / f"{name}.jsonl.gz",
                                                                              result[kind])
            manifest["tasks"][name] = {"episodes": result["episodes"], "records": len(result["scored"]),
                                       "seconds": round(result["seconds"], 1)}
            manifest["problems"][name] = result["problems"]
            manifest["world_hyperparameters"][name] = result["world_hyperparameters"]
            manifest["replay_check"][name] = replay_check(name, result["scored"], result["tables"])
            rc = manifest["replay_check"][name]
            print(name, len(result["scored"]), "problems", len(result["problems"]), "replay mismatches",
                  rc.get("problem_count"), "(incomplete compounds", rc.get("mismatches_on_incomplete_compounds"), ")",
                  f"{result['seconds']:.0f}s", flush=True)
    (out / "manifest.json").write_bytes(json.dumps(manifest, indent=1, sort_keys=True).encode("utf-8") + b"\n")


if __name__ == "__main__":
    main()
