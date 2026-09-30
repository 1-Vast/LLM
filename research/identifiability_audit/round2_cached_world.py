"""Review existing WorldV2 forecasts on identical purchased steps; no new model calls.

This is a historical reading-quality audit, never a forecast-swap intervention.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.identifiability_audit import round2 as R


def run(out: Path):
    destination = out / "cached_world"
    destination.mkdir(exist_ok=False)
    tasks = {}
    for dataset, tier in R.TASKS:
        task = dataset + "_" + tier
        truth = {(r["fold"], r["compound"], r["h1"], r["h2"]): r for r in R.tables(task)}
        records, inputs, skipped = [], {}, 0
        for path in sorted((R.ROOT / "outputs/dual_core_v2_20260928/runs").glob(task + "*.ablation.jsonl.gz")):
            inputs[path.relative_to(R.ROOT).as_posix()] = R.file_hash(path)
            for row in R.read_rows(path):
                identity = row["fold"], row["compound"], row["h1"], row["h2"]
                if identity not in truth:
                    skipped += 1
                    continue
                known = truth[identity]
                values = {}
                for backend in ("reference", "v2"):
                    branch = row["forecasts"].get(backend, {}).get(known["truth"])
                    if not branch:
                        break
                    label = row["label"]
                    values[backend + "_nll"] = -float(np.log(max(branch.get(label, 0.0), 1e-12)))
                    values[backend + "_brier"] = sum((p - (l == label)) ** 2 for l, p in branch.items())
                else:
                    records.append({"independent_unit": str(known["unit"]), "compound": row["compound"],
                                    "fold": row["fold"], "origin_file": path.name, "selected_by": row["arm"],
                                    "step": row["step"], "prompts": row["prompts"], "label": row["label"],
                                    "world_v2_source": row.get("sources", {}).get("v2"), **values,
                                    "delta_nll": values["v2_nll"] - values["reference_nll"],
                                    "delta_brier": values["v2_brier"] - values["reference_brier"]})
        frame = pd.DataFrame(records)
        frame.to_csv(destination / (task + "_selected_step_quality.csv"), index=False, mode="x")
        tasks[task] = {"rows": len(frame), "unmatched_context_rows": skipped, "inputs": inputs,
                       "all_selected_steps": {m: R.paired_ci(frame, m) for m in
                                              ("reference_nll", "v2_nll", "delta_nll", "delta_brier")},
                       "purchased_prompt_steps": {m: R.paired_ci(frame[frame.prompts > 0], m) for m in
                                                 ("reference_nll", "v2_nll", "delta_nll", "delta_brier")}}
    R.save(destination / "summary.json", {"tasks": tasks, "status": "historical_forecast_review_only",
        "limits": "Existing nested models and purchased histories differ from the new intervention freeze. "
                  "Forecasts on identical selected steps support a reading-quality contrast. Their selection "
                  "does not identify all-menu quality or a forecast-swap policy effect. Data exposed since 2026-09-26.",
        "code_sha256": R.file_hash(Path(__file__)), "command": "python -m research.identifiability_audit.round2_cached_world"})
    print("Cached WorldV2 quality reviewed", flush=True)


if __name__ == "__main__":
    run(R.OUT)
