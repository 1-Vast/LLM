"""Nested dual-core v2 runs: one model per excluded fold pair, both of its held-out folds, all arms, lineage recorded.

File summary
- Path: research/dual_core_v2/run.py
- Purpose: produce the traces every v2 analysis reads, under `protocol.json`. A job is
  (dataset, tier, f, g): one model M(f, g) fitted with folds f and g held out (`nested.load`), then
  run on the episodes of fold f and of fold g.
- Core points:
  - Lineage. Each job records `nested.lineage_of` and calls `nested.check_independent` for both
    folds before any episode runs; a failure stops the job.
  - Arms (every arm plans on the same view, menus, budgets and executor):
    - P0 arms: `reference`, `v1`, `v2` (`arms.planner_arm` without a cap);
    - `full` jobs add risk-select arms: world in {reference, v2} x measure in {upper, point} x the
      pre-declared caps; and the diagnostic `oracle` arm, whose world reads the compound's true
      measured shift at each candidate condition. The oracle bounds what a perfect response model
      could do through this interface. It reads outcomes and is never a policy.
  - Ablation (`full` jobs, diagnostic). At every executed step of the `reference` and `v2` P0
    traces, every world variant (reference, v1, v2, each single source, oracle) gives its forecast of
    that step and the action it would have chosen at that decision point from the same real history.
  - Reproduction anchor. The `reference` arm is `arms.planner_arm` with the reference world; on the
    first episodes of each job it is compared with block 2's `belief_arm` (action sequences must match).
  - Write-once per job under `outputs/dual_core_v2_20260928/runs/`.
- Interfaces: `run_job`, `jobs`, CLI `python -m research.dual_core_v2.run [--workers N] [--only KIND]`
- Depends on: nested.py, world3.py, arms.py, research/protocol_v2, research/belief_planning, research/dual_core
"""
from __future__ import annotations

import argparse
import gzip
import json
import time
from pathlib import Path

import numpy as np

from . import nested as NS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/dual_core_v2_20260928/runs"
TIERS = (("sciplex3", "A"), ("sciplex3", "B"), ("l1000", "LT"), ("l1000", "T"))
ANCHOR_EPISODES = 8
VARIANTS = ("reference", "v1", "v2", "prompt", "transfer", "additive", "transfer_dist", "oracle")


def protocol() -> dict:
    return json.loads((ROOT / "research/dual_core_v2/protocol.json").read_text(encoding="utf-8"))


def jobs(kind: str = "all"):
    split = set(NS.split_pairs())
    out = []
    for dataset, tier in TIERS:
        for f, g in NS.all_pairs():
            full = (f, g) in split or (g, f) in split
            if kind == "all" or (kind == "full") == full:
                out.append((dataset, tier, f, g, "full" if full else "base"))
    return out


class OracleWorld:
    """DIAGNOSTIC. Forecasts from the compound's own measured shift at each candidate condition."""

    def __init__(self, world, real_ctx, params):
        self.world, self.real_ctx, self.params = world, real_ctx, params
        self.incontext = {"source": "oracle", **params}

    def forecast(self, key, h1, h2, compound, history=(), prompts=None):
        key = tuple(key)
        row = self.real_ctx.data.index.get(key, {}).get(compound)
        base = self.world.forecast(key, h1, h2, compound, history, prompts=None)
        if row is None or self.params.get("kappa", 0.0) <= 0:
            return base
        logk = self.world.cosine(key, np.asarray(self.real_ctx.data.shift[row], dtype=np.float64)) - 1.0
        return self.world.forecast_from_logkernel(key, h1, h2, compound, history, logk, self.params)


def _branches(forecast) -> dict:
    return {b.hypothesis: dict(b.probabilities) for b in forecast.branches} if not forecast.refusal else {}


def run_job(job) -> dict:
    from threadpoolctl import threadpool_limits

    from research.belief_planning import arms as BA
    from research.belief_planning import tasks as T
    from research.belief_planning import world as W
    from research.incontext_world import world as IW
    from research.protocol_v2 import contracts as K
    from research.protocol_v2 import runner as RN

    from . import arms as AR
    from . import world3 as W3

    dataset, tier, f, g, kind = job
    spec = protocol()
    started = time.time()
    with threadpool_limits(limits=1):
        data, real_ctx, setting, design, original = NS.load(dataset, tier, (f, g))
        unit_of = T.units(dataset)[T.UNIT[dataset]].astype(str).to_dict()
        lineage = NS.lineage_of(dataset, tier, (f, g), real_ctx, original)
        episodes = {fold: NS.episodes_for(real_ctx, original, fold) for fold in (f, g)}
        heldout = {c for c, fo in original.items() if fo in (f, g)}
        for fold in (f, g):
            NS.check_independent(lineage, [c for c, fo in original.items() if fo == fold], unit_of)
        training = lineage.training_compounds
        view = K.public_view(real_ctx, heldout, training_compounds=training, design=design)
        problems = K.public_view_problems(view, heldout)
        reference = BA.world_for(view, "on", "true")
        fp, pos = view.extra["fingerprints"]
        public = view.data.compounds.drop_duplicates("compound").set_index("compound")
        unit_col = "component" if "component" in public.columns else "skeleton"
        groups = {c: gr for c, gr in public[unit_col].items() if isinstance(gr, str)}
        quality = np.clip(np.nan_to_num(np.asarray(data.agreement, dtype=np.float64), nan=0.0), 0.0, 1.0)
        ref_quality = {}
        for key, table in view.ft.tables.items():
            for name in table.names:
                ref_quality.setdefault(name, {})[key] = float(quality[data.index[key][name]])
        assay = "sci-RNA-seq3 pseudobulk shift" if dataset == "sciplex3" else "L1000 Level 5 MODZ"
        fit_started = time.time()
        world = W3.WorldV2(view.ft, view.params, training, dataset=dataset, assay=assay, reference_quality=ref_quality,
                           fingerprints=fp, positions=pos, vc="on", feedback="true",
                           hyperparameters=reference.hyperparameters, groups=groups, heldout=heldout,
                           diagnostic=kind == "full")
        fit_seconds = time.time() - fit_started
        variants = {"reference": AR.ReferenceAdapter(reference), "v1": world.variant("v1"), "v2": world.variant("auto")}
        if kind == "full":
            for src in ("prompt", "transfer", "additive", "transfer_dist"):
                variants[src] = world.variant(src)
            variants["oracle"] = OracleWorld(world, real_ctx, IW.restrict(world.fitted, "oracle")
                                             if world.fitted.get("loglik") else {"kappa": 0.0, "tau": 0.0})
        batch = (data.conditions.plate_rep1 if dataset == "sciplex3" else data.conditions.batch).astype(str).to_numpy()
        executor = AR.LedgerExecutorV2(real_ctx, dataset=dataset, assay=assay, quality=quality, batch=batch,
                                       detected=real_ctx.detected, cost_days=setting.days)
        worlds = {id(view): variants}
        arms = {name: AR.planner_arm(executor, worlds, name) for name in ("reference", "v1", "v2")}
        if kind == "full":
            arms["oracle"] = AR.planner_arm(executor, worlds, "oracle")
            for w in ("reference", "v2"):
                for measure in ("upper", "point"):
                    for cap in spec["risk_select"]["caps"][dataset][measure]:
                        arms[f"{w}|{measure}|{cap:g}"] = AR.planner_arm(executor, worlds, w, cap=cap, cap_measure=measure)
        anchor_arm = BA.belief_arm()
        traces, ablation, anchor = [], [], []
        by_id = {K.T.C.action_id(k): k for k in setting.keys}
        for fold in (f, g):
            for n_ep, (compound, truth, decoy, h1, h2) in enumerate(episodes[fold]):
                available = view.data.availability[compound]
                local = RN.local_setting(setting, available)
                meta = {"dataset": dataset, "tier": tier, "fold": fold, "model": [f, g], "decoy": decoy,
                        "unit": unit_of.get(compound, compound), "role_pair": sorted((f, g))}
                for name, arm in arms.items():
                    ledger = executor.open(compound, h1, h2)
                    trace = RN.run_episode(name, arm, view, real_ctx, compound, h1, h2, setting, execute=executor,
                                           design_menu=True)
                    problems += [f"{name}:{compound}:{p}" for p in RN.audit_trace(trace, local)]
                    trace.update(meta, ledger_refusals=[list(map(str, r)) for r in ledger.refusals])
                    if kind == "full" and name in ("reference", "v2"):
                        public_steps = [{k: s[k] for k in ("key", "action", "outcome", "qc", "eliminated")}
                                        for s in trace["steps"]]
                        real = [(tuple(s["key"]), W.label_of(s["outcome"])) for s in trace["steps"]]
                        for i, step in enumerate(trace["steps"]):
                            key = tuple(step["key"])
                            prompts = ledger.prompt_set(target=key, executed=public_steps[:i])
                            record = {"arm": name, "compound": compound, "h1": h1, "h2": h2, "fold": fold,
                                      "unit": meta["unit"], "step": i, "key": list(key), "label": real[i][1],
                                      "prompts": len(prompts.prompts), "forecasts": {}, "choice": {}}
                            menu = [by_id[a] for a in trace["offered"][i]]
                            for vname, vw in variants.items():
                                record["forecasts"][vname] = _branches(
                                    vw.forecast(key, h1, h2, compound, tuple(real[:i]), prompts=prompts))
                                chooser = AR.planner_arm(executor, worlds, vname)
                                ck, note = chooser(view, compound, h1, h2, public_steps[:i], menu, None, local, None)
                                record["choice"][vname] = K.T.C.action_id(ck) if ck is not None else None
                            record["sources"] = {v: variants[v].incontext.get("source") for v in variants}
                            ablation.append(record)
                    traces.append(trace)
                if n_ep < ANCHOR_EPISODES:
                    executor.open(compound, h1, h2)
                    old = RN.run_episode("belief", anchor_arm, view, real_ctx, compound, h1, h2, setting,
                                         execute=executor, design_menu=True)
                    new = next(t for t in reversed(traces) if t["arm"] == "reference" and t["compound"] == compound
                               and t["h1"] == h1 and t["h2"] == h2)
                    anchor.append([s["action"] for s in old["steps"]] == [s["action"] for s in new["steps"]])
        truth_of = {(c, a, b): t for fold in (f, g) for c, t, _, a, b in episodes[fold]}
        for trace in traces:
            trace["score"] = K.score(trace, truth_of[(trace["compound"], trace["h1"], trace["h2"])])
            trace["truth"] = trace["score"]["truth"]
    return {"job": list(job), "lineage": lineage.payload(), "traces": traces, "ablation": ablation,
            "problems": problems, "anchor": {"episodes": len(anchor), "matches": int(sum(anchor))},
            "episodes": {str(k): len(v) for k, v in episodes.items()},
            "reference_hyperparameters": {k: reference.hyperparameters[k] for k in ("s", "k", "e")},
            "world": {v: {k: variants[v].incontext.get(k) for k in ("source", "kappa", "tau", "gain")} for v in variants},
            "loglik": world.fitted.get("loglik_kappa0"), "loglik_tables": world.fitted.get("loglik"),
            "items": world.fitted.get("items"), "fit_seconds": fit_seconds, "seconds": time.time() - started}


def _base(job) -> Path:
    dataset, tier, f, g, _ = job
    return OUT / f"{dataset}_{tier}_m{f}{g}"


def write(result: dict) -> str:
    base = _base(tuple(result["job"]))
    base.parent.mkdir(parents=True, exist_ok=True)
    for part in ("traces", "ablation"):
        with gzip.open(f"{base}.{part}.jsonl.gz", "wt", encoding="utf-8") as fh:
            for row in result[part]:
                fh.write(json.dumps(row, default=str) + "\n")
    meta = {k: v for k, v in result.items() if k not in ("traces", "ablation")}
    Path(f"{base}.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    return (f"{result['job']} episodes {result['episodes']} traces {len(result['traces'])} problems "
            f"{len(result['problems'])} anchor {result['anchor']['matches']}/{result['anchor']['episodes']} "
            f"fit {result['fit_seconds']:.0f}s total {result['seconds']:.0f}s v2 {result['world']['v2']}")


def _run_and_write(job) -> str:
    if Path(f"{_base(job)}.json").exists():
        return f"{job}: exists, skipped (write-once)"
    return write(run_job(job))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--only", choices=("all", "full", "base"), default="all")
    parser.add_argument("--job", nargs=5, default=None, metavar=("DATASET", "TIER", "F", "G", "KIND"))
    args = parser.parse_args()
    if args.job:
        d, t, f, g, k = args.job
        print(_run_and_write((d, t, int(f), int(g), k)), flush=True)
        return
    import multiprocessing as mp
    todo = sorted(jobs(args.only), key=lambda j: (j[0] != "sciplex3" or j[1] != "B", j[0] != "l1000" or j[1] != "LT"))
    with mp.get_context("spawn").Pool(args.workers, maxtasksperchild=1) as pool:
        for line in pool.imap_unordered(_run_and_write, todo):
            print(line, flush=True)


if __name__ == "__main__":
    main()
