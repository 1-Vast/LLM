"""Rerun one registered development task and compare it with the registered records.

File summary
- Path: research/belief_planning/reproduce.py
- Purpose: check that decisions replay exactly, in this environment or another. Actions,
  readings, stops and terminal decisions must be identical. Floating-point diagnostics in the
  notes (forecast probabilities, expected utilities, beliefs) are compared with an absolute
  tolerance of 1e-9.
- Core points:
  - Why 1e-9. Forecasts are ratios of sums of at most a few thousand weights, and the finest
    registered threshold is 0.005. Last-bit differences between BLAS/libm builds are about 1e-15
    relative, so 1e-9 sits seven orders of magnitude below any gate yet flags any change in the
    computation.
  - `compute_seconds` is wall time and is excluded.
- Run: python -m research.belief_planning.reproduce --task sciplex3:A:1 --out FILE [--compare REGISTERED_DIR]
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from pathlib import Path

TOLERANCE = 1e-9
DECISION_FIELDS = ("final", "stop", "measurements", "days", "utility", "truth", "h1", "h2")


def _walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            _walk(a.get(k), b.get(k), f"{path}.{k}", out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            _walk(x, y, f"{path}[{i}]", out)
    elif isinstance(a, float) and isinstance(b, float):
        if not (math.isnan(a) and math.isnan(b)):
            out["max_abs"] = max(out["max_abs"], abs(a - b))
            if abs(a - b) > TOLERANCE:
                out["over_tolerance"].append(path)
    elif a != b and not (isinstance(a, (int, float)) and isinstance(b, (int, float)) and a == b):
        out["mismatch"].append(path)


def compare(new, old) -> dict:
    key = lambda r: (r["arm"], r["compound"], r["h1"], r["h2"])  # noqa: E731
    a, b = {key(r): r for r in new}, {key(r): r for r in old}
    out = {"records_new": len(a), "records_registered": len(b), "missing": len(set(b) - set(a)),
           "extra": len(set(a) - set(b)), "decision_mismatch": 0, "step_mismatch": 0, "max_abs": 0.0,
           "over_tolerance": [], "mismatch": []}
    for k in set(a) & set(b):
        x, y = a[k], b[k]
        if any(x.get(f) != y.get(f) for f in DECISION_FIELDS):
            out["decision_mismatch"] += 1
        sx = [(s["action"], s["outcome"], s["qc"]) for s in x["steps"]]
        sy = [(s["action"], s["outcome"], s["qc"]) for s in y["steps"]]
        if sx != sy:
            out["step_mismatch"] += 1
        _walk({k2: v for k2, v in x.items() if k2 != "compute_seconds"},
              {k2: v for k2, v in y.items() if k2 != "compute_seconds"}, "", out)
    out["over_tolerance"] = sorted(set(out["over_tolerance"]))[:20]
    out["mismatch"] = sorted(set(out["mismatch"]))[:20]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--compare", default=None)
    args = parser.parse_args()
    from . import locked as L
    dataset, tier, fold = args.task.split(":")
    result = L.dev_task((dataset, tier, int(fold)), L.NAMES)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8") as fh:
        for r in result["records"]:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    report = {"python": sys.version.split()[0], "task": args.task, "records": len(result["records"])}
    if args.compare:
        registered = Path(args.compare) / f"{dataset}_{tier}_{fold}.jsonl.gz"
        with gzip.open(registered, "rt", encoding="utf-8") as fh:
            old = [json.loads(line) for line in fh]
        new = [json.loads(json.dumps(r, sort_keys=True)) for r in result["records"]]
        report["comparison"] = compare(new, old)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
