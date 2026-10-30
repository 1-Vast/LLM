"""Descriptive diagnostics of the single frozen replay; no new choices or fitting."""
from collections import defaultdict
from pathlib import Path
import csv
import json
import numpy as np

root = Path(__file__).resolve().parent
rows = list(csv.DictReader((root / "cell_metrics.csv").open(encoding="utf-8")))
by_arm = defaultdict(dict)
for row in rows:
    by_arm[row["arm"]][row["cell"]] = row
contrasts = {}
for arm in ("frozen", "fixed_global", "fixed_initial10", "random", "nearest5"):
    lower, upper, observed = [], [], []
    for cell, a in by_arm["adaptive"].items():
        b = by_arm[arm][cell]
        lower.append(float(a["hit_lower"]) - float(b["hit_upper"]))
        upper.append(float(a["hit_upper"]) - float(b["hit_lower"]))
        observed.append(float(a["hit_lower"]) - float(b["hit_lower"]))
    contrasts[arm] = {"conservative_difference_bounds": [float(np.mean(lower)), float(np.mean(upper))],
                      "confirmed_hit_fraction_difference": float(np.mean(observed)),
                      "warning": "negative lower bound or its CI does not prove a negative true difference"}
trace = [json.loads(line) for line in (root / "query_trace.jsonl").read_text(encoding="utf-8").splitlines()]
sequences = defaultdict(dict)
for record in trace:
    sequences[record["arm"]].setdefault(record["cell"], []).append(record["probe"])
adaptive = [r for r in trace if r["arm"] == "adaptive"]
report = {"kind": "predefined trace and endpoint diagnostics, no new scientific experiment",
          "contrast_identification_bounds": contrasts,
          "adaptive_total_attempts": len(adaptive),
          "adaptive_finite_feedback": sum(r["observed_response"] is not None for r in adaptive),
          "adaptive_prediction_change_steps": sum(r["prediction_mean_abs_change"] > 1e-12 for r in adaptive),
          "adaptive_shortlist_set_change_steps": sum(set(r["target_before"]) != set(r["target_after"]) for r in adaptive),
          "cells_adaptive_query_order_differs_from_fixed_initial10": sum(
              seq != sequences["fixed_initial10"][cell] for cell, seq in sequences["adaptive"].items()),
          "adaptation_attribution_limit": "Missing feedback can alter design covariance; query changes do not uniquely identify shortlist mediation."}
(root / "root_diagnostics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
