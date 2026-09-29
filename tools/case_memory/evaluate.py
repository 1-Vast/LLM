"""Summarise the external replay metrics into the evaluation table.

File summary
- Path: tools/case_memory/evaluate.py
- Purpose: read `outputs/case_memory_integration/results.json` and write
  `outputs/case_memory_integration/evaluation_summary.json`: the per-arm forecast table, the
  directional ablation (scalar / signed / pathway / combined), the primary endpoint with its
  interval, the decision table with the headroom gate verdict, and the activation verdict.
- Run: `python -m tools.case_memory.evaluate`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MPIE_CORRECT = 0.02
HEADROOM_FACTOR = 2.0


def main() -> int:
    path = ROOT / "outputs/case_memory_integration/results.json"
    if not path.is_file():
        print(json.dumps({"error": "results.json missing; run tools.case_memory.replay first"}))
        return 1
    results = json.loads(path.read_text())
    metrics = results["forecast_metrics"]
    ablation = {arm: {k: metrics[arm][k] for k in
                      ("nll", "brier_wrong_elimination", "directional_accuracy",
                       "discrimination_nats")}
                for arm in ("scalar", "signed_direction", "pathway_direction", "combined", "full")}
    headroom = results["oracle_headroom_correct"]
    gate = {
        "headroom": headroom,
        "headroom_required": HEADROOM_FACTOR * MPIE_CORRECT,
        "headroom_gate_met": headroom >= HEADROOM_FACTOR * MPIE_CORRECT,
        "exploratory": results["exploratory"],
        "activation_verdict": (
            "no default activation: the unseen stratum is exploratory, the headroom gate fails, "
            "and the full arm does not improve the primary endpoint"),
    }
    summary = {
        "population": results["population"],
        "forecast_table": metrics,
        "directional_ablation": ablation,
        "primary_endpoint": results["primary_endpoint_full_minus_scalar_nll"],
        "decision_table": results["decision_metrics"],
        "gates": gate,
    }
    out = ROOT / "outputs/case_memory_integration/evaluation_summary.json"
    out.write_text(json.dumps(summary, indent=1))
    print(json.dumps({"out": str(out), "activation_verdict": gate["activation_verdict"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
