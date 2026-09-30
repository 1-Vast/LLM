"""Development replay of the belief-planning agent and its controls on the registered episodes.

File summary
- Path: research/belief_planning/devrun.py
- Purpose: run the agent (and chosen comparators) through `policies.run_matched` on the
  2026-09-27 development episodes (SciPlex3 A/B, L1000 LT/T). Arms get the sealed policy view.
  Write one record per episode and arm, then print per-tier rates.
- Core points:
  - Development only. Results here choose nothing about an external study except through the
    frozen protocol written before it is opened.
  - The executor runs on the real context. Arms receive `firewall.seal(ctx)` (held-out rows,
    annotations and detection removed).
- Run: python -m research.belief_planning.devrun --out NAME [--arms a,b] [--workers N]
- Depends on: tasks.py, arms.py, research/external_validation/firewall.py
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(variable, "1")

import numpy as np  # noqa: E402

from . import arms as BA  # noqa: E402
from . import tasks as T  # noqa: E402

ROOT = T.ROOT
OUT = ROOT / "outputs" / "belief_planning_20260927"
P, C, E = T.P, T.C, T.E

ARMS = {
    "fixed": lambda: P.fixed,
    "belief": lambda: BA.belief_arm(),
    "belief_h1": lambda: BA.belief_arm(horizon=1),
    "belief_vc_masked": lambda: BA.belief_arm(vc="masked"),
    "belief_vc_permuted": lambda: BA.belief_arm(vc="permuted"),
    "belief_feedback_withheld": lambda: BA.belief_arm(feedback="withheld"),
    "belief_feedback_permuted": lambda: BA.belief_arm(feedback="permuted"),
    "anchored": lambda: BA.belief_arm(anchor=True),
    "anchored_vc_masked": lambda: BA.belief_arm(anchor=True, vc="masked"),
    "anchored_vc_permuted": lambda: BA.belief_arm(anchor=True, vc="permuted"),
    "anchored_feedback_withheld": lambda: BA.belief_arm(anchor=True, feedback="withheld"),
    "anchored_feedback_permuted": lambda: BA.belief_arm(anchor=True, feedback="permuted"),
    "belief_s16": lambda: BA.belief_arm(overrides={"s": 16.0}),
    "belief_s64": lambda: BA.belief_arm(overrides={"s": 64.0}),
    "belief_s1000": lambda: BA.belief_arm(overrides={"s": 1000.0, "k": 0.0}),
    "belief_s1000_nofb": lambda: BA.belief_arm(overrides={"s": 1000.0, "k": 0.0, "e": 1.0}),
    "belief_pooled_only": lambda: BA.belief_arm(overrides={"s": 1e9, "k": 0.0, "e": 1.0}),
}


def run_task(task, arm_names, limit=None):
    from threadpoolctl import threadpool_limits
    from research.external_validation import firewall as F
    dataset, tier, fold = task
    with threadpool_limits(limits=1):
        data, ctx, setting = T.load(dataset, tier, fold)
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        heldout = set(comp.index[comp.fold == fold])
        sealed = F.seal(ctx, heldout)
        episodes = T.prepare(sealed, fold, tier, real_ctx=ctx)
        problems = F.sealed_view_problems(sealed, heldout)
        if limit:
            episodes = episodes[:limit]
        unit = T.units(dataset)[T.UNIT[dataset]]
        records = []
        for compound, truth, decoy, h1, h2 in episodes:
            for name in arm_names:
                arm = ARMS[name]()
                start = time.perf_counter()
                row = P.run_matched(name, arm, sealed, compound, truth, h1, h2, setting, qc_rule="continue",
                                    execute=lambda _c, cpd, key, a, b: E.execute(ctx, cpd, key, a, b))
                problems += [f"{name}:{compound}:{v}" for v in P.audit_record(row, setting)]
                row.update({"dataset": dataset, "tier": tier, "fold": fold, "decoy": decoy, "arm": name,
                            "unit": str(unit.get(compound, compound)), "compute_seconds": time.perf_counter() - start})
                records.append(C.clean(row))
    return {"task": task, "records": records, "problems": problems}


def summarize(records):
    out = {}
    for r in records:
        k = (r["dataset"], r["tier"], r["arm"])
        s = out.setdefault(k, {"n": 0, "correct": 0, "wrong": 0, "deferred": 0, "m": 0, "days": 0.0})
        s["n"] += 1
        s["correct"] += r["final"] == "correct"
        s["wrong"] += r["final"] in ("wrong", "exhausted")
        s["deferred"] += r["final"] == "deferred"
        s["m"] += r["measurements"]
        s["days"] += r["days"]
    for (d, t, a), s in sorted(out.items()):
        n = s["n"]
        print(f"{d:8s} {t:3s} {a:26s} n={n:5d} correct={s['correct']/n:.3f} wrong={s['wrong']/n:.3f} "
              f"deferred={s['deferred']/n:.3f} meas={s['m']/n:.2f} days={s['days']/n:.1f}")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--arms", default=",".join(ARMS))
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--tasks", default=None, help="comma list of dataset:tier to restrict")
    args = parser.parse_args()
    names = args.arms.split(",")
    tasks = T.TASKS
    if args.tasks:
        wanted = {tuple(x.split(":")) for x in args.tasks.split(",")}
        tasks = [t for t in tasks if (t[0], t[1]) in wanted]
    out = OUT / "dev" / args.out
    out.mkdir(parents=True, exist_ok=True)
    records, problems = [], []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_task, t, names, args.limit): t for t in tasks}
        for future in as_completed(futures):
            result = future.result()
            d, t, f = result["task"]
            with gzip.open(out / f"{d}_{t}_{f}.jsonl.gz", "wt", encoding="utf-8") as fh:
                for r in result["records"]:
                    fh.write(json.dumps(r, sort_keys=True) + "\n")
            records += result["records"]
            problems += result["problems"]
    (out / "problems.json").write_text(json.dumps(problems, indent=1), encoding="utf-8")
    print("problems", len(problems), problems[:5])
    summarize(records)


if __name__ == "__main__":
    main()
