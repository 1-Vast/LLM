"""Run the frozen exploratory sequence comparison without rewriting prior records."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

import two_step as S

C, E, V = S.C, S.E, S.V
HERE = Path(__file__).resolve().parent
OUT = S.ROOT / "outputs" / "acquisition_followup" / "sequences"


def run_fold(task):
    tier, fold = task
    data, protocol = C.load(), C.load_protocol()
    detected = C.detected_flags(data, C.detection_null(data, protocol))
    magnitude = E.Magnitude(data, detected)
    records = []
    for ctx, f in E.contexts(data, protocol, detected, magnitude, tier_names=(tier,), folds=(fold,)):
        def da(ctx, c, h1, h2, ex, menu):
            menu = [k for k in menu if not ex or k[1] >= ex[-1]["key"][1]]
            return V.choose_discriminating(ctx, c, h1, h2, ex, menu, minimum=1)

        ctx.extra["policies"] = {
            "da": da,
            "one_step_utility": lambda *args: S.policy(*args, horizon=1),
            "two_step": S.policy,
            "two_step_permuted": lambda *args: S.policy(*args, permuted=True),
        }
        for compound, truth, decoy, h1, h2 in E.episode_list(ctx, f):
            for arm in ("da", "fixed", "one_step_utility", "two_step", "two_step_permuted"):
                row = E.run_episode(arm, ctx, compound, truth, h1, h2, None)
                assert row["days"] <= 16
                assert len(row["steps"]) <= 2
                times = [s["key"][1] for s in row["steps"]]
                assert times == sorted(times)
                assert all(s["qc"] or not s["eliminated"] for s in row["steps"])
                records.append({"tier": tier, "fold": f, "decoy": decoy, **row})
    return records


def analyze(records):
    frame = pd.DataFrame(records)
    frame["correct"] = (frame.final == "correct").astype(float)
    frame["wrong"] = frame.final.isin(("wrong", "exhausted")).astype(float)
    metrics = ["correct", "wrong", "utility", "days", "measurements"]
    summary = {"means": [], "contrasts": []}
    for (tier, policy), group in frame.groupby(["tier", "policy"]):
        summary["means"].append({"tier": tier, "policy": policy, "episodes": len(group),
                                 **{m: float(group[m].mean()) for m in metrics}})
    for tier, group in frame.groupby("tier"):
        for baseline in ("da", "one_step_utility", "fixed", "two_step_permuted"):
            left = group[group.policy == "two_step"].set_index(["compound", "h1", "h2"])
            right = group[group.policy == baseline].set_index(["compound", "h1", "h2"])
            assert left.index.equals(right.index)
            difference = left[metrics] - right[metrics]
            blocks = difference.groupby(level="compound").sum().to_numpy()
            counts = difference.groupby(level="compound").size().to_numpy()
            rng = np.random.default_rng(20260926)
            ix = rng.integers(len(blocks), size=(2000, len(blocks)))
            boot = blocks[ix].sum(axis=1) / counts[ix].sum(axis=1)[:, None]
            for j, metric in enumerate(metrics):
                summary["contrasts"].append({"tier": tier, "baseline": baseline, "metric": metric,
                    "difference": float(difference[metric].mean()),
                    "ci95": np.quantile(boot[:, j], [0.025, 0.975]).tolist(), "compounds": len(blocks)})
    summary["qc_policy_audit"] = []
    for (tier, policy), group in frame.groupby(["tier", "policy"]):
        failed = [steps for steps in group.steps if steps and not steps[0]["qc"]]
        summary["qc_policy_audit"].append({"tier": tier, "policy": policy,
            "first_qc_failed": len(failed), "continued_after_qc_failure": sum(len(s) > 1 for s in failed)})
    return summary


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    protocol = (HERE / "protocol.json").read_bytes()
    freeze = {"frozen_at": datetime.now(timezone.utc).isoformat(), "protocol_sha256": hashlib.sha256(protocol).hexdigest(),
              "python": sys.executable, "status": "exploratory; previously analysed data"}
    # Commit the exact analysis specification to disk before loading outcomes.
    if (OUT / "freeze.json").exists():
        freeze = json.loads((OUT / "freeze.json").read_text(encoding="utf-8"))
        if freeze["protocol_sha256"] != hashlib.sha256(protocol).hexdigest():
            raise ValueError("Frozen protocol differs; use a separately named study.")
    else:
        (OUT / "protocol.json").write_bytes(protocol)
        (OUT / "freeze.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    folds = sorted(int(f) for f in C.load().compounds.fold.unique())
    tasks = [(tier, fold) for tier in ("B", "A") for fold in folds]
    records = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        for task, rows in zip(tasks, pool.map(run_fold, tasks)):
            records.extend(rows)
            print(f"{task}: {len(rows)} records", flush=True)
    (OUT / "episodes.jsonl").write_text("".join(json.dumps(C.clean(r)) + "\n" for r in records), encoding="utf-8")
    summary = analyze(records)
    summary["freeze"] = freeze
    summary["source_sha256"] = {str(p.relative_to(S.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
        HERE / "two_step.py", Path(__file__), V.HERE / "evaluate.py", C.HERE / "common.py", C.HERE / "episodes.py",
        S.ROOT / "src" / "maestro" / "outcome.py")}
    summary["data_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(C.PREPARED.iterdir()) if p.is_file()}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    text = ["# Exploratory sequence comparison", "", "Real SciPlex3; existing held-out scaffold folds. "
            "Previously analysed data: these results cannot justify promotion. Five policies use the same "
            "validator, at most two measurements, 16 assay-days and nondecreasing exposure time.", "",
            "|Tier|Policy|Episodes|Correct|Wrong|Utility|Days|", "|---|---|---:|---:|---:|---:|---:|"]
    for r in summary["means"]:
        text.append(f"|{r['tier']}|{r['policy']}|{r['episodes']}|{r['correct']:.3f}|{r['wrong']:.3f}|{r['utility']:.3f}|{r['days']:.2f}|")
    text += ["", "Paired two_step minus baseline; 95% compound-bootstrap intervals:", "",
             "|Tier|Baseline|Metric|Difference|95% CI|", "|---|---|---|---:|---|"]
    for r in summary["contrasts"]:
        if r["metric"] in ("correct", "wrong", "utility"):
            text.append(f"|{r['tier']}|{r['baseline']}|{r['metric']}|{r['difference']:+.3f}|"
                        f"[{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]|")
    text += ["", "The two-step policy uses paired training-reference transitions conditioned on the first "
             "reading, keeps wrong elimination separate, and executes the precomputed contingent continuation "
             "only after a real result. Missing "
             "paired support ends that branch. Its uniform initial hypothesis weights and Jeffreys "
             "probabilities are planning assumptions, never posterior evidence. The myopic control uses "
             "the same forecasts and conditional continuation, but ranks its first measurement on "
             "immediate utility. Neither policy is enabled by default.", "",
             "The sequence arms stop after a QC failure; da and fixed can continue. Forecast probabilities "
             "come from QC-passing references and do not model execution/missingness probability. Expected "
             "utility is therefore conditional on assay QC, and comparisons against fixed mix planning "
             "and QC-stop behavior. The horizon comparison against one_step_utility shares that behavior. "
             "Intervals resample compounds; related scaffold pairs in tier B may remain dependent."]
    (OUT / "report.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} records and report to {OUT}", flush=True)


if __name__ == "__main__":
    main()
