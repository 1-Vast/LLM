"""E-DATA1: task, menu and unit qualification of the MoA proxy task under protocol v2.1.

File summary
- Path: research/protocol_v2/e_data1.py
- Purpose: answer, before any planner comparison, whether a development task has enough headroom
  and independent units for planner work once the legal menu comes from the study design and the
  hypothesis pools from training compounds (`protocol_v2_1.json`, experiment E-DATA1; thresholds
  committed in `research/gated_plan/registry.json` at c3d2345).
- Core points:
  - `run` executes the arms of `protocol_v2_1.json` (fixed, random_legal, myopic_edv, belief, safe,
    oracle) through the truth-free runner with `design_menu=True`, and records, per episode, every
    planned tier condition's lifecycle and reading (evaluation side only; no arm sees it). Scores are
    joined after execution, as in protocol v2.
  - `analyse` derives two policies from the exact outcome tables: `fixed_star`, the cross-fitted
    best fixed sequence (chosen on the other four folds, applied to the held-out fold), and
    `table_oracle`, which must reproduce the oracle arm's terminal decisions. It reports headroom
    (oracle minus fixed_star, primary; oracle minus fixed), unit mean first and episode mean beside
    it, decision-changeable units, units required for +0.02 from the belief arm's paired SE, menu
    expansion ceilings on identical episodes, and the QC-failed steps the design menu creates.
  - Gate verdicts use only the registered thresholds; nothing is tuned on these results.
- Run: python -m research.protocol_v2.e_data1 run [--workers N] [--tasks sciplex3:A:0,...]
       python -m research.protocol_v2.e_data1 analyse
- Interfaces: `ARMS`, `run_task`, `simulate_sequence`, `legal_sequences`, `fixed_star`, `analyse`, `main`
- Depends on: tasks_v21.py, design.py, contracts.py, runner.py, headroom.py, registry.py, run_dev.py
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(variable, "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import contracts as K  # noqa: E402
from . import headroom as H  # noqa: E402
from . import registry as G  # noqa: E402
from . import runner as RN  # noqa: E402

T, P, C, E = K.T, K.T.P, K.T.C, K.T.E
HERE = Path(__file__).resolve().parent
ROOT = G.ROOT
OUT = ROOT / "outputs" / "protocol_v2_1_20260927" / "e_data1"
PROTOCOL = json.loads((HERE / "protocol_v2_1.json").read_text(encoding="utf-8"))
VERSION = PROTOCOL["version"]
SEED = 20260927
ARMS = ("fixed", "random_legal", "myopic_edv", "belief", "safe", "oracle")
MPIE = 0.02
CODE = ["research/protocol_v2/e_data1.py", "research/protocol_v2/tasks_v21.py", "research/protocol_v2/design.py",
        "research/protocol_v2/contracts.py", "research/protocol_v2/runner.py", "research/protocol_v2/headroom.py",
        "research/protocol_v2/safe.py", "research/protocol_v2/run_dev.py", "research/protocol_v2/registry.py",
        "research/belief_planning/arms.py", "research/belief_planning/world.py", "research/belief_planning/planner.py",
        "research/belief_planning/tasks.py", "research/external_validation/arms.py",
        "research/sequence_audit/policies.py", "research/dynamic_world_model/common.py",
        "research/dynamic_world_model/episodes.py", "src/maestro/outcome.py", "src/maestro/acquisition.py"]
DATA = ["outputs/protocol_v2_1_20260927/design/sciplex3_design.csv",
        "outputs/protocol_v2_1_20260927/design/l1000_design.csv",
        "outputs/dynamic_world_model_20260926/prepared/conditions.csv",
        "outputs/dynamic_world_model_20260926/prepared/shifts.npz",
        "outputs/sequence_audit_20260926/l1000/prepared/compounds.csv",
        "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv",
        "outputs/sequence_audit_20260926/l1000/prepared/shifts.npz"]


# ------------------------------------------------------------------------------ execution
def _arms(real_ctx):
    from research.belief_planning import arms as BA
    from research.external_validation import arms as A

    from .run_dev import EPS, STOP  # registered protocol-v2 calibration constants
    from .safe import safe_arm
    del EPS
    return {"fixed": A.fixed, "random_legal": A.random_legal, "myopic_edv": A.myopic_edv(),
            "belief": BA.belief_arm(), "safe": safe_arm(gate_novelty=True, allow_model_stop=STOP),
            "oracle": A.make_oracle(real_ctx, E.execute)}


def run_task(task, names=ARMS):
    from threadpoolctl import threadpool_limits

    from research.belief_planning import arms as BA

    from . import tasks_v21 as V
    from .safe import max_train_similarity
    dataset, tier, fold = task
    started = time.time()
    with threadpool_limits(limits=1):
        data, real_ctx, setting, design = V.load(dataset, tier, fold)
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        heldout = set(comp.index[comp.fold == fold])
        episodes = V.episode_list(real_ctx, fold)
        training = V.training_compounds(real_ctx, fold)
        view = K.public_view(real_ctx, heldout, training_compounds=training, design=design)
        problems = K.public_view_problems(view, heldout)
        units = T.units(dataset)
        unit_of = units[T.UNIT[dataset]].astype(str).to_dict()
        scaffold_of = {c: (s if isinstance(s, str) and s else None) for c, s in units["murcko_scaffold"].items()}
        world = BA.world_for(view, "on", "true")
        arms = {name: arm for name, arm in _arms(real_ctx).items() if name in names}
        traces, tables = [], []
        for compound, _truth_not_passed, decoy, h1, h2 in episodes:
            available = view.data.availability[compound]
            local = RN.local_setting(setting, available)
            meta = {"dataset": dataset, "tier": tier, "fold": fold, "decoy": decoy, "unit": unit_of.get(compound, compound),
                    "scaffold": scaffold_of.get(compound), "max_train_tanimoto": max_train_similarity(view, world, compound),
                    "protocol_version": VERSION}
            for name, arm in arms.items():
                trace = RN.run_episode(name, arm, view, real_ctx, compound, h1, h2, setting, design_menu=True)
                problems += [f"{name}:{compound}:{p}" for p in RN.audit_trace(trace, local)]
                trace.update(meta, reads_hidden_outcomes=name == "oracle")
                traces.append(trace)
            table = {}
            for key in local.keys:
                result = E.execute(real_ctx, compound, key, h1, h2)
                lifecycle = K.lifecycle_state(True, result)
                table[C.action_id(key)] = {"key": list(key), "lifecycle": lifecycle.value, "readout": K.readout(result),
                                           "outcome": result["outcome"] if lifecycle is K.Lifecycle.MEASURED_VALID
                                           else "quality_failed"}
            tables.append({**meta, "compound": compound, "h1": h1, "h2": h2, "outcomes": table,
                           "unplanned_tier_conditions": len(setting.keys) - len(local.keys)})
        truth_of = {(c, a, b): t for c, t, _, a, b in episodes}
        scored = [{**trace, "score": K.score(trace, truth_of[(trace["compound"], trace["h1"], trace["h2"])])}
                  for trace in traces]
        for row in tables:
            row["truth"] = truth_of[(row["compound"], row["h1"], row["h2"])]
    return {"task": task, "scored": scored, "tables": tables, "problems": problems, "episodes": len(episodes),
            "pool": list(real_ctx.tier.pool), "eligible": len(real_ctx.tier.compounds),
            "setting": {"keys": [list(k) for k in setting.keys], "fixed_order": [list(k) for k in setting.fixed_order],
                        "max_measurements": setting.max_measurements, "budget_days": setting.budget_days,
                        "days": {C.action_id(k): setting.days(k) for k in setting.keys}},
            "seconds": time.time() - started}


def _write(path: Path, rows) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, default=_default) + "\n")
    return G.sha256_file(path)


def _default(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    if isinstance(value, tuple):
        return list(value)
    return str(value)


def run(out: Path, tasks, names, workers: int) -> dict:
    record = G.development_record(out / "run_record.json", "e-data1-protocol-v2.1",
                                  protocol_files=["research/protocol_v2/protocol_v2_1.json",
                                                  "research/gated_plan/registry.json"],
                                  code_files=CODE, data_files=DATA,
                                  command=[sys.executable, "-m", "research.protocol_v2.e_data1", *sys.argv[1:]],
                                  seed=SEED, protocol_version=VERSION)
    print("record", record["status"], "commit", record["git_commit"], "dirty", record["git_dirty"], flush=True)
    manifest = {"run_record_sha256": record["record_sha256"], "arms": list(names), "tasks": {}, "problems": {},
                "outputs_sha256": {}, "settings": {}}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_task, t, names): t for t in tasks}
        for future in as_completed(futures):
            result = future.result()
            d, t, f = result["task"]
            name = f"{d}_{t}_{f}"
            for kind in ("scored", "tables"):
                manifest["outputs_sha256"][f"{kind}/{name}.jsonl.gz"] = _write(out / kind / f"{name}.jsonl.gz",
                                                                              result[kind])
            manifest["tasks"][name] = {"episodes": result["episodes"], "records": len(result["scored"]),
                                       "pool": result["pool"], "eligible_compounds": result["eligible"],
                                       "seconds": round(result["seconds"], 1)}
            manifest["settings"][f"{d}_{t}"] = result["setting"]
            manifest["problems"][name] = result["problems"]
            print(name, result["episodes"], "episodes", len(result["problems"]), "problems",
                  f"{result['seconds']:.0f}s", flush=True)
    (out / "manifest.json").write_bytes(json.dumps(manifest, indent=1, sort_keys=True).encode("utf-8") + b"\n")
    return manifest


# ------------------------------------------------------------------------------ table policies
def legal_sequences(keys, days: dict, budget: float, max_measurements: int) -> list[tuple]:
    """Every ordered sequence of at most `max_measurements` distinct keys in time order within the day budget."""
    out = []
    for n in range(1, max_measurements + 1):
        for seq in itertools.permutations(keys, n):
            if any(seq[i + 1][1] < seq[i][1] for i in range(n - 1)):
                continue
            if sum(days[C.action_id(k)] for k in seq) > budget + 1e-9:
                continue
            out.append(tuple(seq))
    return out


def simulate_sequence(row: dict, sequence) -> dict:
    """The terminal decision of following `sequence` on one episode's exact outcome table.

    Stops at the first elimination, as the runner does; a QC failure or a non-eliminating reading
    continues to the next key; a key the design did not plan for the compound is skipped.
    """
    h1, h2, truth = row["h1"], row["h2"], row["truth"]
    steps, eliminated = 0, None
    for key in sequence:
        entry = row["outcomes"].get(C.action_id(key))
        if entry is None:
            continue
        steps += 1
        outcome = entry["outcome"]
        if entry["lifecycle"] == "measured_valid" and outcome in ("eliminate_a", "eliminate_b"):
            eliminated = h1 if outcome == "eliminate_a" else h2
            break
    if not steps:
        final = "deferred"
    elif eliminated is None:
        final = "undetermined"
    else:
        final = "correct" if eliminated != truth else "wrong"
    return {"final": final, "measurements": steps}


def _frame_from_tables(tables: list, arm: str, chooser) -> pd.DataFrame:
    rows = []
    for row in tables:
        sequence = chooser(row)
        r = simulate_sequence(row, sequence)
        rows.append({"arm": arm, "dataset": row["dataset"], "tier": str(row["tier"]), "fold": row["fold"],
                     "compound": row["compound"], "h1": row["h1"], "h2": row["h2"], "unit": str(row["unit"]),
                     "final": r["final"], "measurements": r["measurements"], "sequence": "|".join(C.action_id(k) for k in sequence)})
    return _endpoints(pd.DataFrame(rows))


def _endpoints(frame: pd.DataFrame) -> pd.DataFrame:
    frame["correct"] = (frame.final == "correct").astype(float)
    frame["wrong"] = frame.final.isin(("wrong", "exhausted")).astype(float)
    frame["decided"] = frame.final.isin(("correct", "wrong", "exhausted")).astype(float)
    frame["deferred"] = (frame.final == "deferred").astype(float)
    frame["utility"] = frame.correct - 2.0 * frame.wrong
    frame["episode"] = (frame.tier.astype(str) + "|" + frame.fold.astype(str) + "|" + frame.compound + "|"
                        + frame.h1 + "|" + frame.h2)
    return frame


def _unit_mean(frame: pd.DataFrame, metric: str) -> float:
    return float(frame.groupby("unit")[metric].mean().mean()) if len(frame) else float("nan")


def fixed_star(tables: list, sequences: list) -> dict:
    """Cross-fitted best fixed sequence per held-out fold: chosen on the other folds' exact tables."""
    folds = sorted({row["fold"] for row in tables})
    choice = {}
    for fold in folds:
        train = [row for row in tables if row["fold"] != fold]
        best = None
        for seq in sequences:
            frame = _frame_from_tables(train, "candidate", lambda row, s=seq: s)
            score = (_unit_mean(frame, "correct"), -len(seq), tuple(C.action_id(k) for k in seq))
            if best is None or (score[0], score[1]) > (best[0][0], best[0][1]) or \
                    ((score[0], score[1]) == (best[0][0], best[0][1]) and score[2] < best[0][2]):
                best = (score, seq)
        choice[fold] = best[1]
    return choice


def table_oracle(row: dict, sequences: list, days: dict) -> tuple:
    """The oracle arm's rule on the exact table: best utility, then fewest days, then fewest measurements."""
    value = {"correct": 1, "undetermined": 0, "deferred": 0, "wrong": -2}
    best = ((0, 0.0, 0), ())
    for seq in sequences:
        r = simulate_sequence(row, seq)
        if r["measurements"] != len(seq):
            continue
        spent = sum(days[C.action_id(k)] for k in seq)
        candidate = (value[r["final"]], -spent, -len(seq))
        if candidate > best[0]:
            best = (candidate, seq)
    return best[1]


# ------------------------------------------------------------------------------ analysis
def _load_scored(out: Path) -> pd.DataFrame:
    rows = []
    for path in sorted((out / "scored").glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                steps = r["steps"]
                rows.append({"arm": r["arm"], "dataset": r["dataset"], "tier": str(r["tier"]), "fold": r["fold"],
                             "compound": r["compound"], "h1": r["h1"], "h2": r["h2"], "unit": str(r["unit"]),
                             "final": r["score"]["final"], "measurements": r["measurements"], "days": r["days"],
                             "qc_failed_steps": sum(s.get("lifecycle") == "measured_qc_failed" for s in steps),
                             "stop": r["stop"], "sequence": "|".join(s["action"] for s in steps)})
    return _endpoints(pd.DataFrame(rows))


def _load_tables(out: Path) -> list:
    rows = []
    for path in sorted((out / "tables").glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            rows.extend(json.loads(line) for line in fh)
    return rows


def _rate(frame, metric):
    values = frame.groupby("unit")[metric].mean()
    return {"unit_mean": float(values.mean()), "episode_mean": float(frame[metric].mean())}


def _power(frame: pd.DataFrame, candidate: str) -> dict:
    diff = H.unit_paired(frame, candidate, "fixed", "correct")
    se = (diff["ci"][1] - diff["ci"][0]) / (2 * 1.959964)
    n = diff["units"]
    required = int(np.ceil(n * (H.Z_POWER * se / MPIE) ** 2)) if se > 0 else None
    return {"candidate": candidate, "difference": diff["difference"], "ci": diff["ci"], "se": se, "units": n,
            "mde_at_current_n": H.Z_POWER * se, "units_required_for_mpie": required,
            "departure_rate": None}


def analyse(out: Path = OUT) -> dict:
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    scored = _load_scored(out)
    tables = _load_tables(out)
    thresholds = PROTOCOL["experiments"]["E-DATA1"]["thresholds"]
    results = {"protocol_version": VERSION, "thresholds": thresholds, "tiers": {}}
    for (dataset, tier), group in scored.groupby(["dataset", "tier"]):
        name = f"{dataset}:{tier}"
        setting = manifest["settings"][f"{dataset}_{tier}"]
        keys = [tuple(k) for k in setting["keys"]]
        days = setting["days"]
        sequences = legal_sequences(keys, days, setting["budget_days"], setting["max_measurements"])
        rows = [r for r in tables if r["dataset"] == dataset and str(r["tier"]) == tier]
        choice = fixed_star(rows, sequences)
        star = _frame_from_tables(rows, "fixed_star", lambda row: choice[row["fold"]])
        oracle_seq = {(r["compound"], r["h1"], r["h2"], r["fold"]): table_oracle(r, sequences, days) for r in rows}
        t_oracle = _frame_from_tables(rows, "table_oracle", lambda row: oracle_seq[(row["compound"], row["h1"], row["h2"], row["fold"])])
        frame = pd.concat([group, star, t_oracle], ignore_index=True)
        oracle_arm = group[group.arm == "oracle"].set_index("episode").final
        table_final = t_oracle.set_index("episode").final.reindex(oracle_arm.index)
        entry = {"units": int(group.unit.nunique()), "episodes": int((group.arm == "fixed").sum()),
                 "compounds": int(group.compound.nunique()), "pool_sizes": sorted({len(manifest["tasks"][f"{dataset}_{tier}_{f}"]["pool"]) for f in range(5)}),
                 "table_oracle_matches_oracle_arm": bool((table_final == oracle_arm).all()),
                 "fixed_star_choice": {str(f): [C.action_id(k) for k in s] for f, s in choice.items()},
                 "fixed_order": ["|".join(C.action_id(tuple(k)) for k in setting["fixed_order"])],
                 "arms": {}}
        for arm in sorted(set(frame.arm)):
            sub = frame[frame.arm == arm]
            entry["arms"][arm] = {m: _rate(sub, m) for m in ("correct", "wrong", "deferred", "decided", "measurements")}
            if "qc_failed_steps" in sub.columns and sub.qc_failed_steps.notna().any():
                entry["arms"][arm]["qc_failed_steps"] = int(sub.qc_failed_steps.fillna(0).sum())
        entry["headroom_vs_fixed_star"] = H.unit_paired(frame, "oracle", "fixed_star", "correct")
        entry["headroom_vs_fixed"] = H.unit_paired(frame, "oracle", "fixed", "correct")
        entry["headroom_utility_vs_fixed_star"] = H.unit_paired(frame, "oracle", "fixed_star", "utility")
        entry["fixed_star_vs_fixed"] = {m: H.unit_paired(frame, "fixed_star", "fixed", m)
                                        for m in ("correct", "wrong", "measurements")}
        fixed = frame[frame.arm == "fixed"].set_index("episode")
        oracle = frame[frame.arm == "oracle"].set_index("episode").reindex(fixed.index)
        entry["decision_changeable_unit_share"] = float((oracle.final != fixed.final).groupby(fixed.unit).any().mean())
        entry["power"] = {arm: _power(frame, arm) for arm in ("belief", "safe", "myopic_edv")}
        belief = frame[frame.arm == "belief"].set_index("episode").reindex(fixed.index)
        entry["belief_departure_rate"] = float((belief.sequence != fixed.sequence).mean())
        h = entry["headroom_vs_fixed_star"]
        eligible = h["difference"] >= 0.04 and h["ci"][0] >= 0.02
        required = entry["power"]["belief"]["units_required_for_mpie"]
        powered = required is not None and required <= entry["units"]
        entry["gate"] = {"primary_eligible": bool(eligible), "powered": bool(powered),
                         "status": "eligible_and_powered" if eligible and powered else
                                   "eligible_underpowered" if eligible else "ineligible_low_headroom"}
        # menu expansion on identical episodes
        if (dataset, tier) in (("sciplex3", "A"), ("l1000", "LT")):
            base_keys = [k for k in keys if (k[1] == 24.0 if dataset == "sciplex3" else k[0] == "A549")]
            base_seq = legal_sequences(base_keys, days, setting["budget_days"], setting["max_measurements"])
            base_oracle = _frame_from_tables(rows, "oracle_base_menu", lambda row: table_oracle(row, base_seq, days))
            base_choice = fixed_star(rows, base_seq)
            base_star = _frame_from_tables(rows, "fixed_star_base_menu", lambda row: base_choice[row["fold"]])
            both = pd.concat([t_oracle, base_oracle, star, base_star], ignore_index=True)
            entry["menu_expansion"] = {
                "base_menu": [C.action_id(k) for k in base_keys], "expanded_menu": [C.action_id(k) for k in keys],
                "delta_oracle_ceiling": H.unit_paired(both, "table_oracle", "oracle_base_menu", "correct"),
                "fixed_star_expanded_minus_base": {m: H.unit_paired(both, "fixed_star", "fixed_star_base_menu", m)
                                                   for m in ("correct", "wrong", "measurements")}}
            d = entry["menu_expansion"]["delta_oracle_ceiling"]
            f = entry["menu_expansion"]["fixed_star_expanded_minus_base"]
            entry["menu_expansion"]["qualifies"] = bool(
                (d["difference"] >= 0.02 and d["ci"][0] > 0) or
                (f["measurements"]["difference"] <= -0.1 and f["correct"]["difference"] >= -0.01
                 and f["wrong"]["difference"] <= 0.005))
        results["tiers"][name] = entry
    results["any_task_qualifies"] = any(t["gate"]["primary_eligible"] and t["gate"]["powered"]
                                        for t in results["tiers"].values())
    results["any_expansion_qualifies"] = any(t.get("menu_expansion", {}).get("qualifies", False)
                                             for t in results["tiers"].values())
    results["verdict"] = ("PASS" if results["any_task_qualifies"] else
                          "FAIL" if not any(t["gate"]["primary_eligible"] for t in results["tiers"].values())
                          else "INCONCLUSIVE")
    (out / "analysis.json").write_bytes(json.dumps(results, indent=1, default=float).encode("utf-8") + b"\n")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "analyse"))
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--tasks", default="")
    parser.add_argument("--arms", default=",".join(ARMS))
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    out = Path(args.out)
    if args.command == "run":
        tasks = [(d, t, int(f)) for d, t, f in (x.split(":") for x in args.tasks.split(",") if x)] or list(T.TASKS)
        run(out, tasks, [n for n in args.arms.split(",") if n], args.workers)
        return
    results = analyse(out)
    for name, t in results["tiers"].items():
        h, g = t["headroom_vs_fixed_star"], t["gate"]
        p = t["power"]["belief"]
        print(f"{name}: units {t['units']} episodes {t['episodes']} oracle-fixed* {h['difference']:+.3f} "
              f"[{h['ci'][0]:+.3f},{h['ci'][1]:+.3f}] (episode mean {h['episode_mean']:+.3f}) "
              f"n_req {p['units_required_for_mpie']} -> {g['status']}; table oracle matches arm "
              f"{t['table_oracle_matches_oracle_arm']}")
        if "menu_expansion" in t:
            d = t["menu_expansion"]["delta_oracle_ceiling"]
            print(f"   expansion {t['menu_expansion']['base_menu'][:2]}... -> ceiling {d['difference']:+.3f} "
                  f"[{d['ci'][0]:+.3f},{d['ci'][1]:+.3f}] qualifies {t['menu_expansion']['qualifies']}")
    print("verdict", results["verdict"])


if __name__ == "__main__":
    main()
