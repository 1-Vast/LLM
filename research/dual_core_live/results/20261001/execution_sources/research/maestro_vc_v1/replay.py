"""Closed-loop replay of the pre-registered arms on the 20 protocol-v2.1 development tasks.

File summary
- Path: research/maestro_vc_v1/replay.py
- Purpose: for each (dataset, tier, fold) build the fold's case-memory snapshot from training
  references only, install the memory worlds in the truth-free public view, run every arm through
  the registered runner on every episode, and record (a) truth-free traces joined to truth only by
  `contracts.score`, (b) each episode's exact outcome table, and (c) forecast-level items: what each
  world forecast, before any reading, for every condition of every episode.
- Core points:
  - Workflow order per episode: the policy sees only the public view (training reference tables,
    structures, unit keys, the study design's menu); it retrieves precedents from the memory, forecasts,
    chooses; the registered executor then reveals the real reading; the runner updates `EvidenceState`
    through the registered rules; after the episode the truth is joined and the case is scored.
  - The memory a fold's arms read is `Snapshot.index`, built from `Case` objects that hold no held-out
    compound. `public_view_problems` is run and its result is stored beside the traces, and the run
    manifest records the digest of every snapshot.
  - Forecast-level items store, per world, the five-label probability vector of both hypotheses'
    branches at empty history, so calibration and discrimination are scored over every (compound,
    condition, contrast) rather than only over the few actions an arm happened to choose. The realised
    label and the truth are evaluator-side fields.
  - Scalar virtual-cell control. `scalar` forecasts the same reading distribution for both hypotheses
    (the pooled distribution at the condition), which is what a magnitude-only prediction can say; its
    hypothesis discrimination is zero by construction.
  - Output layout: `scored/`, `tables/`, `forecasts/` (gzip JSON lines, timestamp-free so the hashes
    are reproducible), `snapshots/` (case store snapshots), `manifest.json`, `run_record.json`.
- Run: python -m research.maestro_vc_v1.replay [--workers N] [--tasks sciplex3:A:0,...] [--out DIR] [--arms a,b]
- Interfaces: `ARMS`, `FORECAST_WORLDS`, `TASKS`, `run_task`, `run`, `main`
- Depends on: arms.py, research/scientific_case_memory, research/protocol_v2, research/belief_planning,
  research/dual_core
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(variable, "1")

import numpy as np  # noqa: E402

from research.scientific_case_memory import adaptation_model as AM  # noqa: E402
from research.scientific_case_memory import build_cases as BC  # noqa: E402
from research.scientific_case_memory import case_store as CS  # noqa: E402
from research.scientific_case_memory import world as CW  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "maestro_vc_v1" / "replay"
CREATED_AT = "2026-09-29"
SEED = 20260929
TASKS = [(d, t, f) for d, tiers in (("sciplex3", ("A", "B")), ("l1000", ("LT", "T"))) for t in tiers for f in range(5)]
ARMS = ["fixed", "random_legal", "coverage", "scalar_vc", "belief_class", "belief_similarity", "cm_similarity_unitout",
        "cm_full", "cm_full_prior", "cm_full_prior_anchored", "cm_nofail", "prior_only", "vc_incontext", "oracle"]
CM_WORLD_CONFIG = {"cm_similarity_unitout": "similarity_unitout", "cm_full": "cm_full", "cm_full_prior": "cm_full_prior",
                   "cm_nofail": "cm_nofail", "prior_only": "prior_only"}
FORECAST_WORLDS = ("class", "similarity", "similarity_unitout", "cm_full", "cm_nofail", "cm_nomisleading", "cm_nonegative")


def _default(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    if isinstance(value, tuple):
        return list(value)
    return str(value)


def _write(path: Path, rows) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with CS.open_text(path, "wt") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, default=_default) + "\n")
    return BC.sha256_file(path)


def _label_vector(branch, own_is_h1: bool, labels) -> list:
    return [round(float(branch.probabilities.get(x, 0.0)), 6) for x in labels]


def run_task(task, names=tuple(ARMS), out: Path | None = None):
    from threadpoolctl import threadpool_limits

    from research.belief_planning import arms as BA
    from research.belief_planning import tasks as T
    from research.belief_planning import world as W
    from research.dual_core import agent as AG
    from research.dual_core import world2 as W2
    from research.protocol_v2 import contracts as K
    from research.protocol_v2 import runner as RN
    from research.protocol_v2 import tasks_v21 as V
    from research.protocol_v2.safe import max_train_similarity

    from . import arms as ARM

    dataset, tier, fold = task
    started = time.time()
    E, C = K.T.E, K.T.C
    with threadpool_limits(limits=1):
        inputs = BC.load_inputs(dataset, tier, fold)
        data, real_ctx, setting, design = inputs.data, inputs.ctx, inputs.setting, inputs.design
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        heldout = set(comp.index[comp.fold == fold])
        episodes = V.episode_list(real_ctx, fold)
        training = V.training_compounds(real_ctx, fold)
        assert tuple(training) == tuple(inputs.training), "case memory and runner disagree on the training set"
        view = K.public_view(real_ctx, heldout, training_compounds=training, design=design)
        problems = K.public_view_problems(view, heldout)
        unit_of = T.units(dataset)[T.UNIT[dataset]].astype(str).to_dict()
        scaffold_of = {c: (s if isinstance(s, str) and s else None) for c, s in T.units(dataset)["murcko_scaffold"].items()}
        # ---- the case memory of this fold: training references only
        snapshot = BC.build_snapshot(inputs, created_at=CREATED_AT)
        table_context = AM.Context(dataset, "transcriptome")
        cm_worlds = {}
        for arm_name, cfg in CM_WORLD_CONFIG.items():
            cm_worlds[arm_name] = CW.CaseMemoryWorld(snapshot.index, real_ctx.params, training, config=CW.CONFIGS[cfg],
                                                     context=table_context, adaptation=snapshot.adaptation)
        forecast_worlds = {
            "class": CW.CaseMemoryWorld(snapshot.index, real_ctx.params, training, config=CW.CONFIGS["class"]),
            "similarity": BA.world_for(view, "on", "true"),
            "similarity_unitout": cm_worlds["cm_similarity_unitout"], "cm_full": cm_worlds["cm_full"],
            "cm_nofail": cm_worlds["cm_nofail"],
            "cm_nomisleading": CW.CaseMemoryWorld(snapshot.index, real_ctx.params, training, config=CW.CONFIGS["cm_nomisleading"]),
            "cm_nonegative": CW.CaseMemoryWorld(snapshot.index, real_ctx.params, training, config=CW.CONFIGS["cm_nonegative"])}
        ARM.install(view, cm_worlds)
        reference = forecast_worlds["similarity"]
        # ---- the virtual-cell arm (block 7's strict in-context world) and its executor
        vc_arm, executor = None, None
        detected = real_ctx.detected
        quality = np.clip(np.nan_to_num(np.asarray(data.agreement, dtype=np.float64), nan=0.0), 0.0, 1.0)
        batch = (data.conditions.plate_rep1 if dataset == "sciplex3" else data.conditions.batch).astype(str).to_numpy()
        executor = AG.LedgerExecutor(real_ctx, dataset=dataset,
                                     assay="sci-RNA-seq3 pseudobulk shift" if dataset == "sciplex3" else "L1000 Level 5 MODZ",
                                     quality=quality, batch=batch, detected=detected, cost_days=setting.days)
        if "vc_incontext" in names:
            fp, pos = view.extra["fingerprints"]
            public = view.data.compounds.drop_duplicates("compound").set_index("compound")
            unit_col = "component" if "component" in public.columns else "skeleton"
            groups = {c: g for c, g in public[unit_col].items() if isinstance(g, str)}
            ref_quality = {}
            for key, tab in view.ft.tables.items():
                for name in tab.names:
                    ref_quality.setdefault(name, {})[key] = float(quality[data.index[key][name]])
            vc_world = W2.StrictInContextWorld(view.ft, view.params, training, reference_quality=ref_quality,
                                               transfer_arm="rrt_q", source="auto", fingerprints=fp, positions=pos,
                                               vc="on", feedback="true", hyperparameters=reference.hyperparameters,
                                               groups=groups, heldout=heldout)
            vc_arm = AG.incontext_arm(executor, {id(view): vc_world})
        arms = ARM.build_arms(names, real_ctx, view, vc_incontext=vc_arm)
        # ---- nearest training neighbour (structure is public; the class is a training label)
        fp_all, pos_all = view.extra["fingerprints"]
        train_rows = [pos_all[c] for c in training if pos_all.get(c, -1) >= 0]
        train_names = [c for c in training if pos_all.get(c, -1) >= 0]
        traces, tables, forecasts = [], [], []
        labels = W.LABELS
        for compound, truth, decoy, h1, h2 in episodes:
            available = view.data.availability[compound]
            local = RN.local_setting(setting, available)
            nn_sim, nn_class = float("nan"), None
            row = pos_all.get(compound, -1)
            if row >= 0 and fp_all[row].any() and train_rows:
                x = fp_all[row]
                m = fp_all[np.asarray(train_rows)]
                inter = m @ x
                union = m.sum(1) + x.sum() - inter
                sim = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
                j = int(sim.argmax())
                nn_sim, nn_class = float(sim[j]), inputs.klass_of.get(train_names[j])
            meta = {"dataset": dataset, "tier": tier, "fold": fold, "decoy": decoy, "unit": unit_of.get(compound, compound),
                    "scaffold": scaffold_of.get(compound), "max_train_tanimoto": max_train_similarity(view, reference, compound),
                    "nn_class": nn_class, "nn_similarity": nn_sim, "protocol_version": "maestro-vc-v1"}
            for name, arm in arms.items():
                executor.open(compound, h1, h2)
                trace = RN.run_episode(name, arm, view, real_ctx, compound, h1, h2, setting, execute=executor,
                                       design_menu=True)
                problems += [f"{name}:{compound}:{p}" for p in RN.audit_trace(trace, local)]
                trace.update(meta, reads_hidden_outcomes=name == "oracle")
                traces.append(trace)
            table = {}
            for key in local.keys:
                result = E.execute(real_ctx, compound, key, h1, h2)
                lifecycle = K.lifecycle_state(True, result)
                outcome = result["outcome"] if lifecycle is K.Lifecycle.MEASURED_VALID else "quality_failed"
                table[C.action_id(key)] = {"key": list(key), "lifecycle": lifecycle.value, "readout": K.readout(result),
                                           "outcome": outcome}
                if lifecycle is K.Lifecycle.MEASURED_VALID or lifecycle is K.Lifecycle.MEASURED_QC_FAILED:
                    row_f = {"compound": compound, "key": C.action_id(key), "h1": h1, "h2": h2, "truth": truth,
                             "unit": meta["unit"], "y": W.label_of(outcome), "tier": tier, "dataset": dataset,
                             "fold": fold, "nn_similarity": nn_sim, "nn_class": nn_class, "worlds": {},
                             "prior_h1": round(float(cm_worlds["cm_full_prior"].hypothesis_prior(
                                 compound, h1, h2, meta["unit"])[h1]), 6)}
                    for wname, world in forecast_worlds.items():
                        f = world.forecast(tuple(key), h1, h2, compound, ())
                        if f.refusal:
                            row_f["worlds"][wname] = None
                            continue
                        by = {b.hypothesis: b for b in f.branches}
                        row_f["worlds"][wname] = {"h1": _label_vector(by[h1], True, labels),
                                                  "h2": _label_vector(by[h2], False, labels),
                                                  "support": [by[h1].support, by[h2].support]}
                    ref_f = forecast_worlds["similarity"].forecast(tuple(key), h1, h2, compound, ())
                    if not ref_f.refusal:
                        entry = forecast_worlds["similarity"].keys[tuple(key)]
                        pooled, qc = entry["pooled"], entry["qc_fail"]
                        own = float((pooled[0] + pooled[1]) / 2.0)
                        vec = [round((1 - qc) * own, 6), round((1 - qc) * own, 6), round((1 - qc) * float(pooled[2]), 6),
                               round((1 - qc) * float(pooled[3]), 6), round(float(qc), 6)]
                        row_f["worlds"]["scalar"] = {"h1": vec, "h2": vec, "support": [0, 0]}
                    forecasts.append(row_f)
            tables.append({**meta, "compound": compound, "h1": h1, "h2": h2, "truth": truth, "outcomes": table,
                           "unplanned_tier_conditions": len(setting.keys) - len(local.keys)})
        truth_of = {(c, a, b): t for c, t, _, a, b in episodes}
        scored = [{**trace, "score": K.score(trace, truth_of[(trace["compound"], trace["h1"], trace["h2"])])}
                  for trace in traces]
    result = {"task": list(task), "scored": scored, "tables": tables, "forecasts": forecasts, "problems": problems,
              "episodes": len(episodes), "pool": list(real_ctx.tier.pool), "eligible": len(real_ctx.tier.compounds),
              "snapshot": snapshot.manifest,
              "hyperparameters": {n: {k: v for k, v in w.hyperparameters.items() if k in ("s", "k", "e", "prior_a", "k_fit")}
                                  for n, w in {**cm_worlds, "reference": reference}.items()},
              "setting": {"keys": [list(k) for k in setting.keys], "fixed_order": [list(k) for k in setting.fixed_order],
                          "max_measurements": setting.max_measurements, "budget_days": setting.budget_days,
                          "days": {C.action_id(k): setting.days(k) for k in setting.keys}},
              "seconds": time.time() - started}
    if out is not None:
        snapshot.store.write_snapshot(out / "snapshots" / f"cases_{dataset}_{tier}_{fold}.jsonl.gz")
    return result


def run(out: Path, tasks, names, workers: int) -> dict:
    manifest = {"created_at": CREATED_AT, "arms": list(names), "tasks": {}, "problems": {}, "outputs_sha256": {},
                "settings": {}, "snapshots": {}, "hyperparameters": {}}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_task, t, tuple(names), out): t for t in tasks}
        for future in as_completed(futures):
            result = future.result()
            d, t, f = result["task"]
            name = f"{d}_{t}_{f}"
            for kind in ("scored", "tables", "forecasts"):
                manifest["outputs_sha256"][f"{kind}/{name}.jsonl.gz"] = _write(out / kind / f"{name}.jsonl.gz",
                                                                              result[kind])
            manifest["tasks"][name] = {"episodes": result["episodes"], "records": len(result["scored"]),
                                       "forecast_items": len(result["forecasts"]), "pool": result["pool"],
                                       "eligible_compounds": result["eligible"], "seconds": round(result["seconds"], 1)}
            manifest["settings"][f"{d}_{t}"] = result["setting"]
            manifest["problems"][name] = result["problems"]
            manifest["snapshots"][name] = {k: result["snapshot"][k] for k in ("digest", "cases", "training_cases",
                                                                              "adaptation_cases", "kinds", "reading_kinds")}
            manifest["hyperparameters"][name] = result["hyperparameters"]
            print(name, result["episodes"], "episodes", len(result["problems"]), "problems", f"{result['seconds']:.0f}s",
                  flush=True)
    (out / "manifest.json").write_bytes(json.dumps(manifest, indent=1, sort_keys=True).encode("utf-8") + b"\n")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 4))
    parser.add_argument("--tasks", default=None, help="comma separated dataset:tier:fold")
    parser.add_argument("--arms", default=",".join(ARMS))
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    tasks = TASKS if not args.tasks else [(a, b, int(c)) for a, b, c in (t.split(":") for t in args.tasks.split(","))]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    names = args.arms.split(",")
    from research.protocol_v2 import registry as G

    from . import freeze as FZ
    record = G.development_record(out / "run_record.json", "maestro-vc-v1-replay",
                                  protocol_files=["research/maestro_vc_v1/protocol.json"],
                                  code_files=[f for f in FZ.FILES if not f.endswith(".json")],
                                  data_files=list(FZ.DATA), command=[sys.executable, "-m", "research.maestro_vc_v1.replay",
                                                                     *sys.argv[1:]], seed=SEED,
                                  protocol_version="maestro-vc-v1")
    print("record", record["status"], "commit", record["git_commit"], "dirty", record["git_dirty"], flush=True)
    run(out, tasks, names, args.workers)


if __name__ == "__main__":
    sys.exit(main())
