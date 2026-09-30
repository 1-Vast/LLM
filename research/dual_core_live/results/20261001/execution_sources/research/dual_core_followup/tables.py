"""Make raw-count tables alongside chemical-unit estimates, without new inference."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys

import pandas as pd

from research.dual_core_followup.snapshot import sha

ROOT = Path(__file__).resolve().parents[2]


def tables(run, out):
    run, out = run.resolve(), out.resolve()
    gate = json.loads((run / "gate.json").read_text())
    if not gate["passed"] or gate["episode_arm_paths"] != 19704:
        raise ValueError("complete_predeclared_run_required")
    out.mkdir(parents=True, exist_ok=False)
    paths = pd.read_csv(run / "episode_metrics.csv")
    summary = json.loads((run / "task_summary.json").read_text())
    fields = ("correct", "wrong", "undetermined", "deferred", "measurements", "days", "utility")
    rows = []
    for (task, arm), group in paths.groupby(["task", "arm"]):
        row = {"task": task, "arm": arm, "episodes": len(group),
               "chemical_units": group.independent_unit.nunique(),
               "source_or_result_unresolved_episodes": int((~group.point_identified).sum())}
        row.update({field + "_sum": float(group[field].sum()) for field in fields})
        row.update({field + "_unit_mean": summary[task]["arms"][arm][field]["mean"] for field in fields})
        rows.append(row)
    pd.DataFrame(rows).to_csv(out / "arm_counts.csv", index=False, mode="x")
    comparisons = []
    for task, result in summary.items():
        for comparison, metrics in result["comparison"].items():
            if comparison.endswith("_vs_fixed_none"):
                comparisons.append({"task": task, "comparison": comparison,
                    **{field: metrics[field]["mean"] for field in
                       ("delta_utility", "delta_lo", "delta_hi", "delta_correct", "delta_wrong", "delta_deferred",
                        "delta_days", "delta_measurements", "sequence_changed", "changed_same_terminal")},
                    "delta_utility_ci95": json.dumps(metrics["delta_utility"]["ci95"]),
                    "chemical_units": metrics["delta_utility"]["units"]})
    pd.DataFrame(comparisons).to_csv(out / "paired_comparisons.csv", index=False, mode="x")
    manifest = {"command": [sys.executable, *sys.argv], "git_parent": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "code_sha256": {str(p.relative_to(ROOT)): sha(p) for p in (Path(__file__), ROOT / "research/dual_core_followup/snapshot.py")},
        "inputs_sha256": {str((run / name).relative_to(ROOT)): sha(run / name) for name in
                          ("gate.json", "episode_metrics.csv", "task_summary.json")},
        "environment": {"python": sys.version, "interpreter": sys.executable, "pandas": pd.__version__, "platform": platform.platform()},
        "outputs_sha256": {p.name: sha(p) for p in out.iterdir()},
        "interpretation": "Raw episode counts/cost sums and existing chemical-unit mean/interval estimates are different denominators. Source bounds remain outer bounds; no new fit, threshold selection or uncertainty calculation."}
    with (out / "manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    tables(arguments.run, arguments.out)
